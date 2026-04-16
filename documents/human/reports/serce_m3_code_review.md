# Code Review: Serce M3 — Auth Core (register, login, refresh, logout, sessions)

Date: 2026-04-16
Reviewer: Architect
Branch: main (commit c031507)
Handoff: msg #107 + #108 (developer → architect)
Plan: M3 auth jako 3. milestone roadmap Serce

## Summary

**Overall assessment: PASS**
**Code maturity level: L3 Senior** — clean separation (security.py pure crypto, deps.py pure guards, auth_service.py business logic, auth.py thin router), refresh token rotation z SHA-256 hash (raw to client only), bcrypt direct (nie passlib — correct choice), session_id w JWT payload dla guard, DI via FastAPI Depends, structured error codes (INVALID_CREDENTIALS, EMAIL_TAKEN, etc.), hCaptcha z graceful no-op w dev.

**Tests:** 45/45 PASS (unit). 20 integration (wymagają Postgres).

**Acceptance criteria vs deliverable:**

| Criterium | Status |
|---|---|
| POST /auth/register (email, username, password, tos, captcha) | ✓ |
| POST /auth/login → access + refresh tokens | ✓ |
| POST /auth/refresh → token rotation | ✓ |
| POST /auth/logout (single session) | ✓ |
| POST /auth/logout-all (revoke all) | ✓ |
| GET /auth/sessions (list active) | ✓ |
| DELETE /auth/sessions/{id} (revoke specific, guard current) | ✓ |
| POST /auth/accept-terms (tos / privacy_policy) | ✓ |
| GET /auth/me (current user) | ✓ |
| Rate limiting (register 5/h, login 10/min, refresh 20/min) | ✓ |
| hCaptcha on register (skip in dev) | ✓ |
| Disposable email denylist | ✓ |
| CANNOT_REVOKE_CURRENT_SESSION guard | ✓ |
| SystemConfig seed migration (tos/privacy versions) | ✓ |

## Decyzje developera — ocena

### bcrypt direct (nie passlib) → **APPROVE**
passlib ma znane problemy kompatybilności z bcrypt>=4.0. Direct bcrypt = mniej zależności, mniej ryzyka. `hash_password` / `verify_password` to 2 linie — nie potrzeba wrapper library.

### JWT payload z session_id ("sid") → **APPROVE**
Potrzebne dla guard CANNOT_REVOKE_CURRENT_SESSION. Alternative: lookup w DB per request (wolniejsze). JWT to stateless źródło prawdy o sesji — correct trade-off.

### AuthContext dataclass → **APPROVE**
Rozszerzenie `get_current_user` o `session_id` bez łamania istniejących endpointów (M2 locations/categories). `get_current_user` deleguje do `get_auth_context` → backward-compatible. Clean DI.

### hCaptcha no-op w dev → **APPROVE**
`_HCAPTCHA_SECRET` empty → skip. Prosty guard, zero risk w prod (secret wymagany). Lazy import `httpx` tylko gdy captcha aktywna.

### Refresh token rotation (SHA-256 hash w DB) → **APPROVE**
Industry standard: raw do klienta, hash w DB. `secrets.token_urlsafe(48)` = 384 bits entropy. Stary token revokowany przy każdym refresh. Replay old token → 401.

### Rate limit na `get_remote_address` → **APPROVE z uwagą** (patrz W1)

## Findings

### Critical Issues (must fix)

**C1: `secret_key` default w config.py = "change-me-to-random-32-char-string"**

`serce/backend/app/config.py:16`:
```python
secret_key: str = "change-me-to-random-32-char-string"
```

Default jest human-readable placeholder. Jeśli `.env` nie ustawia `SECRET_KEY` (typo, brak pliku, pusta wartość) → produkcja działa z publicznym kluczem. Każdy może generować valid JWT.

**Fix:** Walidacja w `Settings` — brak/default → crash na starcie:
```python
@model_validator(mode="after")
def _validate_secret(self):
    if self.secret_key == "change-me-to-random-32-char-string":
        if self.env not in ("development", "test"):
            raise ValueError("SECRET_KEY must be set in production")
    return self
```
Albo prościej: `secret_key: str` bez default (wymusza .env).

### Warnings (should fix)

**W1: Rate limit za reverse proxy — `get_remote_address` widzi proxy IP, nie klienta**

