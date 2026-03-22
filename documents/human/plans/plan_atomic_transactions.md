# Plan: Transakcje atomowe w AgentBus

**Backlog:** #104
**Priorytet:** Low (wzrośnie gdy mrowisko_runner wejdzie do produkcji)
**Data:** 2026-03-22

---

## Problem

`AgentBus` obecnie commituje każdą operację osobno:
- Każda metoda (`add_*`, `update_*`, `send_*`) robi `self._conn.commit()` natychmiast
- Brak mechanizmu transakcyjnego dla złożonych operacji składających się z wielu kroków
- Ryzyko: race conditions, partial writes, niespójny stan przy błędzie w połowie operacji

---

## Use cases (obecne + przyszłe)

### 1. **mrowisko_runner.py** — claim + unclaim + set_instance
```python
# Obecny kod (3 commity):
bus.claim_task(task_id, instance_id)         # COMMIT
try:
    invoke_agent(...)
except:
    bus.unclaim_task(task_id)                # COMMIT
bus.set_instance_idle(instance_id)           # COMMIT
```

**Problem:** Jeśli `unclaim_task` lub `set_instance_idle` failuje, task zostaje claimed ale instance busy — deadlock.

**Potrzeba:** Transakcja dla unclaim + set_instance_idle (rollback obu jeśli coś failuje).

---

### 2. **agent_bus_cli.py cmd_backlog_update** — update status + content
```python
# Obecny kod (2 commity):
if args.status:
    bus.update_backlog_status(id, status)    # COMMIT
if args.content:
    bus.update_backlog_content(id, content)  # COMMIT
```

**Problem:** Jeśli drugi update failuje, pierwszy się udał — backlog w niespójnym stanie.

**Potrzeba:** Transakcja dla obu updates (all-or-nothing).

---

### 3. **Bulk operations** (suggest-bulk, backlog-add-bulk)
```python
# Obecny kod:
for item in items:
    bus.add_suggestion(...)                  # COMMIT per item
```

**Problem:** Failuje w połowie — część itemów w bazie, część nie (partial write).

**Potrzeba:** Transakcja dla całej paczki (all-or-nothing).

---

### 4. **Przyszłość: Suggestion → Backlog**
```python
# Przyszły use case:
backlog_id = bus.add_backlog_item(...)       # COMMIT
bus.update_suggestion_status(sid, status="in_backlog", backlog_id=backlog_id)  # COMMIT
```

**Problem:** Jeśli drugi krok failuje, backlog item istnieje ale suggestion nie ma linku — orphan.

**Potrzeba:** Atomowa migracja suggestion → backlog.

---

## Rozwiązanie: Context manager

### API

```python
# Użycie:
with bus.transaction():
    bus.update_backlog_status(id, "in_progress")
    bus.update_backlog_content(id, new_content)
    # jeśli coś failuje → rollback
    # jeśli wszystko OK → commit na wyjściu z context manager
```

### Implementacja

**Dodać do `AgentBus` (tools/lib/agent_bus.py):**

```python
from contextlib import contextmanager

class AgentBus:
    def __init__(self, db_path: str = "mrowisko.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=3000")
        self._conn.executescript(_SCHEMA_SQL)
        self._run_migrations()
        self._conn.commit()
        self._in_transaction = False  # NEW: flag czy jesteśmy w context manager

    def _auto_commit(self):
        """Commit tylko jeśli NIE jesteśmy w explicit transaction."""
        if not self._in_transaction:
            self._conn.commit()

    @contextmanager
    def transaction(self):
        """Explicit transaction context manager.

        Usage:
            with bus.transaction():
                bus.update_backlog_status(...)
                bus.update_backlog_content(...)
                # commit on exit, rollback on exception
        """
        if self._in_transaction:
            raise RuntimeError("Nested transactions not supported")

        self._in_transaction = True
        try:
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            self._in_transaction = False
```

**Zmienić wszystkie metody modyfikujące:**

Zamienić `self._conn.commit()` → `self._auto_commit()`

```python
def send_message(self, sender: str, ...) -> int:
    cursor = self._conn.execute(...)
    self._auto_commit()  # zamiast self._conn.commit()
    return cursor.lastrowid

def update_backlog_status(self, backlog_id: int, status: str) -> None:
    self._conn.execute(...)
    self._auto_commit()  # zamiast self._conn.commit()
```

---

## Backward compatibility

✓ **TAK** — istniejący kod działa bez zmian:
- Jeśli nie używasz `with bus.transaction():` → każda metoda commituje jak dotychczas
- Jeśli używasz `with bus.transaction():` → commit tylko na końcu, rollback przy exception

---

## Testy

### test_agent_bus.py (nowy plik lub dodać do istniejącego)

