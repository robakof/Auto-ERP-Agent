# Serce — analiza stanu projektu

Date: 2026-04-13
Author: Developer
Source: `serce/`, `documents/architecture/ADR-SERCE-*`, `documents/human/plans/serce_architecture.md` (v16)

---

## TL;DR

Faza architektoniczna dojrzała: plan v16 (932 linii), 5 ADR, głęboki review v2 (wszystkie luki zamknięte przed kodem).
Implementacja ledwo ruszyła — tylko **2 commity**: scaffold FastAPI + 19 modeli domenowych.
**Brak:** migracji Alembic, endpointów biznesowych, serwisów, schematów Pydantic, autoryzacji, frontendu, mobile.
Następny krok po handoffie #50: Faza 1 / Blok 1 (scaffold+auth) — scaffold jest gotowy, więc kolejne w kolejce to **auth + hearts ledger**.

---

## Co istnieje

### Dokumentacja (dojrzała)
- `serce_architecture.md` v16 — 932 linii, 105 decyzji, 53 endpointy, stan: Accepted
- ADR-001..005 (stack, hearts-ledger, account-lifecycle, admin-moderation, user-resources-api)
- Review v2 — wszystkie konflikty, luki, dwuznaczności rozwiązane przed implementacją

### Kod — backend (`serce/backend/`)
- **Scaffold FastAPI** (commit `30c9ebb`): main.py, config (Pydantic Settings), CORS, v1_router, `/health`
- **19 modeli domenowych** (commit `d980d8f`) w `app/db/models/`:
  - Auth: User, RefreshToken, PasswordResetToken, EmailChangeToken, EmailVerificationToken, PhoneVerificationOTP, UserConsent
  - Domain: Location, Category, HeartLedger, Request, Offer, Exchange, Review, Message, Notification
  - Admin: ContentFlag, AdminAuditLog, SystemConfig
  - Constrainty DB zgodne z planem: `heart_balance >= 0`, partial unique index na Exchange ACCEPTED per Request, UNIQUE(exchange_id, reviewer_id) na Review
- **Infra:** Dockerfile, docker-compose (backend + postgres:16-alpine + healthcheck + volume)
- **Alembic:** env.py skonfigurowany (async engine, Base.metadata), ale **katalog `versions/` pusty** — brak pierwszej migracji
- **Testy:** `test_health.py` + `test_models.py` (weryfikacja metadata, 19 tabel, constrainty) — schema-level, bez integracji DB

### Kod — frontend / mobile
- **Brak.** Katalogi `frontend/` i `mobile/` nieutworzone.

---

## Czego brakuje (wg planu v16)

### Krytyczne dla uruchomienia
1. **Migracja Alembic `versions/0001_initial.py`** — `alembic revision --autogenerate` jeszcze nie odpalone
2. **Schematy Pydantic** (`app/schemas/`) — katalog pusty
3. **Serwisy** (`app/services/`) — katalog pusty, brak HeartTransferService, ExchangeService, AuthService
4. **Core domain** (`app/core/`) — katalog pusty (encje domenowe, reguły biznesowe bez SQL)
5. **Auth** (`app/auth/`) — katalog pusty, brak JWT, password hashing, SMS OTP, token rotation
6. **.env** (dev) — tylko `.env.example` (niewidoczny w git status, zakładam że istnieje lub nie)

### Endpointy (53 w planie, zaimplementowane: 1 = /health)
Brak wszystkich endpointów biznesowych: auth (13), users (14), requests (5), offers (5), exchanges (7), reviews (1), hearts (1), flag (4), admin (7).

### Infrastruktura operacyjna
- Brak APScheduler (wygaszanie Request, cleanup tokenów)
- Brak integracji: SMSAPI.pl, Resend, hCaptcha
- Brak deploymentu (nginx, certbot, UFW, backup)
- Brak rate limiting, CAPTCHA middleware

---

## Stan na tle handoffu #50 (2026-04-11)

Handoff mówi: "Faza 1 / Blok 1 (scaffold...)" jako next-action.
Scaffold + modele wykonane w komitach `30c9ebb` i `d980d8f` tego samego dnia (2026-04-11) — więc **Blok 1 w połowie**:
- ✓ Scaffold FastAPI
- ✓ Modele SQLAlchemy (przed migracją)
- ✗ Alembic autogenerate + review + apply
- ✗ Auth module (JWT + refresh tokens)
- ✗ Hearts ledger service (transfer w transakcji)

Plan implementacji w pliku nie został znaleziony (pytanie: czy w ogóle istnieje rozpisanie faz/bloków?).

---

## Ryzyka i obserwacje

1. **Brak planu implementacji per-faza** — architektura v16 jest, ale nie widziałem rozpisania Fazy 1 na bloki/kamienie milowe. Handoff #50 wspomina "Blok 1" — rozpisanie może być w inbox architekta (msg #47, #49) lub nigdzie.
2. **`serce_backend.egg-info` w repo** — artefakty build zaindeksowane przez git? (nie mam git status dla `serce/` bo jest w root). Warto sprawdzić `.gitignore`.
3. **Enum style niespójny** — UserStatus używa lowercase ("active"), ExchangeStatus używa uppercase ("PENDING"). Plan v16 używa uppercase wszędzie. Drobna inkonsystencja do ujednolicenia.
4. **Testy `test_models.py` nie ruszają DB** — walidują tylko metadata. Brak integration testów dla CHECK constraints, partial indexów (wymagają PostgreSQL, nie SQLite).
5. **`docker-compose.yml` bez pgAdmin / mailhog** — OK dla v1, ale warto rozważyć przy auth development.

---

## Rekomendacja kolejnych kroków

Jeśli kontynuujemy Fazę 1 / Blok 1:
1. **Wygenerować migrację:** `alembic revision --autogenerate -m "initial schema"`, przejrzeć, zastosować — odblokuje integration testy
2. **Blind-spot check modeli:** porównać 19 tabel z planem v16 tabela po tabeli (walidacja że żaden model nie odbiega) — osobny task
3. **Ujednolicić enum case** (lowercase vs uppercase) — patch task
4. **Następny blok:** auth module (JWT + refresh + /register, /login) + hearts ledger service

Propozycja: zanim ruszę kod, **zapytać architekta o rozpisanie Fazy 1 na bloki** (jeśli nie istnieje — Developer może je zaproponować).

---

## Pytania do usera

1. Czy chcesz żebym kontynuował implementację od migracji Alembic + reszty Bloku 1?
2. Czy istnieje plan rozpisania Fazy 1 na bloki (poza handoffem #50)?
3. Czy ujednolicić enum case teraz czy odłożyć?
