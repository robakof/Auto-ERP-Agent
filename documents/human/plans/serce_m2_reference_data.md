# Plan M2 — Reference data (Locations + Categories preload)

Date: 2026-04-15
Author: Developer
Status: Draft — do review Architekta
Base:
- Roadmapa: `documents/human/plans/serce_faza1_roadmap.md` §M2
- Architektura: `documents/human/plans/serce_architecture.md` decyzje #106, #107, #109, #110
- Poprzedni milestone: `documents/human/reports/serce_m1_code_review_v2.md` (PASS)

---

## Cel

Po `alembic upgrade head` baza zawiera:
- 16 województw + top-100 miast PL (GUS 2024, cutoff ~60k mieszkańców).
- 9 grup kategorii + 26 podkategorii (decyzja #106) = 35 rekordów.

Trzy endpointy publiczne (bez JWT) zwracają te dane dla frontendu.

## Zakres

**W zakresie:**
- Alembic data migration dla `locations` (16 województw + ~100 miast, parent_id = voivodeship_id).
- Alembic data migration dla `categories` (9 grup parent_id=NULL + 26 podkategorii z sort_order).
- 3 endpointy REST bez auth:
  - `GET /api/v1/locations` — płaska lista (id, name, type, parent_id).
  - `GET /api/v1/locations?scope=VOIVODESHIP|CITY` — filtr.
  - `GET /api/v1/categories` — lista (id, name, parent_id, icon, sort_order, active). Filtr `?active=true` default.
- Schemas (Pydantic) dla response.
- Testy integracyjne (real Postgres, post-migration assertions + endpoint response).

**Poza zakresem:**
- Nested response dla categories (grupy z dziećmi w jednym obiekcie) — klient buduje drzewo sam, albo M12/frontend milestone.
- Cache HTTP (Cache-Control) — roadmapa mówi "cache'owane" ale to frontend/reverse-proxy, nie backend layer.
- Dodawanie/edycja kategorii/lokalizacji przez admin API — poza M2 (brak admin auth przed M3/M15).
- Ikonki kategorii (`icon` pole) — wypełnimy `NULL`; frontend mapuje ikony po ID w Fazie 2.

## Założenia

- Roadmapa sugeruje że kategorie mogą wymagać potwierdzenia z userem — **potwierdzone decyzją #106**, pełna lista w `serce_architecture.md` linie 797-842. Używamy tej listy 1:1.
- Miasta: lista GUS 2024, top-100 wg ludności, cutoff ~60k mieszkańców. Format dataset: `(name, voivodeship_name, population)`. Population służy tylko do selekcji/sortowania przy seedzie, nie ląduje w modelu (decyzja #111).
- Kolejność sort_order w kategoriach: zgodna z kolejnością grup z decyzji #106 (Dom→Opieka→Nauka→Zdrowie→Transport→IT→Urzędowe→Pożyczanie→Inne). Podkategorie: kolejność z dokumentu.
- M2 = **nowa migracja Alembic** (S6 konwencja) — in-place edit `f8e3d1a9b7c2` zakazany.

## Pytania do Architekta (do rozstrzygnięcia przed kodem)

1. **Pattern dla data migration:** `PATTERNS.md` nie zawiera wzorca seed/preload. Proponuję:
   - Migracja Alembic używa `op.bulk_insert()` na `table()` z SA Core (nie ORM model, bo zmiany modelu w przyszłości nie powinny łamać migracji — best practice Alembic).
   - Dane województw i kategorii — inline w migracji (stałe, krótkie listy).
   - Dane miast — ładowane z `serce/backend/alembic/data/cities_pl.csv` (~100 rekordów, długa lista — lepiej w pliku niż w migracji).
   - Czy akceptujesz ten kierunek, czy wolisz wszystko inline w migracji (self-contained migracja)?

2. **Stałość ID:** Czy locations i categories mają mieć stałe ID (explicit INSERT id=1 Warszawa itp.) żeby inne migracje/aplikacje mogły referować, czy ID auto-increment?
   - Rekomendacja: stałe ID dla województw (1-16, często referowane) + stałe ID dla grup kategorii (1-9). Miasta i podkategorie — auto.
   - Risk: zmiana kolejności = zmiana ID, przyszłe data migrations wrażliwe na to.

3. **Endpoint response shape:** Zwracamy listę płaską `[{id, name, parent_id, type}, ...]` (klient buduje drzewo) czy nested `[{id, name, children: [...]}]`?
   - Rekomendacja: płaska (prostsza, zgodna z modelem, łatwiej cachować po stronie klienta).

4. **`?scope` vs `?type`:** Parametr filtra — roadmapa pisze `?scope=VOIVODESHIP|CITY`, ale w modelu pole nazywa się `type`. Który use w query param?
   - Rekomendacja: `?type=` (spójnie z modelem). Jeśli roadmapa trzyma `?scope=` — ok, zmieniam.

## Deliverables

### Migracje (serce/backend/alembic/versions/)
1. `<rev>_seed_voivodeships.py` — INSERT 16 województw (data migration, `op.bulk_insert` na `table('locations', ...)`).
2. `<rev>_seed_cities.py` — INSERT ~100 miast z CSV (`alembic/data/cities_pl.csv`).
3. `<rev>_seed_categories.py` — INSERT 9 grup + 26 podkategorii (inline, z sort_order).

Downgrade każdej: `DELETE FROM <tabela> WHERE ...` z warunkiem zawężającym (np. `name IN (...)`) żeby nie kasować user-added rekordów.

### Kod (serce/backend/app/)
1. `app/api/v1/locations.py` — router z `GET /locations` (filtr `?type=` opcjonalny).
2. `app/api/v1/categories.py` — router z `GET /categories` (filtr `?active=` default true).
3. `app/schemas/location.py`, `app/schemas/category.py` — Pydantic response models.
4. `app/db/repositories/location_repo.py`, `category_repo.py` — query logic (lub inline w endpoincie jeśli trywialne; DRY check przy code review).
5. `app/api/v1/router.py` — include nowe routers.

### Testy (serce/backend/tests/)
1. `tests/integration/db/test_seed_voivodeships.py` — po `upgrade head`: `SELECT COUNT(*) WHERE type='VOIVODESHIP'` = 16, spot-check nazw (Mazowieckie, Śląskie).
2. `tests/integration/db/test_seed_cities.py` — `SELECT COUNT(*) WHERE type='CITY'` = 100 (±2 tolerancja na aktualizacje GUS), każde miasto ma valid `parent_id` w województwie.
3. `tests/integration/db/test_seed_categories.py` — `SELECT COUNT(*) WHERE parent_id IS NULL` = 9, `SELECT COUNT(*) WHERE parent_id IS NOT NULL` = 26.
4. `tests/integration/api/test_locations_endpoint.py` — `GET /api/v1/locations` 200 + liczba ≥ 116; `?type=VOIVODESHIP` 200 + liczba=16.
5. `tests/integration/api/test_categories_endpoint.py` — `GET /api/v1/categories` 200 + liczba=35; response shape validation.
6. `tests/test_migration.py` (existing unit) — dodać test że nowe revisions są po `f8e3d1a9b7c2` w chain.

### Dane
`serce/backend/alembic/data/cities_pl.csv` — `name,voivodeship,population` format, ~100 wierszy z GUS.

## Definition of Done

- `alembic upgrade head` na świeżej bazie: 16 województw + ~100 miast + 35 kategorii.
- `alembic downgrade base` czyści tabele (w tym seed — downgrade każdej migracji cofa swój INSERT).
- `GET /api/v1/locations` zwraca 116+ rekordów, filtr `?type=` działa.
- `GET /api/v1/categories` zwraca 35 rekordów, filtr `?active=` działa.
- Testy: 100% PASS (unit + integration).
- Deploy na VPS: `alembic upgrade head` PASS, endpointy accessible publicly.
- Code review Architekta: PASS.

## Estymacja

Rozmiar: **S-M** (zgodnie z roadmapą).
Pliki: ~10 nowych (3 migracje + 1 CSV + 2 endpointy + 2 schemas + 2 repos + 5 testów) + 1 edit router.
Linie: ~800-1000 (większość to dane województw/miast/kategorii inline lub CSV).

## Etap 1: sync z Architekt

**Zanim napiszę kod** — wysyłam ten plan do Architekta przez `workflow_plan_review`. Pytania z sekcji powyżej (1-4) potrzebują rozstrzygnięcia.

Po PASS:
- Etap 2: seed data (migracje) + unit testy.
- Etap 3: endpointy + schemas + integration testy.
- Etap 4: deploy VPS + weryfikacja.
- Etap 5: handoff do Architekta (workflow_code_review).

## Ryzyka

- **R1: lista miast GUS — gdzie wziąć dataset?** Proponuję ręcznie skompilować z publicznych danych GUS (Wikipedia "Lista miast w Polsce według liczby ludności" jako cross-check). Alternatywa: użytkownik dostarcza plik.
- **R2: stałe ID województw** — jeśli Architekt zatwierdzi, trzeba trzymać dyscyplinę w kolejnych migracjach (nie zmieniać ID).
- **R3: conftest dla integration testów** — obecnie (M1) wymaga env `TEST_DATABASE_URL`. Endpointy HTTP też potrzebują testowej DB — zakładam reuse istniejącej fixture (`migrated_db` z M1).

## Blast radius

- **Nowe pliki** (~10): 3 migracje Alembic, 1 CSV z miastami, 2 routery API, 2 Pydantic schemas, 2 repozytoria, 5 plików testów.
- **Edytowane pliki** (1): `app/api/v1/router.py` (include nowe routery).
- **Role dotknięte:** tylko developer. Brak zmian w promptach, workflow, scaffoldingu agent_bus.
- **Nie dotknięte:** modele domenowe, migracja M1, hearts/auth (przyszłe M).
- **DB impact:** 3 data migrations dopisane po M1 (revision chain: `f8e3d1a9b7c2` → seed_voivodeships → seed_cities → seed_categories).

## Oczekiwana decyzja od Architekta

- **APPROVE** — plan zatwierdzony, Developer startuje implementację (etap 2-5 planu).
- **APPROVE z uwagami** — plan OK, drobne sugestie do uwzględnienia przy implementacji.
- **REJECT** — feedback konkretny: co zmienić, czego nie. Developer poprawia i re-wysyła.
- **ESCALATE do człowieka** — tylko jeśli pytania 1-4 wymagają decyzji biznesowej/scope (nie sądzę — wszystkie są techniczne).

Po PASS: handoff do workflow_code_review po zakończeniu implementacji.
