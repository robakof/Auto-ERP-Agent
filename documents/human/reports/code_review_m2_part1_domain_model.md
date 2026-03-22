# Code Review: Domain Model M2 Part 1

**Date:** 2026-03-22
**Branch:** `feature/domain-model-adr-001`
**Commit:** `c8d0d4f` — feat(core): M2 part 1 - Repository base + SuggestionRepository (17/17 tests pass)
**Reviewer:** Architect
**Developer:** Developer

---

## Summary

**Overall assessment:** PASS ✓
Proceed to M2 part 2 (BacklogRepository, MessageRepository).

**Code maturity level:** **Mid** — Kod działa poprawnie, testy pass, architektura zgodna z ADR-001. Brakuje senior-level polish w niektórych obszarach (DRY w queries, error handling, separation of concerns). To akceptowalne dla pierwszej iteracji — możesz kontynuować M2 part 2. Zanotowane improvements można zaadresować w osobnej iteracji refactoringu po M3.

**Uzasadnienie:**
- Funkcje: 10-28 linii, większość dobrze podzielona ✓
- Naming: Spójne, self-documenting ✓
- Abstrakcja: Copy-paste w find_by_* queries (Mid), brak helper method
- Error handling: Brak obsługi SQLite exceptions (Junior-Mid)
- Edge cases: Nullable fields OK, brakuje enum validation (Mid)
- Tests: 17 testów pass, pokrycie happy+edge ✓ (Senior)
- Dependencies: SQLite built-in, minimalne ✓ (Senior)
- Structure: SRP, clean separation entity/repository ✓ (Senior)

---

## Findings

### Warnings (should fix — ale nie blokują M2 part 2)

#### 1. Copy-paste pattern w find_by_* queries
**Location:** `core/repositories/suggestion_repo.py:237-307`

**Problem:**
Trzy metody (`find_by_status`, `find_by_author`, `find_by_type`) mają prawie identyczną strukturę:
```python
def find_by_X(self, value):
    conn = self._get_connection()
    try:
        cursor = conn.execute("SELECT ... WHERE X = ? ORDER BY ...", (value,))
        return [self._row_to_entity(row) for row in cursor.fetchall()]
    finally:
        conn.close()
```

~70 linii kodu z 90% duplikacji. To jest **Mid-level code** — działa, ale nie skaluje się (każda nowa query = copy-paste 15 linii).

**Fix guidance:**
Wyciągnij generic helper:
```python
def _find_by(self, field: str, value: Any) -> List[Suggestion]:
    """Generic query method dla prostych WHERE field = value."""
    conn = self._get_connection()
    try:
        cursor = conn.execute(
            f"""SELECT id, author, recipients, title, content, type, status, backlog_id,
                       session_id, created_at
                FROM suggestions
                WHERE {field} = ?
                ORDER BY created_at DESC, id DESC""",
            (value,)
        )
        return [self._row_to_entity(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def find_by_status(self, status: SuggestionStatus) -> List[Suggestion]:
    return self._find_by("status", status.value)

def find_by_author(self, author: str) -> List[Suggestion]:
    return self._find_by("author", author)

def find_by_type(self, type: SuggestionType) -> List[Suggestion]:
    return self._find_by("type", type.value)
```

Redukcja z ~70 linii do ~30 linii. Gdy dodasz BacklogRepository/MessageRepository ten pattern będzie się powtarzał — lepiej naprawić teraz.

**When to fix:** Refactor iteration po M3 (nie teraz — żeby nie blokować momentum).

---

#### 2. Brak error handling dla SQLite exceptions
**Location:** `core/repositories/suggestion_repo.py` — wszystkie metody z conn.execute()

**Problem:**
Metody nie łapią wyjątków SQLite (IntegrityError, OperationalError, DatabaseError). Gdy wystąpi:
- DB file locked (concurrent access)
- Disk full
- Foreign key violation (w przyszłości)

Repository crashuje z raw SQLite exception zamiast domenowego błędu (ValidationError, PersistenceError).

**Example failure scenario:**
```python
# Terminal 1: repo1 pisze do mrowisko.db
# Terminal 2: repo2 próbuje pisać do mrowisko.db w tym samym czasie
# → sqlite3.OperationalError: database is locked
```

User dostaje stack trace SQLite zamiast czytelnego komunikatu domenowego.

**Fix guidance:**
Wrap każde `conn.execute()` w try-except:
```python
try:
    cursor = conn.execute("INSERT INTO ...", (...))
except sqlite3.IntegrityError as e:
    raise ValidationError(f"Integrity constraint violation: {e}")
except sqlite3.OperationalError as e:
    raise PersistenceError(f"Database operation failed: {e}")
```

