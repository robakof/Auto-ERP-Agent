# Plan implementacyjny: Event Listener System v1

**ADR:** `documents/architecture/ADR-003-event-listener-system.md`
**Owner:** Developer
**Effort:** srednia (3-5 sesji)
**Priority:** wysoka — odblokuje docelowy model dispatchera

---

## Fazy implementacji

### Faza 1: DB Schema + Migration (1 sesja)

**Cel:** Tabele events, listeners, event_cursor w mrowisko.db.

1. Dodaj migration SQL do `agent_bus.py` (`_MIGRATE_SQL`):
   ```sql
   CREATE TABLE IF NOT EXISTS events (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       event_type TEXT NOT NULL,
       source_role TEXT,
       source_session TEXT,
       event_data TEXT NOT NULL DEFAULT '{}',
       created_at TEXT DEFAULT (datetime('now'))
   );
   CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
   CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);

   CREATE TABLE IF NOT EXISTS listeners (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       subscriber TEXT NOT NULL,
       event_type TEXT NOT NULL,
       filter_json TEXT,
       poke_template TEXT,
       active INTEGER DEFAULT 1,
       created_at TEXT DEFAULT (datetime('now')),
       expires_at TEXT
   );
   CREATE INDEX IF NOT EXISTS idx_listeners_sub_event
       ON listeners(subscriber, event_type, active);

   CREATE TABLE IF NOT EXISTS event_cursor (
       subscriber TEXT PRIMARY KEY,
       last_event_id INTEGER DEFAULT 0,
       updated_at TEXT DEFAULT (datetime('now'))
   );
   ```

2. Napisz test migracji: schemat tworzony poprawnie, indeksy istnieją.

**Exit gate:** `py -m pytest tests/ -k "event"` — schema tests PASS.

---

### Faza 2: Core Library — _emit_event + filter/template (1 sesja)

**Cel:** Reusable function do emisji zdarzeń, wywoływana z CLI i hooks.

1. Nowy moduł: `tools/lib/event_emitter.py`
   ```python
   def emit_event(event_type: str, event_data: dict, db) -> int:
       """Insert event + auto-poke active subscribers. Returns event_id."""

   def _matches_filter(filter_json: str | None, event_data: dict) -> bool:
       """JSON filter matching: every key-value in filter must match event_data."""

   def _render_template(template: str | None, event_data: dict) -> str:
       """Simple {key} replacement in poke template."""

   def _auto_poke(subscriber: str, message: str, db):
       """Poke if subscriber active, else skip (event stays in queue)."""

   def get_pending_events(subscriber: str, db) -> list[dict]:
       """Get events since cursor, filtered by registered listeners. Advances cursor."""

   def register_listener(subscriber, event_type, filter_json, poke_template, expires_at, db) -> int:
       """Idempotent: skip if identical listener exists. Returns listener_id."""

   def cleanup_events(days: int = 7, db):
       """Delete events older than N days. Delete expired listeners."""
   ```

2. Logika `_auto_poke`:
   - Query `live_agents` WHERE role = subscriber AND status = 'active'
   - If found → call existing poke mechanism (subprocess: `agent_bus_cli.py poke`)
   - If not found → skip (event stays in queue for pull on session_init)

3. Logika `_matches_filter`:
   - filter_json = None → match all
   - filter_json = `{"role": "PE"}` → event_data["role"] == "PE"
   - Simple key-value AND matching (no OR, no nested)

4. Logika `register_listener` (idempotent):
   - Check if identical (subscriber, event_type, filter_json) already exists and active
   - If yes → return existing id
   - If no → INSERT

5. Testy:
   - `test_emit_event` — event inserted, correct payload
   - `test_filter_matching` — various filter scenarios
   - `test_template_rendering` — {key} replacement
   - `test_auto_poke_active` — poke called when subscriber active
   - `test_auto_poke_inactive` — poke NOT called when subscriber offline
   - `test_get_pending_events` — cursor advances, events filtered by listeners
   - `test_register_listener_idempotent` — duplicate skipped
   - `test_cleanup_events` — old events purged

**Exit gate:** Wszystkie testy PASS. Zero dependency na extension/CLI (unit tests).

---

### Faza 3: CLI Integration — listen, listeners, unlisten, events (1 sesja)

**Cel:** Komendy CLI do zarządzania listenerami i odczytu eventów.

1. Dodaj do `agent_bus_cli.py` komendy:

   ```
   listen --subscriber <role> --event <event_type> [--filter <json>] [--poke-template <text>] [--expires <datetime>]
   listeners --subscriber <role>
   unlisten --id <id>
   unlisten --subscriber <role> --all
   events --subscriber <role>          # pull pending, advance cursor
   events-ack --subscriber <role>      # advance cursor without reading
   ```

2. Dodaj `_emit_event()` call po state-modifying commands:

   | Command | Event type | Payload fields |
   |---|---|---|
   | `workflow-end` | `workflow_end` | workflow_id, role, status, execution_id |
   | `send` | `message_sent` | sender, recipient, type, title |
   | `handoff` | `handoff_sent` | sender, recipient, phase, status |
   | `flag` | `flag_raised` | sender, reason_preview (first 100 chars) |
   | `backlog-add` | `backlog_changed` | id, title, area, status="planned" |
   | `backlog-update` | `backlog_changed` | id, title, area, status |
   | `step-log` | `step_completed` | execution_id, step_id, status |

