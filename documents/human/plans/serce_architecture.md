# Architektura projektu Serce

Date: 2026-04-09
Updated: 2026-04-10 (v6)
Status: Accepted — gotowy do implementacji (Faza 1)
Author: Architect

---

## Koncepcja

Serce to platforma wzajemnej pomocy. Użytkownicy wymieniają się usługami,
płacąc "sercami" — wewnętrzną walutą systemu. Serca nigdy nie mają wartości
pieniężnej. Można je zdobyć świadcząc usługi lub otrzymując je od innych.
Można poprosić o pomoc bez serc — duch projektu: pomagajmy sobie nawzajem.

---

## Stack technologiczny

| Warstwa | Technologia | Uzasadnienie |
|---|---|---|
| Backend | FastAPI (Python 3.12) | Async, typowany, najszybszy DX w Python |
| Baza danych | PostgreSQL 16 | Transakcje ACID (krytyczne przy transferach serc) |
| ORM / migracje | SQLAlchemy 2.x + Alembic | Standard produkcyjny |
| Frontend web | Next.js 14 (React, TypeScript) | SSR (SEO), duży ekosystem |
| Mobile | React Native + Expo | Współdzielony API client z Next.js, jeden team |
| Auth | JWT (access 15min, refresh 30 dni) + DB refresh tokens | Bezstanowe access, unieważnialny refresh |
| Konteneryzacja | Docker + docker-compose | Lokalne dev i deployment |

Redis, message queue, CDN — nie w v1. Dodajemy gdy potrzeba się manifestuje.

Deployment: decyzja po MVP. Docker umożliwia deploy na dowolną platformę (VPS, Railway, Render, AWS).

---

## Struktura repozytorium

```
serce/
  backend/
    app/
      core/          # encje domenowe, reguły biznesowe (NO SQL)
      api/           # FastAPI routery (v1/)
      db/            # modele SQLAlchemy, migracje Alembic
      services/      # logika aplikacyjna (łączy core + db)
      schemas/       # Pydantic schemas (request/response)
      auth/          # JWT logic, SMS OTP, token rotation
    tests/
      unit/
      integration/
    pyproject.toml
    Dockerfile
  frontend/
    src/
      components/
      app/           # Next.js App Router (pages)
      hooks/
      lib/api/       # API client (współdzielony z mobile)
    package.json
    Dockerfile
  mobile/
    src/
      screens/
      components/
      lib/api/       # symlink lub package → frontend/src/lib/api
    package.json
  docs/
    architecture/    # ADR files (→ documents/architecture/ADR-SERCE-*.md)
  docker-compose.yml
  .env.example
```

---

## Model domenowy

### User

```
id: UUID (PK)
email: str (unique, NOT NULL)
email_verified: bool (DEFAULT false)
username: str (unique, NOT NULL)
password_hash: str
phone_number: str (unique, nullable)       ← jeden numer = jedno konto
phone_verified: bool (DEFAULT false)
heart_balance: int (>= 0 AND <= heart_balance_cap, DEFAULT 0)  ← 0 przy rejestracji, grant po weryfikacji telefonu
location_id: FK → Location (nullable)  ← NULL = brak lokalizacji; feed pokazuje tylko NATIONAL scope
bio: str (nullable)
is_active: bool (DEFAULT true)
is_admin: bool (DEFAULT false)             ← dostęp do panelu admina i flag queue
deleted_at: datetime (nullable)            ← NULL = aktywny; soft delete
anonymized_at: datetime (nullable)         ← NULL = dane osobowe w DB; ustawiane razem z deleted_at
created_at: datetime
```

**Uwagi:**
- `heart_balance` zaczyna się od 0. INITIAL_GRANT (5 serc) następuje po weryfikacji telefonu.
- `heart_balance_cap` konfigurowany przez `SystemConfig` (DEFAULT 50).
- Po soft delete: email/username zastępowane hashem (`deleted_a3f2b1@serce.pl`), dane osobowe usuwane.
  Historia Exchange, HeartLedger, Review — zachowana (powiązana z UUID).

