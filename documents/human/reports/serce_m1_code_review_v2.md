# Code Review v2: Serce M1 — initial_schema migration (post-revision)

Date: 2026-04-15
Branch: main
Commits: `fd775c7` (M1 revision), `126fda2` (values_callable enum fix)
Reviewer: Architect
Base: review v1 `documents/human/reports/serce_m1_code_review.md`,
      revision plan `documents/human/plans/serce_m1_revision_plan.md`,
      developer handoff `tmp/handoff_arch_m1_revision.md`

## Summary

**Overall assessment:** PASS

**Code maturity level:** L3 Senior — wszystkie zastrzeżenia z review v1 zaadresowane,
integration test złapał dodatkowy bug (enum name vs value) zanim wszedłby do M3,
fix `values_callable` zlokalizowany do helpera w `app/db/base.py` (DRY, transferable
pattern). Brak nadinżynierii — odłożone perf indeksy z explicit milestone tags.

## Zakres review

- C1 + W3 — integration test infrastructure
- W1 — server_default w modelach + migracji
- W2 — downgrade enum drop fix
- W4 — UNIQUE token_hash/code_hash (correctness) + explicit defer perf indeksów
- S1 — length constraints
- S2 — users.updated_at
- Out-of-scope ale wymuszone przez C1: `enum_values` helper + `values_callable` w 8 enum-ach

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

Brak.

### Suggestions (nice to have)

- **S5 (nowa): Wzorzec L4 dla str-mixin enums**
  - `app/db/base.py` ma helper `enum_values`, ale developer musi ręcznie pamiętać
    o `values_callable=enum_values` przy każdym nowym lowercase enum. Cicha divergencja
    łatwo wraca przy M5+ (nowe enumy).
  - L4 Staff move: custom wrapper `LowercaseEnum(...)` lub auto-detection
    (jeśli `cls.value != cls.name` → automatycznie aplikuje values_callable).
    Wtedy system **nie pozwala** na zły wzorzec.
  - Nie bloker M1 — odłóż do momentu kiedy pojawi się 2-gi nowy str-mixin enum
    z lowercase value.

- **S6 (nowa): Konwencja "raz wydana migracja jest immutable"**
  - W M1 in-place edit migracji był OK (fundament, 0 użytkowników). Od M2
    każda zmiana schema = nowa migracja. Warto zapisać jako konwencja w
    `documents/conventions/` lub w roadmap przy M2.
  - Brak tej zasady = tech debt loop: ktoś za miesiąc zedytuje migrację już
    zaaplikowaną na produkcji, prod schema rozjedzie się po cichu.

- **S7 (nowa): conftest TEST_DATABASE_URL — zalecane fallback dla CI/CD**
  - Obecnie skip gdy brak env. Dla CI/CD warto rozważyć ephemeral docker-compose
    profile albo testcontainers — żeby integration testy uruchamiały się automatycznie
    a nie tylko manualnie. Odłóż do momentu wprowadzenia CI pipeline.

## Verification details

### C1 + W3 — Integration tests

✓ `serce/backend/tests/integration/conftest.py` — `clean_db` (DROP/CREATE SCHEMA
  CASCADE) + `migrated_db` (alembic upgrade head subprocess), pytest.skip gdy
  TEST_DATABASE_URL brak. Subprocess approach poprawny — alembic env.py używa
  `asyncio.run` co kolidowałoby z pytest-asyncio event loop.

✓ `serce/backend/tests/integration/db/test_schema.py` — 6 testów, real Postgres,
  real INSERT/SELECT, lifecycle (upgrade/downgrade/upgrade idempotency).
  test_insert_location_category_user weryfikuje server_defaults (heart_balance=0,
  status='active', role='user') — rzeczywista weryfikacja W1.

### W1 — server_default

Spot check + grep `server_default` w `app/db/models/`:
- user.py: email_verified, phone_verified, heart_balance, status, role, attempts ✓
- request.py: hearts_offered, status ✓
- offer.py: hearts_asked, status ✓
- exchange.py: hearts_agreed, status ✓
- message.py: is_hidden ✓
- notification.py: is_read ✓
- admin.py: ContentFlag.status ✓

Migration `f8e3d1a9b7c2_initial_schema.py` ma server_default 1:1 z modelami
(zweryfikowane przez test_insert_location_category_user).

### W2 — downgrade enum drop

`f8e3d1a9b7c2_initial_schema.py:612` — `op.execute(f"DROP TYPE IF EXISTS {enum_name}")` ✓
SQL-standard, niezależne od SA internals. Zweryfikowane przez test_upgrade_downgrade_cycle.

### W4 — split decision

Correctness teraz (zweryfikowane przez grep):
- `uq_refresh_tokens_token_hash`, `uq_password_reset_tokens_token_hash`,
  `uq_email_change_tokens_token_hash`, `uq_email_verification_tokens_token_hash`,
  `uq_phone_verification_otps_code_hash` ✓

Perf indeksy odłożone z explicit milestone tags (revision plan lines 71-74):
- M7: `requests.(status, category_id, location_id)`
- M8: `offers.(status, category_id, location_id)`
- M9: `exchanges.requester_id`, `exchanges.helper_id`
- M13: `notifications.(user_id, is_read)`

Decyzja split poprawna — kolizja hashu = security bug (correctness), feed perf
to spekulacja bez query planu (M7+).

