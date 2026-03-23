# Handoff: #125 zakończone, ale wykryto problem migracji danych

## Status

**Backlog #125:** ✓ DONE — 8 failujących testów naprawionych

**CRITICAL:** Wykryto problem w danych produkcyjnych — wymaga data fix.

---

## Co zrobiono (#125)

**Commit:** `d896e10`

1. ✓ Usunięto klasę TestState (44 linie, 6 testów) — metody write_state/get_state nie istnieją po M3/M4
2. ✓ Naprawiono testy Suggestions — zmieniono `"in_backlog"` → `"implemented"` (5 lokalizacji)
3. ✓ Naprawiono legacy_api.py mapping — `SuggestionStatus.IMPLEMENTED` → `"implemented"` zamiast `"in_backlog"`

**Test suite:** 103/103 PASS ✓

---

## Problem wykryty podczas blind spot query

**Lokalizacja:** Baza danych `mrowisko.db`, tabela `suggestions`

**Dane:**
```sql
SELECT status, COUNT(*) FROM suggestions GROUP BY status;

implemented: 95
in_backlog:  12  ← PROBLEM
open:        98
rejected:    21
```

**Root cause:**

12 sugestii w bazie ma status `"in_backlog"` (legacy value), ale:

1. **Domain model nie obsługuje tego enumu:**
   ```python
   # core/entities/messaging.py
   class SuggestionStatus(Enum):
       OPEN = "open"
       IMPLEMENTED = "implemented"  # brak "in_backlog"
       REJECTED = "rejected"
       DEFERRED = "deferred"
   ```

2. **Repository wywala error przy ładowaniu:**
   ```python
   # core/repositories/suggestion_repo.py linia 148
   status_enum = SuggestionStatus(row["status"])
   # ValueError: 'in_backlog' is not a valid SuggestionStatus
   ```

3. **Legacy API mapper wspiera backward compatibility (INPUT):**
   ```python
   # core/mappers/legacy_api.py linia 36
   SUGGESTION_STATUS_TO_DOMAIN = {
       "in_backlog": SuggestionStatus.IMPLEMENTED,  # ← OK dla INPUT
       "implemented": SuggestionStatus.IMPLEMENTED,
   }
   ```

   **Ale nie wspiera OUTPUT (już naprawione w #125):**
   ```python
   # core/mappers/legacy_api.py linia 44 (PO FIX)
   SUGGESTION_STATUS_FROM_DOMAIN = {
       SuggestionStatus.IMPLEMENTED: "implemented",  # ← było "in_backlog"
   }
   ```

**Impact:**

**BLOKER:** `bus.get_suggestions()` wywala `ValidationError` — żadna sugestia nie może być załadowana.

```python
from tools.lib.agent_bus import AgentBus
bus = AgentBus('mrowisko.db')
suggestions = bus.get_suggestions()
# ValidationError: Invalid enum value in database: 'in_backlog' is not a valid SuggestionStatus
```

---

## Rozwiązanie (wymaga implementacji)

**Option A: Data migration (preferowane)**

```sql
UPDATE suggestions SET status = 'implemented' WHERE status = 'in_backlog';
```

**Plusy:**
- Jedno zapytanie SQL
- Czysta baza zgodna z domain model
- Brak legacy baggage

**Minusy:**
- Modyfikuje dane produkcyjne
- Wymaga backup przed migracją

**Option B: Graceful degradation w repository**

```python
# core/repositories/suggestion_repo.py linia 146-150
try:
    status_enum = SuggestionStatus(row["status"])
except ValueError:
    # Legacy "in_backlog" → map to IMPLEMENTED
    if row["status"] == "in_backlog":
        status_enum = SuggestionStatus.IMPLEMENTED
    else:
        raise ValidationError(f"Invalid enum value: {row['status']}")
```

**Plusy:**
- Nie modyfikuje danych
- Backward compatible

**Minusy:**
- Legacy code w warstwie domain
- Problem pozostaje (dane niespójne z modelem)

---

## Inne miejsca wymagające weryfikacji

**CLI choices (nie powodują błędu, ale są niespójne):**

1. `tools/agent_bus_cli.py` linia 309:
   ```python
   choices=["open", "in_backlog", "rejected", "implemented"]
   ```

2. `tools/agent_bus_cli.py` linia 317:
   ```python
   choices=["open", "in_backlog", "rejected", "implemented"]
   ```

**Renderer colors (nie powodują błędu):**

3. `tools/lib/renderers/base.py` linia 17:
   ```python
   "in_backlog": "FFEB9C",
   ```

**Agent bus server (nie powodują błędu):**

4. `tools/agent_bus_server.py` linia 45:
   ```python
   status: Optional[str] = Query(None, description="open|in_backlog|rejected|implemented")
   ```

**Backward compatibility (INPUT):**

5. `core/mappers/legacy_api.py` linia 36:
   ```python
   "in_backlog": SuggestionStatus.IMPLEMENTED,  # Legacy name
   ```

**Uwaga:** Punkt 5 to **celowa** backward compatibility — pozwala na akceptowanie `"in_backlog"` przy update_suggestion_status(). Nie usuwać bez konsultacji.

---

## Rekomendacja

**Krótkoterminowo (ASAP):**
1. Data migration — `UPDATE suggestions SET status = 'implemented' WHERE status = 'in_backlog'`
2. Backup bazy przed migracją

**Średnioterminowo:**
1. Usunąć `"in_backlog"` z CLI choices (linie 309, 317)
2. Zostawić w legacy_api.py (INPUT backward compatibility)
3. Renderer colors i agent_bus_server — nie krytyczne, można zostawić

**Long-term:**
- Dodać migration system do projektu (Alembic / własny)
- ADR dla enum deprecation policy

---

## Następne kroki

Developer powinien:
1. Sprawdzić backup bazy
2. Wykonać data migration: `UPDATE suggestions SET status = 'implemented' WHERE status = 'in_backlog'`
3. Zweryfikować: `bus.get_suggestions()` działa bez błędów
4. Opcjonalnie: usunąć `"in_backlog"` z CLI choices (niski priorytet)

---

## Kontekst sesji

- Sesja rozpoczęta: backlog #125 (napraw failujące testy)
- Workflow: developer_workflow.md Bug fix
- Blind spot query wykonany po naprawie testów
- Wykryto problem podczas sprawdzania czy są inne wystąpienia `"in_backlog"`
- Kontekst wyczerpany (~60%) — handoff zamiast naprawy
