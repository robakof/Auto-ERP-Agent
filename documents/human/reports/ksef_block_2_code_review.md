# Code Review: KSeF Block 2 (Shadow DB + Repository + CLI)

Date: 2026-04-15
Branch: main
Reviewer: Architect
Plan: `documents/human/plans/ksef_developer_block_2.md`
Handoff: msg #70 (developer → architect)

## Summary

**Overall assessment:** **NEEDS REVISION** (1 Critical: brak `-wal`/`-shm` w `.gitignore`)
Po naprawie Critical → PASS bez kolejnej rundy.

**Code maturity level:** **L3 Senior** — warstwy domain/adapter rozdzielone, boundary parsing w jednym miejscu (`_row_to_wysylka`), immutable frozen dataclass, state machine jako pure function (macierz `_ALLOWED` + `is_valid_transition`), DI (clock), whitelist dozwolonych pól transition (fieldname injection defense), WAL mode persystentny, audit trail atomowy z mutacją. Dla L4 brakowałoby: schema v2+migration testu, observability (metrics), self-healing przy uszkodzonej DB.

**Tests:** 88/88 PASS (repo 30 + schema 7 + Block 1: auth 10 + api 41).

**Acceptance vs deliverable:**
- ✓ `core/ksef/schema.sql` — tabele + indeksy + schema_version + check constraints
- ✓ Domain: `Wysylka` (frozen), `ShipmentStatus` (Enum), `is_valid_transition`, `is_active` + `StatusTransition`
- ✓ `ShipmentRepository` — wszystkie metody kontraktu (get, get_latest, has_pending_or_sent, list_by_status, list_recent, create, new_attempt, transition, init_schema)
- ✓ Exceptions hierarchy rozszerzona: `KSefRepoError` + 3 konkretne
- ✓ `tools/ksef_init_db.py` + `tools/ksef_status.py`
- ✓ Testy: repo 30 (plan wymagał ≥25), schema 7 (plan wymagał 4+)
- ✓ WAL mode zweryfikowane: `PRAGMA journal_mode → wal`
- ✓ `data/.gitkeep` w repo; `data/ksef.db*` w `.gitignore` (częściowo — patrz Critical)
- ✓ Zero zmian w Block 1 kodzie (http.py, ksef_api.py, ksef_auth.py netkinięte)
- ✓ Audit trail działa: 3 transitions = 3 wpisy w `ksef_transition`
- ✓ Konkurencja: test dwóch wątków, jeden wygrywa — zgodnie z kontraktem

---

## Findings

### Critical Issues (must fix przed PASS)

- **`.gitignore:41-42`** — brak `data/ksef.db-wal` i `data/ksef.db-shm`. WAL mode **tworzy te pliki automatycznie** przy każdej otwartej sesji (WAL = Write-Ahead Log, SHM = shared memory). Plan §Punkty uwagi 10 explicite wymienił je. Obecnie:
  ```
  data/ksef.db
  data/ksef.db-journal
  ```
  Ma być:
  ```
  data/ksef.db
  data/ksef.db-journal
  data/ksef.db-wal
  data/ksef.db-shm
  ```
  Bez tego po pierwszym `py tools/ksef_init_db.py` na serwerze do commita mogą wpaść śmieciowe pliki.

### Warnings (should fix)

- **`tools/ksef_status.py:50`** — `--gid` hard-coduje `rodzaj="FS"`:
  ```python
  latest = repo.get_latest(args.gid, "FS")
  ```
  Dokumentacja mówi "historia GID (wszystkie attempts)", a:
  1. Obsługiwane jest tylko FS, FSK nie pokaże się
  2. Zwracany jest tylko `get_latest` zamiast wszystkich attempts
  
  Fix: dodaj `--rodzaj FS|FSK|BOTH` (default BOTH) + odczyt przez nowe `repo.list_by_gid(gid, rodzaj)` zwracające wszystkie attempts ORDER BY attempt DESC. Alternatywa minimalna: dwa wywołania `get_latest(gid, "FS")` + `get_latest(gid, "FSK")`. Preferowane pierwsze — ważne dla audytu.

- **`tools/ksef_status.py:61-63`** — `--today` filtruje po UTC:
  ```python
  today = datetime.now(timezone.utc).date()
  rows = [w for w in rows if w.created_at.date() == today]
  ```
  DB zapisuje naive UTC, ale operator używa serwera w strefie PL. Po godzinie 22:00 lokalnego czasu `--today` zacznie pokazywać "jutrzejsze" dokumenty, a przed 01:00 może zjeść "wczorajsze". 
  
  Fix: użyj `datetime.now().astimezone()` → local date, filtruj po konwersji `w.created_at` do lokalnego (lub zaakceptuj UTC i udokumentuj w `--help`).

- **`tools/ksef_status.py:48-64` (`_select`)** — kombinacja flag nie jest jasna:
  - `--gid + --status` → `--status` ignorowany (`_select` wraca na linii 51, status nie brany pod uwagę)
  - `--gid + --limit` → `--limit` ignorowany (zawsze 1 wiersz z `get_latest`)
  - `--gid + --today` → OK (filtr po `--gid` result)
  
  Fix powiązany z poprzednim Warning — jeśli `--gid` zwróci listę z repo, pozostałe flagi będą stosowane spójnie.

### Suggestions (nice to have)

- **`core/ksef/adapters/repo.py:281-286`** — `_ACTIVE_STATUS_NAMES` wyliczane ręcznie, duplikuje `_ACTIVE_STATES` z `domain/shipment.py`. DRY:
  ```python
  # w domain/shipment.py:
  ACTIVE_STATUSES: tuple[ShipmentStatus, ...] = tuple(sorted(_ACTIVE_STATES, key=lambda s: s.value))
  # w repo.py:
  from core.ksef.domain.shipment import ACTIVE_STATUSES
  _ACTIVE_STATUS_NAMES = tuple(s.value for s in ACTIVE_STATUSES)
  ```

