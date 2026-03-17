# Research prompt — Mrowisko Runner Faza 1b (instance routing)

## Kontekst

Budujemy `tools/mrowisko_runner.py` — skrypt Python który:
1. Rejestruje się w SQLite (`mrowisko.db`) jako instancja roli (np. `erp_specialist:a1b2c3`)
2. Czyta inbox (tabela `messages`) i wywołuje agentów przez `claude -p "..."` subprocess
3. Wiele runnerów tej samej roli może działać równolegle — potrzebujemy atomic claim taska

Istniejący kod (Faza 1):
- `tools/mrowisko_runner.py` — subprocess `claude -p`, stream-json rendering
- `tools/lib/agent_bus.py` — SQLite wrapper z WAL mode
- `tools/agent_bus_cli.py` — CLI do wysyłania/odbierania wiadomości

Plan Fazy 1b: `documents/dev/mrowisko_runner_instance_routing.md`

---

## Pytania do zbadania

### 1. SQLite atomic claim przy WAL mode

Plan używa:
```sql
UPDATE messages SET status = 'claimed', claimed_by = ?
WHERE id = ? AND status = 'unread'
```
Potem sprawdzamy `cursor.rowcount` — jeśli 0, inny runner zdążył.

**Pytania:**
- Czy SQLite z `PRAGMA journal_mode=WAL` gwarantuje że dwa równoległe procesy nie zapiszą obu `claimed_by` dla tego samego wiersza? (race condition)
- Czy potrzebujemy `BEGIN IMMEDIATE` lub `BEGIN EXCLUSIVE` dla tej operacji?
- Czy `check_same_thread=False` w `sqlite3.connect()` jest wystarczające przy wielu procesach (nie wątkach), każdy ze swoim połączeniem?

### 2. Claude Code CLI — weryfikacja flag

Poprzedni research (id=45) potwierdził `-p` jako poprawną flagę.

Zweryfikuj czy poniższe flagi istnieją i działają zgodnie z założeniami:

```bash
claude -p "prompt" \
  --output-format stream-json \
  --verbose \
  --include-partial-messages \
  --max-turns 8 \
  --max-budget-usd 1.50 \
  --permission-mode acceptEdits \
  --tools "Read,Grep,Glob,Bash"
```

**Pytania:**
- Czy `--permission-mode acceptEdits` istnieje? Jakie są dostępne wartości?
- Czy `--tools "Read,Grep,Glob,Bash"` faktycznie ogranicza capability boundary? Jaki jest dokładny format (przecinek bez spacji, czy inaczej)?
- Czy `--max-budget-usd` istnieje jako flaga, czy to tylko wewnętrzny mechanizm?
- Czy `--include-partial-messages` jest wymagane przy `stream-json` czy opcjonalne?

### 3. Heartbeat w Pythonie — threading przy subprocess

Runner musi wysyłać heartbeat co 10s do SQLite (`UPDATE agent_instances SET last_seen_at = datetime('now') WHERE instance_id = ?`) **podczas gdy** główny wątek czeka na zakończenie subprocess (`proc.wait(timeout=600)`).

**Pytania:**
- Czy `threading.Timer` (rekurencyjny) jest właściwym narzędziem, czy lepiej `threading.Thread` z pętlą + `Event.wait(10)`?
- Czy SQLite connection może być współdzielona między wątkiem heartbeat a wątkiem głównym przy `check_same_thread=False`? Czy bezpieczniej tworzyć osobne połączenie per wątek?
- Czy jest prostszy pattern (np. `concurrent.futures`) dla tego scenariusza?

### 4. Cleanup przy nagłym zamknięciu terminala

Runner powinien wyrejestrować instancję (`status = 'terminated'`) gdy terminal zostanie zamknięty lub proces zabity.

**Pytania:**
- Czy `signal.signal(signal.SIGTERM, handler)` + `atexit.register()` pokrywa przypadek zamknięcia terminala na Windows?
- Czy na Windows `SIGTERM` jest w ogóle wysyłany przy zamknięciu okna CMD/PowerShell?
- Jaki jest rekomendowany pattern cleanup dla długo działającego skryptu Python na Windows?

---

## Plik odpowiedzi

Zapisz wyniki do: `documents/dev/research_results_runner_faza1b.md`

Format na każde pytanie:
```
## [numer pytania] Tytuł

Odpowiedź: ...
Źródło: ...
Rekomendacja dla implementacji: ...
```

Jeśli nie możesz znaleźć odpowiedzi — napisz wprost: "Nie znaleziono — wymaga testu lokalnego."
