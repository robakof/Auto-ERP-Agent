# Backlog — 2026-03-23

*5 pozycji*

---

## Wysoka wartość, duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 90 | Architektura synchronizacji bazy danych między maszynami | Arch | wysoka | duza |

## Średnia wartość, mała praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 125 | Napraw failujące testy (State + Suggestions) | Dev | srednia | mala |
| 122 | Bug: Multiple VS Code windows opening when starting claude CLI | Dev | srednia | mala |
| 118 | Bug: mark-read --all ustawia read_at przed created_at | Dev | srednia | mala |

## Średnia wartość, średnia/duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 124 | Dependency support w backlogu (depends_on kolumna) | Dev | srednia | srednia |

---

## Szczegóły

### [125] Napraw failujące testy (State + Suggestions)
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Backlog Dev: Napraw failujące testy (State + Suggestions)

## Problem

8 testów failuje w test suite (test_agent_bus.py + test_agent_bus_cli.py):

### State tests (6 failures)
- `TestState::test_write_and_get_state`
- `TestState::test_state_filters_by_type`
- `TestState::test_state_metadata_json`
- `TestState::test_get_state_limit`
- `TestState::test_get_state_ordering_newest_first`
- `TestState::test_state_with_session_id`

**Error:** `AttributeError: 'AgentBus' object has no attribute 'write_state'`

**Root cause:** Metody State (write_state, get_state) usunięte z AgentBus podczas refactoru M3/M4.

### Suggestions tests (2 failures)
- `TestCliSuggestAndBacklog::test_suggest_status_update`
- `TestCliSuggestAndBacklog::test_suggest_status_bulk`

**Error:** `ValueError: 'in_backlog' is not a valid SuggestionStatus`

**Root cause:** Testy używają starego enumu 'in_backlog', ale nowy domain model ma inny zestaw statusów.

## Scope

1. **State tests:** Usunąć całą klasę `TestState` z test_agent_bus.py (metody State nie istnieją)
2. **Suggestions tests:**
   - Sprawdź aktualny `SuggestionStatus` enum w domain model
   - Zaktualizuj testy do zgodności z nowym API (lub usuń jeśli funkcjonalność nie istnieje)

## Expected outcome

- 0 failujących testów w test suite
- Testy zgodne z aktualnym API AgentBus (post-M3 refactor)

## Priorytet

Średni — nie blokuje pracy, ale sygnalizuje technical debt (testy out of sync z kodem).

## Area

Dev (testy)

## Effort

Mała (delete TestState class, update 2 testy Suggestions)

### [124] Dependency support w backlogu (depends_on kolumna)
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-23

# Backlog Dev: Dependency support w backlogu

## Problem

Backlog items nie mają kolumny `depends_on` — nie można oznaczyć że task X zależy od task Y.

**Przykład:**
- #119 (PE — sprawdzanie logów w session_start) zależy od #122 (Dev — session-logs tool)
- Obecnie: dependency tylko w `content` (prose) — nie jest machine-readable

## Scope

### 1. Schema migration

Dodaj kolumnę `depends_on` do `backlog`:
```sql
ALTER TABLE backlog ADD COLUMN depends_on INTEGER REFERENCES backlog(id);
```

Domyślnie NULL (backward compatible).

### 2. CLI support

**backlog-add:**
```bash
py tools/agent_bus_cli.py backlog-add --title "..." --area Dev --depends-on 122 --content-file tmp/x.md
```

**backlog-update:**
```bash
py tools/agent_bus_cli.py backlog-update --id 119 --depends-on 122
```

**backlog (read):**
```json
{
  "id": 119,
  "title": "...",
  "depends_on": 122,
  "status": "planned"
}
```

### 3. Validation (opcjonalnie)

Gdy agent próbuje ustawić status `in_progress` na task który ma dependency:
- Sprawdź czy `depends_on` task ma status `done`
- Jeśli nie → warning (nie blokuj, ale zasygnalizuj)

## Expected outcome

1. Agent może oznaczyć dependency: `--depends-on <id>`
2. Backlog pokazuje zależności (machine-readable)
3. Opcjonalnie: validation przed rozpoczęciem pracy

## Priorytet

Średni — quality of life improvement, nie bloker.

## Area

Dev (narzędzia)

## Effort

Średnia (schema migration + CLI + opcjonalna validation)

### [122] Bug: Multiple VS Code windows opening when starting claude CLI
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Bug: Multiple VS Code windows opening when starting `claude`

## Problem

Każde uruchomienie `claude` w terminalu otwiera **3 nowe okna VS Code** zamiast reuse existing window.

**User report:**
> "gdy zrobię nowy terminal i odpalę claude to otwierają mi się nowe okna VSC X3"

## Impact

- Workflow disruption — użytkownik musi ręcznie zamykać okna
- Resource waste — każde okno VS Code = osobny proces
- Confusion — nie wiadomo które okno jest "właściwe"

## Root Cause (hipoteza)

**Claude Code CLI bug:**
- VS Code workspace detection nie działa
- Każde wywołanie `claude` otwiera nowe okno zamiast reuse
- Symptom: `claude config list` też uruchamia nową instancję Claude zamiast pokazać config

**Verified:**
- ✓ Brak `.vscode/settings.json` w projekcie (nie jest to config issue)
- ✓ Brak `config.json` w `~/.claude/` (Claude Code nie ma config)
- ✓ `claude config list` uruchamia nową instancję (behavior inconsistent)

## Reproduction

