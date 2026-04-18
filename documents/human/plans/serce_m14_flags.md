# Serce M14 — Flag endpoints + ContentFlag

**Wejście:** M7 (requests), M8 (offers), M9 (exchanges), M5 (users)
**Rozmiar:** S
**Autor:** Architect

---

## Cel

Użytkownik może zgłosić naruszenie (flag) na 4 typach zasobów: Request, Offer, Exchange, User.
Flagi trafiają do bazy (status OPEN) — admin je obsługuje w M15. M14 to wyłącznie user-facing
endpoints do tworzenia zgłoszeń.

---

## Stan zastanego kodu

Model `ContentFlag` **już istnieje** (`app/db/models/admin.py`) z pełnym zestawem enum:
`FlagTargetType`, `FlagReason`, `FlagStatus`, `ResolutionAction`.
Tabela `content_flags` **już istnieje** w migracji initial. Nie potrzeba nowej migracji Alembic.

Brakuje: service, router, schemas.

---

## Architektura

### Decyzja 1: Routing — per-resource vs unified

**Wybór: Per-resource POST w jednym `flags.py` router, wspólna logika w service.**

4 endpointy route → 1 service function `create_flag(db, reporter, target_type, target_id, ...)`.

```
POST /api/v1/requests/{id}/flag
POST /api/v1/offers/{id}/flag
POST /api/v1/exchanges/{id}/flag
POST /api/v1/users/{id}/flag
```

Alternatywy:
- (A) Unified `POST /flags` z target_type + target_id w body — prostsze, ale gorsze REST semantics
- (B) Dodanie do istniejących routerów (requests.py, offers.py, ...) — rozproszenie flag logic

Trade-off: 4 thin route handlers (3-4 linie każdy) → DRY przez wspólny service. Czytelne OpenAPI docs.

### Decyzja 2: Walidacja target + self-flag prevention

Per target_type:

| Target | Validate exists | Self-flag rule |
|---|---|---|
| REQUEST | `db.get(Request, id)` → 404 | reporter != request.user_id → 422 CANNOT_FLAG_OWN |
| OFFER | `db.get(Offer, id)` → 404 | reporter != offer.user_id → 422 CANNOT_FLAG_OWN |
| EXCHANGE | `db.get(Exchange, id)` → 404 | reporter IN (requester_id, helper_id) — participant only → 403 NOT_PARTICIPANT |
| USER | `db.get(User, id)` → 404, status=ACTIVE | reporter != target_id → 422 CANNOT_FLAG_OWN |

**Exchange jest wyjątkiem:** tutaj reporter MUSI być participantem (dispute mechanism).
Nie-participant nie powinien znać exchange_id → 404 (nie 403).

### Decyzja 3: Duplicate flag prevention

Application-level check: jeden OPEN flag per (reporter_id, target_type, target_id).
Jeśli istnieje → 422 ALREADY_FLAGGED.

Brak partial unique index w DB (można dodać w przyszłości). Wystarczy query check w service.

### Decyzja 4: Messages — bez osobnego endpointu

Roadmapa: "Messages przez Exchange (opis w reason)". Użytkownik flaguje Exchange
i opisuje problematyczną wiadomość w polu `description`.

`FlagTargetType.MESSAGE` w enum — zarezerwowany dla admin use w M15
(admin może flagować konkretną wiadomość wewnętrznie).

### Decyzja 5: Notifications

M14 nie generuje notyfikacji. Flagi idą do admina — admin notifications to scope M15.

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/flag_service.py` | create_flag (z target dispatch + validation) |
| `app/api/v1/flags.py` | Router: 4 endpointy POST per resource type |
| `app/schemas/flag.py` | CreateFlagBody, FlagRead |
| `tests/test_flag_service.py` | Unit testy service |
| `tests/test_flag_api.py` | Auth guard testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/api/v1/router.py` | Dodaj `flags_router` |

---

## Flag Service (`app/services/flag_service.py`)

```python
async def create_flag(
    db: AsyncSession,
    reporter_id: UUID,
    target_type: FlagTargetType,
    target_id: UUID,
    *,
    reason: FlagReason,
    description: str | None = None,
) -> ContentFlag:
    """Create flag. Validates target exists + self-flag prevention + duplicate check."""

    # 1. Duplicate check
    existing = ... WHERE reporter_id=X AND target_type=Y AND target_id=Z AND status=OPEN
    if exists → 422 ALREADY_FLAGGED

    # 2. Target validation + self-flag prevention (dispatch per target_type)
    if target_type == REQUEST:
        req = await db.get(Request, target_id) → 404
        if reporter_id == req.user_id → 422 CANNOT_FLAG_OWN_RESOURCE
    elif target_type == OFFER:
        offer = await db.get(Offer, target_id) → 404
        if reporter_id == offer.user_id → 422 CANNOT_FLAG_OWN_RESOURCE
    elif target_type == EXCHANGE:
        ex = await db.get(Exchange, target_id) → 404
        if reporter_id not in (ex.requester_id, ex.helper_id) → 404 (hide existence)
    elif target_type == USER:
        user = await db.get(User, target_id) → 404
        if user.status != ACTIVE → 404
        if reporter_id == target_id → 422 CANNOT_FLAG_OWN_RESOURCE

    # 3. Create flag
    flag = ContentFlag(reporter_id=reporter_id, target_type=target_type, ...)
    db.add(flag)
    await db.flush()
    return flag
```

