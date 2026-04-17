# Developer Plan: Serce M5 — User Profile + Email/Phone Change

Data: 2026-04-17
Autor: Architect
Dotyczy: `documents/human/plans/serce_faza1_roadmap.md` §M5
Dla roli: Developer
Status: Ready to start
Prerequisites: M4 (email/phone verification) ✓

---

## Cel

Profil użytkownika + zmiana email/phone/username. Po M5 użytkownik:
1. Widzi pełny profil (`/me` rozszerzony o bio, location, phone_number)
2. Edytuje bio i lokalizację
3. Zmienia username (unique check)
4. Zmienia email (hasło + token 24h + powiadomienie na stary email)
5. Zmienia telefon (hasło + OTP nowy numer, BEZ ponownego INITIAL_GRANT)

**Constraint:** Model `EmailChangeToken` już istnieje w schema M1 (`user.py:84-93`).
Zero nowych migracji Alembic. Nowy router `users.py`, nowy service `profile_service.py`.

---

## Co już istnieje

| Komponent | Lokalizacja | Status |
|---|---|---|
| User model (bio, location_id, phone_number, username) | `app/db/models/user.py:23-57` | ✓ M1 |
| EmailChangeToken model (new_email, token_hash, expires_at, used_at) | `app/db/models/user.py:84-93` | ✓ M1 |
| UserRead schema | `app/schemas/user.py` | ✓ M1 (wymaga rozszerzenia) |
| `GET /auth/me` → UserRead | `app/api/v1/auth.py:147-148` | ✓ M3 |
| AuthContext, get_current_user | `app/core/deps.py` | ✓ M3 |
| verification_service (create_phone_otp, verify_phone) | `app/services/verification_service.py` | ✓ M4 |
| email_service (send_verification, send_password_reset) | `app/services/email_service.py` | ✓ M4 |
| hash_token, hash_password, verify_password | `app/core/security.py` | ✓ M3 |
| Location model (id, name, type) | `app/db/models/location.py:14-19` | ✓ M1 |
| Settings (email_verification_expire_hours=24) | `app/config.py` | ✓ M4 |

---

## Scope — co dokładnie powstaje

### 1. UserRead rozszerzenie: `app/schemas/user.py` (EDYCJA)

```python
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    email_verified: bool
    phone_verified: bool
    phone_number: str | None       # NEW
    bio: str | None                 # NEW
    location_id: int | None         # NEW
    heart_balance: int
    status: str
    role: str
    created_at: datetime
```

### 2. Schemas: `app/schemas/profile.py` (NOWY)

```python
class UpdateProfileRequest(BaseModel):
    bio: str | None = Field(None, max_length=500)
    location_id: int | None = None

class ChangeUsernameRequest(BaseModel):
    new_username: str = Field(min_length=3, max_length=30)

class ChangeEmailRequest(BaseModel):
    password: str
    new_email: EmailStr

class ConfirmEmailChangeRequest(BaseModel):
    token: str = Field(max_length=256)

class ChangePhoneRequest(BaseModel):
    password: str
    new_phone_number: str = Field(pattern=r"^\+48\d{9}$")

class VerifyPhoneChangeRequest(BaseModel):
    new_phone_number: str = Field(pattern=r"^\+48\d{9}$")
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
```

### 3. Profile service: `app/services/profile_service.py` (NOWY)

Logika profilu w osobnym service (SRP — auth_service = login/tokens, verification_service = verify flows, profile_service = profile mutations).

| Funkcja | Logika |
|---|---|
| `update_profile(db, user_id, bio, location_id)` | Validate location_id EXISTS w DB (FK guard). Update User fields. flush(). |
| `change_username(db, user_id, new_username)` | Unique check. Update User.username. flush(). |
| `initiate_email_change(db, user_id, password, new_email)` | Verify current password. Check new_email not taken. Check new_email not disposable. Create EmailChangeToken (hash, 24h expiry). flush(). Return raw_token. |
| `confirm_email_change(db, raw_token)` | Find valid EmailChangeToken. Check new_email still available. Update User.email + email_verified=False. Mark token used. flush(). Return (old_email, new_email). |
| `initiate_phone_change(db, user_id, password, new_phone)` | Verify current password. Check new_phone not taken. Create PhoneVerificationOTP for new_phone. flush(). Return code. |
| `confirm_phone_change(db, user_id, new_phone, code)` | Reuse verification_service._find_valid_otp. Update User.phone_number + phone_verified=True. Mark OTP used. **NO INITIAL_GRANT.** flush(). |
| `change_password(db, user_id, old_password, new_password)` | Verify old password. Update password_hash. flush(). |

