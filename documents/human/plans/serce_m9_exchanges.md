# Serce M9 — Exchanges: create, accept, complete, cancel + hearts transfer

**Wejście:** M7 (requests), M8 (offers), M6 (hearts)
**Rozmiar:** L
**Autor:** Architect

---

## Kontekst

Exchange to centralny mechanizm Serce — łączy Request z Offer, przenosi serduszka
między użytkownikami. Model `Exchange` już istnieje (M2), ale brak service/endpoint.

### Model Exchange (istniejący)

```
id: UUID (PK)
request_id: UUID | None (FK requests)
offer_id: UUID | None (FK offers)
requester_id: UUID (FK users) — kto potrzebuje pomocy (płaci hearts)
helper_id: UUID (FK users) — kto pomaga (otrzymuje hearts)
initiated_by: UUID (FK users) — kto stworzył Exchange
hearts_agreed: int (>= 0)
status: PENDING | ACCEPTED | COMPLETED | CANCELLED
created_at, completed_at
```

CHECK: `request_id IS NOT NULL OR offer_id IS NOT NULL`
Unique partial index: jeden ACCEPTED/COMPLETED Exchange per request_id (PostgreSQL only)

### Flow

**Request-based (helper odpowiada na prośbę):**
1. User A tworzy Request ("potrzebuję pomocy", hearts_offered=5)
2. User B widzi Request → tworzy Exchange (initiated_by=B, helper=B, requester=A, hearts_agreed=5)
3. User A akceptuje → ACCEPTED
4. Pomoc wykonana → COMPLETED → hearts transfer A→B

**Offer-based (requester korzysta z oferty):**
1. User B tworzy Offer ("mogę pomóc", hearts_asked=3)
2. User A widzi Offer → tworzy Exchange (initiated_by=A, requester=A, helper=B, hearts_agreed=3)
3. User B akceptuje → ACCEPTED
4. Pomoc wykonana → COMPLETED → hearts transfer A→B

**Kto akceptuje:** zawsze druga strona (nie initiator).
**Kto płaci:** zawsze requester_id → helper_id.

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/exchange_service.py` | Core: create, accept, complete, cancel, list, get |
| `app/api/v1/exchanges.py` | Router: 6 endpointów |
| `app/schemas/exchange.py` | Request/response models |
| `tests/test_exchange_service.py` | Unit testy |
| `tests/test_exchange_api.py` | Auth guard testy |
| `tests/integration/api/test_exchange_flow.py` | Integration testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/router.py` | Dodaj `exchanges_router` |
| `app/db/models/heart.py` | Dodaj `HeartLedgerType.EXCHANGE` (jeśli nie istnieje) |

---

## Endpointy

### 1. `POST /api/v1/exchanges` (201)

**Auth:** required
**Rate limit:** 20/hour
**Body (CreateExchangeBody):**
```python
request_id: UUID | None = None      # Exchange z Request
offer_id: UUID | None = None        # Exchange z Offer
hearts_agreed: int = Field(ge=0, le=50)
```

**Walidacja schema:** `request_id` XOR `offer_id` — dokładnie jedno musi być podane.

**Logika service (`create_exchange`):**
1. Waliduj XOR: request_id lub offer_id (nie oba, nie żadne) → 422 INVALID_SOURCE
2. **Jeśli request_id:**
   a. Pobierz Request → 404 REQUEST_NOT_FOUND
   b. Sprawdź `request.status == OPEN` → 422 REQUEST_NOT_OPEN
   c. Sprawdź `request.user_id != current_user.id` → 422 CANNOT_EXCHANGE_SELF
   d. Ustaw: `requester_id=request.user_id`, `helper_id=current_user.id`, `initiated_by=current_user.id`
3. **Jeśli offer_id:**
   a. Pobierz Offer → 404 OFFER_NOT_FOUND
   b. Sprawdź `offer.status == ACTIVE` → 422 OFFER_NOT_ACTIVE
   c. Sprawdź `offer.user_id != current_user.id` → 422 CANNOT_EXCHANGE_SELF
   d. Ustaw: `requester_id=current_user.id`, `helper_id=offer.user_id`, `initiated_by=current_user.id`
