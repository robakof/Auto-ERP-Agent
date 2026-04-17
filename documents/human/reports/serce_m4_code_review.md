# Code Review: Serce M4 — Email/Phone Verification + Password Reset + INITIAL_GRANT

Date: 2026-04-17
Commit: `a6d11ff`
Base: `502e519` (M3 last fix)
Plan: `documents/human/plans/serce_m4_email_phone_verification.md`

## Summary

**Overall assessment:** NEEDS REVISION
**Code maturity level:** L3 Senior — struktura kodu, SRP, abstrakcje (Protocol + DI), naming, security patterns (token hashing, idempotent INITIAL_GRANT) na dobrym poziomie. Dwa bugi krytyczne i niedostateczne pokrycie testami blokują PASS.

## Scope reviewed

| Plik | Linie | Rola |
|---|---|---|
| `app/services/verification_service.py` | 258 | Core logic — email verify, phone OTP, password reset, INITIAL_GRANT |
| `app/services/email_service.py` | 73 | Protocol + Mock + Resend.com impl |
| `app/services/sms_service.py` | 59 | Protocol + Mock + SMSAPI.pl impl |
| `app/api/v1/auth.py` | 230 | 6 nowych endpointów + auto-send email on register |
| `app/schemas/auth.py` | 62 | 6 nowych request schemas |
| `app/config.py` | 65 | Settings rozszerzenie (email/sms config) |
| `app/core/rate_limit.py` | 23 | _get_client_ip (bez zmian logiki) |
| `app/services/auth_service.py` | 314 | Bez zmian M4 (kontekst) |
| `tests/test_verification_service.py` | 34 | 3 unit testy |
| `tests/test_email_service.py` | 25 | 3 unit testy |
| `tests/test_sms_service.py` | 24 | 3 unit testy |
| `tests/test_auth_api.py` | 146 | 5 nowych endpoint validation testów |
| `tests/integration/api/test_verification_flow.py` | 159 | 6 integration testów |

**Total nowych linii:** ~832

---

## Findings

### Critical Issues (must fix)

**C1. Resend email rate limit — de facto wyłączony**
`verification_service.py:68-78`

Rate check liczy tokeny z `used_at IS NULL AND created_at >= 24h`. Ale resend na linii 81-88 **najpierw invaliduje** stare tokeny (ustawia `used_at`), a potem tworzy nowy. Efekt:
- Registration: 1 aktywny token
- Resend 1: count=1 (<3) → invalidate → create new → DB: 1 used + 1 active
- Resend 2: count=1 (<3) → invalidate → create new → DB: 2 used + 1 active
- Resend N: count=1 → zawsze przejdzie

Rate limit nigdy nie zadziała — count aktywnych tokenów nigdy nie osiągnie 3.

**Fix:** Zmień count query na `created_at >= since` BEZ warunku `used_at IS NULL`:
```python
select(func.count()).select_from(EmailVerificationToken).where(
    EmailVerificationToken.user_id == user.id,
    EmailVerificationToken.created_at >= since,
)
```
Liczymy ile tokenów UTWORZONO (nie ile aktywnych), co blokuje spam.

---

**C2. DI pattern email/sms — broken for testing**
`email_service.py:69-73`, `sms_service.py:55-59`, `auth.py:59,169,185,219`

`get_email_service()` / `get_sms_service()` tworzą **nową instancję** przy każdym wywołaniu. Endpoint i test dostają różne obiekty `MockEmailService`. Integration test robi:
```python
email_svc = get_email_service()      # instancja A
await _register_and_get_token(...)    # endpoint tworzy instancję B
assert len(email_svc.sent) > before   # sprawdza A.sent — zawsze 0
```

Test przechodzi tylko jeśli nigdy nie został uruchomiony z prawdziwą DB, albo jest false positive.

**Fix:** Użyj FastAPI `Depends()` + `app.dependency_overrides` w testach:
```python
# W auth.py — DI dependency
async def register(..., email_svc: EmailService = Depends(get_email_service)):
    ...

# W conftest.py — override
_mock_email = MockEmailService()
app.dependency_overrides[get_email_service] = lambda: _mock_email
```

