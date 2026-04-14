# Serce — Pre-analiza milestone'ow Fazy 1

Date: 2026-04-14
Author: Architect
Podstawa: `serce_faza1_roadmap.md` (M1-M18), `serce_architecture.md` (v17, 110 decyzji), kod `serce/backend/`

---

## TL;DR

Modele SQLAlchemy sa w 90% zgodne z planem v17, ale **4 rozbieznosci musza byc naprawione
PRZED pierwsza migracja Alembic (M1)** — po migracji kazda zmiana to dodatkowy migration file.
Poza tym: 18 milestone'ow jest dobrze zdefiniowanych, ale kilka wymaga dodatkowych wytycznych
architektonicznych (warstwy, concurrency, testowanie).

---

## BLOK 0: Naprawy modeli PRZED M1

**Dlaczego teraz:** M1 generuje initial migration. Kazdy brak w modelach wykryty po M1
to osobny `alembic revision` + review + apply. Tansza opcja: naprawic modele, potem jedno `autogenerate`.

### 0.1 Category — brak `sort_order` i `active` (Critical)

**Decyzja #109:** `sort_order: int DEFAULT 0`, `active: bool DEFAULT true`.
**Model (`category.py`):** ma tylko `id, name, parent_id, icon`.

```python
# Brakuje:
sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
```

**Impact:** M2 (preload) uzywa `active` do filtrowania feedu (`WHERE categories.active=true`).
M7/M8 (Requests/Offers CRUD) potrzebuja `sort_order` do wyswietlania listy kategorii.
Brak tych pol = dodatkowa migracja po M2.

### 0.2 HeartLedger — brak UNIQUE partial index na INITIAL_GRANT (Critical)

**Plan v17:** `UNIQUE (to_user_id) WHERE type = 'INITIAL_GRANT'` — jeden grant na konto.
**Model (`heart.py`):** brak tego constraintu w `__table_args__`.

```python
# Brakuje w __table_args__:
Index(
    "uix_heart_ledger_initial_grant",
    "to_user_id",
    unique=True,
    postgresql_where=(type == "INITIAL_GRANT"),
)
```

**Impact:** Bez tego constraintu regula #10 (jeden INITIAL_GRANT per user) jest
enforced tylko aplikacyjnie. Race condition = podwojny grant. DB-level enforcement krytyczny
dla integralnosci serc.

### 0.3 Exchange partial index — weryfikacja skladni SQLAlchemy (Warning)

**Model (`exchange.py` linia 37-42):**
```python
Index(
    "uix_exchange_request_accepted",
    "request_id",
    unique=True,
    postgresql_where=(status.in_(["ACCEPTED", "COMPLETED"]) & (request_id.isnot(None))),
)
```

**Ryzyko:** Uzycie `status.in_([...])` na poziomie klasy (nie instancji) moze nie dzialac
prawidlowo w SQLAlchemy 2.x. Trzeba zweryfikowac:
1. Czy `autogenerate` wygeneruje poprawny SQL.
2. Jezeli nie — uzyc `text()`:
```python
postgresql_where=text("status IN ('ACCEPTED', 'COMPLETED') AND request_id IS NOT NULL")
```

**Impact:** Bledny partial index = brak guardu na wiele ACCEPTED per Request. Rdzen domeny.
Developer MUSI zweryfikowac wygenerowany SQL po `autogenerate` (krok review w M1).

### 0.4 Enum case — weryfikacja spojnosci (Warning)

**Wzorzec w planie v17:**
- Domain state machines (uppercase): `OPEN`, `PENDING`, `ACCEPTED`, `ACTIVE`, `INITIAL_GRANT`
- Admin/meta/flags (lowercase): `active`, `suspended`, `open`, `spam`, `tos`

**Modele sa zgodne z tym wzorcem** — to zamierzone rozroznienie.
Ale partial index w planie v17 (sekcja Exchange) ma literowke:
`WHERE status IN ('accepted', 'completed')` — powinno byc `('ACCEPTED', 'COMPLETED')`.
Developer niech uzywa wartosci enum z kodu (uppercase).

---

## BLOK 1: M1 — Alembic initial migration + smoke CRUD

**Rozmiar:** S (1-2h z review).
**Prerequisite:** Blok 0 (naprawy modeli).

### Wytyczne

