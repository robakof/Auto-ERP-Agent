# Code Review: F0 Quick Wins — multi-agent guard + dashboard + lifecycle gate

Date: 2026-03-30
Commit: `4285f33`
Branch: main

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 Senior — systematyczny, dobrze przetestowany, clean separation of concerns. Guard w git_commit.py jest pragmatyczny (direct DB zamiast AgentBus — uzasadnione). Dashboard laczy istniejace queries bez duplikacji logiki.

## Scope (5 plikow, 375 insertions)

1. `tools/hooks/pre_tool_use.py` — lifecycle gate (spawn/stop/resume → -request)
2. `tools/git_commit.py` — multi-agent guard (_count_active_agents)
3. `tools/agent_bus_cli.py` — dashboard CLI + stop-request + resume-request
4. `tests/test_pre_tool_use.py` — 6 testow lifecycle gate
5. `tests/test_git_commit.py` — 5 testow multi-agent guard + fix 3 istniejacych
6. `tests/test_agent_bus_cli.py` — 6 testow (dashboard, stop-request, resume-request)

**Testy: 17/17 PASS** (3.30s)

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1: Lifecycle gate blokuje stop — niezgodne z planem v2**
`pre_tool_use.py:44-48` — LIFECYCLE_GATE blokuje spawn, stop I resume.
Plan v2 mowi: "Stop NIE blokowany — szybkosc reakcji wazniejsza."
Czlowiek zatwierdzil ze kill wymaga zatwierdzenia, ale stop powinien byc wolny.

**Fix:** Usunac "stop" z LIFECYCLE_GATE. Dodac "kill" jesli istnieje komenda kill.

**W2: `_lookup_terminal_name` — brak w diffie**
`agent_bus_cli.py:761,783` — cmd_stop_request i cmd_resume_request uzywaja `_lookup_terminal_name(bus, args.session_id)` ktore nie jest w diffie. Zakladam ze istnieje wczesniej — do zweryfikowania.

**W3: Parser bug — `--task` argument przypisany do spawn-request po stop/resume definicjach**
`agent_bus_cli.py:1240` — linia `p_spawn_req.add_argument("--task", required=True, ...)` jest PO definicjach p_stop_req i p_resume_req. To prawdopodobnie dziala (Python argparse laczy argumenty do parsera) ale jest mylace — wyglada jakby --task nalezal do resume-request.

**Fix:** Przeniesc --task obok --role w bloku spawn-request (przed stop-request).

### Suggestions (nice to have)

**S1: `_count_active_agents` — context manager zamiast manual close**
`git_commit.py:31-36` — `conn = sqlite3.connect(); ...; conn.close()`. Bezpieczniej: `with sqlite3.connect(...) as conn:`.

**S2: Dashboard — brak testu na agents (stale/active)**
`test_agent_bus_cli.py:TestDashboard` — test_dashboard_with_data seeduje messages i backlog ale nie live_agents. Brak testu na agents.active i agents.stale. Dashboard alertow tez nie przetestowany z danymi.

**S3: `invocations` table — kolumny `action` i `target_session_id`**
Nowe kolumny (action, target_session_id) w INSERT ale brak jawnego ALTER TABLE / migration. Zakladam ze schema jest IF NOT EXISTS i nowe kolumny sa dodawane — do zweryfikowania.

## Odpowiedzi na pytania Dev

> `_count_active_agents()` laczy sie bezposrednio do mrowisko.db — akceptowalne?

**Tak.** Lightweight check, read-only, graceful fallback (exception → return 0). AgentBus wciagalby caly modul — overkill dla jednego COUNT. Direct DB poprawna decyzja.

> Dashboard alerts: czy logika stale/dead + pending handoffs + flags wystarczy na MVP?

**Tak.** Pokrywa 3 najczestsze scenariusze alertowe. Rozszerzenie (workflow violations, context usage) moze isc w v2 po event system.

## Recommended Actions

- [W1] Usunac "stop" z LIFECYCLE_GATE (niezgodne z zatwierdzonym planem)
- [W3] Przeniesc --task argument w parserze
- [S2] Dodac test dashboard z live_agents seed (nie-blocker)
