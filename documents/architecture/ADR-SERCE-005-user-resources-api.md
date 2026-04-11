# ADR-SERCE-005: User Resources API — endpointy /me, dashboard, transparentność helperów

Date: 2026-04-11
Status: Accepted

---

## Context

Plan v10 zawiera `PATCH /users/me` (edycja profilu), ale brakuje endpointów zwracających zasoby zalogowanego użytkownika. Bez nich frontend nie może zbudować strony "moje konto", użytkownik nie widzi historii swoich serc, a core flow Request-first (requester wybiera helpera spośród PENDING Exchange) nie ma jak być zrealizowany.

Walkthrough user journeys (`documents/human/reports/serce_walkthrough_gaps.md`) wskazał luki CRITICAL #6, #7, #9 + IMPORTANT #5:

1. **Brak `GET /users/me`** — własny profil z balance, verification status, kluczowymi polami
2. **Brak `GET /users/me/{requests,offers,exchanges,reviews}`** — listy własnych zasobów
3. **Brak listowania Exchange per Request** — core flow Request-first bez endpoint do wyboru helpera
4. **Brak `GET /users/me/ledger`** — user nie widzi transakcji swoich serc
5. **Brak `GET /users/me/summary`** — frontend musi robić 5–7 requestów na start dashboardu

Dodatkowo: nieujednolicony namespace (`GET /notifications` vs `/users/me/*`) wymaga decyzji spójności.

---

## Decision

