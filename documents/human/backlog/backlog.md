# Backlog — 2026-03-26

*6 pozycji*

---

## Szybkie strzały (wysoka wartość, mała praca)

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 174 | [CONV] P1: CONVENTION_GIT — formalizacja | Dev | wysoka | mala |

## Średnia wartość, mała praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 190 | [DEV] SQL extraction — schema i migrations do core/database/ | Dev | srednia | mala |
| 180 | [CONV] P2: CONVENTION_HOOKS | Dev | srednia | mala |
| 166 | convention_init.py — scaffolding tool for new conventions | Dev | srednia | mala |

## Średnia wartość, średnia/duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 178 | [CONV] P2: CONVENTION_TOOL_CLI | Dev | srednia | srednia |

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
