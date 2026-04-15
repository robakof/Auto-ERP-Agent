# Code Review: Serce M1 — initial_schema migration

Date: 2026-04-15
Branch: main
Commits: `a220e6e` (Block 0 model fixes), `8afdcaa` (M1 migration + tests), `00e8c27` (Dockerfile PYTHONPATH)
Reviewer: Architect

## Summary

**Overall assessment:** NEEDS REVISION

**Code maturity level:** L2 Mid — struktura migracji i modeli jest dobrze wykonana (L3 Senior),
ale test coverage jest L1 w wymiarze stack-specific (Python CLI: "Test coverage L1 = zero tests") —
bo testy to wyłącznie string matching przez `inspect.getsource`, a DoD M1 explicit wymaga
integration testu z INSERT. Brak rzeczywistego uruchomienia alembic upgrade/downgrade w teście
to bloker senior-level.

## Zakres

- `serce/backend/alembic/versions/f8e3d1a9b7c2_initial_schema.py` (595 linii) — 19 tabel + enum + CHECK + partial unique indexes
- `serce/backend/tests/test_migration.py` (170 linii) — 9 testów offline
- `serce/backend/Dockerfile` (+PYTHONPATH=/app)
- Block 0 fixy modeli: `category.py`, `exchange.py`, `heart.py`, `offer.py`, `request.py`

## Findings

### Critical Issues (must fix)

- **C1: Brak integration testu z INSERT (DoD M1 violation)**
  - Roadmap `serce_faza1_roadmap.md:45-46`: DoD wymaga `tests/integration/db/test_schema.py` —
    "smoke: wszystkie tabele istnieją, INSERT minimalny user/location/category".
  - Dostarczono: `tests/test_migration.py` — tylko `inspect.getsource` + string matching,
    bez rzeczywistego uruchomienia migracji, bez INSERT, bez SELECT.
  - Ryzyko: rozjazd między `Enum(UserStatus)` SA (name) a enum w migracji (value),
    rozjazd między Python-side `default=0` a brakiem `server_default` w migracji,
    brak CHECK constraintów — wszystkie ujawnią się dopiero przy pierwszym ORM INSERT w M3.
  - "VPS validated, zero diff" z handoff #57 to empiryczny sygnał że schema się zgadza,
    ale nie zastępuje automated testu który złapie regresję w M2+.
  - Fix: dodać `serce/backend/tests/integration/db/test_schema.py` — fixture
    (pytest-postgresql lub ephemeral docker), `alembic upgrade head`, INSERT
    Location/Category/User przez ORM, SELECT zweryfikuj, `alembic downgrade base`,
    `alembic upgrade head` ponownie.

### Warnings (should fix)

- **W1: Brak `server_default` dla kolumn z Python-side `default=...` (Defense in Depth violation)**
  - Pattern: `Validation at Boundary` + `Defense in Depth` — DB powinna mieć defaulty
    żeby non-Python writes (raw SQL, manual DB edit, inne serwisy) nie crashowały.
  - Dotyczy: `users.heart_balance` (default=0 py / brak ddl), `users.email_verified`,
    `users.phone_verified`, `users.status`, `users.role`, `messages.is_hidden`,
    `notifications.is_read`, `requests.hearts_offered`, `requests.status`,
    `offers.hearts_asked`, `offers.status`, `exchanges.hearts_agreed`, `exchanges.status`,
    `phone_verification_otps.attempts`, `content_flags.status`.
  - Fix: dodać `server_default=sa.text("0")` / `sa.text("false")` / `sa.text("'ACTIVE'")`
    do migracji LUB dopisać `server_default` do modeli i wygenerować poprawioną
    migrację. Preferowana opcja: w modelach, żeby kolejne migracje auto-generate
    zawsze były spójne.

- **W2: Downgrade drop enum — kruchy idiom**
  - `f8e3d1a9b7c2_initial_schema.py:578-595` — `sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)`
    tworzy anonimowy Enum object tylko po to żeby wywołać `.drop()`. Zależy od wewnętrznej
    implementacji SA; wystarczy mała zmiana w `Enum.__init__` i migracja padnie.
  - Fix: `op.execute(f"DROP TYPE IF EXISTS {enum_name}")` — prosto, SQL-standard,
    nie zależne od SA internals.