### RefreshToken

```
id: UUID (PK)
user_id: UUID (FK User, CASCADE DELETE)
token_hash: str (NOT NULL)   ← hash tokena, nie plaintext
device_info: str (nullable)  ← "iPhone 15, iOS 18"
ip_address: str (nullable)
created_at: datetime
expires_at: datetime
revoked_at: datetime (nullable)  ← NULL = aktywny
```

Token rotation: przy każdym `POST /auth/refresh` stary token revoked, nowy wydany.
httpOnly cookie dla refresh tokena (XSS protection) + Bearer header dla access tokena.

### Location (geograficzna hierarchia)

```
id: int (PK)
name: str
type: enum [VOIVODESHIP, CITY]
parent_id: int (self-ref FK, nullable)  ← CITY → VOIVODESHIP
```

Dane preloadowane: 16 województw + ~100 największych miast.
Brak pełnej bazy TERYT GUS — uproszczona hierarchia wystarczy na v1.
Rozszerzenie do pełnej bazy gminy/powiaty gdy użytkownicy zgłoszą potrzebę.

### HeartLedger (księga serc — audit trail)

```
id: UUID (PK)
from_user_id: UUID (nullable — NULL = SYSTEM grant)
to_user_id: UUID (NOT NULL)
amount: int (> 0)
type: enum [INITIAL_GRANT, PAYMENT, GIFT, ADMIN_GRANT]
related_exchange_id: UUID (nullable)
note: str (nullable)
created_at: datetime
```

`heart_balance` na User = szybki odczyt.
HeartLedger = pełen audit trail + możliwość rekonstrukcji balansu.

**Constraint:** UNIQUE `(to_user_id)` WHERE `type = 'INITIAL_GRANT'` — jeden grant na konto.

**Transfer serc = DB transaction:**
1. SELECT heart_balance FOR UPDATE (sender)
2. CHECK balance >= amount
3. CHECK recipient balance + amount <= heart_balance_cap (zwróć 422 z `max_receivable` jeśli przekracza)
4. UPDATE user SET heart_balance -= amount (sender)
5. UPDATE user SET heart_balance += amount (recipient)
6. INSERT HeartLedger
7. COMMIT

### Request (prośba o pomoc)

```
id: UUID (PK)
user_id: UUID (FK User — requester)
title: str
description: str
hearts_offered: int (>= 0, DEFAULT 0)  ← 0 = bezpłatna prośba
category_id: int (FK Category)
location_id: int (FK Location — skąd prosi)
location_scope: enum [CITY, VOIVODESHIP, NATIONAL]
status: enum [OPEN, IN_PROGRESS, DONE, CANCELLED]
created_at: datetime
expires_at: datetime (nullable)
```

hearts_offered = 0 jest pełnoprawnym stanem, nie wyjątkiem.
Pomagający sam decyduje czy przyjąć prośbę bez serc.

### Offer (oferta pomocy)

```
id: UUID (PK)
user_id: UUID (FK User — helper)
title: str
description: str
hearts_asked: int (>= 0, DEFAULT 0)
category_id: int (FK Category)
location_id: int (FK Location)
location_scope: enum [CITY, VOIVODESHIP, NATIONAL]
status: enum [ACTIVE, PAUSED, INACTIVE]
created_at: datetime
```

### Exchange (wymiana — kontrakt między stronami)

```
id: UUID (PK)
request_id: UUID (nullable)               ← FK Request; NULL gdy Exchange pochodzi z Offer
offer_id: UUID (nullable)                 ← FK Offer;   NULL gdy Exchange pochodzi z Request
requester_id: UUID (FK User)              ← kto potrzebuje pomocy (semantyczna rola)
helper_id: UUID (FK User)                 ← kto pomaga (semantyczna rola)
initiated_by: UUID (FK User)              ← kto stworzył Exchange (helper lub requester)
hearts_agreed: int (>= 0)
status: enum [PENDING, ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED]
created_at: datetime
completed_at: datetime (nullable)
```

