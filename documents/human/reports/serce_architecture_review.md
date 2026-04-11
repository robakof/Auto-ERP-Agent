# Serce — wstępna weryfikacja architektury

Date: 2026-04-11
Reviewer: Developer
Source: `documents/human/plans/serce_architecture.md` (v13), ADR-001–005

---

## Status: architektura kompletna, gotowa do implementacji z zastrzeżeniami poniżej

95 decyzji zamkniętych, 5 ADR, pełny model domenowy, endpointy API, checklistka Fazy 1.
Jakość dokumentacji wysoka — model, przepływy i konwencje spójne w ~90% przypadków.

---

## BLOKERY (naprawić przed implementacją)

### B1. `is_admin` vs `User.role` enum — niespójność ADR-005 z ADR-004

**ADR-005 D1** (linia ~39): response `GET /users/me` zawiera `"is_admin": false`.
**ADR-004 D7 / decyzja #82**: User.role = ENUM('user','admin'). `is_admin` nie istnieje.

Decyzja #75 (`/users/me/summary`) poprawnie mówi o `role='admin'`.
ADR-005 D1 jest niezaktualizowany po refaktorze z ADR-004.

**Fix:** w ADR-005 D1 zamienić `"is_admin": false` na `"role": "user"`.

### B2. `is_active` w ADR-003 D1 — martwe pole

**ADR-003 D1** (linia ~45): walidacja transfer-recipient: `is_active = true`.
**ADR-004 D5 / decyzja #81**: `is_active` zastąpione `User.status ENUM(active, suspended, deleted)`.

**Fix:** w ADR-003 D1 zamienić `is_active = true` na `status = 'active'`.

### B3. Brak modelu `EmailVerificationToken`

Rejestracja (linia ~411): "Wyślij email weryfikacyjny → POST /auth/verify-email".
Istnieją: `PasswordResetToken`, `EmailChangeToken`. Brak: `EmailVerificationToken`.

Pytania do zamknięcia:
- DB-backed token (jak PasswordResetToken) czy podpisany JWT w linku?
- TTL? (PasswordResetToken ma 15min, EmailChangeToken ma 24h)
- Resend (decyzja #89) unieważnia stary token — wymaga DB-backed podejścia.

**Rekomendacja:** DB-backed token (spójne z resztą auth), TTL 24h, model analogiczny do PasswordResetToken.

### B4. Brak modelu `PhoneVerificationOTP`

SMS OTP wspomniane w rejestracji i zmianie telefonu, ale brak modelu:
- Gdzie trzymać OTP? DB (z TTL, max attempts) czy in-memory?
- TTL? (Standardowo 5-10 minut)
- Max attempts? (Standardowo 3-5)

**Rekomendacja:** DB-backed model `PhoneOTP(id, user_id, phone_number, code_hash, created_at, expires_at, attempts, used_at)`. TTL 10min, max 5 attempts.

---

## WAŻNE (do wyjaśnienia, nie blokują startu)

### W1. heart_balance_cap jako DB CHECK constraint — niemożliwe

Model User (linia ~88): `heart_balance: int (>= 0 AND <= heart_balance_cap)`.
`heart_balance_cap` jest w SystemConfig (tabela, nie stała) — DB CHECK constraint
nie może referencjonować innej tabeli.

**Opcje:**
- a) CHECK tylko `>= 0`, cap walidowany aplikacyjnie (prostsze, rekomendowane)
- b) Trigger function czytający SystemConfig (złożone, wolne)

### W2. Brak endpointu flag dla non-exchange targets

ContentFlag obsługuje `target_type IN (user, request, offer, exchange, message)`,
ale jedyny zdefiniowany endpoint to `POST /exchanges/{id}/flag`.

Jak user flaguje Request, Offer, User, Message? Opcje:
- a) Osobne endpointy per resource (`POST /requests/{id}/flag`, `POST /users/{id}/flag` itd.)
- b) Jeden generyczny `POST /flags` z body `{target_type, target_id, reason, description}`

**Rekomendacja:** opcja (a) — spójne z istniejącym `POST /exchanges/{id}/flag`, proste routing.

### W3. Request-first: hearts_agreed musi = hearts_offered — niejawne

Decyzja #33 jawnie mówi: "hearts_agreed w Offer-first musi = Offer.hearts_asked".
Analogiczna reguła dla Request-first (hearts_agreed = Request.hearts_offered) wynika
z decyzji #24 ("Stały przy CREATE = Request.hearts_offered"), ale nie jest jawnie
sformułowana jako walidacja w service.

**Rekomendacja:** dodać jawny zapis walidacji, analogicznie do decyzji #33.

### W4. Offer.status HIDDEN — ścieżka przejścia

Status Offer: `ACTIVE, PAUSED, INACTIVE, HIDDEN`.
User endpoint `PATCH /offers/{id}/status` obsługuje `ACTIVE ↔ PAUSED ↔ INACTIVE`.
HIDDEN ustawiany tylko przez admin (resolution_action=hide_content).

Pytanie: czy admin unsuspend/unhide przywraca Offer do ACTIVE? Czy user musi sam reaktywować?
Brak jawnej reguły w planie.

### W5. Numeracja reguł biznesowych — przeskoki

Reguły biznesowe (sekcja linia 514+): kolejność: 1–16, 19–25, 17–18.
Reguły 17 i 18 umieszczone po 25. Kosmetyczne, ale mylące.

---

## OBSERWACJE (informacyjne, bez akcji)

- O1. Category.slug brak — URL-friendly name niedostępne. Wystarczające na v1 (id w URL).
- O2. Notification.reason wartości ('account_deleted', 'user_cancel', 'admin_resolve') nie są formalnym enumem — rozważyć enum lub string validation.
- O3. Architektura nie definiuje indexów DB poza partial unique na Exchange. Indeksy na FK i filtry feedu (location, category, status) krytyczne dla performance — do uzupełnienia przy implementacji.
- O4. Rate limit `gift` (#50) exemption przy soft delete (ADR-003 D1) jawnie udokumentowany — dobrze.
- O5. Brak modelu Session — `RefreshToken` pełni rolę sesji. Endpoint `GET /auth/sessions` zwraca listę refresh tokenów z device_info. Spójne, choć nazwa może mylić.

---

## PODSUMOWANIE

| Kategoria | Ilość | Blokujące? |
|-----------|-------|------------|
| Blokery   | 4     | Tak — B1, B2 to erraty w ADR; B3, B4 to brakujące modele |
| Ważne     | 5     | Nie — do wyjaśnienia, nie blokują startu scaffoldu |
| Obserwacje| 5     | Nie |

**Rekomendacja:** Zamknij B1–B4 (decyzje architekta lub moje propozycje wyżej),
potem start implementacji Fazy 1 od scaffoldu (FastAPI + PostgreSQL + Docker + Alembic).
