# Code Review: Identity Redesign

Date: 2026-03-29
Plan: `documents/human/plans/plan_identity_redesign.md`
Request: message #507 (developer)

## Summary

**Overall assessment:** NEEDS REVISION
**Code maturity level:** L2 Mid — Poprawny, czytelny kod z dobrą architekturą, ale z jednym brakującym flow (resume w nowym terminalu), naruszeniem enkapsulacji (_conn leak), i duplikacją logiki resolver.

## Findings

### Critical Issues (must fix)

**C1: Resume w nowym terminalu nie przywraca tożsamości**
- **extension.ts:115-129** + **on_session_start.py:41-50**
- Plan (linie 130-137) mówi: "Spawner tworzy nowy terminal z nowym spawn_token → on_session_start: spawn_token nowy, ale claude_uuid już jest w DB → UPDATE live_agents SET spawn_token=new, terminal_name=new, status='active' WHERE claude_uuid=?. Tożsamość zachowana."
- Implementacja: `resumeAgent` tworzy terminal z nowym `spawn_token` w env, ale NIE wywołuje `registry.insert()`. Na `on_session_start`, branch `if spawn_token` robi `UPDATE WHERE spawn_token = ? AND status = 'starting'` — matchuje 0 rows bo nikt nie pre-insertował rekordu.
- Efekt: `session_init` fallback tworzy NOWY rekord bez `claude_uuid`. Agent działa, ale traci tożsamość (nowy session_id). Stary rekord zostaje 'stopped' z oryginalnym claude_uuid.
- **Fix guidance:** Dwie opcje:
  - (A) W `on_session_start.py`: gdy spawn_token UPDATE matchuje 0 rows, dodaj fallback: `UPDATE live_agents SET spawn_token=?, status='active', terminal_name=? WHERE claude_uuid=? AND status='stopped'` (reactivation via claude_uuid)
  - (B) W `extension.ts resumeAgent`: wywołaj `registry.insert(spawnToken, ...)` przed `createTerminal` — analogicznie do normal spawn

### Warnings (should fix)

**W1: Stale docstrings — 3 pliki**
- **post_tool_use.py:16** — "session_id czytamy z tmp/session_id.txt" — nieprawda, kod używa spawn_token/claude_uuid
- **session_init.py:9** — "Writes session_id to tmp/session_id.txt" — nie pisze
- **agent_launcher_db.py:4** — Usage example ma `--session-id UUID`, a kod przyjmuje `--spawn-token`
- Fix: zaktualizuj docstrings

**W2: _conn leak — hooks bezpośrednio piszą SQL po prywatnym atrybucie AgentBus**
- **on_user_prompt.py:45,69-79** — `bus._conn.execute(...)` (session_id resolver + heartbeat)
- **on_stop.py:38,46,49** — `bus._conn.execute(...)` (session_id resolver + live_agent update)
- **post_tool_use.py:73-85** — `bus._conn.execute(...)` (session_id resolver)
- Problem: tight coupling do SQLite. Zmiana persistence layer wymaga edycji 4 hooków.
- Fix: dodaj do AgentBus publiczne metody `resolve_session_id(spawn_token, claude_uuid)` i `heartbeat(spawn_token, claude_uuid)`.

**W3: DRY — resolve_session_id zduplikowany 4x**
- Pattern `if spawn_token: SELECT WHERE spawn_token=? / if not and claude_uuid: SELECT WHERE claude_uuid=?` skopiowany w:
  - on_user_prompt.py (44-57)
  - post_tool_use.py (71-85)
  - on_stop.py (100-112)
  - session_init.py (201-204 + 242-245)
- Fix: jeden public method w AgentBus, 4 callsites → 1 implementation

**W4: types.ts:27 — komentarz mówi "session_id → Terminal", ale Map jest keyed by spawnToken**
- `spawner.ts:82`: `terminals.set(spawnToken, terminal)` — klucz to spawn_token
- Komentarz: `Map of session_id → vscode.Terminal`
- Fix: zaktualizuj komentarz na `spawn_token → Terminal`

**W5: uuid_bridge CREATE w _SCHEMA_SQL (agent_bus.py:292-298), potem DROP w migration**
- Każde nowe DB: CREATE uuid_bridge → DROP uuid_bridge. Bezużyteczny cykl.
- Fix: usuń CREATE uuid_bridge z _SCHEMA_SQL (migration i tak robi DROP IF EXISTS)

**W6: session_init.py:259-263 — dead ON CONFLICT clause**
- Manual session INSERT ma `ON CONFLICT(session_id) DO UPDATE`, ale session_id jest freshly generated `uuid.uuid4().hex[:12]`. Kolizja statystycznie niemożliwa (1:2^48).
- Fix: usuń ON CONFLICT, używaj prostego INSERT

**W7: Brak explicit test listy**
- Dev podał: "Spawn architect → live_agents: session_id, claude_uuid, heartbeat — wszystko poprawne" — to 1 manual test.
- Identity redesign to fundament systemu. Brakuje automated testów dla:
  - Resume w tym samym terminalu
  - Resume w nowym terminalu
  - Manual session (bez spawn_token)
  - GC (auto-stop po 10 min)
  - Concurrent spawn (2 agentów jednocześnie)
  - Edge: spawn_token → crashed before on_session_start

### Suggestions (nice to have)

**S1: session_init.py:195** — `import os` inside function body. Powinno być na górze pliku (linia 12-15).

**S2: on_stop.py:76** — `import os` inside function body. Powinno być na górze.

**S3: agent_launcher_db.py cleanup timeout** — `cmd_cleanup` używa 1h timeout, ale hooks GC (on_user_prompt) używa 10 min. Niespójność może zostawiać "zombie" rekordy między 10 min a 1h.

## Architecture Compliance

| Wymóg z planu | Status |
|---|---|
| claude_uuid jako primary identity | ✓ Zaimplementowany |
| spawn_token w env var | ✓ Zaimplementowany |
| DROP uuid_bridge | ✓ Zaimplementowany |
| Usunięcie shared files | ✓ Zaimplementowany |
| Flow: Spawn | ✓ Działa |
| Flow: Resume (ten sam terminal) | ✓ Działa (/resume w istniejącym terminalu) |
| Flow: Resume (nowy terminal) | ✗ BROKEN (C1) |
| GC inline | ✓ Zaimplementowany |
| Heartbeat deterministyczny | ✓ Działa (via spawn_token, fallback claude_uuid) |

## Recommended Actions

- [ ] **C1**: Napraw resume-in-new-terminal flow (opcja A lub B w opisie)
- [ ] **W1**: Zaktualizuj 3 stale docstrings
- [ ] **W2+W3**: Wyciągnij `resolve_session_id()` i `heartbeat()` jako public methods AgentBus
- [ ] **W4**: Popraw komentarz w types.ts
- [ ] **W5**: Usuń uuid_bridge z _SCHEMA_SQL
- [ ] **W7**: Dodaj automated testy identity flows (przynajmniej: spawn, resume, manual, GC)
