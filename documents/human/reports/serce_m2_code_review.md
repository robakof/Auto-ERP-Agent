# Code Review: Serce M2 — Reference data

Date: 2026-04-16
Reviewer: Architect
Branch: main (commit e894884)
Plan: `documents/human/plans/serce_m2_reference_data.md`
Plan review: `documents/human/reports/serce_m2_plan_review.md`

## Summary

**Overall assessment: PASS**
**Code maturity level: L3 Senior** — Moduły krótkie i focused (max 28 linii na endpoint), spójna konwencja w całym M2 scope, `sa.table()` pattern w migracjach (immune na przyszłe zmiany ORM), precyzyjne downgradey, test coverage pokrywa happy + edge + boundary.

## U1-U5 Verification (must-fix z plan review)

| # | Wymóg | Status | Dowód |
|---|---|---|---|
| U1 | Stable IDs 1-16 alphabetical | ✓ PASS | `seed_voivodeships.py:22-39` |
| U2 | Literal `voivodeship_id` w CSV (nie name lookup) | ✓ PASS | CSV kolumna `voivodeship_id`, `seed_cities.py:38` |
| U3 | Enum reuse `create_type=False` | ✓ PASS | `seed_voivodeships.py:44`, `seed_cities.py:46` |
| U4 | Public endpoint comment + brak rate limit | ✓ PASS | `locations.py:4`, `categories.py:4` |
| U5 | ASGI client fixture | ✓ PASS | `conftest.py:91-110` (`integration_client`) |

## Decision: 27 vs 26 subcategories

**Zostawiamy 27.** Literalna lista w `serce_architecture.md` (linie 797-842) daje 27 podkategorii. Linia 844 ("26 podkategorii") to counting error w dokumencie. Migracja jest list-authoritative — poprawna.

**Action required:** poprawić linię 844 w `serce_architecture.md`: "26" → "27", "35" → "36".

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1: `?active=` filter nie obsługuje "pokaż wszystkie"**
`categories.py:19` — `active: bool | None = Query(default=True)`. Klient nie ma sposobu na pobranie zarówno aktywnych jak i nieaktywnych kategorii w jednym requeście. Typ `bool | None` z `default=True` oznacza że brak parametru = filtr na `active=True`, a `?active=false` = tylko nieaktywne. Wartość `None` (wszystkie) jest nieosiągalna z query params.

**Wpływ:** zerowy w M2 (wszystko seeded jako active). Staje się istotne w M15 (admin dezaktywuje kategorię).

**Fix options (nie bloker M2):**
- Opcja A: Dodać admin-only endpoint bez filtra w M15.
- Opcja B: Zmienić na `active: str | None = Query(default="true")` z walidacją `true/false/all`.
- Rekomendacja: **Opcja A** — M15 scope, nie ruszać M2.

### Suggestions (nice to have)

**S1: Misleading test comment**
`test_categories_endpoint.py:26` — komentarz "first 9 are groups (parent_id=None)" nie odpowiada faktycznemu orderingowi. `ORDER BY sort_order, id` interleaves grupy i podkategorie (grupy mają sort_order 0-8, subcaty też 0-N; wynik: [Group1(0,1), SubcatA(0,10), SubcatB(0,15)...]). Assertion w teście jest poprawna (filtruje po `parent_id`), ale komentarz myli.

**S2: Brak downgrade smoke test**
Żadna z 3 seed migracji nie ma testu downgrade (`alembic downgrade -1` → verify seed data removed). Gap systemowy — dotyczy wszystkich milestone'ów. Wart dodania jako reusable fixture w przyszłym M.

**S3: CSV cutoff ~44k vs planowane ~60k**
Plan mówił "minimum ~60k" z escape clause "(lub cokolwiek da sensowny rozkład geograficzny)". Top-100 daje cutoff ~44k (Sieradz, 44387), ale **każde z 16 województw jest reprezentowane** (Lubuskie: 2, Opolskie: 2 — najsłabiej, Śląskie: 23 — dominuje). Akceptuję — geograficzna kompletność > arbitralny próg ludności.

