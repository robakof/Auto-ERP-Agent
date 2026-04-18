# Serce M15 — Admin: moderation + audit + hearts grant + suspend

**Wejście:** M14 (flags), M6 (hearts), M5 (users), M3 (auth/refresh tokens)
**Rozmiar:** L
**Autor:** Architect

---

## Cel

Panel administracyjny: obsługa zgłoszeń (flags), zawieszanie użytkowników, przyznawanie/zwrot
serc, audyt trail. Każda akcja admina logowana w admin_audit_log.

---

## Stan zastanego kodu

**Już istnieje (model + tabela + migracja):**
- `ContentFlag` z resolution fields (resolved_by, resolution_action, resolution_reason)
- `AdminAuditLog` z JSONB payload
- `SystemConfig`
- `User.role` (USER/ADMIN), `User.status` (ACTIVE/SUSPENDED/DELETED)
- `User.suspended_at`, `suspended_until`, `suspension_reason`
- `RefreshToken.revoked_at`
- `HeartLedgerType.ADMIN_GRANT`, `ADMIN_REFUND`
- Feed queries (request/offer listing) JUŻ filtrują po `User.status == ACTIVE`
- Login/deps JUŻ blokują non-ACTIVE users (403 ACCOUNT_NOT_ACTIVE)

**Brakuje:** require_admin dependency, admin service, admin router, admin schemas, testy, initial admin seed.

---

## Architektura

### Decyzja 1: require_admin dependency

```python
# app/core/deps.py
async def require_admin(ctx: AuthContext = Depends(get_auth_context)) -> User:
    if ctx.user.role != UserRole.ADMIN:
        raise HTTPException(403, "ADMIN_ONLY")
    return ctx.user
```

Wszystkie admin endpointy używają `Depends(require_admin)` zamiast `Depends(get_current_user)`.

### Decyzja 2: Compound flag resolution

`resolve_flag()` jednocześnie:
1. Zmienia status flagi (RESOLVED / DISMISSED)
2. Wykonuje side effect per action (hide content, suspend user, grant refund)
3. Loguje audit

Dlaczego compound: atomowość. Flag mówi "action: SUSPEND_USER" i user JEST zawieszony.
Alternatywa (resolve + osobny call suspend) ryzykuje niespójność.

Side effects per ResolutionAction:

| Action | Side effect |
|---|---|
| DISMISS | flag → DISMISSED, brak side effect |
| WARN_USER | flag → RESOLVED, brak side effect (notification = Faza 2) |
| HIDE_CONTENT | flag → RESOLVED + hide target (Request→HIDDEN, Offer→HIDDEN) |
| SUSPEND_USER | flag → RESOLVED + suspend owner/user + revoke tokens |
| BAN_USER | flag → RESOLVED + suspend permanently (suspended_until=NULL) |
| GRANT_HEARTS_REFUND | flag → RESOLVED + grant hearts to reporter |

Parametry per action (w body jako `params: dict | None`):
- SUSPEND_USER: `{"duration_days": int}` (opcjonalne — NULL = do ręcznego odwieszenia)
- GRANT_HEARTS_REFUND: `{"amount": int}`
- Pozostałe: brak params

### Decyzja 3: Suspend behavior

Zawieszony user:
- Login → 403 ACCOUNT_NOT_ACTIVE (existing)
- Existing JWT → next API call → 403 (deps.py checks status)
- Refresh token → revoked → can't get new token
- Feed queries → auto-hidden (existing JOIN User WHERE ACTIVE)
- **Exchanges trwają** — nie są auto-cancelowane. Drugi participant może cancel.
- Messages/actions → blocked through auth (403 on all protected endpoints)

### Decyzja 4: Initial admin seed

Nowy setting w config: `initial_admin_email: str = ""`
Alembic data migration: jeśli `initial_admin_email` niepusty, UPDATE first matching user SET role=ADMIN.
Alternatywa: management command `py -m app.cli.create_admin --email X` (bezpieczniejsze).

