# Serce M11 — Reviews: oceny po COMPLETED Exchange

**Wejście:** M9 (exchanges)
**Rozmiar:** S
**Autor:** Architect

---

## Istniejąca infrastruktura

Model `Review` już istnieje (`app/db/models/review.py`):
- id, exchange_id (FK exchanges), reviewer_id (FK users), reviewed_id (FK users), comment (str), created_at
- UNIQUE(exchange_id, reviewer_id) — DB-enforced, max 1 review per osoba per exchange

Brak `rating`/`score` w modelu — review to komentarz tekstowy (decyzja architektoniczna:
prosty MVP, numeric rating = Faza 2).

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/review_service.py` | Create review, list reviews, get review |
| `app/api/v1/reviews.py` | Router: 3 endpointy |
| `app/schemas/review.py` | Request/response models |
| `tests/test_review_service.py` | Unit testy |
| `tests/test_review_api.py` | Auth guard testy |
| `tests/integration/api/test_review_flow.py` | Integration testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/router.py` | Dodaj `reviews_router` |

---

## Endpointy

### 1. `POST /api/v1/exchanges/{exchange_id}/reviews` (201)

**Auth:** required (participant only)
**Rate limit:** 10/hour
**Body (CreateReviewBody):**
```python
comment: str = Field(min_length=10, max_length=2000)
```

**Logika service (`create_review`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź `exchange.status == COMPLETED` → 422 EXCHANGE_NOT_COMPLETED
3. Sprawdź participant → 403 NOT_PARTICIPANT
4. Ustaw `reviewed_id` = druga strona Exchange:
   - Jeśli `current_user.id == exchange.requester_id` → `reviewed_id = exchange.helper_id`
   - Jeśli `current_user.id == exchange.helper_id` → `reviewed_id = exchange.requester_id`
5. Sprawdź duplikat: `UNIQUE(exchange_id, reviewer_id)` — DB-enforced.
   Aplikacyjnie: sprawdź przed INSERT → 422 REVIEW_ALREADY_EXISTS (lepszy error message niż IntegrityError)
6. Utwórz Review(exchange_id, reviewer_id=current_user.id, reviewed_id, comment)
7. `db.flush()`, return review

**Brak edycji** — raz napisana recenzja jest niezmieniana (reguła #27 z planu v17).

### 2. `GET /api/v1/exchanges/{exchange_id}/reviews` (200)

**Auth:** required (participant only)
**Logika service (`list_reviews_for_exchange`):**
1. Pobierz Exchange → 404 EXCHANGE_NOT_FOUND
2. Sprawdź participant → 403 NOT_PARTICIPANT
3. Query: `WHERE exchange_id = X`
4. Return lista (max 2 reviews — requester + helper)

### 3. `GET /api/v1/users/{user_id}/reviews` (200)

**Auth:** required (public — każdy zalogowany może zobaczyć reviews użytkownika)
**Query params:**
```python
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service (`list_reviews_for_user`):**
1. Sprawdź User istnieje → 404 USER_NOT_FOUND
2. Query: `WHERE reviewed_id = user_id`
3. Sort: `created_at DESC`
4. Pagination (offset/limit/total)
5. Return (entries, total)

Publiczny profil recenzji — budowanie reputacji.

---

## Schemas (`app/schemas/review.py`)

```python
class CreateReviewBody(BaseModel):
    comment: str = Field(min_length=10, max_length=2000)

class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    exchange_id: UUID
    reviewer_id: UUID
    reviewed_id: UUID
    comment: str
    created_at: datetime

class ReviewListResponse(BaseModel):
    entries: list[ReviewRead]
    total: int
    offset: int
    limit: int
```

---

## Testy

### Unit testy (`tests/test_review_service.py`)

| Test | Opis |
|---|---|
| **Create** | |
| test_create_review_as_requester | Requester ocenia helper'a |
| test_create_review_as_helper | Helper ocenia requester'a |
| test_create_exchange_not_completed | → 422 |
| test_create_not_participant | → 403 |
| test_create_duplicate_review | → 422 REVIEW_ALREADY_EXISTS |
| test_create_exchange_not_found | → 404 |
| **List for exchange** | |
| test_list_reviews_for_exchange | Zwraca 1-2 reviews |
| test_list_reviews_not_participant | → 403 |
| **List for user** | |
| test_list_reviews_for_user | Publiczny profil, pagination |
| test_list_reviews_user_not_found | → 404 |
| test_list_reviews_empty | Nowy user, 0 reviews |
| test_list_reviews_pagination | offset/limit + total |

~12 unit testów.

### Auth guard testy (`tests/test_review_api.py`)

| Test | Opis |
|---|---|
| test_create_no_token | → 401 |
| test_list_exchange_no_token | → 401 |
| test_list_user_no_token | → 401 |

3 auth guard testy.

### Integration testy (`tests/integration/api/test_review_flow.py`)

| Test | Opis |
|---|---|
| test_full_review_flow | Exchange COMPLETED → Both review → verify |
| test_review_on_pending_rejected | Exchange PENDING → review → 422 |
| test_user_reviews_profile | Create reviews → GET /users/{id}/reviews |

3 integration testy.

**Total: ~18 testów.**

---

## Wzorce do zachowania

1. **flush-only w service, commit w endpoint**
2. **Participant guard** (create, list for exchange)
3. **DB-enforced uniqueness** + aplikacyjny pre-check (lepszy error message)
4. **Brak edycji/usunięcia** — immutable reviews
5. **Nested route** — `/exchanges/{id}/reviews` dla per-exchange view
6. **User route** — `/users/{id}/reviews` dla profilu reputacji

---

## Kluczowe decyzje

### Brak rating (numeric score)
Model Review nie ma pola `rating`. Decyzja MVP: komentarz tekstowy wystarczy.
Numeric rating (1-5 gwiazdek) = Faza 2. Dodanie kolumny = prosty Alembic migration.

### Brak edycji (reguła #27)
Review raz utworzone jest niezmieniane. Moderacja (hide) = M15 admin panel.
Delete = M16 soft delete (anonimizacja).

### reviewed_id wyliczany automatycznie
Reviewer nie podaje kogo ocenia — system ustala na podstawie roli w Exchange.
Eliminuje edge case gdzie reviewer próbuje ocenić sam siebie.
