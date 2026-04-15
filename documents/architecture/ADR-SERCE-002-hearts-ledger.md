# ADR-SERCE-002: Serca jako księga (ledger), nie obiekty

Date: 2026-04-09
Status: Proposed

---

## Context

Serca to waluta platformy. Pytanie: jak je reprezentować w bazie danych?

**Opcja A — Obiekty:** Każde serce = osobny wiersz w tabeli `hearts`.
Transfer = UPDATE heart SET owner_id = new_owner.

**Opcja B — Ledger:** Użytkownik ma `heart_balance: int`. Każda transakcja
= wiersz w `HeartLedger` z delta (+/-). Balance = szybki odczyt z User.

---

## Decision

**Ledger (Opcja B).**

Tabela `HeartLedger` przechowuje każdy ruch serc:
```
from_user_id (nullable = SYSTEM), to_user_id, amount, type, related_exchange_id
```

Pole `heart_balance` na tabeli `User` = denormalizowany cache dla szybkiego odczytu.
Zawsze spójne z ledgerem (update w tej samej transakcji).

DB constraint: `heart_balance >= 0` (CHECK).

---

## Consequences

### Zyskujemy

- **Audit trail:** pełna historia transferów — kto, komu, kiedy, za co
- **Performance:** odczyt balansu = SELECT heart_balance FROM users WHERE id=X (O(1))
- **Atomowość:** jedna DB transaction: UPDATE user (−) + UPDATE user (+) + INSERT ledger
- **Prostota:** brak tabeli z 10 000 wierszy (jeden wiersz per serce), brak fragmentacji
- **Analityka:** łatwe raporty (ile serc krąży, top givers, top receivers)
- **Rekonstrukcja:** balance można zrekonstruować z samego ledgera (fallback)

### Tracimy / ryzykujemy

- Brak "indywidualności" serc — nie możemy śledzić konkretnego serca od A do B do C.
  Akceptowalne: serce to jednostka rozliczeniowa, nie unikalny obiekt.
- `heart_balance` może wyjść z sync z ledgerem jeśli błąd w transakcji.
  Mitygacja: DB transaction + constraint + reconciliation script (narzędzie diagnostyczne).

### Odwracalność

Wysoka — zmiana modelu danych to migracja DB. Ledger jest prostszy niż obiekty,
więc migracja w drugą stronę (objects → ledger) byłaby prostsza gdyby zaszła potrzeba.

---

## Alternatywy odrzucone

**Opcja A — Obiekty (jeden wiersz per serce):**
- Przy 10 000 użytkowników × 5 serc = 50 000 wierszy startowo, rośnie z każdym transferem
- Każdy transfer = UPDATE (nie INSERT) — nadpisujemy historię, brak audit trail
- Złożone queries: "ile serc ma user X?" = COUNT(*) WHERE owner_id=X
- Odrzucone: gorsza wydajność, brak historii, niepotrzebna złożoność
