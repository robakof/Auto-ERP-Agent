# Architecture: Agent Launcher

*Data: 2026-03-26*
*Autor: Architect*
*PRD: `documents/human/plans/PRD_agent_launcher.md`*
*Tech Stack: `documents/human/plans/TECHSTACK_agent_launcher.md`*

---

## 1. Architektura systemu

```
┌─────────────────────────────────────────────────────────┐
│                    VS Code Window A                      │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Terminal 1   │  │ Terminal 2   │  │ Terminal 3   │    │
│  │ Agent: dev   │  │ Agent: erp   │  │ Human: arch  │    │
│  │ (spawned)    │  │ (spawned)    │  │ (ręczny)     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │            │
│  ┌──────┴─────────────────┴─────────────────┴──────┐    │
│  │              Extension Host A                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │    │
│  │  │ Spawner  │  │ Registry │  │ Watcher  │      │    │
│  │  │          │  │ (poll DB)│  │ (events) │      │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘      │    │
│  └───────┼──────────────┼──────────────┼────────────┘    │
└──────────┼──────────────┼──────────────┼────────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────────────────────────────────────┐
    │           mrowisko.db (SQLite)            │
    │                                          │
    │  live_agents   invocations   messages     │
    │  sessions      backlog       suggestions  │
    └──────────────────────────────────────────┘
           ▲              ▲              ▲
           │              │              │
┌──────────┼──────────────┼──────────────┼────────────────┐
│          │              │              │                 │
│  ┌───────┼──────────────┼──────────────┼────────────┐   │
│  │       Extension Host B (poll DB, spawn local)    │   │
│  └──────────────────────────────────────────────────┘   │
│                    VS Code Window B                      │
└─────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────┐
    │         Claude Code Hooks            │
    │                                      │
    │  SessionStart → live_agents INSERT   │
    │  Stop         → live_agents UPDATE   │
    │  SessionEnd   → live_agents UPDATE   │
    └──────────────────────────────────────┘
```

---

## 2. Komponenty wtyczki

### 2.1 Spawner

Odpowiedzialność: tworzenie terminali i uruchamianie sesji Claude Code.

```
Input:  SpawnRequest { role, task, permissionMode, systemPrompt? }
Output: Terminal + LiveAgent record w DB

Flow:
1. Generuj UUID4 → session_id
2. INSERT do live_agents (status: starting)
3. createTerminal({ name, location: Editor })
4. sendText(claude --name ... --session-id ... --append-system-prompt ...)
5. sendText("Rola, task")  ← auto-start
```

### 2.2 Registry

Odpowiedzialność: odczyt stanu żywych agentów z mrowisko.db.

```
Metody:
- getActiveAgents(): LiveAgent[]
- getAgentBySessionId(id): LiveAgent | null
- getAgentsByRole(role): LiveAgent[]
- updateStatus(sessionId, status): void
- cleanup(): void  ← oznacz orphaned agents jako stopped
```

Wtyczka **polluje** registry co N sekund (np. 5s) żeby odświeżyć widok.
Hooki **piszą** do registry (SessionStart/Stop/SessionEnd).

### 2.3 Watcher

Odpowiedzialność: reagowanie na eventy VS Code Terminal API.

```
Events:
- onDidCloseTerminal → cleanup: oznacz agenta jako stopped w DB
- onDidOpenTerminal  → register: aktualizuj terminal_name
- onDidChangeActiveTerminal → UI update (opcjonalnie)
```

### 2.4 Commands (VS Code Command Palette)

| Command | Opis | Faza |
|---|---|---|
| `mrowisko.spawnAgent` | Quick pick: rola → task → spawn | 1 |
| `mrowisko.listAgents` | Pokaż żywych agentów (z DB) | 1 |
| `mrowisko.stopAgent` | Zamknij terminal wybranego agenta | 1 |
| `mrowisko.approveSpawn` | Zatwierdzenie auto-spawnu | 2 |
| `mrowisko.requestSpawn` | Agent żąda spawnu innego agenta | 2 |

