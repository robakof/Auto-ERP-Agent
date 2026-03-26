# Backlog — 2026-03-26

*12 pozycji*

---

## Szybkie strzały (wysoka wartość, mała praca)

| id  | tytuł                                    | obszar | wartość | effort |
| --- | ---------------------------------------- | ------ | ------- | ------ |
| 174 | [CONV] P1: CONVENTION_GIT — formalizacja | Dev    | wysoka  | mala   |
|     |                                          |        |         |        |

## Wysoka wartość, średnia praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 158 | CLI-API sync guard: test + docelowo single source of truth | Dev | wysoka | srednia |

## Średnia wartość, mała praca

| id  | tytuł                                                        | obszar | wartość | effort |
| --- | ------------------------------------------------------------ | ------ | ------- | ------ |
| 190 | [DEV] SQL extraction — schema i migrations do core/database/ | Dev    | srednia | mala   |
| 184 | inbox --full --status unread (bulk read)                     | Dev    | srednia | mala   |
| 180 | [CONV] P2: CONVENTION_HOOKS                                  | Dev    | srednia | mala   |
| 166 | convention_init.py — scaffolding tool for new conventions    | Dev    | srednia | mala   |
| 155 | Cancelled/superseded status dla handoff                      | Dev    | srednia | mala   |
| 154 | agent_bus_cli: filtr po senderze                             | Dev    | srednia | mala   |
| 141 | Agent communication — broadcast messages (do wszystkich)     | Dev    | srednia | mala   |

## Średnia wartość, średnia/duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 178 | [CONV] P2: CONVENTION_TOOL_CLI | Dev | srednia | srednia |
| 124 | Dependency support w backlogu (depends_on kolumna) | Dev | srednia | srednia |

## Pozostałe

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 185 | tool_calls.source column (live/replay) | Dev | niska | mala |

---

## Szczegóły

### [190] [DEV] SQL extraction — schema i migrations do core/database/
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

## Problem

agent_bus.py zawiera ~200 linii SQL (schema + migrations) wklejone w plik Python. Mieszanie języków, nie da się lintować SQL osobno.

## Propozycja

Wyciągnij schema i migrations do core/database/:
- core/database/schema.sql — definicje tabel
- core/database/migrations/ — osobne pliki .sql per migracja
- core/database/bootstrap.py — ładuje schema, wykonuje migracje

agent_bus.py (facade) traci ~200 linii, spada do ~400.

## Źródło

Review #149 (suggestion: schema extraction do core/database.py) + feedback usera o mieszaniu języków.

### [185] tool_calls.source column (live/replay)
**area:** Dev  **value:** niska  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

Dodać kolumnę `source` (live/replay) do tool_calls dla przejrzystości skąd pochodzi wpis.

Powiązane: #147 telemetry deduplication (live vs replay mają różne timestamp formats).

Źródło: Architect review #304

### [184] inbox --full --status unread (bulk read)
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

Inbox zwraca summary lub --full (wszystkie). Brakuje trybu: pełna treść tylko nieprzeczytanych.

Propozycja: `inbox --role X --status unread --full` lub domyślnie --full filtruje tylko unread.

Źródło: PE #305

### [180] [CONV] P2: CONVENTION_HOOKS
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 3 / P2

Konwencja hookow — pre/post tool use, on_stop, on_user_prompt.
Owner: Developer. Reviewer: Architect.
Zrodlo: 4 hooki w tools/hooks/, brak specyfikacji co moga a czego nie.

### [178] [CONV] P2: CONVENTION_TOOL_CLI
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 3 / P2

Konwencja interfejsu CLI narzedzi — output JSON contract, argument parsing, error format.
Owner: Developer. Reviewer: Architect.
Zrodlo: 55+ narzedzi w tools/, brak unified interface contract.

### [174] [CONV] P1: CONVENTION_GIT — formalizacja
**area:** Dev  **value:** wysoka  **effort:** mala  **status:** planned  **created_at:** 2026-03-25

