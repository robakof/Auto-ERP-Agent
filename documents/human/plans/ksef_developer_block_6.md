# Developer Block 6 — KSeF M5 Auto-scan Daemon (ScanErp + batch dispatch)

Data: 2026-04-16
Autor: Architect
Dotyczy planu: `documents/human/plans/ksef_api_automation.md` (§5 M5)
Dla roli: Developer
Status: Ready to start
Prerequisites: Block 1 ✓ (API), Block 2 ✓ (Shadow DB), Block 3 ✓ (XML), Block 4 ✓ (SendInvoice e2e)

---

## Cel bloku

Daemon skanuje ERP co N sekund, wykrywa nowo zatwierdzone FS/FSK, automatycznie
wysyła każdy dokument na KSeF przez istniejący `SendInvoiceUseCase`.

Po ukończeniu: `py tools/ksef_daemon.py` działa w tle — nowa zatwierdzona faktura
w ERP XL pojawia się w KSeF bez interwencji operatora.

**Constraint:** Daemon nie modyfikuje ERP XL. Jedyne źródło stanu wysyłek = shadow DB (`data/ksef.db`).

---

## Co już istnieje (z Block 1-4)

| Komponent | Lokalizacja | Status |
|---|---|---|
| SendInvoiceUseCase (full e2e) | `core/ksef/usecases/send_invoice.py` | ✓ Block 4 |
| ShipmentRepository (CRUD, state machine) | `core/ksef/adapters/repo.py` | ✓ Block 2 |
| ErpReader (SQL → domain, filters: gids, date_from/to) | `core/ksef/adapters/erp_reader.py` | ✓ Block 3 |
| XmlBuilder (domain → XML) | `core/ksef/adapters/xml_builder.py` | ✓ Block 3 |
| KSeFAuth + KSeFEncryption | `core/ksef/adapters/` | ✓ Block 1+4 |
| config.py (KSEF_ENV, KSEF_TOKEN, KSEF_NIP) | `core/ksef/config.py` | ✓ Block 1 |
| SQL views: ksef_fs_draft.sql, ksef_fsk_draft.sql | `solutions/ksef/` | ✓ Pre-Block |

**Co brakuje (scope Block 6):**
1. `core/ksef/usecases/scan_erp.py` — wykrycie nowych zatwierdzonych dokumentów
2. `tools/ksef_daemon.py` — tick loop z graceful shutdown
3. Filtr "zatwierdzony" w SQL (`TrN_Bufor = 0`)
4. XML generation pipeline (ErpReader → XmlBuilder → file → SendInvoice)
5. Testy: unit + contract

---

## Odpowiedzi na pytania Q1-Q3

### Q1: ScanErp — flaga "zatwierdzona" z ERP XL

**Developer może zidentyfikować samodzielnie. Handoff do ERP Specialist nie wymagany.**

W Comarch XL `CDN.TraNag`:
- `TrN_Bufor = 0` → dokument zatwierdzony (usunięty z bufora)
- `TrN_Bufor = 1` → dokument w buforze (draft, niezatwierdzony)

Istniejące SQL (`ksef_fs_draft.sql:232`, `ksef_fsk_draft.sql:319`) filtrują po `TrN_GIDTyp` (2033=FS, 2041=FSK) ale **nie filtrują po `TrN_Bufor`**. Dodaj warunek:

```sql
WHERE n.TrN_GIDTyp = 2033
  AND n.TrN_Bufor = 0    -- tylko zatwierdzone
```

**Uwaga:** Nie modyfikuj istniejących SQL views. ScanErp buduje **własne** lekkie zapytanie
(tylko GIDNumer + numer + data) z warunkiem `TrN_Bufor = 0`. Pełne dane dokumentu
czyta `ErpReader.fetch_faktury()` dopiero po decyzji o wysyłce.

### Q2: Daemon — prosty loop z sleep (nie Windows service)

**Rekomendacja: prosty loop z `time.sleep()` + graceful shutdown (`signal.SIGINT`).**

Uzasadnienie:
- ~20-30 dok/dzień to triwalny throughput — nie wymaga service managera
- Operator uruchamia ręcznie lub przez Task Scheduler
- Łatwiejsze debugowanie niż Windows service
- `Ctrl+C` = graceful shutdown (dokończ bieżący dokument, close session)
- Docelowo (M6): wrapper jako Windows service jeśli wymagane — osobny scope

