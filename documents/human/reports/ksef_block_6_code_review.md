# Code Review: KSeF Block 6 — M5 Daemon (ScanErp + auto-send)

Date: 2026-04-16
Reviewer: Architect
Branch: main (commit ae6e478)
Plan: `documents/human/plans/ksef_developer_block_6.md`
Handoff: msg #98 (developer → architect), detale: `tmp/handoff_block_6_review.md`

## Summary

**Overall assessment: PASS**
**Code maturity level: L3 Senior** — frozen dataclasses, DI throughout (run_query, repo, send_factory, sleep, on_tick), structured JSON logging, graceful shutdown (signal handler + interruptible sleep), error isolation per document. Clean separation scan_erp (use case) vs daemon (orchestration loop) vs CLI (wiring).

**Tests:** 166/166 PASS (17 nowych + 149 z Block 1-4). ScanErp: 9 unit. Daemon: 8 contract.

**Acceptance criteria vs deliverable:**

| Criterium | Status |
|---|---|
| scan_erp.py — lekkie SQL, TrN_Bufor=0, Python-side filter | ✓ 119 L |
| ksef_daemon.py — tick loop, graceful shutdown, --once, --dry-run | ✓ 246 L |
| Error isolation: błąd jednego nie blokuje kolejnych | ✓ tested |
| Graceful shutdown (SIGINT/SIGTERM) | ✓ interruptible sleep, tested |
| is_known via get_latest (YAGNI — no new repo method) | ✓ good call |
| --once mode for testing/Task Scheduler | ✓ |
| --dry-run mode | ✓ |
| Tests ≥15 nowych, suite ≥164 | ✓ 17 nowych, suite 166 |

## Decyzje developera — ocena

### `get_latest() is not None` zamiast nowej metody `is_known()` → **APPROVE**
YAGNI. Istniejąca metoda repo wystarczy. Zero nowego kodu w repo.py. Dobrze.

### `_generate_xml` w daemon CLI → **APPROVE**
Pipeline ErpReader→XmlBuilder→file żyje w `ksef_daemon.py` (CLI wiring), nie w use case.
Poprawne — daemon = wiring layer, use cases nie wiedzą o sobie nawzajem.

### ScanErp error: return `[]` zamiast raise → **APPROVE**
`_query_erp` loguje błąd i zwraca pustą listę. Daemon kontynuuje na następnym tick.
Correct for scan — daemon nie powinien crashować gdy ERP tymczasowo niedostępne.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1: Duplicate `_run_query` definition — linie 155-157 i 209-211**

`ksef_daemon.py` definiuje `_run_query` lambda dwukrotnie:
- W `_build_send_factory()` (linia 155) — używane przez ErpReader w pipeline
- W `main()` (linia 209) — używane przez ScanErpUseCase

Obie są identyczne. Wyciągnij do jednej definicji w `main()` i przekaż do obu.

**W2: `_build_send_factory` tworzy drugie repo (linia 148)**

`main()` tworzy `repo` (linia 213) dla ScanErpUseCase. `_build_send_factory()` tworzy
osobne `repo` (linia 148) dla SendInvoiceUseCase. Dwa `ShipmentRepository` na ten sam plik DB.

W praktyce SQLite WAL mode obsługuje to, ale to niepotrzebna duplikacja.
Lepiej: `_build_send_factory(repo, ...)` — przekaż jedno repo.

Analogicznie: `_build_send_factory` wewnętrznie tworzy `cfg`, `http`, `api`, `auth`, `encryption`
— te obiekty mogłyby być tworzone raz w `main()` i przekazywane. Ale to refaktor wiring code,
nie core logic. **Non-blocking — nice-to-have.**

### Suggestions (nice to have)

**S1: `_generate_xml` filename pattern niespójny z ksef_generate.py**

`ksef_daemon.py:185` generuje filename:
```python
f"{prefix}{doc.rodzaj}-{doc.gid}_{d.strftime('%m_%y')}_{d.isoformat()}.xml"
```
Wynik: `ksef_FS-59_04_26_2026-04-14.xml`

