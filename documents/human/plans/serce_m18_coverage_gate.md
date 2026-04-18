# Serce — M18: Test coverage gate — MUST-COVER verification

Date: 2026-04-18
Status: Proposed
Author: Architect
Depends on: M1-M17 (wszystkie)

---

## Cel

Audyt pokrycia testowego Fazy 1. Weryfikacja, że wszystkie scenariusze MUST-COVER
mają testy. Uzupełnienie brakujących integration testów. Wygenerowanie raportu
pokrycia (`pytest --cov`) jako baseline dla Fazy 2.

---

## Audyt MUST-COVER — cross-reference

### 1. Hearts transfer + concurrency (M6) — ✓ COVERED

| Scenariusz | Test | Status |
|---|---|---|
| Gift valid + balance update | `test_hearts_service::test_gift_hearts_valid`, `test_gift_hearts_updates_both_balances` | ✓ |
| Self-gift rejected | `test_gift_self_rejected` | ✓ |
| Insufficient balance | `test_gift_insufficient_balance` | ✓ |
| Cap exceeded | `test_gift_recipient_cap_exceeded`, `test_gift_cap_over_rejected` | ✓ |
| Exact balance / cap edge | `test_gift_exact_balance_succeeds`, `test_gift_cap_exact_succeeds` | ✓ |
| Suspended recipient | `test_gift_recipient_not_active` | ✓ |
| 100 concurrent gifts no negative | `test_hearts_concurrency::test_concurrent_gifts_no_negative_balance` | ✓ |
| Concurrent gifts to same recipient cap | `test_concurrent_gifts_to_same_recipient_cap` | ✓ |
| Concurrent gift + receive | `test_concurrent_gift_and_receive` | ✓ |
| Ledger entries + pagination + filter | 4 testy w `test_hearts_service` | ✓ |
| Integration E2E | `test_hearts_flow` — 5 testów | ✓ |

### 2. Exchange state machine (M9) — ✓ COVERED

| Scenariusz | Test | Status |
|---|---|---|
| Create from request/offer | `test_create_from_request_valid`, `test_create_from_offer_valid` | ✓ |
| Accept + escrow | `test_accept_valid` | ✓ |
| Complete + hearts transfer | `test_complete_valid` | ✓ |
| Cancel pending | `test_cancel_pending` | ✓ |
| Cancel accepted + refund | `test_cancel_accepted_refund` | ✓ |
| Illegal transitions | `test_accept_not_pending`, `test_complete_not_accepted`, `test_cancel_completed` | ✓ |
| Integration E2E | `test_exchange_flow` — 6 testów (full request+offer flow) | ✓ |

### 3. Exchange creation guards (M9) — ✓ COVERED

| Guard | Test | Status |
|---|---|---|
| Request not found | `test_create_request_not_found` | ✓ |
| Request not OPEN | `test_create_request_not_open` | ✓ |
| Self-exchange | `test_create_request_self_exchange`, `test_create_offer_self_exchange` | ✓ |
| Duplicate PENDING | `test_create_request_duplicate_pending` | ✓ |
| Offer not found / not active | `test_create_offer_not_found`, `test_create_offer_not_active` | ✓ |
| No source | `test_create_no_source` | ✓ |

### 4. Auth (M3/M4) — ✓ COVERED

| Scenariusz | Test | Status |
|---|---|---|
| Register validation | `test_auth_api` — 6 testów (tos, password, email, username, disposable) | ✓ |
| Login/logout E2E | `test_auth_flow` — 18 testów integration | ✓ |
| JWT create/decode/expire | `test_security` — 8 testów | ✓ |
| Refresh rotation + old rejected | `test_auth_flow::test_refresh_rotates_tokens`, `test_refresh_old_token_rejected` | ✓ |
| Session management + revoke | `test_auth_flow::test_list_sessions`, `test_revoke_other_session_by_id` | ✓ |
| CANNOT_REVOKE_CURRENT_SESSION | `test_auth_flow::test_revoke_current_session_blocked` | ✓ |
| Email verification | `test_verification_flow::test_verify_email_activates_flag` | ✓ |
| Phone OTP + INITIAL_GRANT | `test_verification_flow::test_phone_otp_flow_and_initial_grant` | ✓ |
| Password reset | `test_verification_flow::test_forgot_password_and_reset` | ✓ |
| hCaptcha | `test_captcha` — 4 testy | ✓ |
| Temp-mail denylist | `test_email_denylist` — 6 testów | ✓ |
| Secret key in prod | `test_config` — 5 testów | ✓ |

### 5. Rate limiting (M3) — ⚠️ GAP

| Scenariusz | Test | Status |
|---|---|---|
| Register 5/hour → 429 | brak | ❌ |
| Login 10/min → 429 | brak | ❌ |
| Resend verification 3/hour → 429 | brak | ❌ |

**Uwaga:** Rate limiting to feature frameworku (slowapi). Testy weryfikowałyby
integrację konfiguracji, nie logikę biznesową. Priorytet: **niski** — slowapi
jest dobrze przetestowanym frameworkiem. Dodanie testów byłoby nice-to-have
ale nie blokuje PASS.

**Decyzja:** Deferred — oznaczymy jako "framework trust" w raporcie pokrycia.
Jeśli chcesz testować rate limiting — wymaga osobnej sesji DB (slowapi state
w pamięci nie persystuje między testami ASGI).

### 6. Public vs private endpoints — ✓ COVERED