Deployment: `py tools/ksef_daemon.py` w terminalu lub Task Scheduler z `pythonw`.

### Q3: Batch send — 1 sesja per dokument (bez zmian)

**Rekomendacja: zachowaj 1 sesja per dokument (jak Block 4).**

Uzasadnienie:
- Decyzja z planu architektonicznego (§2: "pojedyncza sesja per dokument")
- Upraszcza recovery — błąd w jednym dokumencie nie blokuje sesji z innymi
- ~20-30 dok/dzień × ~5s per send = ~2.5 min/dzień — narzut auth/session opening marginalny
- State machine w shadow DB śledzi per-dokument (DRAFT→ACCEPTED) — batch wymagałby refaktoru
- Batch optimization to oddzielny milestone jeśli skala wzrośnie

**Implikacja:** Daemon robi N iteracji `SendInvoiceUseCase.execute()` w pętli, nie batch.

---

## Scope — co dokładnie powstaje

### 1. Use case: `core/ksef/usecases/scan_erp.py` (NOWY, ~120 linii)

```python
@dataclass(frozen=True)
class PendingDocument:
    """Dokument z ERP wykryty do wysyłki."""
    gid: int
    rodzaj: str                     # "FS" | "FSK"
    nr_faktury: str
    data_wystawienia: date


class ScanErpUseCase:
    """Wykrywa nowo zatwierdzone dokumenty z ERP nie obecne w shadow DB."""

    def __init__(
        self,
        run_query: RunQuery,
        repo: ShipmentRepository,
    ) -> None: ...

    def scan(self) -> list[PendingDocument]:
        """
        Flow:
        1. Query ERP: zatwierdzone FS (TrN_GIDTyp=2033, TrN_Bufor=0)
           → lista (GIDNumer, numer_faktury, data_wystawienia)
        2. Query ERP: zatwierdzone FSK (TrN_GIDTyp=2041, TrN_Bufor=0)
           → lista (GIDNumer, numer_korekty, data_wystawienia)
        3. Filtruj: odrzuć GIDy które już istnieją w shadow DB
           (has_pending_or_sent LUB status=ACCEPTED)
        4. Return sorted by data_wystawienia ASC (najstarsze najpierw)
        """
```

**Scan SQL — lekkie zapytanie (nie full view):**

```sql
-- FS: lista zatwierdzonych FS do wysyłki
SELECT
    n.TrN_GIDNumer                                          AS gid,
    'FS-' + CAST(n.TrN_TrNNumer AS VARCHAR(20))
        + '/' + RIGHT('0' + CAST(MONTH(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(2)), 2)
        + '/' + RIGHT(CAST(YEAR(DATEADD(day, n.TrN_Data2, '1800-12-28')) AS VARCHAR(4)), 2)
        + '/' + RTRIM(n.TrN_TrNSeria)                      AS nr_faktury,
    CONVERT(DATE, DATEADD(day, n.TrN_Data2, '1800-12-28'))  AS data_wystawienia
FROM CDN.TraNag n
WHERE n.TrN_GIDTyp = 2033
  AND n.TrN_Bufor = 0
```

Analogicznie dla FSK (TrN_GIDTyp=2041).

**Filtrowanie na stronie Pythona** (nie SQL): ScanErp pobiera listę GIDów, odrzuca te które `repo.has_pending_or_sent()` lub `repo.get_latest()` z ACCEPTED. Powód: shadow DB = SQLite, ERP = MSSQL — nie da się JOIN cross-DB.

### 2. Pipeline: XML generation (w ScanErp lub Daemon)

Daemon per pending document:
1. `ErpReader.fetch_faktury(gids=[gid])` → domain `Faktura`
2. `XmlBuilder.build_faktura(faktura)` → `xml_bytes`
3. Zapisz XML do `output/ksef/{filename}.xml`
4. `SendInvoiceUseCase.execute(xml_path, gid, rodzaj, nr, data_wyst)` → result

**Uwaga:** SendInvoiceUseCase oczekuje `xml_path` (Path do pliku). Daemon generuje XML
na dysk przed wysyłką. Tymczasowy plik w `output/ksef/` — zachowany dla audytu.