**Wybrany approach**: Management command, nie migracja. Migracja biegnie automatycznie —
admin powinien być tworzony świadomie. CLI script w `app/cli/promote_admin.py`.

### Decyzja 5: Audit log — co logujemy

Każda mutacja admina = 1 wpis w admin_audit_log:

| Action string | Target type | Payload |
|---|---|---|
| `resolve_flag` | FLAG | {resolution_action, resolution_reason, target_type, target_id} |
| `suspend_user` | USER | {reason, duration_days, revoked_tokens_count} |
| `unsuspend_user` | USER | {} |
| `grant_hearts` | USER | {amount, ledger_type, note} |

### Decyzja 6: Suspend nie zmienia error message na login

Obecny kod zwraca `403 ACCOUNT_NOT_ACTIVE` generycznie. Zmiana na specyficzne
`ACCOUNT_SUSPENDED` vs `ACCOUNT_DELETED` to nice-to-have ale wymaga zmiany w auth_service
i deps. **Defer:** nie w scope M15, decyzja kosmetyczna.

---

## Pliki do utworzenia / zmodyfikowania

### Nowe pliki

| Plik | Opis |
|---|---|
| `app/services/admin_service.py` | list_flags, get_flag, resolve_flag, suspend_user, unsuspend_user, grant_hearts, list_audit, _log_audit helper |
| `app/api/v1/admin.py` | Router: 8 endpointów pod /admin |
| `app/schemas/admin.py` | Schemas: Flag list/read/resolve, Suspend/Unsuspend body, GrantHearts body, AuditLog read/list |
| `app/cli/promote_admin.py` | CLI: promote user to admin by email |
| `tests/test_admin_service.py` | Unit testy service |
| `tests/test_admin_api.py` | Auth guard + admin-only testy |

### Modyfikowane pliki

| Plik | Zmiana |
|---|---|
| `app/core/deps.py` | +require_admin dependency |
| `app/config.py` | +initial_admin_email (opcjonalne, dla CLI) |
| `app/api/v1/router.py` | +admin_router |

---

## Admin Service (`app/services/admin_service.py`)

### Flag management

```python
async def list_flags(
    db, *, status: FlagStatus | None, target_type: FlagTargetType | None,
    offset: int = 0, limit: int = 20,
) -> tuple[list[ContentFlag], int]:

async def get_flag(db, flag_id: UUID) -> ContentFlag:

async def resolve_flag(
    db, admin_id: UUID, flag_id: UUID, *,
    action: ResolutionAction, reason: str,
    params: dict | None = None,
) -> ContentFlag:
    """Compound: resolve flag + execute side effect + audit log."""
```

### User management

```python
async def suspend_user(
    db, admin_id: UUID, user_id: UUID, *,
    reason: str, duration_days: int | None = None,
) -> User:
    """Set status=SUSPENDED, revoke all refresh tokens, audit log."""

async def unsuspend_user(
    db, admin_id: UUID, user_id: UUID,
) -> User:
    """Set status=ACTIVE, clear suspension fields, audit log."""
```

### Hearts management

```python
async def grant_hearts(
    db, admin_id: UUID, user_id: UUID, *,
    amount: int, ledger_type: str,  # "ADMIN_GRANT" or "ADMIN_REFUND"
    reason: str,
) -> HeartLedger:
    """Grant/refund hearts + audit log. No from_user (system action)."""
```

### Audit

```python
async def list_audit(
    db, *, actor_id: UUID | None, action: str | None,
    target_type: AuditTargetType | None,
    from_date: datetime | None, to_date: datetime | None,
    offset: int = 0, limit: int = 20,
) -> tuple[list[AdminAuditLog], int]:

async def _log_audit(
    db, admin_id: UUID, action: str,
    target_type: AuditTargetType, target_id: UUID | None,
    payload: dict, reason: str | None = None,
) -> AdminAuditLog:
    """Internal — called by every admin mutation."""
```

