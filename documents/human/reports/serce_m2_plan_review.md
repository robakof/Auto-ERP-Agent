# Plan Review: Serce M2 — Reference data

Date: 2026-04-15
Reviewer: Architect
Plan: `documents/human/plans/serce_m2_reference_data.md`
Base: `documents/human/plans/serce_faza1_roadmap.md` §M2, `CONVENTION_MIGRATIONS.md` v1.0

## Verdict

**APPROVE z uwagami.**

Plan jest spójny z roadmapą i architekturą. Trade-offy przemyślane, blast radius zawężony. Pytania 1-4 rozstrzygam poniżej. Uwagi U1-U5 są must-fix przy implementacji (nie blokują startu — ale muszą trafić do kodu).

## Odpowiedzi na pytania Developera

### Q1 — Pattern data migration: `op.bulk_insert` na SA Core table() + CSV dla miast

**Zatwierdzam kierunek.** `op.bulk_insert` na `sa.table(...)` (nie ORM) jest Alembic best practice — migracja immune na przyszłe zmiany modelu. Inline dla województw (16) i kategorii (35) + CSV dla miast (~100) = sensowny podział.

**Warunek (U1):** CSV jest immutable razem z migracją. Od momentu commitu migracji `seed_cities.py` + `cities_pl.csv` — żaden plik nie jest edytowany. Aktualizacja listy miast w przyszłości = nowa migracja `update_cities_YYYY_MM.py` + nowy CSV. To wynika z `CONVENTION_MIGRATIONS.md` 01R, CSV jest częścią migracji.

**Po implementacji:** contribute wzorzec do `PATTERNS.md` — "Alembic seed migration: table() + op.bulk_insert + immutable data file". Podaj mi ścieżkę przy handoff code review, dopiszę do PATTERNS.

### Q2 — Stałe ID dla województw (1-16) i grup kategorii (1-9)

**Zatwierdzam.** Województw jest stała liczba (16, nie zmieni się w kraju), grupy kategorii (9) — stabilne z dekretu projektowego #106. Stałe ID = deterministyczny seed + deterministyczne FK w kolejnych migracjach.

**Warunek (U2):** `seed_cities.py` NIE wolno lookupować nazwy województwa (`SELECT id FROM locations WHERE name='Mazowieckie'`). Zamiast tego — hardcoded `voivodeship_id=7` (lub jakie tam Mazowieckie dostanie). Dlaczego: jeśli admin przemianuje województwo w M15, lookup po nazwie padnie. Migracja musi być deterministyczna na revision ID nie na danych.

Konwencja stałych ID: dopisz przy kolejnej iteracji do `CONVENTION_DB_SCHEMA.md` jako 12R (Alembic-specific) — ale to nie bloker M2, mogę sam dopisać po PASS.

### Q3 — Response shape: płaska lista

**Zatwierdzam płaską.** Argumenty za:
- Endpoint prosty (1 SELECT, bez agregacji).
- HTTP cache działa na prostym JSON.
- Klient buduje drzewo raz i trzyma w stanie — mniej ruchu na kolejnych requestach.
- Spójne z modelem (pole `parent_id` explicit, typ `type`/`LocationType`).

Nie dodawaj `children` ani agregacji serwerowej — to frontend job.

### Q4 — `?type=` zamiast `?scope=`

**Zatwierdzam `?type=`.** Roadmapa była szkicem pre-model. Model jest authoritative: `Location.type` (enum LocationType: VOIVODESHIP / CITY). `?scope=` koliduje semantycznie z `LocationScope` w `request.py`/`offer.py` (CITY_ONLY/VOIVODESHIP_WIDE/COUNTRY — widoczność ogłoszenia, inny concept). Użycie `?scope=` dla location type byłoby API smell.

Zaktualizuję roadmapę przy okazji (not blocker).

## Uwagi implementacyjne (must-fix w kodzie)

### U1 (z Q1): CSV immutable

`serce/backend/alembic/data/cities_pl.csv` po commit = nieedytowalny razem z migracją. Każda aktualizacja = nowa migracja + nowy plik.

### U2 (z Q2): seed_cities używa literalnych voivodeship_id

Nie `SELECT ... WHERE name=...`. Przykład w migracji:
```python
cities = [
    ("Warszawa", 7),   # 7 = mazowieckie (z seed_voivodeships)
    ("Kraków", 12),    # 12 = małopolskie
    ...
]
op.bulk_insert(locations_tbl, [{"name": n, "type": "CITY", "parent_id": vid} for n, vid in cities])
```

