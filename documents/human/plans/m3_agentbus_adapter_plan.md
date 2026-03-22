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

### Phase 2: Backlog
4. **add_backlog_item()** → `BacklogRepository.save()`
5. **get_backlog()** → `BacklogRepository.find_by_*()` + `find_all()`
6. **update_backlog_status()** → `BacklogRepository.get()` + `save()`
7. **update_backlog_content()** → `BacklogRepository.get()` + `save()`

### Phase 3: Messages
8. **send_message()** → `MessageRepository.save()`
9. **get_inbox()** → `MessageRepository.find_by_recipient()` + filter
10. **mark_read()** → `MessageRepository.get()` + `mark_read()` + `save()`
11. **get_messages()** → `MessageRepository.find_by_*()` + filters

### Phase 4: Others (out of scope M3)
- session_log, trace, sessions, instances (później)

---

## Implementation pattern

**Example: add_suggestion()**

```python
# OLD (procedural)
def add_suggestion(self, author, content, title="", type="observation", ...):
    cursor = self._conn.execute(
        "INSERT INTO suggestions (...) VALUES (...)",
        (author, content, title, type, ...)
    )
    return cursor.lastrowid

# NEW (adapter → repository)
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

    # Save via repository
    repo = SuggestionRepository(db_path=self.db_path)
    saved = repo.save(suggestion)

    # Return ID (backward compatible)
    return saved.id
```

**Key points:**
1. API nie zmienia się (parametry, return type)
2. Wewnętrznie używamy repositories
3. Dict ↔ Entity conversion w adapterze

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

## Success criteria M3

✓ add_suggestion() + get_suggestions() + update_suggestion_status() używają repositories
✓ Backward compatibility: agent_bus_cli.py działa bez zmian
✓ Testy agent_bus pass
✓ Plan Phase 2 (Backlog) gotowy

**Out of scope M3:**
- Backlog, Messages (Phase 2-3)
- session_log, trace (Phase 4)
- Deprecation starego kodu
- Migracja agentów na repositories

---

## Next after M3

**M4:** Backlog + Messages adapters (Phase 2-3)
**M5:** Migracja agentów (używają repositories zamiast agent_bus)
**M6:** Deprecation + cleanup starego kodu
