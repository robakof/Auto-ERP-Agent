# Serce — Faza 1 roadmapa implementacyjna

Date: 2026-04-14
Status: Proposed
Author: Architect
Podstawa: `documents/human/plans/serce_architecture.md` (v16, 42 pozycje w Fazie 1)

---

## Cel

Rozpisanie Fazy 1 (Backend core — MVP) na sekwencję milestone'ów z jasnymi wejściami,
wyjściami i definicją ukończenia (DoD). Każdy M jest commitowalny niezależnie
i zamykany code-reviewem Architekta.

## Konwencje

- **DoD per milestone:** kod + testy 100% PASS + migracja Alembic + code review PASS.
- **Tests First tam, gdzie logika domenowa:** hearts, exchange state machine, auth guardy — testy przed implementacją.
- **Commit granularity:** jeden milestone = jeden PR/commit albo seria spójnych commitów z tym samym scope.
- **Review gate:** po każdym milestone handoff do Architekta → code review → PASS przed startem następnego M.
- **Nie łącz M-ów.** Trzy małe passy są bezpieczniejsze niż jeden duży.

---

## Stan aktualny (bootstrap done)

| Commit | Zakres | Status |
|---|---|---|
| `30c9ebb` | Scaffold: FastAPI, PostgreSQL, Alembic, Docker, pytest, health | ✓ |
| `d980d8f` | 19 modeli domenowych + CHECK constraints + partial indexes | ✓ (migracja?) |

**Do weryfikacji przed M1:** czy `d980d8f` zawiera Alembic migration initial (`alembic upgrade head` = 19 tabel)?
Jeśli nie — M1 = generate initial migration + smoke test (create_all równoważny Alembic).

---

## Milestone'y Fazy 1

### M1. Alembic initial migration + smoke CRUD
**Wejście:** scaffold, 19 modeli.
**Deliverables:**
- `alembic revision --autogenerate -m "initial schema"`
- Weryfikacja: migracja generuje wszystkie CHECK, UNIQUE, partial indexes 1:1 z modelami.
- `tests/integration/db/test_schema.py` — smoke: wszystkie tabele istnieją, INSERT minimalny user/location/category.
**DoD:** `alembic upgrade head` + `alembic downgrade base` działa na świeżej bazie. Test PASS.
**Rozmiar:** S.