### 3. Daemon: `tools/ksef_daemon.py` (NOWY, ~150 linii)

```python
"""KSeF daemon — auto-scan ERP + send approved invoices.

    py tools/ksef_daemon.py                     # default: tick co 60s
    py tools/ksef_daemon.py --interval 30       # tick co 30s
    py tools/ksef_daemon.py --once              # single scan + send, exit
    py tools/ksef_daemon.py --dry-run           # scan only, show what would be sent
"""

class KSeFDaemon:
    def __init__(
        self,
        scan: ScanErpUseCase,
        send_factory: Callable[[PendingDocument], SendResult],
        *,
        interval_s: float = 60.0,
        on_tick: Callable[[int, list[PendingDocument]], None] = _default_on_tick,
    ) -> None: ...

    def run(self) -> None:
        """Main loop. Ctrl+C = graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        while not self._shutdown:
            pending = self._scan.scan()
            self._on_tick(self._tick_count, pending)
            for doc in pending:
                if self._shutdown:
                    break
                self._process_one(doc)
            self._tick_count += 1
            self._sleep_interruptible(self._interval)

    def run_once(self) -> list[SendResult]:
        """Single scan + send. Returns results."""

    def _process_one(self, doc: PendingDocument) -> SendResult | None:
        """Generate XML + send. Errors logged, not raised."""
        try:
            result = self._send_factory(doc)
            return result
        except Exception as exc:
            _LOG.error(...)
            return None

    def _handle_shutdown(self, sig, frame) -> None:
        """Set shutdown flag — current document finishes, then exit."""
        self._shutdown = True

    def _sleep_interruptible(self, seconds: float) -> None:
        """Sleep in small increments, checking shutdown flag."""
```

**Kontrakt:**
- `send_factory` callback: daemon buduje pipeline (ErpReader→XmlBuilder→file→SendInvoiceUseCase) per document. Wstrzykiwane dla testowalności.
- `--once` mode: single tick, return results, exit. Przydatne do testowania i Task Scheduler.
- `--dry-run`: scan + print, zero API calls.
- Graceful shutdown: `self._shutdown = True` → bieżący `_process_one` kończy, loop exits.
- Sleep interruptible: zamiast `time.sleep(60)` → loop z `time.sleep(1)` × 60 sprawdzając `_shutdown`.
- Error isolation: błąd w jednym dokumencie → log + continue. Nie zatrzymuje kolejnych.

**CLI parametry:**
- `--interval N` — sekundy między tickami (default 60)
- `--once` — single scan + send, exit
- `--dry-run` — scan only
- `--date-from` / `--date-to` — filtr zakresu dat (opcjonalny, default: brak = wszystkie zatwierdzone)
- `--rodzaj FS|FSK` — filtruj typ dokumentu (opcjonalny, default: oba)

### 4. Aktualizacja: `core/ksef/adapters/repo.py`

Dodaj metodę potrzebną do ScanErp:

```python
def is_known(self, gid: int, rodzaj: str) -> bool:
    """Czy GID istnieje w shadow DB w jakimkolwiek stanie (nie tylko active)."""
```

Istniejący `has_pending_or_sent` sprawdza active stany. ScanErp potrzebuje wiedzieć
czy GID w ogóle był przetwarzany (włącznie z ACCEPTED, REJECTED, ERROR) —
bo ACCEPTED nie powinien być ponownie wysyłany.

Alternatywa: `get_latest(gid, rodzaj)` już istnieje — ScanErp może sprawdzić
`get_latest() is not None`. **Decyzja Developera** — oba podejścia OK. Ważne:
ACCEPTED = nie wysyłaj ponownie. ERROR/REJECTED = **też** nie wysyłaj automatycznie
(wymaga ręcznej interwencji lub explicit retry).

### 5. Testy

#### Unit: `tests/ksef/test_scan_erp.py` (NOWY)

```
test_scan_returns_pending_fs()
test_scan_returns_pending_fsk()
test_scan_excludes_already_in_shadow_db()
test_scan_excludes_accepted()
test_scan_excludes_error()                   # nie auto-retry!
test_scan_empty_erp_returns_empty()
test_scan_sql_error_raises()
test_scan_sorted_by_date_asc()
```
Minimum: **≥8 unit**

