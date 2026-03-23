# Code Review: M3 Phase 1 - AgentBus Suggestion Adapter

Date: 2026-03-22
Branch: feature/domain-model-adr-001
Commit: edc3dbe

---

## Summary

**Overall assessment:** NEEDS REVISION (Critical Issue)
**Code maturity level:** Mid → Junior

**Rationale:** Adapter pattern implementation jest technicznie poprawna dla backward compatibility API, ale zawiera **krytyczny bug** — nie wspiera transaction() context z AgentBus, łamiąc atomicity operacji. Repository tworzy własne połączenie SQLite zamiast używać współdzielonego self._conn, co powoduje:
- Database locked errors w transaction context
- Brak rollback przy błędach (dane zapisywane mimo exception)
- 2/2 transaction tests FAILED

Kod jest na poziomie mid dla pojedynczych operacji (backward compatibility działa, 10/10 suggestion tests PASS), ale obniżony do junior przez brak transaction support — fundamentalną funkcjonalność istniejącego systemu.

---

## Test Results

**Repository tests:** 38/38 PASS ✓
- SuggestionRepository: 17/17 PASS
- BacklogRepository: 10/10 PASS
- MessageRepository: 9/9 PASS

**AgentBus adapter tests:** 58/66 PASS (88%)
- Suggestion adapters: 10/10 PASS ✓ (backward compatibility works)
- Transaction tests: 0/2 PASS ✗ (CRITICAL)
- State tests: 0/6 PASS (out of scope M3, not migrated yet)

---

## Findings

### Critical Issues (must fix)

#### 1. Transaction support broken
**Location:** tools/lib/agent_bus.py:306, 324, 372

**Problem:**
Adapter tworzy nowe instancje SuggestionRepository z własnym połączeniem SQLite:
```python
def add_suggestion(...):
    repo = SuggestionRepository(db_path=self._db_path)  # ← NOWE połączenie
    saved = repo.save(suggestion)                        # ← commit natychmiast
    return saved.id
```

Repository używa własnego context manager `_connection()` który:
1. Tworzy nowe połączenie (`self._get_connection()`)
2. Commituje natychmiast przy sukcesie (`conn.commit()`)
3. Zamyka połączenie (`conn.close()`)

Jest całkowicie nieświadome AgentBus transaction context (`self._in_transaction`).

**Impact:**
- `test_transaction_multiple_operations` — FAILED z "database is locked" (repo próbuje commitować w trakcie transaction)
- `test_transaction_rollback_mixed_operations` — FAILED, assertion `len(suggestions) == 0` failed (suggestion zapisany mimo rollback)
- Atomicity operations złamana — mixed operations (suggestion + backlog + message) nie mogą być rollbackowane jako całość
- Production risk: partial writes przy błędach

**Fix guidance:**
Repository musi być transaction-aware. Opcje:
1. **Przekazuj connection do repository** (najszybsze):
   ```python
   def add_suggestion(...):
       repo = SuggestionRepository(db_path=self._db_path, conn=self._conn if self._in_transaction else None)
   ```
   Repository checks: jeśli dostał conn — używa go, nie commituje; jeśli nie — tworzy własne i commituje (jak teraz).

2. **Shared connection pool** (elegantsze, wymaga więcej refactoru):
   AgentBus i Repository używają wspólnego connection pool/session manager, który rozumie transaction context.

3. **Adapter layer manages connection** (quick fix):
   Adapter otacza repo.save() w `if self._in_transaction` logic i używa self._conn zamiast tworzyć repo.

**Recommended:** Opcja 1 — minimalna inwazja, backward compatible, jasny kontrakt.

---

### Warnings (should fix)

#### 2. Multiple filter handling — O(N) in-memory
**Location:** tools/lib/agent_bus.py:327-330

**Problem:**
```python
if status and author and type:
    # Multiple filters - use find_all and filter manually (TODO: optimize)
    suggestions = repo.find_all()
    suggestions = [s for s in suggestions if ...]
```

Gdy mamy wszystkie 3 filtry, kod ładuje WSZYSTKIE suggestions i filtruje in-memory (O(N)).
Acknowledged tech debt (TODO komentarz), ale nie skaluje się.

