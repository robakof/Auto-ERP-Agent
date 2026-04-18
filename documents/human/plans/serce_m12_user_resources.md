# Serce M12 — User Resources API: /me/requests, /offers, /exchanges, /reviews, /ledger, summary

**Wejście:** M5 (profile), M6 (hearts), M7 (requests), M8 (offers), M9 (exchanges), M11 (reviews)
**Rozmiar:** M
**Autor:** Architect

---

## Cel

Jeden punkt dostępu do wszystkich zasobów zalogowanego użytkownika. Endpointy agregacyjne
pod `/users/me/*` — dashboard-ready. Publiczny profil pod `/users/{id}` (ograniczony widok).

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/user_resources_service.py` | Query functions: my requests/offers/exchanges/summary |
| `app/api/v1/user_resources.py` | Router: 7 endpointów |
| `app/schemas/user_resources.py` | Summary schema + PublicProfileRead |
| `tests/test_user_resources_service.py` | Unit testy |
| `tests/test_user_resources_api.py` | Auth guard testy |
| `tests/integration/api/test_user_resources_flow.py` | Integration testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/router.py` | Dodaj `user_resources_router` |

---

## Endpointy

### 1. `GET /api/v1/users/me/requests` (200)

**Auth:** required
**Query params:**
```python
status: RequestStatus | None = None   # None = wszystkie statusy (own view)
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service (`my_requests`):**
1. Query: `WHERE user_id = current_user.id`
2. Opcjonalny filtr `status`
3. Sort: `created_at DESC`
4. Pagination
5. Return (entries, total)

Owner widzi WSZYSTKIE swoje statusy (OPEN, CANCELLED, HIDDEN) — w odróżnieniu od public feed.

### 2. `GET /api/v1/users/me/offers` (200)

**Auth:** required
**Query params:**
```python
status: OfferStatus | None = None
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service (`my_offers`):**
Analogiczna do my_requests — owner widzi wszystkie statusy.

### 3. `GET /api/v1/users/me/exchanges` (200)

**Auth:** required
**Query params:**
```python
role: str | None = Query(None, pattern="^(requester|helper)$")
status: ExchangeStatus | None = None
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service:** Reuse `exchange_service.list_exchanges` — już filtruje po current_user.

### 4. `GET /api/v1/users/me/reviews` (200)

**Auth:** required
**Query params:**
```python
type: str | None = Query(None, pattern="^(received|given)$")  # default: received
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service (`my_reviews`):**
1. `type=received` (default): `WHERE reviewed_id = current_user.id`
2. `type=given`: `WHERE reviewer_id = current_user.id`
3. Sort: `created_at DESC`, pagination

### 5. `GET /api/v1/users/me/ledger` (200)

**Auth:** required
**Logika:** Reuse `hearts_service.get_ledger` — już działa po user_id.

### 6. `GET /api/v1/users/me/summary` (200)

**Auth:** required
**Response (UserSummary):**
```python
class UserSummary(BaseModel):
    active_requests: int
    active_offers: int
    pending_exchanges: int
    completed_exchanges: int
    heart_balance: int
    reviews_received: int
    avg_review_count: int     # ile reviews (proxy for reputation, brak rating)
```

**Logika service (`user_summary`):**
Kilka COUNT queries:
1. `COUNT(requests) WHERE user_id=me AND status=OPEN`
2. `COUNT(offers) WHERE user_id=me AND status=ACTIVE`
3. `COUNT(exchanges) WHERE (requester=me OR helper=me) AND status=PENDING`
4. `COUNT(exchanges) WHERE (requester=me OR helper=me) AND status=COMPLETED`
5. `user.heart_balance` (z modelu)
6. `COUNT(reviews) WHERE reviewed_id=me`

### 7. `GET /api/v1/users/{user_id}/profile` (200)

**Auth:** required (public — każdy zalogowany)
**Response (PublicProfileRead):**
```python
class PublicProfileRead(BaseModel):
    id: UUID
    username: str
    bio: str | None
    location_id: int | None
    heart_balance: int
    created_at: datetime
    reviews_received: int
    completed_exchanges: int
```

