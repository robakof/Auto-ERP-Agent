# Code Review: Backlog #152 (handoff type) + #153 (workflow execution tracking)

Date: 2026-03-24
Commits: `fdaee88`, `153517f`, `a9c7d52`, `47e64aa`
Handoff: #270 (Developer → Architect)

## Summary

**Overall assessment:** PASS
**Code maturity level:** Senior — czysty podział odpowiedzialności (entity/mapper/CLI/bus), spójny styl z resztą codebase, pragmatyczne decyzje (flat tables, CHECK constraints). Brak over-engineering.

## Scope przeglądu

| Commit | Opis | Pliki |
|--------|------|-------|
| `fdaee88` | Handoff type (#152) | entity, mapper, migration, CLI |
| `153517f` | Message ordering fix | agent_bus.py (1 linia) |
| `a9c7d52` | Workflow tracking tables (#153 phase 1) | migration, DDL w agent_bus.py |
| `47e64aa` | Workflow tracking API + CLI (#153 phase 2-3) | agent_bus.py, agent_bus_cli.py |

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

- **W1: `end_workflow_execution` nie waliduje statusu wejściowego**
  `tools/lib/agent_bus.py:814` — Można zakończyć workflow który jest już "completed" lub "failed". Brak idempotency guard. Nie jest to groźne (DB CHECK constraint chroni wartości), ale pozwala na logiczny nonsens: `completed` → `failed` bez ostrzeżenia.
  **Fix guidance:** Sprawdź aktualny status przed UPDATE. Jeśli `ended_at IS NOT NULL` — zwróć informację zamiast nadpisywać.

- **W2: `log_step` nie waliduje czy execution istnieje/jest running**
  `tools/lib/agent_bus.py:795` — FOREIGN KEY jest zdefiniowany, ale SQLite domyślnie nie wymusza FK (wymaga `PRAGMA foreign_keys = ON`). Agent_bus ustawia `journal_mode=WAL` na starcie, ale nie ustawia `foreign_keys=ON`.
  **Fix guidance:** Dodaj `PRAGMA foreign_keys = ON` w `__init__` (obok WAL). Lub sprawdź execution status przed INSERT.

- **W3: Brak testów dla nowych metod workflow tracking**
  Nowe tabele (workflow_execution, step_log) i 5 metod API nie mają dedykowanych testów. Pokryte tylko pośrednio (testy CLI mogą nie istnieć). Istniejące testy (77 PASS) nie dotyczą nowego kodu.
  **Fix guidance:** Dodaj TestWorkflowExecution (start/step/end/status/interrupted) analogicznie do TestMessages/TestSuggestions/TestBacklog.

- **W4: Brak testów dla cmd_handoff**
  Handoff type dodany do entity/mapper/CLI, ale brak testu który weryfikuje round-trip: send handoff → inbox → structured content.
  **Fix guidance:** Test w TestMessages: send_message z type="handoff", verify w inbox.

### Suggestions (nice to have)

- **S1: `get_interrupted_executions` duplikacja SQL**
  `tools/lib/agent_bus.py:848-865` — Dwie gałęzie (z role / bez role) z prawie identycznym SQL. Można ujednolicić dynamicznym WHERE.
  **Rationale:** Spójność z innymi metodami (get_suggestions używa dynamicznego filtrowania).

- **S2: `cmd_handoff` buduje content przez string concatenation**
  `tools/agent_bus_cli.py:65-92` — Handoff content budowany przez `parts.append()` + `"\n".join()`. Działa, ale format jest hardcoded w CLI. Jeśli kiedykolwiek będziemy parsować handoff content (np. do structured display) — lepiej zapisywać jako JSON z polami.
  **Rationale:** Na razie wystarczające. Flaguję jako future consideration, nie blocker.

- **S3: Migration scripts nie są rejestrowane w centralnym miejscu**
  Mamy teraz 3 pliki migration (`migration_add_handoff_type.py`, `migration_m4_2_2_check_constraints.py`, `migration_workflow_tracking.py`). Brak rejestru migracji w DB (np. tabela `schema_migrations`).
  **Rationale:** Przy rosnącej liczbie migracji ryzyko że ktoś odpali starą migrację lub pominie nową. Na razie niski priorytet — DDL w `_SCHEMA_SQL` jest idempotentny (`CREATE IF NOT EXISTS`).

## Wynik testów

- agent_bus: 69/69 PASS
- setup_machine: 8/10 PASS, 2 FAILED (encoding polskich znaków w subprocess — **pre-existing bug**, nie związany z review)
- Testy ERP/Bot: 15 collection errors (brak pyodbc/search_bi — zależności domenowe)

## Ogólna ocena

Kod jest spójny z architekturą projektu. Podział entity → mapper → bus → CLI zachowany. Migracje mają dry-run mode (dobra praktyka). CHECK constraints w DB chronią spójność danych.

Główny gap to **brak testów dla nowego kodu** (W3, W4). Developer powinien dopisać testy przed uznaniem feature za production-ready.

## Recommended Actions

- [ ] **W2:** Dodać `PRAGMA foreign_keys = ON` w AgentBus.__init__
- [ ] **W3:** Testy workflow execution (5 metod)
- [ ] **W4:** Test handoff round-trip
- [ ] **W1:** Idempotency guard w end_workflow_execution (opcjonalnie)