### S1 — length constraints

`password_hash: String(60)` (bcrypt) ✓
`token_hash: String(64)` (SHA-256 hex) — 4 token tables ✓
`code_hash: String(64)` ✓

### S2 — users.updated_at

`user.py:51-53` + migration linia ~106 — `server_default=func.now(), onupdate=func.now()` ✓

### Bonus: values_callable fix (C1 byproduct)

`app/db/base.py` — `enum_values()` helper centralizuje values_callable.
Zaaplikowane do 8 enum-ów z lowercase values:
- UserStatus, UserRole, DocumentType (user.py)
- FlagTargetType, FlagReason, FlagStatus, ResolutionAction, AuditTargetType (admin.py)

Inne enum-y (uppercase: RequestStatus, OfferStatus, ExchangeStatus, NotificationType,
LocationType, LocationScope, HeartLedgerType) zostawione bez zmian — `name == value`,
default SA behavior działa.

**Architectural impact:** to dokładnie scenariusz przewidziany w C1 — "rozjazd między
`Enum(UserStatus)` SA (name) a enum w migracji (value) ujawni się dopiero przy
pierwszym ORM INSERT". Bez integration testu wszedłby do M3. Walidacja wartości
integration testów: 1 bug znaleziony w M1, oszczędzony 1 incydent w M3.

## Test list (21/21 PASS na VPS)

```
tests/integration/db/test_schema.py::test_upgrade_creates_all_tables PASSED
tests/integration/db/test_schema.py::test_insert_location_category_user PASSED
tests/integration/db/test_schema.py::test_insert_respects_check_constraints PASSED
tests/integration/db/test_schema.py::test_insert_respects_partial_unique_index PASSED
tests/integration/db/test_schema.py::test_downgrade_drops_all_tables PASSED
tests/integration/db/test_schema.py::test_upgrade_downgrade_cycle PASSED
tests/test_health.py::test_health_returns_ok PASSED
tests/test_migration.py::test_migration_revision_metadata PASSED
tests/test_migration.py::test_migration_covers_all_tables PASSED
tests/test_migration.py::test_downgrade_drops_all_tables PASSED
tests/test_migration.py::test_migration_column_coverage PASSED
tests/test_migration.py::test_check_constraints_present PASSED
tests/test_migration.py::test_partial_indexes_present PASSED
tests/test_migration.py::test_unique_constraints_present PASSED
tests/test_migration.py::test_foreign_key_cascades PASSED
tests/test_migration.py::test_enum_types_dropped_in_downgrade PASSED
tests/test_models.py::test_all_tables_registered PASSED
tests/test_models.py::test_all_models_importable PASSED
tests/test_models.py::test_user_table_has_check_columns PASSED
tests/test_models.py::test_exchange_has_partial_unique_index PASSED
tests/test_models.py::test_review_has_unique_constraint PASSED
```

`21 passed in 20.24s` (15 unit + 6 integration na VPS Postgres `serce_test` DB)

## Open question — produkcyjny `serce` DB

Decyzja Architekta: **Opcja 1 — drop & recreate produkcyjny DB.**

Uzasadnienie:
- Produkcja ma 0 użytkowników (M1 to fundament, brak danych do migracji).
- Revision ID `f8e3d1a9b7c2` niezmienione → `alembic upgrade head` na produkcji to noop.
- Opcja 2 (diff migration) = overengineering bez wartości dla zerowych danych.
- Opcja 3 (zostawić) = toxic tech debt, M3 odkryje przy pierwszym INSERT przez ORM.

Komendy do wykonania na VPS przez Developera:
```bash
docker compose stop backend
docker compose exec db psql -U serce -d postgres -c "DROP DATABASE serce; CREATE DATABASE serce OWNER serce;"
docker compose start backend
docker compose exec backend alembic upgrade head
```

**WAŻNE precedens (S6):** to ostatni raz kiedy in-place edit zaaplikowanej migracji
jest dopuszczalny. Od M2 każda zmiana schema = nowa migracja (Alembic best practice).
Zalecam zapisanie tej zasady jako konwencja przed startem M2.

## Recommended Actions

- [x] C1 — integration test z INSERT/SELECT na real Postgres → DONE
- [x] W1 — server_default w modelach + migracji → DONE
- [x] W2 — downgrade enum drop przez op.execute → DONE
- [x] W3 — automated upgrade/downgrade cycle test → DONE
- [x] W4 — UNIQUE token_hash/code_hash now, perf indeksy odłożone z milestone tags → DONE
- [x] S1 — length constraints → DONE
- [x] S2 — users.updated_at → DONE
- [ ] **Drop & recreate produkcyjny `serce` DB na VPS** (4 komendy powyżej)
- [ ] Zapisać konwencję S6 (immutable migrations po wydaniu) przed startem M2
- [ ] S5/S7 — odłożone (nice-to-have, nie blokują M2)

## Next step

**M1 zamknięte. Start M2 (Reference data) — autoryzowany.**

Developer:
1. Wykonaj drop & recreate prod DB (4 komendy SSH).
2. Otwórz handoff S6 do Prompt Engineera (utworzenie konwencji `documents/conventions/CONVENTION_MIGRATIONS.md`) lub zapisz suggestion.
3. Start M2 wg roadmap.
