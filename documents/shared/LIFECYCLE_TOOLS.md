# Lifecycle agentów — narzędzia i model tożsamości

Dokumentacja mechanizmów zarządzania cyklem życia agentów w mrowisku.
Dotyczy: Dyspozytor (obowiązkowy), Developer, Architect, Prompt Engineer (referencyjny).

---

## Model tożsamości agenta

Każdy agent w mrowisku ma trzy identyfikatory:

| Identyfikator | Źródło | Kiedy powstaje | Użycie |
|---|---|---|---|
| `spawn_token` | `crypto.randomUUID()` w VS Code | Przy spawn (przed startem agenta) | Linkowanie pre-registered record z sesją |
| `claude_uuid` | Claude Code (session_id) | Przy starcie sesji Claude | Primary identity — identyfikuje konwersację |
| `session_id` | `session_init.py` (skrót) | Przy session_init agenta | Identyfikator w mrowisko.db, używany w CLI |

**Flow:**
1. `spawn` → extension generuje `spawn_token`, pre-rejestruje w `live_agents` (status: `starting`)
2. Terminal startuje z env var `MROWISKO_SPAWN_TOKEN=<spawn_token>`
3. Claude Code startuje → hook `on_session_start` odczytuje `MROWISKO_SPAWN_TOKEN`
4. Hook linkuje `spawn_token` ↔ `claude_uuid` w DB → status: `active`
5. `session_init` generuje `session_id` (skrót) → agent gotowy

Sesje ręczne (bez spawn): hook wstawia rekord z `claude_uuid` bezpośrednio (brak `spawn_token`).

---

## Komendy CLI — agent_bus_cli.py

### Spawn — uruchomienie nowego agenta

```
py tools/agent_bus_cli.py spawn --from dispatcher --role <rola> --task "opis zadania"
```

Tworzy terminal w VS Code, ustawia `MROWISKO_SPAWN_TOKEN` env var,
pre-rejestruje agenta w `live_agents` (status: `starting`).
Gdy agent uruchomi `session_init`, `spawn_token` linkuje się z `claude_uuid` → status: `active`.

Opcjonalny parametr: `--permission-mode <mode>` (override domyślnego trybu uprawnień).

### Stop — zatrzymanie żywego agenta

```
py tools/agent_bus_cli.py stop --session-id <session_id>
```

Wysyła `/exit` do terminala agenta, ustawia status: `stopped` w DB.
`session_id` bierzesz z `live-agents`.

### Resume — wznowienie zatrzymanego agenta

```
py tools/agent_bus_cli.py resume --session-id <session_id>
```

Tworzy nowy terminal z `claude --resume <claude_uuid>`.
Agent odzyskuje pełny kontekst konwersacji. `session_id` = ten sam co przy stop.

### Poke — wiadomość do żywego agenta

```
py tools/agent_bus_cli.py poke --from <rola> --role <rola_docelowa> --message "treść"
py tools/agent_bus_cli.py poke --from <rola> --role <rola_docelowa> --message-file tmp/poke.md
```

Wysyła wiadomość do żywego agenta. Agent widzi ją jako deny z prefixem
`[POKE od <rola>]` przy następnym Bash tool call.

Zastosowania:
- Dyspozytor → agent: "wyślij status", "przerwij zadanie", "sprawdź inbox"
- Workflow auto-poke: automatyczna wymiana między sparowanymi rolami (np. ERP ↔ Analityk)

Ograniczenia techniczne:
- Poke dociera przy następnym Bash tool call (nie natychmiast)
- Jeden poke na raz (starszy nadpisany nowszym)
- Brak gwarancji przetworzenia — prompt-only mechanism

### Monitoring

```
py tools/agent_bus_cli.py live-agents
  → Lista aktywnych agentów (role, status, session_id, claude_uuid, task)

py tools/agent_bus_cli.py invocations --status running
  → Tracking spawnionych agentów

py tools/agent_bus_cli.py invocations --status completed
  → Ostatnie zakończone sesje
```

---

## VS Code URI handler — vscode_uri.py

Bezpośredni dostęp do extensiona VS Code (bez trackingu w DB).
Preferuj `agent_bus_cli.py` (spawn/stop/resume/poke) — opakowuje `vscode_uri.py`
i dodaje tracking w DB.

```
py tools/vscode_uri.py --command spawnAgent --role <rola> --task "opis"
py tools/vscode_uri.py --command stopAgent --session-id <UUID>
py tools/vscode_uri.py --command resumeAgent --session-id <UUID> --claude-uuid <UUID>
py tools/vscode_uri.py --command pokeAgent --terminal-name "Agent: rola" --message "tekst"
py tools/vscode_uri.py --command listAgents
py tools/vscode_uri.py --command reload
```

Bezpośrednie użycie `vscode_uri.py` tylko gdy potrzebujesz `reload` lub `listAgents`
(brak wrappera w `agent_bus_cli.py`).
