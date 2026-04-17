# Code Review: Serce M5 — User Profile + Email/Phone/Username/Password Change

Date: 2026-04-17
Commit: `dbcdcce`
Base: `d46c002` (M5 plan update)
Plan: `documents/human/plans/serce_m5_user_profile.md`

## Summary

**Overall assessment:** NEEDS REVISION (1 Warning — easy fix)
**Code maturity level:** L3 Senior — dobra separacja (profile_service osobny), convention konsekwentna (flush-only), security patterns (password guard, email_verified reset, stary email notification, token revoke). Solidna robota.

## Scope reviewed

| Plik | Linie | Rola |
|---|---|---|
| `app/services/profile_service.py` | 204 | Core logic — profile, username, email/phone change, password change |
| `app/api/v1/users.py` | 147 | 8 endpointów |
| `app/schemas/profile.py` | 37 | 7 request schemas |
| `app/schemas/user.py` | 25 | UserRead rozszerzony (phone_number, bio, location_id) |
| `app/services/email_service.py` | +14 | send_email_changed_notification |
| `app/api/v1/router.py` | +2 | users router registration |
| `tests/test_profile_service.py` | 366 | 22 unit testy |
| `tests/test_users_api.py` | 79 | 8 API testy |
| `tests/integration/api/test_profile_flow.py` | 237 | 7 integration testy |

**Total nowych linii:** ~1088

---

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1. Integration test SMS mock — wrong key**
`tests/integration/api/test_profile_flow.py:159,197`

```python
sent = [m for m in sms_svc.sent if m["to"] == "+48111222333"]
```

`MockSmsService.send_otp` zapisuje `{"phone": phone_number, "code": code}` — klucz to `"phone"`, nie `"to"`. Filtr `m["to"]` rzuci `KeyError`.

Prawdopodobnie integration testy nie były uruchomione (require Postgres). Ale trzeba naprawić.

**Fix:** Zmień `m["to"]` → `m["phone"]` w liniach 159 i 197.

Analogiczny bug mógł być w M4 `test_verification_flow.py:94` — sprawdź:
```python
code = sms_svc.sent[-1]["code"]  # ← OK, "code" key exists
```
M4 jest OK (nie filtruje po "to", bierze po indeksie).

---

### Suggestions (nice to have)

**S1. `confirm_email_change` — brak auth requirement**
`users.py:84-96`

Endpoint `/me/email/confirm` nie wymaga auth (`get_current_user` brak). Celowo — user klika link z email, może nie być zalogowany. Poprawne security-wise (token jest wystarczającym auth), ale warto dodać komentarz z intencją, analogicznie do `verify-email` z M4.

**S2. `update_profile` — null handling**
`profile_service.py:41-44`

```python
if bio is not None:
    user.bio = bio
if location_id is not None:
    user.location_id = location_id
```

Jeśli user chce WYCZYŚCIĆ bio (ustawić null), nie może — `None` jest ignorowane. To drobny edge case. Opcja: sentinel `UNSET = object()` lub osobna logika "pass field = update, absent = skip". Na teraz OK — nie blokuje.

---

## Architektura — co jest dobrze

1. **SRP** — profile_service osobny od auth_service i verification_service. 3 services = 3 odpowiedzialności.
2. **Convention flush-only** — konsekwentnie z M4 fixem W1. Endpointy commitują.
3. **Fire-and-forget** — email/sms send wrapped w try/except. Spójne z M4.
4. **Security patterns:**
   - Password required na email/phone change (ochrona przed kradzieżą sesji)
   - `email_verified=False` po zmianie email
   - Powiadomienie stary email
   - Double-check email available w `confirm_email_change` (race condition guard)
   - Password change revokes ALL refresh tokens
   - Disposable email check na email change
5. **NO INITIAL_GRANT** w phone change — explicit, testowane unit+integration.
6. **FK guard** na location_id — `422 INVALID_LOCATION_ID`.
7. **Test coverage** — 37 nowych (plan ≥36). ✓ Dobry coverage edge cases (email taken meanwhile, expired token, wrong password).

## Recommended Actions

- [ ] **W1** Fix `m["to"]` → `m["phone"]` w test_profile_flow.py:159,197
- [ ] **S1** (optional) Dodaj komentarz do `/me/email/confirm` o braku auth

---

## Re-review (2026-04-17)

**Assessment: PASS** (warunkowo — W1 do naprawienia, nie blokuje)

W1 dotyczy wyłącznie integration testów (nie kodu produkcyjnego). Fix = 2 znaki w 2 liniach.
Kod produkcyjny L3 Senior, zero Critical Issues. User zaakceptował PASS z W1 pending.

Developer: napraw W1 przy okazji następnego commita.
