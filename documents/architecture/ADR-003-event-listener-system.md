# ADR-003: Event Listener System — Event-Driven Monitoring

Date: 2026-03-29
Status: Proposed

## Context

### Problem

Dispatcher nie ma sposobu na event-driven monitoring. Obecny model wymaga ręcznego
pollowania `live-agents`, `inbox-summary`, `handoffs-pending` w pętli — co zjada
kontekst (tokeny na redundantne queries) i wymusza ciągłe działanie dispatchera.

Diagnoza startu (2026-03-29) wykazała:
- 4 minuty + zbędne tokeny na orientację
- Dispatcher musi siedzieć w pętli poll żeby wykryć zmiany
- Docelowy model: dispatcher przywoływany przez człowieka, nie działający ciągle

### Docelowy model (z diagnozy)

> Dispatcher na nasłuchu — czeka na wywołanie od człowieka.
> Gdy wywołany — uruchamia agenta (resume > spawn).
> Pracuje na otwartych, nie wykończonych sesjach.
> Przyzywanie agenta jest DROGIE — czas i kontekst.

### Istniejąca infrastruktura

- **Poke**: message type='poke' → pre_tool_use hook deny → agent widzi na next tool use
- **Hooks**: on_session_start/end, pre/post_tool_use, on_user_prompt — Python, DB access
- **Extension approver**: polls `invocations` table co 5s — wzorzec polling w extension
- **session_init**: ładuje inbox, backlog, session_logs na starcie sesji

### Ograniczenia poke

1. Fires on next tool use (nie natychmiast)
2. Nie działa gdy agent idle (czeka na user input)
3. Jeden poke procesowany per tool call (LIMIT 1)

### Relacja do backlog #168 (Tryb nasłuchu)

#168 to **pull model**: agent okresowo refreshuje kontekst.
Ten ADR to **push model**: system powiadamia agenta gdy zdarzenie wystąpi.
Komplementarne — event listeners redukują potrzebę na #168 dla zarejestrowanych zdarzeń.

## Opcje rozważone

### Option A: DB Event Queue + Extension Push

- CLI/hooks emitują events do tabeli `events`
- Nowy `EventProcessor` w extension polls `events` co 5-10s
- Match against `listeners` → extension `terminal.sendText()` budzi agenta
- Prawdziwy push — działa nawet gdy agent idle

**Pro:** True push, agent budzony natychmiast, extension ma direct terminal access.
**Con:** Wymaga TypeScript changes w extension, nowy moduł do maintain.

### Option B: CLI Post-Action + Session Init Pull (RECOMMENDED v1)

- CLI commands emitują events do tabeli `events` po state mutation
- Hooks emitują events na lifecycle changes
- Active agent: po emisji, CLI sprawdza listeners → auto-poke jeśli subscriber active
- Idle agent: events kumulują się w queue → dostarczane na session_init
- Nowa komenda `events` do ręcznego pull w trakcie sesji

**Pro:** Zero extension changes, pure Python, uses existing poke, graceful degradation.
**Con:** Poke latency (next tool use), nie budzi idle agenta.

### Option C: Dedicated Background Process

- Standalone daemon polls DB → matches listeners → triggers pokes
- **Pro:** Decoupled, sophisticated batching.
- **Con:** New process to manage, overkill for current scale.

## Decision

**Option B (CLI Post-Action + Session Init Pull) dla v1.**
**Option A jako upgrade path dla v2** (gdy potrzebujemy budzić idle agentów).

Uzasadnienie:
1. **Manifestation Through Action** — najprostsza działająca implementacja
2. Pure Python — zero TypeScript, zero nowych procesów
3. DB schema identyczny dla v1 i v2 — migracja bezbolesna
4. Overhead minimalny: 1 SELECT (listeners) po każdym state-modifying command
5. Docelowy model dispatchera (intermittent) naturalnie pasuje do pull-on-init

## Architecture

### Hybrid Push/Pull Model

```
At rest (dispatcher offline):
  events accumulate in queue → delivered on next session_init

Active (dispatcher running):
  CLI mutation → emit event → check listeners → auto-poke active subscriber
  Agent tool call → pre_tool_use processes poke → agent reacts
```

### DB Schema

```sql
-- Event queue: append-only log of system events
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

-- Listeners: subscriptions to event types
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

-- Cursor: tracks last processed event per subscriber
CREATE TABLE IF NOT EXISTS event_cursor (
    subscriber TEXT PRIMARY KEY,
    last_event_id INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now'))
);
```

### Event Types (v1)

| Event Type | Source | Trigger Point | Payload |
|---|---|---|---|
| `workflow_end` | CLI `workflow-end` | Po UPDATE status | `{workflow_id, role, status, execution_id}` |
| `message_sent` | CLI `send` | Po INSERT message | `{sender, recipient, type, title}` |
| `handoff_sent` | CLI `handoff` | Po INSERT message | `{sender, recipient, phase, status}` |
| `flag_raised` | CLI `flag` | Po INSERT message | `{sender, reason_preview}` |
| `agent_started` | Hook `on_session_start` | Po UPDATE live_agents | `{role, session_id}` |
| `agent_stopped` | Hook `on_session_end` | Po UPDATE live_agents | `{role, session_id}` |
| `backlog_changed` | CLI `backlog-add/update` | Po INSERT/UPDATE | `{id, title, area, status}` |
| `step_completed` | CLI `step-log` | Po INSERT step_log | `{execution_id, step_id, status}` |

