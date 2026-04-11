# ADR-SERCE-003: Cykl życia konta (soft delete, kaskada, prezentacja)

Date: 2026-04-11
Status: Accepted

---

## Context

Plan v9 decyzja #11 wprowadza soft delete (anonimizacja, `deleted_at`, `anonymized_at`), ale nie precyzuje **konsekwencji** usunięcia konta w czterech obszarach:

1. **heart_balance** — co z saldem waluty usera w momencie usunięcia
2. **OPEN Requests** i **ACTIVE/PAUSED Offers** — czy pozostają w feedzie
3. **Aktywne Exchange** (PENDING/ACCEPTED/IN_PROGRESS) — co z zobowiązaniami wobec drugiej strony
4. **Prezentacja usuniętego usera** w historii (Exchange, Messages, Reviews) drugiej strony

Walkthrough user journeys (`documents/human/reports/serce_walkthrough_gaps.md`) ujawnił że bez tych decyzji Faza 1 nie domyka cyklu życia konta. Obszar dotyka waluty systemowej i zobowiązań między użytkownikami — ryzyko prawne, utraty zaufania, zawieszonych transakcji.

---

## Decision

### D1 — Heart balance przy soft delete: wymagana dyspozycja (opcja C)

User inicjujący `DELETE /users/me` z `heart_balance > 0` **musi wskazać dyspozycję** waluty. Bez dyspozycji endpoint zwraca 422.

**API:**
```
DELETE /users/me
Body: {
  "balance_disposition": "void" | "transfer",
  "transfer_to_user_id": "<uuid>" (wymagane gdy disposition=transfer)
}
```

Gdy `heart_balance = 0` — body opcjonalne (lub z `disposition=void` dla spójności).

**Dwie opcje dyspozycji:**

1. **`void`** — user świadomie akceptuje że `X` serc przepadnie.
   - INSERT `HeartLedger(from_user_id=user, to_user_id=NULL, amount=balance, type=ACCOUNT_DELETED)`
   - `UPDATE user SET heart_balance = 0`

2. **`transfer`** — user przekazuje saldo innemu użytkownikowi.
   - Walidacja: recipient istnieje, `is_active = true`, `deleted_at IS NULL`, `!= self`, `recipient.heart_balance + amount <= heart_balance_cap`
   - Jeśli przekracza cap → 422 `CAP_EXCEEDED` z `max_receivable` (user wybiera: zmniejszyć amount przez void części, zmienić recipient)
   - INSERT `HeartLedger(from_user_id=user, to_user_id=recipient, amount=balance, type=GIFT, note='balance transfer przed usunięciem konta')`
   - Notification `HEARTS_RECEIVED` do recipient

