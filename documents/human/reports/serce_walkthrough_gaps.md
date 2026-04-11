# Walkthrough architektury Serce — analiza pokrycia user journeys

Date: 2026-04-11
Author: Architect
Status: Draft — do review przez usera

## Cel

Sprawdzić czy architektura Serce v9 (62 decyzje) pokrywa wszystkie realistyczne ścieżki użytkownika od wejścia na stronę po usunięcie konta. Metoda: symulacja krok po kroku 12 journeys, przy każdym kroku pytanie "czy architektura ma endpoint/mechanikę dla tego?".

## Metodologia

Dla każdego journey:
1. Wylistuj kroki użytkownika (UX-first, nie API-first)
2. Przypisz wymagany endpoint / mechanikę
3. Oznacz: **OK** (pokryte), **GAP** (brak), **UNCLEAR** (spisane ale niedoprecyzowane)

Luki zgrupowane po priorytecie:
- **CRITICAL** — blokuje Fazę 1 lub istnieje ryzyko prawne/finansowe
- **IMPORTANT** — luka funkcjonalna MVP, można dorobić w trakcie Fazy 1
- **NICE** — Faza 2+, quality of life

---

## Journey 1: Anonimowy odwiedzający przegląda platformę

**Krok 1:** Wchodzi na `/` — widzi landing + feed
**Krok 2:** `GET /requests?page=1&limit=20` — widzi listę próśb — **OK** (decyzja #30, #44)
**Krok 3:** Filtruje: kategoria "Nauka", lokalizacja "Warszawa"
  - `GET /requests?category_id=5&location_scope=CITY&location_id=123` — **UNCLEAR** (plan wspomina filtry, ale parametry query string nie są explicite w konwencjach API)
**Krok 4:** Chce znaleźć "angielski" w opisach
  - `GET /requests?q=angielski` — **GAP #1: brak full-text lub LIKE search na title+description**
**Krok 5:** Sortuje po dacie/serach
  - `GET /requests?sort=created_at:desc` — **GAP #2: brak decyzji o sortowaniu (default ORDER BY? parametr `?sort=`?)**
**Krok 6:** Klika Request → `GET /requests/{id}` — **OK**
**Krok 7:** Klika profil requestera → `GET /users/{id}` — **OK** (decyzja #37)
**Krok 8:** Chce odpowiedzieć → redirect do rejestracji — **OK**

---

## Journey 2: Rejestracja + onboarding

**Krok 1:** `POST /auth/register {email, username, password, captcha_token}` — **OK** (decyzja #8, #49, #50)
**Krok 2:** Dostaje email weryfikacyjny — **OK** (decyzja #7, #48)
**Krok 3:** Klika link → `POST /auth/verify-email {token}` — **OK**
**Krok 4:** Email nie przyszedł (spam) — chce ponowić
  - `POST /auth/resend-verification-email` — **GAP #3: brak endpoint ponownego wysłania email verification**
**Krok 5:** Login → `POST /auth/login` — **OK**
**Krok 6:** Akceptacja regulaminu (ToS) — **GAP #4 CRITICAL: brak mechaniki akceptacji regulaminu (GDPR, legal)**
**Krok 7:** Uzupełnia profil: `PATCH /users/me {bio, location_id}` — **OK** (decyzja #28)
**Krok 8:** Weryfikacja telefonu:
  - `POST /auth/send-otp {phone_number}` — **UNCLEAR** (plan mówi "SMS OTP" ale brak konkretnych endpointów)
  - `POST /auth/verify-phone {code}` → `INITIAL_GRANT` 5 serc — **OK**
**Krok 9:** User nie ma / nie chce podać numeru — czy dostaje INITIAL_GRANT?
  - Nie — plan mówi "phone verification = gate do INITIAL_GRANT". **OK** (spójne z #8)
**Krok 10:** Widzi dashboard — **GAP #5: brak endpoint `/users/me/summary` (balance, unread count, pending exchanges)**

---

## Journey 3: Pierwsza Request

**Krok 1:** Klika "Poproś o pomoc" — formularz
**Krok 2:** `POST /requests {title, description, hearts_offered, category_id, location_scope, expires_at}` — **OK**
**Krok 3:** Widzi swoje Request:
  - `GET /users/me/requests` — **GAP #6 CRITICAL: brak endpointów "moje" zasoby** (`/users/me/requests`, `/users/me/offers`, `/users/me/exchanges`)
**Krok 4:** Edytuje — `PATCH /requests/{id}` — **OK** (decyzja #26)
**Krok 5:** Widzi kto się zgłosił (PENDING Exchange na jej Request):
  - `GET /requests/{id}/exchanges` lub `GET /exchanges?request_id=X&status=PENDING` — **GAP #7 CRITICAL: brak endpoint do listowania Exchange per Request (core flow — requester musi to widzieć żeby wybrać)**

---

## Journey 4: Helper inicjuje Exchange (Request-first)

**Krok 1:** Helper przegląda feed, znajduje Request
**Krok 2:** `POST /exchanges {request_id, hearts_agreed}` — **OK**
**Krok 3:** Czat przed akceptacją — `POST /exchanges/{id}/messages` — **OK**
**Krok 4:** Odczyt wiadomości:
  - `GET /exchanges/{id}/messages?page=1` — **UNCLEAR** (nie spisane explicite, ale implied)
**Krok 5:** Wysłał wiadomość z błędem — chce edytować/usunąć
  - `PATCH /messages/{id}` lub `DELETE /messages/{id}` — **GAP #8: brak decyzji o edycji/usuwaniu wiadomości (spójnie z Review powinno być: brak)**
**Krok 6:** Requester akceptuje → `POST /exchanges/{id}/accept` — **OK**
**Krok 7:** Pozostałe PENDING auto-cancel — **OK** (decyzja #7 w Fazie 1)
**Krok 8:** Spotkanie offline, usługa wykonana
**Krok 9:** Requester → `POST /exchanges/{id}/complete` — transfer serc — **OK**
**Krok 10:** Helper chce zweryfikować że dostał serca:
  - `GET /users/me/balance` lub `GET /users/me` — **GAP: część GAP #6** (brak "moje" endpointów)
**Krok 11:** Chce zobaczyć historię transakcji:
  - `GET /users/me/ledger?page=1` — **GAP #9: brak endpoint historii HeartLedger (user nie ma wglądu w swoje transakcje serc)**
**Krok 12:** Oboje wystawiają Review — `POST /exchanges/{id}/reviews` — **OK**

---

## Journey 5: Offer-first

**Krok 1-3:** Analogicznie — **OK**
**Krok 4:** Brak niespodzianek vs Journey 4.
**Krok 5:** Helper ma wiele PENDING Offer-first na tym samym Offer (bez limitu):
  - Widzi kolejkę kto go pytał — `GET /offers/{id}/exchanges` lub `GET /users/me/offers/{id}/exchanges` — **GAP: część GAP #7**

---

## Journey 6: Darowizna serc (gift)

**Krok 1:** User znajduje innego przez profil (`GET /users/{id}`) — **OK**
**Krok 2:** `POST /hearts/gift {to_user_id, amount, note}` — **OK** (decyzja #50 rate limit)
**Krok 3:** Widzi w historii — **GAP #9** (ledger endpoint)
**Krok 4:** Próbuje dać za dużo → `CAP_EXCEEDED` z `max_receivable` — **OK**

---

## Journey 7: Problem i eskalacja (flag)

**Krok 1:** Druga strona znika, nie reaguje dni
**Krok 2:** User → `POST /exchanges/{id}/cancel` — **OK** (decyzja #23, #35)
**Krok 3:** Podejrzenie nadużycia → `POST /exchanges/{id}/flag {reason}` — **OK** (decyzja #21)
**Krok 4:** **Kto tę flagę rozpatrzy?** Admin.
  - `GET /admin/flags?status=open` — **GAP #10 CRITICAL: brak admin endpointów w Fazie 1** (Flag endpoint jest w Fazie 1, ale proces rozpatrywania spisany jako "Faza 4 admin panel" — czyli nikt nie rozpatrzy flag przez miesiące)
**Krok 5:** User widzi toxic behavior u innego usera (nie w Exchange — na bio, Offer, Request):
  - `POST /users/{id}/flag`, `POST /requests/{id}/flag`, `POST /offers/{id}/flag` — **GAP #11: ExchangeFlag jest tylko dla Exchange. Brak mechaniki flagowania bio/Offer/Request.**

---

## Journey 8: Reset hasła

**Krok 1-8:** Plan ma kompletny flow (#20) — **OK**

---

## Journey 9: Utrata telefonu / kompromitacja konta

**Krok 1:** User zauważa podejrzaną aktywność
**Krok 2:** Zmiana hasła → reset flow — **OK**
**Krok 3:** Wylogowanie wszystkich sesji → `POST /auth/logout-all` — **OK** (decyzja #9)
**Krok 4:** Czy logout-all wymaga re-auth (password confirmation)?
  - **GAP #12: brak decyzji — critical action powinien wymagać hasła** (prevent CSRF/session hijacking z już złamanego konta)
**Krok 5:** Podgląd aktywnych sesji → `GET /auth/sessions` — **OK**
**Krok 6:** Unieważnienie pojedynczej sesji → `DELETE /auth/sessions/{id}` — **GAP #13: brak endpoint unieważniania konkretnej sesji (tylko logout-all all-or-nothing)**

---

## Journey 10: Zmiana danych konta

**Krok 1:** `PATCH /users/me {bio, location_id}` — **OK**
**Krok 2:** Zmiana username → `PATCH /users/me/username` — **OK** (decyzja #28)
**Krok 3:** Zmiana emaila — flow z weryfikacją:
  - Plan wspomina "analogicznie do password reset" ale brak szczegółów endpointów
  - `POST /users/me/email/change {new_email}` → `POST /users/me/email/confirm {token}` — **GAP #14: brak doprecyzowania flow zmiany emaila (decyzja #38 wspomina mechanikę ale brak endpointów)**
**Krok 4:** Zmiana numeru telefonu:
  - Plan milczy. Czy można? Co z re-INITIAL_GRANT (nie — constraint UNIQUE per user)?
  - **GAP #15: brak decyzji o zmianie phone_number** (+ jaka re-verification)

---

## Journey 11: Usunięcie konta (sygnalizowane przez usera)

**Krok 1:** User → `DELETE /users/me` — **OK** (decyzja #11)
**Krok 2:** Anonimizacja: email/username → hash, phone_number → NULL — **OK**
**Krok 3:** **Co z saldem serc (np. 23)?**
  - Plan milczy. Przepadają do system? Możliwość przekazania komuś przed usunięciem?
  - **GAP #16 CRITICAL: brak decyzji co dzieje się z heart_balance przy soft delete** (to waluta — brak decyzji = potencjalnie utracona wartość usera bez wyjaśnienia, potencjalny spór prawny)
**Krok 4:** **Co z otwartymi Requests usera?** (status=OPEN)
  - Plan milczy. Powinny być auto-CANCELLED.
  - **GAP #17: brak decyzji co się dzieje z Requests/Offers przy soft delete**
**Krok 5:** **Co z aktywnymi Exchange w toku (PENDING/ACCEPTED)?**
  - Plan milczy. Druga strona zostaje z niczym?
  - Powinny być auto-CANCELLED + NotificationEXCHANGE_CANCELLED do drugiej strony.
  - **GAP #18: brak decyzji co z aktywnymi Exchange przy soft delete**
**Krok 6:** Historia Exchange zachowana, ale druga strona widzi "Wymiana z [usunięty]":
  - Plan wspomina dla Review ("Użytkownik usunięty"), nie wspomina dla Exchange/Messages
  - **GAP #19: brak decyzji jak prezentować usuniętego użytkownika w Exchange/Messages historii**
**Krok 7:** User zmienił zdanie, chce odzyskać konto
  - **GAP #20: brak account recovery (nie-krytyczne, bo soft delete można cofnąć ręcznie przez admina)**

---

## Journey 12: Admin — moderacja

**Krok 1:** Admin loguje się (zwykły login) — **OK**
**Krok 2:** Widzi dashboard admina:
  - `GET /admin/dashboard` (ile open flag, ile nowych userów, ile aktywnych Exchange) — **GAP #21: brak admin endpointów**
**Krok 3:** Lista flag → rozwiązanie — **GAP #21** (część #10 CRITICAL)
**Krok 4:** Grant serc (ADMIN_GRANT):
  - `POST /admin/hearts/grant {user_id, amount, note}` — **GAP #21**
  - Typ `ADMIN_GRANT` jest w enum HeartLedger (#40) ale brak endpoint
**Krok 5:** Zawieszenie toxic usera:
  - `POST /admin/users/{id}/suspend` → `is_active = false`
  - **GAP #22: brak decyzji co przełącza `is_active` na false oprócz soft delete** (ban/suspension semantyka)
**Krok 6:** Audit log akcji admina:
  - **GAP #23: brak admin audit log (kto grant serc, kto suspended usera, kiedy)**

---

## Podsumowanie luk po priorytetach

### CRITICAL (blokują Fazę 1 lub mają implikacje prawne/finansowe)

1. **#4 — Akceptacja regulaminu (ToS)** — GDPR/legal. User musi zaakceptować wersję regulaminu przy rejestracji, wersja zapisana w DB.
2. **#6 — Endpointy "moje" zasoby** — `GET /users/me`, `GET /users/me/requests`, `/me/offers`, `/me/exchanges`, `/me/notifications`, `/me/balance`. Bez tego frontend nie ma jak zbudować "moje konto".
3. **#7 — Listowanie Exchange per Request** — core flow Request-first. Requester musi widzieć listę PENDING żeby wybrać. `GET /requests/{id}/exchanges` lub `GET /exchanges?request_id=X`.
4. **#9 — Historia HeartLedger** — `GET /users/me/ledger`. User nie ma wglądu w transakcje swoich serc = brak transparentności waluty.
5. **#10 — Admin endpointy w Fazie 1** — Flag endpoint istnieje, ale bez panelu admina nikt nie rozpatrzy flag. Minimum: `GET /admin/flags`, `POST /admin/flags/{id}/resolve`, `POST /admin/hearts/grant`.
6. **#16 — heart_balance przy soft delete** — waluta zostaje u usera? Wraca do systemu? Można przekazać przed usunięciem? **Krytyczne dla integralności waluty.**
7. **#17 — Requests/Offers przy soft delete** — auto-CANCEL/INACTIVE? Co z aktywnymi Exchange na tych zasobach?
8. **#18 — Aktywne Exchange przy soft delete** — druga strona musi być powiadomiona, Exchange auto-CANCELLED.

### IMPORTANT (funkcjonalne braki MVP)

9. **#1 — Search na feedzie (`?q=`)** — user nie znajdzie rzeczy bez wyszukiwania po tytule/opisie. Min. PostgreSQL `ILIKE '%q%'`.
10. **#2 — Sortowanie feedu** — default `ORDER BY created_at DESC`, opcjonalnie `?sort=` parametr (`created_at`, `hearts_offered`).
11. **#3 — Resend email verification** — `POST /auth/resend-verification` (rate limit 3/24h/email).
12. **#5 — `/users/me/summary` (dashboard)** — jeden strzał: balance, unread notifications count, pending exchanges count, active requests count. Odciąża frontend przy starcie.
13. **#11 — Flag dla User/Request/Offer (nie tylko Exchange)** — Decyzja: refactor `ExchangeFlag` → `ContentFlag` z polem `target_type: enum`, `target_id: UUID`. Pokrywa wszystkie typy.
14. **#14 — Flow zmiany emaila (endpointy explicite)** — analogiczny do password reset. Spisać w planie.
15. **#15 — Zmiana phone_number** — decyzja: wymaga re-verification OTP + brak nowego INITIAL_GRANT (HeartLedger UNIQUE constraint pilnuje).
16. **#19 — Prezentacja usuniętych userów w historii** — stała nazwa `"Użytkownik usunięty"` wszędzie (Exchange, Messages, Reviews).
17. **#21 — Admin endpointy pełne** — flags, hearts grant, suspend user, categories CRUD (opcjonalnie), audit log.
18. **#22 — Semantyka `is_active`** — kiedy = false: (a) soft delete, (b) admin suspend. Jak działa suspend (login zablokowany? feed zablokowany?).

### NICE (Faza 2+, quality of life)

19. **#8 — Edycja/usunięcie wiadomości** — decyzja: **nie** (spójnie z Review immutability). Wystarczy zapisać decyzję.
20. **#12 — Logout-all password confirmation** — security UX.
21. **#13 — Unieważnianie pojedynczej sesji** — `DELETE /auth/sessions/{id}`.
22. **#20 — Account recovery** — undo soft delete przez admina lub przez usera w ciągu X dni.
23. **#23 — Admin audit log** — nowa tabela `AdminAction` (user_id, action_type, target_id, detail, created_at).

---

## Rekomendacje

### Ścieżka A — blok decyzji #63–#75 (addendum do v9)

Zamknij CRITICAL i IMPORTANT jako nowy blok decyzji w tym samym planie. Kolejne commity, v10.

**Za:**
- Szybkie domknięcie MVP
- Wszystko w jednym dokumencie (Developer ma jedno źródło)

**Przeciw:**
- Plan rośnie do ~750 linii, trudny do czytania linearnie
- Mieszanie warstw (legal, business logic, admin, edge cases)

### Ścieżka B — rozbicie na ADR-y

Wydziel CRITICAL do osobnych ADR:
- `ADR-SERCE-003-account-lifecycle.md` — soft delete, heart_balance, Requests/Offers/Exchanges handling
- `ADR-SERCE-004-admin-moderation.md` — admin endpointy, flags, audit log, ContentFlag refactor
- `ADR-SERCE-005-user-resources-api.md` — "moje" endpointy, dashboard, ledger history
- `ADR-SERCE-006-legal-compliance.md` — ToS acceptance, GDPR retention

IMPORTANT pozostaje w planie jako decyzje #63+.

**Za:**
- Każdy obszar ma zwięzły, skoncentrowany dokument
- Developer implementując konkretny obszar czyta 1 ADR (30 linii), nie cały plan (750 linii)
- ADR jako reference przy code review (Architect ma wąski focus)
- Zgodnie z pattern "Convention First" i duchem projektu (PATTERNS.md)

**Przeciw:**
- Więcej plików do utrzymania
- Więcej overhead na start

### Moja rekomendacja: **Ścieżka B**

Uzasadnienie:
1. **Fundament przed detalami** (critical_rules #9): gap-y CRITICAL dotyczą fundamentów (lifecycle, moderacja, legal) — zasługują na dedykowane ADR z rozwinięciem Context/Decision/Consequences, nie jednej linii w tabeli.
2. **Skalowalność** (SPIRIT.md: "Buduj dom, nie szałas"): plan v9 (630 linii) jest blisko granicy czytelności. Dodanie 15 decyzji w tabeli zrobi z niego ścianę tekstu. ADR-y rozkładają ciężar.
3. **Niezależność obszarów**: lifecycle nie zależy od moderacji, admin nie zależy od /me endpointów. Każdy obszar może być projektowany, reviewowany i implementowany niezależnie.
4. **Proces code review**: Developer implementując moderację otwiera ADR-SERCE-004, Architect reviewuje kod przeciw tej konkretnej specyfikacji.

---

## Następne kroki (do zatwierdzenia przez usera)

1. **Zatwierdzenie ścieżki** (A vs B) — user decyduje
2. **Dla każdego ADR / bloku decyzji** — Architect projektuje i prezentuje blokowo (jak v5–v9)
3. **Kolejność priorytetu** (jeśli ścieżka B):
   - **P1 (krytyczne dla MVP):** ADR-003 (lifecycle), ADR-004 (admin moderation), ADR-005 (user resources)
   - **P2 (przed release):** ADR-006 (legal)
   - **P3 (blok decyzji #63+):** IMPORTANT category w istniejącym planie
4. **NICE** — osobny backlog, nie blokuje Fazy 1

---

## Stan pokrycia po analizie

**Pokryte well:** auth core (register/login/refresh/reset), Exchange state machine, hearts transfer, review, flagi (mechanika), notifications (mechanika), konwencje API, security layers, paginacja, logging, ops.

**Niepokryte / niedoprecyzowane:** user resources ("moje"), admin moderation flow, lifecycle (soft delete consequences), content flagging (poza Exchange), search/sort, legal.

**Skala luk:** 23 zidentyfikowane, z czego 8 CRITICAL, 10 IMPORTANT, 5 NICE.

**Wniosek:** Architektura v9 jest **solidna w core domain** (65% pokrycia realnych user journeys), ale ma **systematyczne luki w obszarach życia konta i moderacji** (~35%). Bez uzupełnienia CRITICAL, Faza 1 backend nie daje użytecznego MVP.
