# Serce M13 — Notifications (in-app + email)

**Wejście:** M4 (email service), M9 (exchange events), M6 (hearts events), M10 (message events), M11 (review events)
**Rozmiar:** M
**Autor:** Architect

---

## Cel

Każde istotne zdarzenie generuje notyfikację (DB record) + email (best-effort, async).
User ma endpointy do odczytu, oznaczania jako przeczytane i zliczania nieprzeczytanych.

---

## Stan zastanego kodu

Model `Notification` **już istnieje** (`app/db/models/notification.py`) z 8 typami enum.
Tabela `notifications` **już istnieje** w migracji initial. Nie potrzeba nowej migracji Alembic.
`EmailService` (Protocol + Mock + Resend) **już istnieje** (`app/services/email_service.py`).

Brakuje: service, router, schemas, hook'i w istniejących serwisach, metoda email per type.

---

## Architektura

### Decyzja 1: Gdzie tworzyć notyfikacje?

**Wybór: helper `create_notification()` w `notification_service.py`, wywoływany z istniejących serwisów.**

Alternatywy rozważone:
- (A) Inline Notification() w każdym serwisie — rozproszony, duplikacja konstruktorów
- (B) Helper w notification_service — DRY, jedna funkcja, testowalna ✓
- (C) Router wywołuje po serwisie — łatwo zapomnieć, router się komplikuje

Trade-off: serwisy (exchange, hearts, message, review) importują notification_service.
To akceptowalne — coupling jest jednokierunkowy i stabilny (notyfikacja nie zmienia logiki domenowej).

### Decyzja 2: Email — synchronicznie czy async?

**Wybór: FastAPI `BackgroundTasks` — email po db.commit(), best-effort.**

Flow:
1. Service tworzy Notification w tej samej transakcji (flush)
2. Router commituje
3. Router dodaje email do BackgroundTasks (po commit — gwarancja że notyfikacja jest w DB)
4. Email fail → log warning, nie blokuje odpowiedzi

Alternatywy rozważone:
- Celery/Redis — overkill na tym etapie, brak infrastruktury
- Synchroniczny email przed response — blokuje request, fail = 500

### Decyzja 3: Kto jest odbiorcą notyfikacji?

Każda notyfikacja idzie do **dokładnie jednego** usera — drugiej strony zdarzenia:

| Typ | Trigger | Odbiorca |
|---|---|---|
| NEW_EXCHANGE | create_exchange | Właściciel Request/Offer (nie initiator) |
| EXCHANGE_ACCEPTED | accept_exchange | Initiator exchange |
| EXCHANGE_COMPLETED | complete_exchange | Helper |
| EXCHANGE_CANCELLED | cancel_exchange | Druga strona (nie canceller) |
| NEW_MESSAGE | send_message | Drugi participant (nie sender) |
| NEW_REVIEW | create_review | Reviewed user |
| HEARTS_RECEIVED | gift_hearts | Recipient giftu |
| REQUEST_EXPIRED | (M17 — scheduler) | Owner request |

### Decyzja 4: REQUEST_EXPIRED

M13 przygotowuje typ + email template + helper function.
M17 implementuje APScheduler job który wywołuje `create_notification()`.
M13 **nie** implementuje background job.

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/notification_service.py` | create_notification, list, mark_read, mark_all_read, unread_count |
| `app/api/v1/notifications.py` | Router: 4 endpointy |
| `app/schemas/notification.py` | NotificationRead, NotificationListResponse, UnreadCountResponse |
| `tests/test_notification_service.py` | Unit testy CRUD + create_notification |
| `tests/test_notification_api.py` | Auth guard + endpoint testy |
| `tests/test_notification_hooks.py` | Testy integracji: zdarzenie → notification created |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/services/exchange_service.py` | +4 wywołania create_notification (create/accept/complete/cancel) |
| `app/services/message_service.py` | +1 wywołanie create_notification (send_message) |
| `app/services/review_service.py` | +1 wywołanie create_notification (create_review) |
| `app/services/hearts_service.py` | +1 wywołanie create_notification (gift_hearts) |
| `app/services/email_service.py` | +1 metoda send_notification (Protocol + Mock + Resend) |
| `app/api/v1/router.py` | +include notifications_router |
| `app/api/v1/exchanges.py` | +BackgroundTasks email po create/accept/complete/cancel |
| `app/api/v1/messages.py` | +BackgroundTasks email po send |
| `app/api/v1/reviews.py` | +BackgroundTasks email po create |
| `app/api/v1/hearts.py` | +BackgroundTasks email po gift |

---

## Notification Service (`app/services/notification_service.py`)