**Constraint:**
```sql
CHECK (request_id IS NOT NULL OR offer_id IS NOT NULL)
```

**Uwagi:**
- Status `DISPUTED` usunięty. Platforma działa na zasadzie dobrej wiary obu stron.
  W razie problemu: POST /exchanges/{id}/flag → admin interweniuje ręcznie.
- PENDING = rozmowa wstępna. Wiadomości dostępne od PENDING. Wiele PENDING per Exchange-source dozwolone.
- `POST /exchanges/{id}/accept` — dostępny wyłącznie dla strony która NIE jest `initiated_by`.
- Transfer serc następuje przy status → COMPLETED.
- Brak zamrożenia serc przy ACCEPTED — uproszcza UX v1.

**Przepływy inicjacji (dwukierunkowe):**
```
Request-first (helper inicjuje):
  Helper → POST /exchanges {request_id, hearts_agreed}
  initiated_by = helper_id
  Requester widzi wiele PENDING → wybiera → POST /exchanges/{id}/accept
  → Exchange: ACCEPTED; pozostałe PENDING dla tego request_id → auto-CANCELLED

Offer-first (requester inicjuje):
  Requester → POST /exchanges {offer_id, hearts_agreed}
  initiated_by = requester_id; helper_id = Offer.user_id
  Helper → POST /exchanges/{id}/accept (lub odrzuca → CANCELLED)
  → Exchange: ACCEPTED; inne PENDING per offer_id — pozostają aktywne
    (Offer = stała wizytówka, bez limitu jednoczesnych ACCEPTED)
```

**DB constraints:**
```sql
-- Jeden ACCEPTED per Request (nie per Offer)
CREATE UNIQUE INDEX uix_exchange_request_accepted
  ON exchanges(request_id)
  WHERE status IN ('accepted', 'in_progress', 'completed')
  AND request_id IS NOT NULL;
```

### Review (ocena po wymianie)

```
id: UUID (PK)
exchange_id: UUID (FK Exchange)
reviewer_id: UUID (FK User)
reviewed_id: UUID (FK User)
comment: str (NOT NULL)
created_at: datetime

UNIQUE(exchange_id, reviewer_id)  ← jedna ocena per strona per wymiana (max 2 per Exchange)
```

Forma: komentarz tekstowy, brak gwiazdek. Wystawiana po COMPLETED.
Obustronność: obie strony mogą wystawić ocenę (dwa wpisy per Exchange).
Komentarze publiczne na profilu — społeczność weryfikuje reputację.
Komentarze zachowane po soft delete autora (widoczne jako "Użytkownik usunięty").

### SystemConfig (konfiguracja admina)

```
key: str (PK)
value: str
updated_at: datetime
updated_by: UUID (FK User — admin)
```

Przykładowe klucze:
- `request_default_expiry_days` — domyślna liczba dni do wygaśnięcia prośby
- `initial_heart_grant` — ile serc dostaje nowy user po weryfikacji telefonu (DEFAULT: 5)
- `heart_balance_cap` — maksymalny balans serc (DEFAULT: 50)
- `flag_admin_alert_days` — po ilu dniach bez rozwiązania flagi alert do admina (DEFAULT: 7)

### PasswordResetToken

```
id: UUID (PK)
user_id: UUID (FK User, CASCADE DELETE)
token_hash: str (NOT NULL)
created_at: datetime
expires_at: datetime     ← 15 minut
used_at: datetime (nullable)  ← NULL = nieużyty
```

### Notification

```
id: UUID (PK)
user_id: UUID (FK User)
type: enum [NEW_EXCHANGE, EXCHANGE_ACCEPTED, EXCHANGE_COMPLETED,
            NEW_MESSAGE, EXCHANGE_CANCELLED, NEW_REVIEW]
related_exchange_id: UUID (nullable)
related_message_id: UUID (nullable)
is_read: bool (DEFAULT false)
created_at: datetime
```

