# Plan: Odblokowanie agentów — id=58 + id=24

**Data:** 2026-03-16
**Dotyczy backlog:** id=58 (hook smart fallback), id=24 (newline bug)

---

## Problem

Agenci blokują się na komendach Bash wymagających zatwierdzenia przez człowieka.
Gdy człowiek niedostępny → sesja stoi. Dwa poziomy problemu:

**Poziom 1 (id=24) — bug w matchowaniu wzorców:**
Komenda z wiodącym `\n` (np. `\npython tools/...`) nie matchuje `Bash(python:*)`.
Claude Code generuje klucz z newlinem, allow list go nie łapie → blokada.

**Poziom 2 (id=58) — brak trybu autonomicznego:**
Nawet z idealną allow list, runner wywołujący agenta jako subprocess musi mieć
osobny profil uprawnień — inaczej każda nowa sesja agenta startuje bez pozwoleń.

---

## Rozwiązanie — 3 fazy

### Faza 1: Napraw allow list (mała, natychmiastowa)

**Cel:** Wyeliminować blokady przy normalnej pracy agenta w sesji interaktywnej.

Zmiany w `.claude/settings.local.json`:

1. **Fix newline bug (id=24):** dodać warianty z `\n` dla kluczowych komend
   ```
   "Bash(\npython:*)", "Bash(\npython3:*)", "Bash(\ngit:*)", "Bash(\npytest:*)"
   ```

2. **Luki w obecnej liście** — komendy które blokują agentów a są bezpieczne:
   ```
   "Bash(rm:*)"          — usuwanie plików (np. rm tmp/*)
   "Bash(type:*)"        — Windows odpowiednik cat (rzadki ale blokuje)
   "Bash(echo:*)"        — rzadki, ale pojawia się w pipeline
   "Bash(python -m:*)"   — pytest, pip przez -m module (nie zawsze łapane przez python:*)
   ```

3. **Weryfikacja pokrycia:** po zmianie uruchomić `tools/hooks/check_allow_coverage.py`
   (do zbudowania w tej fazie) który skanuje hook logs i raportuje czy są wzorce
   nie pokryte przez allow list.

**Ryzyko:** żadne — rozszerzamy listę, nie usuwamy.

---

### Faza 2: PreToolUse hook — normalizacja + smart fallback (średnia)

**Cel:** Zamiast statycznej listy wzorców — hook który rozumie komendę.

Claude Code obsługuje hook `PreToolUse` (obok UserPromptSubmit/Stop).
Hook dostaje pełną komendę przed wykonaniem i może:
- Znormalizować (strip leading `\n`, `\t`)
- Sprawdzić komendę przez whitelist logiki (nie tylko prefix match)
- Zamiast blokady: zwrócić odpowiednik bezpieczny (np. sugestię dla agenta)

**Implementacja: `tools/hooks/pre_tool_use.py`**

```
input:  {"tool_name": "Bash", "tool_input": {"command": "..."}}
output: {"decision": "approve"} | {"decision": "block", "message": "użyj X zamiast Y"}
```

Logika:
- Strip `\n` z początku → sprawdź przez wzorce
- `$(...)` w komendzie → block z komunikatem "zapisz do tmp/ i przekaż ścieżkę"
- `python -c "..."` → block z komunikatem "zapisz do tmp/*.py"
- Komenda na whitelist → approve bez blokady

Rejestracja w settings.local.json:
```json
"PreToolUse": [{"hooks": [{"type": "command", "command": "python tools/hooks/pre_tool_use.py"}]}]
```

**Trade-off:** PreToolUse hook może zwolnić każde wywołanie Bash o ~100ms.
Akceptowalne przy obecnej częstości wywołań.

---

### Faza 3: Tryb autonomiczny dla runnera (średnia, zależna od Fazy 2)

**Cel:** Gdy runner wywołuje agenta jako subprocess — agent nie wymaga
żadnych zatwierdzeń człowieka (pełna autonomia dla zaufanych tasków).

**Mechanizm:**
Runner wywołuje agenta przez CLI z flagą `--dangerouslySkipPermissions`:
```
claude --dangerouslySkipPermissions --print "treść zadania"
```
Ta flaga wyłącza cały system uprawnień dla tej sesji.

**Warunki bezpieczeństwa (przed wdrożeniem runnera):**
1. Agent nie może eskalować uprawnień (wywoływać roli wyżej w hierarchii bez zgody)
2. Max N iteracji per task (guard przed pętlą)
3. Każde wywołanie logowane do session_log z `parent_session_id`
4. Zakres operacji ograniczony przez opis taska (agent dostaje tylko to co potrzebuje)

**Uwaga:** Faza 3 sensowna dopiero gdy runner (id=51) jest gotowy.
Bez runnera — Faza 1 + 2 rozwiązują problem dla sesji interaktywnych.

---

## Kolejność implementacji

| Faza | Co | Effort | Unblocks |
|------|----|--------|----------|
| 1 | Fix allow list + check_allow_coverage.py | mała (1h) | natychmiastowe odblokowanie |
| 2 | pre_tool_use.py hook | średnia (3-4h) | trwałe rozwiązanie bez maintenance |
| 3 | --dangerouslySkipPermissions w runnerze | mała (30min) | runner autonomiczny |

**Rekomendacja:** Faza 1 dziś (natychmiastowy efekt), Faza 2 w tej samej sesji jeśli
czas pozwala, Faza 3 przy implementacji runnera.

---

## Otwarte pytania

1. Czy `PreToolUse` hook jest dostępny w obecnej wersji Claude Code? (do weryfikacji)
2. Czy `--dangerouslySkipPermissions` akceptowalny politycznie dla sesji runnera?
   (decyzja użytkownika — trade-off bezpieczeństwo vs autonomia)
3. Jakie komendy blokują najczęściej? (do zbadania przez hook logs przed Fazą 2)