**Fix guidance:**
Dodaj composite query do SuggestionRepository:
```python
def find_by_filters(status=None, author=None, type=None):
    conditions = []
    if status: conditions.append("status = ?")
    if author: conditions.append("author = ?")
    if type: conditions.append("type = ?")
    where = " AND ".join(conditions)
    # ...
```

---

#### 3. Status mapping inline — backward compatibility layer
**Location:** tools/lib/agent_bus.py:380-387

**Problem:**
```python
status_map = {
    "in_backlog": "implemented",  # Old name for implemented
    "open": "open",
    ...
}
normalized_status = status_map.get(status, status)
```

Status mapping dict jest inline w metodzie. Backward compatibility logic powtórzona będzie w Phase 2 (Backlog), Phase 3 (Messages).

**Fix guidance:**
Wyciągnij do shared conversion layer:
```python
# tools/lib/agent_bus_compat.py
def normalize_suggestion_status(old_status: str) -> str:
    """Maps old status names to new domain model."""
    mapping = {"in_backlog": "implemented", ...}
    return mapping.get(old_status, old_status)
```

Reuse w innych adapterach.

---

#### 4. DRY violation — repository creation
**Location:** tools/lib/agent_bus.py:306, 324, 372

**Problem:**
`repo = SuggestionRepository(db_path=self._db_path)` powtarzane 3x w każdej metodzie.

**Fix guidance:**
Property lub helper:
```python
@property
def _suggestion_repo(self):
    return SuggestionRepository(db_path=self._db_path, conn=...)
```

Lub inicjalizuj w `__init__` i reuse (jeśli connection pool).

---

#### 5. Silent failures — no error/log
**Location:** tools/lib/agent_bus.py:375-377

**Problem:**
```python
suggestion = repo.get(suggestion_id)
if not suggestion:
    return  # Silently ignore if not found (backward compatible behavior)
```

Silent failure — gdy suggestion nie istnieje, metoda po prostu zwraca bez error/log.
Backward compatible (stary kod tak robił), ale nie best practice.

**Fix guidance:**
Co najmniej log warning:
```python
if not suggestion:
    logger.warning(f"update_suggestion_status: suggestion {suggestion_id} not found")
    return
```

---

### Suggestions (nice to have)

#### 6. Dict conversion boilerplate
**Location:** tools/lib/agent_bus.py:342-355

**Problem:**
14 linii konwersji Entity → dict w get_suggestions():
```python
for s in suggestions:
    d = {
        "id": s.id,
        "author": s.author,
        ...  # 10 more fields
    }
    result.append(d)
```

Będzie duplikowane w Phase 2 (Backlog), Phase 3 (Messages).

**Fix guidance:**
Helper method w adapterze lub w Entity:
```python
def _suggestion_to_dict(entity: Suggestion) -> dict:
    return {
        "id": entity.id,
        "author": entity.author,
        ...
    }
```

Albo dodaj do Entity:
```python
# core/entities/messaging.py
def to_dict(self) -> dict:
    return {...}
```

---

#### 7. Long functions
**Location:**
- `get_suggestions()` — 48 linii (tools/lib/agent_bus.py:311-357)
- `update_suggestion_status()` — 48 linii (tools/lib/agent_bus.py:359-407)

**Problem:**
Senior level function length: ≤15 linii. Obecne: 48 linii (3x przekroczenie).

**Fix guidance:**
Refaktor get_suggestions():
```python
def get_suggestions(...):
    repo = self._suggestion_repo
    suggestions = self._query_suggestions(repo, status, author, type)
    return [self._suggestion_to_dict(s) for s in suggestions]

def _query_suggestions(repo, status, author, type):
    # Filter logic here (12 linii)

def _suggestion_to_dict(entity):
    # Conversion here (14 linii)
```

Podobnie update_suggestion_status() — wyciągnij status mapping + entity method dispatch do podfunkcji.

---

## Code Maturity Analysis