1. **`alembic revision --autogenerate -m "initial_schema"`**
2. **REVIEW wygenerowanego pliku** — to najwazniejszy moment. Sprawdzic:
   - Wszystkie CHECK constraints obecne (heart_balance >= 0, amount > 0, hearts_offered >= 0, hearts_asked >= 0, exchange_has_source)
   - Partial unique indexes: `uix_exchange_request_accepted`, `uix_heart_ledger_initial_grant`
   - UniqueConstraint na Review (exchange_id, reviewer_id)
   - Enum types: czy Alembic generuje PostgreSQL ENUM (a nie VARCHAR)
   - CASCADE DELETE na tokenach (RefreshToken, PasswordResetToken, EmailChangeToken, EmailVerificationToken, PhoneVerificationOTP, UserConsent)
3. **`alembic upgrade head`** na swiezej bazie
4. **`alembic downgrade base`** — weryfikacja reversibility
5. **Smoke test:** INSERT user, INSERT location, INSERT category — happy path
6. **Nie ruszaj kodu serwisow/endpointow** — scope M1 = tylko migracja + weryfikacja schema

### Testy

```
tests/integration/db/test_schema.py:
  - test_all_tables_created (19 tabel)
  - test_check_constraints_enforced (heart_balance < 0 → IntegrityError)
  - test_unique_constraints (duplicate email → IntegrityError)
  - test_partial_index_exchange (2x ACCEPTED per request_id → IntegrityError)
  - test_partial_index_initial_grant (2x INITIAL_GRANT per user → IntegrityError)
  - test_cascade_delete_user_tokens (DELETE user → tokens gone)
```

**Uwaga:** testy wymagaja PostgreSQL (partial index, ENUM). Conftest powinien podnosic
testowa baze (docker-compose test profile lub testcontainers).

---

## BLOK 2: M2 — Reference data (Locations + Categories)

**Rozmiar:** S-M (pol dnia).
**Prerequisite:** M1.

### Wytyczne