4. Sprawdź brak duplikatu: nie ma PENDING Exchange od tego samego initiatora na ten sam request/offer → 422 EXCHANGE_ALREADY_EXISTS
5. Utwórz Exchange(status=PENDING, hearts_agreed=hearts_agreed)
6. `db.flush()`, return exchange

**Nie sprawdzamy balance przy create** — hearts_agreed to propozycja. Balance sprawdzany przy accept.

### 2. `GET /api/v1/exchanges/{exchange_id}` (200)

**Auth:** required (participant only — requester, helper, or admin)
**Logika service (`get_exchange`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź `current_user.id in (exchange.requester_id, exchange.helper_id)` lub admin → 403 NOT_PARTICIPANT
3. Return exchange

### 3. `PATCH /api/v1/exchanges/{exchange_id}/accept` (200)

**Auth:** required (non-initiator only)
**Logika service (`accept_exchange`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź `exchange.status == PENDING` → 422 NOT_PENDING
3. Sprawdź `current_user.id != exchange.initiated_by` → 403 CANNOT_ACCEPT_OWN
4. Sprawdź current_user jest participant (requester lub helper) → 403 NOT_PARTICIPANT
5. **Balance guard:** requester.heart_balance >= exchange.hearts_agreed → 422 INSUFFICIENT_BALANCE
   (SELECT FOR UPDATE na requester — lock)
6. **Request unique guard (jeśli request_id):** sprawdź brak innego ACCEPTED/COMPLETED Exchange
   na ten request → 422 REQUEST_ALREADY_ACCEPTED
7. `exchange.status = ACCEPTED`
8. **Deduct hearts** z requester (escrow): `requester.heart_balance -= hearts_agreed`
9. Dodaj HeartLedger(type=EXCHANGE_ESCROW, from=requester, to=system, amount=hearts_agreed)
10. `db.flush()`, return exchange

**Decyzja architektoniczna: escrow at accept.**
Alternatywa: transfer at complete (prostsze, ale ryzyko braku balance).
Wybór: escrow — serduszka zdjęte z requester'a przy accept, kredytowane helper'owi przy complete.
Cancel po accept → refund.

### 4. `PATCH /api/v1/exchanges/{exchange_id}/complete` (200)

**Auth:** required (requester only — osoba która płaci potwierdza wykonanie)
**Logika service (`complete_exchange`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź `exchange.status == ACCEPTED` → 422 NOT_ACCEPTED
3. Sprawdź `current_user.id == exchange.requester_id` → 403 ONLY_REQUESTER_COMPLETES
4. **Credit hearts** do helper'a: `helper.heart_balance += hearts_agreed`
   (SELECT FOR UPDATE na helper — lock, sprawdź cap)
5. Dodaj HeartLedger(type=EXCHANGE_COMPLETE, from=requester, to=helper, amount=hearts_agreed)
6. `exchange.status = COMPLETED`, `exchange.completed_at = now()`
7. `db.flush()`, return exchange

**Cap guard:** jeśli helper osiągnie heart_balance_cap → 422 RECIPIENT_CAP_EXCEEDED
(edge case — akceptujemy jako bloker, requester odzyska hearts przez cancel)

### 5. `PATCH /api/v1/exchanges/{exchange_id}/cancel` (200)

**Auth:** required (either participant)
**Logika service (`cancel_exchange`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź `exchange.status in (PENDING, ACCEPTED)` → 422 NOT_CANCELLABLE
3. Sprawdź participant → 403 NOT_PARTICIPANT
4. **Jeśli status == ACCEPTED** (escrow active):
   a. Refund: `requester.heart_balance += hearts_agreed` (SELECT FOR UPDATE)
   b. HeartLedger(type=EXCHANGE_REFUND, from=system, to=requester, amount=hearts_agreed)
5. `exchange.status = CANCELLED`
6. `db.flush()`, return exchange

### 6. `GET /api/v1/exchanges` (200)

**Auth:** required
**Query params:**
```python
role: str | None = Query(None, pattern="^(requester|helper)$")  # filtruj rolę usera
status: ExchangeStatus | None = None
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service (`list_exchanges`):**
1. Base filter: `requester_id == current_user.id OR helper_id == current_user.id`
2. Opcjonalny filtr `role`: requester only / helper only
3. Opcjonalny filtr `status`
4. Sort: `created_at DESC`
5. Pagination (offset/limit/total)
6. Return (entries, total)

---

## Schemas (`app/schemas/exchange.py`)

```python
class CreateExchangeBody(BaseModel):
    request_id: UUID | None = None
    offer_id: UUID | None = None
    hearts_agreed: int = Field(ge=0, le=50)

    @model_validator(mode="after")
    def exactly_one_source(self) -> Self:
        if bool(self.request_id) == bool(self.offer_id):
            raise ValueError("Exactly one of request_id or offer_id required")
        return self

class ExchangeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    request_id: UUID | None
    offer_id: UUID | None
    requester_id: UUID
    helper_id: UUID
    initiated_by: UUID
    hearts_agreed: int
    status: str
    created_at: datetime
    completed_at: datetime | None

class ExchangeListResponse(BaseModel):
    entries: list[ExchangeRead]
    total: int
    offset: int
    limit: int
```

---

## Hearts integration — nowe typy ledger

Dodaj do `HeartLedgerType`:

| Typ | Kiedy | from | to | Opis |
|---|---|---|---|---|
| `EXCHANGE_ESCROW` | accept | requester | (system) | Hearts zdjęte z requester'a |
| `EXCHANGE_COMPLETE` | complete | requester | helper | Hearts kredytowane helper'owi |
| `EXCHANGE_REFUND` | cancel po accept | (system) | requester | Refund escrow |

Ledger entries z `from_user_id` i `to_user_id` — dla ESCROW/REFUND oba wskazują na requester'a
(system nie ma user_id). Alternatywa: `to_user_id=None` dla escrow.

**Decyzja:** `from_user_id=requester_id`, `to_user_id=requester_id` dla ESCROW (self-reference, type wyjaśnia kierunek). Dla COMPLETE: `from=requester, to=helper`. Dla REFUND: `from=requester, to=requester`.

---

## Testy

### Unit testy (`tests/test_exchange_service.py`)

Fixture: SQLite in-memory (wzorzec M7/M8).

| Test | Opis |
|---|---|
| **Create — request-based** | |
| test_create_from_request_valid | Helper tworzy Exchange na OPEN Request |
| test_create_request_not_found | → 404 |
| test_create_request_not_open | → 422 |
| test_create_request_self_exchange | → 422 |
| test_create_request_duplicate_pending | → 422 EXCHANGE_ALREADY_EXISTS |
| **Create — offer-based** | |
| test_create_from_offer_valid | Requester tworzy Exchange na ACTIVE Offer |
| test_create_offer_not_found | → 404 |
| test_create_offer_not_active | → 422 |
| test_create_offer_self_exchange | → 422 |
| **Create — validation** | |
| test_create_no_source | → 422 (schema validator) |
| test_create_both_sources | → 422 (schema validator) |
| **Get** | |
| test_get_as_requester | ✓ |
| test_get_as_helper | ✓ |
| test_get_not_participant | → 403 |
| test_get_not_found | → 404 |
| **Accept** | |
| test_accept_valid | Non-initiator akceptuje, hearts deducted |
| test_accept_own_exchange | → 403 CANNOT_ACCEPT_OWN |
| test_accept_not_pending | → 422 |
| test_accept_insufficient_balance | → 422 |
| test_accept_request_already_accepted | → 422 (unique guard) |
| **Complete** | |
| test_complete_valid | Requester completes, helper credited |
| test_complete_not_requester | → 403 |
| test_complete_not_accepted | → 422 |
| test_complete_cap_exceeded | → 422 |
| **Cancel** | |
| test_cancel_pending | PENDING → CANCELLED (no refund needed) |
| test_cancel_accepted_refund | ACCEPTED → CANCELLED + hearts refunded |
| test_cancel_not_participant | → 403 |
| test_cancel_completed | → 422 NOT_CANCELLABLE |
| **List** | |
| test_list_my_exchanges | Zwraca exchanges gdzie user jest requester/helper |
| test_list_filter_role | role=requester filtruje |
| test_list_filter_status | status=PENDING filtruje |
| test_list_pagination | offset/limit + total |

~30 unit testów.

### Auth guard testy (`tests/test_exchange_api.py`)

| Test | Opis |
|---|---|
| test_create_no_token | POST /exchanges → 401 |
| test_get_no_token | GET /exchanges/{id} → 401 |
| test_accept_no_token | PATCH /exchanges/{id}/accept → 401 |
| test_complete_no_token | PATCH /exchanges/{id}/complete → 401 |
| test_cancel_no_token | PATCH /exchanges/{id}/cancel → 401 |
| test_list_no_token | GET /exchanges → 401 |

6 auth guard testów.

### Integration testy (`tests/integration/api/test_exchange_flow.py`)

| Test | Opis |
|---|---|
| test_full_request_flow | Create Request → Create Exchange → Accept → Complete → verify hearts |
| test_full_offer_flow | Create Offer → Create Exchange → Accept → Complete → verify hearts |
| test_cancel_pending | Create → Cancel → verify |
| test_cancel_accepted_refund | Create → Accept → Cancel → verify hearts refunded |
| test_accept_insufficient_balance | Create → Accept with 0 balance → 422 |
| test_list_my_exchanges | Create multiple → list → verify filter |

6 integration testów.

**Total: ~42 testy.**

---

## Kluczowe decyzje architektoniczne

### Escrow at accept (nie at complete)

**Decyzja:** Hearts zdjęte z requester'a przy accept, kredytowane helper'owi przy complete.

**Alternatywa:** Transfer at complete (bez escrow).

**Trade-off:**
- Escrow: gwarantuje że hearts istnieją gdy exchange jest ACCEPTED. Brak surprises at complete.
- Escrow: wymaga refund logic przy cancel. Złożoność +1 endpoint state.
- No-escrow: prostsze, ale requester może wydać hearts między accept a complete → INSUFFICIENT_BALANCE at complete → zły UX.

**Wybór: escrow.** Lepszy UX, gwarancja balance, refund jest prosty.

### Requester completes (nie helper, nie obie strony)

**Decyzja:** Tylko requester (osoba płacąca) potwierdza wykonanie usługi.

**Alternatywa 1:** Helper completes (dostawca usługi potwierdza).
**Alternatywa 2:** Obie strony muszą potwierdzić (dual confirm).

**Trade-off:**
- Requester completes: naturalne — "zapłaciłem, potwierdzam że dostałem usługę". Proste.
- Helper completes: ryzyko abuse (helper potwierdza nie wykonaną usługę).
- Dual confirm: najlepsze ale złożone (partial state, timeout, dispute).

**Wybór: requester completes.** MVP simplicity. Dual confirm = M15+ (dispute system).

### Unique Exchange per Request (istniejący index)

Index `uix_exchange_request_accepted` gwarantuje max 1 ACCEPTED/COMPLETED Exchange per Request.
Service musi sprawdzić przed accept. Offer nie ma tego ograniczenia — jedno offer może mieć wiele exchanges.

### HIDDEN cascade (W1 z M8 review)

**Decyzja:** Exchange create guard sprawdza `offer.status == ACTIVE` i `request.status == OPEN`.
HIDDEN offer/request → 422 przy tworzeniu Exchange. Istniejące PENDING Exchanges na HIDDEN offer
nie są automatycznie kaskadowane — ale nowe nie mogą powstać. Kaskada PENDING→CANCELLED przy HIDDEN
to opcja do rozważenia w M15 (admin panel).

---

## Wzorce do zachowania

1. **flush-only w service, commit w endpoint** — jak M4-M8
2. **SELECT FOR UPDATE** na balance operations — wzorzec z M6 hearts_service
3. **Sorted lock order** — jeśli lockujemy 2 users (tu: requester at accept) — wzorzec z M6
4. **Ownership/participant guard** — wzorzec z M7/M8
5. **Paginacja** — offset/limit/total/entries — konwencja M6-M8

---

## Zależności

- `HeartLedgerType` wymaga 3 nowych wartości: `EXCHANGE_ESCROW`, `EXCHANGE_COMPLETE`, `EXCHANGE_REFUND`. Dodaj do enum w `app/db/models/heart.py`. Alembic migration potrzebne dla Postgres (ALTER TYPE ADD VALUE).
- `HeartLedger.related_exchange_id` (FK exchanges) — **już istnieje** w modelu. Użyj przy tworzeniu ledger entries.
- Exchange model już istnieje — brak zmian schema.
- Hearts_service: reuse `SELECT FOR UPDATE` pattern, nie reuse `gift_hearts` (inna logika: escrow vs transfer).
