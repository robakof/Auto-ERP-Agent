# Plan: Dispatcher invoke — programistyczne podnoszenie agentów

## Problem
Dyspozytor rejestruje intencję spawnu (invocation record), ale nie może uruchomić sesji.
Po zatwierdzeniu przez człowieka, człowiek musi ręcznie otworzyć terminal.

## Istniejąca infrastruktura
- `vscode_uri.py` — otwiera URI w VS Code (spawnAgent, listAgents, stopAgent)
- `agent_launcher_db.py` — CRUD live_agents + invocations (insert, approve, reject, complete)
- VS Code extension `mrowisko-terminal-control` — obsługuje URI, otwiera terminal

## Proponowane rozwiązanie
Nowa komenda w `agent_bus_cli.py`: `invoke`

### Flow
```
Dyspozytor: py tools/agent_bus_cli.py invoke --role <rola> --task "opis"
  1. Tworzy invocation record (status=pending) w tabeli invocations
  2. Wywołuje vscode_uri.py --command spawnAgent --role <rola> --task "opis"
  3. Zwraca JSON: {ok, invocation_id, uri_sent}
```

### Dlaczego w agent_bus_cli a nie osobne narzędzie
- Dyspozytor już używa agent_bus_cli do wszystkiego
- Jedno narzędzie = mniej do pamiętania
- Invocations table jest już w agent_bus DB

### Zakres zmian
1. `tools/agent_bus_cli.py` — nowa komenda `invoke` (~30 linii)
   - `--role` (required)
   - `--task` (required)
   - `--permission-mode` (optional, default: "default")
2. Testy: test_agent_bus_cli.py lub osobny test

### Czego NIE robimy
- Nie zmieniamy VS Code extension
- Nie zmieniamy vscode_uri.py
- Nie budujemy kolejki / polling — invoke jest jednorazowy fire-and-forget
- Nie budujemy mechanizmu zatwierdzania (approve flow istnieje, ale to osobny topic)

### Exit gate
- [ ] Komenda `invoke` działa
- [ ] Invocation record tworzony w DB
- [ ] URI wysyłany do VS Code
- [ ] Test PASS
