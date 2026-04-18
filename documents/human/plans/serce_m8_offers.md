# Serce M8 — Offers: CRUD + listing + status management

**Wejście:** M2 (categories/locations), M5 (profile)
**Rozmiar:** M
**Autor:** Architect

---

## Istniejąca infrastruktura

Model `Offer` już istnieje (`app/db/models/offer.py`):
- id, user_id (FK users), title, description, hearts_asked (CHECK >= 0)
- category_id (FK categories), location_id (FK locations), location_scope (reuse z Request)
- status: ACTIVE / PAUSED / INACTIVE / HIDDEN
- created_at, updated_at (onupdate)

Brak `expires_at` — oferty nie wygasają (w odróżnieniu od Request).

Model `Exchange` ma `offer_id` FK — M9 będzie sprawdzać status oferty przy tworzeniu Exchange.

Wzorce z M7 do reuse: pagination, feed filter, ILIKE search, ownership guard.

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/offer_service.py` | Core CRUD + listing + status management |
| `app/api/v1/offers.py` | Router: 5 endpointów |
| `app/schemas/offer.py` | Request/response models |
| `tests/test_offer_service.py` | Unit testy |
| `tests/test_offer_api.py` | Auth guard testy |
| `tests/integration/api/test_offer_flow.py` | Integration testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/router.py` | Dodaj `offers_router` |

---

## Endpointy

### 1. `POST /api/v1/offers` (201)

**Auth:** required
**Rate limit:** 10/hour
**Body (CreateOfferBody):**
```python
title: str = Field(min_length=3, max_length=200)
description: str = Field(min_length=10, max_length=2000)
hearts_asked: int = Field(ge=0, le=50)
category_id: int
location_id: int
location_scope: LocationScope
```

**Logika service (`create_offer`):**
1. Sprawdź `category_id` istnieje i `active=True` → 404 CATEGORY_NOT_FOUND
2. Sprawdź `location_id` istnieje → 404 LOCATION_NOT_FOUND
3. Utwórz Offer(user_id=current_user.id, status=ACTIVE, ...)
4. `db.flush()`, return offer

Brak guarda INSUFFICIENT_BALANCE — hearts_asked to oczekiwanie od requestera, nie deklaracja offerer'a.

### 2. `GET /api/v1/offers/{offer_id}` (200)

**Auth:** required
**Logika service (`get_offer`):**
1. Pobierz Offer po id → 404 OFFER_NOT_FOUND
2. Jeśli `status == HIDDEN` i `user_id != current_user.id` → 404 OFFER_NOT_FOUND
3. Jeśli `status == INACTIVE` i `user_id != current_user.id` → 404 OFFER_NOT_FOUND
4. Return offer

INACTIVE i HIDDEN ukryte dla non-owner (INACTIVE = wycofana przez ownera, HIDDEN = ukryta przez admina).

### 3. `PATCH /api/v1/offers/{offer_id}` (200)

**Auth:** required (owner only)
**Body (UpdateOfferBody):**
```python
title: str | None = Field(None, min_length=3, max_length=200)
description: str | None = Field(None, min_length=10, max_length=2000)
hearts_asked: int | None = Field(None, ge=0, le=50)
```

**Logika service (`update_offer`):**
1. Pobierz Offer po id → 404 OFFER_NOT_FOUND
2. Sprawdź `offer.user_id == current_user.id` → 403 NOT_OWNER
3. Sprawdź `offer.status in (ACTIVE, PAUSED)` → 422 OFFER_NOT_EDITABLE (INACTIVE/HIDDEN nie edytowalne)
4. Update podanych pól (pomiń None)
5. `db.flush()`, return offer

Brak hearts_asked lock — w odróżnieniu od Request, hearts_asked to oczekiwanie cenowe, owner może je zmieniać dowolnie. Exchange.hearts_agreed jest niezależne.

### 4. `PATCH /api/v1/offers/{offer_id}/status` (200)