Albo: singleton pattern (module-level cache):
```python
_email_service: EmailService | None = None
def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = ResendEmailService(...) if settings.resend_api_key else MockEmailService()
    return _email_service
```

---

**C3. Test coverage — daleko poniżej planu**

Plan wymagał ≥34 nowych testów. Zaimplementowane:

| Plik | Plan | Actual | Status |
|---|---|---|---|
| test_verification_service.py | ≥18 | 3 | ✗ (3 testy dotyczą `generate_otp` i `hash_token`, nie verification_service) |
| test_email_service.py | ≥2 | 3 | ✓ |
| test_sms_service.py | ≥3 | 3 | ✓ |
| test_auth_api.py (nowe) | ≥5 | 5 | ✓ |
| test_verification_flow.py | ≥6 | 6 | ✓ (ale C2 oznacza że email/sms assertions mogą być false positive) |
| **Total** | **≥34** | **20** | **✗ brak 14 testów** |

Brakuje unit testów dla core logic:
- `verify_email` (valid, expired, already used)
- `resend_email_verification` (rate limit exceeded, email not found)
- `create_phone_otp` (rate exceeded)
- `verify_phone` (valid, wrong code, max attempts, expired)
- `verify_phone` triggers INITIAL_GRANT + idempotent
- `create_password_reset` (email not found)
- `reset_password` (valid, expired, revokes tokens)

---

### Warnings (should fix)

**W1. Transaction boundary inconsistency**

Niektóre service functions commitują wewnętrznie, inne nie:

| Funkcja | Commit? |
|---|---|
| `verify_email` | tak (linia 52) |
| `verify_phone` | tak (linia 141) |
| `reset_password` | tak (linia 217) |
| `resend_email_verification` | tak (linia 92) |
| `create_email_verification` | nie (flush) — endpoint commituje |
| `create_phone_otp` | nie (flush) — endpoint commituje |
| `create_password_reset` | nie (flush) — endpoint commituje |

Pattern z M3 (`auth_service`): service commituje. M4 miesza oba podejścia.

**Fix:** Ustal jedną konwencję. Rekomendacja: service NIE commituje (flush only), endpoint zarządza transakcją. To daje endpointowi kontrolę nad atomowością (np. register + send email w jednej transakcji).

---

**W2. `_client_ip` zduplikowana**

Identyczna logika w dwóch plikach:
- `rate_limit.py:15-19` (`_get_client_ip`)
- `auth.py:38-44` (`_client_ip`)

**Fix:** Wyciągnij do `app/core/request_utils.py` lub użyj jednej z `rate_limit.py` w obu miejscach.

---

**W3. External service errors — generic 500**
`email_service.py:66`, `sms_service.py:47`

`resp.raise_for_status()` propaguje `httpx.HTTPStatusError` do endpointu → niezłapany → FastAPI zwraca generic 500. Użytkownik nie wie co się stało.

**Fix:** Wrap w dedykowany exception lub try/catch w endpoincie z graceful fallback:
```python
try:
    await email_svc.send_verification(...)
except httpx.HTTPStatusError:
    # Log error, but don't fail registration
    pass
```

---

**W4. Register: email send failure = 500 ale user registered**
`auth.py:59-63`

`register_user` commituje usera. Potem `create_email_verification` + commit. Potem `send_verification`. Jeśli send rzuci exception → 500 response, ale user IS registered w DB. Klient myśli że rejestracja nie powiodła się i próbuje ponownie → EMAIL_TAKEN.

**Fix:** Wrap `send_verification` w try/except (fire-and-forget). Rejestracja powinna się powieść niezależnie od stanu usługi email.

---

### Suggestions (nice to have)

**S1. Token schemas: brak max_length**
`schemas/auth.py:36,57`

`VerifyEmailRequest.token` i `ResetPasswordRequest.token` to `str` bez ograniczeń. Ktoś może wysłać megabajt — SHA-256 obsłuży, ale to zmarnowane zasoby.