---

## 3. Domain Model

```
┌────────────┐     ┌────────────┐
│  Session   │     │  Terminal   │
│            │     │            │
│ session_id │     │ terminal_id│
│ role       │     │ name       │
│ name       │     │ window     │
│ resumable  │     │ ephemeral  │
└─────┬──────┘     └─────┬──────┘
      │                  │
      └────────┬─────────┘
               │
        ┌──────▼──────┐
        │  LiveAgent   │
        │              │
        │ = Session    │
        │ + Terminal   │
        │ + status     │
        │ + task       │
        │ + spawned_by │
        └──────────────┘

┌────────────┐
│ Invocation │
│            │
│ invoker    │──→ LiveAgent | Human
│ target     │──→ Role
│ task       │
│ status     │
│ approval   │
└────────────┘
```

**Lifecycle LiveAgent:**
```
starting → active → stopped
                 ↑
                 │ (SessionStart hook)
```

---

## 4. Data Flow

### 4.1 Ręczny spawn (Faza 1)

```
Human → Command Palette → mrowisko.spawnAgent
    │
    ▼
Quick Pick: wybierz rolę
    │
    ▼
Input Box: wpisz task
    │
    ▼
Spawner:
    1. uuid = crypto.randomUUID()
    2. DB INSERT live_agents(session_id=uuid, role, task, status='starting')
    3. terminal = createTerminal({name: "Agent: {role}", location: Editor})
    4. terminal.sendText('claude --name "Agent-{role}" --session-id "{uuid}" --append-system-prompt "..."')
    5. terminal.sendText('{role}, {task}')
    │
    ▼
Claude Code startuje → SessionStart hook → DB UPDATE status='active'
    │
    ▼
Agent pracuje... Human może wejść w terminal i pisać
    │
    ▼
Agent kończy → SessionEnd hook → DB UPDATE status='stopped', stopped_at=now()
    │
    ▼
Terminal zamknięty → onDidCloseTerminal → cleanup
```

### 4.2 Agent-to-agent invocation (Faza 2)

```
Agent A (w workflow) → agent_bus send --to <rola> --content-file tmp/task.md
    │
    ▼
agent_bus INSERT invocations(invoker='agent', target_role, task, status='pending')
    │
    ▼
Wtyczka (poll invocations) → wykrywa pending
    │
    ▼
[Approval gate] → Human zatwierdza (Faza testów) / auto-approve (zaufane pary)
    │
    ▼
Spawner → nowy terminal → Claude Code → SessionStart hook
    │
    ▼
Agent B pracuje → kończy → wysyła wynik do Agent A
```

---

## 5. Struktura plików

```
extensions/mrowisko-terminal-control/
├── package.json           ← manifest wtyczki, commands, configuration
├── tsconfig.json
├── src/
│   ├── extension.ts       ← activate/deactivate, command registration
│   ├── spawner.ts         ← SpawnRequest → Terminal + DB
│   ├── registry.ts        ← LiveAgent CRUD (better-sqlite3)
│   ├── watcher.ts         ← Terminal API event handlers
│   ├── commands.ts        ← Command implementations
│   └── types.ts           ← LiveAgent, SpawnRequest, etc.
├── test/
│   └── suite/
│       └── extension.test.ts
└── README.md

tools/hooks/
├── on_session_start.py    ← NOWY: live_agents INSERT
├── on_stop.py             ← ROZSZERZENIE: live_agents UPDATE last_activity
└── on_session_end.py      ← NOWY: live_agents UPDATE status=stopped
```

---

## 6. Konfiguracja wtyczki (package.json)