Tworzona automatycznie przy każdym zdarzeniu. Email wysyłany równolegle przy INSERT.
Endpointy: `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`.

### ExchangeFlag

```
id: UUID (PK)
exchange_id: UUID (FK Exchange)
reported_by: UUID (FK User)
reason: str (NOT NULL)
created_at: datetime
resolved_at: datetime (nullable)
resolved_by: UUID (nullable, FK User — admin)
resolution_note: str (nullable)
```

### Message

```
id: UUID (PK)
exchange_id: UUID (FK Exchange)
sender_id: UUID (FK User)
content: str
created_at: datetime
```

Wiadomości powiązane z Exchange — kontakt w ramach konkretnej wymiany.
Dostępne od stanu PENDING (komunikacja przed zobowiązaniem).

### Category

```
id: int (PK)
name: str
parent_id: int (nullable, hierarchiczna)
icon: str (nullable)
```

Przykłady: Transport, Dom i ogród, Nauka, IT, Gotowanie, Opieka, Rękodzieło.

---

## Kluczowe przepływy

### Rejestracja

1. User POST /auth/register → walidacja email/username (+ CAPTCHA, IP rate limit, temp-mail denylist)
2. hash password → INSERT User (heart_balance=0, email_verified=false, is_admin=false)
3. Wyślij email weryfikacyjny → POST /auth/verify-email
4. User POST /auth/verify-phone → SMS OTP
5. Po weryfikacji telefonu: INSERT HeartLedger (type=INITIAL_GRANT, amount=initial_heart_grant)
   UPDATE User SET heart_balance=5, phone_verified=true
6. Zwróć JWT (access token) + refresh token w httpOnly cookie

### Reset hasła

1. User POST /auth/forgot-password {email}
2. INSERT PasswordResetToken (expires_at = now + 15min)
3. Email z linkiem: /reset-password?token=<plaintext>
4. User POST /auth/reset-password {token, new_password}
5. Weryfikacja token_hash, sprawdzenie expires_at i used_at
6. UPDATE User SET password_hash = new_hash
7. UPDATE PasswordResetToken SET used_at = now()
8. Revoke wszystkich refresh_tokens usera (wymuś re-login)

**Anti-farming layers:**
- CAPTCHA na formularzu rejestracji
- IP rate limit: max 3 rejestracje / IP / 24h (FastAPI middleware)
- Temp-mail denylist: odrzucaj znane domeny jednorazowych emaili
- phone_number UNIQUE — jeden numer = jeden INITIAL_GRANT
- HeartLedger UNIQUE `(to_user_id, INITIAL_GRANT)` — DB-level guard

### Wystawienie prośby

1. User POST /requests → Request z hearts_offered (może być 0)
2. Widoczna w feedzie filtrowanym po location_scope

### Flow A: Request-first (helper inicjuje)

1. Helper POST /exchanges {request_id, hearts_agreed} → Exchange (PENDING, initiated_by=helper)
2. Obie strony piszą przez POST /exchanges/{id}/messages (dostępne od PENDING)
3. Requester POST /exchanges/{id}/accept → ACCEPTED
   - Pozostałe PENDING dla tego request_id → auto-CANCELLED (ExchangeService)
   - Request status → IN_PROGRESS
4. Usługa wykonana → requester POST /exchanges/{id}/complete
   - Walidacja: requester balance >= hearts_agreed
   - Walidacja: helper balance + hearts_agreed <= cap (422 z `max_receivable` jeśli nie)
   - DB transaction: transfer serc requester → helper + INSERT HeartLedger
   - Exchange status → COMPLETED, Request status → DONE
5. (opcjonalnie) Obie strony POST /exchanges/{id}/review → komentarz

### Flow B: Offer-first (requester inicjuje)

1. Requester POST /exchanges {offer_id, hearts_agreed} → Exchange (PENDING, initiated_by=requester)
   helper_id = Offer.user_id; requester_id = caller
