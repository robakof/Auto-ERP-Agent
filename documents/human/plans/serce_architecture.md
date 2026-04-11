# Architektura projektu Serce

Date: 2026-04-09
Updated: 2026-04-11 (v14)
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
heart_balance: int (>= 0, DEFAULT 0)  ← DB CHECK >= 0; cap (<= heart_balance_cap) walidowany aplikacyjnie
location_id: FK → Location (nullable)  ← NULL = brak lokalizacji; feed pokazuje tylko NATIONAL scope
bio: str (nullable)
status: enum [active, suspended, deleted] (DEFAULT active)   ← zastępuje is_active (ADR-004 D5)
role: enum [user, admin] (DEFAULT user)                      ← zastępuje is_admin (ADR-004 D7)
suspended_at: datetime (nullable)          ← kiedy zawieszono
suspended_until: datetime (nullable)       ← NULL = permanentny ban
suspension_reason: str (nullable)
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
to_user_id: UUID (nullable — NULL = ACCOUNT_DELETED void)
amount: int (> 0)
type: enum [INITIAL_GRANT, PAYMENT, GIFT, ADMIN_GRANT, ADMIN_REFUND, ACCOUNT_DELETED]
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
status: enum [OPEN, IN_PROGRESS, DONE, CANCELLED, HIDDEN]  ← HIDDEN = admin hide_content (ADR-004 D3)
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
status: enum [ACTIVE, PAUSED, INACTIVE, HIDDEN]  ← HIDDEN = admin hide_content (ADR-004 D3)
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
- Transfer serc następuje przy status → COMPLETED. Jeśli hearts_agreed = 0 — pomiń INSERT HeartLedger.
- Brak zamrożenia serc przy ACCEPTED — upraszcza UX v1.
- `POST /exchanges/{id}/cancel` — dostępny dla obu stron w każdym momencie przed COMPLETED. Na cancel: Exchange → CANCELLED, Request → OPEN (jeśli był IN_PROGRESS).
- Self-exchange zablokowany: service zwraca 422 gdy initiator = druga strona Exchange.

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
- `tos_current_version` — aktualna wersja regulaminu (np. "1.0")
- `privacy_current_version` — aktualna wersja polityki prywatności (np. "1.0")

### PasswordResetToken

```
id: UUID (PK)
user_id: UUID (FK User, CASCADE DELETE)
token_hash: str (NOT NULL)
created_at: datetime
expires_at: datetime     ← 15 minut
used_at: datetime (nullable)  ← NULL = nieużyty
```

### UserConsent (akceptacja regulaminu — decyzja #90)

```
id: UUID (PK)
user_id: UUID (FK User, CASCADE DELETE)
document_type: enum [tos, privacy_policy]
document_version: str (NOT NULL)           ← np. "1.0", "1.1"
accepted_at: datetime
ip_address: str
```

Aktualna wersja regulaminu w SystemConfig: `tos_current_version`, `privacy_current_version`.
Przy rejestracji: INSERT per document_type. Zmiana regulaminu → frontend banner → `POST /auth/accept-terms`.

### EmailChangeToken (decyzja #93)

```
id: UUID (PK)
user_id: UUID (FK User, CASCADE DELETE)
new_email: str (NOT NULL)
token_hash: str (NOT NULL)
created_at: datetime
expires_at: datetime     ← 24h
used_at: datetime (nullable)
```

### EmailVerificationToken (decyzja #96)

```
id: UUID (PK)
user_id: UUID (FK User, CASCADE DELETE)
token_hash: str (NOT NULL)
created_at: datetime
expires_at: datetime     ← 24h (spójne z EmailChangeToken)
used_at: datetime (nullable)
```