### M2. Reference data — Locations + Categories preload
**Wejście:** M1.
**Deliverables:**
- Alembic data migration: 16 województw + ~100 miast (seed z listy).
- Alembic data migration: bazowe kategorie (lista z decyzji projektowej — uzgodnić z userem jeśli brak).
- `GET /locations`, `GET /locations?scope=VOIVODESHIP|CITY`, `GET /categories` (bez auth, cache'owane).
**DoD:** po `upgrade head` lista województw i kategorii w bazie. Endpointy zwracają dane. Test integracyjny.
**Rozmiar:** S-M.

### M3. Auth core — register + login + refresh + logout
**Wejście:** M1. Nie wymaga weryfikacji email/phone jeszcze (to M4).
**Deliverables:**
- `POST /auth/register` (email + password + username + tos_accepted + privacy_policy_accepted + hCaptcha).
- `POST /auth/login` → access (15min) + refresh (30d, DB-backed, httpOnly cookie).
- `POST /auth/refresh` → rotacja refresh tokena.
- `POST /auth/logout` (unieważnia current session), `POST /auth/logout-all`.
- `GET /auth/sessions`, `DELETE /auth/sessions/{id}` (guard CANNOT_REVOKE_CURRENT_SESSION).
- `POST /auth/accept-terms` + tabela `UserConsent` (document_type, version, ip_address).
- SystemConfig seed: `tos_current_version`, `privacy_current_version`.
- Warstwy anti-farming: IP rate limit (register), temp-mail denylist, CAPTCHA validation.
- Bcrypt password hashing, JWT sign/verify, refresh token rotation.
**DoD:** rejestracja+login+refresh+logout E2E; token rotation testowana; testy rate limit.
**Rozmiar:** L. **Ryzyko:** wysokie (fundament bezpieczeństwa) → code review szczególnie dokładny.

### M4. Email & phone verification + password reset
**Wejście:** M3.
**Deliverables:**
- `EmailVerificationToken` model + flow (`POST /auth/verify-email`, `POST /auth/resend-verification-email` rate 3/email/24h).
- `PhoneVerificationOTP` model + flow (`POST /auth/verify-phone`, integracja SMSAPI.pl stub + prod).
- `PasswordResetToken` model + flow (`POST /auth/forgot-password`, `POST /auth/reset-password`).
- Email sender service (Resend.com, mockowany w testach).
- SMS sender service (SMSAPI.pl, mockowany w testach).
- INITIAL_GRANT serc przy pierwszej weryfikacji phone (decyzja #8 — phone = gate).
**DoD:** wszystkie tokeny wygasające; resend unieważnia stary; INITIAL_GRANT tylko raz na użytkownika.
**Rozmiar:** L.

### M5. User profile + email/phone change
**Wejście:** M4.
**Deliverables:**
- `GET /users/me`, `PATCH /users/me` (bio, location_id).
- `PATCH /users/me/username` (unique check).
- `POST /users/me/email/change` (hasło + `EmailChangeToken` 24h + powiadomienie stary email) + `POST /auth/confirm-email-change`.
- `POST /users/me/phone/change` (hasło + OTP nowy numer) + `POST /users/me/phone/verify` (brak ponownego INITIAL_GRANT).
**DoD:** zmiana email/phone E2E, brak podwójnego INITIAL_GRANT, powiadomienie stary email wysłane.
**Rozmiar:** M.

### M6. Hearts — ledger + transfer + gift + balance
**Wejście:** M3 (auth).
**Deliverables:**
- Hearts service: atomowy transfer z walidacją (balance >= amount, cap, CHECK >= 0, SystemConfig.heart_balance_cap walidowany aplikacyjnie).
- `POST /hearts/gift` (dobrowolny transfer, `HeartLedger.type=GIFT`).
- `GET /users/me/hearts/balance`.
- `GET /users/me/ledger` z paginacją (type filter, date range).
- `HeartLedger.type=PAYMENT` zastrzeżony dla Exchange completion (użyty w M9).
**DoD:** concurrency test — 100 równoległych transferów z tego samego konta nie pozwala zejść poniżej 0; żaden transfer nie dubluje się; 422 z `max_receivable` przy cap.
**Rozmiar:** M. **Ryzyko:** wysokie (pieniądz systemu) → MUST-COVER tests.

### M7. Requests — CRUD + listing + search + cancel
**Wejście:** M2 (categories/locations), M5 (profile).
**Deliverables:**
- `POST /requests`, `GET /requests/{id}`, `PATCH /requests/{id}` (title/description/expires_at; hearts_offered zablokowany gdy PENDING Exchange).
- `GET /requests` z filtrami (`location_scope`, `category`, `status`, `?q=` ILIKE, `?sort=`, `?order=`, paginacja).
- `POST /requests/{id}/cancel` (owner, OPEN → CANCELLED + auto-cancel PENDING Exchanges związanych).
- Własność: tylko owner edytuje/usuwa.
**DoD:** search działa, paginacja spójna z konwencją, feed query WHERE owner.status='active'.
**Rozmiar:** M.

### M8. Offers — CRUD + listing + status management
**Wejście:** M2, M5.
**Deliverables:**
- `POST /offers`, `GET /offers/{id}`, `PATCH /offers/{id}` (title/description/hearts_asked).
- `PATCH /offers/{id}/status` (ACTIVE / PAUSED / INACTIVE; HIDDEN tylko admin).
- `GET /offers` — filtry jak requests.
**DoD:** PAUSED blokuje nowe Exchange (weryfikacja w M9), INACTIVE nie pojawia się na feedzie.
**Rozmiar:** M.

### M9. Exchange state machine (core)
**Wejście:** M6, M7, M8.
**Deliverables:**
- `POST /exchanges` (PENDING, dwukierunkowy; guardy: Request=OPEN, Offer=ACTIVE, request_owner != helper).
- `POST /exchanges/{id}/accept` (tylko non-initiator; Request-first → auto-cancel pozostałych PENDING).
- `POST /exchanges/{id}/complete` (transfer `HeartLedger.type=PAYMENT`, atomowy).
- `POST /exchanges/{id}/cancel` (przed COMPLETED, participants; reguła #4 / #23 skorygowane w v2).
- Request-first `hearts_agreed = hearts_offered` (jawna walidacja — W3 z review v1).
- Exchange.IN_PROGRESS usunięte z enum (K2 z review v2).
**DoD:** state machine nie pozwala na niedozwolone przejścia (property test); transfer przy complete atomowy (test współbieżności z M6); partial unique index wymusza max 1 ACCEPTED per Request.
**Rozmiar:** L. **Ryzyko:** wysokie — rdzeń domeny. MUST-COVER.

### M10. Messages w Exchange
**Wejście:** M9.
**Deliverables:**
- `POST /exchanges/{id}/messages`, `GET /exchanges/{id}/messages` (sort ASC, paginacja, autoryzacja tylko participants).
**DoD:** non-participant → 403; wiadomości widoczne też po COMPLETED.
**Rozmiar:** S.

### M11. Reviews
**Wejście:** M9.
**Deliverables:**
- `POST /exchanges/{id}/reviews` (komentarz tekstowy, tylko po COMPLETED, UNIQUE exchange_id + reviewer_id).
- `GET /users/{id}/reviews?direction=received|given`.
**DoD:** druga próba review → 409 (unique); review przed COMPLETED → 422.
**Rozmiar:** S.

### M12. User resources API (ADR-SERCE-005)
**Wejście:** M5, M7, M8, M9, M11, M6.
**Deliverables:**
- `GET /users/me/summary` (agregat: balance, active requests, active offers, pending exchanges).
- `GET /users/me/requests`, `/offers`, `/exchanges`, `/reviews?direction=`, `/ledger`.
- Exchange transparency: `GET /requests/{id}/exchanges`, `GET /offers/{id}/exchanges` (owner + participants widzą pełne; rywale — zredukowany widok).
**DoD:** owner widzi wszystkie swoje Exchanges; rywal widzi tylko ich istnienie bez detali.
**Rozmiar:** M.

### M13. Notifications (in-app + email)
**Wejście:** M4 (email service), M9 (zdarzenia Exchange), M6 (zdarzenia Hearts).
**Deliverables:**
- `Notification` model, typy enum (EXCHANGE_CREATED, EXCHANGE_ACCEPTED, EXCHANGE_COMPLETED, EXCHANGE_CANCELLED, HEARTS_RECEIVED, REQUEST_EXPIRED, …).
- INSERT przy każdym zdarzeniu + email wysyłany równolegle (background task).
- `GET /users/me/notifications` (paginacja + unread filter), `POST /users/me/notifications/{id}/read`, `POST /users/me/notifications/read-all`.
**DoD:** każde zdarzenie generuje notification; email fail nie blokuje zdarzenia (best-effort).
**Rozmiar:** M.

### M14. Flag endpoints + ContentFlag
**Wejście:** M7, M8, M9, M5 (users).
**Deliverables:**
- `POST /{resource}/{id}/flag` per resource: `exchanges`, `requests`, `offers`, `users`. Messages przez Exchange (opis w reason).
- `ContentFlag` INSERT z odpowiednim `target_type` (W2 z review v1).
**DoD:** każdy target_type ma endpoint; user nie może zaflagować własnego zasobu (wg decyzji projektowej — do potwierdzenia).
**Rozmiar:** S.

### M15. Admin — moderation + audit + hearts grant + suspend
**Wejście:** M14, M6.
**Deliverables:**
- `GET /admin/flags` (paginacja + filtry status, target_type), `GET /admin/flags/{id}`, `POST /admin/flags/{id}/resolve` (resolution_action + params; unhide policy z decyzji #100).
- `POST /admin/users/{id}/suspend` (+ revoke refresh tokens, audit log), `POST /admin/users/{id}/unsuspend`.
- `POST /admin/hearts/grant` (+ `HeartLedger.type=ADMIN_REFUND`, audit log).
- `GET /admin/audit` (paginacja + filtry actor_id, action, target_type, from, to).
- Dependency `require_admin()` + seed migration (INITIAL_ADMIN_EMAIL z .env).
- Suspended account: login → 401 ACCOUNT_SUSPENDED; feed query WHERE owner.status='active'; Exchanges trwają, messages/akcje zablokowane.
**DoD:** admin może zawiesić usera, ten nie może się zalogować ani publikować, ale trwające Exchange idą dalej.
**Rozmiar:** L.

### M16. Soft delete (account)
**Wejście:** M15, M6, M12.
**Deliverables:**
- `DELETE /users/me` z dyspozycją salda (`void` | `transfer_to={user_id}`).
- Transakcyjna kaskada 8 kroków (ADR-SERCE-003 D6): anonymize user, cancel requests/offers/exchanges PENDING, close active exchanges (z flagą?), clear messages body, etc.
- Test atomowości — failure w połowie = rollback wszystkiego.
**DoD:** po delete user widoczny jako "(usunięty)" w historii Exchange/Review; dane osobowe usunięte; saldo zgodne z dyspozycją.
**Rozmiar:** L. **Ryzyko:** wysokie — atomowość kaskady.

### M17. APScheduler — expire requests
**Wejście:** M7.
**Deliverables:**
- Job co godzinę: `UPDATE requests SET status='CANCELLED' WHERE expires_at < now() AND status='OPEN'`.
- Notification REQUEST_EXPIRED do ownera.
- Setup APScheduler lifecycle w FastAPI startup/shutdown.
**DoD:** test fake-time potwierdza ekspirację; brak podwójnego anulowania.
**Rozmiar:** S.

### M18. Test coverage gate — MUST-COVER verification
**Wejście:** wszystkie wcześniejsze.
**Deliverables:**
- Audyt pokrycia: hearts transfer + concurrency (M6), Exchange state machine (M9), Exchange creation guardy (M9), Auth (M3/M4), rate limiting (M3), public vs private endpoints (wszystkie), Review unique (M11), APScheduler expire (M17).
- Integration tests `tests/integration/api/*` dla happy path każdego flow.
- Raport pokrycia (`pytest --cov`) — baseline dla Fazy 2.
**DoD:** wszystkie MUST-COVER scenarios w testach; CI zielone; coverage raport zapisany w `documents/human/reports/serce_faza1_coverage.md`.
**Rozmiar:** M.

---

## Graf zależności (uproszczony)

```
M1 ──┬── M2 ──┬── M7 ──┐
     │        │        │
     └── M3 ──┼── M8 ──┤
              │        │
              ├── M4 ──┼── M6 ──┼── M9 ──┬── M10
              │        │        │        ├── M11
              │        │        │        ├── M12
              │        │        │        ├── M13
              │        │        │        ├── M14 ── M15 ── M16
              │        │        │        └── M17
              └── M5 ──┘
```

**Ścieżka krytyczna:** M1 → M3 → M4 → M6 → M9 → M15 → M16 → M18.

---

## Potencjalne równoległe pasma (gdy mamy ≥2 Developerów)

- Pasmo A (auth): M3 → M4 → M5
- Pasmo B (domena): M2 → M6 → (M7 ∥ M8) → M9
- Pasmo C (infra): M17 (APScheduler) — niezależne po M7
- Pasmo D (admin): M14 → M15 — po M7/M8/M9

Przy jednym Developerze trzymaj sekwencję M1..M18.

---

## Decyzje zamknięte (2026-04-14)

1. **M2 — lista bazowych kategorii:** Architekt zaproponował, user zaakceptował → decyzja #106 (9 grup + 26 podkategorii).
2. **M14 — flag na własnym zasobie:** 422 CANNOT_FLAG_OWN_RESOURCE (wyjątek: dispute Exchange) → decyzja #108.
3. **M16 — soft delete dyspozycja salda:** `void` (serca przepadają) lub `transfer` (do wskazanego usera) → ADR-SERCE-003 D6.
4. **M3 — hCaptcha:** potwierdzone (decyzja #53). Rate limiter: slowapi (decyzja #114).

---

## Review cadence

Po każdym milestone:
1. Developer robi handoff do Architekta z testami PASS i linkiem do commitów.
2. Architekt uruchamia `workflow_code_review.md`.
3. PASS → start kolejnego M. NEEDS REVISION → Developer poprawia, re-handoff.

Nie startuj kolejnego M bez PASS. To bufor przed architectural drift.

---

## Mierzenie postępu

Każdy milestone = 1 pozycja checklist. Faza 1 = 18 milestone'ów. Raport postępu:

```
[x] M1 — Alembic initial migration + smoke CRUD
[x] M2 — Reference data (Locations + Categories)
[ ] M3 — Auth core
...
```

Wklej do `documents/human/reports/serce_faza1_progress.md` i aktualizuj po każdym PASS.