Istniejący ksef_generate.py tworzy: `ksef_FS-59_04_26_SPKR_2026-04-14.xml` (z serią).

Daemon nie ma serii (scan SQL nie pobiera). **Akceptowalne** — pliki daemon mają inny
naming pattern, nie kolidują z ręcznie generowanymi. Ale dla spójności warto dodać
serię do scan SQL (`n.TrN_TrNSeria`) i włączyć w filename. **Minor, non-blocking.**

**S2: `--date-from` / `--date-to` z planu nie zaimplementowane**

Plan sugerował opcjonalne filtry zakresu dat. Developer nie dodał. OK — scan SQL
pobiera wszystkie zatwierdzone, Python-side filter odrzuca known. Filtr dat to
convenience, nie wymagany w acceptance criteria.

## Architecture Assessment

### Module boundaries

```
tools/ksef_daemon.py (CLI wiring + KSeFDaemon loop ~246L)
    ↓ DI
core/ksef/usecases/scan_erp.py (scan ~119L)
    ↓
core/ksef/adapters/repo.py (get_latest — reuse)
core/ksef/adapters/erp_reader.py (fetch_faktury — reuse)
core/ksef/adapters/xml_builder.py (build_faktura — reuse)
core/ksef/usecases/send_invoice.py (execute — reuse)
```

Daemon = wiring + loop. Nie duplikuje logiki. Reużywa wszystko z Block 2-4. **Correct.**

### Pattern compliance

| Pattern | Status |
|---|---|
| DI for Testability | ✓ scan, send_factory, sleep, on_tick — all injectable |
| Error Isolation | ✓ _process_one try/except, log + continue |
| Graceful Shutdown | ✓ Signal handler + interruptible sleep |
| Idempotency | ✓ is_known check (via scan) + has_pending_or_sent (via SendInvoice UC) |
| Structured Logging | ✓ JSON format throughout |

### Anti-pattern check

| Anti-pattern | Status |
|---|---|
| God Object | ✓ Clean — daemon = loop, scan = detection, send = pipeline |
| Silent Failure | ✓ Clean — errors logged with context |
| Retry Sprawl | ✓ Avoided — no auto-retry, daemon retries on next tick |
| Mixed Dimensions | ✓ Clean — scan SQL ≠ full document SQL |

## Test Coverage Analysis

| File | Tests | Plan min | Status |
|---|---|---|---|
| test_scan_erp.py | 9 | ≥8 | ✓ |
| test_daemon.py | 8 | ≥7 | ✓ |
| **Total new** | **17** | **≥15** | ✓ |
| + Block 1-4 | 149 | 149 | ✓ |
| **Suite total** | **166** | **≥164** | ✓ |

**ScanErp tests quality:** Mock run_query + repo. Covers: FS, FSK, exclusion (shadow DB, accepted, error), empty, SQL error, date sorting, date type coercion. Solidne.

**Daemon tests quality:** Mock scan + send_factory. Covers: batch processing, results, dry-run, graceful shutdown mid-batch, error isolation, empty scan, tick count, on_tick callback. Solidne.

## Recommended Actions

### Before commit (must):

Brak — commit already done. W1 i W2 to wiring cleanup, non-blocking.

### Nice-to-have (non-blocking):
- [ ] W1: Deduplicate `_run_query` w ksef_daemon.py
- [ ] W2: Share single `repo` instance between scan and send
- [ ] S1: Dodaj TrN_TrNSeria do scan SQL dla spójnego filename pattern

## Verdict

**PASS.** Block 6 to kompletny daemon: ScanErp wykrywa zatwierdzone dokumenty z ERP (`TrN_Bufor=0`), Python-side filter vs shadow DB, KSeFDaemon z graceful shutdown, error isolation, --once/--dry-run modes. 17 nowych testów, 166/166 PASS. Daemon reużywa pełen pipeline z Block 2-4 bez duplikacji logiki. Dwa warnings (W1: duplicate `_run_query`, W2: duplicate repo) to wiring cleanup — non-blocking.

M5 (daemon) complete. Next: M6 (observability & safety) — decyzja człowieka.