| Scenariusz | Test | Status |
|---|---|---|
| All protected → 401 without token | 13 plików `test_*_api.py`, każdy endpoint ma `test_*_no_token` | ✓ |
| Admin-only → 403 for non-admin | `test_admin_api` — 12 testów (list/resolve/suspend/unsuspend/grant/audit) | ✓ |
| Public endpoints (health, locations, categories) | `test_health`, integration tests | ✓ |

### 7. Review unique (M11) — ✓ COVERED

| Scenariusz | Test | Status |
|---|---|---|
| Duplicate review → 409 REVIEW_ALREADY_EXISTS | `test_review_service::test_create_duplicate_review` | ✓ |
| Review before COMPLETED → 422 | `test_create_exchange_not_completed` | ✓ |
| Non-participant → 403 | `test_create_not_participant` | ✓ |
| Integration | `test_review_flow::test_review_on_pending_rejected` | ✓ |

### 8. APScheduler expire (M17) — ✓ COVERED

| Scenariusz | Test | Status |
|---|---|---|
| Expire past-due OPEN request | `test_scheduler::test_expire_open_request_past_expiry` | ✓ |
| No expire future request | `test_no_expire_open_request_future` | ✓ |
| Idempotency (already cancelled) | `test_no_expire_cancelled_request` | ✓ |
| Cascade PENDING exchanges | `test_cascade_pending_exchanges` | ✓ |
| No double cancel | `test_no_double_cancel` | ✓ |
| Email notification | `test_email_sent_on_expire` | ✓ |

---

## Integration test gaps

| Flow | Plik integration | Status |
|---|---|---|
| Auth | `test_auth_flow.py` (18 tests) | ✓ |
| Verification | `test_verification_flow.py` (7 tests) | ✓ |
| Profile | `test_profile_flow.py` (7 tests) | ✓ |
| Requests | `test_request_flow.py` (6 tests) | ✓ |
| Offers | `test_offer_flow.py` (6 tests) | ✓ |
| Exchanges | `test_exchange_flow.py` (6 tests) | ✓ |
| Hearts | `test_hearts_flow.py` (5 tests) | ✓ |
| Messages | `test_message_flow.py` (3 tests) | ✓ |
| Notifications | `test_notification_flow.py` (2 tests) | ✓ |
| Reviews | `test_review_flow.py` (3 tests) | ✓ |
| User resources | `test_user_resources_flow.py` (3 tests) | ✓ |
| Categories | `test_categories_endpoint.py` (3 tests) | ✓ |
| Locations | `test_locations_endpoint.py` (4 tests) | ✓ |
| Schema + seeds | `test_schema.py` + `test_seed_*.py` (15 tests) | ✓ |
| **Flags** | brak | **❌ GAP** |
| **Admin** | brak | **❌ GAP** |
| **Account deletion** | brak | **❌ GAP** |

---

## Deliverables

### 1. Integration test: `tests/integration/api/test_flag_flow.py`

Happy path flag creation:
| Test | Opis |
|---|---|
| `test_flag_request_e2e` | Utwórz request → flaguj → sprawdź flag istnieje |
| `test_flag_own_request_rejected_e2e` | Flagowanie własnego zasobu → 422 |
| `test_flag_duplicate_rejected_e2e` | Podwójna flaga → 409 |

### 2. Integration test: `tests/integration/api/test_admin_flow.py`

Happy path admin operations:
| Test | Opis |
|---|---|
| `test_resolve_flag_dismiss_e2e` | Admin rozwiązuje flagę (dismiss) |
| `test_suspend_user_e2e` | Admin zawieszenie → user login → 401 ACCOUNT_SUSPENDED |
| `test_unsuspend_user_e2e` | Admin odwieszenie → user login działa |
| `test_grant_hearts_e2e` | Admin grant hearts → user balance wzrasta |
| `test_audit_log_e2e` | Po operacjach admin → audit log zawiera wpisy |

**Uwaga:** Wymaga seed admina lub endpoint tworzący admina w testach. Sprawdź
czy `integration/conftest.py` ma helper do tworzenia admin usera — jeśli nie, dodaj.

### 3. Integration test: `tests/integration/api/test_account_flow.py`

Happy path account deletion:
| Test | Opis |
|---|---|
| `test_soft_delete_void_e2e` | Usunięcie konta (void) → login → 401, profil publiczny = placeholder |
| `test_soft_delete_transfer_e2e` | Usunięcie z transfer → odbiorca ma saldo |

### 4. Coverage report: `pytest --cov`

Uruchom `pytest --cov=app --cov-report=term-missing` i zapisz output
do `documents/human/reports/serce_faza1_coverage.md`.

Raport powinien zawierać:
- Procentowe pokrycie per moduł
- Lista modułów poniżej 80% (jeśli są)
- Podsumowanie MUST-COVER: 7/8 COVERED, 1/8 deferred (rate limiting)

---

## Nie robimy (out of scope)

- Testy rate limitingu (framework trust — slowapi, deferred)
- Testy end-to-end z prawdziwym SMTP/SMS (mock-only)
- Testy APScheduler timing (testujemy logikę joba, nie framework)
- Frontend testy (Faza 2)

---

## DoD (Definition of Done)

1. 3 nowe pliki integration testów (flags, admin, account deletion).
2. Wszystkie nowe testy PASS.
3. Wszystkie istniejące testy PASS (zero regresji).
4. Coverage report zapisany w `documents/human/reports/serce_faza1_coverage.md`.
5. MUST-COVER: 7/8 confirmed, 1 deferred z uzasadnieniem.

---

## Rozmiar: M

3 nowe pliki testów integration + coverage report. Logika testów powtarza wzorce
z istniejących plików (test_exchange_flow.py, test_hearts_flow.py — te same helpers).
