# Developer Plan: Serce M4 — Email & Phone Verification + Password Reset

Data: 2026-04-16
Autor: Architect
Dotyczy: `documents/human/plans/serce_faza1_roadmap.md` §M4
Dla roli: Developer
Status: Ready to start
Prerequisites: M3 (auth core) ✓

---

## Cel

Weryfikacja email i telefonu + reset hasła. Po M4 użytkownik:
1. Otrzymuje email z linkiem weryfikacyjnym po rejestracji
2. Może zweryfikować telefon kodem SMS (OTP 6 cyfr)
3. Może zresetować hasło przez email
4. Dostaje INITIAL_GRANT serc przy pierwszej weryfikacji telefonu

**Constraint:** Modele DB (`EmailVerificationToken`, `PhoneVerificationOTP`, `PasswordResetToken`,
`HeartLedger` z partial unique index `INITIAL_GRANT`) już istnieją w schema M1.
M4 = warstwa serwisowa + endpointy + integracja z dostawcami. Zero migracji Alembic.

---

## Co już istnieje

| Komponent | Lokalizacja | Status |
|---|---|---|
| EmailVerificationToken model | `app/db/models/user.py:96-104` | ✓ M1 |
| PhoneVerificationOTP model (attempts, code_hash) | `app/db/models/user.py:107-117` | ✓ M1 |
| PasswordResetToken model | `app/db/models/user.py:73-81` | ✓ M1 |
| HeartLedger + INITIAL_GRANT partial unique index | `app/db/models/heart.py` | ✓ M1 |
| User.email_verified, phone_verified | `app/db/models/user.py:27,31` | ✓ M1 |
| security.py (hash_token, create_refresh_token pattern) | `app/core/security.py` | ✓ M3 |
| auth_service.py (register, login flow) | `app/services/auth_service.py` | ✓ M3 |
| Settings (initial_heart_grant=5) | `app/config.py:26` | ✓ M1 |

---

## Scope — co dokładnie powstaje

### 1. Email service: `app/services/email_service.py` (NOWY)

```python
from typing import Protocol

class EmailService(Protocol):
    async def send_verification(self, to: str, token: str) -> None: ...
    async def send_password_reset(self, to: str, token: str) -> None: ...

class ResendEmailService:
    """Production — Resend.com API."""
    def __init__(self, api_key: str, from_email: str): ...
    async def send_verification(self, to, token): ...
    async def send_password_reset(self, to, token): ...

class MockEmailService:
    """Test/dev — stores sent emails in memory."""
    sent: list[dict]
    async def send_verification(self, to, token):
        self.sent.append({"type": "verification", "to": to, "token": token})
    async def send_password_reset(self, to, token):
        self.sent.append({"type": "reset", "to": to, "token": token})
```

**Konfiguracja w Settings:**
```python
# Email (Resend.com)
resend_api_key: str = ""
email_from: str = "noreply@serce.app"
email_verification_url: str = "http://localhost:3000/verify-email"
password_reset_url: str = "http://localhost:3000/reset-password"
```

**DI:** `get_email_service()` dependency — MockEmailService gdy `resend_api_key` pusty, ResendEmailService w prod.

### 2. SMS service: `app/services/sms_service.py` (NOWY)

```python
class SmsService(Protocol):
    async def send_otp(self, phone_number: str, code: str) -> None: ...

class SmsApiService:
    """Production — SMSAPI.pl."""
    def __init__(self, api_token: str, sender_name: str): ...
    async def send_otp(self, phone_number, code): ...

class MockSmsService:
    """Test/dev — stores sent SMS in memory."""
    sent: list[dict]
    async def send_otp(self, phone_number, code):
        self.sent.append({"phone": phone_number, "code": code})
```

**Konfiguracja w Settings:**
```python
# SMS (SMSAPI.pl)
smsapi_token: str = ""
smsapi_sender: str = "Serce"
```

**DI:** analogicznie — MockSmsService gdy `smsapi_token` pusty.

### 3. Verification service: `app/services/verification_service.py` (NOWY)

Cała logika weryfikacji w osobnym service (nie w auth_service — SRP).

**Endpointy + logika:**

| Endpoint | Logika |
|---|---|
| `POST /auth/verify-email` `{token}` | Znajdź EmailVerificationToken po hash, sprawdź expiry + used_at, ustaw used_at, ustaw User.email_verified=True |
| `POST /auth/resend-verification-email` | Rate: 3/email/24h (query COUNT w tabeli). Unieważnij stare (ustaw used_at), stwórz nowy token, wyślij email |
| `POST /auth/send-phone-otp` `{phone_number}` | Validate format (+48...). Stwórz 6-digit OTP, hash do DB, wyślij SMS. Max 3 aktywne OTP per user. |
| `POST /auth/verify-phone` `{phone_number, code}` | Znajdź OTP po hash, sprawdź expiry + attempts < 5 + used_at. Increment attempts przy błędzie. Przy sukcesie: used_at, User.phone_verified=True, User.phone_number=phone, **trigger INITIAL_GRANT** |
| `POST /auth/forgot-password` `{email}` | Stwórz PasswordResetToken, wyślij email z linkiem. Nie ujawniaj czy email istnieje (zawsze 200). |
| `POST /auth/reset-password` `{token, new_password}` | Znajdź token po hash, sprawdź expiry + used_at. Ustaw used_at, zmień password_hash. Revoke ALL refresh tokens (force re-login). |