### U3: Downgrade precision

`DELETE FROM locations WHERE type='VOIVODESHIP'` usunie też user-added wojewódzka (gdyby istniały). Użyj `WHERE id BETWEEN 1 AND 16` (stałe ID pozwalają na precyzyjny downgrade). Dla kategorii analogicznie: `WHERE id BETWEEN 1 AND 9` dla grup + `WHERE parent_id BETWEEN 1 AND 9 AND name IN (...)` dla podkategorii.

Alternatywa: dodać kolumnę `seeded_revision` w schema (wskaźnik "to zaseedowane przez X"). Overengineering dla M2 — pomiń, zostaw precyzyjne WHERE BETWEEN.

### U4: Public endpoint comment + brak rate limit

W kodzie routerów:
```python
# Public endpoint — no auth, no rate limit (M2).
# Rate limiting będzie w M3 (slowapi global middleware).
@router.get("/locations")
async def list_locations(...):
    ...
```

### U5: Pytanie do Ciebie (nie bloker): asgi_client fixture

Test `test_locations_endpoint.py` potrzebuje ASGI client (httpx AsyncClient + FastAPI app). Sprawdź przed pisaniem czy `conftest.py` ma fixture albo dodaj. Jeśli brak — dodaj w ramach M2 (mała rzecz, ~15 linii). Nie handoffuj do mnie za to.

## Ryzyka — komentarze

**R1 (lista miast):** Developerzy dostarczają draft z GUS 2024 cross-check (Wikipedia "Lista miast w Polsce według liczby ludności"). User akceptuje lub dostarcza own. Reguła cutoff: top-100 wg ludności, minimum ~60k (lub cokolwiek da sensowny rozkład geograficzny). Przy code review zobaczę listę i ewentualnie flagę do decyzji usera. Nie blokuje startu implementacji.

**R2 (dyscyplina ID):** Zaadresowane przez `CONVENTION_MIGRATIONS.md` + stałe ID jako patten świadomy decyzji.

**R3 (fixture reuse):** `migrated_db` z M1 integration conftest jest reusable. ASGI client = drugi fixture obok (U5). Nie reuse conflicting, dwie równoległe fixtures dla dwóch warstw (DB + HTTP).

## Proaktywne obserwacje (nie bloker M2)

### Cache HTTP
Plan wykluczył `Cache-Control` — zgadzam się dla M2. Dodaj do `M18 coverage gate` jako "sprawdzić czy ref data endpointy są cache-friendly". Jeśli tak — `Cache-Control: public, max-age=3600` + `ETag` przy wejściu na prod (Faza 2 frontend).

### Ikonki kategorii
Plan wypełnia NULL teraz. OK. Backlog suggestion: "M-TBD: uzupełnić Category.icon po designie frontendu" — dopiszę do backlogu po PASS.

### DoS vector
`GET /categories` bez auth i rate limit to potencjalny DoS w prod (spam requestów). M3 rate limiter (slowapi) musi objąć te endpointy. Nie bloker M2, ale **zapisz w notes planu** żebym w M3 review tego pilnował.

### Migracja as pattern
Trzy migracje seed (voivodeships/cities/categories) to dobry test nowej konwencji `CONVENTION_MIGRATIONS.md`. Każda osobna, append-only, żadnej in-place edit. Przy handoff code review zweryfikuję że wszystkie trzy są odrębnymi plikami (nie jedną migracją "seed_all").

## Recommended Actions

- [x] Q1-Q4 rozstrzygnięte (patrz wyżej)
- [ ] Developer: implementacja etap 2-5 z U1-U5 wbudowanymi
- [ ] Developer: handoff `workflow_code_review` po etapie 5
- [ ] Architect (po PASS): contribute seed pattern do `PATTERNS.md`
- [ ] Architect (po PASS): update `serce_faza1_roadmap.md` — `?scope=` → `?type=`
- [ ] Architect (po PASS): dopisać 12R do `CONVENTION_DB_SCHEMA.md` — Alembic stałe ID dla reference data

## Next step

Developer startuje implementację (etap 2-5 planu). Po PASS testów lokalnych + deploy VPS → handoff do `workflow_code_review`.
