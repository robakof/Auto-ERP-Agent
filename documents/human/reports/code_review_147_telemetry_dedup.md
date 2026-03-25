# Code Review: #147 Telemetry Deduplication

Date: 2026-03-25
Files: tools/lib/agent_bus.py, tests/test_agent_bus.py

## Summary

**Overall assessment:** PASS
**Code maturity level:** Senior — pragmatyczny pattern (UNIQUE INDEX + INSERT OR IGNORE), czysta migracja, testy pokrywają oba scenariusze (dedup + różne timestamps).

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

- **agent_bus.py:1001** — Docstring mówi "Returns row id (0 if duplicate ignored)". W SQLite `cursor.lastrowid` przy INSERT OR IGNORE, gdy wiersz jest zignorowany, zwraca ostatni udany insert (nie 0). Wartość zwracana jest niedeterministyczna dla ignored rows. Jeśli nikt nie używa return value do detekcji duplikatów — kosmetyka. Jeśli ktoś używa — bug.

### Suggestions (nice to have)

- **agent_bus.py:213** — Migracja nie czyści istniejących duplikatów z DB — index `CREATE UNIQUE INDEX IF NOT EXISTS` na danych z duplikatami rzuci błąd SQLite. Developer raportuje cleanup (73k→19k), więc prawdopodobnie zrobił ręczny DELETE przed migracją. Ale przy cold start na innej maszynie z brudnymi danymi migracja się wysypie. Rozważ dodanie `DELETE` duplikatów w `_MIGRATE_SQL` PRZED `CREATE UNIQUE INDEX`.

## Odpowiedzi na pytania Developera

### Q1: Akceptujemy 2 wpisy (live + replay) czy single source of truth?

**Rekomendacja: Single source of truth — replay.**

Replay ma pełne dane z transcript (input_summary, dokładne timestamps). Live ma `datetime('now')` — mniej precyzyjne. Replay jest autorytatywny.

Ale to jest osobny task, nie bloker obecnego commitu. Obecne rozwiązanie (6x→1x per source) jest poprawne i wystarczające teraz.

### Q2: Warto dodać kolumnę `source`?

**Tak, ale w follow-upie.** Kolumna `source TEXT CHECK (source IN ('live', 'replay'))` da przejrzystość i umożliwi filtrowanie. Gdy zdecydujemy o single source — łatwo `DELETE WHERE source = 'live'`.

Dodaj jako backlog item, nie komplikuj obecnego commitu.

## Recommended Actions

- [ ] Napraw docstring `add_tool_call` — return value semantics (Warning)
- [ ] Dodaj cleanup duplikatów do migracji przed CREATE INDEX (Suggestion)
- [ ] (Follow-up) Backlog: kolumna `source` + single source of truth
