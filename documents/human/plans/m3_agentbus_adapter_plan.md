# Plan M3: AgentBus Adapter

**Goal:** Backward compatibility z CLI — agent_bus_cli.py działa bez zmian.

**Approach:** Stopniowa migracja — stary kod deleguje do repositories.

---

## Strategia

**Adapter pattern:**
- `tools/lib/agent_bus.py` (stary kod proceduralny) → adaptery → `core/repositories/` (nowy kod OOP)
- Zachowujemy backward compatibility: CLI nie wymaga zmian
- Dict-based API (dla CLI) → Domain Model (wewnętrznie)

**Nie robimy:**
- ❌ Big bang rewrite
- ❌ Breaking changes w CLI
- ❌ Usuwanie starego kodu (dopiero po M3 complete + migracji agentów)

---

## Metody do adaptacji (priority order)

### Phase 1: Suggestions (proof of concept)
1. **add_suggestion()** → `SuggestionRepository.save()`
   - Input: dict z parametrami
   - Convert: dict → Suggestion entity
   - Save: przez repository
   - Return: suggestion_id (backward compatible)

2. **get_suggestions()** → `SuggestionRepository.find_by_*()` + `find_all()`
   - Input: filters (author, status, type, limit)
   - Query: przez repository
   - Convert: Suggestion entity → dict
   - Return: list[dict] (backward compatible)

3. **update_suggestion_status()** → `SuggestionRepository.get()` + `save()`
   - Load entity
   - Update status (przez metody encji: implement(), reject(), defer())
   - Save
   - Backward compatible

### Phase 1.1: CRITICAL FIX (before Phase 2)
**Status:** Required before Phase 2 can start

**Issue:** Transaction support broken (identified in code review commit edc3dbe)
- Repository creates own connection instead of using AgentBus shared connection
- Tests: test_transaction_multiple_operations FAILED ("database is locked")
- Production risk: partial writes, atomicity broken

**Fix:**
1. Add `conn` parameter to SuggestionRepository.__init__()
2. Repository uses external conn when in transaction context
3. Repository commits only when using own connection (not external)
4. Update all 3 adapter methods (add_suggestion, get_suggestions, update_suggestion_status)

**Verify:**
```bash
py -m pytest tests/test_agent_bus.py::TestTransactions -v
# All PASS required
```

**Code review report:** documents/human/reports/code_review_m3_phase1_adapter_pattern.md

---

### Phase 2: Backlog
4. **add_backlog_item()** → `BacklogRepository.save()`
5. **get_backlog()** → `BacklogRepository.find_by_*()` + `find_all()`
6. **update_backlog_status()** → `BacklogRepository.get()` + `save()`
7. **update_backlog_content()** → `BacklogRepository.get()` + `save()`

**Apply lessons from Phase 1:**
- ✓ Transaction support (conn parameter) from day 1
- ✓ Test transaction_multiple_operations as checkpoint
- ✓ Status mapping to shared conversion layer (DRY)
- ✓ Dict conversion helpers (reduce boilerplate)

### Phase 3: Messages
8. **send_message()** → `MessageRepository.save()`
9. **get_inbox()** → `MessageRepository.find_by_recipient()` + filter
10. **mark_read()** → `MessageRepository.get()` + `mark_read()` + `save()`
11. **get_messages()** → `MessageRepository.find_by_*()` + filters

### Phase 4: Others (out of scope M3)
- session_log, trace, sessions, instances (później)

---

## Implementation pattern

**Example: add_suggestion() with transaction support**

```python
# OLD (procedural)
def add_suggestion(self, author, content, title="", type="observation", ...):
    cursor = self._conn.execute(
        "INSERT INTO suggestions (...) VALUES (...)",
        (author, content, title, type, ...)
    )
    return cursor.lastrowid

# NEW (adapter → repository with transaction support)
def add_suggestion(self, author, content, title="", type="observation", ...):
    from core.repositories.suggestion_repo import SuggestionRepository
    from core.entities.messaging import Suggestion, SuggestionType

    # Convert dict → entity
    suggestion = Suggestion(
        author=author,
        content=content,
        title=title,
        type=SuggestionType(type) if type else SuggestionType.OBSERVATION
    )

    # Save via repository (CRITICAL: pass connection for transaction support)
    conn = self._conn if self._in_transaction else None
    repo = SuggestionRepository(db_path=self.db_path, conn=conn)
    saved = repo.save(suggestion)

    # Return ID (backward compatible)
    return saved.id
```

**Repository transaction support:**

```python
# core/repositories/suggestion_repo.py
class SuggestionRepository(Repository[Suggestion]):
    def __init__(self, db_path: str, conn: Optional[sqlite3.Connection] = None):
        self._db_path = db_path
        self._external_conn = conn  # Shared connection from AgentBus transaction

    def _get_connection(self):
        if self._external_conn:
            return self._external_conn  # Use shared connection
        else:
            return sqlite3.connect(self._db_path)  # Create own connection

    @contextmanager
    def _connection(self):
        conn = self._get_connection()
        should_commit = (self._external_conn is None)  # Only commit if own connection
        try:
            yield conn
            if should_commit:
                conn.commit()
        except Exception:
            if should_commit:
                conn.rollback()
            raise
        finally:
            if should_commit:
                conn.close()
```

**Key points:**
1. API nie zmienia się (parametry, return type)
2. Wewnętrznie używamy repositories
3. Dict ↔ Entity conversion w adapterze
4. **CRITICAL:** Repository dostaje `conn` parameter dla transaction support
5. Repository commituje tylko gdy używa własnego połączenia (nie external conn)

