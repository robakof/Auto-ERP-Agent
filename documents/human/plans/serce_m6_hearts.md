# Developer Plan: Serce M6 — Hearts Ledger + Transfer + Gift + Balance

Data: 2026-04-17
Autor: Architect
Dotyczy: `documents/human/plans/serce_faza1_roadmap.md` §M6
Dla roli: Developer
Status: Ready to start
Prerequisites: M3 (auth) ✓

---

## Cel

Hearts to waluta systemu Serce. Po M6:
1. User może podarować serca innemu userowi (`POST /hearts/gift`)
2. User widzi swój balans (`GET /users/me/hearts/balance`)
3. User widzi historię transakcji (`GET /users/me/ledger` z paginacją i filtrami)
4. Transfer jest atomowy — concurrent writes nie pozwalają zejść poniżej 0
5. System respektuje cap (max serc na koncie)

**Constraint:** Model `HeartLedger` + `HeartLedgerType` + CHECK constraints + partial unique index (INITIAL_GRANT) już istnieją z M1. `INITIAL_GRANT` obsłużony w M4. M6 = service transferowy + endpointy + concurrency safety. Zero nowych migracji Alembic.

**Ryzyko: WYSOKIE.** Hearts to pieniądz systemu. Atomowość transferu i ochrona przed race conditions to fundament. MUST-COVER testami.

---

## Co już istnieje

| Komponent | Lokalizacja | Status |
|---|---|---|
| HeartLedger model (from_user_id, to_user_id, amount, type, note) | `app/db/models/heart.py` | ✓ M1 |
| HeartLedgerType enum (INITIAL_GRANT, PAYMENT, GIFT, ADMIN_GRANT, ADMIN_REFUND, ACCOUNT_DELETED) | `app/db/models/heart.py:11-18` | ✓ M1 |
| CHECK `amount > 0` | `app/db/models/heart.py:33` | ✓ M1 |
| Partial unique index `uix_heart_ledger_initial_grant` | `app/db/models/heart.py:34-38` | ✓ M1 |
| User.heart_balance (default 0, CHECK >= 0) | `app/db/models/user.py:32,56` | ✓ M1 |
| Settings.initial_heart_grant=5, heart_balance_cap=50 | `app/config.py:26-27` | ✓ M1 |
| _grant_initial_hearts (INITIAL_GRANT flow) | `app/services/verification_service.py:222-243` | ✓ M4 |
| AuthContext, get_current_user | `app/core/deps.py` | ✓ M3 |
| Users router (`/users`) | `app/api/v1/users.py` | ✓ M5 |

---

## Scope — co dokładnie powstaje

### 1. Hearts service: `app/services/hearts_service.py` (NOWY)

Core logic — atomowe transfery serc.

```python
async def gift_hearts(
    db: AsyncSession, from_user_id: UUID, to_user_id: UUID, amount: int, note: str | None,
) -> HeartLedger:
    """
    Atomowy transfer serc (GIFT). 
    
    Guards:
    1. from != to (CANNOT_GIFT_SELF)
    2. amount > 0 (walidacja w schema, CHECK w DB)
    3. from_user.heart_balance >= amount (INSUFFICIENT_BALANCE)
    4. to_user.heart_balance + amount <= cap (RECIPIENT_CAP_EXCEEDED)
    5. to_user.status == ACTIVE (RECIPIENT_NOT_ACTIVE)
    
    Atomowość: SELECT FOR UPDATE na obu userach → update balance → INSERT ledger → flush.
    """
```

**Kluczowy pattern — SELECT FOR UPDATE:**

```python
# Lock both users in deterministic order (prevent deadlock)
user_ids = sorted([from_user_id, to_user_id])
users = {}
for uid in user_ids:
    result = await db.execute(
        select(User).where(User.id == uid).with_for_update()
    )
    users[uid] = result.scalar_one_or_none()

sender = users[from_user_id]
recipient = users[to_user_id]

# Validate after locking
if sender.heart_balance < amount:
    raise HTTPException(422, "INSUFFICIENT_BALANCE")

max_receivable = settings.heart_balance_cap - recipient.heart_balance
if amount > max_receivable:
    raise HTTPException(422, "RECIPIENT_CAP_EXCEEDED")

# Atomic update
sender.heart_balance -= amount
recipient.heart_balance += amount

# Ledger entry
ledger = HeartLedger(
    from_user_id=from_user_id,
    to_user_id=to_user_id,
    amount=amount,
    type=HeartLedgerType.GIFT,
    note=note,
)
db.add(ledger)
await db.flush()
```