---

## Endpointy (Router `app/api/v1/flags.py`)

### 1. `POST /api/v1/requests/{target_id}/flag` (201)

**Auth:** required
**Rate limit:** 10/hour (prevents flag spam)
**Body:** `CreateFlagBody` (reason: FlagReason, description: str | None)
**Response:** `FlagRead`

### 2. `POST /api/v1/offers/{target_id}/flag` (201)

Identyczny pattern, target_type=OFFER.

### 3. `POST /api/v1/exchanges/{target_id}/flag` (201)

Identyczny pattern, target_type=EXCHANGE.
Guard: reporter must be participant (enforced in service).

### 4. `POST /api/v1/users/{target_id}/flag` (201)

Identyczny pattern, target_type=USER.

### Router pattern (DRY)

```python
router = APIRouter(tags=["flags"])

@router.post("/requests/{target_id}/flag", response_model=FlagRead, status_code=201)
@limiter.limit("10/hour")
async def flag_request(
    request: FastAPIRequest,
    target_id: UUID,
    body: CreateFlagBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await flag_service.create_flag(
        db, current_user.id, FlagTargetType.REQUEST, target_id,
        reason=body.reason, description=body.description,
    )
    await db.commit()
    return result

# Analogicznie: flag_offer, flag_exchange, flag_user
```

---

## Schemas (`app/schemas/flag.py`)

```python
class CreateFlagBody(BaseModel):
    reason: str       # FlagReason enum value: spam, scam, abuse, inappropriate, other
    description: str | None = Field(None, max_length=1000)

class FlagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID | None
    target_type: str
    target_id: UUID
    reason: str
    description: str | None
    status: str
    created_at: datetime
```

`FlagRead` nie zwraca resolution fields (resolved_by, resolution_action) — te pola to scope admin M15.

---

## Testy

### Unit testy (`tests/test_flag_service.py`)

| Test | Opis |
|---|---|
| **Create flag** | |
| test_flag_request_valid | Flag na request → 201, FlagTargetType.REQUEST |
| test_flag_offer_valid | Flag na offer → 201, FlagTargetType.OFFER |
| test_flag_exchange_valid | Flag na exchange (participant) → 201 |
| test_flag_user_valid | Flag na user → 201 |
| **Self-flag prevention** | |
| test_flag_own_request_rejected | Owner flags own request → 422 CANNOT_FLAG_OWN_RESOURCE |
| test_flag_own_offer_rejected | Owner flags own offer → 422 |
| test_flag_self_rejected | User flags self → 422 |
| **Exchange special rules** | |
| test_flag_exchange_non_participant | Non-participant → 404 (not 403) |
| **Target validation** | |
| test_flag_nonexistent_request | → 404 |
| test_flag_nonexistent_user | → 404 |
| test_flag_suspended_user | → 404 (hidden) |
| **Duplicate prevention** | |
| test_flag_duplicate_rejected | Second OPEN flag on same target → 422 ALREADY_FLAGGED |
| test_flag_after_resolved_allowed | Resolved flag → new flag OK |

~13 unit testow.

### Auth guard testy (`tests/test_flag_api.py`)

| Test | Opis |
|---|---|
| test_flag_request_no_token | → 401 |
| test_flag_offer_no_token | → 401 |
| test_flag_exchange_no_token | → 401 |
| test_flag_user_no_token | → 401 |

4 auth guard testow.

**Total: ~17 testow.**

---

## Wzorce do zachowania

1. **flush-only w service, commit w router**
2. **404 dla non-existent targets** — nie ujawniaj istnienia (Exchange → 404, nie 403 dla non-participant)
3. **Application-level duplicate check** — query przed INSERT
4. **Rate limit 10/hour** — zapobiega flag spam
5. **Brak notifications** — flagi idą cicho do bazy, admin obsługuje w M15

---

## Kolejnosc implementacji

1. Schemas (flag.py) — CreateFlagBody, FlagRead
2. flag_service.py — create_flag z target dispatch
3. tests/test_flag_service.py — unit testy
4. Router (flags.py) — 4 endpoints
5. tests/test_flag_api.py — auth guard
6. Router registration (router.py)

---

## Poza scope M14

- Admin flag management: list, resolve, dismiss (M15)
- Admin audit log entry on flag creation (M15)
- Notification do admina o nowym flag (M15)
- Message-level flagging endpoint (M15 — admin may flag individual messages)
- Flag stats / dashboard (Faza 2)