Albo wrap na poziomie `_get_connection()` context manager (bardziej DRY).

**Priority:** Medium — system działa single-threaded obecnie (jedna sesja agenta naraz), więc ten problem nie występuje w praktyce. Ale przy multi-agent (Horyzont 2-3) stanie się critical.

**When to fix:** Przed wdrożeniem multi-agent / concurrent sessions.

---

#### 3. Auto-generate title mutuje encję (separation of concerns)
**Location:** `core/repositories/suggestion_repo.py:162-164`

```python
if not entity.title:
    entity.title = entity.content[:80].split("\n")[0]
```

**Problem:**
Repository **mutuje** encję jako side effect save(). To naruszenie separation of concerns:
- Repository powinna tylko zapisywać dane, nie zmieniać encji
- Co jeśli user chce zachować pusty title? (teraz nie może — zawsze auto-generated)
- Logika należy do encji (Suggestion.__init__ lub validate()), nie do infrastructure layer

**Example problem:**
```python
suggestion = Suggestion(author="dev", content="Test", title="")
repo.save(suggestion)
print(suggestion.title)  # "Test" — MUTATED by repository!
```

To jest **leaky abstraction** — infrastructure layer (repo) wpływa na domain layer (entity).

**Fix guidance:**
Przenieś logikę do encji:
```python
# core/entities/messaging.py — Suggestion.__init__
def __init__(self, author, content, title="", ...):
    if not title and content:
        title = content[:80].split("\n")[0]
    self.title = title
    # ...
```

Repository tylko:
```python
if not entity.title:
    raise ValidationError("Suggestion must have a title")
```

Albo zmień kontrakt: title jest optional, ale agent_bus_cli.py generuje go przed utworzeniem Suggestion.

**Priority:** Low — obecne zachowanie działa i jest backward compatible z agent_bus.py. Ale przy refaktorze warto poprawić.

**When to fix:** Refactor iteration po M3.

---

#### 4. Brak enum validation przy deserializacji
**Location:** `core/repositories/suggestion_repo.py:90`

```python
def _row_to_entity(self, row: sqlite3.Row) -> Suggestion:
    return Suggestion(
        # ...
        type=SuggestionType(row["type"]),  # ← ValueError jeśli nieprawidłowa wartość w DB
        status=SuggestionStatus(row["status"]),
        # ...
    )
```

**Problem:**
Jeśli w bazie jest nieprawidłowa wartość (np. `type="invalid_type"`), konstruktor enuma rzuci `ValueError`:
```
ValueError: 'invalid_type' is not a valid SuggestionType
```

To może wystąpić gdy:
- User ręcznie edytuje DB (dla testów/debug)
- Migracja zmienia wartości enumów
- Stara baza z nieaktualnymi wartościami

**Fix guidance:**
```python
try:
    type_enum = SuggestionType(row["type"])
    status_enum = SuggestionStatus(row["status"])
except ValueError as e:
    raise ValidationError(f"Invalid enum value in database: {e}")

return Suggestion(
    type=type_enum,
    status=status_enum,
    # ...
)
```

**Priority:** Low — w praktyce nie powinno wystąpić (agent_bus pisze poprawne wartości). Ale defensive programming.

**When to fix:** Refactor iteration po M3.

---

### Suggestions (nice to have)

#### 1. Repository.exists(id: int) -> bool missing
**Location:** `core/repositories/base.py`

**Observation:**
Interfejs Repository[T] ma get/save/delete/find_all, ale brak `exists(id) -> bool`.

Często używany pattern:
```python
if repo.exists(42):
    # ...
```

Łatwiejszy do implementacji niż get() (nie trzeba deserializować całej encji):
```python
def exists(self, id: int) -> bool:
    conn = self._get_connection()
    try:
        cursor = conn.execute("SELECT 1 FROM suggestions WHERE id = ? LIMIT 1", (id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()
```

**Recommendation:** Dodaj do Repository[T] interface w osobnej iteracji (breaking change dla implementacji).

---

#### 2. Context manager dla connection management
**Location:** `core/repositories/suggestion_repo.py` — wszystkie metody

**Observation:**
Każda metoda ma boilerplate:
```python
conn = self._get_connection()
try:
    # ...
finally:
    conn.close()
```

16 linii boilerplate w każdej metodzie × 10 metod = 160 linii.