```python
async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    type: NotificationType,
    *,
    reason: str | None = None,
    related_exchange_id: UUID | None = None,
    related_message_id: UUID | None = None,
) -> Notification:
    """Create in-app notification. Same transaction as caller (flush only)."""

async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    *,
    unread_only: bool = False,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Notification], int]:

async def mark_as_read(
    db: AsyncSession,
    notification_id: UUID,
    current_user_id: UUID,
) -> Notification:

async def mark_all_as_read(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Returns count of updated notifications."""

async def unread_count(
    db: AsyncSession,
    user_id: UUID,
) -> int:
```

---

## Email Extension (`app/services/email_service.py`)

Nowa metoda w Protocol + obu implementacjach:

```python
class EmailService(Protocol):
    ...
    async def send_notification(self, to: str, notification_type: str, reason: str | None) -> None: ...
```

Subject mapping per type:
- NEW_EXCHANGE → "Nowa propozycja wymiany — Serce"
- EXCHANGE_ACCEPTED → "Wymiana zaakceptowana — Serce"
- EXCHANGE_COMPLETED → "Wymiana zakonczona — Serce"
- EXCHANGE_CANCELLED → "Wymiana anulowana — Serce"
- NEW_MESSAGE → "Nowa wiadomosc w wymianie — Serce"
- NEW_REVIEW → "Otrzymales/as opinie — Serce"
- HEARTS_RECEIVED → "Otrzymales/as serca — Serce"
- REQUEST_EXPIRED → "Twoja prosba wygasla — Serce"

Body: prosty tekst z reason (jeśli podany). HTML templates = Faza 2.

MockEmailService: appenduje do `sent` list (jak istniejące metody).

---

## Endpointy (Router `app/api/v1/notifications.py`)

Prefix: `/users/me/notifications` (pod user_resources lub osobny router)

### 1. `GET /api/v1/users/me/notifications` (200)

**Auth:** required
**Query params:**
```python
unread: bool = Query(False)         # True = tylko nieprzeczytane
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Response:** `NotificationListResponse` (entries, total, offset, limit)

### 2. `POST /api/v1/users/me/notifications/{notification_id}/read` (200)

**Auth:** required
**Guards:** notification.user_id == current_user.id → 404 (nie 403, ukryj istnienie)
**Response:** `NotificationRead`

### 3. `POST /api/v1/users/me/notifications/read-all` (200)

**Auth:** required
**Response:** `{"updated": int}` — ile oznaczono

### 4. `GET /api/v1/users/me/notifications/unread-count` (200)

**Auth:** required
**Response:** `{"count": int}`
**Uzasadnienie:** Lekki endpoint dla badge UI — nie wymaga pełnego list.

---

## Schemas (`app/schemas/notification.py`)

```python
class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: str
    reason: str | None
    related_exchange_id: UUID | None
    related_message_id: UUID | None
    is_read: bool
    created_at: datetime

class NotificationListResponse(BaseModel):
    entries: list[NotificationRead]
    total: int
    offset: int
    limit: int

class UnreadCountResponse(BaseModel):
    count: int

class MarkAllReadResponse(BaseModel):
    updated: int
```

---

## Hook'i w istniejących serwisach

### exchange_service.py

```python
from app.services import notification_service

async def create_exchange(...) -> Exchange:
    ...
    db.add(exchange)
    await db.flush()

    # Notify the other party (not initiator)
    recipient_id = exchange.requester_id if exchange.initiated_by != exchange.requester_id else exchange.helper_id
    await notification_service.create_notification(
        db, recipient_id, NotificationType.NEW_EXCHANGE,
        related_exchange_id=exchange.id,
    )
    return exchange
```

Analogicznie dla accept (→ initiator), complete (→ helper), cancel (→ druga strona).

### message_service.py

```python
async def send_message(...) -> Message:
    ...
    db.add(msg)
    await db.flush()

    # Notify other participant
    other_id = exchange.helper_id if current_user_id == exchange.requester_id else exchange.requester_id
    await notification_service.create_notification(
        db, other_id, NotificationType.NEW_MESSAGE,
        related_exchange_id=exchange_id,
        related_message_id=msg.id,
    )
    return msg
```

### review_service.py

```python
async def create_review(...) -> Review:
    ...
    db.add(review)
    await db.flush()

    await notification_service.create_notification(
        db, reviewed_id, NotificationType.NEW_REVIEW,
        related_exchange_id=exchange_id,
    )
    return review
