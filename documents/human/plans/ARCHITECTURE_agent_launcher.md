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

Registry komunikuje się z mrowisko.db przez **Python bridge** (`tools/agent_launcher_db.py`
wywoływany przez `execFileSync`). `better-sqlite3` odrzucony — ABI mismatch z Electron.

Hooki **piszą** do registry (SessionStart/Stop/SessionEnd) bezpośrednio przez `sqlite3` (Python stdlib).

### 2.3 Watcher

Odpowiedzialność: reagowanie na eventy VS Code Terminal API.

```
Events:
- onDidCloseTerminal → cleanup: oznacz agenta jako stopped w DB
- onDidOpenTerminal  → register: aktualizuj terminal_name
- onDidChangeActiveTerminal → UI update (opcjonalnie)
```

### 2.4 URI Handler (CLI → Extension bridge)

Agenci i człowiek mogą sterować wtyczką z terminala przez URI:

```bash
code --open-url "vscode://mrowisko.mrowisko-terminal-control?command=spawnAgent&role=developer&task=check+backlog"
code --open-url "vscode://mrowisko.mrowisko-terminal-control?command=listAgents"
code --open-url "vscode://mrowisko.mrowisko-terminal-control?command=stopAgent&sessionId=UUID"
```

**Uwaga Windows:** `code.cmd` interpretuje `&` jako separator. Używaj `Code.exe` bezpośrednio lub URL-encode.

To jest kluczowy mechanizm: daje agentom dostęp do GUI wtyczki bez interakcji z UI. Agent w terminalu wywołuje URI → wtyczka reaguje.

### 2.5 Commands (VS Code Command Palette)

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

**Wariant A: Direct URI (zaufane pary)**
```
Agent A (w workflow) → code --open-url "vscode://mrowisko...?command=spawnAgent&role=developer&task=..."
    │
    ▼
URI handler → Spawner → nowy terminal → Claude Code → SessionStart hook
    │
    ▼
Agent B pracuje → kończy → wysyła wynik do Agent A
```

**Wariant B: Approval gate (faza testów)**
```
Agent A → agent_bus INSERT invocations(status='pending')
    │
    ▼
Wtyczka (poll invocations) → wykrywa pending → pokazuje approval dialog
    │
    ▼
Human zatwierdza → URI handler → Spawner → terminal
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
│   ├── registry.ts        ← LiveAgent CRUD (Python bridge via execFileSync)
│   ├── watcher.ts         ← Terminal API event handlers
│   ├── commands.ts        ← Command implementations
│   └── types.ts           ← LiveAgent, SpawnRequest, etc.
├── test/
│   └── suite/
│       └── extension.test.ts
└── README.md

tools/
├── agent_launcher_db.py   ← Python bridge: CRUD live_agents (wywoływany przez registry.ts)
└── hooks/
    ├── on_session_start.py    ← live_agents UPDATE starting→active (tylko spawned agents)
    ├── on_stop.py             ← ROZSZERZENIE: live_agents UPDATE last_activity
    └── on_session_end.py      ← live_agents UPDATE status=stopped
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
| M1.2 | `types.ts` + `registry.ts` (Python bridge) + `agent_launcher_db.py` | src/, tools/ | M1.1 |
| M1.3 | `spawner.ts` (createTerminal + sendText + DB insert) | src/ | M1.2 |
| M1.4 | `commands.ts` (spawnAgent, listAgents, stopAgent) | src/ | M1.3 |
| M1.5 | `watcher.ts` (onDidCloseTerminal → cleanup) | src/ | M1.2 |
| M1.6 | `extension.ts` (activate: register commands + watcher) | src/ | M1.4, M1.5 |
| M1.7 | Hook `on_session_start.py` | tools/hooks/ | M1.1 |
| M1.8 | Hook `on_session_end.py` + rozszerzenie `on_stop.py` | tools/hooks/ | M1.1 |
| M1.9 | URI handler (CLI → Extension bridge) | src/extension.ts | M1.6 |
| M1.10 | Testy via URI handler + fix | — | M1.9 |

### Milestone 1: STATUS — DONE ✓

Commit: `9ac9a48`, `411bcad`, `cdc8a11`. Testy manualne PASS. Code review PASS (L3 Senior).

### Milestone 2: Invocation (Faza 2)

| # | Task | Opis |
|---|---|---|
| M2.1 | CLI spawn helper | Skrypt/komenda `agent_bus_cli.py spawn` budujący URI i wywołujący `code --open-url`. Agent z terminala spawni innego agenta. |
| M2.2 | Invocation tracking | `agent_bus_cli.py spawn` zapisuje do `invocations` table (kto, kogo, kiedy, status). |
| M2.3 | Approval gate (wariant B) | Wtyczka polluje `invocations` (status=pending) → dialog zatwierdzenia → spawn via URI. Konfigurowalne: auto-approve dla zaufanych par. |
| M2.4 | Workflow invocation | Agent w workflow może wywołać innego agenta bezpośrednio (wariant A — direct URI, bez approval). |
| M2.5 | Windows helper | Rozwiązanie problemu `code.cmd` vs `Code.exe` + `&` w URI na PowerShell. |

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
| D4 | Python bridge (nie better-sqlite3) | better-sqlite3, node-sqlite3 | better-sqlite3 ABI mismatch z Electron. Python bridge reużywa infrastrukturę, zero native deps. Async w Fazie 3. |
| D5 | `TerminalLocation.Editor` default | Panel (dół) | User chce terminale obok siebie pionowo |
| D6 | Permission mode konfigurowalne | Hardcoded default | User oczekuje elastyczności per spawn |
| D7 | UUID4 generowany przed spawnem | Claude generuje session_id | Pre-registration w registry zanim agent wystartuje |
| D8 | URI handler (nie `code --command`) | `code --command` nie istnieje | URI handler daje agentom pełny dostęp do wtyczki z terminala. Kluczowy mechanizm dla Fazy 2. |
| D9 | Manual sessions nie w live_agents | Rejestruj wszystko | Tylko spawned agents trackowane. Ręczne sesje nie zaśmiecają registry. |