[CONV EPIC #169] Fala 2 / P1

Formalizacja istniejacych regul git jako konwencja.
Owner: Developer. Reviewer: Architect.

Zakres: format commit message (feat/fix/refactor/docs/test/chore),
uzycie git_commit.py, kiedy push, branch naming, co nie commitowac.
Zrodlo: CLAUDE.md (sekcja git), git_commit.py.

### [166] convention_init.py — scaffolding tool for new conventions
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Tool: py tools/convention_init.py --id X --scope Y --audience Z. Generuje plik z YAML header i pustymi sekcjami zgodnie z CONVENTION_META. Eliminuje bledy struktury. Zrodlo: sugestia #255 (PE).

### [158] CLI-API sync guard: test + docelowo single source of truth
**area:** Dev  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-24

## Problem

AgentBus (API) i agent_bus_cli.py (CLI) to dwa pliki opisujące to samo. Ręczna synchronizacja się rozjeżdża — brakuje np. `suggestions --id` choć `backlog --id` istnieje. Klasa błędów której nie da się wyeliminować dyscypliną.

## Krok 1: Test-guard (MVP)

Test introspektuje publiczne metody AgentBus i porównuje z komendami CLI. Brak pokrycia = FAIL.

Scope:
- Jeden test w test_agent_bus.py
- Introspection: AgentBus public methods vs CLI commands dict
- Fail message: "AgentBus.X() nie ma odpowiednika w CLI"

## Krok 2: Single source of truth (docelowo)

CLI generowany z deklaracji na metodach AgentBus. Metoda = komenda. agent_bus_cli.py z ~550 linii → ~30.

Podejście: dekorator na metodach AgentBus definiuje argumenty CLI. CLI iteruje dekoratory, buduje argparse, dispatchuje.

## Źródło

- Sugestia #294 (Developer)
- Code review handoff #270 — Architect natknął się na brak `suggestions --id`

### [155] Cancelled/superseded status dla handoff
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

## Problem

Handoff do siebie (#267) stał się obsolete gdy ukończyłem zadanie w tej samej sesji. Brak mechanizmu anulowania — tylko `mark-read` maskuje problem.

## Propozycja

1. Dodać status `cancelled`/`superseded` do messages (lub osobne pole)
2. Komenda CLI: `py tools/agent_bus_cli.py cancel-handoff --id 267 --reason "Completed in same session"`
3. Filtrowanie w inbox: cancelled handoffy nie pokazują się domyślnie

## Alternatywa

Handoff automatycznie cancelled gdy:
- Ten sam sender wysyła nowy handoff do tego samego recipient
- Lub gdy backlog powiązany zmienia status na `done`

### [154] agent_bus_cli: filtr po senderze
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Dodać możliwość filtrowania wiadomości po senderze w agent_bus_cli.

**Problem:** Obecnie `inbox --role X` pokazuje wiadomości DO roli X. Brak sposobu na sprawdzenie wiadomości OD roli (np. "co Architect pisał o research?").

**Propozycja:**
- `inbox --sender architect` — wiadomości wysłane przez architekta
- lub `outbox --role architect` — outbox danej roli

**Use case:** Agent chce zweryfikować ustalenia innej roli bez czytania surowej bazy.

### [141] Agent communication — broadcast messages (do wszystkich)
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-24

Agent communication — możliwość broadcast messages (wysyłanie do wszystkich ról naraz).

**Problem:**
PE notyfikuje wszystkie role o zmianach promptów — brak mechanizmu broadcast (musi wysyłać do każdej roli ręcznie).

**Task dla Developer:**
1. Sprawdzić czy możliwe `agent_bus_cli.py send --to all`?
2. Jeśli nie → implementacja:
   - `send --to all --content-file tmp/x.md`
   - Creates N messages (one per role) atomically
   - Exclude: sender nie dostaje swojej własnej wiadomości

**Task dla PE (po wdrożeniu):**
Dodaj do end_of_turn_checklist:
"Jeśli modyfikowałem prompty ról — wysłałem notyfikację broadcast?"

**Success criteria:**
- `send --to all` działa (lub backlog item)
- PE checklist zawiera broadcast notification reminder
- Test: PE zmienia 3 prompty → broadcast → 3 role dostają notification

**Source:** Sugestia #234

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