| Wymiar | Poziom | Uzasadnienie |
|---|---|---|
| **Functions** | Mid | 3 funkcje 34-48 linii — granica mid/senior (senior ≤15). Można zrefaktorować. |
| **Naming** | Senior | Spójne w projekcie, self-documenting (`add_suggestion`, `update_suggestion_status`) |
| **Abstrakcja** | Mid | Lokalne abstrakcje sensowne (adapter pattern OK), ale brak DI/interface dla repo |
| **Error handling** | Mid | Try-catch bez propagacji context, silent failures (`if not suggestion: return`) |
| **Edge cases** | Mid | Backward compatibility obsługuje (status mapping), ale transaction edge case pominięty |
| **Tests** | Senior | 10/10 backward compatibility tests PASS, ale brak transaction coverage w M3 scope |
| **Dependencies** | Senior | Minimalna dependency (tylko SuggestionRepository), sensowny kontrakt |
| **Structure** | Mid | SRP OK (adapter robi jedno), ale tight coupling (brak interface, direct instantiation) |
| **Transaction support** | **Junior** | **KRYTYCZNY BUG — nie wspiera transaction(), fundamentalna funkcjonalność złamana** |

**Overall:** Mid → Junior (obniżone przez critical bug transaction support)

---

## Positive aspects

✓ Backward compatibility API zachowana — CLI działa bez zmian
✓ 10/10 suggestion tests PASS dla pojedynczych operacji
✓ Adapter pattern technicznie poprawny (dict ↔ entity conversion)
✓ Status mapping backward compatible (`in_backlog` → `implemented`)
✓ Entity methods używane gdy możliwe (`implement()`, `reject()`, `defer()`)
✓ Repository layer separation of concerns czytelna

---

## Recommended Actions

**PRZED Phase 2:**

- [x] **[CRITICAL]** Fix transaction support — repository musi używać AgentBus shared connection w transaction context
  - Recommended: Przekazuj `conn` parameter do Repository constructor
  - Test: `test_transaction_multiple_operations` i `test_transaction_rollback_mixed_operations` muszą PASS

**Phase 2 (Backlog adapters):**

- [ ] **[HIGH]** Zastosuj lekcje z Phase 1:
  - Transaction support od początku (connection parameter do BacklogRepository)
  - DRY — wyciągnij status mapping do shared conversion layer
  - DRY — wyciągnij dict conversion do helper
  - Repository creation jako property/helper zamiast inline

**Post-M3 (gdy wszystkie adaptery gotowe):**

- [ ] **[MEDIUM]** Refactor długich funkcji (get_suggestions, update_suggestion_status) — wyciągnij do podfunkcji
- [ ] **[MEDIUM]** Optimize multiple filter handling — composite query w repository
- [ ] **[LOW]** Add logging dla silent failures

---

## Decision: GO/NO-GO Phase 2

**NO-GO** — Phase 2 (Backlog adapters) nie może rozpocząć się przed poprawą transaction support w Phase 1.

**Rationale:**
1. Phase 2 będzie miał **ten sam problem** transaction support (BacklogRepository będzie tworzyć własne połączenie)
2. Test `test_transaction_multiple_operations` sprawdza mixed operations (suggestion + backlog) — oba muszą działać z transaction
3. Fixing Phase 1 + Phase 2 razem po implementacji będzie droższe niż fix Phase 1 teraz i apply pattern w Phase 2
4. Transaction support to nie refactor — to **critical functionality** istniejącego systemu

**Fix Phase 1 transaction support → verify tests PASS → GREEN LIGHT Phase 2.**

---

## Next Steps

1. Developer implementuje fix transaction support (connection parameter do Repository)
2. Verify: `py -m pytest tests/test_agent_bus.py::TestTransactions -v` — wszystkie PASS
3. Commit fix jako M3.1 patch
4. Architect approves → GREEN LIGHT Phase 2

---

## Summary for Developer

**Dobra robota na backward compatibility** — CLI działa bez zmian, adapter pattern technicznie poprawny.

**Ale:** Repository isolation (własne połączenie + context manager) złamał transaction support. To nie edge case — to production risk (partial writes przy błędach).

**Fix:** Repository musi być transaction-aware. Przekaż `conn` parameter i używaj go gdy w transaction context, albo twórz własne gdy standalone. Pattern apply w Phase 2.

**Po fix:** M3 Phase 1 będzie **solid foundation** dla Phase 2-3. ✓
