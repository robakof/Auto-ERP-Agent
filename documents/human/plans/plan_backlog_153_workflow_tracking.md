# Plan: Backlog #153 — Wielowarstwowe progress logi

## Cel

Workflow execution tracking — każdy krok workflow powiązany z execution_id, możliwość sprawdzenia gdzie agent skończył i wznowienia.

---

## Faza 1: Schema (tabele)

### 1.1 Tabela `workflow_execution`

```sql
CREATE TABLE workflow_execution (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id     TEXT NOT NULL,          -- np. "ERP_COLUMNS", "DEVELOPER_BUGFIX"
    role            TEXT NOT NULL,          -- agent który wykonuje
    session_id      TEXT,                   -- powiązanie z sesją Claude
    status          TEXT NOT NULL DEFAULT 'running',  -- running, completed, interrupted
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    CHECK (status IN ('running', 'completed', 'interrupted', 'failed'))
);
```

### 1.2 Tabela `step_log`

```sql
CREATE TABLE step_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id    INTEGER NOT NULL,       -- FK → workflow_execution
    step_id         TEXT NOT NULL,          -- np. "verify_git", "load_schema"
    step_index      INTEGER,                -- kolejność (opcjonalne)
    status          TEXT NOT NULL,          -- PASS, FAIL, BLOCKED, SKIPPED
    output_summary  TEXT,                   -- krótki opis wyniku
    output_json     TEXT,                   -- pełne dane (opcjonalne)
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (execution_id) REFERENCES workflow_execution(id),
    CHECK (status IN ('PASS', 'FAIL', 'BLOCKED', 'SKIPPED', 'IN_PROGRESS'))
);

CREATE INDEX idx_step_log_execution ON step_log(execution_id);
```

---

## Faza 2: AgentBus API

### 2.1 Metody w `agent_bus.py`

```python
def start_workflow_execution(self, workflow_id: str, role: str, session_id: str = None) -> int:
    """Tworzy nowy workflow_execution, zwraca execution_id."""

def log_step(self, execution_id: int, step_id: str, status: str,
             output_summary: str = None, output_json: dict = None) -> int:
    """Loguje krok workflow, zwraca step_log.id."""

def end_workflow_execution(self, execution_id: int, status: str = 'completed') -> None:
    """Zamyka execution (ustawia ended_at, status)."""

def get_execution_status(self, execution_id: int) -> dict:
    """Zwraca status execution + ostatni krok + next expected."""

def get_interrupted_executions(self, role: str = None) -> list[dict]:
    """Zwraca przerwane executions (status=interrupted/running bez ended_at)."""
```

---

## Faza 3: CLI komendy

### 3.1 `workflow-start`

```bash
py tools/agent_bus_cli.py workflow-start \
  --workflow-id ERP_COLUMNS \
  --role erp_specialist \
  --session-id abc123

# → {"ok": true, "execution_id": 42}
```

### 3.2 `step-log`

```bash
py tools/agent_bus_cli.py step-log \
  --execution-id 42 \
  --step-id verify_git \
  --status PASS \
  --summary "Git clean, branch: main"

# → {"ok": true, "step_id": 1}
```

### 3.3 `workflow-end`

```bash
py tools/agent_bus_cli.py workflow-end \
  --execution-id 42 \
  --status completed

# → {"ok": true}
```

### 3.4 `execution-status`

```bash
py tools/agent_bus_cli.py execution-status --execution-id 42

# → {
#     "ok": true,
#     "data": {
#       "execution_id": 42,
#       "workflow_id": "ERP_COLUMNS",
#       "status": "running",
#       "steps": [
#         {"step_id": "verify_git", "status": "PASS", "timestamp": "..."},
#         {"step_id": "load_schema", "status": "PASS", "timestamp": "..."}
#       ],
#       "last_step": "load_schema",
#       "last_status": "PASS"
#     }
#   }
```

### 3.5 `interrupted-workflows` (bonus)

```bash
py tools/agent_bus_cli.py interrupted-workflows --role erp_specialist

# → lista przerwanych workflow do wznowienia
```

---

## Faza 4: Testy

1. `test_workflow_execution_lifecycle` — start → steps → end
2. `test_step_log_ordering` — kroki w kolejności
3. `test_interrupted_detection` — wykrywanie przerwanych
4. `test_execution_status_query` — poprawny output

---

## Faza 5: Integracja z session_init (opcjonalne)

Dodać do `context` w session_init:
```json
{
  "interrupted_workflows": [
    {"execution_id": 42, "workflow_id": "ERP_COLUMNS", "last_step": "load_schema"}
  ]
}
```

Agent widzi przerwane workflow na starcie sesji.

---

## Kolejność implementacji

| Krok | Opis | Effort |
|------|------|--------|
| 1 | Schema (tabele w _SCHEMA_SQL + migracja) | mały |
| 2 | AgentBus metody (5 metod) | średni |
| 3 | CLI komendy (5 komend) | średni |
| 4 | Testy | mały |
| 5 | Integracja session_init | mały (opcjonalne) |

**Total effort:** średni (jak w backlog)

---

## Pytania do decyzji

1. **Czy step_index wymagany?** — jeśli workflow ma zdefiniowaną kolejność kroków, step_index pozwala sprawdzić "następny oczekiwany". Jeśli nie — można pominąć.

2. **Czy output_json przechowywać?** — może być duży. Alternatywa: tylko output_summary (string).

3. **Automatyczne "interrupted"?** — jeśli execution jest "running" przez >X godzin bez nowego step_log, oznaczyć jako interrupted? Czy zostawić to agentowi?

---

## Gotowe do implementacji

Po zatwierdzeniu planu → Faza 1 (schema).
