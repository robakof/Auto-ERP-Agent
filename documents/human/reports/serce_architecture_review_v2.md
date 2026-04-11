# Serce v14 — głęboka weryfikacja przed implementacją

Date: 2026-04-11
Reviewer: Developer
Source: `documents/human/plans/serce_architecture.md` (v14, 862 linii)

---

## KONFLIKTY (sprzeczne zapisy w planie)

### K1. Reguła #4 vs #23 i decyzja #35 — zakres cancel Exchange

- **Reguła #4** (linia 548): "Exchange można anulować **do ACCEPTED**"
- **Reguła #23** (linia 566): "Cancel Exchange: dostępny w każdym momencie **przed COMPLETED**"
- **Decyzja #35** (linia 679): "Obie strony, w każdym momencie **przed COMPLETED**"

"Do ACCEPTED" wyklucza IN_PROGRESS. "Przed COMPLETED" obejmuje IN_PROGRESS.
Reguła #23 i decyzja #35 są spójne. Reguła #4 jest stała — powinna mówić "przed COMPLETED".

### K2. Exchange.IN_PROGRESS — status bez zdefiniowanego przejścia

Exchange.status enum: `PENDING, ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED`.

Zdefiniowane przejścia w flowach:
- PENDING → ACCEPTED (via /accept)
- PENDING → CANCELLED (via /cancel, auto-cancel)
- ACCEPTED → COMPLETED (via /complete)
- ACCEPTED → CANCELLED (via /cancel)
- ??? → IN_PROGRESS (brak triggera)

IN_PROGRESS jest w enum ale **żaden flow, endpoint ani reguła nie definiuje kiedy Exchange wchodzi w ten stan**. Opcje:
- (a) Usunąć IN_PROGRESS z enum — ACCEPTED → COMPLETED bezpośrednio
- (b) IN_PROGRESS = auto po /accept (semantycznie: "usługa w trakcie realizacji")
- (c) Dodać endpoint POST /exchanges/{id}/start

Rekomendacja: (a) — upraszcza state machine, v1 nie potrzebuje granulacji ACCEPTED vs IN_PROGRESS.

---

## BRAKUJĄCE ZACHOWANIA (plan milczy)

### B1. Brak endpointu anulowania własnego Request przez usera

Request.status: `OPEN, IN_PROGRESS, DONE, CANCELLED, HIDDEN`.
Offer ma `PATCH /offers/{id}/status` (ACTIVE/PAUSED/INACTIVE).
Request nie ma odpowiednika — user nie ma jak anulować własnej otwartej prośby.

APScheduler wygasza po expires_at, ale user nie może sam anulować wcześniej.
Soft delete anuluje Requests kaskadowo, ale to nie jest cancel jednego Request.

**Potrzebny:** `POST /requests/{id}/cancel` lub `PATCH /requests/{id}/status` (analogicznie do Offer).

### B2. Brakujące guardy: na jakim statusie Request/Offer można tworzyć Exchange?

Flow zakłada Exchange na OPEN Request / ACTIVE Offer, ale brak jawnej walidacji:
- Exchange na CANCELLED/DONE/HIDDEN Request → powinien 422
- Exchange na INACTIVE/PAUSED/HIDDEN Offer → powinien 422? PAUSED = pauza, ale czy blokuje nowe Exchange?

Rekomendacja: Exchange dozwolony tylko na OPEN Request i ACTIVE Offer. PAUSED Offer blokuje nowe Exchange (semantyka pauzy).

### B3. HeartLedger type=PAYMENT — nigdzie nie przypisany

Enum: `INITIAL_GRANT, PAYMENT, GIFT, ADMIN_GRANT, ADMIN_REFUND, ACCOUNT_DELETED`.
Przepływy:
- Exchange complete → transfer serc → INSERT HeartLedger z typem **???**
- Gift → type=GIFT
- Initial grant → type=INITIAL_GRANT

PAYMENT jest logicznym typem dla transferu przy Exchange completion, ale **żaden flow tego nie mówi jawnie**.

### B4. PATCH /users/me/username — w checkliście, brak w URL structure i flowach

Checklista (linia 587): "PATCH /users/me/username + PATCH /users/me/email (z weryfikacją)"
Decyzja #28: "Zmiana username i email przez osobne endpointy z weryfikacją"

