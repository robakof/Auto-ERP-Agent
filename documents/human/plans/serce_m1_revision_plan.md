# Serce M1 — Revision Plan (post code review)

Date: 2026-04-15
Base: review report `documents/human/reports/serce_m1_code_review.md`
Status: Proposed

---

## Scope

Wdrożenie C1 + W1-W4 + S1-S2. Bez scope creep.

## Zakres szczegółowy

### C1 + W3 — Integration test
- Plik: `serce/backend/tests/integration/db/test_schema.py`
- Fixture (conftest.py): łączy się z Postgres z env `TEST_DATABASE_URL` (format asyncpg),
  skip gdy brak. CREATE SCHEMA isolated per session, DROP SCHEMA teardown.
- Testy:
  1. `test_upgrade_creates_all_tables` — alembic upgrade head → introspekcja
     wszystkich 19 tabel + enum types.
  2. `test_insert_location_category_user` — INSERT po jednym rekordzie do
     Location/Category/User przez ORM, SELECT weryfikacja.
  3. `test_insert_respects_check_constraints` — INSERT `heart_balance=-1`
     powinien rzucić IntegrityError.
  4. `test_insert_respects_partial_unique_index` — dwa INITIAL_GRANT dla
     tego samego usera → IntegrityError.
  5. `test_downgrade_drops_all_tables` — alembic downgrade base → schema puste.
  6. `test_upgrade_downgrade_cycle` — upgrade → downgrade → upgrade (idempotentność).
- Dodaj `asyncpg` + `sqlalchemy[asyncio]` już są; brak extra deps.
- Runtime: developer uruchamia gdy ma dostępny Postgres (lokalny docker compose
  lub VPS). Dokumentacja w docstringu jak uruchomić.

### W1 — server_default w modelach
Dodać `server_default=sa.text("...")` / server_default="..." w modelach:
- `user.py`: email_verified, phone_verified, heart_balance, status, role
- `request.py`: hearts_offered, status
- `offer.py`: hearts_asked, status
- `exchange.py`: hearts_agreed, status
- `message.py`: is_hidden
- `notification.py`: is_read
- `user.py`: PhoneVerificationOTP.attempts
- `admin.py`: ContentFlag.status

Potem ręcznie zaktualizować migrację `f8e3d1a9b7c2_initial_schema.py` żeby
server_default był odzwierciedlony. (Nie regeneruję migracji — zbyt duży diff
wobec hand-written structure.)

### W2 — downgrade drop enum
`f8e3d1a9b7c2_initial_schema.py:578-595` — zamiana:
```python
sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
```
na:
```python
op.execute(f"DROP TYPE IF EXISTS {enum_name}")
```

### W4 — indeksy (split decision)

**Dodaję teraz (correctness, nie performance):**
- UNIQUE na `token_hash` w `refresh_tokens`, `password_reset_tokens`,
  `email_verification_tokens`, `email_change_tokens`
- UNIQUE na `code_hash` w `phone_verification_otps`

Uzasadnienie: kolizja hasha = security bug (dwa tokeny o tym samym hashu =
logikalny crash w verify flow). To nie index performance, to constraint integrity.

**Odkładam z explicit przypisaniem milestone:**
- `requests.(status, category_id, location_id)` — **M7** (Requests feed z filtrami,
  wtedy EXPLAIN ANALYZE weryfikuje czy index potrzebny).
- `offers.(status, category_id, location_id)` — **M8** (analogicznie).
- `exchanges.requester_id`, `exchanges.helper_id` — **M9** (Exchange state machine,
  queries per-user exchanges).
- `notifications.(user_id, is_read)` — **M13** (Notifications feed z unread filter).

Rationale: indeksy dodane bez query którego używają = spekulacja. Z M7/M8/M9/M13
mamy konkretne queries → można zmierzyć (pg_stat_statements, EXPLAIN).

### S1 — length constraints
- `password_hash`: `String(60)` (bcrypt = 60 znaków)
- `token_hash`: `String(64)` (SHA-256 hex = 64 znaki) — 4 token tables
- `code_hash`: `String(64)` (SHA-256)

### S2 — updated_at w users
Dodać do `User` model:
```python
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
)
```
I odpowiednio w migracji.

## Poza zakresem (explicit skip)

- **S3** CHECK `exchanges.(status = 'COMPLETED') = (completed_at IS NOT NULL)` —
  architect explicit "niekonieczne w M1, zapis jako uwaga do M9".
- **S4** `message.is_hidden` audit trail — open design question, nie do M1
  revision.

## Kolejność wykonania

1. W1 — modele (+ server_default)
2. W2 — downgrade enum fix
3. W4 — UNIQUE token_hash/code_hash + length S1 + updated_at S2 (w modelach + migracji)
4. C1/W3 — integration test (conftest + test_schema.py)
5. Run full suite: unit (existing 15) + integration (6 new) — wymaga Postgres
6. Re-handoff do Architekta z listą testów

## Definition of Done

- [ ] Wszystkie modele mają server_default dla pól z Python-side default
- [ ] Migracja odzwierciedla server_default 1:1
- [ ] Downgrade enum drop przez op.execute
- [ ] UNIQUE index na token_hash/code_hash w migracji + modelu
- [ ] password_hash/token_hash/code_hash mają length constraint
- [ ] users ma updated_at
- [ ] Integration test: 6 testów PASS przeciw rzeczywistemu Postgres
- [ ] Unit test (existing): 15/15 PASS (brak regresji)
- [ ] Explicit test list w re-handoff: `test_X::test_Y — N/N PASS`

## Ryzyko

- Integration test wymaga dostępnego Postgres. Developer nie ma lokalnego Dockera —
  uruchomienie na VPS przez `docker compose exec backend pytest tests/integration/`
  albo po postawieniu lokalnego `docker compose up -d db`. Dokumentacja w testscie.
- Update migracji hand-written + pilnowanie spójności z modelami — manualna praca,
  ryzyko divergence. Integration test C1 złapie rozjazd.