**Alternative:**
```python
from contextlib import contextmanager

@contextmanager
def _connection(self):
    conn = self._get_connection()
    try:
        yield conn
        conn.commit()  # Auto-commit on success
    except Exception:
        conn.rollback()  # Auto-rollback on error
        raise
    finally:
        conn.close()

def get(self, id: int) -> Optional[Suggestion]:
    with self._connection() as conn:
        cursor = conn.execute("SELECT ... WHERE id = ?", (id,))
        row = cursor.fetchone()
        return self._row_to_entity(row) if row else None
```

Redukcja boilerplate + automatic transaction handling.

**Recommendation:** Consider dla BacklogRepository/MessageRepository w M2 part 2 (proof of concept).

---

#### 3. Paginated queries zamiast find_all()
**Location:** `core/repositories/base.py:87` — find_all() docstring warning

**Observation:**
find_all() docstring mówi "może zwrócić tysiące rekordów — używaj ostrożnie", ale brak alternatywy.

Przy 42 otwartych suggestions obecnie OK, ale gdy będzie 500+ stanie się problemem (memory, performance).

**Alternative:**
```python
def find_paginated(self, limit: int = 50, offset: int = 0) -> List[T]:
    """Pobiera encje z paginacją (LIMIT/OFFSET)."""
    pass
```

Albo cursor-based pagination (bardziej skalowalne):
```python
def find_after(self, after_id: int, limit: int = 50) -> List[T]:
    """Pobiera następne N encji po after_id."""
    pass
```

**Recommendation:** Not urgent — ale warto rozważyć przy refaktorze queries (wraz z fix #1 copy-paste).

---

## Test Coverage Analysis

**17 testów, wszystkie PASS (0.79s)** ✓

**Pokrycie:**
- ✓ save (INSERT/UPDATE)
- ✓ get (existing/nonexistent)
- ✓ delete (existing/nonexistent)
- ✓ find_all (empty/multiple)
- ✓ find_by_status/author/type
- ✓ Auto-generate title
- ✓ Validation (no author/content)
- ✓ Enum serialization roundtrip
- ✓ Nullable fields (backlog_id, session_id)

**Brakuje:**
- ✗ SQLite errors (locked DB, disk full) — pokrywa Warning #2
- ✗ Invalid enum value w DB (corrupted data) — pokrywa Warning #4
- ✗ Concurrent access (dwa repo na tej samej bazie)
- ✗ Transaction rollback (co jeśli save() fails w połowie UPDATE?)

**Assessment:** Pokrycie happy path + podstawowe edge cases jest **Senior-level** ✓
Brakuje error scenarios (Mid-level gap) — ale to akceptowalne dla pierwszej iteracji.

---

## Recommended Actions

### Immediate (przed M2 part 2):
- [x] NONE — proceed to BacklogRepository/MessageRepository implementation

### Short-term (po M2 part 2 complete, przed M3):
- [ ] Rozważ proof of concept dla context manager w BacklogRepository (Suggestion #2)
- [ ] Zanotuj DRY pattern dla find_by_* — może być przydatny w BacklogRepository

### Medium-term (refactor iteration po M3):
- [ ] Fix Warning #1: Wyciągnij _find_by() helper (apply do wszystkich repositories)
- [ ] Fix Warning #3: Przenieś auto-generate title do Suggestion.__init__
- [ ] Fix Warning #4: Dodaj enum validation przy deserializacji
- [ ] Suggestion #1: Dodaj Repository.exists() do interfejsu

### Long-term (przed multi-agent):
- [ ] Fix Warning #2: Error handling dla SQLite exceptions (CRITICAL przed concurrent sessions)
- [ ] Suggestion #3: Paginated queries (gdy suggestions przekroczą ~200 items)

---

## Decision

**GREEN LIGHT** ✓ — Proceed to M2 part 2 (BacklogRepository, MessageRepository).

Kod jest **production-ready** dla obecnego single-agent use case. Zanotowane warnings nie blokują dalszej pracy — można je zaadresować w osobnej iteracji po M3 (adapter AgentBus).

**Rationale:**
1. Architektura zgodna z ADR-001 ✓
2. Testy pass, pokrycie akceptowalne ✓
3. Kod czytelny, SRP, minimalna abstrakcja ✓
4. Warnings dotyczą polish i future scalability, nie fundamentalnych błędów
5. Better to ship M2+M3 z Mid-level code niż czekać na perfect Senior-level refactor

Keep momentum. Fix iteracyjnie.

---

**Next:** M2 part 2 — BacklogRepository, MessageRepository (analogiczne do SuggestionRepository).
**After M2:** M3 — AgentBus adapter (backward compatibility CLI).
**After M3:** Refactor iteration — address Warnings #1, #3, #4.