#### Contract: `tests/ksef/test_daemon.py` (NOWY)

Daemon z full mock (scan + send_factory):

```
test_daemon_once_processes_all_pending()
test_daemon_once_returns_results()
test_daemon_dry_run_no_send()
test_daemon_graceful_shutdown_mid_batch()
test_daemon_error_one_continues_next()
test_daemon_empty_scan_no_send()
test_daemon_tick_count_increments()
```
Minimum: **≥7 contract**

#### Minimum testów

- ScanErp: ≥8 unit
- Daemon: ≥7 contract
- **Total nowych: ≥15 + zachowane 149 z Block 1-4 = ≥164 PASS**

---

## Decyzje zatwierdzone

| Decyzja | Wybór | Uzasadnienie |
|---|---|---|
| Flaga "zatwierdzony" | `TrN_Bufor = 0` | Standard Comarch XL, nie wymaga ERP Specialist |
| Daemon type | Prosty loop + sleep | ~20-30 dok/dzień, nie wymaga service managera |
| Session policy | 1 per dokument (jak Block 4) | Recovery, state machine per-dokument |
| Scan SQL | Lekkie zapytanie (GID+nr+data) | Pełne dane lazy-load przez ErpReader |
| Cross-DB filter | Python-side (not SQL JOIN) | SQLite + MSSQL = no cross-DB join |
| Error policy | Log + skip, nie zatrzymuj | Błąd jednego dokumentu nie blokuje kolejnych |
| Retry policy | Brak auto-retry | ERROR/REJECTED wymaga ręcznej interwencji |
| Graceful shutdown | signal handler + interruptible sleep | Ctrl+C bezpieczne |

---

## Out of scope (świadomie)

- **Batch send** (wiele faktur w jednej sesji KSeF) — osobny milestone jeśli skala wzrośnie
- **Windows service wrapper** — M6 (observability) jeśli wymagane
- **Auto-retry failed documents** — wymaga policy decision (ile razy? jaki backoff?)
- **Rate limiting** — M6 scope (ochrona przed bug w daemon)
- **Dashboard / status CLI** — M6 scope
- **Prod safety guard** — M6 scope (`KSEF_PROD_CONFIRMED`)
- **Notyfikacja o błędach** (flag do człowieka) — M6 scope

---

## Ryzyka

| Ryzyko | Mitygacja |
|---|---|
| `TrN_Bufor` nie pokrywa wszystkich stanów zatwierdzenia | Weryfikacja na real DB; jeśli odkryjesz edge case — flag do Architekta |
| ERP niedostępne (MSSQL offline) | ErpReader rzuca wyjątek → daemon loguje, retry na następnym tick |
| Duży backlog na starcie (setki zatwierdzonych faktur) | `--date-from` filtr na CLI; daemon przetwarza po kolei |
| Shadow DB locked (concurrent access) | WAL mode z Block 2 + SQLite single writer |
| XML generation failure (ErpReader/XmlBuilder) | Error isolation — log + skip, nie crash daemon |
| Daemon dies mid-send | SendInvoiceUseCase zostawia stan w shadow DB; restart daemon = idempotency check |

---

## Kolejność pracy (rekomendacja)

1. **scan_erp.py** (use case) + unit testy — izolowany moduł, mock run_query + repo
2. **repo.py update** — `is_known()` lub użyj `get_latest()` (decyzja Developera)
3. **ksef_daemon.py** — tick loop + graceful shutdown + `--once` mode
4. Contract testy daemon (full mock)
5. Integration test: `py tools/ksef_daemon.py --once --dry-run` na real ERP
6. Full test: `py tools/ksef_daemon.py --once` na Demo (real send)

---

## Workflow i handoff

Developer realizuje przez `workflow_developer_tool`.

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "ksef_block_6_review" --status PASS \
  --summary "Block 6: daemon + scan_erp. --once mode verified on Demo. 164+ tests PASS." \
  --next-action "Code review — core/ksef/usecases/scan_erp.py, tools/ksef_daemon.py, tests/ksef/test_{scan_erp,daemon}.py"
```

Po PASS → M6 observability (dashboard, rate limits, Prod safety) — decyzja człowieka.