1. **Alembic data migration** (nie `INSERT` w kodzie aplikacji):
   - `alembic revision -m "seed_locations"` — 16 wojewodztw + ~100 miast (decyzja #107: top-100 wg GUS, cutoff ~60k)
   - `alembic revision -m "seed_categories"` — 9 grup + 26 podkategorii (decyzja #106, sekcja "Bazowe kategorie" w planie v17)
   - `alembic revision -m "seed_system_config"` — klucze: `request_default_expiry_days=30`, `initial_heart_grant=5`, `heart_balance_cap=50`, `tos_current_version=1.0`, `privacy_current_version=1.0`, `flag_admin_alert_days=7`

2. **Endpointy (public, bez JWT):**
   - `GET /api/v1/locations` — z opcjonalnym `?scope=VOIVODESHIP|CITY`
   - `GET /api/v1/categories` — hierarchiczne (grupy z children)
   - Response cacheable (dane statyczne)

3. **Walidacja lisc kategorii (decyzja #110):**
   Logika `CATEGORY_MUST_BE_LEAF` bedzie potrzebna w M7/M8, ale juz teraz warto
   przygotowac utility: `is_leaf_category(category_id) -> bool`.

### Architektura warstw (wzorzec dla wszystkich M)

```
routes (api/v1/) → schemas (Pydantic) → services → repositories → DB
                                           ↑
                                        core/ (domain rules, NO SQL)
```

**Dla M2 to prosta sciezka**: route → query DB → zwroc. Brak service layer potrzebny.
Ale Developer MUSI zalozyc strukture katalogow: `app/services/`, `app/schemas/`, `app/core/`
z `__init__.py` i pierwszym przykladem (choby pusty base class).

### Pytanie otwarte

- **Population na Location?** Decyzja #107 mowi "Format: (name, voivodeship_parent_id, population)"
  ale model nie ma kolumny `population`. Czy to dane zrodlowe do preloadu, czy kolumna?
  **Rekomendacja Architekta:** nie dodawac — to dane referencyjne dla sortowania przy
  preloadzie. Jezeli kiedys trzeba sortowac po populacji w UI — Alembic migration.

---

## BLOK 3: M3 — Auth core (CRITICAL PATH)

**Rozmiar:** L (2-3 dni).
**Prerequisite:** M1.
**Ryzyko:** Wysokie — fundament bezpieczenstwa.

### Wytyczne architektoniczne

1. **Warstwy:**
   - `app/auth/jwt.py` — create_access_token, create_refresh_token, verify_token
   - `app/auth/password.py` — hash_password, verify_password (bcrypt)
   - `app/auth/dependencies.py` — `get_current_user()`, `require_admin()` (FastAPI Depends)
   - `app/services/auth_service.py` — register, login, refresh, logout (business logic)
   - `app/api/v1/auth.py` — routes (thin, deleguje do service)

2. **Refresh token rotation:**
   - Login → nowy RefreshToken + access token
   - Refresh → revoke stary, wydaj nowy (atomowo w transakcji)
   - httpOnly cookie dla refresh token (config: `Secure=True` w prod, `SameSite=Lax`)
   - Access token w response body (frontend trzyma w memory, nie w localStorage)

3. **Rate limiting:**
   - Register: IP-based, np. 5/godzine per IP
   - **Implementacja:** slowapi (integracja z FastAPI) lub custom middleware
   - Nie budowac custom rate limiter od zera — uzyc biblioteki

4. **Temp-mail denylist:**
   - Lista domen jednorazowych emaili (disposable-email-domains na GitHub)
   - Serwis: `is_disposable_email(email) -> bool`
   - Plik z domenami w `app/auth/disposable_domains.txt` lub JSON

5. **hCaptcha:**
   - Stub w testach (env `CAPTCHA_ENABLED=false`)
   - W prod: walidacja server-side (POST do hCaptcha verify endpoint)
   - **Nie blokuj reszty auth na hCaptcha** — CAPTCHA jest gate'em na register, nie na login

6. **SystemConfig vs env:**
   `config.py` ma `initial_heart_grant`, `heart_balance_cap` jako env vars.
   Plan mowi ze to SystemConfig (admin-edytowalne w runtime).
   **Decyzja architektoniczna:** env = defaults przy braku SystemConfig. Runtime reads z DB.
   Pattern: `get_config(key, default=settings.value_from_env)`.
   Developer implementuje to w M3 (uzywane od M4 dalej).

### Testy MUST-COVER

```
- test_register_happy_path
- test_register_duplicate_email → 409
- test_register_disposable_email → 422
- test_login_wrong_password → 401
- test_login_suspended_account → 401 ACCOUNT_SUSPENDED
- test_refresh_token_rotation (stary revoked, nowy wydany)
- test_refresh_expired_token → 401
- test_refresh_revoked_token → 401
- test_logout_revokes_current_session
- test_logout_all_revokes_all_sessions
- test_sessions_list
- test_session_delete_current → 422 CANNOT_REVOKE_CURRENT_SESSION
- test_accept_terms (UserConsent INSERT)
- test_rate_limit_register (6th request → 429)
```

---

## BLOK 4: M4 — Email & phone verification

**Rozmiar:** L (2 dni).
**Prerequisite:** M3.

### Wytyczne

1. **Email service (Resend.com):**
   - `app/services/email_service.py` — interface + Resend implementation
   - Mock w testach (nie wysylaj realnych maili)
   - Pattern: `EmailService` protocol → `ResendEmailService` (prod) + `MockEmailService` (test)

2. **SMS service (SMSAPI.pl):**
   - Analogicznie: protocol + implementation + mock
   - OTP: 6 cyfr, hash przechowywany, max 5 prob, wygasa po 10min

3. **INITIAL_GRANT trigger:**
   - Weryfikacja phone → `PhoneVerificationOTP.used_at = now()` → INSERT HeartLedger(INITIAL_GRANT)
   - Guard: partial unique index (Blok 0.2) gwarantuje DB-level
   - Aplikacyjnie: sprawdz czy user juz ma INITIAL_GRANT przed INSERT (fail gracefully)

4. **Resend email rate limit:**
   - 3/email/24h — liczone per email address, nie per user
   - Query: `COUNT(*) FROM email_verification_tokens WHERE user_id=X AND created_at > now()-24h`

---

## BLOK 5: M5 — User profile + email/phone change

**Rozmiar:** M (1 dzien).
**Prerequisite:** M4.

### Wytyczne

1. **Email change (bezpieczny flow):**
   - Wymaga password re-auth
   - EmailChangeToken (24h) wysylany na NOWY email
   - Powiadomienie na STARY email ("ktos zmienil Twoj email")
   - Po potwierdzeniu: revoke all refresh tokens (regula #25)

2. **Phone change:**
   - Wymaga password re-auth
   - OTP na NOWY numer
   - **Brak ponownego INITIAL_GRANT** — jawna walidacja

3. **Username change:**
   - Unique check
   - Brak re-verification (username nie jest security-critical)

---

## BLOK 6: M6 — Hearts ledger + transfer + gift + balance

**Rozmiar:** M (1-2 dni).
**Prerequisite:** M3.
**Ryzyko:** Wysokie — pieniadz systemu.

### Wytyczne architektoniczne

1. **HeartService — atomowy transfer:**
   ```python
   async def transfer(sender_id, recipient_id, amount, type, exchange_id=None):
       async with session.begin():
           sender = await session.get(User, sender_id, with_for_update=True)
           recipient = await session.get(User, recipient_id, with_for_update=True)
           # 1. balance >= amount
           # 2. recipient.heart_balance + amount <= cap
           # 3. UPDATE sender, UPDATE recipient, INSERT HeartLedger
   ```

2. **FOR UPDATE** — row-level locking. Kolejnosc lockow: zawsze `min(id), max(id)`
   zeby uniknac deadlocku przy rownoczesnych transferach A→B i B→A.

3. **Cap validation:**
   - `heart_balance_cap` z SystemConfig (nie z env!)
   - Przy przekroczeniu: 422 z `max_receivable = cap - recipient.balance`
   - **Nie obcinaj cicho** — user decyduje

4. **Pomiń INSERT HeartLedger gdy amount = 0** (regula #24)

### Testy MUST-COVER

```
- test_transfer_happy_path
- test_transfer_insufficient_balance → 422 BALANCE_INSUFFICIENT
- test_transfer_cap_exceeded → 422 CAP_EXCEEDED (+ max_receivable)
- test_transfer_concurrent_100x (asyncio.gather) → balance nigdy < 0
- test_gift_happy_path
- test_gift_zero_amount → skip HeartLedger (lub 422?)
- test_balance_endpoint
- test_ledger_pagination_with_type_filter
```

**Test wspolbieznosci jest kluczowy.** 100 rownoczesnych transferow z jednego konta (saldo=50, kazdy transfer=1).
Oczekiwany wynik: dokladnie 50 PASS, 50 FAIL (BALANCE_INSUFFICIENT). Balance = 0.

---

## BLOK 7: M7 + M8 — Requests + Offers CRUD

**Rozmiar:** M+M (2-3 dni lacznie).
**Prerequisite:** M2 (categories/locations), M5 (profile).

### Wytyczne

1. **Wspolny pattern:** Request i Offer maja niemal identyczna strukture (CRUD + filtry + paginacja).
   Developer moze wyciagnac wspolna logike:
   - `BaseFeedService` z filtrami (location_scope, category, status, q, sort, order, page, limit)
   - Lub po prostu 2 osobne serwisy jezeli roznica jest mala (pragmatyzm > abstrakcja)

2. **ILIKE search (`?q=`):**
   ```sql
   WHERE (title ILIKE '%query%' OR description ILIKE '%query%')
   ```
   Dla v1 wystarczy. FTS w Fazie 4.

3. **Leaf category validation (decyzja #110):**
   - `Request.category_id` i `Offer.category_id` musi wskazywac podkategorie
   - Walidacja aplikacyjna: `422 CATEGORY_MUST_BE_LEAF`

4. **Feed publiczny (bez JWT):** `GET /requests`, `GET /offers` — filtruj `WHERE owner.status='active'`
5. **hearts_offered guard (regula #16):** PATCH /requests/{id} — hearts_offered zablokowany gdy istnieje >= 1 PENDING Exchange

---

## BLOK 8: M9 — Exchange state machine (CORE DOMAIN)

**Rozmiar:** L (3-4 dni).
**Prerequisite:** M6, M7, M8.
**Ryzyko:** Najwyzsze — rdzen domeny.

### Wytyczne architektoniczne

1. **State machine jako explicit klasa w `app/core/`:**
   ```python
   class ExchangeStateMachine:
       TRANSITIONS = {
           (PENDING, "accept"): ACCEPTED,
           (PENDING, "cancel"): CANCELLED,
           (ACCEPTED, "complete"): COMPLETED,
           (ACCEPTED, "cancel"): CANCELLED,
       }
   ```
   **Nie rozrzucaj logiki transitions po endpointach.** Jedno zrodlo prawdy.

2. **Auto-cancel przy Request-first accept:**
   - Accept PENDING → ACCEPTED
   - Wszystkie inne PENDING dla tego `request_id` → CANCELLED
   - Notification do kazdego helpera ktorego Exchange zostal anulowany
   - **W jednej transakcji** (atomowosc)

3. **Complete = transfer serc:**
   - Exchange ACCEPTED → COMPLETED
   - `HeartService.transfer(requester_id, helper_id, hearts_agreed, type=PAYMENT, exchange_id=id)`
   - Jezeli `hearts_agreed = 0` → pomiń transfer, tylko status update
   - `Exchange.completed_at = now()`

4. **Guardy create:**
   - Request-first: Request.status=OPEN, `hearts_agreed = Request.hearts_offered` (regula #26)
   - Offer-first: Offer.status=ACTIVE, `hearts_agreed = Offer.hearts_asked` (regula #22)
   - Self-exchange: requester_id != helper_id (regula #21)
   - Suspended user: 422

5. **Cancel side-effects:**
   - Exchange PENDING/ACCEPTED → CANCELLED
   - Jezeli byl Request-first i Request.status=IN_PROGRESS → Request.status=OPEN

### Testy MUST-COVER

```
- test_create_request_first_happy_path
- test_create_offer_first_happy_path
- test_create_self_exchange → 422 SELF_EXCHANGE
- test_create_on_cancelled_request → 422
- test_create_on_paused_offer → 422
- test_create_hearts_mismatch → 422 HEARTS_MISMATCH
- test_accept_by_non_initiator (happy)
- test_accept_by_initiator → 403
- test_accept_auto_cancel_other_pending
- test_complete_with_transfer
- test_complete_zero_hearts (no HeartLedger entry)
- test_complete_concurrent (2x complete → only 1 succeeds)
- test_cancel_before_complete (happy)
- test_cancel_after_complete → 422 EXCHANGE_NOT_CANCELLABLE
- test_cancel_restores_request_to_open
- test_partial_unique_index (2x accept same request → IntegrityError)
- test_state_transitions_exhaustive (all invalid transitions → 422)
```

---

## BLOK 9: M10 + M11 — Messages + Reviews

**Rozmiar:** S+S (1 dzien lacznie).
**Prerequisite:** M9.

### M10 Messages
- Proste CRUD, autorizacja: tylko participants Exchange
- Sort ASC (chronologiczny), paginacja
- Wiadomosci dostepne od PENDING (nie czekac na ACCEPTED)

### M11 Reviews
- Create po COMPLETED only
- UNIQUE(exchange_id, reviewer_id) — DB-enforced
- Brak edycji (regula #27)
- `reviewed_id` = druga strona Exchange

---

## BLOK 10: M12 — User resources API

**Rozmiar:** M (1 dzien).
**Prerequisite:** M5, M7, M8, M9, M11, M6.

### Wytyczne
- Glownie READ endpointy: `/users/me/requests`, `/offers`, `/exchanges`, `/reviews`, `/ledger`
- `/users/me/summary` — agregat w jednym query (lub kilku rownoleglych)
- Exchange transparency: owner + participants widza pelne dane; rywale — zredukowany widok

---

## BLOK 11: M13 — Notifications

**Rozmiar:** M (1-2 dni).
**Prerequisite:** M4 (email service), M9 (zdarzenia).

### Wytyczne
- Notification INSERT przy kazdym zdarzeniu — **w tej samej transakcji co zdarzenie**
- Email wysylany **poza transakcja** (background task, best-effort)
- Pattern: `await notification_service.notify(user_id, type, context)` — re-uzywalny
- `FastAPI BackgroundTasks` dla emaili (nie blokuj response)

---

## BLOK 12: M14 + M15 — Flag + Admin

**Rozmiar:** S + L (2-3 dni lacznie).
**Prerequisite:** M7, M8, M9, M5.

### M14 Flags
- Decyzja #108: `422 CANNOT_FLAG_OWN_RESOURCE` (wyjątek: exchange dispute)
- Proste INSERT — nie wymaga skomplikowanej logiki

### M15 Admin
- `require_admin()` dependency
- Seed migration: INSERT User(role=admin) z `INITIAL_ADMIN_EMAIL` z env
- Suspend: revoke refresh tokens + audit log w jednej transakcji
- Unhide (decyzja #29): Offer → INACTIVE, Request → CANCELLED (user reaktywuje sam)

---

## BLOK 13: M16 — Soft delete

**Rozmiar:** L (2 dni).
**Prerequisite:** M15, M6, M12.
**Ryzyko:** Wysokie — atomowosc kaskady.

### Wytyczne
- Transakcyjna kaskada 8 krokow (ADR-SERCE-003 D6)
- Dyspozycja salda: `void` (serca przepadaja → HeartLedger ACCOUNT_DELETED) lub `transfer` (do wskazanego usera)
- Anonimizacja: email → `deleted_<hash>@serce.pl`, username → `deleted_<hash>`, phone → NULL, bio → NULL
- **Test atomowosci:** failure w kroku 5 = rollback wszystkiego

---

## BLOK 14: M17 — APScheduler

**Rozmiar:** S (pol dnia).
**Prerequisite:** M7.

### Wytyczne
- APScheduler lifecycle w `main.py` lifespan handler
- Job co godzine: expire Requests
- Idempotentny: podwojne uruchomienie nie psuje stanu
- Notification REQUEST_EXPIRED do ownera

---

## BLOK 15: M18 — Test coverage gate

**Rozmiar:** M (1-2 dni).
**Prerequisite:** Wszystkie M.

### Wytyczne
- Audyt MUST-COVER scenarios
- `pytest --cov` baseline
- Raport do `documents/human/reports/serce_faza1_coverage.md`

---

## Obserwacje dodatkowe

### `serce_backend.egg-info` w repo
Build artifact — dodac do `.gitignore`.

### Config dual-source (env vs SystemConfig)
Rozwiazac w M3: env = defaults, SystemConfig = runtime overrides.
Pattern: `get_config(key)` czyta z DB, fallback na `settings.X`.

### Brak `updated_at` na Request/Offer
Plan nie wymaga, ale PATCH operations bez `updated_at` utrudniaja diagnostyke.
**Rekomendacja:** dodac przed M1 — koszt = 2 linie per model, wartosc = lepszy debugging.

### Conftest + test DB
M1 wymaga PostgreSQL do testow integracyjnych. Developer musi ustawic:
- `docker-compose.test.yml` z osobna baza testowa, lub
- testcontainers-python, lub
- fixture z async connection do istniejacego PostgreSQL (port mapping)

Decyzja o podejsciu: Developer, ale Architect preferuje testcontainers (izolacja, CI-ready).

---

## Kolejnosc realizacji (sekwencyjna, 1 Developer)

```
Blok 0  (naprawy modeli)     → 2h
M1      (Alembic migration)  → S (pol dnia)
M2      (reference data)     → S-M (pol dnia)
M3      (auth core)          → L (2-3 dni)     ← krytyczna sciezka
M4      (email/phone verify) → L (2 dni)
M5      (user profile)       → M (1 dzien)
M6      (hearts)             → M (1-2 dni)     ← krytyczne: concurrency
M7+M8   (requests+offers)    → M+M (2-3 dni)
M9      (exchange)           → L (3-4 dni)     ← krytyczne: rdzen domeny
M10+M11 (messages+reviews)   → S+S (1 dzien)
M12     (user resources)     → M (1 dzien)
M13     (notifications)      → M (1-2 dni)
M14+M15 (flags+admin)        → S+L (2-3 dni)
M16     (soft delete)        → L (2 dni)
M17     (APScheduler)        → S (pol dnia)
M18     (coverage gate)      → M (1-2 dni)
```

**Szacowany total: ~20-25 dni roboczych** (1 Developer, z review po kazdym M).

---

## Decyzje potwierdzone (2026-04-14)

1. **Population na Location** — nie dodawac. Dane zrodlowe, nie kolumna. (decyzja #111)
2. **updated_at na Request/Offer** — dodac przed M1. (decyzja #112)
3. **Test DB strategy** — testcontainers-python. Izolacja, CI-ready. (decyzja #113)
4. **Rate limiter** — slowapi (in-memory). Furtka na Redis gdy distributed. (decyzja #114)
