# Code Review: Agent Launcher M1

Date: 2026-03-26
Commit: `9ac9a48`

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 (Senior) — czytelna architektura, SRP w komponentach, property separation (types/registry/spawner/watcher/commands), sensowne edge cases (pre-registered vs manual, cross-window stop). Dobra implementacja per ARCHITECTURE doc.

## Findings

### Critical Issues (must fix)

*Brak.*

### Warnings (should fix)

- **spawner.ts:51-59** — Budowanie komendy claude przez string concatenation. Jeśli `systemPrompt` zawiera znaki specjalne PowerShella (backticki, dolary, nawiasy) — komenda się rozpadnie. Rozważ: escape function lub generowanie pliku z promptem + `--append-system-prompt` z pliku (jeśli obsługiwane). Na razie niebloker bo kontrolujemy input, ale przy agent-to-agent invocation (Faza 2) to będzie problem.

- **spawner.ts:63-64** — `sendText(task)` leci natychmiast po `sendText(cmd)`. Nie ma gwarancji że Claude Code wystartował zanim task dotrze. Terminal bufferuje input więc prawdopodobnie działa, ale warto dodać komentarz wyjaśniający dlaczego to jest bezpieczne (terminal buffer queues input).

- **on_session_start.py:38** — `bus._conn` — bezpośredni dostęp do prywatnego atrybutu. Narusza enkapsulację. Powinien być helper method w AgentBus albo bezpośredni `sqlite3.connect()` (hook nie potrzebuje pełnego AgentBus). Ten sam problem w `on_session_end.py:38`.

- **on_session_start.py:53-56** — Manual session insertuje `role='unknown'`. Każda ręcznie uruchomiona sesja (`claude` bez spawnerа) trafi do live_agents jako unknown. Czy to zamierzone? Może lepiej nie insertować manual sessions do live_agents (hook odpala się dla KAŻDEJ sesji, nie tylko spawned).

### Suggestions (nice to have)

- **commands.ts:6-13** — Lista ROLES hardcoded. W przyszłości: czytaj z `config/session_init_config.json` (tam są role) lub z konfiguracji wtyczki. Nie blokuje Fazy 1.

- **registry.ts:77-81** — Cleanup threshold 1h hardcoded. Per sugestia "preferuj konfigurowalne" — rozważ parametr. Nie blokuje Fazy 1.

- **watcher.ts** — Iteracja po TerminalMap żeby znaleźć terminal to O(n). Przy 100+ agentów może być wolne. Rozważ reverse map (Terminal → sessionId). Faza 3 optimization.

- **extension.ts:24** — `cleanup()` na starcie jest dobry pattern (orphan protection). Warto logować ile agentów wyczyszczono (debug).

## DB Schema Review

Tabele `live_agents` i `invocations` w `_MIGRATE_SQL` — **zgodne z CONVENTION_DB_SCHEMA**:
- ✓ snake_case plural names
- ✓ CHECK constraints na enumach
- ✓ idx_ naming
- ✓ Komentarz z kontekstem
- ✓ `created_at TEXT NOT NULL DEFAULT (datetime('now'))`

## Hooks Review

- `on_session_start.py` — poprawna logika pre-registered vs manual. Error handling zapisuje do pliku (defensive).
- `on_session_end.py` — `COALESCE(?, transcript_path)` — dobry pattern (nie nadpisuj jeśli już jest).
- Oba hooki: `sys.stdin = io.TextIOWrapper(...)` — spójne z istniejącym `on_stop.py`. OK.

## Architecture Compliance

| Komponent z ARCHITECTURE | Zaimplementowany? | Zgodny? |
|---|---|---|
| Spawner | ✓ spawner.ts | ✓ |
| Registry | ✓ registry.ts | ✓ |
| Watcher | ✓ watcher.ts | ✓ |
| Commands | ✓ commands.ts | ✓ |
| types.ts | ✓ | ✓ |
| extension.ts | ✓ | ✓ |
| on_session_start.py | ✓ | ✓ |
| on_session_end.py | ✓ | ✓ |
| on_stop.py rozszerzenie | ✓ | ✓ |
| live_agents table | ✓ | ✓ (CONVENTION_DB_SCHEMA) |
| invocations table | ✓ | ✓ (CONVENTION_DB_SCHEMA) |

## Recommended Actions

- [ ] **W1:** Dodaj komentarz w spawner.ts wyjaśniający bezpieczeństwo kolejnych sendText
- [ ] **W2:** Zamień `bus._conn` na bezpośredni `sqlite3.connect()` w hookach (nie potrzebują AgentBus)
- [ ] **W3:** Rozważ czy manual sessions powinny trafiać do live_agents (on_session_start.py:53)
- [ ] **W4:** PowerShell escape w spawner.ts — na razie komentarz, fix przed Fazą 2