`serce/backend/app/core/rate_limit.py:13`:
```python
limiter = Limiter(key_func=get_remote_address)
```

Za nginx/Caddy `request.client.host` = `127.0.0.1` → wszyscy użytkownicy dzielą jeden bucket. Rate limit nie działa.

**Fix:** Konfigurowalny `key_func`:
```python
def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

limiter = Limiter(key_func=_get_client_ip)
```

Plus trusted proxy config (accept X-Forwarded-For only from known IPs). Na start wystarczy X-Forwarded-For z informacją w docs/deploy.

**W2: `document_version="1.0"` hardcoded w `register_user`**

`serce/backend/app/services/auth_service.py:77`:
```python
db.add(UserConsent(
    user_id=user.id,
    document_type=doc_type,
    document_version="1.0",
    ip_address=ip_address,
))
```

Wersja hardcoded — po update TOS do "2.0" w SystemConfig, register nadal zapisze "1.0". Powinno czytać z SystemConfig (jak robi `accept_terms`).

**Fix:** Przed pętlą consents w `register_user`:
```python
tos_ver = await _get_current_version(db, "tos_current_version")
pp_ver = await _get_current_version(db, "privacy_current_version")
```

**W3: `_client_ip` w auth.py nie obsługuje X-Forwarded-For**

`serce/backend/app/api/v1/auth.py:29-30`:
```python
def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
```

Analogicznie do W1 — za proxy IP klienta nie jest widoczne. `ip_address` w `UserConsent`, `RefreshToken` będzie `127.0.0.1`. Wartość audytowa = zero.

**Fix:** Wydzielić jedną utility `get_client_ip(request)` i użyć w rate_limit.py i auth.py.

### Suggestions (nice to have)

**S1: Email denylist — 35 domen wystarczy na start**

Pytanie developera "czy 35 wystarczy" — tak, na start. Ale warto dodać TODO: external denylist (np. disposable-email-domains npm/pypi package) gdy user base >1000. Frozenset in-code jest OK dopóki lista jest krótka.

**S2: `password_hash: String(60)` — tight dla bcrypt**

`serce/backend/app/db/models/user.py:29`:
```python
password_hash: Mapped[str] = mapped_column(String(60), nullable=False)
```

bcrypt output = 60 chars. Ale jeśli przejdziemy na argon2 w przyszłości → hash dłuższy (~97 chars). `String(128)` daje zapas bez kosztu.

**S3: `test_register_disposable_email` — test przechodzi ale nie sprawdza detail**

`serce/backend/tests/test_auth_api.py:62-70` — sprawdza `status_code == 422` ale nie `detail == "DISPOSABLE_EMAIL"`. Jeśli walidacja Pydantic odrzuci wcześniej (np. z innego powodu), test przejdzie false-positive.

**S4: `logout` endpoint nie wymaga auth**

`serce/backend/app/api/v1/auth.py:77-82` — `POST /auth/logout` przyjmuje refresh_token w body, bez auth header. To poprawne (client może nie mieć valid access token), ale warto udokumentować tę decyzję (public endpoint, anyone with refresh token can revoke it).

## Architecture Assessment

### Module boundaries

```
app/api/v1/auth.py (thin router — 130L, zero business logic)
    ↓ Depends
app/core/deps.py (AuthContext — JWT decode + user load + status check)
app/core/security.py (pure crypto — bcrypt, JWT, SHA-256)
app/core/captcha.py (hCaptcha — async httpx, no-op in dev)
app/core/email_denylist.py (frozenset lookup)
app/core/rate_limit.py (slowapi singleton)
    ↓ service
app/services/auth_service.py (business logic — 305L, 8 functions)
    ↓ models
app/db/models/user.py (User, RefreshToken, consents, tokens)
app/db/models/admin.py (SystemConfig)
    ↓ schemas
app/schemas/auth.py (request/response validation)
app/schemas/session.py, user.py (read models)
```

Router = wiring. Service = business logic. Security = pure crypto. **Correct layering.**

### Pattern compliance

| Pattern | Status |
|---|---|
| Thin Router / Fat Service | ✓ Router = 130L wiring, service = 305L logic |
| DI for Testability | ✓ FastAPI Depends throughout |
| Token Rotation | ✓ Revoke old + issue new on refresh |
| Hash at Rest | ✓ SHA-256 for refresh/verification tokens, bcrypt for password |
| Fail-Fast Auth | ✓ deps.py checks status, raises 401/403 immediately |
| Rate Limit at Boundary | ✓ Decorator on endpoint, not in service |
| Consent Audit Trail | ✓ UserConsent with IP, version, timestamp |

