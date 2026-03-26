# Code Review: Agent Launcher M2

Date: 2026-03-26
Commits: `24dd4ae`, `90b6d33`

## Summary

**Overall assessment:** PASS
**Code maturity level:** L3 (Senior) — dobrze rozdzielone komponenty, pragmatyczne rozwiązania (Python bridge, URI handler), czytelna logika approval gate. Dobre obsłużenie edge cases (processing Set, reject path, cleanup).

## Findings

### Critical Issues (must fix)

*Brak.*

### Warnings (should fix)

- **agent_bus_cli.py:499** — `bus._conn` bezpośredni dostęp. Ten sam problem co W2 z M1. `cmd_spawn` i `cmd_spawn_request` powinny używać serwisu lub bezpośredniego `sqlite3.connect()`. Teraz jest niespójne: hooki naprawione (direct connect), CLI nadal na `_conn`.

- **agent_bus_cli.py:506** — `last_insert_rowid()` po `commit()`. Potencjalnie niebezpieczne przy concurrent access — inny proces mógł wstawić wiersz między commit a rowid query. Bezpieczniejszy: `cursor.lastrowid` z obiektu cursor przed commitem, lub `RETURNING id` (SQLite 3.35+).

- **approver.ts:45** — `console.log("[Mrowisko Approver] poll result:", output.trim())` — debug log który loguje pełny output DB na każdy poll (co 5s). To jest dużo noise. Oznaczony do cleanup w M3.3, ale potwierdzone jako warning.

- **approver.ts:19** — `processing = new Set<number>()` — dobry pattern (zapobiega wielokrotnym dialogom), ale Set nigdy nie jest persisted. Jeśli Extension Host się restartuje — pending invocations pokażą dialog ponownie. Akceptowalne (lepiej pokazać 2x niż 0x), ale warto komentarz.

### Suggestions (nice to have)

- **vscode_uri.py:24-28** — Hardcoded ścieżki do Code.exe. Działa na standardowych instalacjach, ale nie na portable/custom. Fallback przez `shutil.which` jest dobry. Rozważ: env variable `VSCODE_PATH` jako override.

- **approver.ts:69** — `showWarningMessage` ma limit 3 przycisków na Windows. Przy wielu pending invocations naraz — wiele dialogów. Rozważ: batch approval (QuickPick z multi-select) w Fazie 3.

- **agent_launcher_db.py** — Każda operacja otwiera i zamyka connection. Przy polling co 5s = nowe połączenie co 5s. Dla SQLite z WAL to OK (lekkie), ale warto monitorować przy skali 100+ agentów. Async w Fazie 3 może wprowadzić connection pool.

## Architecture Compliance

| Komponent z ARCHITECTURE M2 | Zaimplementowany? | Zgodny? |
|---|---|---|
| M2.1 CLI spawn | ✓ `agent_bus_cli.py spawn` | ✓ |
| M2.2 Invocation tracking | ✓ tabela `invocations` | ✓ |
| M2.3 Approval gate | ✓ `approver.ts` + polling | ✓ |
| M2.4 Workflow invocation | ✓ = M2.1 (direct spawn) | ✓ |
| M2.5 Windows helper | ✓ `vscode_uri.py` | ✓ |
| URI handler | ✓ `extension.ts` | ✓ (D8) |

## Recommended Actions

- [ ] **W1:** `cmd_spawn`/`cmd_spawn_request` — zamień `bus._conn` na direct connect lub serwis
- [ ] **W2:** `last_insert_rowid()` — użyj `cursor.lastrowid` przed commit
- [ ] **W3:** Debug logs cleanup (M3.3 — już zaplanowane)
- [ ] **W4:** Komentarz w approver.ts o processing Set nie przeżywającym restart
