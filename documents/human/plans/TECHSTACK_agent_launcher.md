# Tech Stack: Agent Launcher

*Data: 2026-03-26*
*Autor: Architect*
*PRD: `documents/human/plans/PRD_agent_launcher.md`*
*Eksperymenty: `documents/human/reports/experiments_agent_launcher_results.md`*

---

## 1. Wtyczka VS Code

| Element | Technologia | Uzasadnienie |
|---|---|---|
| Język | **TypeScript** | Standard VS Code extensions. Strict mode. |
| Extension API | **VS Code Terminal API** | `createTerminal`, `sendText`, `onDidCloseTerminal`, `TerminalLocation.Editor`. Potwierdzone E-04. |
| Bundler | **esbuild** (via `@vscode/vsce`) | Standard VS Code. Szybki build. |
| Testy | **@vscode/test-electron** | Oficjalny framework testowy dla extensions. |

### Kluczowe API

```typescript
// Spawn terminal w editor area
vscode.window.createTerminal({
    name: "Agent: developer",
    location: TerminalLocation.Editor,
    // opcjonalnie: viewColumn dla pozycji w gridzie
});

// Lifecycle events
vscode.window.onDidCloseTerminal(terminal => { /* cleanup */ });
vscode.window.onDidOpenTerminal(terminal => { /* register */ });
```

---

## 2. Claude Code CLI

| Element | Flagi | Uzasadnienie |
|---|---|---|
| Spawn | `claude --append-system-prompt "..." --session-id "<uuid>" --name "Agent: role"` | Potwierdzone E-01 + manualna weryfikacja. Interaktywna sesja, CLAUDE.md ładuje się. |
| Permission | `--permission-mode <mode>` | Konfigurowalne per spawn. Default: `default`. |
| Resume | `claude --resume "Agent: role"` | Potwierdzone manualnie. |
| Auto-start | `terminal.sendText("Rola, wykonaj task")` | Pierwsza wiadomość wysłana przez wtyczkę po spawnie. |

---

## 3. Baza danych

| Element | Technologia | Uzasadnienie |
|---|---|---|
| DB | **SQLite / mrowisko.db** | Istniejąca infrastruktura. Cross-window mediator (E-02). WAL mode. |
| Dostęp z TS | **Python bridge** (`tools/agent_launcher_db.py` via `execFileSync`) | `better-sqlite3` (native C++) nie działa w Electron (ABI mismatch). Python bridge reużywa infrastrukturę, zero native deps. Sync ~50ms — do async w Fazie 3. |
| Dostęp z Python | **sqlite3** (stdlib) | Istniejący pattern (agent_bus.py). |

### Nowa tabela: `live_agents`

Per CONVENTION_DB_SCHEMA (draft):

```sql
CREATE TABLE IF NOT EXISTS live_agents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT UNIQUE NOT NULL,
    role            TEXT NOT NULL,
    task            TEXT,
    terminal_name   TEXT,
    window_id       TEXT,
    status          TEXT NOT NULL DEFAULT 'starting',
    spawned_by      TEXT,
    permission_mode TEXT NOT NULL DEFAULT 'default',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_activity   TEXT,
    stopped_at      TEXT,
    transcript_path TEXT,
    CHECK (status IN ('starting', 'active', 'stopped'))
);

CREATE INDEX IF NOT EXISTS idx_live_agents_status ON live_agents(status);
CREATE INDEX IF NOT EXISTS idx_live_agents_role ON live_agents(role);
```

Uwaga: `idle` usunięte z enum — brak natywnego sygnału (decyzja z E-03).

### Nowa tabela: `invocations`

```sql
CREATE TABLE IF NOT EXISTS invocations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoker_type    TEXT NOT NULL,
    invoker_id      TEXT NOT NULL,
    target_role     TEXT NOT NULL,
    task            TEXT NOT NULL,
    session_id      TEXT REFERENCES sessions(id),
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    CHECK (invoker_type IN ('human', 'agent', 'orchestrator')),
    CHECK (status IN ('pending', 'approved', 'running', 'completed', 'failed', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_invocations_status ON invocations(status);
```

---

## 4. Hooki (Python)

| Hook | Plik | Trigger | Akcja |
|---|---|---|---|
| `SessionStart` | `tools/hooks/on_session_start.py` | Start sesji | Zarejestruj w `live_agents` (status: active) |
| `Stop` | `tools/hooks/on_stop.py` (rozszerzenie) | Agent kończy odpowiedź | Update `last_activity` w `live_agents` |
| `SessionEnd` | `tools/hooks/on_session_end.py` | Koniec sesji | Oznacz `status: stopped`, ustaw `stopped_at` |

---

## 5. Odrzucone alternatywy

| Alternatywa | Dlaczego odrzucona |
|---|---|
| Agent SDK (Python/TS) | Nie daje pełnej interaktywnej sesji CLI. Brak slash commands, status line. |
| Agent Teams | Brak integracji z mrowisko.db (E-01). |
| tmux / Windows Terminal | Wymaga WSL, mniejsza kontrola niż VS Code Extension API. |
| subprocess + stream-json | Brak interaktywności. `-p` = print and exit. |
| node-sqlite3 (async) | Callback-based, trudniejsze w extensions. |
| better-sqlite3 | Native C++ moduł — ABI mismatch z Electron (VS Code Extension Host). Nie kompiluje się bez electron-rebuild. Python bridge prostszy i kompatybilny. |