2. Obie strony piszą przez POST /exchanges/{id}/messages
3. Helper POST /exchanges/{id}/accept → ACCEPTED
   - Inne PENDING dla tego offer_id — pozostają (Offer = stała wizytówka, bez limitu)
4. Dalej identycznie jak Flow A (kroki 4-5)

### Darowizna serc

1. User POST /hearts/gift → {to_user_id, amount, note}
2. Walidacja balance >= amount
3. Walidacja: recipient nie przekroczy cap
4. Transfer (jak wyżej, type=GIFT)

### Usunięcie konta

1. User DELETE /users/me
2. `deleted_at = now()`, `is_active = false`
3. email / username zastąpione hashem, phone_number = NULL → `anonymized_at = now()`
4. Historia Exchange / HeartLedger / Review — zachowana (UUID powiązania niezmienione)
5. Refresh tokens — wszystkie revoked

---

## Reguły biznesowe (enforced w services/)

1. `heart_balance >= 0 AND <= heart_balance_cap` zawsze — DB CHECK + aplikacyjna walidacja
2. Transfer serc atomowy — zawsze w DB transaction
3. hearts_offered=0 dozwolone wszędzie — nie blokuj
4. Exchange można anulować do ACCEPTED (brak konsekwencji — serca nie zamrożone)
5. Po COMPLETED — brak odwołania; w razie sporu: POST /exchanges/{id}/flag → admin
6. Jeden ACCEPTED Exchange per Request — partial unique index w DB (nie dotyczy Offer)
7. Przy akceptacji Request-first Exchange → pozostałe PENDING dla tego request_id → auto-CANCELLED
8. Wygasanie próśb: expires_at ustawiane wg SystemConfig.request_default_expiry_days
9. Jeśli transfer przekroczyłby heart_balance_cap helpera → 422 z polem `max_receivable`
   (brak cichego obcinania — helper decyduje co zrobić)
10. INITIAL_GRANT: jeden per user (HeartLedger unique constraint), trigger = weryfikacja telefonu
11. Soft delete: anonimizacja danych osobowych przy usunięciu konta (GDPR compliance)
12. Reset hasła: po użyciu tokena revokowane są wszystkie refresh_tokens usera
13. `initiated_by` w Exchange determinuje kto może wywołać /accept (tylko druga strona)
14. Przy każdym zdarzeniu (ACCEPTED, COMPLETED, NEW_MESSAGE itd.) → INSERT Notification + wyślij email
15. APScheduler uruchomiony przy starcie aplikacji: co godzinę wygasza Requests z przekroczonym expires_at
16. Edycja Request: tylko status=OPEN; zmiana hearts_offered zablokowana gdy istnieje ≥1 PENDING Exchange (422)
19. Feed publiczny (bez JWT): GET /requests, GET /offers, GET /users/{id}; operacje zapisu wymagają konta
20. location_id nullable: brak lokalizacji → tylko NATIONAL scope w feedzie
17. Review niemodyfikowalne po wystawieniu — brak PATCH /reviews/{id}
18. Zmiana email/username wymaga weryfikacji (analogicznie do password reset flow)

---

## Fazy implementacji (dla Developera)

### Faza 1 — Backend core (MVP)