**Dlaczego SELECT FOR UPDATE:**
- Race condition: 2 concurrent gifts od tego samego usera → oba czytają balance=10, oba odejmują 8 → balance=-6
- `WITH FOR UPDATE` blokuje wiersz do końca transakcji → serializacja
- Sorted order → brak deadlocków (zawsze locki w tej samej kolejności)
- DB CHECK `heart_balance >= 0` to safety net — nie powinno się aktywować przy prawidłowym locking

```python
async def get_balance(db: AsyncSession, user_id: UUID) -> int:
    """Get current heart balance."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "USER_NOT_FOUND")
    return user.heart_balance


async def get_ledger(
    db: AsyncSession, user_id: UUID, *,
    type_filter: HeartLedgerType | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[HeartLedger], int]:
    """Get paginated ledger entries for user. Returns (entries, total_count)."""
    base_q = select(HeartLedger).where(
        (HeartLedger.from_user_id == user_id) | (HeartLedger.to_user_id == user_id)
    )
    if type_filter:
        base_q = base_q.where(HeartLedger.type == type_filter)
    
    # Count
    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    
    # Fetch page
    entries_q = base_q.order_by(HeartLedger.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()
    
    return list(entries), total
```

### 2. Schemas: `app/schemas/hearts.py` (NOWY)

```python
class GiftRequest(BaseModel):
    to_user_id: UUID
    amount: int = Field(gt=0, le=50)  # le=cap
    note: str | None = Field(None, max_length=200)

class BalanceResponse(BaseModel):
    heart_balance: int
    heart_balance_cap: int

class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    from_user_id: UUID | None
    to_user_id: UUID | None
    amount: int
    type: str
    note: str | None
    created_at: datetime

class LedgerResponse(BaseModel):
    entries: list[LedgerEntryRead]
    total: int
    offset: int
    limit: int
```

### 3. Endpointy: `app/api/v1/hearts.py` (NOWY router)

```python
router = APIRouter(prefix="/hearts", tags=["hearts"])

@router.post("/gift", response_model=LedgerEntryRead, status_code=201)
@limiter.limit("30/hour")   # anti-spam
async def gift_hearts(req, current_user, db):
    ...

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(current_user, db):
    ...

@router.get("/ledger", response_model=LedgerResponse)
async def get_ledger(current_user, db, type: str | None = None, offset: int = 0, limit: int = 20):
    ...
```

### 4. Router registration: `app/api/v1/router.py` (EDYCJA)

```python
from app.api.v1.hearts import router as hearts_router
v1_router.include_router(hearts_router)
```

---

## Decyzje zatwierdzone

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| Concurrency control | SELECT FOR UPDATE (row-level lock) | Serializacja transferów — jedyna bezpieczna opcja |
| Deadlock prevention | Sorted user_ids lock order | Deterministic order = no deadlock |
| Cap validation | Aplikacyjna + DB CHECK | Aplikacyjna → graceful error, DB CHECK → safety net |
| GIFT max amount | le=cap (50) w schema | Nie można podarować więcej niż cap |
| PAYMENT type | Zastrzeżony — NIE używać w M6 | PAYMENT = Exchange completion (M9) |
| ADMIN_GRANT/REFUND | NIE w M6 | Admin endpoints = M15 |
| Osobny hearts router | `/hearts` | SRP — nie mieszać z `/users` |
| Ledger paginacja | offset+limit (default 20) | Proste, wystarczające na MVP |
| Ledger filter | type (optional) | Filtr po typie transakcji |
| Transaction convention | Service flush, endpoint commit | Zgodne z M4/M5 |
| Alembic migrations | Zero | Model z M1 |

---

## Testy

### Unit: `tests/test_hearts_service.py` (NOWY) — MUST-COVER

```
# Gift happy path
test_gift_hearts_valid()
test_gift_hearts_updates_both_balances()
test_gift_hearts_creates_ledger_entry()

# Gift guards
test_gift_self_rejected()
test_gift_insufficient_balance()
test_gift_recipient_cap_exceeded()
test_gift_recipient_not_active()
test_gift_amount_zero_rejected()      # Schema level, ale też service guard
test_gift_sender_not_found()
test_gift_recipient_not_found()

# Gift edge cases
test_gift_exact_balance_succeeds()     # balance=5, gift=5 → balance=0
test_gift_cap_exact_succeeds()         # recipient at 49, gift 1 → 50 (cap)
test_gift_cap_over_rejected()          # recipient at 49, gift 2 → rejected

# Balance
test_get_balance()
test_get_balance_user_not_found()

# Ledger
test_get_ledger_empty()
test_get_ledger_with_entries()
test_get_ledger_pagination()
test_get_ledger_type_filter()
test_get_ledger_includes_sent_and_received()
```
Minimum: **≥18 unit**

