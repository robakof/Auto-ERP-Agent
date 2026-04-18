# Serce M7 — Requests: CRUD + listing + search + cancel

**Wejście:** M2 (categories/locations), M5 (profile), M6 (hearts convention)
**Rozmiar:** M
**Autor:** Architect

---

## Istniejąca infrastruktura

Model `Request` już istnieje (`app/db/models/request.py`):
- id, user_id (FK users), title, description, hearts_offered (CHECK >= 0)
- category_id (FK categories), location_id (FK locations), location_scope (CITY/VOIVODESHIP/NATIONAL)
- status: OPEN / IN_PROGRESS / DONE / CANCELLED / HIDDEN
- created_at, expires_at, updated_at (onupdate)

Model `Exchange` istnieje (`app/db/models/exchange.py`) z request_id FK — M7 musi przygotować cascade logikę (cancel PENDING Exchanges), choć Exchange CRUD pojawi się dopiero w M9.

Config: `request_default_expiry_days: int = 30` — już w settings.

Paginacja: konwencja z M6 (offset/limit, total w response).

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/request_service.py` | Core CRUD + search + cancel |
| `app/api/v1/requests.py` | Router: 5 endpointów |
| `app/schemas/request.py` | Request/response models |
| `tests/test_request_service.py` | Unit testy |
| `tests/test_request_api.py` | Auth guard testy |
| `tests/integration/api/test_request_flow.py` | Integration testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/router.py` | Dodaj `requests_router` |

---

## Endpointy

### 1. `POST /api/v1/requests` (201)

**Auth:** required (get_current_user)
**Rate limit:** 10/hour
**Body (CreateRequestBody):**
```python
title: str = Field(min_length=3, max_length=200)
description: str = Field(min_length=10, max_length=2000)
hearts_offered: int = Field(ge=0, le=50)  # le=heart_balance_cap
category_id: int
location_id: int
location_scope: LocationScope  # reuse enum from model
expires_at: datetime | None = None  # None → default +30 days
```

**Logika service (`create_request`):**
1. Sprawdź `category_id` istnieje i `active=True` → 404 CATEGORY_NOT_FOUND
2. Sprawdź `location_id` istnieje → 404 LOCATION_NOT_FOUND
3. Jeśli `hearts_offered > 0` — sprawdź `user.heart_balance >= hearts_offered` → 422 INSUFFICIENT_BALANCE (informacyjny guard — serca nie są blokowane przy tworzeniu, transfer nastąpi dopiero przy Exchange complete w M9)
4. Jeśli `expires_at is None` → ustaw `now() + settings.request_default_expiry_days`
5. Jeśli `expires_at` podane → walidacja: musi być w przyszłości → 422 EXPIRES_IN_PAST
6. Utwórz Request(user_id=current_user.id, status=OPEN, ...)
7. `db.flush()`, return request

**Uwaga:** `hearts_offered` to deklaracja, nie blokada. Nie odejmuj serduszek przy tworzeniu. Transfer dopiero przy Exchange complete (M9).

### 2. `GET /api/v1/requests/{request_id}` (200)

**Auth:** required
**Logika service (`get_request`):**
1. Pobierz Request po id → 404 REQUEST_NOT_FOUND
2. Jeśli `status == HIDDEN` i `user_id != current_user.id` → 404 REQUEST_NOT_FOUND
3. Return request

### 3. `PATCH /api/v1/requests/{request_id}` (200)

**Auth:** required (owner only)
**Body (UpdateRequestBody):**
```python
title: str | None = Field(None, min_length=3, max_length=200)
description: str | None = Field(None, min_length=10, max_length=2000)
expires_at: datetime | None = None
hearts_offered: int | None = Field(None, ge=0, le=50)
```

**Logika service (`update_request`):**
1. Pobierz Request po id → 404 REQUEST_NOT_FOUND
2. Sprawdź `request.user_id == current_user.id` → 403 NOT_OWNER
3. Sprawdź `request.status == OPEN` → 422 REQUEST_NOT_EDITABLE (tylko OPEN requests)
4. Jeśli `hearts_offered` zmieniane:
   - Sprawdź czy istnieje Exchange z `request_id = this` i `status = 'PENDING'` → 422 HEARTS_OFFERED_LOCKED