- [ ] Setup: FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker
- [ ] Auth: register (+ CAPTCHA validation, IP rate limit, temp-mail check), login, refresh (token rotation), logout, logout-all
- [ ] Auth: verify-email (token link), verify-phone (SMS OTP)
- [ ] Auth: forgot-password + reset-password (PasswordResetToken)
- [ ] Auth: sessions endpoint (GET /auth/sessions — lista aktywnych refresh tokens)
- [ ] Profil: PATCH /users/me (bio, location_id); PATCH /users/me/username + PATCH /users/me/email (z weryfikacją)
- [ ] Soft delete: DELETE /users/me (anonimizacja)
- [ ] Locations: preload województwa + wybrane miasta
- [ ] Categories: preload bazowe kategorie
- [ ] Hearts: transfer, gift, balance endpoint
- [ ] Requests: CRUD + listing z filtrami (location_scope, category, status); PATCH /requests/{id} (title/description/expires_at, tylko OPEN, hearts_offered zablokowany gdy PENDING Exchange)
- [ ] Offers: CRUD + listing; PATCH /offers/{id} (title/description/hearts_asked); PATCH /offers/{id}/status (ACTIVE/PAUSED/INACTIVE)
- [ ] Exchanges: create (PENDING, dwukierunkowy), accept (tylko non-initiator), complete, cancel + messages
- [ ] Exchanges: auto-cancel pozostałych PENDING przy akceptacji Request-first Exchange
- [ ] Reviews: create po COMPLETED (UNIQUE exchange_id + reviewer_id)
- [ ] Flag endpoint: POST /exchanges/{id}/flag → INSERT ExchangeFlag
- [ ] Notifications: INSERT przy każdym zdarzeniu + email wysyłany równolegle; GET /notifications, POST /notifications/{id}/read
- [ ] Background job: APScheduler — co godzinę CANCELLED wygasłe Requests (expires_at < now, status=OPEN)
- [ ] Paginacja: wszystkie listing endpoints (requests, offers, exchanges, notifications) — ?page + ?limit
- [ ] Testy: unit (services) + integration (API endpoints)

### Faza 2 — Frontend web

- [ ] Setup: Next.js, TypeScript, API client
- [ ] Auth: login, register (+ CAPTCHA), email/phone verification flow
- [ ] Feed: przeglądanie próśb i ofert, filtry geograficzne
- [ ] Exchange flow: PENDING → wiadomości → ACCEPTED → COMPLETED
- [ ] Wiadomości w Exchange
- [ ] Moje konto: historia serc, moje prośby/oferty, aktywne sesje
- [ ] Profil: historia reviews

### Faza 3 — Mobile

- [ ] Setup: React Native + Expo
- [ ] Współdzielony API client z frontendem
- [ ] Funkcjonalność równoważna z web (mobile-first UX)

### Faza 4 — Rozszerzenia

- [ ] Powiadomienia (push mobile, email)
- [ ] Admin panel (ADMIN_GRANT serc, moderacja, widok flagowanych Exchange)
- [ ] Wyszukiwanie pełnotekstowe (PostgreSQL FTS)
- [ ] Heart balance cap progresywny (rośnie z liczbą udanych wymian)
- [ ] Redis dla refresh tokens (gdy skala tego wymaga)

---

## Decyzje projektowe (zamknięte)