1. Otwórz terminal (zewnętrzny lub integrated)
2. Uruchom `claude`
3. **Observe:** 3 nowe okna VS Code otwarte

**Expected:** 1 okno (lub reuse existing jeśli jest otwarte)

## Workarounds (krótkoterminowe)

**A. Używaj VS Code integrated terminal:**
- `Ctrl+\`` w VS Code → uruchom `claude`
- Może zmniejszyć problem (ale nie gwarantowane)

**B. Zamykaj wszystkie okna przed `claude`:**
- Zamknij wszystkie VS Code windows
- Uruchom `claude` → otworzy 1 nowe (lub 3, ale przynajmniej kontrolowane)

## Investigation Needed

1. **Claude Code CLI logs:**
   - Sprawdź czy są logi diagnostyczne
   - Gdzie claude szuka workspace detection?

2. **VS Code integration:**
   - Jak claude otwiera VS Code? (`code .` command? API?)
   - Czy respektuje `window.openFoldersInNewWindow` setting?

3. **GitHub issues:**
   - Czy to known issue w claude-code repo?
   - Czy inni użytkownicy raportują podobny problem?

## Long-term Solution

**Zgłosić jako bug do Claude Code:**
- Repo: https://github.com/anthropics/claude-code/issues
- Title: "Multiple VS Code windows open when starting `claude` CLI"
- Include: reproduction steps, expected vs actual behavior, environment (Windows, npm install)

## Severity

**Medium** — disrupts workflow, ale workaround dostępny (use integrated terminal).

## Environment

- OS: Windows
- Claude Code: npm install (global)
- VS Code: installed
- Terminal: external (PowerShell/cmd) triggers issue

### [118] Bug: mark-read --all ustawia read_at przed created_at
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-23

# Bug: mark-read --all ustawia read_at z przyszłością

## Problem

Message #207 ma `read_at` **przed** `created_at`:
- Created: 2026-03-23 04:05:42
- Read At: 2026-03-23 03:07:59

To niemożliwe fizycznie — wiadomość została przeczytana godzinę przed jej utworzeniem.

## Root Cause (hipoteza)

`agent_bus_cli.py mark-read --all --role developer` ustawia `read_at` dla **wszystkich** wiadomości do danej roli, nawet tych które jeszcze nie istniały w momencie wywołania.

**Możliwe scenariusze:**
1. Bulk mark-read używa `UPDATE messages SET read_at = ? WHERE recipient = ?` bez warunku `AND status = 'unread'`
2. Race condition — wiadomość dodana PODCZAS transakcji mark-read
3. Timestamp bug w AgentBus — używa cached timestamp zamiast `datetime.now()`

## Impact

- ✗ Trudne debugowanie (read_at < created_at to red flag)
- ✗ Messages nie pokazują się w inbox --status unread (mimo że są nowe)
- ✗ Agent nie widzi nowych wiadomości po bulk mark-read

## Reproduction

1. `mark-read --all --role developer` (np. 03:07:59)
2. Architect wysyła wiadomość (np. 04:05:42)
3. `inbox --role developer --status unread` → pusty (mimo że msg #207 nowa)
4. SELECT ... WHERE id = 207 → read_at = 03:07:59 (przed created_at)

## Expected Behavior

`mark-read --all` powinno:
- Ustawiać `read_at` tylko dla wiadomości WHERE `status = 'unread'`
- NIE dotykać wiadomości które jeszcze nie istnieją
- `read_at >= created_at` zawsze (invariant)

## Investigation Needed

1. Sprawdź `agent_bus_cli.py mark-read --all` implementation
2. Sprawdź `AgentBus.mark_read()` — czy filtruje po status?
3. Sprawdź `MessageRepository.mark_read()` — SQL WHERE clause
4. Verify race condition scenario (concurrent INSERT + mark-read)

## Severity

**Medium** — nie blokuje pracy, ale powoduje confusion i przeładowany kontekst (agent nie widzi że wiadomość już read).

### [90] Architektura synchronizacji bazy danych między maszynami
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** planned  **created_at:** 2026-03-21

# Architektura synchronizacji bazy danych między maszynami

## Problem

`mrowisko.db` zawiera komunikację między agentami (agent_bus), backlog zadań, logi sesji.
Praca na dwóch maszynach równolegle powoduje konflikty merge niemożliwe do automatycznego rozwiązania.

## Zakres

Zaprojektować i wdrożyć architekturę synchronizacji bazy danych między maszynami, która umożliwi:
- Wymianę wiadomości między agentami na różnych maszynach
- Współdzielony backlog zadań
- Brak konfliktów git
- Minimalne opóźnienie synchronizacji

## Opcje rozwiązań

Szczegółowa analiza opcji w: `documents/dev/machine_sync_architecture.md`

Opcje:
- **A:** Git LFS + manual merge (prowizorka)
- **B:** Baza zewnętrzna PostgreSQL/cloud (profesjonalne, wymaga hostingu)
- **C:** Podział lokalnej i shared DB (kompromis, offline-first)
- **D:** Event sourcing append-only (eleganckie, wymaga refactoru agent_bus)

## Następne kroki

1. User decyduje którą opcję wybrać (na podstawie priorytetów: koszt vs realtime vs elegancja)
2. Szczegółowy plan implementacji dla wybranej opcji
3. Implementacja etapami

## Tymczasowe rozwiązanie

Baza danych wyłączona z synchronizacji git (dodana do .gitignore) do czasu wdrożenia docelowej architektury.