**Kluczowe decyzje:**
- `email_verified=False` po zmianie email — user musi ponownie zweryfikować nowy email
- Stary email dostaje powiadomienie "Twój email został zmieniony na {new_email}"
- `phone_verified=True` od razu po OTP (numer zweryfikowany w procesie zmiany)
- Brak ponownego INITIAL_GRANT — `_grant_initial_hearts` NIE jest wywoływany

### 4. Email service rozszerzenie: `app/services/email_service.py` (EDYCJA)

Dodaj metodę do Protocol i implementacji:

```python
class EmailService(Protocol):
    async def send_verification(self, to: str, token: str) -> None: ...
    async def send_password_reset(self, to: str, token: str) -> None: ...
    async def send_email_changed_notification(self, to: str, new_email: str) -> None: ...  # NEW
```

Mock: `self.sent.append({"type": "email_changed", "to": to, "new_email": new_email})`

Resend impl: plain text "Twój adres email w Serce został zmieniony na {new_email}. Jeśli to nie Ty — skontaktuj się z nami."

### 5. Endpointy: `app/api/v1/users.py` (NOWY router)

```python
router = APIRouter(prefix="/users", tags=["users"])

# Profile
@router.get("/me", response_model=UserRead)              # przeniesienie z auth.py
@router.patch("/me", response_model=UserRead)             # bio, location_id

# Username
@router.patch("/me/username", response_model=MessageResponse)

# Email change
@router.post("/me/email/change", response_model=MessageResponse)   # password + new_email → token
@router.post("/me/email/confirm", response_model=MessageResponse)   # token → email zmieniony

# Phone change
@router.post("/me/phone/change", response_model=MessageResponse)   # password + new_phone → OTP
@router.post("/me/phone/verify", response_model=MessageResponse)    # phone + code → zmieniony

# Password change
@router.post("/me/password", response_model=MessageResponse)        # old + new password
```

**Migration note:** `GET /auth/me` z auth.py zostaje (backward compat) — obie ścieżki zwracają to samo. W przyszłości `/auth/me` do deprecacji.

**Rate limits:**
| Endpoint | Limit | Uzasadnienie |
|---|---|---|
| `/me/email/change` | 3/hour per IP | Anti-spam (email sending) |
| `/me/phone/change` | 5/hour per IP | Koszt SMS |

### 6. Router registration: `app/api/v1/router.py` (EDYCJA)

```python
from app.api.v1.users import router as users_router
v1_router.include_router(users_router)
```

---

## Decyzje zatwierdzone

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| Osobny users router | `api/v1/users.py` | SRP — auth.py = auth flows, users.py = profile |
| `/auth/me` zostaje | Backward compat | Oba endpointy zwracają to samo; deprecacja później |
| `email_verified=False` po zmianie | Security | User musi potwierdzić nowy email |
| Powiadomienie stary email | Security | User wie że ktoś zmienił email |
| `phone_verified=True` po OTP | UX | OTP sam w sobie weryfikuje numer |
| Brak INITIAL_GRANT przy phone change | Business rule | Grant jest jednorazowy (partial unique index) |
| Password required for email/phone change | Security | Zapobiega zmianie po kradzieży sesji |
| location_id validation | FK guard | Sprawdź czy location istnieje w DB |
| Profile service osobny | SRP | Nie pęczniej auth_service |
| Alembic migrations | Zero | Modele z M1, UserRead to schema Pydantic |
| Transaction convention | Service flush, endpoint commit | Zgodne z M4 fix W1 |

---

## Konfiguracja Settings

Brak nowych settings — reużywa `email_verification_expire_hours` (24h) dla EmailChangeToken.

---

## Testy