| # | Pytanie | Decyzja |
|---|---|---|
| 1 | Zamrożenie serc przy ACCEPTED? | ✗ Brak zamrożenia. Transfer dopiero przy COMPLETED. |
| 2 | Wygasanie próśb — default? | Admin ustala przez SystemConfig (expires_at konfigurowalne). |
| 3 | Limit serc? | Górny limit konfigurowalny (DEFAULT 50). DB CHECK constraint. SystemConfig: `heart_balance_cap`. |
| 4 | Rating/reputacja? | Komentarz tekstowy po COMPLETED. Brak gwiazdek w v1. |
| 5 | Lokalizacje — TERYT pełna baza? | Nie. 16 województw + ~100 największych miast. |
| 6 | Deployment? | Decyzja po MVP. Docker zapewnia przenośność. |
| 7 | Email verification? | Tak — wymagana przed pełnym dostępem. |
| 8 | Anti-farming? | Phone verification = gate do INITIAL_GRANT. CAPTCHA + IP rate limit + temp-mail denylist jako warstwy uzupełniające. |
| 9 | Refresh token storage? | DB (tabela refresh_tokens) + token rotation. httpOnly cookie. Endpointy logout + logout-all + sessions. |
| 10 | Nadwyżka serc przy transferze? | 422 z `max_receivable` — brak cichego obcinania. Helper decyduje. |
| 11 | Soft delete? | Tak. deleted_at + anonymized_at. Dane osobowe usuwane, historia Exchange/Ledger/Review zachowana. GDPR-ready. |
| 12 | Dispute mechanism? | Brak w v1. Platforma działa na dobrej wierze. Flag endpoint → admin ręcznie. |
| 13 | COUNTY w location_scope? | Usunięte. Zakres: CITY / VOIVODESHIP / NATIONAL. |
| 14 | Komunikacja przed Exchange? | PENDING Exchange = rozmowa wstępna. Wiele PENDING per Request dozwolone. Jeden ACCEPTED — partial unique index. |
| 15 | Review unique constraint? | UNIQUE(exchange_id, reviewer_id) — jedna ocena per strona per Exchange (max 2 total). |
| 16 | Offer → Exchange flow? | Dwukierunkowy. Request-first: helper inicjuje. Offer-first: requester inicjuje. `initiated_by` determinuje kto akceptuje. |
| 17 | Limit ACCEPTED per Offer? | Brak. Offer = stała wizytówka. Helper może obsługiwać wielu jednocześnie. |
| 18 | Admin role w modelu? | `is_admin: bool` na User (DEFAULT false). Prosta i wystarczająca na v1. |
| 19 | Exchange bez Request i Offer? | Niedozwolone. CHECK (request_id IS NOT NULL OR offer_id IS NOT NULL). |
| 20 | Password reset? | Tabela PasswordResetToken (DB-backed, expires 15min). Po użyciu: revoke wszystkich refresh_tokens. |
| 21 | Flag mechanism? | Osobna tabela ExchangeFlag (reported_by, reason, resolved_by, resolution_note). |
| 22 | Powiadomienia? | Email + in-app (tabela Notification). Tworzone przy każdym zdarzeniu, email wysyłany równolegle. Faza 1. |
| 23 | Paginacja feedu? | Wymagana od Fazy 1. Wszystkie listing endpoints: ?page + ?limit. |
| 24 | Negocjacja hearts_agreed? | Brak. Stały przy CREATE = Request.hearts_offered. |
| 25 | Wygasanie Request? | APScheduler co godzinę: UPDATE status=CANCELLED WHERE expires_at < now AND status=OPEN. |
| 26 | Edycja Request po opublikowaniu? | `PATCH /requests/{id}` — tylko pola `title / description / expires_at`, tylko gdy `status = OPEN`. Zmiana `hearts_offered` zablokowana gdy istnieje ≥1 PENDING Exchange (422). |
| 27 | Edycja Offer po opublikowaniu? | `PATCH /offers/{id}` — pola `title / description / hearts_asked` edytowalne w każdym stanie. Zmiana statusu przez osobny endpoint `PATCH /offers/{id}/status` (ACTIVE ↔ PAUSED ↔ INACTIVE). |
| 28 | Edycja profilu użytkownika? | `PATCH /users/me` — pola `bio`, `location_id`. Zmiana `username` i `email` przez osobne endpointy z weryfikacją (analogicznie do password reset). |
| 29 | Edycja Review po wystawieniu? | Brak. Review jest niemodyfikowalne po wystawieniu. Integralność reputacji ważniejsza niż wygoda edycji. |
| 30 | Publiczny dostęp do feedu (bez konta)? | Tak. GET /requests, GET /offers, GET /users/{id} (profil publiczny) — dostępne bez JWT. Tworzenie, odpowiadanie, wiadomości, transfer serc — wymagają konta. |
| 31 | location_id wymagane przy rejestracji? | Nullable. Brak lokalizacji → feed pokazuje tylko NATIONAL scope. Soft requirement: UX motywuje do podania, nie wymuszamy technicznie. |

---

## ADR powiązane

- `ADR-SERCE-001-stack.md` — wybór stack (FastAPI, Next.js, React Native)
- `ADR-SERCE-002-hearts-ledger.md` — serca jako księga, nie obiekty