---

## Endpointy (Router `app/api/v1/admin.py`)

Prefix: `/admin`

### Flags

**1. `GET /api/v1/admin/flags` (200)**
Auth: require_admin
Query: status, target_type, offset, limit
Response: FlagListResponse

**2. `GET /api/v1/admin/flags/{flag_id}` (200)**
Auth: require_admin
Response: FlagDetailRead (full flag with resolution fields)

**3. `POST /api/v1/admin/flags/{flag_id}/resolve` (200)**
Auth: require_admin
Body: ResolveFlagBody (action: ResolutionAction, reason: str, params: dict | None)
Response: FlagDetailRead

### Users

**4. `POST /api/v1/admin/users/{user_id}/suspend` (200)**
Auth: require_admin
Body: SuspendUserBody (reason: str, duration_days: int | None)
Response: UserAdminRead
Guards: can't suspend admin, can't suspend already suspended

**5. `POST /api/v1/admin/users/{user_id}/unsuspend` (200)**
Auth: require_admin
Response: UserAdminRead
Guards: must be SUSPENDED

### Hearts

**6. `POST /api/v1/admin/hearts/grant` (201)**
Auth: require_admin
Body: GrantHeartsBody (user_id: UUID, amount: int, type: str, reason: str)
Response: HeartLedgerRead (reuse existing schema)
Guards: amount > 0, type IN (ADMIN_GRANT, ADMIN_REFUND), cap check

### Audit

**7. `GET /api/v1/admin/audit` (200)**
Auth: require_admin
Query: actor_id, action, target_type, from_date, to_date, offset, limit
Response: AuditListResponse

---

## Schemas (`app/schemas/admin.py`)

```python
# Flag schemas
class FlagDetailRead(BaseModel):
    """Full flag with resolution fields (admin view)."""
    id, reporter_id, target_type, target_id, reason, description,
    status, resolved_by, resolved_at, resolution_action, resolution_reason,
    created_at

class FlagListResponse(BaseModel):
    entries: list[FlagDetailRead]
    total, offset, limit

class ResolveFlagBody(BaseModel):
    action: ResolutionAction
    reason: str = Field(max_length=1000)
    params: dict | None = None  # action-specific params

# User schemas
class SuspendUserBody(BaseModel):
    reason: str = Field(max_length=1000)
    duration_days: int | None = Field(None, ge=1, le=365)

class UserAdminRead(BaseModel):
    """Admin view — includes suspension details."""
    id, email, username, status, role, suspended_at, suspended_until,
    suspension_reason, heart_balance, created_at

# Hearts schemas
class GrantHeartsBody(BaseModel):
    user_id: UUID
    amount: int = Field(gt=0)
    type: str  # ADMIN_GRANT or ADMIN_REFUND
    reason: str = Field(max_length=1000)

# Audit schemas
class AuditLogRead(BaseModel):
    id, admin_id, action, target_type, target_id, payload, reason, created_at

class AuditListResponse(BaseModel):
    entries: list[AuditLogRead]
    total, offset, limit
```

---

## Promote Admin CLI (`app/cli/promote_admin.py`)

```bash
py -m app.cli.promote_admin --email admin@example.com
```

Synchronous script:
1. Connect to DB
2. Find user by email
3. Set role = ADMIN
4. Print confirmation

Nie migracja Alembic — admin tworzony świadomie przez operatora.

---

## Testy

### Unit testy (`tests/test_admin_service.py`)