### Unit: `tests/test_hearts_api.py` (NOWY)

```
test_gift_no_token()
test_gift_missing_to_user_id()
test_gift_invalid_amount_zero()
test_gift_invalid_amount_negative()
test_balance_no_token()
test_ledger_no_token()
```
Minimum: **≥6 unit**

### Concurrency: `tests/test_hearts_concurrency.py` (NOWY) — MUST-COVER

```
test_concurrent_gifts_no_negative_balance()
    """100 concurrent gifts of 1 heart from user with balance=50.
    All 50 should succeed, rest should fail. Final balance = 0, never < 0."""

test_concurrent_gifts_to_same_recipient_cap()
    """Multiple senders gift to same recipient near cap. No one exceeds cap."""

test_concurrent_gift_and_receive()
    """User sends and receives concurrently. Balance stays consistent."""
```
Minimum: **≥3 concurrency** (require Postgres — asyncpg + real transactions)

### Integration: `tests/integration/api/test_hearts_flow.py` (NOWY)

```
test_gift_e2e()
test_gift_and_check_balance()
test_gift_and_check_ledger()
test_gift_cap_exceeded_e2e()
test_gift_insufficient_balance_e2e()
```
Minimum: **≥5 integration**

### Minimum testów

- Hearts service: ≥18
- Hearts API: ≥6
- Concurrency: ≥3
- Integration: ≥5
- **Total nowych: ≥32**
- **Suite total: ≥150** (118 z M1-M5 + 32 nowych)

---

## Out of scope (świadomie)

- **PAYMENT transfer** — M9 (Exchange completion)
- **ADMIN_GRANT / ADMIN_REFUND** — M15 (Admin endpoints)
- **ACCOUNT_DELETED** — M16 (Soft delete)
- **Hearts purchase (real money)** — Faza 2
- **Transfer history between specific users** — nice-to-have, nie w MVP

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| Race condition → negative balance | SELECT FOR UPDATE + DB CHECK >= 0 |
| Deadlock (cross-transfer A→B, B→A) | Sorted lock order (mniejszy UUID pierwszy) |
| Cap exceeded w concurrent scenario | Validate after lock, before update |
| Slow SELECT FOR UPDATE pod load | Akceptowalne na MVP scale; sharding/optimistic locking w przyszłości |
| SQLite w unit testach nie ma FOR UPDATE | Concurrency testy require Postgres (asyncpg). Unit testy = logika bez concurrency |

---

## Uwagi do concurrency testów

SQLite nie wspiera `SELECT FOR UPDATE` — testy concurrency MUSZĄ biegać na Postgres.

Pattern:
```python
@pytest.mark.asyncio
async def test_concurrent_gifts_no_negative_balance(pg_session_factory):
    """Requires TEST_DATABASE_URL with real Postgres."""
    # Setup: user with balance=50
    # Launch 100 asyncio.tasks, each gifting 1 heart
    # Assert: exactly 50 succeed, 50 fail
    # Assert: final balance == 0
```

Oznacz `@pytest.mark.postgres` lub skip gdy `TEST_DATABASE_URL` niedostępny.

---

## Kolejność pracy (rekomendacja)

1. **Schemas** `hearts.py` (GiftRequest, BalanceResponse, LedgerEntryRead, LedgerResponse)
2. **hearts_service.py** (gift_hearts z SELECT FOR UPDATE, get_balance, get_ledger) + unit testy
3. **hearts.py** router (3 endpointy) + rejestracja w router.py + API testy
4. **Concurrency testy** (require Postgres)
5. **Integration testy** (full flows z mock)
6. Verify: `py -m pytest tests/ -q --ignore=tests/integration` → ≥150 PASS

---

## Workflow i handoff

Developer realizuje przez `workflow_developer_tool`.

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "serce_m6_review" --status PASS \
  --summary "M6: hearts service + gift + balance + ledger. 150+ tests PASS. Concurrency tested on Postgres." \
  --next-action "Code review — hearts_service atomicity, SELECT FOR UPDATE, cap validation, concurrency tests"
```