Brak:
- Endpointu w URL structure
- Opisu flow weryfikacji (co wymaga? hasło? token? email confirmation?)
- Email change ma pełny flow (decyzja #93). Username change nie ma żadnego.

### B5. POST /hearts/gift — w flow, brak w URL structure

Flow "Darowizna serc" (linia 463): "User POST /hearts/gift → {to_user_id, amount, note}"
Nie pojawia się w sekcji URL structure (linii 752–808).

### B6. DELETE /users/me — w flow, brak w URL structure

Soft delete flow szczegółowo opisany, ale endpoint nie pojawia się w URL structure.

---

## DWUZNACZNOŚCI (można interpretować na dwa sposoby)

### D1. Request.IN_PROGRESS — kiedy wraca do OPEN?

Reguła #23: "Request → OPEN (jeśli był IN_PROGRESS)" przy cancel Exchange.
Ale Request.IN_PROGRESS jest ustawiany "when Exchange ACCEPTED" (flow linia 451).

Scenariusz:
1. Request OPEN → Helper tworzy Exchange → Exchange PENDING
2. Requester accepts → Exchange ACCEPTED → Request IN_PROGRESS
3. Helper cancels → Exchange CANCELLED → Request OPEN (per reguła #23)
4. Inny helper tworzy Exchange → OK, Request jest OPEN

Ale: co jeśli Exchange cancel był przy Exchange IN_PROGRESS (nie ACCEPTED)?
Per konflikt K2 — jeśli IN_PROGRESS nie istnieje w Exchange, to problem znika.
Jeśli istnieje — reguła #23 powinna obejmować oba stany Exchange.

### D2. GET /users/{id} (publiczny profil) — sublists bez paginacji

Decyzja #37: response zawiera "lista aktywnych Offers, lista aktywnych Requests, lista Reviews".
Pozostałe listing endpoints mają paginację. Tu brak specyfikacji.

User z 50 aktywnymi Offers i 200 Reviews → response może być bardzo duży.
Opcje: (a) limit do N ostatnich per sublist, (b) paginacja, (c) osobne endpointy (ale to publiczny profil).

### D3. `pending_reviews_count` w /users/me/summary — definicja

Decyzja #75 wymienia `pending_reviews_count` ale nie definiuje semantyki.
Domniemana logika: COUNT(Exchange) WHERE status=COMPLETED AND current_user is participant AND NOT EXISTS Review(exchange_id, reviewer_id=current_user).

---

## URL STRUCTURE — NIEKOMPLETNA

Sekcja "Przykłady:" (linia 758) sugeruje że lista nie jest wyczerpująca.
Brakujące endpointy (opisane w flowach/checkliście, ale nie w URL structure):

```
# Auth (podstawowe — opisane w flowach)
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/logout-all
POST   /api/v1/auth/verify-email
POST   /api/v1/auth/verify-phone
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password

# Profile
PATCH  /api/v1/users/me/username          # checklista, brak flow

# Hearts
POST   /api/v1/hearts/gift                # flow "Darowizna serc"
GET    /api/v1/hearts/balance             # checklista "balance endpoint" — lub wystarczy /users/me?

# Requests
POST   /api/v1/requests/{id}/cancel       # brakujący (B1)

# Account
DELETE /api/v1/users/me                   # flow "Soft delete"
```

Rekomendacja: zamienić "Przykłady:" na pełną listę endpointów — eliminuje dwuznaczności przy implementacji.

---

## DROBNE (nie blokują, do odnotowania)

- M1. Reguły: numery 17-18 nadal puste (gap po renumeracji). Kosmetyczne.
- M2. Brak rate limit na flag endpoints — spam flagów możliwy. Drobne ryzyko w v1.
- M3. Notification.user_id nie ma CASCADE DELETE (inne tokeny mają). Nieistotne przy soft delete, ale ważne przy future hard delete.
- M4. hearts/balance jako osobny endpoint vs /users/me — checklista mówi "balance endpoint" ale /users/me i /users/me/summary już zwracają heart_balance.

---

## PODSUMOWANIE

| Kategoria | Ilość | Akcja |
|-----------|-------|-------|
| Konflikty | 2 | K1 = errata reguły #4. K2 = decyzja architekta (Exchange.IN_PROGRESS) |
| Brakujące zachowania | 6 | B1-B2 wymagają decyzji. B3-B6 = uzupełnienia planu |
| Dwuznaczności | 3 | D1 znika jeśli K2 rozwiązane. D2-D3 = drobne |
| URL structure | ~12 endpointów | Uzupełnić do pełnej listy |
| Drobne | 4 | Informacyjne |

**Najważniejsze do zamknięcia przed kodem:**
1. K2 — Exchange.IN_PROGRESS: usunąć czy zdefiniować przejście?
2. B1 — Brak cancel Request: dodać endpoint?
3. B2 — Guardy Exchange creation: jawnie zdefiniować dozwolone statusy
