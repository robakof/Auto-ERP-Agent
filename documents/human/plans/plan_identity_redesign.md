# Plan: Agent Identity Redesign — claude_uuid jako primary identity

**Data:** 2026-03-29
**Autor:** Architect
**Status:** Zaimplementowany (code review PASS 2026-03-29, warnings W1-W7 w backlogu)

---

## Zasada

**Tożsamość agenta = rozmowa Claude Code (claude_uuid), nie terminal.**

Terminal jest efemeryczny — może być zamknięty, odtworzony, zmieniony. Rozmowa przeżywa /resume.
claude_uuid jest nadawany przez Claude Code, unikalny per sesja, stabilny. Opieramy się na nim.

session_id (nasz krótki 12-char hex) zostaje jako alias do wyświetlania i referencji w CLI.
Nie jest primary identity — jest convenience label.

---

## Architektura

### live_agents — nowy schemat

```sql
-- Usunąć starą tabelę i stworzyć od nowa (2 dni danych, zero legacy)
DROP TABLE IF EXISTS live_agents;
CREATE TABLE live_agents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    claude_uuid     TEXT UNIQUE,                        -- PRIMARY IDENTITY (z Claude Code payload)
    session_id      TEXT UNIQUE,                        -- alias (krótki, z session_init)
    role            TEXT,                                -- ustawiane przez session_init
    terminal_name   TEXT,                               -- ustawiane przez spawner
    task            TEXT,
    status          TEXT NOT NULL DEFAULT 'starting',    -- starting/active/stopped
    spawned_by      TEXT,                                -- 'human', 'dispatcher', 'manual'
    spawn_token     TEXT,                                -- one-time bridge spawner↔hook
    last_activity   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    stopped_at      TEXT,
    transcript_path TEXT
);
```

### Usunąć

```sql
DROP TABLE IF EXISTS uuid_bridge;
```

Pliki do usunięcia:
- `tmp/session_id.txt` — reads/writes
- `tmp/session_data.json` — reads/writes
- `tmp/pending_claude_uuid.txt` — reads/writes
- Funkcje: `read_session_id()`, `write_session_id()` w session_init.py
- Funkcje: `_read_session_id()` w on_session_start.py, on_session_end.py, on_user_prompt.py

---

## Flow: Spawn (Dispatcher/human uruchamia agenta)

```
1. SPAWNER (extension):
   spawn_token = randomUUID()
   INSERT live_agents (spawn_token=T, role='developer', terminal_name='Dev-abc', status='starting')
   createTerminal({ name: 'Dev-abc', env: { MROWISKO_SPAWN_TOKEN: T } })
   sendText('claude')

2. ON_SESSION_START (hook):
   spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN")
   claude_uuid = payload["session_id"]

   if spawn_token:
       UPDATE live_agents SET claude_uuid=?, status='active', last_activity=now
       WHERE spawn_token=?
   else:
       # Manual session — insert z claude_uuid
       INSERT live_agents (claude_uuid=?, status='active', spawned_by='manual')

3. SESSION_INIT (agent):
   spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN")

   if spawn_token:
       row = SELECT * FROM live_agents WHERE spawn_token=?
       claude_uuid = row.claude_uuid
       session_id = row.session_id or generate_session_id()
       UPDATE live_agents SET session_id=?, role=? WHERE spawn_token=?
   else:
       # Manual session — find by claude_uuid (z pending file fallback? lub z DB by recent)
       session_id = generate_session_id()
       ...

   # Load context, return JSON

4. HEARTBEAT (on_user_prompt):
   spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN")
   claude_uuid = payload.get("session_id")

   if spawn_token:
       UPDATE live_agents SET last_activity=now WHERE spawn_token=?
   elif claude_uuid:
       UPDATE live_agents SET last_activity=now WHERE claude_uuid=?
   # Zero shared files. Zawsze deterministyczny match.

5. SESSION_END (on_session_end):
   claude_uuid = payload.get("session_id")
   UPDATE live_agents SET status='stopped', stopped_at=now WHERE claude_uuid=?
```

---

## Flow: Resume (/resume w istniejącym terminalu)

```
1. Claude Code robi /resume → ta sama rozmowa → ten sam claude_uuid
2. on_session_start fires → claude_uuid ten sam → UPDATE status='active'
3. session_init fires → spawn_token ten sam (env var przeżywa) → ten sam record
4. session_init widzi: record istnieje z moim claude_uuid → resumed=true
5. Ładuje świeży kontekst (inbox, backlog)
```

Agent zachowuje tożsamość bo claude_uuid się nie zmienił. Terminal jest ten sam (env var ten sam).

---

## Flow: Resume (nowy terminal, ta sama rozmowa)

```
1. Stary terminal zamknięty → session_end → status='stopped'
2. Spawner tworzy nowy terminal z nowym spawn_token
3. sendText('claude --resume')
4. Claude Code wznawia → TEN SAM claude_uuid
5. on_session_start: spawn_token nowy, ale claude_uuid już jest w DB
   → UPDATE live_agents SET spawn_token=new, terminal_name=new, status='active'
     WHERE claude_uuid=?
6. Tożsamość zachowana. Nowy terminal, ta sama rozmowa.
```

---

## GC: auto-stop martwych sesji

```sql
-- W on_user_prompt, inline:
UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now')
WHERE status IN ('active', 'starting')
  AND last_activity < datetime('now', '-10 minutes');
```

---

## Scope implementacji

### Faza 1: Fundament (~1 sesja Dev)

1. **agent_bus.py**: DROP + CREATE live_agents (nowy schemat), DROP uuid_bridge
2. **spawner.ts**: `env: { MROWISKO_SPAWN_TOKEN: spawnToken }` w createTerminal
3. **extension.ts**: to samo dla resumeAgent (jeśli tworzy terminal)
4. **on_session_start.py**: czytaj env spawn_token + payload claude_uuid → UPDATE/INSERT
5. **session_init.py**: czytaj env spawn_token → find record → set session_id + role
6. **on_user_prompt.py**: heartbeat po spawn_token lub claude_uuid (env + payload)
7. **on_session_end.py**: stop po claude_uuid (payload) — bez zmian (już działa)
8. **Usunąć**: read_session_id, write_session_id, uuid_bridge, pending file, session_data reads

### Faza 2: GC + cleanup

9. **on_user_prompt.py**: inline GC (10 min timeout)
10. **v_agent_status**: weryfikacja że view nadal działa z nowym schematem
11. **render_dashboard.py**: weryfikacja

### Faza 3: Testy

12. Test: spawn 2 agentów → oba mają poprawny claude_uuid i session_id
13. Test: resume → ten sam claude_uuid, session_id zachowany
14. Test: heartbeat → aktualizuje SWÓJ record
15. Test: GC → martwe sesje auto-stopped

---

## Co NIE zmienia się

- messages, backlog, suggestions, workflow_execution — używają session_id (alias), nie dotykamy
- agent_bus_cli komendy — `--session-id` zostaje (krótki, wygodny)
- Dashboard — czyta z v_agent_status (view, nie tabela bezpośrednio)
- Poke, stop, resume CLI — matchują po session_id lub terminal_name (bez zmian w interfejsie)
