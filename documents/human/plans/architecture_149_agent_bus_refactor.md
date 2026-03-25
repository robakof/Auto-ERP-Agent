# ARCHITECTURE: AgentBus Refaktor — Separation of Concerns (#149)

## PRD (skrócone)

**Cel:** Rozdzielić AgentBus (1262 linii, ~50 metod) na wyspecjalizowane serwisy.
**Problem:** Jedna klasa robi messaging, backlog, sesje, telemetrię, workflow, instancje.
Nowe pole wymaga zmian w N miejscach. Trudno testować, trudno zmieniać.
**Użytkownik:** Developer (dodaje narzędzia), CLI (agent_bus_cli.py), Runner (mrowisko_runner.py).
**Wymagania niefunkcjonalne:** Zero breaking changes, backward compat, zero test regression.

## Tech Stack

- Python 3.12, SQLite (WAL), dataclasses
- Istniejące: core/entities/, core/repositories/, core/mappers/
- Bez nowych zależności

## Architektura docelowa

```
AgentBusFacade (thin orchestrator, ~100 linii)
  ├── MessageService        (send, inbox, mark_read, archive)
  ├── SuggestionService     (add, get, update_status)
  ├── BacklogService        (add, get, update_status, update_content)
  ├── SessionService        (log, get_logs, upsert, conversation)
  ├── TelemetryService      (tool_calls, token_usage, session_trace)
  ├── WorkflowService       (start, step_log, end, status, interrupted)
  ├── InstanceService       (register, heartbeat, busy/idle, terminate, claim/unclaim)
  ├── KnownGapsService      (add, get, resolve)
  └── Repositories          (istniejące — bez zmian)
```

## Inwentarz metod → serwisy

### MessageService (8 metod)
| Metoda | Linia | Uwagi |
|--------|-------|-------|
| send_message | 333 | uses _extract_title_from_markdown |
| get_inbox | 373 | |
| get_message_by_id | 408 | |
| mark_read | 419 | |
| archive_message | 441 | direct SQL → use repo |
| mark_message_read | 955 | duplicate of mark_read? |
| mark_all_read | 963 | direct SQL |
| get_messages | 801 | direct SQL, filtering |

### SuggestionService (3 metody)
| Metoda | Linia |
|--------|-------|
| add_suggestion | 453 |
| get_suggestions | 491 |
| update_suggestion_status | 526 |

### BacklogService (5 metod)
| Metoda | Linia |
|--------|-------|
| add_backlog_item | 568 |
| get_backlog | 605 |
| get_backlog_by_id | 633 |
| update_backlog_status | 652 |
| update_backlog_content | 677 |

### SessionService (5 metod)
| Metoda | Linia |
|--------|-------|
| add_session_log | 699 |
| get_session_log | 715 |
| get_session_logs | 726 |
| get_session_logs_init | 765 |
| add_conversation_entry | 1065 |
| get_conversation | 1082 |

### TelemetryService (3 metody)
| Metoda | Linia |
|--------|-------|
| add_tool_call | 997 |
| add_token_usage | 1015 |
| get_session_trace | 1038 |

### WorkflowService (5 metod)
| Metoda | Linia |
|--------|-------|
| start_workflow_execution | 832 |
| log_step | 844 |
| end_workflow_execution | 863 |
| get_execution_status | 893 |
| get_interrupted_executions | 917 |

### InstanceService (9 metod)
| Metoda | Linia |
|--------|-------|
| register_instance | 1097 |
| heartbeat | 1109 |
| set_instance_busy | 1117 |
| set_instance_idle | 1125 |
| terminate_instance | 1133 |
| get_free_instances | 1141 |
| get_all_instances | 1153 |
| claim_task | 1164 |
| unclaim_task | 1175 |
| get_pending_tasks | 1185 |

### KnownGapsService (3 metody)
| Metoda | Linia |
|--------|-------|
| add_known_gap | 1202 |
| get_known_gaps | 1221 |
| resolve_known_gap | 1244 |