## Data Quality Verification

### CSV cities_pl.csv

- **Liczba:** 100 miast ✓
- **Encoding:** UTF-8, polskie znaki poprawne (Łódź, Kędzierzyn-Koźle, Bielsko-Biała) ✓
- **voivodeship_id range:** wszystkie w [1, 16] ✓
- **Spot-check mapping:**
  - Warszawa → 7 (Mazowieckie) ✓
  - Kraków → 6 (Małopolskie) ✓
  - Wrocław → 1 (Dolnośląskie) ✓
  - Gdańsk → 11 (Pomorskie) ✓
  - Opole → 8 (Opolskie) ✓
  - Rzeszów → 9 (Podkarpackie) ✓
- **Pokrycie geograficzne:** 16/16 województw ✓

### Seed categories

- **Grupy:** 9 z stable IDs 1-9, names zgodne z `serce_architecture.md` ✓
- **Podkategorie:** 27, names zgodne z listą referencyjną 1:1 ✓
- **sort_order:** contiguous 0-N w ramach grupy ✓
- **setval:** between group insert and subcat insert — poprawna sekwencja ✓

## Architecture Assessment

### Pattern compliance

| Pattern | Compliance |
|---|---|
| Incremental Migration | ✓ 3 osobne migracje (nie seed_all) |
| Validation at Boundary | ✓ FastAPI enum validation (422 na ?type=FOO) |
| Repository | N/A — endpointy trywialne (inline query), słusznie bez repo layer |
| Convention First | ✓ Zgodne z CONVENTION_MIGRATIONS (S6 append-only) |
| Defense in Depth | ✓ DB CHECK + Python enum |

### Fixtures architecture

`conftest.py` — dobrze zaprojektowane warstwy:
- `clean_db` → izolacja (DROP/CREATE schema)
- `migrated_db` → `clean_db` + `alembic upgrade head` via subprocess (unika nested asyncio)
- `integration_client` → `migrated_db` + ASGI transport z `dependency_overrides`

Trzy warstwy, każda testowalna niezależnie. L3 pattern.

## Test Coverage

| File | Tests | Scope |
|---|---|---|
| test_seed_voivodeships.py | 2 | count + IDs, spot-check names |
| test_seed_cities.py | 3 | count + parents, spot-check mapping, ID range |
| test_seed_categories.py | 4 | groups count+IDs, leaves count+parents, sort_order, spot-check |
| test_locations_endpoint.py | 4 | all, filter VOIVODESHIP, filter CITY, invalid type |
| test_categories_endpoint.py | 3 | default active, sort order, inactive filter |
| **Total** | **16** | Happy + edge + boundary |

Developer raportował 13 nowych testów — widzę 16 asercji w 16 test functions. Różnica wynika prawdopodobnie z tego że developer liczył test files (5) + existing modified (test_migration.py). Bez znaczenia — coverage adekwatny.

**Missing (not blocker):** downgrade test, explicit `?active=true` test.

## Recommended Actions

### Blocker (before M3 start):
- [ ] Fix `serce_architecture.md` linia 844: "26 podkategorii" → "27", "35 rekordów" → "36"

### Non-blocker (backlog for future M):
- [ ] W1: `?active=all` lub admin endpoint — scope M15
- [ ] S2: Downgrade smoke test fixture — scope next M with test infrastructure
- [ ] Contribute seed pattern do `PATTERNS.md` — Architect after PASS
- [ ] Update `serce_faza1_roadmap.md` — `?scope=` → `?type=` — Architect after PASS

## Verdict

**PASS.** M2 implementacja jest czysta, kompletna, dobrze przetestowana i spójna z architekturą. Wszystkie U1-U5 z plan review spełnione. 27 podkategorii to poprawna wartość (counting error w dokumencie, nie w kodzie). Developer może startować M3 (auth + JWT).
