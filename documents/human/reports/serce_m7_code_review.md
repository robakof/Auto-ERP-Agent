# Serce M7 — Code Review: Requests (CRUD + listing + search + cancel)

**Commit:** 6620b7c
**Reviewer:** Architect
**Handoff:** #125 od Developer

---

## Verdict: PASS

Kod zgodny z planem, konwencjami projektu i wzorcami z M4-M6.
Brak issues Critical lub Warning. Cztery obserwacje informacyjne (I0).

---

## Pliki przejrzane (7)

| Plik | Linie | Opis |
|---|---|---|
| `app/services/request_service.py` | 204 | Core: create, get, update, list, cancel |
| `app/api/v1/requests.py` | 116 | Router: 5 endpointów |
| `app/schemas/request.py` | 58 | Request/response models |
| `app/api/v1/router.py` | 17 | Rejestracja requests_router |
| `tests/test_request_service.py` | 488 | 23 unit tests |
| `tests/test_request_api.py` | 47 | 5 auth guard tests |
| `tests/integration/api/test_request_flow.py` | 187 | 6 integration tests |

---

## Ocena per komponent

### 1. request_service.py — L3 Senior ✓

**create_request:**
- Walidacja category (active check) i location ✓
- Informacyjny guard INSUFFICIENT_BALANCE (hearts nie blokowane) ✓
- Default expires_at z `settings.request_default_expiry_days` ✓
- EXPIRES_IN_PAST guard ✓
- flush-only ✓

**get_request:**
- HIDDEN visibility: owner widzi, inni dostają 404 ✓

**update_request:**
- NOT_OWNER (403), REQUEST_NOT_EDITABLE (tylko OPEN) ✓
- hearts_offered lock: sprawdza PENDING Exchange ✓
- Partial update (tylko non-None pola) ✓
- EXPIRES_IN_PAST guard na nowej wartości ✓

**list_requests:**
- JOIN User WHERE status='active' — feed filter ✓
- Filtry: category_id, location_id, location_scope, status ✓
- ILIKE search na title + description ✓
- Sort z getattr + fallback (zabezpieczone regex pattern w schema) ✓
- Paginacja offset/limit/total — konwencja M6 ✓

**cancel_request:**
- NOT_OWNER (403), REQUEST_NOT_CANCELLABLE (tylko OPEN) ✓
- Cascade: `UPDATE Exchange SET status=CANCELLED WHERE request_id=X AND status=PENDING` ✓
- Non-PENDING Exchanges nietknięte ✓

### 2. requests.py (router) — L3 Senior ✓

- POST / (201): rate limit 10/hour, `db.commit()` ✓
- GET /{id}: no rate limit ✓
- PATCH /{id}: `db.commit()` ✓
- GET /: sort/order validated via regex pattern, status default OPEN ✓
- POST /{id}/cancel: `db.commit()` ✓
- `FastAPIRequest` alias unika konfliktu z `Request` modelem ✓

### 3. schemas/request.py — L3 Senior ✓

- CreateRequestBody: walidacja min/max length, ge/le ✓
- UpdateRequestBody: wszystkie pola Optional (partial update) ✓
- RequestRead: from_attributes=True, kompletne pola ✓
- RequestListResponse: entries + total + offset + limit ✓
- CancelResponse: id + status (lean) ✓

### 4. Testy — 34 total, pokrycie kompletne ✓

| Suite | Count | Pokrycie |
|---|---|---|
| test_request_service.py | 23 | Create (4: valid, default/custom expires, guards) + Get (4: valid, 404, hidden non-owner/owner) + Update (5: title, hearts, not_owner, not_open, hearts_locked) + List (7: default, ilike, category, scope, pagination, sort, suspended_users) + Cancel (5: valid, not_owner, not_open, cascade, ignore_non_pending) |
| test_request_api.py | 5 | Auth guard na 5 endpointach |
| test_request_flow.py | 6 | E2E: create+get, create+list, update, cancel, search, pagination |

Test `test_cancel_ignores_non_pending_exchanges` poprawnie weryfikuje że ACCEPTED exchange nie jest kaskadowo anulowany. Forward-compatible z M9.

Test `test_update_hearts_locked` tworzy ręcznie Exchange PENDING — poprawna weryfikacja lock mechanizmu.

---

## Obserwacje informacyjne (I0)

### I0-1: ILIKE pattern nie escapuje `%` i `_`

`request_service.py:160` — `pattern = f"%{q}%"`. Użytkownik szukający `%` lub `_` dostanie szersze wyniki niż oczekiwane (SQL LIKE wildcards). Nie jest to SQL injection (zapytanie parametryzowane), ale UX edge case.

Fix (opcjonalny): `q.replace("%", "\\%").replace("_", "\\_")` lub SQLAlchemy `contains(q, autoescape=True)`.

### I0-2: hearts_offered lock sprawdza tylko PENDING (nie PENDING+ACCEPTED)

`request_service.py:107` — plan w sekcji "Kluczowe decyzje" mówił o PENDING/ACCEPTED, ale sekcja endpointu mówi PENDING only. Implementacja sprawdza PENDING — co jest poprawne biznesowo: po ACCEPTED, `hearts_agreed` na Exchange jest niezależny od `hearts_offered` na Request.

### I0-3: UpdateRequestBody nie pozwala wyczyścić expires_at

`schemas/request.py:26` — `expires_at: datetime | None = None` — brak rozróżnienia "nie podano" vs "ustaw na null". Service pomija None (linia 123-124). Akceptowalne — request bez expiry nie ma sensu biznesowego.

### I0-4: Integration tests zakładają seed data (categories, locations)

`test_request_flow.py:36-43` — `_ensure_category_and_location` pobiera z API, fallback na id=1. Działa bo migracja Alembic seeduje dane. Fragile jeśli seed się zmieni — ale testy przechodzą.

---

## Zgodność z planem M7

| Element planu | Status |
|---|---|
| POST /requests (201, rate 10/hour) | ✓ |
| GET /requests/{id} (HIDDEN → 404 non-owner) | ✓ |
| PATCH /requests/{id} (owner, OPEN, hearts lock) | ✓ |
| GET /requests (filtry, ILIKE, sort, pagination) | ✓ |
| POST /requests/{id}/cancel (cascade Exchanges) | ✓ |
| Feed filter: JOIN User WHERE active | ✓ |
| flush-only, endpoint commit | ✓ |
| Unit testy (happy + guards + edge) | ✓ 23 |
| Auth guard testy | ✓ 5 |
| Integration testy | ✓ 6 |

---

## Podsumowanie

M7 to solidna implementacja CRUD + search + cancel. Kluczowe elementy:
- hearts_offered lock działa poprawnie (Exchange PENDING guard)
- Cancel cascade na PENDING Exchanges forward-compatible z M9
- Feed filter (JOIN User, exclude suspended) — production-ready
- ILIKE search wystarczający na skalę MVP
- 34 testów z dobrym pokryciem edge cases

**PASS — bez zastrzeżeń.**