### Core (AgentBusFacade)
| Metoda | Linia | Uwagi |
|--------|-------|-------|
| __init__ | 225 | DB setup, migrations |
| _run_migrations | 237 | |
| _auto_commit | 244 | |
| _get_repository | 249 | |
| transaction | 267 | context manager |
| _extract_title_from_markdown | 295 | static, move to utils |
| flag_for_human | 938 | uses send_message |
| upsert_session | 976 | |
| close | 1091 | |

## Duplikaty do wyeliminowania

1. `mark_read()` (L419) vs `mark_message_read()` (L955) — ten sam cel, różna implementacja
2. `get_inbox()` (L373) vs `get_messages()` (L801) — inbox = get_messages z filtrem recipient+status
3. `archive_message()` (L441) — direct SQL, powinno iść przez repo

## Plan implementacji — kamienie milowe

### M1: Extract services (incremental, per service)

Kolejność extractu: od najprostszego do najtrudniejszego.

1. **KnownGapsService** — 3 metody, 0 zależności, warmup
2. **WorkflowService** — 5 metod, 0 zależności
3. **TelemetryService** — 3 metody, FK do sessions
4. **SuggestionService** — 3 metody, uses repo
5. **BacklogService** — 5 metod, uses repo
6. **SessionService** — 5+2 metod, upsert_session
7. **InstanceService** — 9+1 metod, claim/unclaim
8. **MessageService** — 8 metod, najtrudniejsze (duplikaty, direct SQL)

**Pattern per extract:**
1. Create `core/services/<name>.py` z metodami skopiowanymi z AgentBus
2. Serwis przyjmuje `conn` (shared connection) w konstruktorze
3. AgentBus deleguje do serwisu (zachowaj stary interface)
4. Testy — istniejące PASS + nowy unit test per serwis
5. Commit per serwis

### M2: Eliminate duplicates

Po extract MessageService:
- `mark_message_read` → alias do `mark_read`
- `get_inbox` → delegacja do `get_messages` z filtrem
- `archive_message` → przez repo zamiast direct SQL

### M3: Create AgentBusFacade

1. AgentBus → rename do AgentBusFacade
2. Facade deleguje do services
3. CLI/Runner używają facade (interface bez zmian)
4. Deprecation warnings na stare direct-call patterns

### M4: Cleanup

1. Usuń zduplikowane metody
2. Usuń direct SQL (wszystko przez services/repos)
3. Update testy

## Zasady refaktoru

1. **Jeden serwis = jeden commit.** Atomic, reversible.
2. **Interface AgentBus nie zmienia się.** CLI/Runner nie widzą refaktoru.
3. **Testy PASS po każdym commicie.** 227+ testów to safety net.
4. **Serwis = pure logic + conn.** Bez DB setup, migrations, schema.
5. **Direct SQL → repository.** Każdy direct SQL w serwisie to bug do naprawienia w M2.

## Struktura plików docelowa

```
core/
  services/
    __init__.py
    message_service.py
    suggestion_service.py
    backlog_service.py
    session_service.py
    telemetry_service.py
    workflow_service.py
    instance_service.py
    known_gaps_service.py
  entities/        (bez zmian)
  repositories/    (bez zmian)
  mappers/         (bez zmian)
tools/lib/
  agent_bus.py     (AgentBusFacade — thin delegator)
```

## Ryzyka

| Ryzyko | Mitygacja |
|--------|-----------|
| Concurrent sessions commitują z --all | Commit per serwis, atomic |
| CLI/Runner breaking changes | Interface AgentBus preserved |
| Transaction isolation | Services share conn via facade |
| Test regression | 227 PASS = gate per commit |

## Success Criteria

- [ ] 8 serwisów wydzielonych
- [ ] Duplikaty wyeliminowane (mark_read, get_inbox, archive)
- [ ] Direct SQL → repository
- [ ] AgentBusFacade < 200 linii
- [ ] 227+ testów PASS
- [ ] Zero breaking changes CLI/Runner
