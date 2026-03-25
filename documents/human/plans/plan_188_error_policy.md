# Plan: #188 Spójna polityka błędów

## Audit — obecny stan

| Warstwa | Pattern | Problemy |
|---------|---------|----------|
| Services (domain) | Mix: ValueError, silent return, bare except | Brak spójności — `except Exception: return` maskuje bugi |
| Repository | None na not-found, raise na violations | OK — spójne |
| AgentBus (facade) | auto_commit po delegacji | OK — thin |
| CLI | Brak error handling — exception propaguje jako stack trace | Brudny output |

## Polityka docelowa

### Warstwa 1: Services (domain logic)
- **Not-found**: return None (get_by_id) lub silent return (update na nieistniejącym)
- **Invalid input**: raise ValueError z opisem
- **Invalid state**: raise InvalidStateError (z core.exceptions)
- **ZAKAZ**: bare `except Exception` — maskuje bugi. Łap konkretne wyjątki.

### Warstwa 2: AgentBus (facade)
- Deleguje bez łapania — exception propaguje do CLI
- auto_commit() tylko po sukcesie

### Warstwa 3: CLI (boundary)
- try/except na top-level
- Error → `{"ok": false, "error": "message"}` (JSON, nie stack trace)
- Zawsze exit code 0 (JSON output) lub 1 (unexpected crash)

## Zmiany

### 1. MessageService.mark_read() — bare except → konkretny
```python
# PRZED:
except Exception:
    return
# PO:
except InvalidStateError:
    return  # already read — graceful
```

### 2. SuggestionService.add() — bare except → konkretny
```python
# PRZED:
except ValueError:
    type_enum = SuggestionType.OBSERVATION
# OK — to jest poprawny fallback, zostawiamy
```

### 3. BacklogService.update_status() — silent return na not-found
OK — backward compat. Dodać komentarz.

### 4. CLI top-level — brak error boundary
Dodać try/except w main() z JSON error output.

## Scope

- 1 fix w service (MessageService bare except)
- Komentarze polityki w każdym service
- CLI error boundary
