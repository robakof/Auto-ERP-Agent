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
 subprocess: claude --print ... < task_prompt
       ↓
 session_log (wynik)
       ↓
 agent_bus (odpowiedź do nadawcy)
```

---

## Mechanizmy kontroli (zawsze aktywne)

| Zabezpieczenie | Opis |
|---|---|
| `max_depth` | Każda invokacja niesie `depth` — blokada przy depth > 3 |
| `no_escalation` | Agent nie może wywołać roli o wyższych uprawnieniach |
| `loop_guard` | `parent_session_id` — blokuje jeśli task pochodzi z sesji w tym samym łańcuchu |
| `token_budget` | Max tokeny na łańcuch wywołań (konfigurowalny) |
| `timeout` | Max czas na wywołanie (domyślnie 10 min) |

---

## Poziomy autonomii (tabela `invocation_policy` w DB)

```
REQUIRE_HUMAN  — runner pyta przed każdym wywołaniem (domyślne dla nowych par)
AUTO           — runner odpala bez pytania (po whitelistowaniu)
DENY           — zawsze blokowane
```

Kolumny: `from_role`, `to_role`, `task_type`, `policy`, `approved_by`, `approved_at`

Start: wszystkie pary → `REQUIRE_HUMAN`.
Whitelist po N udanych wywołaniach weryfikowanych przez człowieka.

---

## Fazy implementacji

### Faza 1 — PoC z approval gate (zakres bieżący)

**Cel:** mechanizm działa, człowiek zatwierdza każde wywołanie.

**Zakres:**
1. `tools/mrowisko_runner.py` — CLI: `python tools/mrowisko_runner.py --role erp_specialist`
2. Czyta inbox wybranej roli (filtr: typ `task`)
3. Dla każdego taska: wyświetla nadawcę, treść, pyta `[Y/n]`
4. Po zatwierdzeniu: buduje prompt systemowy (rola + treść zadania), wywołuje:
   ```
   claude --print --output-format text < tmp/runner_prompt.md
   ```
5. Wynik zapisuje do `session_log` przez `agent_bus_cli.py log`
6. Opcjonalnie odsyła odpowiedź do nadawcy przez `agent_bus send`

**Nie ma w Fazie 1:**
- Daemon / polling w tle
- Tabel `invocation_policy` (decyzja człowieka przy każdym wywołaniu)
- Przekazywanie wyniku do kolejnego agenta automatycznie

**Output w terminalu:**
```
[RUNNER] Rola: erp_specialist | Oczekujące taski: 2

[1/2] Od: developer | Temat: Zbuduj widok TwrKarty
Treść: Zbuduj widok BI dla kartoteki towarowej. Eksportuj do solutions/bi/views/.
Invoke? [Y/n]: Y

→ Uruchamiam agenta... (Ctrl+C aby przerwać)
[agent output pojawia się tu w czasie rzeczywistym]
→ Zakończono. Zapisano log sesji.
```

### Faza 2 — Whitelist + policy engine

Tabela `invocation_policy`. Komenda do whitelistowania pary:
```
python tools/mrowisko_runner.py --whitelist erp_specialist analyst
```

### Faza 3 — Daemon

Daemon polling inbox co N sekund, auto-run dla whitelistowanych par,
REQUIRE_HUMAN dla pozostałych (notyfikacja w terminalu lub Telegram).

---

## Szczegóły techniczne — Faza 1

### Wywołanie agenta

```python
# Budowanie promptu
prompt = build_prompt(role, task_content)  # rola + treść zadania
Path("tmp/runner_prompt.md").write_text(prompt)

# Subprocess z live output
proc = subprocess.Popen(
    ["claude", "--print", "--output-format", "text"],
    stdin=open("tmp/runner_prompt.md"),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
output_lines = []
for line in proc.stdout:
    print(line, end="")       # live output w terminalu
    output_lines.append(line)
proc.wait()
output = "".join(output_lines)
```

### Prompt budowany przez runnera

```
[TASK od: {from_role}]
{task_content}
```

Agent dostaje treść zadania jako pierwszy komunikat — session_init wywoła rola z CLAUDE.md jak w normalnej sesji.

### Zależności

- Claude Code CLI zainstalowane i dostępne jako `claude` w PATH
- `agent_bus_cli.py` do odczytu inbox i zapisu log
- Brak nowych bibliotek

---

## Otwarte pytania (do weryfikacji przez Researchera)

1. Czy `claude --print < prompt` poprawnie inicjalizuje sesję z CLAUDE.md hooks?
2. Czy subprocess Popen daje live streaming output czy buforuje?
3. Czy istnieje `--session-id` flag w Claude Code CLI do linkowania sesji parent→child?
4. Jakie są best practices multi-agent orchestration z Claude Code CLI?
5. Czy jest lepszy mechanizm przekazania kontekstu agentowi niż plik tymczasowy?
