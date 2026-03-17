# Mrowisko Runner — Plan implementacji

## Cel

Skrypt `tools/mrowisko_runner.py` który czyta inbox wybranej roli i wywołuje agentów
jako subprocess Claude Code CLI. Człowiek widzi działanie agenta w terminalu w czasie
rzeczywistym i zatwierdza każde wywołanie.

---

## Architektura

```
agent_bus (inbox)
       ↓
 runner.py (poller)
       ↓
  approval gate  ← człowiek zatwierdza / odrzuca
       ↓
 subprocess: claude -p "$TASK_PROMPT" --output-format stream-json ...
       ↓
 session_log (wynik + session_id)
       ↓
 agent_bus (odpowiedź do nadawcy)
```

---

## Mechanizmy kontroli (zawsze aktywne)

| Zabezpieczenie | Realizacja |
|---|---|
| `max_turns` | `--max-turns 8` (flaga CLI) |
| `max_budget_usd` | `--max-budget-usd 1.50` (flaga CLI) |
| `timeout` | wall-clock timeout w runnerze (subprocess.wait(timeout=600)) |
| `max_depth` | każdy task niesie `depth` w DB — blokada przy depth > 3 |
| `no_escalation` | runner odmawia wywołania roli o wyższych uprawnieniach niż nadawca |
| `loop_guard` | `parent_session_id` w SQLite — blokuje jeśli task pochodzi z sesji w łańcuchu |
| `tool_scope` | `--tools` ogranicza capability boundary per rola agenta |

---

## Poziomy autonomii

```
REQUIRE_HUMAN  — runner pyta przed każdym wywołaniem (domyślne dla wszystkich par)
AUTO           — runner odpala bez pytania (po whitelistowaniu)
DENY           — zawsze blokowane
```

Tabela `invocation_policy` w DB: `from_role`, `to_role`, `task_type`, `policy`.
Start: wszystkie pary → `REQUIRE_HUMAN`. Whitelist po N udanych wywołaniach.

---

## Fazy implementacji

### Faza 1 — PoC z approval gate (zakres bieżący)

**Cel:** mechanizm działa, człowiek zatwierdza każde wywołanie ręcznie.

**Zakres:**
1. `tools/mrowisko_runner.py` — CLI: `python tools/mrowisko_runner.py --role erp_specialist`
2. Czyta inbox wybranej roli (filtr: typ `task`)
3. Dla każdego taska: wyświetla nadawcę, treść, pyta `[Y/n]`
4. Po zatwierdzeniu: wywołuje agenta
5. Wynik zapisuje przez `agent_bus_cli.py log`
6. Opcjonalnie odsyła odpowiedź do nadawcy przez `agent_bus send`

**Nie ma w Fazie 1:**
- Daemon / polling w tle
- Tabela `invocation_policy` (decyzja człowieka przy każdym wywołaniu)
- Auto-przekazywanie wyniku do kolejnego agenta

**Output w terminalu:**
```
[RUNNER] Rola: erp_specialist | Oczekujące taski: 2

[1/2] Od: developer | Temat: Zbuduj widok TwrKarty
Treść: Zbuduj widok BI dla kartoteki towarowej. Eksportuj do solutions/bi/views/.
Invoke? [Y/n]: Y

→ Uruchamiam agenta... (Ctrl+C aby przerwać)
[agent output pojawia się tu w czasie rzeczywistym — stream-json renderowany jako tekst]
→ Zakończono. session_id: abc-123. Koszt: $0.42. Turns: 6/8.
```

### Faza 2 — Whitelist + policy engine

Tabela `invocation_policy`. Komenda:
```
python tools/mrowisko_runner.py --whitelist erp_specialist analyst
```

### Faza 3 — Daemon

Polling inbox co N sekund, auto-run dla whitelistowanych par,
REQUIRE_HUMAN dla pozostałych (notyfikacja Telegram lub terminal).

---

## Szczegóły techniczne — Faza 1

### Wywołanie agenta (korekta po researchu)

```python
import subprocess, json

cmd = [
    "claude", "-p", task_prompt,
    "--output-format", "stream-json",
    "--verbose",
    "--include-partial-messages",
    "--max-turns", "8",
    "--max-budget-usd", "1.50",
    "--tools", tool_scope,          # np. "Read,Grep,Glob,Bash"
    "--allowedTools", auto_approved, # np. "Read,Grep,Glob"
]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
output_lines = []

for line in proc.stdout:
    try:
        event = json.loads(line)
        # renderuj tekst z event dla człowieka
        if event.get("type") == "stream_event":
            delta = event.get("event", {}).get("delta", {})
            if delta.get("type") == "text_delta":
                print(delta["text"], end="", flush=True)
    except json.JSONDecodeError:
        print(line, end="")
    output_lines.append(line)

proc.wait(timeout=600)
```

### Prompt przekazywany agentowi

```
[TASK od: {from_role}]
{task_content}
```

Agent dostaje treść zadania — `session_init` uruchamia rolę z CLAUDE.md jak w normalnej sesji.

### Tracking sesji w SQLite

```sql
-- tabela invocation_log (nowa)
session_id TEXT, parent_session_id TEXT, from_role TEXT, to_role TEXT,
task_id INT, depth INT, turns INT, cost_usd REAL, status TEXT, created_at TEXT
```

`--session-id` Claude Code CLI: runner może przypisać własne UUID lub odczytać
session_id z eventu `system` w stream-json output i zapisać do DB.

### Tool scope per rola

| Rola | `--tools` |
|---|---|
| erp_specialist | `Read,Grep,Glob,Bash` |
| analyst | `Read,Grep,Glob` |
| developer | `Read,Grep,Glob,Bash,Write,Edit` |

### Zależności

- Claude Code CLI (`claude`) dostępne w PATH
- `agent_bus_cli.py` do odczytu inbox i zapisu log
- Brak nowych bibliotek

---

## Otwarte kwestie do decyzji przed implementacją

1. **`--permission-mode`** dla child agentów — `default` (pyta o każde nowe uprawnienie)
   czy `acceptEdits` (auto-zatwierdza edycje plików)?
   Rekomendacja: `acceptEdits` dla ERP Specialist (tylko reads + SQL writes w solutions/).

2. **Worktrees dla równoległości** — Faza 1 jest sekwencyjna więc nieistotne.
   Faza 3 (daemon): każdy agent w osobnym worktree żeby unikać konfliktów plików.

3. **Jak renderować stream-json dla człowieka** — tylko text_delta (czytelne)
   czy pełne eventy z tool_use (więcej info, więcej szumu)?
   Rekomendacja: text_delta domyślnie, `--verbose-runner` dla pełnych eventów.
