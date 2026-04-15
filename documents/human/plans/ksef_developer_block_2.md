# Developer Block 2 — KSeF Shadow DB + Repository

Data: 2026-04-15
Autor: Architect
Dotyczy planu: `documents/human/plans/ksef_api_automation.md` (§5 M1)
Dla roli: Developer
Status: Ready to start
Prerequisites: Block 1 ✓ (commit 1566f94)

---

## Cel bloku

Dostarczyć **persystencję stanu wysyłek** — `data/ksef.db` + warstwę repo z idempotencją
i audit trail. Fundament pod M4 (SendInvoice use case) i M5 (daemon).

**Zero kontaktu z KSeF API, zero XML, zero ERP.** Czysty state store + kontrakt repo.

Po ukończeniu Block 2 mamy gwarancję że:
- Żadna faktura nie zostanie wysłana dwa razy (unique constraint + `has_pending_or_sent`)
- Każda wysyłka ma trwały ślad (stan, timestampy, error diagnostyka)
- Daemon może wznowić pracę po restarcie bez utraty stanu

---

## Decyzje zatwierdzone (2026-04-15)

| Decyzja | Wybór |
|---|---|
| Lokalizacja DB | `data/ksef.db` (osobny plik, nie mrowisko.db) |
| Silnik | **SQLite3** (stdlib, bez nowych deps) |
| Migracje | **Raw SQL w `core/ksef/schema.sql`** — alembic dopiero przy M6 gdy schema się rozrośnie |
| Tryb dostępu | Single-writer (daemon) + optional readonly (CLI status) — WAL mode |
| Strategia retry | Każda próba = osobny wiersz z rosnącym `attempt` (audit, nie overwrite) |
| State machine | Forward-only; cofka = nowy `attempt`, nie update starego wiersza |

---

## Scope — co dokładnie powstaje

### Pliki

```
core/
  ksef/
    schema.sql              # DDL — CREATE TABLE, INDEX
    adapters/
      repo.py               # ShipmentRepository — interfejs + implementacja SQLite
    domain/
      __init__.py
      shipment.py           # Wysylka (dataclass) + ShipmentStatus (Enum)
      events.py             # StatusTransition (dataclass) — rekord zmiany stanu

data/
  .gitkeep                  # katalog commitowany, pliki .db ignorowane

tools/
  ksef_init_db.py           # CLI: utworzenie / migracja schema
  ksef_status.py            # CLI: odczyt stanu (tabela ostatnich N wysyłek)

tests/
  ksef/
    test_ksef_repo.py       # testy repo: happy + edge
    test_ksef_schema.py     # testy schema: constraints, indeksy
```

`.gitignore`:
```
data/ksef.db
data/ksef.db-journal
data/ksef.db-wal
data/ksef.db-shm
```

### Schema — `core/ksef/schema.sql`

```sql
-- KSeF Shadow DB schema v1
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS ksef_wysylka (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    gid_erp           INTEGER NOT NULL,
    rodzaj            TEXT    NOT NULL CHECK (rodzaj IN ('FS', 'FSK')),
    nr_faktury        TEXT    NOT NULL,
    data_wystawienia  DATE    NOT NULL,
    xml_path          TEXT    NOT NULL,
    xml_hash          TEXT    NOT NULL,                        -- SHA-256 hex
    status            TEXT    NOT NULL CHECK (status IN (
                          'DRAFT','QUEUED','AUTH_PENDING',
                          'SENT','ACCEPTED','REJECTED','ERROR'
                      )),
    ksef_session_ref  TEXT,
    ksef_invoice_ref  TEXT,
    ksef_number       TEXT,
    upo_path          TEXT,
    error_code        TEXT,
    error_msg         TEXT,
    attempt           INTEGER NOT NULL DEFAULT 1,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    queued_at         TIMESTAMP,
    sent_at           TIMESTAMP,
    accepted_at       TIMESTAMP,
    rejected_at       TIMESTAMP,
    errored_at        TIMESTAMP,
    UNIQUE (gid_erp, rodzaj, attempt)
);

CREATE INDEX IF NOT EXISTS idx_ksef_status
    ON ksef_wysylka(status);
CREATE INDEX IF NOT EXISTS idx_ksef_gid_rodzaj
    ON ksef_wysylka(gid_erp, rodzaj);
CREATE INDEX IF NOT EXISTS idx_ksef_xml_hash
    ON ksef_wysylka(xml_hash);

-- Log transitions (audit) — osobna tabela, nie nadpisujemy historii
CREATE TABLE IF NOT EXISTS ksef_transition (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    wysylka_id      INTEGER NOT NULL REFERENCES ksef_wysylka(id),
    from_status     TEXT    NOT NULL,
    to_status       TEXT    NOT NULL,
    occurred_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    meta_json       TEXT                                        -- opcjonalne pola dodatkowe
);

CREATE INDEX IF NOT EXISTS idx_ksef_transition_wysylka
    ON ksef_transition(wysylka_id, occurred_at);

-- Schema version (pod przyszłe migracje)
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT OR IGNORE INTO schema_version(version) VALUES (1);
```