### D1 — `GET /users/me` (własny profil, rozszerzony)

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "email_verified": true,
  "username": "jan_kowalski",
  "phone_number": "+48...",
  "phone_verified": true,
  "heart_balance": 23,
  "location": {"id": 12, "name": "Warszawa", "type": "CITY"},
  "bio": "...",
  "is_admin": false,
  "created_at": "2026-01-15T10:30:00Z"
}
```

Różnica vs publiczny `GET /users/{id}` (decyzja #37): `/users/me` zawiera prywatne pola (email, phone_number, heart_balance, email_verified, phone_verified, is_admin, created_at). Nie zawiera listy Offers/Requests/Reviews — te są osobnymi endpointami z paginacją, żeby nie tworzyć monster-response.

**Autoryzacja:** wymaga JWT, user widzi tylko siebie.

### D2 — `GET /users/me/requests`

- Parametry: `?status=OPEN|IN_PROGRESS|DONE|CANCELLED` (opcjonalny, domyślnie wszystkie), `?page`, `?limit`
- Default sort: `created_at DESC`
- Response: standardowa paginacja `{items, total, page, limit, pages}` (#44)
- Item: pełny Request + liczba PENDING Exchange na niego (`pending_exchanges_count`) — pomaga requesterowi szybko zobaczyć które Request ma odpowiedzi

### D3 — `GET /users/me/offers`

- Parametry: `?status=ACTIVE|PAUSED|INACTIVE`, paginacja, sort `created_at DESC`
- Item: pełny Offer + `pending_exchanges_count` na ten Offer

### D4 — `GET /users/me/exchanges`

- Parametry:
  - `?status=PENDING|ACCEPTED|IN_PROGRESS|COMPLETED|CANCELLED`
  - `?role=requester|helper` (opcjonalny — domyślnie zwraca gdzie user jest dowolną stroną)
  - `?initiated_by=me|other` (opcjonalny — filtr "kto utworzył Exchange"; przydatne dla "kogo muszę akceptować")
- Paginacja, sort `created_at DESC`
- Response item: Exchange + skrócony Request/Offer (id, title, hearts_offered/asked, status) + druga strona (zredukowany User: id, username, is_deleted)

### D5 — `GET /users/me/reviews`

- Parametr: `?direction=given|received` (wymagany, brak domyślnego — frontend explicit o co pyta)
- `given` — opinie wystawione przez usera (historia moich ocen)
- `received` — opinie otrzymane (co o mnie mówią)
- Paginacja, sort `created_at DESC`

**Uzasadnienie wymaganego parametru:** dwa wymiary semantyczne w jednym endpoint, default byłby arbitralny. Frontend zawsze wie który widok renderuje ("Moje oceny" vs "Opinie o mnie").

### D6 — `GET /users/me/ledger` — historia serc

Lista wpisów HeartLedger gdzie `from_user_id=me OR to_user_id=me`, każdy wpis znormalizowany do perspektywy zalogowanego usera:

```json
{
  "id": "uuid",
  "direction": "in" | "out",
  "amount": 5,
  "type": "INITIAL_GRANT" | "PAYMENT" | "GIFT" | "ADMIN_GRANT" | "ACCOUNT_DELETED",
  "counterparty": {
    "id": "uuid",
    "username": "maria",
    "is_deleted": false
  } | null,
  "related_exchange_id": "uuid" | null,
  "note": "...",
  "created_at": "2026-04-11T12:00:00Z"
}
```

**Reguły:**
- `direction` wyliczane przez backend (`out` gdy `from_user_id=me`, `in` gdy `to_user_id=me`)
- `counterparty` = null dla:
  - SYSTEM grants (`INITIAL_GRANT`, `ADMIN_GRANT` od systemu — `from_user_id IS NULL`)
  - `ACCOUNT_DELETED` z perspektywy patrzącego (to_user_id=NULL po void)
- `counterparty` = placeholder (username=null, is_deleted=true) jeśli druga strona usunęła konto
- Parametry: `?type=` (filtr), `?direction=in|out` (filtr), paginacja, sort `created_at DESC`

### D7 — Namespace notifications: unifikacja do `/users/me/notifications`

`GET /notifications` **usunięte z planu**. Zastąpione przez `GET /users/me/notifications`.

**Powód:** spójność namespace — wszystkie zasoby zalogowanego usera pod `/users/me/*`. Plan v10 jeszcze nie zaimplementowany, ujednolicenie teraz = zero breaking changes.

Analogicznie:
- `POST /notifications/{id}/read` → `POST /users/me/notifications/{id}/read`
- `POST /notifications/read-all` → `POST /users/me/notifications/read-all`

### D8 — `GET /users/me/summary` — dashboard w jednym strzale

```json
{
  "heart_balance": 23,
  "unread_notifications_count": 4,
  "pending_exchanges_count": 2,
  "pending_reviews_count": 1,
  "active_requests_count": 1,
  "active_offers_count": 3,
  "email_verified": true,
  "phone_verified": false,
  "unresolved_flags_count": 7
}
```

**Mapowanie pól na UI:**

| Pole | Kalkulacja | UI |
|---|---|---|
| `heart_balance` | User.heart_balance | Nagłówek, widżet przy avatarze |
| `unread_notifications_count` | COUNT Notification WHERE user_id=me AND is_read=false | Badge dzwonka |
| `pending_exchanges_count` | COUNT Exchange WHERE (requester=me OR helper=me) AND status=PENDING | Badge "Moje wymiany" |
| `pending_reviews_count` | COUNT Exchange WHERE (requester=me OR helper=me) AND status=COMPLETED AND brak Review(reviewer=me) | Badge/prompt "Oceń" |
| `active_requests_count` | COUNT Request WHERE user_id=me AND status IN (OPEN, IN_PROGRESS) | Badge "Moje prośby" |
| `active_offers_count` | COUNT Offer WHERE user_id=me AND status=ACTIVE | Badge "Moje oferty" |
| `email_verified` | User.email_verified | Banner ostrzegawczy jeśli false |
| `phone_verified` | User.phone_verified | Banner "zweryfikuj, dostaniesz 5 serc" jeśli false |
| `unresolved_flags_count` | COUNT ExchangeFlag WHERE resolved_at IS NULL | Badge admina (tylko gdy `is_admin=true`, inaczej pole nieobecne) |

**Zasady:**
- Endpoint read-only, brak skutków ubocznych — łatwy do cache'owania (Redis w przyszłości)
- Liczniki wyliczane SQL COUNT — akceptowalny koszt dla v1 (skala <10k userów)
- Pole `unresolved_flags_count` **warunkowe** — obecne tylko w response gdy `is_admin=true`, pomijane dla zwykłych userów (nie null, nie 0 — nieobecne w kluczach JSON)

**Pominięte świadomie:**
- Listy obiektów (najnowsze Request, Exchange) — to są osobne endpointy z paginacją, nie dashboard
- `member_since`, `completed_exchanges_count` — nie są first-render critical, dostępne w `/users/me` lub publicznym profilu

### D9 — Listowanie Exchange per Request/Offer: transparentność helperów

**`GET /requests/{id}/exchanges`** — lista wszystkich Exchange na ten Request.

**`GET /offers/{id}/exchanges`** — lista wszystkich Exchange na ten Offer.

**Autoryzacja (transparentność):**

- **Owner zasobu** (Request.user_id lub Offer.user_id) widzi **wszystkie** Exchange na swój zasób (pełny widok "kto się zgłosił")
- **Helper z PENDING/ACCEPTED Exchange** na tym Request/Offer widzi **wszystkie** Exchange (własny + rywali) — **transparentność**: helper wie z kim konkuruje, ile innych osób zgłosiło się, jakie oferują hearts_agreed
- **Inny zalogowany user** (nie owner, nie uczestnik żadnego Exchange) → 403 Forbidden
- **Anonim** (bez JWT) → 401

**Uzasadnienie transparentności:**

- **Duch projektu** (SPIRIT.md): "Buduj dom, nie szałas" — helperzy podejmują świadome decyzje czy nadal pchać Exchange, widząc konkurencję
- **UX uczciwości:** helper nie jest pozostawiony w czarnej skrzynce — wie co go czeka
- **Anti-ghosting:** widząc 5 innych helperów, helper nie czuje obowiązku realizowania Exchange na siłę (redukcja poczucia winy przy cancel)
- **Social proof:** requester widzi że jego Request ma odzew — mniej poczucia odrzucenia

**Redukowane pola dla nie-ownerów:**

Helper widząc rywali nie potrzebuje wszystkiego. Response item dla nie-owner:
```json
{
  "id": "uuid",
  "helper": {"id": "uuid", "username": "marek", "is_deleted": false},
  "hearts_agreed": 5,
  "status": "PENDING",
  "created_at": "..."
}
```

Pełny obiekt Exchange (wszystkie pola + Message history) → tylko owner Request lub uczestnik tego konkretnego Exchange (via `GET /exchanges/{id}`).

**Alternatywa odrzucona (ścieżka A z propozycji):** endpoint tylko dla ownera. Odrzucona — priorytet transparentności wyższy niż prywatność konkurencyjnych helperów (decyzja usera 2026-04-11).

### D10 — `GET /exchanges/{id}/messages` — odczyt wiadomości Exchange

- Parametry: `?page=1&limit=50`
- Default sort: `created_at ASC` (chronologicznie, chat-like UX)
- Autoryzacja: tylko `requester_id` i `helper_id` tego Exchange; 403 inni, 401 anonim
- Response item: Message (id, sender, content, created_at) + sender jako zredukowany User (id, username, is_deleted)

**Uwaga:** plan v10 wspomina `POST /exchanges/{id}/messages` w Fazie 1 — ADR-005 doprecyzowuje `GET` do kompletu.

### D11 — Edycja/usuwanie wiadomości: brak

Message jest **niemodyfikowalne** po wysłaniu. Brak `PATCH /messages/{id}`, brak `DELETE /messages/{id}`.

**Uzasadnienie:**

- **Spójność z Review** (#29) — również niemodyfikowalne
- **Integralność kontekstu Exchange** — druga strona nie zobaczy zmian retroaktywnie zmieniających znaczenie rozmowy
- **Prostota modelu** — brak `edited_at`, `deleted_at` na Message; brak logiki cache invalidation
- **Duch projektu** — rozmowa to ślad intencji w danym momencie, nie dokument do redakcji

**Edge case — wiadomość obraźliwa/błędna:** flagowanie przez `ContentFlag` (ADR-SERCE-004) → admin interweniuje ręcznie (oznaczenie jako ukrytej lub edit w DB). Nie self-service.

---

## Consequences

### Zyskujemy

- **Kompletny /me namespace** — frontend ma jedno spójne miejsce dla zasobów zalogowanego usera
- **Minimalizacja latencji startu aplikacji** — dashboard w 1 request (`/users/me/summary`) zamiast 5–7
- **Core flow Request-first odblokowany** — `GET /requests/{id}/exchanges` pozwala requesterowi zobaczyć i wybrać helpera
- **Transparentność helperów** (D9) — fair-play konkurencja, świadome decyzje, anti-ghosting
- **Audit transparentności waluty** — `/users/me/ledger` daje userowi pełny wgląd w transakcje serc, buduje zaufanie
- **Spójność namespace** — wszystkie moje zasoby pod `/users/me/*`
- **Prostota modelu wiadomości** — niemodyfikowalność eliminuje klasy bugów (edit conflicts, stale cache)

### Koszty / trade-offy

- **Wiele endpointów do implementacji w Fazie 1** — 10 nowych ścieżek API (`/users/me`, `/me/requests`, `/me/offers`, `/me/exchanges`, `/me/reviews`, `/me/ledger`, `/me/notifications`, `/me/summary`, `/requests/{id}/exchanges`, `/offers/{id}/exchanges`, `/exchanges/{id}/messages`)
- **COUNT queries w `/me/summary`** — 7 COUNT w jednym request, akceptowalne dla <10k userów, ale przy skalowaniu → materialized view lub Redis cache
- **Autoryzacja złożona dla D9** — logika "czy user jest ownerem LUB helperem z aktywnym Exchange" wymaga kilku SELECT. Mitygacja: dedykowana funkcja `can_view_request_exchanges(user_id, request_id)` w warstwie service
- **Transparentność D9 może wzmocnić FOMO** — helper widzący 10 rywali może rezygnować zamiast konkurować. Mitygacja: monitorowanie metryki "cancel rate PENDING Exchange" po launch; rollback do owner-only jeśli problem się zmaterializuje (hybryda możliwa: transparentność tylko powyżej N rywali)
- **Message niemodyfikowalne** — user nie cofnie literówki. Akceptowalny trade-off (spójność z Review, prostota)

### Odwracalność

- **Wysoka dla D1–D8, D10, D11:** dodawanie/usuwanie pól response, zmiana parametrów — bez wpływu na dane w DB
- **Średnia dla D9:** zmiana autoryzacji z transparentnej na owner-only wymaga analizy metryk + komunikacji do userów. Łatwo technicznie, trudniej społecznie
- **Wysoka dla D7:** namespace można zmienić przez dodanie aliasu (backward-compat)

---

## Rozszerzenia wymagane w planie v10

**Sekcja "Decyzje projektowe":**
- Nowe decyzje #70–#79 (10 pozycji — jedna per D1..D11, łączymy D2/D3 w jedną linijkę gdzie stosowne)

**Sekcja "Konwencje API":**
- Dodanie endpointów `/users/me/*` do listy przykładów
- Dodanie `/requests/{id}/exchanges`, `/offers/{id}/exchanges`

**Faza 1 implementacji:**
- Rozszerzenie o 10 nowych endpointów
- Zamiana `GET /notifications` na `GET /users/me/notifications` (D7)

**Decyzja #22 (Powiadomienia):**
- Korekta ścieżek: `GET /users/me/notifications` zamiast `GET /notifications`

---

## Testy (rozszerzenie MUST-COVER #58)

```
test_get_me__returns_private_fields_including_email_phone_balance
test_get_me__without_jwt__returns_401
test_get_me_requests__filters_by_status
test_get_me_requests__includes_pending_exchanges_count
test_get_me_exchanges__role_filter_requester_excludes_helper_rows
test_get_me_exchanges__initiated_by_other__returns_only_needing_my_action
test_get_me_reviews__direction_required_or_422
test_get_me_ledger__direction_in_for_to_user_id_me
test_get_me_ledger__counterparty_null_for_system_grant
test_get_me_ledger__counterparty_placeholder_for_deleted_user
test_get_me_summary__admin_gets_unresolved_flags_count_field
test_get_me_summary__regular_user_no_unresolved_flags_count_key
test_get_me_summary__pending_reviews_count_excludes_already_reviewed
test_get_request_exchanges__as_owner__sees_all_participants
test_get_request_exchanges__as_participating_helper__sees_rivals_reduced_view
test_get_request_exchanges__as_uninvolved_user__returns_403
test_get_request_exchanges__without_jwt__returns_401
test_get_exchange_messages__as_non_participant__returns_403
test_message_endpoints__no_patch_no_delete_exist (404 na obu metodach)
```

---

## Ref

- Plan: `documents/human/plans/serce_architecture.md` (decyzje #22, #37, #44)
- Walkthrough: `documents/human/reports/serce_walkthrough_gaps.md` (CRITICAL #6, #7, #9; IMPORTANT #5)
- ADR-SERCE-003: Account Lifecycle (prezentacja usuniętego usera — spójność z D1, D5, D9)