### Unit: `tests/test_profile_service.py` (NOWY)

```
test_update_profile_bio()
test_update_profile_location_id_valid()
test_update_profile_location_id_invalid()
test_change_username_valid()
test_change_username_taken()
test_initiate_email_change_valid()
test_initiate_email_change_wrong_password()
test_initiate_email_change_email_taken()
test_initiate_email_change_disposable_email()
test_confirm_email_change_valid()
test_confirm_email_change_expired_token()
test_confirm_email_change_already_used()
test_confirm_email_change_email_taken_meanwhile()
test_initiate_phone_change_valid()
test_initiate_phone_change_wrong_password()
test_initiate_phone_change_phone_taken()
test_confirm_phone_change_valid()
test_confirm_phone_change_wrong_code()
test_confirm_phone_change_no_initial_grant()
```
Minimum: **≥19 unit**

### Unit: `tests/test_users_api.py` (NOWY)

```
test_get_me_returns_extended_fields()
test_patch_me_bio()
test_patch_me_no_token()
test_change_username_no_token()
test_change_email_no_token()
test_change_phone_no_token()
test_confirm_email_no_body()
test_verify_phone_change_invalid_format()
```
Minimum: **≥8 unit**

### Integration: `tests/integration/api/test_profile_flow.py` (NOWY)

```
test_update_profile_and_read_back()
test_change_username_e2e()
test_email_change_flow_e2e()
test_email_change_sends_notification_to_old_email()
test_phone_change_flow_e2e()
test_phone_change_no_initial_grant()
```
Minimum: **≥6 integration**

### Minimum testów

- Profile service: ≥19
- Users API: ≥8
- Integration: ≥6
- **Total nowych: ≥36**
- **Suite total: ≥118** (82 z M1-M4 + 36 nowych)

---

## Out of scope (świadomie)

- **Avatar upload** — osobny scope (storage, CDN)
- **Public user profile** (`GET /users/{id}`) — M12 (User resources API)
- **Username change cooldown** — można dodać później jeśli potrzebne
- ~~**Password change**~~ — włączony do M5 (decyzja 2026-04-17)

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Race condition: email taken between check and update | UNIQUE constraint na DB — IntegrityError catch → 409 |
| Race condition: phone taken | j.w. — UNIQUE constraint `users.phone_number` |
| Stale EmailChangeToken (new_email taken po wydaniu tokena) | Double-check w `confirm_email_change` przed UPDATE |
| Brak password change endpoint | Użytkownik ma reset-password z M4; dedykowany endpoint to nice-to-have |

---

## Decyzja: Password change włączony

**`POST /users/me/password`** (old_password + new_password) — włączony do M5 (decyzja 2026-04-17).

**Schema:**
```python
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
```

**Logika w profile_service:**
```python
async def change_password(db, user_id, old_password, new_password):
    """Change password. Verify old password first."""
    user = await db.get(User, user_id)
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(400, "INVALID_PASSWORD")
    user.password_hash = hash_password(new_password)
    await db.flush()
```

**Dodatkowe testy (+3):**
- `test_change_password_valid()`
- `test_change_password_wrong_old()`
- `test_change_password_e2e()` (integration)

**Minimum testów zaktualizowany:** ≥36 nowych (22 unit + 8 API + 6 integration).

---

## Kolejność pracy (rekomendacja)

1. **UserRead rozszerzenie** (dodaj phone_number, bio, location_id) — 0 ryzyka
2. **Schemas** `profile.py` (6 request models)
3. **profile_service.py** (update_profile, change_username, email change, phone change) + unit testy
4. **email_service.py** rozszerzenie (send_email_changed_notification)
5. **users.py** router (7 endpointów) + rejestracja w router.py
6. **Integration testy** (full flows z mock email/sms)
7. Verify: `py -m pytest tests/ -q --ignore=tests/integration` → ≥115 PASS

---

## Workflow i handoff

Developer realizuje przez `workflow_developer_tool`.

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "serce_m5_review" --status PASS \
  --summary "M5: user profile + email/phone/username change. 115+ tests PASS." \
  --next-action "Code review — profile_service, users router, email change flow, phone change no-INITIAL_GRANT"
```