```

### hearts_service.py

```python
async def gift_hearts(...) -> HeartLedger:
    ...
    db.add(ledger)
    await db.flush()

    await notification_service.create_notification(
        db, to_user_id, NotificationType.HEARTS_RECEIVED,
        reason=note,
    )
    return ledger
```

---

## Email w routerach (BackgroundTasks)

Pattern per router (przykład exchanges.py):

```python
from fastapi import BackgroundTasks
from app.services.email_service import get_email_service

@router.post("", response_model=ExchangeRead, status_code=201)
async def create_exchange_endpoint(
    ...,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await exchange_service.create_exchange(...)
    await db.commit()

    # Best-effort email (after commit)
    recipient = await db.get(User, recipient_id)
    if recipient and recipient.email:
        email_svc = get_email_service()
        background_tasks.add_task(
            email_svc.send_notification,
            to=recipient.email,
            notification_type="NEW_EXCHANGE",
            reason=None,
        )

    return result
```

**Uwaga:** Recipient email query po commit — nie blokuje transakcji.
Fail w background_task → FastAPI loguje exception, response już wysłany.

---

## Testy

### Unit testy (`tests/test_notification_service.py`)

| Test | Opis |
|---|---|
| test_create_notification | Tworzy notyfikację, sprawdza pola |
| test_list_notifications_empty | Nowy user → 0 |
| test_list_notifications_paginated | Tworzy N, sprawdza offset/limit/total |
| test_list_notifications_unread_filter | Filtr unread_only=True |
| test_mark_as_read | is_read → True |
| test_mark_as_read_not_found | → 404 |
| test_mark_as_read_wrong_user | → 404 (nie 403) |
| test_mark_all_as_read | N unread → 0 unread, returns count |
| test_unread_count | Tworzy mix read/unread, sprawdza count |

~9 unit testow.

### Hook testy (`tests/test_notification_hooks.py`)

| Test | Opis |
|---|---|
| test_exchange_create_notifies_other_party | create_exchange → NEW_EXCHANGE dla non-initiator |
| test_exchange_accept_notifies_initiator | accept → EXCHANGE_ACCEPTED dla initiator |
| test_exchange_complete_notifies_helper | complete → EXCHANGE_COMPLETED dla helper |
| test_exchange_cancel_notifies_other | cancel → EXCHANGE_CANCELLED dla druga strona |
| test_message_send_notifies_other | send_message → NEW_MESSAGE |
| test_review_create_notifies_reviewed | create_review → NEW_REVIEW |
| test_gift_hearts_notifies_recipient | gift → HEARTS_RECEIVED |

~7 hook testow.

### Auth guard testy (`tests/test_notification_api.py`)

| Test | Opis |
|---|---|
| test_list_notifications_no_token | → 401 |
| test_mark_read_no_token | → 401 |
| test_mark_all_read_no_token | → 401 |
| test_unread_count_no_token | → 401 |
| test_list_notifications_returns_own_only | User A nie widzi notyfikacji User B |
| test_mark_read_other_user_notification | → 404 |

~6 auth/API testow.

### Integration testy (skip — need Postgres)

| Test | Opis |
|---|---|
| test_exchange_flow_generates_notifications | Create → accept → complete = 3 notifications |
| test_email_sent_on_notification | Mock email service, verify send called |

**Total: ~24 testy (22 unit + 2 integration skip).**

---

## Wzorce do zachowania

1. **flush-only w service, commit w router** — notification_service.create_notification() robi flush
2. **Notification w tej samej transakcji** — atomowość z triggering event
3. **Email po commit** — BackgroundTasks, best-effort
4. **404 (nie 403)** dla cudzej notyfikacji — ukryj istnienie (security)
5. **Paginacja** — offset/limit/total konwencja M6-M12
6. **rate limit** na read-all: `10/minute` (zapobiega abuse)

---

## Kolejnosc implementacji (sugerowana)

1. Schemas (notification.py) — czyste Pydantic, zero zależności
2. notification_service.py — CRUD + create_notification helper
3. tests/test_notification_service.py — unit testy service
4. Hook'i w istniejących serwisach (exchange, message, review, hearts)
5. tests/test_notification_hooks.py — weryfikacja hook'ów
6. Email extension (email_service.py +send_notification)
7. Router (notifications.py) + BackgroundTasks w istniejących routerach
8. tests/test_notification_api.py — auth guard + endpoint testy
9. Router registration (router.py)

---

## Poza scope M13

- REQUEST_EXPIRED background job (M17 — APScheduler)
- User notification preferences / opt-out per type (Faza 2)
- HTML email templates (Faza 2)
- Push notifications / WebSocket (Faza 2+)
- Notification grouping / digest (Faza 2+)