**Auth:** required (owner: ACTIVE/PAUSED/INACTIVE; admin: HIDDEN)
**Body (ChangeOfferStatusBody):**
```python
status: OfferStatus
```

**Logika service (`change_offer_status`):**
1. Pobierz Offer po id → 404 OFFER_NOT_FOUND
2. Sprawdź ownership LUB admin:
   - Owner może: ACTIVE ↔ PAUSED, ACTIVE/PAUSED → INACTIVE
   - Admin może: → HIDDEN (z dowolnego stanu)
   - Inne przejścia → 422 INVALID_STATUS_TRANSITION
3. Sprawdź `current_user.id == offer.user_id` LUB `current_user.role == 'admin'` → 403 NOT_OWNER
4. Jeśli przejście do INACTIVE i istnieją PENDING Exchanges → kaskadowo CANCEL (jak Request cancel w M7)
5. `offer.status = new_status`
6. `db.flush()`, return offer

**Dozwolone przejścia (owner):**

| Z | Do | Efekt |
|---|---|---|
| ACTIVE | PAUSED | Blokuje nowe Exchange (M9 guard) |
| PAUSED | ACTIVE | Odblokuje |
| ACTIVE | INACTIVE | Wycofanie + cancel PENDING Exchanges |
| PAUSED | INACTIVE | Wycofanie + cancel PENDING Exchanges |

**Dozwolone przejścia (admin):**

| Z | Do | Efekt |
|---|---|---|
| * | HIDDEN | Moderacja — ukrycie oferty |

INACTIVE/HIDDEN → ACTIVE: nie dozwolone (trzeba utworzyć nową ofertę).

### 5. `GET /api/v1/offers` (200)

**Auth:** required
**Query params:** identyczne jak M7 GET /requests:
```python
category_id: int | None = None
location_id: int | None = None
location_scope: LocationScope | None = None
status: OfferStatus | None = Query(default=OfferStatus.ACTIVE)
q: str | None = Query(None, max_length=100)
sort: str = Query("created_at", pattern="^(created_at|hearts_asked)$")
order: str = Query("desc", pattern="^(asc|desc)$")
offset: int = Query(0, ge=0)
limit: int = Query(20, ge=1, le=100)
```

**Logika service (`list_offers`):**
1. Base filter: `Offer.status == status_filter` (default ACTIVE)
2. JOIN User, WHERE `User.status == 'active'` — feed filter
3. Filtry: category_id, location_id, location_scope
4. ILIKE search na title + description
5. Sort + order + pagination
6. Return (entries, total)

Identyczny wzorzec jak `list_requests` z M7.

---

## Schemas (`app/schemas/offer.py`)

```python
class CreateOfferBody(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    hearts_asked: int = Field(ge=0, le=50)
    category_id: int
    location_id: int
    location_scope: LocationScope

class UpdateOfferBody(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=2000)
    hearts_asked: int | None = Field(None, ge=0, le=50)

class ChangeOfferStatusBody(BaseModel):
    status: OfferStatus

class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    title: str
    description: str
    hearts_asked: int
    category_id: int
    location_id: int
    location_scope: str
    status: str
    created_at: datetime
    updated_at: datetime

class OfferListResponse(BaseModel):
    entries: list[OfferRead]
    total: int
    offset: int
    limit: int
```

---

## Testy

### Unit testy (`tests/test_offer_service.py`)

Fixture: SQLite in-memory (wzorzec z M7). Tabele: User, Offer, Category, Location, Exchange.