- **W3: Brak testu że `alembic upgrade head` + `alembic downgrade base` faktycznie działa**
  - Powiązane z C1 ale wydzielone: nawet bez INSERT, sam cykl upgrade/downgrade
    powinien być testem automated. Teraz jedyne potwierdzenie to ręczne uruchomienie
    na VPS (handoff #57). Regresja za miesiąc = nikt jej nie złapie aż do produkcji.
  - Fix: pytest-alembic lub własny test który uruchamia `command.upgrade(cfg, "head")`
    i `command.downgrade(cfg, "base")` w transaction rollback na świeżej bazie.

- **W4: Brak indeksów na często filtrowanych kolumnach**
  - Feed queries (M7/M8): `requests.status + category_id + location_id`,
    `offers.status + category_id + location_id` — brak indeksów.
  - Exchange lookup: `exchanges.requester_id`, `exchanges.helper_id` — brak.
  - Token lookup: `refresh_tokens.token_hash`, `password_reset_tokens.token_hash`,
    `email_verification_tokens.token_hash`, `email_change_tokens.token_hash`,
    `phone_verification_otps.code_hash` — brak UNIQUE indexu mimo że są używane
    jako klucz lookupu przy weryfikacji.
  - Notifications: `notifications.user_id + is_read` — feed notyfikacji nieoptymalny.
  - Fix: dodać teraz albo explicit zapis w rapporcie M1 że indeksy zostaną dodane
    w M3/M7/M8 gdy pojawi się konkretne query. Odłożenie jest OK jeśli świadome.

### Suggestions (nice to have)

- **S1: Length constraint dla security-sensitive String**
  - `password_hash` (bcrypt = 60 chars), `token_hash` (hash hex — 64 chars jeśli SHA-256).
  - Bez limitu → TEXT w PostgreSQL — marnowane storage, potencjalny DoS przy malformed
    input (chociaż bcrypt hash z właściwego serwisu zawsze = 60).
  - Fix: `sa.String(60)` / `sa.String(64)` zgodnie z faktycznym formatem.
  - `admin_audit_log.action = String(64)` — dobry przykład już jest.

- **S2: Brak `updated_at` na `users`**
  - User ma `created_at` ale nie `updated_at`. M5 (User profile edit) będzie tego
    potrzebował. Taniej dodać teraz (jedna kolumna) niż robić migrację w M5
    z `ADD COLUMN updated_at DEFAULT now() NOT NULL` + backfill.
  - Fix: dodać `updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
    server_default=func.now(), onupdate=func.now())`.

- **S3: `exchanges.completed_at` nullable — rozważ CHECK**
  - `completed_at IS NULL` dla `status != COMPLETED`, `completed_at IS NOT NULL`
    dla `status = COMPLETED`. Można wymusić CHECK: `(status = 'COMPLETED') =
    (completed_at IS NOT NULL)`. Prevents stale/missing timestamp.
  - Niekonieczne w M1 — logika jest w warstwie aplikacji. Zapis jako uwaga do M9.

- **S4: `message.is_hidden` — brakujący use case**
  - Kolumna istnieje, ale w M9/M10 nie widać jak jest używana (moderacja?). Jeśli
    to moderation hide, rozważ `hidden_by: Optional[user_id]` + `hidden_at` — pełny
    audit trail zamiast samego boolean.

## Zgodność z PATTERNS.md

- ✓ **Incremental Migration:** M1 to pierwszy z 18 milestone'ów, scope wąski, commitable.
- ✗ **Defense in Depth:** W1 narusza — Python layer bez DB layer dla defaults.
- ✓ **Validation at Boundary:** CHECK constraints obecne na kluczowych polach
  (`heart_balance >= 0`, `hearts_offered >= 0`, `amount > 0`, `request_id OR offer_id`).
- ✓ **Separation of Dimensions:** Status + ownership rozdzielone (users: status +
  role + suspended_at + deleted_at — dobre rozdzielenie wymiarów).
- ⚠ **Proactive Discovery:** Kiedy to initial schema na pustej bazie, audit
  before enforcement nie ma zastosowania — pattern nie łamany, ale warto odnotować
  że przy pierwszej prawdziwej migracji danych (M2) ten pattern wchodzi do gry.

## Test list

Developer nie podał explicit test listy. Na podstawie `serce/backend/tests/test_migration.py`:

```
test_migration.py::test_migration_revision_metadata — PASS (assumed)
test_migration.py::test_migration_covers_all_tables — PASS (19 tabel pokrytych)
test_migration.py::test_downgrade_drops_all_tables — PASS
test_migration.py::test_migration_column_coverage — PASS
test_migration.py::test_check_constraints_present — PASS (5 CHECK)
test_migration.py::test_partial_indexes_present — PASS (2 partial unique)
test_migration.py::test_unique_constraints_present — PASS
test_migration.py::test_foreign_key_cascades — PASS (6 CASCADE)
test_migration.py::test_enum_types_dropped_in_downgrade — PASS (15 enum)
```

Test list wg handoff: "15/15 testów PASS (6 model + 9 migration)". Model tests
nie ma widocznych w zakresie review — prośba o explicit listę tych testów
w re-submit.

## Recommended Actions

- [ ] **C1 (bloker):** dodać `tests/integration/db/test_schema.py` z `alembic upgrade head`
      + INSERT User/Location/Category przez ORM + SELECT + downgrade. Minimum: pytest-postgresql
      fixture lub docker-compose test profile.
- [ ] **W1:** dodać `server_default` dla Python-side defaults (lista w W1). Preferowana
      droga: w modelach SA, regenerate migration, compare vs obecna.
- [ ] **W2:** zmienić downgrade drop enum na `op.execute("DROP TYPE IF EXISTS ...")`.
- [ ] **W3:** test `alembic upgrade head` + `alembic downgrade base` w pipeline
      (w C1 to może być ten sam test).
- [ ] **W4:** dodać indeksy LUB explicit decision że odkładamy do M3/M7/M8 z listą
      gdzie który indeks powstanie.
- [ ] **S1-S4:** opcjonalne, rozważ przy okazji.
- [ ] Re-handoff do Architekta po fixach: explicit lista testów `tests/*::test_X — N/N PASS`.

## Next step

Developer wdraża poprawki C1-W4 → re-handoff. Re-review skupiony tylko na C1-W4 (nie rozszerzam zakresu).
Po PASS: start M2 (Reference data).