- **`core/ksef/adapters/repo.py:107-115`** — `placeholders = ",".join("?" * len(...))` wyliczane per wywołanie. Przenieś na poziom modułu jako stałą.

- **`core/ksef/adapters/repo.py:323-328` (`_as_datetime`)** — rejestrujesz `register_converter("TIMESTAMP", ...)` (linia 39) więc row z PARSE_DECLTYPES zwraca już `datetime`. Fallback `datetime.fromisoformat(str(value))` jest dead path w happy case. Można albo usunąć (polegać na konwerterze), albo udokumentować dlaczego zostawiony (defensywnie przy starych DB bez DECLTYPES). Kosmetyka.

- **`core/ksef/adapters/repo.py:36-39`** — `sqlite3.register_adapter`/`register_converter` na poziomie modułu ma globalny side-effect. Jeśli kiedyś inny moduł zaimportuje się i zarejestruje inny converter dla DATE/TIMESTAMP — kolizja. Zmień na rejestrację w `__init__` repo (lub connection-scoped). Nie blokuje teraz, ale sygnał dla M6.

- **`tests/ksef/test_ksef_repo.py:231-236`** — `assert rows == [("DRAFT", "QUEUED", '{"by": "test"}')]` — kruchy assert na format JSON (space po `:`). Jeśli ktoś doda `json.dumps(..., separators=(',',':'))` — test pada bez winy. Lepsze: parse meta_json i asercja na dict `{"by": "test"}`.

- **`tools/ksef_status.py:73`** — `zip(_COLS, widths)` bez `strict=True`. Python 3.10+ support. Nie blokuje, ale dobra praktyka.

- **`tools/ksef_status.py`** — brak `--db-readonly` / otwarcia w trybie `?mode=ro`. Przy aktywnym daemonie mającym write-lock, status może zacinać się na chwilowe locki. WAL to łagodzi, ale explicit readonly connection jest bezpieczniejszy. Można dodać w M6.

---

## Recommended Actions

Developer wykonuje patch:

- [ ] **C1** `.gitignore` — dodać `data/ksef.db-wal` i `data/ksef.db-shm`. Zweryfikować `git check-ignore data/ksef.db-wal` po zmianie.
- [ ] **W1** `tools/ksef_status.py --gid` — dodać obsługę FSK + wszystkich attempts (nowa metoda `repo.list_by_gid(gid, rodzaj=None)` lub dwa wywołania `get_latest`). Zaktualizować `--help`.
- [ ] **W2** `tools/ksef_status.py --today` — filtr po local date zamiast UTC (albo udokumentuj w help że to UTC, zdecyduj).
- [ ] **W3** `_select()` — spójna interakcja flag. Po fix W1 powinno wyjść naturalnie.
- [ ] **Suggestions S1-S6** — opcjonalne. Jeśli zostawia bez zmian, niech krótko uzasadni w handoff.

Po wykonaniu C1-W3: handoff zwrotny do Architekta na drugie review (krótkie — tylko delta).

---

## Architektura — co zostało zrobione dobrze

Warto utrwalić jako wzorzec:

1. **Whitelist dozwolonych pól transition** — `_ALLOWED_TRANSITION_FIELDS` + `ValueError` przy nieznanym kluczu. Chroni przed `transition(id, QUEUED, drop_table="users")` (SQL injection via column name). Rzadko spotykane, bardzo dobre.
2. **Terminal timestamp column map** — `_TERMINAL_TIMESTAMP_COL` mapuje stan → kolumnę. Jeden punkt zmiany gdy dodajemy nowy stan z timestampem. Kod jeden, reguła deklaratywna.
3. **State machine jako pure function** — `is_valid_transition(old, new)` bez side-effectów. Testowalne bez DB. Jedno źródło prawdy o dozwolonych przejściach.
4. **Audit table osobna** — `ksef_transition` vs `ksef_wysylka`. Stan aktualny i historia rozdzielone. Pattern event sourcing-lite.
5. **Frozen dataclass Wysylka** — zero "czy to kopia?". Każda mutacja wraca nowy obiekt z repo.
6. **Konkurencja testowana realnie** — 2 wątki + assertion że jeden dostaje `IntegrityError`. Nie polegamy na teorii UNIQUE constraint.
7. **`init_schema()` idempotent** — `IF NOT EXISTS` + `INSERT OR IGNORE` — drugie wywołanie bez efektu. Pozwala na "restart serwera, uruchom init_db, spokojnie".
8. **WAL mode w `schema.sql`** — `PRAGMA journal_mode = WAL` persystentny w DB file. Ustawione raz, działa dla wszystkich connections.

---

## Wnioski strategiczne

Block 2 ma solidny fundament persistencji. Po naprawie 1 Critical mamy bazę pod:
- **Block 3 (M0)** — konsolidacja XML, pisze `xml_path` + `xml_hash` do DB przy `create`
- **Block 4 (M4)** — SendInvoice use case używa `has_pending_or_sent` przed startem
- **Block 5 (M5)** — daemon polluje `list_by_status(DRAFT)` co tick

**Pattern do wpisania w `PATTERNS.md`** (osobny task, po Block 2):
- "Forward-only State Machine with Retry-as-New-Row" — nie update istniejącego wiersza, tylko nowy attempt. Audit + restart recovery + retry policy w jednym.
- "Whitelist Column Fields in Dynamic UPDATE" — obrona przed injection przy kwargs-based transition API.