### Domain — `core/ksef/domain/shipment.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

class ShipmentStatus(str, Enum):
    DRAFT         = "DRAFT"
    QUEUED        = "QUEUED"
    AUTH_PENDING  = "AUTH_PENDING"
    SENT          = "SENT"
    ACCEPTED      = "ACCEPTED"
    REJECTED      = "REJECTED"
    ERROR         = "ERROR"

# State machine — forward-only, allowed transitions
_ALLOWED: dict[ShipmentStatus, frozenset[ShipmentStatus]] = {
    ShipmentStatus.DRAFT:        frozenset({ShipmentStatus.QUEUED, ShipmentStatus.ERROR}),
    ShipmentStatus.QUEUED:       frozenset({ShipmentStatus.AUTH_PENDING, ShipmentStatus.ERROR}),
    ShipmentStatus.AUTH_PENDING: frozenset({ShipmentStatus.SENT, ShipmentStatus.ERROR}),
    ShipmentStatus.SENT:         frozenset({ShipmentStatus.ACCEPTED, ShipmentStatus.REJECTED, ShipmentStatus.ERROR}),
    ShipmentStatus.ACCEPTED:     frozenset(),   # terminal
    ShipmentStatus.REJECTED:     frozenset(),   # terminal
    ShipmentStatus.ERROR:        frozenset(),   # terminal (retry = new attempt)
}

def is_valid_transition(old: ShipmentStatus, new: ShipmentStatus) -> bool:
    return new in _ALLOWED[old]

@dataclass(frozen=True)
class Wysylka:
    id: int
    gid_erp: int
    rodzaj: str                  # 'FS' | 'FSK'
    nr_faktury: str
    data_wystawienia: date
    xml_path: str
    xml_hash: str
    status: ShipmentStatus
    ksef_session_ref: str | None
    ksef_invoice_ref: str | None
    ksef_number: str | None
    upo_path: str | None
    error_code: str | None
    error_msg: str | None
    attempt: int
    created_at: datetime
    queued_at: datetime | None
    sent_at: datetime | None
    accepted_at: datetime | None
    rejected_at: datetime | None
    errored_at: datetime | None
