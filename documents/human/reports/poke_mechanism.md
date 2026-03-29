# Mechanizm Poke — jak działa komunikacja z żywym agentem

## Czym jest poke

Poke to **budzik z drogowskazem** — budzi stojącego agenta i wskazuje mu konkretne zadanie
(backlog item lub wiadomość). Nie jest typem wiadomości, jest typem interakcji między agentami.

Poke NIE przeszkadza pracującemu agentowi. Pracujący agent jest w workflow, w swojej
przestrzeni koncentracji. Poke czeka aż agent skończy.

## Typy interakcji poke

| Typ | Kiedy | Efekt |
|---|---|---|
| **poke** | Agent stoi (idle) | Budzi agenta, wskazuje zadanie |
| **poke** | Agent pracuje | Czeka aż agent skończy, dopiero wtedy dostarczany |
| **poke-stop** | Agent pracuje (sytuacja awaryjna) | Przerywa pracę agenta natychmiast |

## Adresowanie

Poke jest skierowany do **konkretnego żywego agenta** (session_id), nie do roli.
Nadawca (--from) nie jest potrzebny — system sam identyfikuje kto poke'uje na
podstawie sesji wywołującego agenta.

## Zakres — co poke zawiera

Poke nie niesie treści. Niesie **odniesienie**:

```
py tools/agent_bus_cli.py poke --session-id <session_id> --ref backlog:205
py tools/agent_bus_cli.py poke --session-id <session_id> --ref message:461
```

Agent dostaje: "Masz nowe zadanie. Sprawdź backlog #205." lub "Masz wiadomość. Przeczytaj #461."
Sam pobiera szczegóły — nie dostaje ściany tekstu w terminalu.

## Stany agenta i zachowanie poke

| Stan agenta | display_status | Zachowanie poke |
|---|---|---|
| **Stoi (idle)** | stale | sendText do terminala — agent budzi się natychmiast |
| **Pracuje** | working | Poke **czeka**. Dostarczany dopiero gdy agent skończy i wróci do `>` |
| **Martwy** | dead | Poke nie zadziała. Trzeba respawnować (`spawn`) |

## Flow: poke (normalny)

```
1. Dispatcher sprawdza live-agents → widzi agenta (session_id, display_status)
2. Dispatcher: py tools/agent_bus_cli.py poke --session-id <id> --ref backlog:205
3. CLI lookup: SELECT terminal_name FROM live_agents WHERE session_id = ?
4. CLI → vscode_uri.py → extension → terminal.sendText
5. Agent widzi w terminalu:
   "[POKE] Sprawdź backlog #205"
   lub
   "[POKE] Sprawdź wiadomość #461"
6. Agent pobiera szczegóły: py tools/agent_bus_cli.py backlog --id 205
7. Agent realizuje zadanie
```

## Flow: poke-stop (awaryjny)

```
1. Dispatcher widzi że agent robi coś złego (display_status = working)
2. Dispatcher: py tools/agent_bus_cli.py poke-stop --session-id <id> --reason "konflikt z innym agentem"
3. PreToolUse hook przechwytuje następny tool call → DENY
4. Agent zatrzymuje bieżącą pracę
5. Agent czyta powód zatrzymania i eskaluje / czeka na instrukcje
```

## Komenda

```
# Normalny poke — budzi stojącego, czeka na pracującego
py tools/agent_bus_cli.py poke --session-id <id> --ref backlog:<id>
py tools/agent_bus_cli.py poke --session-id <id> --ref message:<id>

# Awaryjny stop — przerywa pracującego
py tools/agent_bus_cli.py poke-stop --session-id <id> --reason "powód"
```

## Co jeszcze nie działa (known gaps)

1. **Ręczne sesje** — sendText wymaga terminal_name. Ręczne sesje go nie mają.
2. **Mechanizm "czekaj aż skończy"** — nie zaimplementowany. Dziś poke dostarczany natychmiast.
3. **Brak instrukcji w promptach** — agenci nie mają w CLAUDE.md instrukcji jak reagować na poke.
   Backlog #200 dla PE.
4. **poke-stop** — nie zaimplementowany. Dziś PreToolUse intercept istnieje ale ma inny interfejs.