```python
def test_transaction_commit():
    """Transaction commits all operations on success."""
    bus = AgentBus(db_path=":memory:")

    with bus.transaction():
        id1 = bus.add_backlog_item(title="Task 1", content="Content 1")
        id2 = bus.add_backlog_item(title="Task 2", content="Content 2")

    items = bus.get_backlog()
    assert len(items) == 2
    assert items[0]["title"] == "Task 2"  # newest first
    assert items[1]["title"] == "Task 1"

def test_transaction_rollback():
    """Transaction rolls back all operations on exception."""
    bus = AgentBus(db_path=":memory:")

    try:
        with bus.transaction():
            bus.add_backlog_item(title="Task 1", content="Content 1")
            raise ValueError("Simulated error")
    except ValueError:
        pass

    items = bus.get_backlog()
    assert len(items) == 0  # rollback — nic nie zostało zapisane

def test_transaction_nested_not_supported():
    """Nested transactions raise RuntimeError."""
    bus = AgentBus(db_path=":memory:")

    with pytest.raises(RuntimeError, match="Nested transactions"):
        with bus.transaction():
            with bus.transaction():
                pass

def test_backward_compat_auto_commit():
    """Without transaction context, operations auto-commit as before."""
    bus = AgentBus(db_path=":memory:")

    id1 = bus.add_backlog_item(title="Task 1", content="Content 1")
    items = bus.get_backlog()
    assert len(items) == 1  # auto-commit zadziałał
```

---

## Wdrożenie use cases

### mrowisko_runner.py
```python
# Przed (unsafe):
try:
    invoke_agent(...)
except:
    bus.unclaim_task(task_id)
bus.set_instance_idle(instance_id)

# Po (safe):
try:
    invoke_agent(...)
except:
    with bus.transaction():
        bus.unclaim_task(task_id)
        bus.set_instance_idle(instance_id)
```

### agent_bus_cli.py cmd_backlog_update
```python
# Przed (unsafe):
if args.status:
    bus.update_backlog_status(args.id, args.status)
if args.content_file or args.content:
    bus.update_backlog_content(args.id, _read_content(args))

# Po (safe):
with bus.transaction():
    if args.status:
        bus.update_backlog_status(args.id, args.status)
    if args.content_file or args.content:
        bus.update_backlog_content(args.id, _read_content(args))
```

### Bulk operations (opcjonalne)
```python
# Przed (partial writes):
def cmd_suggest_bulk(args, bus):
    for block in blocks:
        bus.add_suggestion(...)  # commit per item

# Po (all-or-nothing):
def cmd_suggest_bulk(args, bus):
    with bus.transaction():
        for block in blocks:
            bus.add_suggestion(...)  # commit tylko na końcu
```

**Trade-off bulk:**
- ✓ Atomowość (all-or-nothing)
- ✗ Jeśli 1 z 100 itemów ma błąd → rollback wszystkich (może być niepożądane)

**Rekomendacja:** Opcjonalnie — user decision czy bulk ma być atomowy.

---

## Effort estimate

- **AgentBus changes:** ~20 linii (context manager + _auto_commit + flag)
- **Testy:** ~50 linii (4 test cases)
- **Wdrożenie use cases:** ~10 linii (wrap w `with bus.transaction()`)
- **Total:** ~80 linii, ~1-2h pracy

---

## Pytania do user

1. **Czy bulk operations mają być atomowe (all-or-nothing)?**
   - Opcja A: Tak — wrap w transaction → failuje 1 item = rollback wszystkich
   - Opcja B: Nie — jak dotychczas → failuje 1 item = partial write (część itemów w bazie)

2. **Czy wdrożyć use cases od razu czy tylko zbudować mechanism?**
   - Opcja A: Tylko mechanism + testy → use cases wdrożone gdy mrowisko_runner wejdzie do produkcji
   - Opcja B: Mechanism + testy + wdrożenie use cases od razu (mrowisko_runner, cmd_backlog_update)

3. **Czy nested transactions są potrzebne?**
   - Obecnie: RuntimeError jeśli ktoś próbuje zagnieździć
   - Alternatywa: SQLite SAVEPOINT (kompleksowe, większy effort)

---

## Rekomendacja

1. **Bulk operations:** Opcja A (atomowe) — spójniejsze zachowanie, user widzi sukces/fail całej paczki
2. **Wdrożenie use cases:** Opcja B (od razu) — małe ryzyko, duża wartość (eliminuje edge case bugs)
3. **Nested transactions:** Opcja A (RuntimeError) — YAGNI, można dodać później jeśli potrzeba

---

## Exit criteria

- [ ] Context manager zaimplementowany w AgentBus
- [ ] Wszystkie metody używają `_auto_commit()` zamiast `_conn.commit()`
- [ ] 4 testy przechodzą (commit, rollback, nested error, backward compat)
- [ ] Use cases wdrożone (mrowisko_runner, cmd_backlog_update, bulk?)
- [ ] Commit + push

---

Ścieżka: `tmp/plan_atomic_transactions.md`