```

### Repository — `core/ksef/adapters/repo.py`

```python
class ShipmentRepository:
    def __init__(self, db_path: Path, clock: Callable[[], datetime] = datetime.utcnow) -> None: ...

    # Queries
    def get(self, wysylka_id: int) -> Wysylka | None: ...
    def get_latest(self, gid_erp: int, rodzaj: str) -> Wysylka | None: ...
    def has_pending_or_sent(self, gid_erp: int, rodzaj: str) -> bool:
        """True gdy istnieje wpis w stanie QUEUED/AUTH_PENDING/SENT/ACCEPTED."""
    def list_by_status(self, status: ShipmentStatus, limit: int = 100) -> list[Wysylka]: ...
    def list_recent(self, limit: int = 50) -> list[Wysylka]: ...

    # Mutations
    def create(self, *, gid_erp: int, rodzaj: str, nr_faktury: str,
               data_wystawienia: date, xml_path: str, xml_hash: str,
               attempt: int = 1) -> Wysylka:
        """Tworzy wiersz w stanie DRAFT. Raises IntegrityError jeśli duplikat (gid, rodzaj, attempt)."""

    def transition(self, wysylka_id: int, new_status: ShipmentStatus,
                   *, meta: dict | None = None, **fields) -> Wysylka:
        """Zmiana statusu + opcjonalne pola (ksef_session_ref, error_code itd.).
        Waliduje przejście przez is_valid_transition. Loguje do ksef_transition.
        Atomowa (transaction)."""

    def new_attempt(self, gid_erp: int, rodzaj: str, **create_kwargs) -> Wysylka:
        """Tworzy nowy wiersz z attempt = prev.attempt + 1 dla retry."""

    # Housekeeping
    def init_schema(self) -> None:
        """Wykonuje schema.sql jeśli DB pusty."""
