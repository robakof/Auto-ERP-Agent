# Plan: Dispatcher agent lifecycle — stop + resume

## Problem
Dispatcher nie ma CLI do zamykania i wznawiania agentów. Bez tego nie zarządza lifecycle.

## Istniejąca infrastruktura

| Co | Gdzie | Status |
|---|---|---|
| stopAgent URI handler | extension.ts:80-90 | Istnieje, matchuje po sessionId z terminals map |
| terminals map | extension spawner | Keyed po spawner UUID (nie nasz session_id) |
| terminal_name | live_agents DB | "Agent: {role}" — stabilny identyfikator |
| pokeAgent | extension.ts:58-75 | Matchuje po terminalName — działa |
| vscode_uri.py | tools/ | Obsługuje stopAgent z --session-id |

## Problem z stopAgent
Extension stopAgent matchuje po `sessionId` w `terminals` map. Spawner UUID ≠ nasz session_id ≠ claude_uuid.
Po session_init spawner UUID znika z DB. Nikt nie wie jaki key jest w terminals map.

## Rozwiązanie

### 1. Extension: stopAgent matchuje po terminalName (jak pokeAgent)
Dodaj alternatywny path: jeśli `terminalName` w params → findTerminal by name → dispose.

### 2. Extension: resumeAgent — nowa komenda
Szuka terminala po terminalName:
- Terminal istnieje → sendText("/resume")
- Terminal nie istnieje → createTerminal + sendText("claude --resume")

### 3. CLI: agent_bus_cli `stop` i `resume`
```
py tools/agent_bus_cli.py stop --session-id <id>
  → lookup terminal_name z live_agents
  → vscode_uri.py --command stopAgent --terminal-name <name>
  → markStopped w DB

py tools/agent_bus_cli.py resume --session-id <id>
  → lookup terminal_name z live_agents
  → vscode_uri.py --command resumeAgent --terminal-name <name>
```

### 4. vscode_uri.py: --command resumeAgent
Dodaj obsługę nowej komendy.

## Zakres zmian
1. `extension.ts` — stopAgent: dodaj terminalName path. Nowa komenda resumeAgent (~15 linii)
2. `agent_bus_cli.py` — nowe komendy `stop` i `resume` (~40 linii łącznie)
3. `vscode_uri.py` — bez zmian (--terminal-name już obsługiwane)

## Exit gate
- [ ] CLI stop zamyka agenta
- [ ] CLI resume wznawia agenta
- [ ] Extension stopAgent matchuje po terminalName
- [ ] Extension resumeAgent istnieje
- [ ] Test end-to-end z Dispatcherem: spawn → stop → resume → live-agents