| Test | Opis |
|---|---|
| **Create — happy path** | |
| test_create_offer_valid | Tworzy offer, sprawdza pola, status=ACTIVE |
| **Create — guards** | |
| test_create_category_not_found | → 404 |
| test_create_category_inactive | → 404 |
| test_create_location_not_found | → 404 |
| **Get** | |
| test_get_offer_valid | Pobiera po id |
| test_get_offer_not_found | → 404 |
| test_get_hidden_offer_by_non_owner | → 404 |
| test_get_hidden_offer_by_owner | → 200 |
| test_get_inactive_offer_by_non_owner | → 404 |
| test_get_inactive_offer_by_owner | → 200 |
| **Update — happy path** | |
| test_update_title_only | Partial update |
| test_update_hearts_asked | Zmiana hearts_asked |
| test_update_paused_offer | PAUSED też edytowalna |
| **Update — guards** | |
| test_update_not_owner | → 403 |
| test_update_inactive_offer | → 422 OFFER_NOT_EDITABLE |
| test_update_hidden_offer | → 422 OFFER_NOT_EDITABLE |
| **Status management** | |
| test_status_active_to_paused | ✓ |
| test_status_paused_to_active | ✓ |
| test_status_active_to_inactive | ✓ + cascade PENDING Exchanges |
| test_status_paused_to_inactive | ✓ + cascade |
| test_status_inactive_to_active_rejected | → 422 |
| test_status_hidden_to_active_rejected | → 422 |
| test_status_not_owner | → 403 |
| test_status_admin_can_hide | Admin → HIDDEN z dowolnego stanu |
| test_status_inactive_cascades_exchanges | Exchange PENDING → CANCELLED |
| test_status_inactive_ignores_non_pending | Exchange ACCEPTED untouched |
| **List** | |
| test_list_default_active | Zwraca tylko ACTIVE |
| test_list_search_ilike | q= filtruje po title/description |
| test_list_filter_category | category_id filtr |
| test_list_pagination | offset/limit + total |
| test_list_excludes_suspended_users | User.status=suspended → offer niewidoczna |

~30 unit testów.

### Auth guard testy (`tests/test_offer_api.py`)

| Test | Opis |
|---|---|
| test_create_no_token | POST /offers → 401 |
| test_get_no_token | GET /offers/{id} → 401 |
| test_update_no_token | PATCH /offers/{id} → 401 |
| test_status_no_token | PATCH /offers/{id}/status → 401 |
| test_list_no_token | GET /offers → 401 |

5 auth guard testów.

### Integration testy (`tests/integration/api/test_offer_flow.py`)

| Test | Opis |
|---|---|
| test_create_and_get_offer | Create → Get → verify |
| test_create_and_list | Create 2 → List → verify count |
| test_update_offer | Create → Update title → verify |
| test_status_pause_and_resume | Create → PAUSED → ACTIVE → verify |
| test_status_inactive | Create → INACTIVE → verify, confirm not in list |
| test_list_search | Create 2 → q= → 1 result |

6 integration testów.

**Total: ~41 testów.**

---

## Wzorce do zachowania

1. **flush-only w service, commit w endpoint** — jak M4-M7
2. **Paginacja** — offset/limit/total/entries — konwencja M6-M7
3. **Feed filter** — JOIN User WHERE active
4. **ILIKE search** — wzorzec z M7
5. **Ownership guard** — wzorzec z M7
6. **Status transition validation** — whitelist dozwolonych przejść

---

## Kluczowe decyzje

### Brak hearts_asked lock
W odróżnieniu od Request.hearts_offered, Offer.hearts_asked nie jest "obietnicą" — to oczekiwanie cenowe. Owner może je zmieniać dowolnie. Exchange.hearts_agreed jest ustalane przy tworzeniu Exchange (M9).

### INACTIVE/HIDDEN → nie da się wrócić do ACTIVE
Wycofanie oferty jest nieodwracalne (trzeba utworzyć nową). HIDDEN przez admina — nieodwracalne bez interwencji admina (admin unhide = osobny endpoint w M15 Admin panel).

### PAUSED edytowalna
Owner może edytować title/description/hearts_asked w stanie PAUSED (przygotowanie do ponownej aktywacji).

### INACTIVE cascade
Przejście do INACTIVE kaskadowo anuluje PENDING Exchanges — identyczny wzorzec jak cancel Request w M7.

### Admin status check
`change_offer_status` musi sprawdzić `current_user.role == 'admin'` dla przejścia → HIDDEN. Wymaga to dostępu do `UserRole` z modelu User. Endpoint przekazuje `current_user` do service (nie tylko `current_user.id`).