```

**Kontrakt zachowań (obowiązkowe, pokryte testami):**

1. `create()` w istniejącym aktywnym stanie (`has_pending_or_sent=True`) → `ShipmentAlreadyActiveError`
2. `transition()` niedozwolone przejście (np. `ACCEPTED→QUEUED`) → `InvalidTransitionError`
3. `transition()` do stanu terminalnego zapisuje odpowiedni `*_at` timestamp
4. `new_attempt()` z nieistniejącego GID → `ShipmentNotFoundError`
5. Wszystkie mutacje w pojedynczej transakcji (commit lub rollback)
6. Równoczesne wywołania `create()` dla tego samego `(gid, rodzaj, attempt=1)` z dwóch procesów — jeden wygrywa, drugi dostaje `IntegrityError` → tłumaczymy na `ShipmentAlreadyActiveError`

### Exceptions — `core/ksef/exceptions.py` (rozszerzenie)

Dodajemy do istniejącej hierarchii z Block 1:

```python
class KSefRepoError(KSefError): ...
class ShipmentAlreadyActiveError(KSefRepoError): ...
class InvalidTransitionError(KSefRepoError): ...
class ShipmentNotFoundError(KSefRepoError): ...
```

### CLI: `tools/ksef_init_db.py`

```
py tools/ksef_init_db.py
py tools/ksef_init_db.py --db data/ksef.db     # opcjonalna ścieżka
py tools/ksef_init_db.py --check               # tylko sprawdź, nie twórz
```

Exit codes: 0 = OK (stworzono lub istnieje poprawna schema), 1 = niezgodność, 2 = błąd I/O.

### CLI: `tools/ksef_status.py`

Podgląd stanu — idempotentny, readonly.

```
py tools/ksef_status.py                         # ostatnie 20 wysyłek
py tools/ksef_status.py --status ERROR          # filtr po statusie
py tools/ksef_status.py --gid 123456            # historia GID (wszystkie attempts)
py tools/ksef_status.py --today                 # tylko dzisiejsze
```

Output: tabela ASCII (stdlib) — kolumny: id, gid, rodzaj, nr, status, ksef_number, attempt, sent_at.

---

## Testy

### Repo tests — `tests/ksef/test_ksef_repo.py`

Biblioteka: `pytest` + `tempfile.mkdtemp` (osobny DB per test).

Scenariusze (minimum ~25 testów):

**Happy path:**
- `create()` tworzy wiersz w stanie DRAFT z poprawnymi timestampami
- `get(id)` zwraca utworzony obiekt
- `get_latest(gid, rodzaj)` zwraca najnowszą próbę (najwyższy `attempt`)
- `transition(DRAFT → QUEUED)` ustawia `queued_at`
- `transition(SENT → ACCEPTED)` ustawia `accepted_at` + `ksef_number`
- `list_by_status(ERROR)` zwraca tylko wiersze w stanie ERROR

**State machine:**
- `transition(DRAFT → SENT)` → `InvalidTransitionError` (pomijamy QUEUED, AUTH_PENDING)
- `transition(ACCEPTED → *)` → `InvalidTransitionError` (stan terminalny)
- Każde niedozwolone przejście per macierz `_ALLOWED`

**Idempotency:**
- `create()` dla (gid=1, FS) gdy istnieje QUEUED → `ShipmentAlreadyActiveError`
- `create()` dla (gid=1, FS) gdy istnieje ACCEPTED → `ShipmentAlreadyActiveError`
- `create()` dla (gid=1, FS) gdy istnieje tylko ERROR → OK (ERROR nie jest aktywny)
- `new_attempt()` po ERROR tworzy wiersz z `attempt=2`

**Audit trail:**
- Po `transition()` powstaje wpis w `ksef_transition` z from/to status
- Historia 3 przejść = 3 wpisy w audit table

**Edge cases:**
- `get(nonexistent_id)` → None (nie wyjątek)
- `has_pending_or_sent` zwraca False gdy wszystkie attempts w stanie terminalnym (ACCEPTED też?) — **UWAGA:** ACCEPTED blokuje nową próbę (już wysłano do KSeF), ERROR i REJECTED nie blokują. Pokryj testem.
- `xml_hash` NULL → reject przez NOT NULL constraint

**Konkurencja:**
- Dwa `create()` dla tego samego (gid, rodzaj, attempt=1) w dwóch wątkach → jeden success, drugi `ShipmentAlreadyActiveError`

### Schema tests — `tests/ksef/test_ksef_schema.py`

- `init_schema()` na pustej DB tworzy tabele + indeksy
- `init_schema()` na istniejącej DB z v1 nie robi zmian (idempotent)
- Wszystkie CHECK constraints aktywne (zapis niepoprawnego statusu → IntegrityError)
- `schema_version` zawiera 1

### Integration — nie potrzebne

Block 2 to czysty local state — zero I/O poza SQLite. Nie ma nic do testowania integracyjnie.

---

## Acceptance criteria

- [ ] `data/ksef.db` tworzony przez `py tools/ksef_init_db.py` — schema aktywna
- [ ] `ShipmentRepository` ze wszystkimi metodami z kontraktu, 100% typed
- [ ] State machine z `is_valid_transition()` + `_ALLOWED` macierzą
- [ ] Repo tests: ≥25 testów, 100% PASS
- [ ] Schema tests: 4+ testy, 100% PASS
- [ ] `tools/ksef_status.py` działa na pustej DB (pokazuje "brak wysyłek") i z danymi
- [ ] `.gitignore` zawiera `data/ksef.db*` (plus WAL/journal/shm)
- [ ] `data/.gitkeep` commitowany (katalog istnieje w repo)
- [ ] Audit trail: każde `transition()` zapisuje wpis w `ksef_transition`
- [ ] Zero zmian w `core/ksef/adapters/` z Block 1 (http, ksef_api, ksef_auth) — repo to osobny pakiet

### Jakość kodu (L3 Senior — kontynuacja standardów z Block 1)

- Funkcje ≤15 linii (helpery z uzasadnieniem mogą być dłuższe)
- Zero `print()` — `logging`
- Typed throughout (mypy clean)
- `from __future__ import annotations` + PEP 604
- SQL w osobnym pliku (`schema.sql`), nie inline w Pythonie
- Connection jako context manager, zawsze z transakcją
- Frozen dataclass dla `Wysylka` (immutable — uniknij "czy to kopia czy oryginał")
- Boundary validation: row (sqlite) → Wysylka w jednym miejscu (`_row_to_wysylka`)

---

## Out of scope w Block 2 (świadomie)

- **Integracja z KSeF API** — to M4 (Block 4). Tu tylko state store.
- **ERP reader (SQL z ERP XL)** — to M0 (Block 3). Tu tylko ślad wysyłki.
- **XML generation / konsolidacja** — to Block 3 (M0). Tu XML dostajemy z parametru (`xml_path`).
- **Alembic** — raw SQL w schema.sql wystarczy do M6.
- **Multi-tenant** — CEiM = jedna firma.
- **Encryption at rest** — SQLite plain, backup polityką dysku.
- **Web UI** — CLI + tabela wystarczy.
- **Metrics / Prometheus** — M6.

---

## Punkty uwagi dla Developera

1. **WAL mode** — `PRAGMA journal_mode = WAL` zapewnia konkurencyjny odczyt podczas pisu (ważne dla `ksef_status.py` obok daemona). Weryfikuj że DB po `init_schema()` faktycznie jest w WAL.

2. **Timestampy w UTC** — wszystkie `*_at` zapisywane jako UTC naive (`datetime.utcnow()`). CLI `ksef_status.py` konwertuje do lokalnego przy wyświetleniu. Reason: serwer i tak jest na PL timezone, ale DB neutralna.

3. **Idempotency klucz** — `UNIQUE (gid_erp, rodzaj, attempt)` nie `(gid_erp, rodzaj)`. Powód: retry po ERROR tworzy nowy wiersz, nie nadpisuje. Testy konkurencyjne muszą to uwzględniać.

4. **`has_pending_or_sent` dokładna semantyka** — blokuje nową próbę gdy istnieje wpis w `{QUEUED, AUTH_PENDING, SENT, ACCEPTED}`. Stany ERROR/REJECTED **nie blokują** (dozwolona kolejna próba — ale przez `new_attempt()`, nie `create()`).

5. **Transition meta** — parametr `meta: dict` jest serializowany do `meta_json` w audit table. Używamy przy `transition(ERROR, meta={'step': 'auth', 'exc': '...'})`. Validacja że dict jest JSON-serializable przed zapisem.

6. **Konkurencja** — SQLite z WAL pozwala na 1 writer + N readers. Dla daemon (single writer) to wystarczy. W teście konkurencji użyj `threading` + 2 writery = jeden IntegrityError. Nie multiprocessing.

7. **Nie używaj ORM** — czysty `sqlite3` stdlib. Reason: zero new deps, pełna kontrola nad SQL-em, kontekst projektu (mrowisko.db też surowe sqlite).

8. **Migration future-proof** — `schema_version` tabela daje punkt zaczepienia gdy w M6 pojawi się v2. Teraz tylko rejestruj v1.

9. **XML hash** — SHA-256 hex (64 znaki). Policz z bytes XML po walidacji XSD. Hash NIE jest dla bezpieczeństwa — tylko dla integrity check "czy plik na dysku to ten sam co wysłano".

10. **`data/` w repo** — tylko `.gitkeep`. `.db` i WAL/journal/shm pliki wyłącznie w `.gitignore`.

---

## Workflow i handoff z powrotem

Developer realizuje przez `workflow_developer_tool` (nowy moduł + CLI).

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "ksef_block_2_review" --status PASS \
  --summary "Block 2 zaimplementowany: schema, repo, init_db, status CLI, 25+ testów PASS" \
  --next-action "Code review — core/ksef/{domain,adapters/repo.py,schema.sql}, tools/ksef_{init_db,status}.py, tests/ksef/test_ksef_{repo,schema}.py"
```

Po PASS code review → Block 3 (M0 konsolidacja XML) lub Block 4 (M4 SendInvoice) — decyzja człowieka po review.

---

## Ryzyka Block 2

| Ryzyko | Mitygacja |
|---|---|
| State machine za ciasny — jakiś realny case nie pasuje | Macierz `_ALLOWED` w jednym miejscu, łatwo rozszerzyć + test per przejście |
| SQLite lock przy konkurencji | WAL mode + single-writer pattern; dokumentacja "1 daemon, N readers" |
| Zapomniany `*_at` timestamp przy transition | Test per przejście sprawdza że timestamp ustawiony |
| Audit log puchnie (30 dok/dzień × 5 transitions × 365 dni = ~55k/rok) | Akceptowalne; cleanup polityką w M6 (archiwizacja po N miesiącach) |
| Race na `create()` przy równoczesnej pracy dwóch narzędzi | UNIQUE constraint + translacja IntegrityError → ShipmentAlreadyActiveError |