```json
{
    "contributes": {
        "commands": [
            { "command": "mrowisko.spawnAgent", "title": "Mrowisko: Spawn Agent" },
            { "command": "mrowisko.listAgents", "title": "Mrowisko: List Agents" },
            { "command": "mrowisko.stopAgent", "title": "Mrowisko: Stop Agent" }
        ],
        "configuration": {
            "title": "Mrowisko Agent Launcher",
            "properties": {
                "mrowisko.dbPath": {
                    "type": "string",
                    "default": "mrowisko.db",
                    "description": "Path to mrowisko.db"
                },
                "mrowisko.defaultPermissionMode": {
                    "type": "string",
                    "enum": ["default", "acceptEdits", "plan", "bypassPermissions"],
                    "default": "default",
                    "description": "Default permission mode for spawned agents"
                },
                "mrowisko.pollIntervalMs": {
                    "type": "number",
                    "default": 5000,
                    "description": "Registry poll interval (ms)"
                },
                "mrowisko.terminalLocation": {
                    "type": "string",
                    "enum": ["editor", "panel"],
                    "default": "editor",
                    "description": "Where to open agent terminals"
                }
            }
        }
    }
}
```

---

## 7. Plan implementacji

### Milestone 1: Spawn + Registry (Faza 1)

| # | Task | Pliki | Zależność |
|---|---|---|---|
| M1.1 | Tabele `live_agents` + `invocations` w agent_bus.py | agent_bus.py | — |
| M1.2 | `types.ts` + `registry.ts` (better-sqlite3) | src/ | M1.1 |
| M1.3 | `spawner.ts` (createTerminal + sendText + DB insert) | src/ | M1.2 |
| M1.4 | `commands.ts` (spawnAgent, listAgents, stopAgent) | src/ | M1.3 |
| M1.5 | `watcher.ts` (onDidCloseTerminal → cleanup) | src/ | M1.2 |
| M1.6 | `extension.ts` (activate: register commands + watcher) | src/ | M1.4, M1.5 |
| M1.7 | Hook `on_session_start.py` | tools/hooks/ | M1.1 |
| M1.8 | Hook `on_session_end.py` + rozszerzenie `on_stop.py` | tools/hooks/ | M1.1 |
| M1.9 | Testy manualne + fix PoC | — | M1.6, M1.7, M1.8 |

### Milestone 2: Invocation (Faza 2)

| # | Task |
|---|---|
| M2.1 | CLI: `agent_bus_cli.py spawn-request` — agent żąda spawnu |
| M2.2 | Wtyczka: poll `invocations` table, approval gate UI |
| M2.3 | Hooki: SubagentStart/SubagentStop |
| M2.4 | Multi-window: każda instancja polluje, spawni lokalnie |

### Milestone 3: Orkiestracja (Faza 3)

| # | Task |
|---|---|
| M3.1 | Rola orkiestratora — prompt + workflow |
| M3.2 | Auto-spawn z backlogu |
| M3.3 | Status dashboard (VS Code panel) |
| M3.4 | Stress test: 10+ agentów naraz |

---

## 8. Decyzje architektoniczne

| # | Decyzja | Alternatywa | Uzasadnienie |
|---|---|---|---|
| D1 | CLI spawn (nie Agent SDK) | Agent SDK | CLI = pełna interaktywność, slash commands, status line |
| D2 | `live_agents` osobna tabela | Rozszerzenie `sessions` | Różne lifecycle: sessions=trwała historia, live_agents=runtime |
| D3 | Polling DB (nie IPC) | WebSocket/IPC między oknami | Prostsze, mrowisko.db już współdzielona, WAL mode |
| D4 | `better-sqlite3` (nie async) | node-sqlite3 | Sync API prostsze w extensions, brak callback hell |
| D5 | `TerminalLocation.Editor` default | Panel (dół) | User chce terminale obok siebie pionowo |
| D6 | Permission mode konfigurowalne | Hardcoded default | User oczekuje elastyczności per spawn |
| D7 | UUID4 generowany przed spawnem | Claude generuje session_id | Pre-registration w registry zanim agent wystartuje |