---

## Testing strategy

**Backward compatibility:**
- Istniejące testy `test_agent_bus.py` muszą pass
- CLI działa bez zmian
- Integration test: stary CLI → adapter → repository → DB

**New tests:**
- Adapter conversion (dict → entity → dict)
- Error handling (ValidationError → user-friendly message)

---

## Success criteria M3 Phase 1 (Suggestions)

**Implementation:**
✓ add_suggestion() + get_suggestions() + update_suggestion_status() używają repositories
✓ Repository transaction-aware (conn parameter)
✓ Backward compatibility: agent_bus_cli.py działa bez zmian

**Tests (EXPLICITE - all must PASS):**
✓ Repository tests: tests/core/test_repositories.py (Suggestion tests: 17/17 PASS)
✓ Adapter backward compatibility: tests/test_agent_bus.py::TestSuggestions (10/10 PASS)
✓ **Transaction support:** tests/test_agent_bus.py::TestTransactions (2/2 PASS) ← **CRITICAL CHECKPOINT**

**Documentation:**
✓ Plan Phase 2 (Backlog) gotowy

**Lessons learned Phase 1:**
- Transaction support był pominięty w pierwszej implementacji (code review wyłapał)
- Success criteria muszą explicite wymieniać które testy (nie tylko "testy pass")
- Transaction tests są CRITICAL dla adapter pattern — muszą być checkpoint przed Phase 2

---

## Success criteria M3 Phase 2 (Backlog)

**Implementation:**
- add_backlog_item() + get_backlog() + update_backlog_status/content() używają repositories
- Repository transaction-aware (conn parameter) **od początku** (lesson z Phase 1)
- Backward compatibility: agent_bus_cli.py działa bez zmian
- Status mapping w shared conversion layer (DRY, lesson z Phase 1)

**Tests (EXPLICITE - all must PASS):**
- Repository tests: tests/core/test_repositories.py (Backlog tests: 10/10 PASS)
- Adapter backward compatibility: tests/test_agent_bus.py::TestBacklog (wszystkie PASS)
- **Transaction support:** tests/test_agent_bus.py::TestTransactions::test_transaction_multiple_operations (PASS) ← **CRITICAL CHECKPOINT**
  - Test sprawdza mixed operations (suggestion + backlog + message) — atomicity
  - Musi PASS przed zakończeniem Phase 2

**Documentation:**
- Plan Phase 3 (Messages) gotowy

**Out of scope M3:**
- Messages (Phase 3)
- session_log, trace (Phase 4)
- Deprecation starego kodu
- Migracja agentów na repositories

---

## Phase 1 Retrospective (2026-03-22)

### What went well ✓
- Backward compatibility API zachowana (CLI działa bez zmian)
- 10/10 suggestion adapter tests PASS
- Repository tests 17/17 PASS
- Adapter pattern technicznie poprawny (dict ↔ entity conversion clean)
- Entity methods używane (implement(), reject(), defer())
- Code review wyłapał critical bug przed Phase 2

### What went wrong ✗
- **Transaction support pominięty** w pierwszej implementacji
  - Repository tworzy własne połączenie zamiast używać shared AgentBus conn
  - 0/2 transaction tests PASS
  - Production risk: partial writes, atomicity broken
  - **Root cause:** Success criteria nie wymieniały explicite transaction tests

### Lessons learned

**1. Success criteria muszą być explicite:**
- ❌ Bad: "Testy agent_bus pass" (ambiguous)
- ✓ Good: "tests/test_agent_bus.py::TestSuggestions (10/10 PASS) + ::TestTransactions (2/2 PASS)"

**2. Transaction support to CRITICAL requirement dla adapter pattern:**
- Nie można migrować proceduralnego kodu (shared connection) na Repository bez transaction awareness
- Transaction tests muszą być checkpoint przed zakończeniem fazy

**3. Code review wyłapuje bugs — ale lepiej wyłapać przed implementacją:**
- Gdyby success criteria miały explicite transaction tests → Developer by je uruchomił przed kodem review
- Code review jako safety net działa, ale kosztuje (rework)

**4. Apply patterns konsekwentnie:**
- Phase 2 musi mieć transaction support od początku (nie jako fix po code review)
- DRY principles z Phase 1 (status mapping, dict conversion) należy zastosować w Phase 2

### Recommendations for Phase 2

**Before implementation:**
1. Fix Phase 1 transaction support (Phase 1.1 patch)
2. Verify all transaction tests PASS
3. Review Phase 2 success criteria — explicite test list

**During implementation:**
1. Transaction support (conn parameter) od pierwszego commita
2. Test checkpoint: run TestTransactions po każdej metodzie (add, get, update)
3. DRY helpers dla status mapping i dict conversion

**After implementation:**
1. Code review przed Phase 3 (nie czekać do końca M3)
2. Verify lessons applied (transaction support, DRY, test coverage)

---

## Next after M3

**M3.1 (PATCH):** Fix Phase 1 transaction support (BEFORE Phase 2)
**M3.2 (Phase 2):** Backlog adapters (apply lessons learned)
**M3.3 (Phase 3):** Message adapters
**M4:** Cleanup + optimization (DRY refactors, composite queries)
**M5:** Migracja agentów (używają repositories zamiast agent_bus)
**M6:** Deprecation + cleanup starego kodu
