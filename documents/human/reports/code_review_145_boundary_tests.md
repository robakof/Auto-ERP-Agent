# Code Review: #145 Boundary Tests + Fix claimed_by

Date: 2026-03-25
Files: tests/test_boundary.py, core/repositories/message_repo.py

## Summary

**Overall assessment:** PASS
**Code maturity level:** Senior — testy testują granice MIĘDZY modułami (nie wewnątrz), round-trip patterns, graceful degradation. Fix claimed_by domyka bug z #313.

## Fix claimed_by

Poprawne domknięcie buga z #313. Repository teraz zawiera claimed_by w SELECT/INSERT/UPDATE. Boundary test potwierdza round-trip Runner→Repo.

## Boundary Tests — ocena per suite

### Suite 1: TestClaimedByBoundary (4 testy) — ✓

Pokrywa kluczowe granice:
- claim_task (direct SQL) → repo.get() → entity ma claimed_by ✓
- INSERT z claimed_by → GET → wartość persisted ✓
- UPDATE claimed_by → GET → wartość updated ✓
- Legacy 'claimed' status → graceful degradation ✓

### Suite 2: TestTelemetryDedupBoundary (3 testy) — ✓

Pokrywa unique index behavior:
- Same (session, tool, timestamp) → 1 row ✓
- Different timestamp → 2 rows ✓
- Different tool → 2 rows ✓

### Suite 3: TestSafetyGateBoundary (4 testy) — ✓

Pokrywa krytyczne granice hooka:
- Protected file → deny ✓
- tmp/ file → allow ✓
- Chain safe+unsafe → deny ✓
- Wildcard → deny ✓

### Suite 4: TestLegacyMappingBoundary (4 testy) — ✓

Pokrywa mapping round-trip:
- flag_human → ESCALATION ✓
- info → DIRECT ✓
- in_backlog → IMPLEMENTED ✓
- Round-trip consistency (TO_DOMAIN ∘ FROM_DOMAIN = identity) ✓

## Odpowiedzi na pytania

**Q1: Czy 15 testów to wystarczający safety net dla #149?**

Tak, z zastrzeżeniem. Te 15 testów pokrywa 4 kluczowe granice zidentyfikowane w assessment.
Refaktor #149 (separation of concerns) nie zmienia zachowania — zmienia strukturę.
Boundary tests weryfikują zachowanie na granicach → jeśli po refaktorze nadal PASS = zachowanie nienaruszone.

Jedyna luka: brak testu boundary dla `get_messages()` i `get_pending_tasks()` (direct SQL z #314).
Po refaktorze te metody znikną (przejdą do MessageService → repo), więc test jest zbędny POST refaktor.
Ale PRE refaktor mógłby wykryć regresję. Niekrytyczne — decyzja Developera.

**Q2: FK setup via direct SQL (`bus._conn.execute`) w telemetry testach — akceptowalny?**

Akceptowalny w boundary testach. Test sprawdza zachowanie na granicy live↔replay.
Session record to prerequisite, nie testowany obiekt. Direct SQL jako fixture setup = OK.
Pattern analogiczny do SQL fixtures w test_agent_bus.py.

## Findings

### Warnings

Brak.

### Suggestions

- **test_boundary.py:177** — `run_hook()` i `make_bash()` zduplikowane z `test_pre_tool_use.py`. Wyciągnij do `tests/conftest.py` jako shared fixtures. Nie blokuje.

## Recommended Actions

- [ ] (Opcjonalnie) Shared fixtures do conftest.py
- [ ] Przejdź do etapu 2 (#149 refaktor)