**Logika service (`public_profile`):**
1. Pobierz User → 404 USER_NOT_FOUND
2. Sprawdź `user.status == ACTIVE` → 404 (ukryj suspended/deleted)
3. COUNT reviews + COUNT completed exchanges
4. Return ograniczony widok (brak email, phone, role)

---

## Schemas (`app/schemas/user_resources.py`)

```python
class UserSummary(BaseModel):
    active_requests: int
    active_offers: int
    pending_exchanges: int
    completed_exchanges: int
    heart_balance: int
    reviews_received: int

class PublicProfileRead(BaseModel):
    id: UUID
    username: str
    bio: str | None
    location_id: int | None
    heart_balance: int
    created_at: datetime
    reviews_received: int
    completed_exchanges: int
```

Reuse istniejących schemas: `RequestListResponse`, `OfferListResponse`, `ExchangeListResponse`,
`ReviewListResponse`, `LedgerResponse`.

---

## Testy

### Unit testy (`tests/test_user_resources_service.py`)

| Test | Opis |
|---|---|
| **my_requests** | |
| test_my_requests_all | Zwraca wszystkie statusy |
| test_my_requests_filter_status | Filtr po status |
| test_my_requests_empty | Nowy user, 0 requests |
| test_my_requests_pagination | offset/limit + total |
| **my_offers** | |
| test_my_offers_all | Zwraca wszystkie statusy |
| test_my_offers_filter_status | Filtr po status |
| **my_reviews** | |
| test_my_reviews_received | Default: received |
| test_my_reviews_given | type=given |
| test_my_reviews_empty | Nowy user, 0 reviews |
| **summary** | |
| test_summary_empty_user | Wszystkie countery = 0 |
| test_summary_with_data | Tworzy dane, sprawdza counts |
| **public_profile** | |
| test_public_profile_valid | Zwraca ograniczony widok |
| test_public_profile_not_found | → 404 |
| test_public_profile_suspended_hidden | → 404 |

~14 unit testów.

### Auth guard testy (`tests/test_user_resources_api.py`)

| Test | Opis |
|---|---|
| test_my_requests_no_token | → 401 |
| test_my_offers_no_token | → 401 |
| test_my_exchanges_no_token | → 401 |
| test_my_reviews_no_token | → 401 |
| test_my_ledger_no_token | → 401 |
| test_my_summary_no_token | → 401 |
| test_public_profile_no_token | → 401 |

7 auth guard testów.

### Integration testy (`tests/integration/api/test_user_resources_flow.py`)

| Test | Opis |
|---|---|
| test_summary_reflects_activity | Register → Create request + offer → Summary → verify counts |
| test_public_profile | Register → GET /users/{id}/profile → verify |
| test_my_requests_list | Create requests → GET /me/requests → verify |

3 integration testy.

**Total: ~24 testy.**

---

## Wzorce do zachowania

1. **flush-only w service, commit w endpoint**
2. **Reuse istniejących services** (exchange_service.list_exchanges, hearts_service.get_ledger)
3. **Paginacja** — offset/limit/total konwencja M6-M11
4. **Public profile = ograniczony widok** — bez email, phone, role
5. **Owner view = pełny dostęp** — wszystkie statusy widoczne

---

## Kluczowe decyzje

### Reuse vs nowe queries
`my_exchanges` i `my_ledger` reuse istniejących service functions (exchange_service, hearts_service).
`my_requests`, `my_offers`, `my_reviews` to nowe queries bo istniejące list_ functions
mają feed filter (JOIN User WHERE active) który nie ma sensu dla owner view.

### Brak avg_rating
Model Review nie ma `rating` (MVP — komentarz tekstowy). Summary zwraca `reviews_received` count
jako proxy dla reputacji. Dodanie avg_rating = Faza 2 (po dodaniu kolumny rating do Review).

### Public profile — nie exposed: email, phone, role
Bezpieczeństwo i prywatność. Email i phone to dane wrażliwe. Role widoczne tylko dla admina.

### Router prefix: /users/me/*
Endpointy pod istniejącym `/users` router byłyby zbyt duże. Osobny router `user_resources`
z prefix `/users` — FastAPI merguje route'y. Alternatywa: dodać do istniejącego users.py,
ale ten plik obsługuje profile changes i stałby się God Router.
