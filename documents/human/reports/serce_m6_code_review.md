# Serce M6 — Code Review: Hearts (gift + balance + ledger)

**Commit:** ebbd072
**Reviewer:** Architect
**Handoff:** #122 od Developer

---

## Verdict: PASS

Kod zgodny z planem, konwencjami projektu i wzorcami z M4/M5.
Brak issues Critical lub Warning. Trzy obserwacje informacyjne (I0).

---

## Pliki przejrzane (8)

| Plik | Linie | Opis |
|---|---|---|
| `app/services/hearts_service.py` | 110 | Core logic: gift_hearts, get_balance, get_ledger |
| `app/api/v1/hearts.py` | 69 | Router: 3 endpointy |
| `app/schemas/hearts.py` | 37 | Request/response modele |
| `app/db/models/heart.py` | 41 | HeartLedger model + CHECK + partial unique index |
| `app/api/v1/router.py` | 17 | Rejestracja hearts_router |
| `tests/test_hearts_service.py` | 264 | 18 unit tests |
| `tests/test_hearts_api.py` | 62 | 6 auth guard tests |
| `tests/test_hearts_concurrency.py` | 167 | 3 concurrency tests (Postgres-only) |
| `tests/integration/api/test_hearts_flow.py` | 143 | 5 integration tests |

---

## Ocena per komponent

### 1. hearts_service.py — L3 Senior ✓

**Concurrency safety (kluczowy wymóg planu):**
- SELECT FOR UPDATE z sorted lock order (`sorted([from_user_id, to_user_id])`) — poprawna ochrona przed deadlockami
- Oba salda aktualizowane atomowo w jednej transakcji
- DB CHECK constraint `amount > 0` jako safety net

**Guards (6/6 wymaganych):**
- CANNOT_GIFT_SELF (422)
- SENDER_NOT_FOUND (404)
- RECIPIENT_NOT_FOUND (404)
- RECIPIENT_NOT_ACTIVE (422)
- INSUFFICIENT_BALANCE (422)
- RECIPIENT_CAP_EXCEEDED (422) — używa `settings.heart_balance_cap`

**Konwencje:**
- flush-only (endpoint commituje) ✓
- HTTPException z kodowymi detail ✓

### 2. hearts.py (router) — L3 Senior ✓

- POST /gift: status 201, rate limit 30/hour, `db.commit()` po service call ✓
- GET /balance: zwraca balance + cap z settings ✓
- GET /ledger: paginacja (offset/limit), opcjonalny type filter ✓
- Sender status nie sprawdzany w service — poprawnie, bo `get_current_user` (deps.py:46) już to robi ✓

### 3. schemas/hearts.py — L3 Senior ✓

- GiftRequest: `amount: int = Field(gt=0, le=50)`, note max_length=200
- LedgerEntryRead: from_attributes=True, type jako str (enum serializuje się poprawnie)
- LedgerResponse: entries + total + offset + limit — kompletna paginacja

### 4. heart.py (model) — L3 Senior ✓

- HeartLedgerType: 6 typów (INITIAL_GRANT, PAYMENT, GIFT, ADMIN_GRANT, ADMIN_REFUND, ACCOUNT_DELETED) — forward-looking
- CHECK constraint `amount > 0` ✓
- Partial unique index na INITIAL_GRANT (idempotency z M4) ✓
- FK do exchanges.id — model Exchange istnieje, FK valid

### 5. Testy — 32 total, pokrycie kompletne ✓

| Suite | Count | Pokrycie |
|---|---|---|
| test_hearts_service.py | 18 | Happy path (3), guards (6), edge cases (3), balance (2), ledger (4) |
| test_hearts_api.py | 6 | Auth guards na wszystkich 3 endpointach |
| test_hearts_concurrency.py | 3 | Race conditions: negative balance, cap overflow, bidirectional |
| test_hearts_flow.py | 5 | E2E: gift, balance check, ledger, cap, insufficient |

**Testy concurrency** (Postgres-only, `skipif not TEST_DATABASE_URL`):
- `test_concurrent_gifts_no_negative_balance`: 100 gifts × 1 heart, balance=50 → dokładnie 50 succeeds
- `test_concurrent_gifts_to_same_recipient_cap`: 10 senders × 2 hearts, recipient=45 → ≤2 succeeds
- `test_concurrent_gift_and_receive`: bidirectional, conservation law `a + b = 60`

Test fixture w test_hearts_service.py poprawnie dropuje partial unique index (`DROP INDEX IF EXISTS uix_heart_ledger_initial_grant`) — SQLite nie obsługuje `postgresql_where`.

---

## Obserwacje informacyjne (I0)

### I0-1: GiftRequest.amount le=50 hardcoded

`schemas/hearts.py:12` — `le=50` zamiast referencji do `settings.heart_balance_cap`.
Pydantic Field nie pozwala na łatwe użycie runtime settings w walidatorze.
Akceptowalne — jeśli cap się zmieni, trzeba pamiętać o aktualizacji schema.

### I0-2: Invalid ledger type filter silently ignored

`hearts.py:62-64` — `except ValueError: pass` przy nieprawidłowym typie.
`?type=INVALID` zwraca wszystkie wpisy zamiast 422.
Akceptowalne dla query filtra — nie krytyczne.

### I0-3: Brak sprawdzenia sender.status w service

`hearts_service.py` sprawdza `recipient.status != ACTIVE` ale nie sender.
Poprawne — sender status weryfikowany przez `get_current_user` (deps.py:46).
Duplikacja byłaby zbędna.

---

## Zgodność z planem M6

| Element planu | Status |
|---|---|
| SELECT FOR UPDATE + sorted lock order | ✓ |
| DB CHECK constraint (amount > 0) | ✓ |
| Guards: self-gift, balance, cap, active, not-found | ✓ |
| flush-only convention | ✓ |
| Rate limit POST /gift | ✓ 30/hour |
| Paginacja ledger | ✓ offset/limit |
| Type filter ledger | ✓ |
| Unit testy (happy + guards + edge) | ✓ 18 |
| Concurrency testy | ✓ 3 (Postgres-only) |
| Integration testy | ✓ 5 |

---

## Podsumowanie

M6 to solidna implementacja. Concurrency safety (sorted lock order + SELECT FOR UPDATE)
jest kluczowym elementem i jest poprawnie zaimplementowany. Testy pokrywają zarówno
logikę biznesową, jak i race conditions. Kod spójny z konwencjami M4/M5.

**PASS — bez zastrzeżeń.**