5. Jeśli `expires_at` podane → walidacja: musi być w przyszłości → 422 EXPIRES_IN_PAST
6. Update podanych pól (pomiń None)
7. `db.flush()`, return request

### 4. `GET /api/v1/requests` (200)

**Auth:** required
**Query params:**
```python
category_id: int | None = None
location_id: int | None = None
location_scope: LocationScope | None = None
status: RequestStatus | None = Query(default=RequestStatus.OPEN)
q: str | None = Query(None, max_length=100)  # ILIKE search
sort: str = Query("created_at", pattern="^(created_at|hearts_offered|expires_at)$")
order: str = Query("desc", pattern="^(asc|desc)$")
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service (`list_requests`):**
1. Base filter: `Request.status == status_filter` (default OPEN)
2. **Feed filter:** JOIN User, WHERE `User.status == 'active'` — ukryj requests od suspended/deleted
3. Jeśli `category_id` → AND `Request.category_id == category_id`
4. Jeśli `location_id` → AND `Request.location_id == location_id`
5. Jeśli `location_scope` → AND `Request.location_scope == location_scope`
6. Jeśli `q` → AND `(Request.title ILIKE %q% OR Request.description ILIKE %q%)`
7. Order by `sort` direction `order`
8. Count total (before pagination)
9. Apply offset/limit
10. Return (entries, total)

**Response:** `RequestListResponse(entries=[...], total=N, offset=X, limit=Y)` — ta sama konwencja co M6 LedgerResponse.

### 5. `POST /api/v1/requests/{request_id}/cancel` (200)

**Auth:** required (owner only)
**Logika service (`cancel_request`):**
1. Pobierz Request po id → 404 REQUEST_NOT_FOUND
2. Sprawdź `request.user_id == current_user.id` → 403 NOT_OWNER
3. Sprawdź `request.status == OPEN` → 422 REQUEST_NOT_CANCELLABLE (nie można cancel IN_PROGRESS/DONE/CANCELLED/HIDDEN)
4. `request.status = CANCELLED`
5. **Cascade:** UPDATE Exchange SET status='CANCELLED' WHERE request_id=this AND status='PENDING'
   - Użyj `update(Exchange).where(Exchange.request_id == request.id, Exchange.status == ExchangeStatus.PENDING).values(status=ExchangeStatus.CANCELLED)`
   - Zwróć count cancelled exchanges (informacyjny)
6. `db.flush()`, return request

---

## Schemas (`app/schemas/request.py`)

```python
class CreateRequestBody(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    hearts_offered: int = Field(ge=0, le=50)
    category_id: int
    location_id: int
    location_scope: LocationScope
    expires_at: datetime | None = None

class UpdateRequestBody(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=2000)
    hearts_offered: int | None = Field(None, ge=0, le=50)
    expires_at: datetime | None = None

class RequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    title: str
    description: str
    hearts_offered: int
    category_id: int
    location_id: int
    location_scope: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    updated_at: datetime

class RequestListResponse(BaseModel):
    entries: list[RequestRead]
    total: int
    offset: int
    limit: int

class CancelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
```

---

## Testy

### Unit testy (`tests/test_request_service.py`)

Fixture: SQLite in-memory (wzorzec z test_hearts_service.py). Dodaj tabele: User, Request, Category, Location, Exchange.

| Test | Opis |
|---|---|
| **Create — happy path** | |
| test_create_request_valid | Tworzy request, sprawdza pola |
| test_create_request_default_expires | expires_at = None → +30 days |
| test_create_request_custom_expires | Podany expires_at |
| **Create — guards** | |
| test_create_category_not_found | Nieistniejąca kategoria → 404 |
| test_create_category_inactive | category.active=False → 404 |
| test_create_location_not_found | Nieistniejąca lokalizacja → 404 |
| test_create_expires_in_past | expires_at w przeszłości → 422 |
| **Get** | |
| test_get_request_valid | Pobiera po id |
| test_get_request_not_found | → 404 |
| test_get_hidden_request_by_non_owner | → 404 |
| test_get_hidden_request_by_owner | → 200 (owner widzi) |
| **Update — happy path** | |
| test_update_title_only | Partial update |
| test_update_hearts_offered | Zmiana hearts_offered |
| **Update — guards** | |
| test_update_not_owner | → 403 |
| test_update_not_open | status=CANCELLED → 422 |
| test_update_hearts_locked | Exchange PENDING → 422 |
| **List** | |
| test_list_default_open | Zwraca tylko OPEN |
| test_list_search_ilike | q= filtruje po title/description |
| test_list_filter_category | category_id filtr |
| test_list_filter_location_scope | location_scope filtr |
| test_list_pagination | offset/limit + total |
| test_list_sort_hearts_desc | sort=hearts_offered, order=desc |
| test_list_excludes_suspended_users | User.status=suspended → request nie widoczny |
| **Cancel** | |
| test_cancel_request_valid | OPEN → CANCELLED |
| test_cancel_not_owner | → 403 |
| test_cancel_not_open | status=DONE → 422 |
| test_cancel_cascades_pending_exchanges | Exchange PENDING → CANCELLED |
| test_cancel_ignores_non_pending_exchanges | Exchange ACCEPTED untouched |

~26 unit testów.

### Auth guard testy (`tests/test_request_api.py`)

| Test | Opis |
|---|---|
| test_create_no_token | POST /requests → 401 |
| test_get_no_token | GET /requests/{id} → 401 |
| test_update_no_token | PATCH /requests/{id} → 401 |
| test_list_no_token | GET /requests → 401 |
| test_cancel_no_token | POST /requests/{id}/cancel → 401 |

5 auth guard testów.

### Integration testy (`tests/integration/api/test_request_flow.py`)

| Test | Opis |
|---|---|
| test_create_and_get_request | Create → Get → verify |
| test_create_and_list | Create 2 → List → verify count |
| test_update_request | Create → Update title → verify |
| test_cancel_request | Create → Cancel → verify status |
| test_list_search | Create 2 z różnymi tytułami → q= → 1 result |
| test_list_pagination | Create 5 → offset=2, limit=2 → verify |

6 integration testów.

**Total: ~37 testów.**

---

## Wzorce do zachowania

1. **flush-only w service, commit w endpoint** — jak M4-M6
2. **Paginacja** — offset/limit/total/entries — konwencja z M6 LedgerResponse
3. **Rate limit** — POST /requests: 10/hour (create), brak na GET
4. **Auth** — get_current_user na wszystkich endpointach
5. **ILIKE search** — PostgreSQL ILIKE (SQLite case-insensitive LIKE w testach)
6. **Feed filter** — JOIN User, exclude suspended/deleted

---

## Kluczowe decyzje

### hearts_offered to deklaracja, nie blokada
Przy tworzeniu requesta serca NIE są odejmowane z balance. Odejmowanie nastąpi przy Exchange complete (M9). Guard `INSUFFICIENT_BALANCE` w create jest informacyjny — zapobiega tworzeniu obietnic bez pokrycia, ale nie blokuje środków.

### HIDDEN requests widoczne dla ownera
Owner widzi swoje HIDDEN requests (mogą być ukryte przez admina). Inni użytkownicy dostają 404.

### Cancel tylko z OPEN
IN_PROGRESS (Exchange accepted) wymaga cancel Exchange najpierw (M9 logika). DONE/CANCELLED/HIDDEN — immutable.

### hearts_offered lock
Sprawdzaj Exchange z request_id = this AND status PENDING/ACCEPTED. Jeśli istnieje — hearts_offered zablokowane. Zapobiega zmianie stawki po tym jak ktoś już odpowiedział.

### Wyszukiwanie
ILIKE na `title` i `description`. Pełny full-text search (tsvector) zostawiony na przyszłość — ILIKE wystarczy na skalę MVP.