### 4. INITIAL_GRANT logic

Przy pierwszej weryfikacji telefonu:

```python
async def _grant_initial_hearts(db: AsyncSession, user_id: UUID) -> None:
    """Grant initial hearts on first phone verification. Idempotent."""
    # Check application-level (DB partial unique handles race)
    existing = await db.execute(
        select(HeartLedger).where(
            HeartLedger.to_user_id == user_id,
            HeartLedger.type == HeartLedgerType.INITIAL_GRANT,
        )
    )
    if existing.scalar_one_or_none():
        return  # already granted

    db.add(HeartLedger(
        to_user_id=user_id,
        amount=settings.initial_heart_grant,  # 5
        type=HeartLedgerType.INITIAL_GRANT,
        note="Phone verification",
    ))
    # Update user balance
    user = await db.get(User, user_id)
    user.heart_balance += settings.initial_heart_grant
    # DB constraint ck_heart_ledger_amount_positive + partial unique index
    # handle race conditions at DB level
```

**Guard:** Partial unique index `uix_heart_ledger_initial_grant` (z M1) = DB-level gwarancja jednorazowości. Aplikacyjny check = graceful (nie IntegrityError w happy path).

### 5. Auto-send verification email on register

Rozszerz `register_user` w auth_service.py:
```python
# Po create user + consents:
token = await verification_service.create_email_verification(db, user.id, user.email)
await email_service.send_verification(user.email, token)
```

### 6. Endpointy: `app/api/v1/auth.py` (rozszerzenie)

Dodaj 6 endpointów do istniejącego auth router:

```python
@router.post("/verify-email", response_model=MessageResponse)
@router.post("/resend-verification-email", response_model=MessageResponse)
@limiter.limit("3/hour")
@router.post("/send-phone-otp", response_model=MessageResponse)
@limiter.limit("5/hour")
@router.post("/verify-phone", response_model=MessageResponse)
@limiter.limit("10/hour")
@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/hour")
@router.post("/reset-password", response_model=MessageResponse)
```

**Rate limits:**
| Endpoint | Limit | Uzasadnienie |
|---|---|---|
| resend-verification-email | 3/hour per IP | Anti-spam |
| send-phone-otp | 5/hour per IP | Koszt SMS |
| verify-phone | 10/hour per IP | Brute-force OTP |
| forgot-password | 3/hour per IP | Anti-spam |

### 7. Schemas: `app/schemas/auth.py` (rozszerzenie)

```python
class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class SendPhoneOtpRequest(BaseModel):
    phone_number: str = Field(pattern=r"^\+48\d{9}$")

class VerifyPhoneRequest(BaseModel):
    phone_number: str = Field(pattern=r"^\+48\d{9}$")
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
```

---

## Decyzje zatwierdzone

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| Email provider | Resend.com (httpx async) | Proste API, darmowy tier wystarczy na start |
| SMS provider | SMSAPI.pl (httpx async) | Polski provider, wymagany do +48 |
| OTP format | 6 cyfr, hash w DB | Industry standard, brute-force resistant z attempts limit |
| OTP max attempts | 5 | Balans UX vs security |
| OTP expiry | 10 minut | Standard |
| Email token expiry | 24h | Wystarczające na opóźniony dostęp do email |
| Password reset token expiry | 1h | Krótki — security first |
| Resend rate | 3/email/24h per email address | Anti-spam (liczone per email, nie per user) |
| INITIAL_GRANT trigger | Phone verification (nie email) | Decyzja #8 z roadmap — phone = real person gate |
| Protocol + DI pattern | EmailService/SmsService protocol + mock | Testable, zero real calls w testach |
| Verification service | Osobny moduł (nie w auth_service) | SRP — auth_service = login/register/tokens, verification_service = verify flows |
| forgot-password response | Zawsze 200 OK | Nie ujawniaj czy email istnieje (security) |
| reset-password side-effect | Revoke ALL refresh tokens | Force re-login na wszystkich urządzeniach |
| Alembic migrations | Zero — schema z M1 | Modele już istnieją, wystarczy warstwa serwisowa |

---

## Konfiguracja Settings (rozszerzenie config.py)