Resend (#89): DELETE stary (unused) przed INSERT nowego.
Konwencja wspólna z PasswordResetToken / EmailChangeToken.

### PhoneVerificationOTP (decyzja #97)

```
id: UUID (PK)
user_id: UUID (FK User, CASCADE DELETE)
phone_number: str (NOT NULL)     ← numer na który wysłano (ważne przy zmianie telefonu)
code_hash: str (NOT NULL)        ← hash, nie plaintext
created_at: datetime
expires_at: datetime             ← 10min
attempts: int (DEFAULT 0)        ← max 5, potem 422 OTP_MAX_ATTEMPTS
used_at: datetime (nullable)
```

Nowy OTP unieważnia stary (DELETE WHERE user_id AND used_at IS NULL).

### Notification

```
id: UUID (PK)
user_id: UUID (FK User)
type: enum [NEW_EXCHANGE, EXCHANGE_ACCEPTED, EXCHANGE_COMPLETED,
            NEW_MESSAGE, EXCHANGE_CANCELLED, NEW_REVIEW,
            HEARTS_RECEIVED, REQUEST_EXPIRED]
reason: str (nullable)              ← kontekst dla EXCHANGE_CANCELLED: "account_deleted", "user_cancel", "admin_resolve"
related_exchange_id: UUID (nullable)
related_message_id: UUID (nullable)
is_read: bool (DEFAULT false)
created_at: datetime
```

Tworzona automatycznie przy każdym zdarzeniu. Email wysyłany równolegle przy INSERT.
Endpointy: `GET /users/me/notifications`, `POST /users/me/notifications/{id}/read`, `POST /users/me/notifications/read-all` (namespace ujednolicony — decyzja #79).

### ContentFlag (zastępuje ExchangeFlag — ADR-SERCE-004 D2)

```
id: UUID (PK)
reporter_id: UUID (FK User, nullable)     ← nullable = anonimowe zgłoszenie z publicznego feedu
target_type: enum [user, request, offer, exchange, message]
target_id: UUID                           ← brak FK (polimorficzny); walidacja w serwisie
reason: enum [spam, scam, abuse, inappropriate, other]
description: str (nullable, max 1000)
status: enum [open, resolved, dismissed] (DEFAULT open)
resolved_by: UUID (FK User — admin, nullable)
resolved_at: datetime (nullable)
resolution_action: enum [dismiss, warn_user, hide_content, suspend_user, ban_user, grant_hearts_refund] (nullable)
resolution_reason: str (nullable, max 1000)
created_at: datetime
```

**Endpoint użytkownika:** `POST /exchanges/{id}/flag` tworzy ContentFlag z `target_type='exchange'`.
**Endpoint admina:** `GET /admin/flags`, `POST /admin/flags/{id}/resolve` (z wybraną `resolution_action`).

### AdminAuditLog (ADR-SERCE-004 D4)

```
id: UUID (PK)
admin_id: UUID (FK User, NOT NULL)
action: str (max 64)                      ← np. "flag.resolve", "user.suspend", "hearts.grant"
target_type: enum [user, request, offer, exchange, message, flag, system]
target_id: UUID (nullable)                ← NULL przy akcjach systemowych
payload: JSONB                            ← pełny request body + kontekst
reason: str (wymagane dla akcji sankcyjnych)
created_at: datetime
```

**Immutable** — brak UPDATE/DELETE. Każda akcja admin zapisana w tej samej transakcji co akcja właściwa.
Brak wpisu = brak akcji (enforced w serwisie).

### Message

```
id: UUID (PK)
exchange_id: UUID (FK Exchange)
sender_id: UUID (FK User)
content: str
is_hidden: bool (DEFAULT false)           ← admin hide_content (ADR-004 D3)
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

1. User POST /auth/register → walidacja email/username (+ CAPTCHA, IP rate limit, temp-mail denylist) + `tos_accepted`, `privacy_policy_accepted` wymagane (422 TERMS_NOT_ACCEPTED)
2. hash password → INSERT User (heart_balance=0, email_verified=false, status='active', role='user') + INSERT UserConsent (tos + privacy_policy z aktualnymi wersjami z SystemConfig)
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

### Usunięcie konta (soft delete — ADR-SERCE-003)

**Wymagana dyspozycja salda** (gdy heart_balance > 0):
```
DELETE /users/me
Body: {
  "balance_disposition": "void" | "transfer",
  "transfer_to_user_id": "<uuid>"  // wymagane gdy disposition=transfer
}
```

Gdy `heart_balance = 0` — body opcjonalne.

**Transakcja all-or-nothing** w `UserService.soft_delete()`:

1. Walidacja dyspozycji (422 gdy balance > 0 i brak dispositon; walidacja recipient przy transfer)
2. Auto-CANCEL Exchange WHERE (requester=user OR helper=user) AND status IN (PENDING, ACCEPTED, IN_PROGRESS)
   - Request drugiej strony wraca do OPEN jeśli user był helperem (spójnie z #34)
   - Notification EXCHANGE_CANCELLED do drugiej strony z reason='account_deleted'
3. Auto-CANCEL Request WHERE user_id=user AND status=OPEN
4. Auto-INACTIVE Offer WHERE user_id=user AND status IN (ACTIVE, PAUSED)
5. Dyspozycja heart_balance:
   - **void:** INSERT HeartLedger(type=ACCOUNT_DELETED, to_user_id=NULL, amount=balance); balance=0
   - **transfer:** walidacja cap recipienta (422 CAP_EXCEEDED z max_receivable); UPDATE recipient balance; INSERT HeartLedger(type=GIFT, to_user_id=recipient, note='balance transfer przed usunięciem konta'); balance=0; Notification HEARTS_RECEIVED do recipient
6. Anonimizacja: email/username zastąpione hashem (`deleted_a3f2b1@serce.pl`), phone_number=NULL
7. SET deleted_at=now(), anonymized_at=now(), status='deleted'
8. Revoke wszystkich refresh_tokens (UPDATE revoked_at)

Poza transakcją (best effort): wysyłka emaili z powiadomieniami, email "konto usunięte" na stary adres.

**Prezentacja usuniętego usera w API** (GET /users/{id}, Exchange participants, Messages sender, Reviews author):
```json
{
  "id": "<UUID>",
  "username": null,
  "bio": null,
  "location": null,
  "is_deleted": true
}
```
HTTP 200 (nie 404). Frontend renderuje "Użytkownik usunięty" jako UI concern (i18n-ready).

---

## Reguły biznesowe (enforced w services/)

1. `heart_balance >= 0` — DB CHECK constraint. Cap (`<= heart_balance_cap`) walidowany aplikacyjnie w HeartService (cross-table CHECK niemożliwy w PostgreSQL)
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
19. Feed publiczny (bez JWT): GET /requests, GET /requests/{id}, GET /offers, GET /offers/{id}, GET /users/{id}, GET /categories, GET /locations; wszystkie POST/PATCH/DELETE i GET /exchanges/*, /messages/*, /notifications wymagają JWT
20. location_id nullable: brak lokalizacji → tylko NATIONAL scope w feedzie
21. Self-exchange zablokowany: walidacja w service przy CREATE Exchange (422 gdy requester = helper)
22. hearts_agreed w Offer-first musi = Offer.hearts_asked: walidacja w service przy CREATE (422 przy niezgodności)
23. Cancel Exchange: dostępny dla obu stron w każdym momencie przed COMPLETED; Exchange → CANCELLED, Request → OPEN (jeśli był IN_PROGRESS); brak konsekwencji finansowych
24. HeartLedger: pomiń INSERT gdy amount = 0
25. Zmiana emaila: nowy email weryfikowany zanim zastąpi stary; powiadomienie na stary email; revoke wszystkich refresh_tokens
26. W Request-first Exchange: `hearts_agreed` przy CREATE musi = `Request.hearts_offered`. Walidacja w ExchangeService, 422 HEARTS_MISMATCH przy niezgodności. Symetrycznie z regułą #22 (Offer-first).
27. Review niemodyfikowalne po wystawieniu — brak PATCH /reviews/{id}
28. Zmiana email/username wymaga weryfikacji (analogicznie do password reset flow)
29. Admin unhide (Offer/Request) → status przywrócony do INACTIVE (Offer) / CANCELLED (Request). User reaktywuje sam. Auto-ACTIVE po interwencji admina niedopuszczalne — user musi kontrolować widoczność.

---

## Fazy implementacji (dla Developera)

### Faza 1 — Backend core (MVP)

- [ ] Setup: FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker
- [ ] Auth: register (+ CAPTCHA validation, IP rate limit, temp-mail check), login, refresh (token rotation), logout, logout-all
- [ ] Auth: verify-email (token link), verify-phone (SMS OTP), resend-verification-email (rate limit 3/email/24h)
- [ ] Auth: forgot-password + reset-password (PasswordResetToken)
- [ ] Auth: sessions endpoint (GET /auth/sessions, DELETE /auth/sessions/{id} z guardem CANNOT_REVOKE_CURRENT_SESSION)
- [ ] Auth: accept-terms (POST /auth/accept-terms) + UserConsent model (document_type, document_version, ip_address)
- [ ] Auth: rejestracja wymaga tos_accepted + privacy_policy_accepted; SystemConfig: tos_current_version, privacy_current_version
- [ ] Profil: PATCH /users/me (bio, location_id); PATCH /users/me/username + PATCH /users/me/email (z weryfikacją)
- [ ] Profil: POST /users/me/email/change (hasło + EmailChangeToken 24h + powiadomienie stary email), POST /auth/confirm-email-change
- [ ] Profil: POST /users/me/phone/change (hasło + OTP nowy numer), POST /users/me/phone/verify (brak ponownego INITIAL_GRANT)
- [ ] Soft delete: DELETE /users/me z dyspozycją salda (void/transfer), transakcyjna kaskada 8 kroków (ADR-SERCE-003 D6), test atomowości
- [ ] Locations: preload województwa + wybrane miasta
- [ ] Categories: preload bazowe kategorie
- [ ] Hearts: transfer, gift, balance endpoint
- [ ] Requests: CRUD + listing z filtrami (location_scope, category, status, `?q=` ILIKE search, `?sort=`+`?order=`); PATCH /requests/{id} (title/description/expires_at, tylko OPEN, hearts_offered zablokowany gdy PENDING Exchange)
- [ ] Offers: CRUD + listing z filtrami (analogicznie: location_scope, category, status, `?q=`, `?sort=`+`?order=`); PATCH /offers/{id} (title/description/hearts_asked); PATCH /offers/{id}/status (ACTIVE/PAUSED/INACTIVE)
- [ ] Exchanges: create (PENDING, dwukierunkowy), accept (tylko non-initiator), complete, cancel + messages
- [ ] Exchanges: auto-cancel pozostałych PENDING przy akceptacji Request-first Exchange
- [ ] Reviews: create po COMPLETED (UNIQUE exchange_id + reviewer_id)
- [ ] Flag endpoints: POST /exchanges/{id}/flag, POST /requests/{id}/flag, POST /offers/{id}/flag, POST /users/{id}/flag → INSERT ContentFlag z odpowiednim target_type. Message flag przez Exchange (opis w reason).
- [ ] Admin: GET /admin/flags (paginacja + filtry status, target_type), GET /admin/flags/{id}, POST /admin/flags/{id}/resolve (resolution_action + params)
- [ ] Admin: POST /admin/users/{id}/suspend (+ revoke refresh tokens, audit log), POST /admin/users/{id}/unsuspend
- [ ] Admin: POST /admin/hearts/grant (+ HeartLedger type=ADMIN_REFUND, audit log)
- [ ] Admin: GET /admin/audit (paginacja + filtry actor_id, action, target_type, from, to)
- [ ] Admin: dependency require_admin() + seed migration (INITIAL_ADMIN_EMAIL z .env)
- [ ] Suspended account: login → 401 ACCOUNT_SUSPENDED; feed query WHERE owner.status='active'; Exchanges trwają, Messages/akcje zablokowane
- [ ] Notifications: INSERT przy każdym zdarzeniu + email wysyłany równolegle; GET /users/me/notifications, POST /users/me/notifications/{id}/read, POST /users/me/notifications/read-all
- [ ] User resources API (ADR-SERCE-005): GET /users/me, /users/me/summary, /users/me/requests, /users/me/offers, /users/me/exchanges, /users/me/reviews (direction required), /users/me/ledger
- [ ] Exchange transparency: GET /requests/{id}/exchanges, GET /offers/{id}/exchanges (owner + uczestnicy widzą, zredukowany widok dla rywali)
- [ ] Messages: GET /exchanges/{id}/messages (sort ASC, paginacja, autoryzacja participants)
- [ ] Background job: APScheduler — co godzinę CANCELLED wygasłe Requests (expires_at < now, status=OPEN)
- [ ] Paginacja: wszystkie listing endpoints (requests, offers, exchanges, notifications) — ?page + ?limit
- [ ] Testy: struktura `tests/{unit/{core,services},integration/{api,db}}` + `conftest.py` + `factories.py`
- [ ] Testy: pokrycie MUST-COVER (hearts transfer + concurrency, Exchange state machine, Exchange creation, Auth, rate limiting, public vs private, Review unique, APScheduler expire)

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
| 11 | Soft delete? | Tak. deleted_at + anonymized_at. Dane osobowe usuwane, historia Exchange/Ledger/Review zachowana. GDPR-ready. Szczegóły kaskady (balance, requests, offers, exchanges, prezentacja) → ADR-SERCE-003 / decyzje #63–#69. |
| 12 | Dispute mechanism? | Brak w v1. Platforma działa na dobrej wierze. Flag endpoint → admin ręcznie. |
| 13 | COUNTY w location_scope? | Usunięte. Zakres: CITY / VOIVODESHIP / NATIONAL. |
| 14 | Komunikacja przed Exchange? | PENDING Exchange = rozmowa wstępna. Wiele PENDING per Request dozwolone. Jeden ACCEPTED — partial unique index. |
| 15 | Review unique constraint? | UNIQUE(exchange_id, reviewer_id) — jedna ocena per strona per Exchange (max 2 total). |
| 16 | Offer → Exchange flow? | Dwukierunkowy. Request-first: helper inicjuje. Offer-first: requester inicjuje. `initiated_by` determinuje kto akceptuje. |
| 17 | Limit ACCEPTED per Offer? | Brak. Offer = stała wizytówka. Helper może obsługiwać wielu jednocześnie. |
| 18 | ~~Admin role w modelu?~~ | ~~`is_admin: bool`~~ → zastąpione `User.role: ENUM('user','admin')`. **Superseded by #82 (ADR-SERCE-004 D7).** |
| 19 | Exchange bez Request i Offer? | Niedozwolone. CHECK (request_id IS NOT NULL OR offer_id IS NOT NULL). |
| 20 | Password reset? | Tabela PasswordResetToken (DB-backed, expires 15min). Po użyciu: revoke wszystkich refresh_tokens. |
| 21 | ~~Flag mechanism?~~ | ~~ExchangeFlag~~ → zastąpione polimorficznym ContentFlag (target_type + target_id). **Superseded by #80 (ADR-SERCE-004 D2).** |
| 22 | Powiadomienia? | Email + in-app (tabela Notification). Tworzone przy każdym zdarzeniu, email wysyłany równolegle. Faza 1. Endpointy: `GET /users/me/notifications`, `POST /users/me/notifications/{id}/read`, `POST /users/me/notifications/read-all` (namespace ujednolicony w ADR-SERCE-005 D7). |
| 23 | Paginacja feedu? | Wymagana od Fazy 1. Wszystkie listing endpoints: ?page + ?limit. |
| 24 | Negocjacja hearts_agreed? | Brak. Stały przy CREATE = Request.hearts_offered. |
| 25 | Wygasanie Request? | APScheduler co godzinę: UPDATE status=CANCELLED WHERE expires_at < now AND status=OPEN. |
| 26 | Edycja Request po opublikowaniu? | `PATCH /requests/{id}` — tylko pola `title / description / expires_at`, tylko gdy `status = OPEN`. Zmiana `hearts_offered` zablokowana gdy istnieje ≥1 PENDING Exchange (422). |
| 27 | Edycja Offer po opublikowaniu? | `PATCH /offers/{id}` — pola `title / description / hearts_asked` edytowalne w każdym stanie. Zmiana statusu przez osobny endpoint `PATCH /offers/{id}/status` (ACTIVE ↔ PAUSED ↔ INACTIVE). |
| 28 | Edycja profilu użytkownika? | `PATCH /users/me` — pola `bio`, `location_id`. Zmiana `username` i `email` przez osobne endpointy z weryfikacją (analogicznie do password reset). |
| 29 | Edycja Review po wystawieniu? | Brak. Review jest niemodyfikowalne po wystawieniu. Integralność reputacji ważniejsza niż wygoda edycji. |
| 30 | Publiczny dostęp do feedu (bez konta)? | Tak. GET /requests, GET /offers, GET /users/{id} (profil publiczny) — dostępne bez JWT. Tworzenie, odpowiadanie, wiadomości, transfer serc — wymagają konta. |
| 31 | location_id wymagane przy rejestracji? | Nullable. Brak lokalizacji → feed pokazuje tylko NATIONAL scope. Soft requirement: UX motywuje do podania, nie wymuszamy technicznie. |
| 32 | Self-exchange (Exchange na własny Request/Offer)? | Zablokowany. Walidacja w service przy CREATE + opcjonalnie CHECK w DB. |
| 33 | hearts_agreed w Offer-first — czy musi = Offer.hearts_asked? | Tak. hearts_agreed przy CREATE Exchange na Offer musi równać się Offer.hearts_asked. Brak negocjacji (spójnie z #24). Walidacja w service, 422 przy niezgodności. |
| 34 | Request status przy CANCEL Exchange po ACCEPTED? | Request wraca do OPEN. Cancel możliwy przez obie strony w każdym momencie przed COMPLETED. Brak konsekwencji finansowych (serca nie zamrożone). Exchange → CANCELLED, Request → OPEN (jeśli był IN_PROGRESS). |
| 35 | Kto i kiedy może anulować Exchange? | Obie strony, w każdym momencie przed COMPLETED. Duch platformy: pomoc, nie umowa. Brak timeoutów w v1 — jeśli ktoś znika, druga strona anuluje sama lub flaguje admina. |
| 36 | Granica public/private endpointów? | Publiczne (bez JWT): GET /requests, GET /requests/{id}, GET /offers, GET /offers/{id}, GET /users/{id}, GET /categories, GET /locations. Prywatne (wymagają JWT): wszystkie POST/PATCH/DELETE, GET /exchanges/*, GET /messages/*, GET /notifications, GET /auth/sessions. |
| 37 | Schemat publicznego profilu użytkownika? | GET /users/{id} zwraca: username, location (nazwa), bio, lista aktywnych Offers, lista aktywnych Requests, lista Reviews (komentarze jako reviewed). Ukryte: email, phone_number, heart_balance, deleted_at. |
| 38 | Flow zmiany emaila — bezpieczeństwo? | Nowy email wymaga weryfikacji zanim zastąpi stary (stary aktywny do potwierdzenia). Stary email dostaje powiadomienie o zmianie (anti-hijacking). Zmiana emaila revokuje wszystkie refresh_tokens (wymuś re-login). |
| 39 | HeartLedger przy hearts_agreed = 0? | Pomiń INSERT HeartLedger gdy amount = 0. Brak transakcji finansowej — wpis bez wartości. Exchange COMPLETED jest wystarczającym śladem w historii. |
| 40 | Brakujące typy Notification? | Dodać do enum: HEARTS_RECEIVED (przy Gift), REQUEST_EXPIRED (APScheduler przy wygaśnięciu). EXCHANGE_FLAGGED dla admina — Faza 4. |
| 41 | URL prefix i wersjonowanie API? | `/api/v1/` prefix na wszystkich endpointach. Wersja w URL (nie nagłówku). |
| 42 | Format błędów API? | `{"error": "ERROR_CODE", "message": "...", "detail": {...}}`. Kody: SELF_EXCHANGE, BALANCE_INSUFFICIENT, CAP_EXCEEDED, NOT_FOUND, UNAUTHORIZED, FORBIDDEN, VALIDATION_ERROR. |
| 43 | HTTP status codes — konwencja? | 201 CREATE, 200 UPDATE/akcje, 204 DELETE, 422 błąd biznesowy, 400 błąd formatu, 401 brak JWT, 403 brak uprawnień, 404 nie znaleziono. |
| 44 | Pagination — format? | `?page=1&limit=20`. Response: `{"items": [...], "total": N, "page": N, "limit": N, "pages": N}`. Cursor-based — Faza 4. |
| 45 | Format dat? | ISO 8601 UTC wszędzie (`2026-04-10T13:47:47Z`). Konwersja na lokalny czas — obowiązek frontendu/mobilki. |
| 46 | Limity długości pól? | username 3–30 znaków `[a-z0-9_.-]`; password 8–128 (min 1 cyfra lub znak specjalny); title 5–100; description 10–2000; comment/message 1–1000/2000; bio 0–500. |
| 47 | SMS OTP provider? | SMSAPI.pl (polska platforma, GDPR, PLN). |
| 48 | Email provider? | Resend.com (nowoczesne API, darmowy tier 3k/mies.). |
| 49 | CAPTCHA provider? | hCaptcha (privacy-first, GDPR-friendly, darmowy tier). |
| 50 | Rate limiting — pełny zakres? | Rejestracja: 3/IP/24h (istniejące). Login: 10 prób/IP/15min. SMS OTP: 3 wysyłki/numer/24h. Wiadomości: 50/user/h. Gift serc: 10 transferów/user/24h. Biblioteka: SlowAPI (FastAPI middleware). |
| 51 | CORS? | Whitelist origins z `.env` (`CORS_ORIGINS`). Wildcard `*` tylko w trybie dev. |
| 52 | Polityka haseł? | Min 8 znaków, min 1 cyfra LUB znak specjalny. Brak wymogu wielkich liter. |
| 53 | Health check endpoint? | `GET /health` — publiczny, bez JWT. Response: `{"status": "ok", "db": "ok"}`. Wymagany dla Docker healthcheck. |
| 54 | Struktura `.env`? | Klucze zdefiniowane w `.env.example`: DATABASE_URL, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, SMSAPI_TOKEN, RESEND_API_KEY, HCAPTCHA_SECRET, CORS_ORIGINS, INITIAL_HEART_GRANT, HEART_BALANCE_CAP, REQUEST_DEFAULT_EXPIRY_DAYS, INITIAL_ADMIN_EMAIL. |
| 55 | Logging? | Structured JSON (biblioteka `structlog`). Per-request: method, path, status_code, duration_ms, user_id. Poziomy: INFO (2xx/3xx), WARNING (4xx), ERROR (5xx). |
| 56 | Podział testów unit vs integration? | 30% unit (core + services z mock repo) / 70% integration (API + test DB). Unit testuje pure logic (entities, walidacje, transfer math, state transitions). Integration testuje kontrakty request→service→DB→response przez FastAPI TestClient / `httpx.AsyncClient`. |
| 57 | Testowa baza danych? | Osobna baza `serce_test` w tym samym kontenerze Postgres co dev. `conftest.py` aplikuje Alembic migracje raz na sesję. Fixture `db_session`: transakcja per test z rollbackiem. Guard: `RuntimeError` gdy `DATABASE_URL` nie kończy się na `_test` (anty-pomyłka). |
| 58 | Kryterium akceptacji testów? | Lista MUST-COVER ścieżek, nie procent coverage. Metryka % motywuje do testowania niewłaściwych rzeczy (getters/setters) zamiast krytycznej logiki. MUST-COVER: (1) hearts transfer — happy + BALANCE_INSUFFICIENT + CAP_EXCEEDED + amount=0 skip ledger + concurrency; (2) Exchange state machine — wszystkie dozwolone przejścia + każde niedozwolone → 422 INVALID_STATUS_TRANSITION; (3) Exchange creation — Request-first, Offer-first, self-exchange block, hearts_agreed mismatch, auto-cancel PENDING przy ACCEPTED; (4) Auth — register + CAPTCHA, login, refresh rotation (stary token po użyciu → 401), logout-all, password reset revoke, email change revoke; (5) rate limiting — register/login/SMS OTP/messages/gift; (6) public vs private endpoints — GET /requests bez JWT = 200, POST = 401; (7) Review UNIQUE(exchange_id, reviewer_id); (8) APScheduler — expired Request → CANCELLED. |
| 59 | Test concurrency dla hearts transfer? | Dedykowany `tests/integration/test_hearts_concurrency.py` z `asyncio.gather()` uruchamiającym N równoległych `complete_exchange()`. Weryfikuje że `SELECT ... FOR UPDATE` w `HeartService.transfer()` zapobiega race condition — suma balance zachowana po wszystkich operacjach. Jedyny test concurrency w suite. |
| 60 | Struktura katalogów testów? | `backend/tests/{unit/{core,services}, integration/{api,db}}`. `conftest.py` (app, db_session, client, auth fixtures) + `factories.py` (`create_user()`, `create_request()`, `create_offer()`) w `tests/` root. Helpery zamiast `factory_boy` — skala nie uzasadnia biblioteki. |
| 61 | Konwencja nazewnictwa testów? | `test_<action>__<condition>__<expected>`. Przykłady: `test_create_exchange__self_exchange__returns_422`, `test_complete_exchange__balance_insufficient__returns_422_and_no_ledger`, `test_refresh_token__already_used__returns_401`, `test_get_requests__no_jwt__returns_200_public`. Grep-friendly, czytelne bez ciała testu, naturalne grupowanie po akcji. |
| 62 | Narzędzia testowe? | `pytest` + `pytest-asyncio` (async support), `httpx.AsyncClient` (async test client), `pytest-cov` zainstalowany jako narzędzie diagnostyczne (HTML raport) — **bez egzekwowania progu**. Brak `factory_boy`, brak `pytest-postgresql` (osobna DB via docker-compose wystarczy). `pytest-xdist` opcjonalnie, gdy testy zaczną być wolne. |
| 63 | Heart balance przy soft delete? | Wymagana dyspozycja gdy balance > 0: `void` (przepadają + HeartLedger type=ACCOUNT_DELETED, to_user_id=NULL) lub `transfer` (gift do wskazanego usera, walidacja cap, HeartLedger type=GIFT). 422 gdy balance>0 i brak dyspozycji. User zachowuje kontrolę do końca. Szczegóły: **ADR-SERCE-003 D1**. |
| 64 | OPEN Requests i ACTIVE/PAUSED Offers przy soft delete? | Auto-CANCELLED (Requests) i auto-INACTIVE (Offers) w tej samej transakcji co soft delete. Kaskadowo triggerują anulowanie PENDING Exchange. **ADR-SERCE-003 D2/D3**. |
| 65 | Aktywne Exchange (PENDING/ACCEPTED/IN_PROGRESS) przy soft delete? | Auto-CANCELLED, brak konsekwencji finansowych (spójnie z #35). Notification EXCHANGE_CANCELLED do drugiej strony z `reason='account_deleted'`. Request drugiej strony wraca do OPEN jeśli user był helperem (Request-first). **ADR-SERCE-003 D4**. |
| 66 | Prezentacja usuniętego usera w API? | `{id, username:null, bio:null, location:null, is_deleted:true}` wszędzie (public profile, Exchange, Messages, Reviews). HTTP 200 (nie 404). Frontend renderuje tekst ("Użytkownik usunięty") — i18n-ready. **ADR-SERCE-003 D5**. |
| 67 | Transakcyjność soft delete? | All-or-nothing — cała kaskada (8 kroków) w jednej DB transaction. Częściowy fail = pęknięta spójność domeny, niedopuszczalny. Dedykowany integration test na atomowość. **ADR-SERCE-003 D6**. |
| 68 | Grace period / account recovery? | Brak w v1. Soft delete = natychmiastowy, nieodwracalny self-service. Admin może cofnąć ręcznie w DB w skrajnych przypadkach. Self-service undelete → NICE backlog, Faza 2+. **ADR-SERCE-003 D7**. |
| 69 | Hard delete (GDPR right to be forgotten)? | Odroczony do Fazy 4. v1: tylko soft delete = pseudoanonymization (zgodna z GDPR art. 17 — dane osobowe usunięte, historia finansowa/kontraktowa zachowana jako legalny interes). Hard delete = osobna decyzja architektoniczna. **ADR-SERCE-003 D8**. |
| 70 | `GET /users/me` — własny profil? | Rozszerzony response vs publiczny: zawiera email, phone_number, email_verified, phone_verified, heart_balance, role, status, created_at (vs publiczny #37 bez tych pól). Bez list Offers/Requests/Reviews — osobne endpointy. **ADR-SERCE-005 D1**. |
| 71 | `GET /users/me/{requests,offers}`? | Paginacja + filtr `?status`, sort `created_at DESC`. Item zawiera `pending_exchanges_count` na zasób (szybki podgląd odzewu). **ADR-SERCE-005 D2, D3**. |
| 72 | `GET /users/me/exchanges`? | Paginacja + filtry `?status`, `?role=requester\|helper`, `?initiated_by=me\|other`. Sort `created_at DESC`. Item: Exchange + skrócony Request/Offer + druga strona (zredukowany User). **ADR-SERCE-005 D4**. |
| 73 | `GET /users/me/reviews`? | Wymagany parametr `?direction=given\|received` (brak defaulta — frontend explicit). Paginacja. **ADR-SERCE-005 D5**. |
| 74 | `GET /users/me/ledger`? | Historia HeartLedger z perspektywy usera: `direction` (in/out) wyliczane backendem, `counterparty` = null dla SYSTEM/ACCOUNT_DELETED lub placeholder dla usuniętego usera. Parametry `?type`, `?direction`. Paginacja. **ADR-SERCE-005 D6**. |
| 75 | `GET /users/me/summary` — dashboard w 1 requeście? | Liczniki: `heart_balance`, `unread_notifications_count`, `pending_exchanges_count`, `pending_reviews_count`, `active_requests_count`, `active_offers_count`, `email_verified`, `phone_verified`. Admin dodatkowo: `unresolved_flags_count` (warunkowe, obecne tylko gdy `role='admin'`). **ADR-SERCE-005 D8**. |
| 76 | `GET /requests/{id}/exchanges`, `GET /offers/{id}/exchanges` — transparentność? | Tak: owner zasobu widzi wszystko, helper z aktywnym Exchange widzi rywali (zredukowany widok: helper, hearts_agreed, status, created_at). Transparentność > prywatność konkurencyjnych helperów — anti-ghosting, social proof, fair-play. 403 dla nie-uczestników, 401 dla anonim. **ADR-SERCE-005 D9**. |
| 77 | `GET /exchanges/{id}/messages`? | Paginacja, sort `created_at ASC` (chat UX). Autoryzacja: tylko `requester_id` i `helper_id` Exchange. **ADR-SERCE-005 D10**. |
| 78 | Edycja/usuwanie wiadomości? | Brak. Message niemodyfikowalne po wysłaniu (brak PATCH/DELETE). Spójnie z #29 (Review). Integralność kontekstu Exchange, prostota modelu. Obraźliwe wiadomości → ContentFlag (ADR-SERCE-004) → admin ręcznie. **ADR-SERCE-005 D11**. |
| 79 | Namespace notifications? | Ujednolicony: `/users/me/notifications/*` (usunięto `GET /notifications` z planu). Wszystkie zasoby zalogowanego usera pod `/users/me/*`. **ADR-SERCE-005 D7**. |
| 80 | ContentFlag zamiast ExchangeFlag? | Tak. Polimorficzny ContentFlag (`target_type` + `target_id`) zastępuje wąski ExchangeFlag. Pokrywa User, Request, Offer, Exchange, Message bez nowych tabel. **ADR-SERCE-004 D2**. |
| 81 | `User.status` zamiast `is_active`? | `status: ENUM(active, suspended, deleted)` zamiast `is_active: BOOL`. Eliminuje nielegalne kombinacje flag. `deleted_at`/`anonymized_at` pozostają (ADR-003). Nowe pola: `suspended_at`, `suspended_until`, `suspension_reason`. **ADR-SERCE-004 D5**. |
| 82 | `User.role` zamiast `is_admin`? | `role: ENUM(user, admin) DEFAULT 'user'`. Dependency `require_admin()` na wszystkich `/admin/*`. Pierwszy admin = seed migration (`INITIAL_ADMIN_EMAIL` z `.env`). Brak endpointu promocji — świadoma decyzja (SQL only). **ADR-SERCE-004 D7**. |
| 83 | Admin endpoints w Fazie 1? | Tak — pełny zestaw: flags (list/detail/resolve), suspend/unsuspend, hearts grant, audit log. Prefiks `/api/v1/admin/`. Ograniczenie zakresu zostawiłoby moderację ślepą lub bezzębną. **ADR-SERCE-004 D1**. |
| 84 | AdminAuditLog — transakcyjność? | Immutable log. Każda akcja admin (flag.resolve, user.suspend, hearts.grant) zapisana w tej samej transakcji co akcja właściwa. Brak wpisu = brak akcji. `GET /admin/audit` z paginacją i filtrami. **ADR-SERCE-004 D4**. |
| 85 | Akcje moderacyjne — skończony enum? | `dismiss`, `warn_user`, `hide_content` (Request/Offer → HIDDEN, Message → is_hidden), `suspend_user`, `ban_user` (suspend z until=NULL), `grant_hearts_refund` (HeartLedger type=ADMIN_REFUND). **ADR-SERCE-004 D3**. |
| 86 | Zachowanie zawieszonego konta? | Revoke refresh tokens, Requests/Offers ukryte z feedu (query filter `owner.status='active'` — nie anulowane), Exchanges trwają (druga strona może dokończyć), saldo zamrożone, login → 401 ACCOUNT_SUSPENDED z reason. Unsuspend odwraca stan. **ADR-SERCE-004 D6**. |
| 87 | Search na feedzie? | `?q=` parametr na `GET /requests` i `GET /offers`. ILIKE na `title \|\| ' ' \|\| description` na start. PostgreSQL FTS (tsvector) jako upgrade gdy baza > ~10k rekordów. Zewnętrzny search (Meilisearch) → Faza 4. |
| 88 | Sortowanie feedu? | `?sort=created_at\|hearts_offered\|hearts_asked` + `?order=asc\|desc` (default: `created_at DESC`). Whitelist dozwolonych kolumn (SQL injection prevention). Dotyczy `GET /requests` i `GET /offers`. |
| 89 | Resend email verification? | `POST /auth/resend-verification-email {email}`. Email w body (nie wymaga JWT — user może nie być zalogowany). Rate limit: 3/email/24h. Stary token unieważniony przy nowym wysłaniu. Guard: 422 ALREADY_VERIFIED gdy `email_verified=true`. |
| 90 | Akceptacja regulaminu (ToS)? | Pełny model `UserConsent` (user_id, document_type, document_version, accepted_at, ip_address). Przy rejestracji: `tos_accepted` + `privacy_policy_accepted` wymagane. Aktualna wersja w SystemConfig (`tos_current_version`, `privacy_current_version`). Zmiana regulaminu → banner → `POST /auth/accept-terms`. Brak akceptacji = brak rejestracji. |
| 91 | Logout-all wymaga hasła? | Nie. Logout-all to akcja obronna (nie destrukcyjna) — user w panice nie powinien być spowalniany. Access token krótkotrwały (15 min), ryzyko niskie. |
| 92 | Unieważnianie pojedynczej sesji? | `DELETE /auth/sessions/{id}`. User może usunąć tylko swoje sesje. Guard: 422 CANNOT_REVOKE_CURRENT_SESSION (zapobiega przypadkowemu self-logout). |
| 93 | Flow zmiany emaila — endpointy? | `POST /users/me/email/change {new_email, password}` → walidacja hasła, unikalność, INSERT EmailChangeToken (expires 24h), link na nowy email, powiadomienie na stary. `POST /auth/confirm-email-change {token}` → UPDATE email, revoke refresh tokens. Rate limit: 3/user/24h. |
| 94 | Zmiana phone_number? | `POST /users/me/phone/change {new_phone_number, password}` → walidacja hasła, unikalność, SMS OTP na nowy numer. `POST /users/me/phone/verify {code}` → UPDATE phone, revoke refresh tokens. Brak nowego INITIAL_GRANT (HeartLedger UNIQUE constraint pilnuje). Stary numer zwolniony. Rate limit: 3/user/24h. |
| 95 | Account recovery po soft delete? | Brak. Soft delete natychmiastowy i nieodwracalny (self-service). Anonimizacja danych osobowych uniemożliwia pełne odzyskanie. Admin może cofnąć `status='deleted'` w DB ale dane osobowe już zanonimizowane — user musiałby uzupełnić od nowa. Świadoma decyzja, nie luka. Potwierdzenie #68 (ADR-003). |
| 96 | Model EmailVerificationToken? | DB-backed token (spójne z PasswordResetToken/EmailChangeToken). TTL 24h. Resend (#89) unieważnia stary (DELETE unused). Pola: id, user_id, token_hash, created_at, expires_at, used_at. |
| 97 | Model PhoneVerificationOTP? | DB-backed OTP. TTL 10min, max 5 attempts (422 OTP_MAX_ATTEMPTS). Pola: id, user_id, phone_number, code_hash, created_at, expires_at, attempts, used_at. Nowy OTP unieważnia stary. |
| 98 | heart_balance_cap — DB CHECK? | CHECK tylko `>= 0`. Cap walidowany aplikacyjnie w HeartService (cross-table CHECK niemożliwy w PostgreSQL). |
| 99 | Flag endpoints non-exchange? | Per-resource: POST /requests/{id}/flag, /offers/{id}/flag, /users/{id}/flag. Message flag przez Exchange (opis w reason). Brak generycznego POST /flags. |
| 100 | Offer/Request status po admin unhide? | Offer → INACTIVE, Request → CANCELLED. User reaktywuje sam. Auto-ACTIVE po interwencji admina niedopuszczalne. Reguła biznesowa #29. |

---

## Konwencje API

### URL structure

```
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{action}
```

Przykłady:
```
GET    /api/v1/requests
POST   /api/v1/requests
PATCH  /api/v1/requests/{id}
GET    /api/v1/requests/{id}/exchanges         # owner + aktywni helperzy (transparentność)
GET    /api/v1/offers/{id}/exchanges           # analogicznie
POST   /api/v1/exchanges/{id}/accept
POST   /api/v1/exchanges/{id}/cancel
POST   /api/v1/exchanges/{id}/complete
GET    /api/v1/exchanges/{id}/messages
POST   /api/v1/exchanges/{id}/messages

# Flag endpoints (per-resource)
POST   /api/v1/exchanges/{id}/flag
POST   /api/v1/requests/{id}/flag
POST   /api/v1/offers/{id}/flag
POST   /api/v1/users/{id}/flag

# Auth uzupełnienia
POST   /api/v1/auth/resend-verification-email  # email w body, rate limit 3/email/24h
POST   /api/v1/auth/accept-terms               # document_type + document_version
POST   /api/v1/auth/confirm-email-change       # token z EmailChangeToken
DELETE /api/v1/auth/sessions/{id}              # selective session revoke

GET    /api/v1/users/me                        # własny profil (rozszerzony)
PATCH  /api/v1/users/me                        # edycja bio, location
POST   /api/v1/users/me/email/change           # new_email + password (re-auth)
POST   /api/v1/users/me/phone/change           # new_phone_number + password
POST   /api/v1/users/me/phone/verify           # OTP code
GET    /api/v1/users/me/summary                # dashboard w 1 requeście
GET    /api/v1/users/me/requests               # moje prośby
GET    /api/v1/users/me/offers                 # moje oferty
GET    /api/v1/users/me/exchanges              # moje wymiany
GET    /api/v1/users/me/reviews?direction=given|received
GET    /api/v1/users/me/ledger                 # historia serc
GET    /api/v1/users/me/notifications
POST   /api/v1/users/me/notifications/{id}/read
POST   /api/v1/users/me/notifications/read-all

GET    /health

# Admin (require_admin dependency — ADR-004)
GET    /api/v1/admin/flags                      # paginacja + filtry status, target_type
GET    /api/v1/admin/flags/{id}
POST   /api/v1/admin/flags/{id}/resolve         # resolution_action + params
POST   /api/v1/admin/users/{id}/suspend         # body: reason, until (nullable)
POST   /api/v1/admin/users/{id}/unsuspend
POST   /api/v1/admin/hearts/grant               # body: to_user_id, amount, reason
GET    /api/v1/admin/audit                      # paginacja + filtry actor_id, action, target_type, from, to
```

### Error response

```json
{
  "error": "BALANCE_INSUFFICIENT",
  "message": "Insufficient heart balance to complete transfer",
  "detail": {
    "required": 10,
    "available": 3
  }
}
```

Kody błędów (wyczerpująca lista):
- `VALIDATION_ERROR` — błąd formatu/walidacji pola
- `NOT_FOUND` — zasób nie istnieje
- `UNAUTHORIZED` — brak lub nieprawidłowy JWT
- `FORBIDDEN` — brak uprawnień do zasobu
- `SELF_EXCHANGE` — próba Exchange z samym sobą
- `BALANCE_INSUFFICIENT` — za mało serc
- `CAP_EXCEEDED` — odbiorca przekroczyłby heart_balance_cap
- `HEARTS_MISMATCH` — hearts_agreed ≠ Offer.hearts_asked (Offer-first)
- `EXCHANGE_NOT_CANCELLABLE` — Exchange już COMPLETED
- `INVALID_STATUS_TRANSITION` — niedozwolona zmiana statusu
- `ACCOUNT_SUSPENDED` — konto zawieszone przez admina (401 przy logowaniu, z `suspended_until` i `reason`)
- `FORBIDDEN_ADMIN_ONLY` — endpoint wymaga roli admin (403)
- `ALREADY_VERIFIED` — email/phone już zweryfikowane (422)
- `CANNOT_REVOKE_CURRENT_SESSION` — próba unieważnienia aktywnej sesji (422)
- `TERMS_NOT_ACCEPTED` — brak akceptacji regulaminu przy rejestracji (422)
- `INVALID_PASSWORD` — hasło nieprawidłowe przy re-auth (401)
- `OTP_MAX_ATTEMPTS` — przekroczono limit prób OTP (422)

### Pagination response

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

## ADR powiązane

- `ADR-SERCE-001-stack.md` — wybór stack (FastAPI, Next.js, React Native)
- `ADR-SERCE-002-hearts-ledger.md` — serca jako księga, nie obiekty
- `ADR-SERCE-003-account-lifecycle.md` — cykl życia konta (soft delete, kaskada, prezentacja)
- `ADR-SERCE-004-admin-moderation.md` — ContentFlag, AdminAuditLog, User.status/role refactor, suspend/unsuspend, akcje moderacyjne
- `ADR-SERCE-005-user-resources-api.md` — /users/me/* namespace, dashboard, transparentność Exchange per Request/Offer, niemodyfikowalne wiadomości