3. Testy integracyjne:
   - `test_listen_and_events` — register, emit, pull
   - `test_emit_triggers_poke` — mock poke, verify called
   - `test_events_cursor` — cursor advances, re-read returns empty
   - `test_unlisten` — listener removed, events no longer matched

**Exit gate:** CLI tests PASS. Manual test: `listen` → `send` → `events` shows event.

---

### Faza 4: Hook Integration — agent_started/stopped (1 sesja)

**Cel:** Hooks emitują events na lifecycle changes.

1. `tools/hooks/on_session_start.py`:
   - Po udanym linkowaniu spawn_token → `emit_event("agent_started", {role, session_id})`
   - Import: `from lib.event_emitter import emit_event`

2. `tools/hooks/on_session_end.py`:
   - Po UPDATE status='stopped' → `emit_event("agent_stopped", {role, session_id})`

3. **Uwaga:** hooks muszą importować event_emitter. Sprawdź sys.path.
   Hook cwd = project root → `from tools.lib.event_emitter import emit_event`
   lub: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))` → `from lib.event_emitter import emit_event`

4. Testy: mock DB, verify event emitted po hook execution.

**Exit gate:** Testy PASS. Manual: start agent → event "agent_started" w events table.

---

### Faza 5: Session Init Integration (1 sesja)

**Cel:** Pending events dostarczane na session_init w context.

1. `tools/session_init.py`:
   - Po załadowaniu inbox/backlog: `events = get_pending_events(role, db)`
   - Dodaj do context output: `"events": events`
   - Cleanup: `cleanup_events(days=7, db)` (fire-and-forget)

2. Nowa sekcja w context output:
   ```json
   {
     "context": {
       "inbox": {...},
       "backlog": {...},
       "events": {
         "items": [
           {"id": 42, "event_type": "workflow_end", "source_role": "prompt_engineer",
            "event_data": {"workflow_id": "...", "status": "completed"},
            "created_at": "2026-03-29 22:15:00"}
         ],
         "count": 1
       }
     }
   }
   ```

3. Events pojawiają się TYLKO gdy rola ma zarejestrowane listeners.
   Brak listeners → events section pusty (zero overhead).

**Exit gate:** Manual test: register listener, emit event, restart session → event w context.

---

## Orchestracja dispatchera (po wdrożeniu)

### Setup listeners (jednorazowy, na starcie pierwszej sesji):

```bash
py tools/agent_bus_cli.py listen --subscriber dispatcher --event workflow_end \
    --poke-template "Workflow {workflow_id} zakończony przez {role}: {status}"
py tools/agent_bus_cli.py listen --subscriber dispatcher --event handoff_sent \
    --poke-template "Handoff od {sender} do {recipient}: {phase}"
py tools/agent_bus_cli.py listen --subscriber dispatcher --event agent_stopped \
    --poke-template "Agent {role} zatrzymany (session: {session_id})"
py tools/agent_bus_cli.py listen --subscriber dispatcher --event agent_started \
    --poke-template "Agent {role} wystartował (session: {session_id})"
py tools/agent_bus_cli.py listen --subscriber dispatcher --event flag_raised \
    --poke-template "Eskalacja od {sender}: {reason_preview}"
```

### Cykl pracy dispatchera (nowy model):

```
1. session_init → context zawiera pending events
2. Przeczytaj events → zareaguj (proponuj akcje człowiekowi)
3. Podczas pracy → poke'i dostarczają nowe events w real-time
4. Koniec sesji → events kumulują się w queue
5. Następna sesja → powtórz od 1
```

### Efekt:

- Zamiast 3+ polling queries per cykl → events przychodzą automatycznie
- Zamiast ciągłego działania → dispatcher przywoływany gdy potrzebny
- Zamiast zgadywania "co się zmieniło" → explicit event log

---

## Test plan (end-to-end)

- [ ] Schema migration — tabele + indeksy tworzone poprawnie
- [ ] emit_event — event w tabeli, poprawny payload
- [ ] filter matching — None=all, {"key":"val"} filters, non-matching skipped
- [ ] template rendering — {key} replaced, missing key = literal {key}
- [ ] listen (idempotent) — duplicate listener skipped
- [ ] unlisten — listener deactivated, events no longer matched
- [ ] auto-poke — active subscriber poked, inactive skipped
- [ ] events pull — returns pending since cursor, advances cursor
- [ ] events-ack — cursor advanced without reading
- [ ] CLI integration — workflow-end emits event, send emits event, etc.
- [ ] Hook integration — session_start/end emit agent_started/stopped
- [ ] session_init — pending events in context output
- [ ] cleanup — events >7 days purged, expired listeners removed
- [ ] E2E: register listener → emit event → check events → event delivered

---

## v2 Upgrade Path (Extension Push)

Po stabilizacji v1, jeśli potrzebujemy budzić idle agentów:
1. Nowy moduł `EventProcessor` w extension (`extensions/mrowisko-terminal-control/src/event_processor.ts`)
2. Wzorowany na `approver.ts` — poll `events` table co 5-10s
3. Match against `listeners` (reuse SQL queries z event_emitter.py)
4. Delivery: `terminal.sendText("[EVENT] ...")` — budzi agenta jak user message
5. Zero zmian w DB schema — identyczny model danych
6. Extension staje się hub eventów — CLI emituje, extension doręcza

**Trigger dla v2:** Gdy dispatcher regularnie nie otrzymuje events na czas
(poke latency staje się blokerem w realnej pracy).