```python
# Email (Resend.com)
resend_api_key: str = ""
email_from: str = "noreply@serce.app"
email_verification_url: str = "http://localhost:3000/verify-email"
password_reset_url: str = "http://localhost:3000/reset-password"
email_verification_expire_hours: int = 24
password_reset_expire_minutes: int = 60

# SMS (SMSAPI.pl)
smsapi_token: str = ""
smsapi_sender: str = "Serce"
phone_otp_expire_minutes: int = 10
phone_otp_max_attempts: int = 5
```

Pusty `resend_api_key` / `smsapi_token` = mock mode (dev/test). Analogicznie do hCaptcha pattern z M3.

---

## Testy

### Unit: `tests/test_verification_service.py` (NOWY)

```
test_create_email_verification_token()
test_verify_email_valid_token()
test_verify_email_expired_token()
test_verify_email_already_used()
test_resend_email_creates_new_token()
test_resend_email_rate_limit_exceeded()
test_create_phone_otp()
test_verify_phone_valid_code()
test_verify_phone_wrong_code_increments_attempts()
test_verify_phone_max_attempts_exceeded()
test_verify_phone_expired_otp()
test_verify_phone_triggers_initial_grant()
test_initial_grant_idempotent()
test_forgot_password_creates_token()
test_forgot_password_nonexistent_email_no_error()
test_reset_password_valid_token()
test_reset_password_expired_token()
test_reset_password_revokes_all_refresh_tokens()
```
Minimum: **≥18 unit**

### Unit: `tests/test_email_service.py` (NOWY)

```
test_mock_email_service_stores_sent()
test_resend_service_calls_api() (mock httpx)
```
Minimum: **≥2 unit**

### Unit: `tests/test_sms_service.py` (NOWY)

```
test_mock_sms_service_stores_sent()
test_smsapi_service_calls_api() (mock httpx)
test_otp_generation_6_digits()
```
Minimum: **≥3 unit**

### Unit: `tests/test_auth_api.py` (rozszerzenie)

```
test_verify_email_no_token_body()
test_verify_phone_invalid_format()
test_forgot_password_no_body()
test_reset_password_short_password()
test_send_phone_otp_invalid_number()
```
Minimum: **≥5 nowych**

### Integration: `tests/integration/api/test_verification_flow.py` (NOWY)

```
test_register_sends_verification_email()
test_verify_email_activates_flag()
test_resend_verification_email()
test_phone_otp_flow_and_initial_grant()
test_forgot_password_and_reset()
test_reset_password_force_relogin()
```
Minimum: **≥6 integration** (require Postgres + mock email/sms)

### Minimum testów

- Verification service: ≥18
- Email service: ≥2
- SMS service: ≥3
- Auth API (endpoint validation): ≥5 nowych
- Integration: ≥6
- **Total nowych: ≥34**
- **Suite total: ≥84** (50 z M1-M3 + 34 nowych)

---

## Out of scope (świadomie)

- **Real Resend.com / SMSAPI.pl integration test** — mock wystarczy, real = ręczne na staging
- **Email templates (HTML)** — plain text na start, HTML w przyszłości
- **Phone number normalization** (np. 0048 → +48) — Pydantic regex `^\+48\d{9}$` wystarczy
- **Magic link login** — osobny scope (M5 lub later)
- **2FA / TOTP** — osobny scope, nie w roadmapie fazy 1

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Resend.com / SMSAPI.pl niedostępne | Mock mode (pusty api_key) + retry w przyszłości |
| OTP brute-force (6 cyfr = 1M combinations) | Max 5 attempts + 10min expiry + rate limit 10/h per IP |
| Race condition INITIAL_GRANT | Partial unique index DB-level + aplikacyjny check |
| Email spoofing (ktoś weryfikuje cudzy email) | Token SHA-256 hash, 48 bytes entropy — nie do zgadnięcia |
| Resend rate bypass (zmiana IP) | Per-email counting (nie per IP) — 3 aktywne tokeny per email/24h |

---

## Kolejność pracy (rekomendacja)

1. **Settings** rozszerzenie (email/sms config) — 0 ryzyka, czysta konfiguracja
2. **email_service.py + sms_service.py** (Protocol + Mock + Prod impl) + unit testy
3. **verification_service.py** (cała logika: email verify, phone OTP, password reset, INITIAL_GRANT) + unit testy
4. **Schemas** rozszerzenie (6 nowych request models)
5. **auth.py** endpointy (6 nowych) + rozszerzenie register (auto-send verification email)
6. **Integration testy** (full flow z mock email/sms)
7. Verify: `py -m pytest tests/ -q --ignore=tests/integration` → ≥84 PASS

---

## Workflow i handoff

Developer realizuje przez `workflow_developer_tool`.

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "serce_m4_review" --status PASS \
  --summary "M4: email/phone verification + password reset + INITIAL_GRANT. 84+ tests PASS." \
  --next-action "Code review — verification_service, email/sms services, auth endpoints, INITIAL_GRANT"
```