| Test | Opis |
|---|---|
| **Flag resolution** | |
| test_resolve_flag_dismiss | DISMISS → DISMISSED, audit log |
| test_resolve_flag_warn | WARN_USER → RESOLVED, audit log |
| test_resolve_flag_hide_request | HIDE_CONTENT → request.status=HIDDEN |
| test_resolve_flag_hide_offer | HIDE_CONTENT → offer.status=HIDDEN |
| test_resolve_flag_suspend | SUSPEND_USER → user suspended + tokens revoked |
| test_resolve_flag_not_found | → 404 |
| test_resolve_flag_already_resolved | → 422 |
| test_resolve_flag_grant_refund | GRANT_HEARTS_REFUND → hearts to reporter |
| **Suspend** | |
| test_suspend_user_valid | status=SUSPENDED, suspended_at set, audit log |
| test_suspend_revokes_tokens | all refresh tokens revoked |
| test_suspend_admin_rejected | can't suspend admin → 422 |
| test_suspend_already_suspended | → 422 |
| test_suspend_not_found | → 404 |
| test_suspend_with_duration | suspended_until calculated |
| **Unsuspend** | |
| test_unsuspend_valid | status=ACTIVE, fields cleared, audit log |
| test_unsuspend_not_suspended | → 422 |
| **Hearts grant** | |
| test_grant_hearts_admin_grant | ADMIN_GRANT, balance increased, audit log |
| test_grant_hearts_admin_refund | ADMIN_REFUND type, audit log |
| test_grant_cap_exceeded | → 422 |
| test_grant_user_not_found | → 404 |
| test_grant_invalid_type | → 422 |
| **Audit log** | |
| test_list_audit_empty | 0 entries |
| test_list_audit_paginated | offset/limit/total |
| test_list_audit_filter_action | filter by action string |
| test_list_audit_filter_target_type | filter by target_type |
| test_list_audit_filter_date | from/to range |
| **Flag listing** | |
| test_list_flags_all | no filter |
| test_list_flags_filter_status | status=open |
| test_list_flags_filter_target_type | target_type=request |
| test_get_flag_valid | full detail |
| test_get_flag_not_found | → 404 |

~30 unit testow.

### Auth guard testy (`tests/test_admin_api.py`)

| Test | Opis |
|---|---|
| test_list_flags_no_token | → 401 |
| test_list_flags_non_admin | → 403 |
| test_resolve_flag_no_token | → 401 |
| test_resolve_flag_non_admin | → 403 |
| test_suspend_no_token | → 401 |
| test_suspend_non_admin | → 403 |
| test_unsuspend_no_token | → 401 |
| test_grant_no_token | → 401 |
| test_grant_non_admin | → 403 |
| test_audit_no_token | → 401 |
| test_audit_non_admin | → 403 |

~11 auth guard testow.

**Total: ~41 testow.**

---

## Kolejnosc implementacji

1. `require_admin` dependency (deps.py) — fundament
2. Schemas (admin.py) — typy
3. admin_service.py: _log_audit helper → list/get flags → resolve_flag (z side effects)
4. admin_service.py: suspend_user, unsuspend_user
5. admin_service.py: grant_hearts
6. admin_service.py: list_audit
7. tests/test_admin_service.py — po każdej grupie
8. Router (admin.py) — 7 endpointów
9. tests/test_admin_api.py — auth guard
10. Router registration
11. CLI promote_admin.py (opcjonalnie — nie blokuje)

---

## Wzorce do zachowania

1. **flush-only w service, commit w router**
2. **require_admin na każdym admin endpoint** — nie get_current_user
3. **Audit log przy KAŻDEJ mutacji** — resolve, suspend, unsuspend, grant
4. **Compound resolve** — atomowe: flag resolved + side effect w jednej TX
5. **Revoke tokens na suspend** — bulk UPDATE refresh_tokens SET revoked_at=now()
6. **404 zamiast 403** dla non-existent resources (security)
7. **Paginacja** — offset/limit/total konwencja

---

## Poza scope M15

- Push notification do usera o suspension (Faza 2)
- WARN_USER email notification (Faza 2)
- Admin dashboard UI (Faza 2)
- BAN_USER as permanent (używamy suspend z duration_days=NULL)
- Unban endpoint (= unsuspend)
- Audit log export (Faza 2)