Rekomendacja: `token: str = Field(max_length=256)` (urlsafe base64 z 48 bytes = 64 chars, 256 to duży margines).

---

**S2. OTP wrong-code behavior — udokumentuj intencję**
`verification_service.py:156-167`

`_find_valid_otp` iteruje WSZYSTKIE aktywne OTP dla usera+phone i inkrementuje `attempts` na każdym nie-pasującym. Jeśli user ma 3 aktywne OTP, jeden zły kod podnosi `attempts` na wszystkich trzech. To ogranicza total guesses — rozsądne security-wise, ale nieoczywiste. Warto dodać komentarz z intencją.

---

## Architektura — co jest dobrze

1. **Protocol + DI pattern** (email/sms) — czysty, testowalny (po naprawie C2), łatwo wymienić provider.
2. **Separation of Services** — verification_service oddzielony od auth_service (SRP). Dobrze.
3. **INITIAL_GRANT idempotentność** — aplikacyjny check + DB partial unique index (defense in depth). L4 pattern.
4. **Security patterns:**
   - Token hashing (SHA-256) — raw nigdy w DB
   - OTP attempts limit
   - Password reset revokes all sessions
   - forgot-password: always 200 (nie ujawnia czy email istnieje)
   - resend-verification: always 200 (j.w.)
5. **Config pattern** — consistent z M3 (empty key = mock mode).
6. **Schemas** — Pydantic z regex, min/max_length. Phone format `^\+48\d{9}$`. OTP `^\d{6}$`.

## Recommended Actions

- [x] **C1** Fix resend rate limit — count all tokens (not just unused) — `f294240`
- [x] **C2** Fix email/sms DI — singleton pattern — `f294240`
- [x] **C3** Dopisz brakujące unit testów — 21 testów (plan ≥18) — `f294240`
- [x] **W1** Ujednolić convention: service flush-only, endpoint commituje — `f294240`
- [x] **W2** Wyciągnij `_client_ip` — deleguje do `rate_limit._get_client_ip` — `f294240`
- [x] **W3+W4** Wrap external calls w try/except — fire-and-forget on register/resend — `f294240`
- [x] **S1** Dodaj max_length do token fields w schemas — `f294240`

---

## Re-review (2026-04-17)

Commit: `f294240`
**Assessment: PASS**

Wszystkie Critical Issues (C1-C3) i Warnings (W1-W4) naprawione poprawnie.
Suggestion S1 zaimplementowany.

### Weryfikacja per finding

| Finding | Fix | Status |
|---|---|---|
| C1 rate limit | `used_at IS NULL` usunięty z count query | ✓ Poprawny |
| C2 DI singleton | Module-level `_email_service`/`_sms_service` cache | ✓ Poprawny |
| C3 testy | 21 unit testów verification_service (plan ≥18) | ✓ Pokrycie OK |
| W1 transaction | Service: flush-only. Endpoint: commit. Konsekwentnie. | ✓ Poprawny |
| W2 DRY | `auth.py:_client_ip` → `rate_limit._get_client_ip` | ✓ Poprawny |
| W3+W4 fire-and-forget | try/except na register + resend email send | ✓ Poprawny |
| S1 max_length | `token: str = Field(max_length=256)` | ✓ Poprawny |

### Nowe obserwacje (non-blocking)

**S2 (new).** `forgot_password` endpoint — `send_password_reset` bez try/except (linia 225), niespójne z register/resend. Mniejsze ryzyko (token committed, retry możliwy), ale warto ujednolicić.

### Final test count

| Plik | Count |
|---|---|
| test_verification_service.py | 21 |
| test_email_service.py | 3 |
| test_sms_service.py | 3 |
| test_auth_api.py (M3+M4) | 16 |
| test_verification_flow.py (integration) | 6 |
| **Total M4 nowych** | **38** (plan ≥34) ✓ |

**Code maturity: L3 Senior** — potwierdzone po re-review.