**Rate limit `gift` (#50) nie dotyczy tego transferu** — jest to akcja jednorazowa przy usunięciu, nie zwykły gift. Osobna ścieżka w service.

**Uzasadnienie wyboru opcji C vs A (przepadają zawsze):**
- User zachowuje kontrolę nad własną walutą do końca
- Eliminuje ryzyko "przypadkowej utraty waluty" (klient omyłkowo kliknął delete)
- Wymusza świadomą decyzję (anti-regret UX pattern)
- Audit trail jednoznaczny: ledger pokazuje intencję usera (void vs transfer)

**Koszt:** dodatkowy endpoint preview + walidacja dyspozycji + logika transferu w service delete. Akceptowalny — obszar dotyka waluty, dodatkowy tarcie UX jest cechą, nie wadą.

### D2 — OPEN Requests przy soft delete: auto-CANCELLED

Wszystkie `Request.status = OPEN` należące do usera → `CANCELLED` w tej samej transakcji co soft delete.

Powiązane `Exchange.status = PENDING` na te Requests → auto-CANCELLED (patrz D4, kaskadowo).

**Dlaczego CANCELLED, nie DONE/DELETED:** spójne z semantyką cancel w #34/#35. Status `CANCELLED` oznacza "zakończone bez realizacji". Druga strona (PENDING helper) dostaje standardowe powiadomienie.

### D3 — ACTIVE/PAUSED Offers przy soft delete: auto-INACTIVE

Wszystkie `Offer.status ∈ {ACTIVE, PAUSED}` usera → `INACTIVE`.

Powiązane `Exchange.status = PENDING` → auto-CANCELLED (D4).

**Dlaczego INACTIVE, nie CANCELLED:** Offer to wizytówka (#17), nie proszenie. Status `INACTIVE` istnieje w enum Offer (plan v9). Semantyka: "ta oferta już nie obowiązuje". Nie trzeba nowego stanu.

### D4 — Aktywne Exchange przy soft delete: auto-CANCELLED z powiadomieniem

Wszystkie `Exchange.status ∈ {PENDING, ACCEPTED, IN_PROGRESS}` gdzie user = `requester_id` LUB `helper_id` → `CANCELLED`.

**Konsekwencje dla drugiej strony:**

- **Brak konsekwencji finansowych** — spójne z #35 (serca nie zamrożone w ACCEPTED, cancel możliwy zawsze przed COMPLETED)
- Notification `EXCHANGE_CANCELLED` do drugiej strony z polem `reason: 'account_deleted'`
- Jeśli Exchange był Request-first i powiązany Request należał do **usuwanego** usera → Request już jest auto-CANCELLED przez D2
- Jeśli Exchange był Request-first i powiązany Request należał do **drugiej** strony (tj. usuwany user był helperem) → Request drugiej strony **wraca do OPEN** (spójnie z #34 — cancel po ACCEPTED cofa Request do OPEN)
- Jeśli Exchange był Offer-first i Offer należała do **usuwanego** usera → Offer już jest auto-INACTIVE przez D3
- Jeśli Exchange był Offer-first i Offer należała do **drugiej** strony → Offer drugiej strony **pozostaje ACTIVE** (Offer = wizytówka, inne Exchange na nią nadal mogą trwać)

**Rozszerzenie Notification:** dodanie pola `reason: str (nullable)` — kontekst dla `EXCHANGE_CANCELLED` ("account_deleted", "user_cancel", "admin_resolve", ...).

### D5 — Prezentacja usuniętego usera: flag + null fields

Wszystkie endpointy zwracające referencję do User (public profile, Exchange participants, Messages sender, Reviews author) renderują **ten sam format** dla usuniętego konta:

```json
{
  "id": "<oryginalne UUID>",
  "username": null,
  "bio": null,
  "location": null,
  "is_deleted": true
}
```

**Pełne reguły:**

- `GET /users/{deleted_uuid}` → **HTTP 200** z placeholder powyżej (nie 404, UUID technicznie istnieje)
- W listingach (Exchange messages, reviews) — sender/author serializowany tym samym formatem
- `is_deleted: true` + `username: null` jest sygnałem dla frontendu; renderowanie tekstu ("Użytkownik usunięty", "Deleted user", ikona) → **frontend concern** (i18n-ready)
- Reviews wystawione przez usuniętego użytkownika **pozostają widoczne** (publiczna opinia, integralność reputacji), autor = placeholder
- Aktywne Offers nie są zwracane (są INACTIVE → filtr feedu je wyklucza)
- Zgodnie z #37: email, phone_number, heart_balance, deleted_at są ukryte na publicznym profilu — tu dodatkowo username, bio, location → null

**Uzasadnienie vs stały tekst "Użytkownik usunięty":**
- Technicznie elastyczne (flag + null)
- i18n: tłumaczenie w UI, nie w API
- Frontend może wybrać różne reprezentacje dla różnych kontekstów (Exchange history vs public feed)
- Spójne z REST principle: API zwraca dane, nie gotowe UI strings

### D6 — Transakcyjność soft delete: all-or-nothing

Operacja soft delete jest **jedną DB transaction** w `UserService.soft_delete(user_id, disposition)`:

```
BEGIN TX
  1. Walidacja dyspozycji (D1): gdy balance > 0 — wymagane; gdy transfer — walidacja recipient
  2. Auto-CANCEL Exchange WHERE (requester_id=user OR helper_id=user)
       AND status IN ('PENDING','ACCEPTED','IN_PROGRESS')
     → Dla każdego: Request drugiej strony → OPEN (D4), Notification queued
  3. Auto-CANCEL Request WHERE user_id=user AND status='OPEN'
  4. Auto-INACTIVE Offer WHERE user_id=user AND status IN ('ACTIVE','PAUSED')
  5. Dyspozycja heart_balance:
       - void: INSERT HeartLedger(type=ACCOUNT_DELETED, to_user_id=NULL, amount=balance)
       - transfer: SELECT recipient FOR UPDATE; walidacja cap; UPDATE recipient balance;
                   INSERT HeartLedger(type=GIFT, to_user_id=recipient, amount=balance)
     UPDATE user heart_balance = 0
  6. Anonimizacja: email=hash, username=hash, phone_number=NULL
  7. UPDATE user SET deleted_at=now, anonymized_at=now, is_active=false
  8. UPDATE refresh_tokens SET revoked_at=now WHERE user_id=user
COMMIT

-- Poza TX (best effort, nie blokuje delete):
  - Wysyłka emaili z powiadomieniami (queued w kroku 2)
  - Wysyłka emaila "konto usunięte" na stary email (przed anonimizacją zachować kopię)
```

**Uzasadnienie atomowości:**

Częściowy fail = spójność domeny pęknięta. Przykłady:
- Kroki 1–6 się powiodły, krok 7 padł → user nadal `is_active`, ale balance wyzerowany, historia zresetowana → duch w systemie
- Kroki 1–4 się powiodły, krok 5 padł → Exchange pocancelowane, ale user nadal żyje z saldem → druga strona dostała cancel bez powodu

All-or-nothing eliminuje klasy tych błędów. **Service ma być testowany jako pierwsza integration test kandydatura** (lista MUST-COVER #58).

### D7 — Grace period / undelete: brak w v1

Soft delete = natychmiastowy, nieodwracalny self-service.

**Odrzucono:** 30-dniowy grace period z możliwością undelete.

**Powód odrzucenia:**
- Wymaga: dodatkowy stan `pending_deletion`, scheduled job finalizujący po 30 dniach, logika "zawieszonego" konta (czy może się zalogować? widzieć feed? akceptować Exchange?)
- Dla v1 (MVP) — overhead nie uzasadniony
- Admin może w skrajnych przypadkach ręcznie cofnąć soft delete przez DB (UPDATE deleted_at=NULL) — nie self-service

Account recovery (self-service undelete) → NICE backlog, Faza 2+.

### D8 — Hard delete (GDPR "right to be forgotten"): odroczony

**v1:** tylko soft delete self-service + soft delete admin.

Soft delete = pseudoanonymization zgodna z GDPR art. 17 — dane osobowe (email, username, phone, bio, location) usunięte, historia finansowa (HeartLedger) i kontraktowa (Exchange, Review, Messages) zachowana jako legalny interes (integralność waluty, reputacja społeczności).

**Hard delete** (fizyczne usunięcie wszystkich wierszy + hash UUID z FK) → **Faza 4 lub ad-hoc** przez admina na żądanie prawne. Wymaga osobnej decyzji (które FK NULLować, jak zachować audit trail finansowy bez powiązania z userem).

Nie blokuje Fazy 1.

---

## Consequences

### Zyskujemy

- **Jednoznaczny cykl życia konta** — brak szarych stref, każdy stan (balance, requests, offers, exchanges) ma zdefiniowaną dyspozycję
- **Audit trail waluty** — HeartLedger kompletny, intencja usera (void vs transfer) zapisana
- **Druga strona zawsze powiadomiona** — żadne Exchange/Request/Offer nie zostaje w stanie zawieszonym
- **User zachowuje kontrolę** — wymagana świadoma dyspozycja (D1 opcja C) eliminuje przypadkowe straty
- **Spójność transakcyjna** — all-or-nothing eliminuje klasę błędów "duch w systemie"
- **Historia zachowana dla integralności** — Review, Messages, Exchange nadal widoczne, autor = placeholder (D5)
- **API elastyczne** — flag `is_deleted` + null fields zamiast sztywnego stringa, frontend i18n-ready

### Koszty / ryzyka

- **`HeartLedger.to_user_id` nullable** — więcej null-handling w zapytaniach i serializacji, zmiana existing schematu (Alembic migration)
- **Rozszerzenie enum HeartLedger.type** — dodanie `ACCOUNT_DELETED` (Alembic migration + CHECK constraint update)
- **Rozszerzenie Notification** — dodanie pola `reason: str (nullable)` (Alembic migration)
- **Service `soft_delete` złożony** — 8 kroków w transakcji, trudny do debugowania gdy fail. Mitygacja: dedykowane integration testy (MUST-COVER), structured logging per krok (decyzja #55)
- **Brak account recovery** — błędne delete jest nieodwracalne self-service. Mitygacja: wymagana dyspozycja (D1) + UI ostrzeżenie z listą konsekwencji (frontend concern)
- **Dyspozycja transfer rodzi cap edge case** — recipient może mieć mało miejsca na saldo. Rozwiązane przez 422 z `max_receivable` (użytkownik redukuje amount lub zmienia recipient)

### Odwracalność

- D1 (opcja C): średnio odwracalna. Zmiana na A (zawsze void) to usunięcie walidacji + uproszczenie endpoint — łatwe. Zmiana z A na C (po deploy) trudna, bo userowie mogli już stracić serca bez ostrzeżenia (trust erosion).
- D2–D4: średnio odwracalna. Zmiana semantyki kaskady po deploy wymaga analizy historycznej — "czy te Requests powinny były wrócić do OPEN, a wróciły do CANCELLED?". Lepiej zdecydować dobrze teraz.
- D5: wysoce odwracalna. Format API może ewoluować (dodanie/usunięcie pól) bez zmian historycznych danych.
- D6: odwracalna tylko technicznie (transakcja to implementation detail). Usunięcie atomowości = regresja.
- D7/D8: wysoce odwracalna. Grace period i hard delete można dodać w dowolnym momencie.

---

## Rozszerzenia wymagane w planie v9

**Model domenowy (sekcja User, HeartLedger, Notification):**
- `HeartLedger.to_user_id`: NOT NULL → **nullable**
- `HeartLedger.type` enum: dodanie `ACCOUNT_DELETED`
- `Notification`: dodanie pola `reason: str (nullable)`

**Sekcja "Usunięcie konta" (przepływy):**
- Rozszerzenie o D1 (dyspozycja) + D6 (transakcja 8 kroków)

**Sekcja "Decyzje projektowe":**
- Dopisek do #11: "Szczegóły kaskady w ADR-SERCE-003"
- Nowe decyzje #63–#67 jako skrócony wiersz w tabeli z referencją do ADR-003

**Faza 1 implementacji:**
- Nowy punkt: "Soft delete: UserService.soft_delete z transakcyjną kaskadą (D1–D6), testy integracyjne all-or-nothing"

---

## Testy (rozszerzenie MUST-COVER w #58)

```
test_soft_delete__balance_zero__succeeds_without_disposition
test_soft_delete__balance_positive__requires_disposition_or_422
test_soft_delete__disposition_void__ledger_entry_account_deleted
test_soft_delete__disposition_transfer__recipient_balance_updated_and_ledger_gift
test_soft_delete__disposition_transfer_exceeds_cap__returns_422_max_receivable
test_soft_delete__disposition_transfer_to_self__returns_422
test_soft_delete__disposition_transfer_to_deleted_user__returns_422
test_soft_delete__with_open_requests__auto_cancels_all
test_soft_delete__with_active_offers__auto_inactive_all
test_soft_delete__with_active_exchanges_as_helper__cancels_and_requests_reopen
test_soft_delete__with_active_exchanges_as_requester__cancels_own_request
test_soft_delete__with_pending_exchanges_on_own_request__cascades_cancel
test_soft_delete__notifies_affected_parties_with_reason_account_deleted
test_soft_delete__revokes_all_refresh_tokens
test_soft_delete__transaction_fails_mid_way__rolls_back_all_state
test_get_deleted_user__returns_placeholder_with_is_deleted_true
test_get_deleted_user_offers__not_in_feed (inactive)
test_messages_from_deleted_user__renders_placeholder_sender
```

---

## Alternatywy odrzucone

**D1 opcja A (zawsze void):** prosta, ale eliminuje kontrolę usera nad walutą. Odrzucona po rozmowie — user zachowuje prawo do dyspozycji.

**D1 opcja B (zachowane technicznie):** ukryta waluta bez beneficjenta, sprzeczna z brakiem grace period. Odrzucona.

**D1 opcja D (auto-transfer do predefiniowanego):** rodzi pytania "do kogo?", "dlaczego tam?", uzależnia od konfiguracji systemowej. Odrzucona jako over-engineering.

**D5 stały tekst "Użytkownik usunięty":** mieszanie warstw (UI string w API response), blokuje i18n. Odrzucone na rzecz flag + null fields.

**D7 30-dniowy grace period:** wymaga scheduled job, nowego stanu, logiki zawieszonego konta. Over-engineering dla v1. Odrzucone — do backlogu NICE.

**D8 hard delete w v1:** wymaga osobnego projektu (które FK NULLować, jak zachować audit bez powiązania). Odłożone do Fazy 4.

---

## Ref

- Plan: `documents/human/plans/serce_architecture.md` (decyzja #11)
- Walkthrough: `documents/human/reports/serce_walkthrough_gaps.md` (gap-y CRITICAL #16, #17, #18, #19)
- ADR-SERCE-002: Hearts Ledger (model który rozszerzamy o `ACCOUNT_DELETED`)
