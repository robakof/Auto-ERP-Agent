# Code Review: #149 AgentBus Refaktor — Separation of Concerns

Date: 2026-03-25
Files: core/services/*.py (8 serwisów), tools/lib/agent_bus.py (facade)

## Summary

**Overall assessment:** PASS
**Code maturity level:** Senior — czysta ekstrakcja, delegacja bez logiki w facade, zero regression (172 PASS), backward compat zachowany.

## Metryki

| Metryka | Przed | Po | Ocena |
|---------|-------|-----|-------|
| agent_bus.py | 1262 linii | 617 linii | ✓ 51% redukcja |
| Serwisy | 0 | 8 | ✓ SRP |
| Testy | 172 PASS | 172 PASS | ✓ Zero regression |
| Breaking changes | — | 0 | ✓ |
| Facade target | <200 | 617 | ✗ Nie osiągnięto |

## Odpowiedzi na pytania

### Q1: AgentBus 617 linii — wystarczająco thin?

**Nie idealnie, ale akceptowalnie.** 617 = ~200 schema/migrations + ~100 init/infra + ~317 delegacja. Delegacja jest czysta (3-4 linie per metoda). Schema i migrations to infrastruktura która powinna docelowo wynieść się do osobnego modułu (np. `core/database.py`), ale to follow-up, nie bloker.

**Rekomendacja follow-up:** Wyciągnij `_SCHEMA_SQL` + `_MIGRATE_SQL` + `_run_migrations()` do `core/database.py`. Facade spadnie do ~400 linii. Nie teraz — po stabilizacji.

### Q2: conn param pattern — OK?

**Tak.** Services przyjmujące `conn` to poprawny pattern dla transaction support. Facade zarządza transakcjami, services operują na przekazanym connection. Czysty separation of concerns.

### Q3: InstanceService direct SQL na messages (claim/unclaim)

**Zatwierdzony wcześniej** (review #321). Runner use case — InstanceService jest poprawnym ownerem. MessageService nie powinien wiedzieć o instancjach.

### Q4: MessageService.archive() direct SQL

**Akceptowalny trade-off.** 1 UPDATE vs 3 operacje (get + entity update + save). Warunek: komentarz w kodzie wyjaśniający dlaczego direct SQL ("performance: bulk archive, 1 query vs 3").

## Findings

### Warnings

Brak.

### Suggestions

- **agent_bus.py** — Schema + migrations do osobnego modułu (follow-up, nie teraz)
- **MessageService.archive()** — dodaj komentarz o trade-off performance vs purity

## Recommended Actions

- [ ] Komentarz w archive() o trade-off
- [ ] (Follow-up) Schema extraction do core/database.py
- [ ] Przejdź do etapu 3 (#188 polityka błędów)