### Anti-pattern check

| Anti-pattern | Status |
|---|---|
| Timing Attack on Login | ⚠ `verify_password` uses bcrypt.checkpw (constant-time), BUT `select User` + `if not user` short-circuits before password check → timing leak reveals email existence. See Note below. |
| Token in URL | ✓ Clean — tokens in body/header only |
| Mixed Responsibilities | ✓ Clean — no crypto in router, no DB in security |
| Silent Failure | ✓ Clean — structured error codes |

**Note on timing attack:** `login_user` returns 401 INVALID_CREDENTIALS for both "user not found" and "wrong password" (same error code — good). But DB query duration for existing vs non-existing user differs. In practice: low risk for this app type, but worth noting. Mitigation: dummy `verify_password` call when user not found. Non-blocking.

## Test Coverage Analysis

| File | Tests | Description | Status |
|---|---|---|---|
| test_security.py | 9 | bcrypt, JWT, refresh token, hash | ✓ |
| test_auth_api.py | 12 | Endpoint validation (no DB) | ✓ |
| test_email_denylist.py | 6 | Denylist lookup + case | ✓ |
| test_captcha.py | 5 | hCaptcha mock (skip/required/valid/invalid) | ✓ |
| test_models.py | existing | Model sanity | ✓ |
| test_migration.py | existing | Alembic chain | ✓ |
| **Unit total** | **45** | | ✓ |
| integration/api/test_auth_flow.py | 20 | Full flow (register→login→refresh→logout→sessions→revoke) | ✓ (requires Postgres) |

**Unit test quality:** Solidne. Covers happy + edge cases. JWT expired, invalid, missing session_id, bcrypt salt uniqueness, refresh token uniqueness, disposable email case insensitivity, captcha mock/skip/valid/invalid.

**Integration test quality:** Solidne. Full CRUD flow: register duplicate email/username, login valid/wrong/nonexistent, me with token, refresh rotation + old rejected, logout single + all, sessions list, accept-terms already-accepted, revoke current blocked, revoke other succeeds.

## Odpowiedzi na otwarte pytania developera

### Q1: Rate limit za reverse proxy — trusted proxies?
Tak — patrz W1. Wydziel `get_client_ip` z X-Forwarded-For. Na start wystarczy bez trusted proxy config, z informacją w docs/deploy. Pełna konfiguracja (whitelist proxy IPs) w M4+ jeśli potrzebna.

### Q2: Email denylist — 35 domen wystarczy?
Tak na start. Patrz S1 — rozszerzaj gdy user base > 1000. Nie inwestuj w external package teraz.

### Q3: Consent version "1.0" hardcoded?
Powinno czytać z SystemConfig — patrz W2. To jest **should fix**, nie nice-to-have. Gdy TOS się zmieni, register będzie logował starą wersję.

## Recommended Actions

### Must fix (before merge):

- [ ] **C1:** SECRET_KEY — walidacja w Settings (crash w prod gdy default)

### Should fix:

- [ ] **W1:** `get_client_ip` z X-Forwarded-For (rate limit + audit IP)
- [ ] **W2:** `register_user` — czytaj consent version z SystemConfig
- [ ] **W3:** `_client_ip` w auth.py — użyj wspólnego `get_client_ip`

### Nice to have:

- [ ] S2: `password_hash String(128)` zapas na argon2
- [ ] S3: `test_register_disposable_email` — assert detail
- [ ] S4: Udokumentuj decyzję: POST /logout public (no auth header)

## Verdict

**PASS** (z C1 do naprawienia przed deploy na prod).

M3 to kompletny auth core: 9 endpointów, refresh token rotation, bcrypt + JWT, session management z guard CANNOT_REVOKE_CURRENT_SESSION, hCaptcha, disposable email denylist, rate limiting. Layering poprawny (thin router / fat service / pure crypto). 45 unit + 20 integration testów. Jeden critical: SECRET_KEY default w prod. Trzy warnings: X-Forwarded-For (rate limit + audit), consent version hardcoded, shared `get_client_ip` utility.

**Next:** C1 fix → re-verify → M4 planning.