### CLI Commands (nowe)

```bash
# Register listener
py tools/agent_bus_cli.py listen \
    --subscriber dispatcher \
    --event workflow_end \
    --filter '{"role": "prompt_engineer"}' \
    --poke-template "PE zakończył workflow {workflow_id}: {status}"

# List active listeners
py tools/agent_bus_cli.py listeners --subscriber dispatcher

# Remove listener
py tools/agent_bus_cli.py unlisten --id <listener_id>

# Pull pending events (advances cursor)
py tools/agent_bus_cli.py events --subscriber dispatcher

# Acknowledge all (advance cursor without reading)
py tools/agent_bus_cli.py events-ack --subscriber dispatcher
```

### Integration Points

```
agent_bus_cli.py:
  workflow-end   → _emit_event("workflow_end", {...})
  send           → _emit_event("message_sent", {...})
  handoff        → _emit_event("handoff_sent", {...})
  flag           → _emit_event("flag_raised", {...})
  backlog-add    → _emit_event("backlog_changed", {...})
  backlog-update → _emit_event("backlog_changed", {...})
  step-log       → _emit_event("step_completed", {...})

tools/hooks/on_session_start.py:
  Po link spawn_token → _emit_event("agent_started", {...})

tools/hooks/on_session_end.py:
  Po UPDATE stopped → _emit_event("agent_stopped", {...})

tools/session_init.py:
  Po załadowaniu inbox/backlog → _get_pending_events(role) → dodaj do context
```

### Core Function: _emit_event

```python
def _emit_event(event_type: str, event_data: dict, db):
    """Emit event to queue. Auto-poke active subscribers."""
    # 1. Persist event
    event_id = db.execute(
        "INSERT INTO events (event_type, source_role, source_session, event_data) "
        "VALUES (?, ?, ?, ?)",
        (event_type, event_data.get('source_role'),
         event_data.get('source_session'), json.dumps(event_data))
    ).lastrowid
    db.commit()

    # 2. Find matching active listeners with live subscribers
    rows = db.execute("""
        SELECT l.subscriber, l.filter_json, l.poke_template
        FROM listeners l
        JOIN live_agents la ON la.role = l.subscriber AND la.status = 'active'
        WHERE l.event_type = ? AND l.active = 1
          AND (l.expires_at IS NULL OR l.expires_at > datetime('now'))
    """, (event_type,)).fetchall()

    # 3. Filter + poke
    for row in rows:
        if not _matches_filter(row['filter_json'], event_data):
            continue
        msg = _render_template(row['poke_template'], event_data) \
              if row['poke_template'] \
              else f"[EVENT:{event_type}] {json.dumps(event_data, ensure_ascii=False)}"
        _auto_poke(row['subscriber'], f"[EVENT] {msg}")
```

### Dispatcher Usage

```
# Session start — register listeners (idempotent, skip if already registered)
listen --subscriber dispatcher --event workflow_end
listen --subscriber dispatcher --event handoff_sent --filter '{"recipient": "dispatcher"}'
listen --subscriber dispatcher --event agent_stopped
listen --subscriber dispatcher --event flag_raised
listen --subscriber dispatcher --event agent_started

# session_init context now includes:
# context.events: [{event_type: "workflow_end", ...}, ...]

# During session — events arrive as pokes:
# "[EVENT] PE zakończył workflow workflow_dispatcher: completed"
# → dispatcher reacts (proposes next action to human)

# Between sessions — events accumulate in queue
# → delivered on next session_init
```

### Event Cleanup

Events older than 7 days auto-purged (run in session_init or as periodic maintenance):
```sql
DELETE FROM events WHERE created_at < datetime('now', '-7 days');
```

Listeners with `expires_at` past → ignored (soft delete via `active` flag or hard delete in cleanup).

## Consequences

### Gains
- Dispatcher nie marnuje kontekstu na polling (events przychodzą do niego)
- Zdarzenia nie giną między sesjami (event queue persists)
- Composable — dowolna rola może się zarejestrować jako subscriber
- DB schema forward-compatible z Option A (extension push v2)
- Minimalny overhead: 1 SELECT per state-modifying CLI command

### Costs
- Każdy state-modifying CLI command slightly slower (~1-5ms, 1 SELECT)
- Hooks (session_start/end) gain DB write (event emission)
- Poke delivery latency: fires on next tool use, nie natychmiast
- Idle agent nie dostaje events w real-time (adresowane w v2)

### Risks
- **Poke storm**: wiele zdarzeń → wiele poke'ów → context pollution
  - Mitigation v1: poke template krótki, procesowane 1 per tool call
  - Mitigation v2: event batching (digest zamiast individual pokes)
- **Event queue growth**: append-only bez cleanup = disk growth
  - Mitigation: 7-day TTL, auto-purge w session_init
- **SQLite write contention**: wiele agentów emituje events jednocześnie
  - Mitigation: WAL mode, events append-only (low contention)

### v2 Upgrade Path (Extension Push)

Gdy potrzebujemy budzić idle agentów:
1. Nowy moduł `EventProcessor` w extension (wzorowany na Approver)
2. Polls `events` table co 5-10s
3. Match against `listeners` (reuse existing logic)
4. `terminal.sendText("[EVENT] ...")` — budzi agenta jak user message
5. Zero zmian w DB schema — ten sam model danych
