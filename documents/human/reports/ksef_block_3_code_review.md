# Code Review: KSeF Block 3 — M0 konsolidacja XML (domain + builder + reader)

Date: 2026-04-16
Reviewer: Architect
Branch: main (commit 7c134e7)
Plan: `documents/human/plans/ksef_developer_block_3.md`
Handoff: msg #77 (developer → architect), detale: `tmp/handoff_block_3_review.md`

## Summary

**Overall assessment: PASS**
**Code maturity level: L3 Senior (strong)** — frozen dataclasses z Decimal discipline, DI (clock, run_query), boundary validation (`_row_to_*` jako jedyne miejsce mapowania), shared helpers bez if/else branching FS vs FSK, snapshot testy byte-identical z produkcją, 70%+ redukcja kodu CLI. Częściowo L4 (snapshot pattern eliminuje klasę XML drift bugów, error hierarchy).

**Tests:** 126/126 PASS (36 nowych + 90 z Block 1+2). Real-DB: 10/10 FS + 1/1 FSK byte-identical.

**Acceptance criteria vs deliverable:**

| Criterium | Status |
|---|---|
| Domain frozen dataclasses, Decimal | ✓ `invoice.py` (103 L), `correction.py` (79 L) |
| ErpReader row→domain w jednym miejscu | ✓ `erp_reader.py` (293 L), `_row_to_*` boundary pattern |
| XmlBuilder domain→XML, shared helpers | ✓ `xml_builder.py` (260 L), clock DI |
| XsdValidator module function | ✓ `xsd_validator.py` (25 L) |
| CLI thin wrapper (target ~40 L) | ~95 L each (2.5x target, ale cienkie — plan estimate was off) |
| .bat files bez zmian | ✓ (developer verified na real DB) |
| Snapshots ≥3 FS + ≥1 FSK | ✓ 3 FS + 1 FSK + cross-check vs prod |
| Unit tests ≥21 | ✓ 31 (12 reader + 16 builder + 3 xsd) |
| Suite ≥115 PASS | ✓ 126 PASS |
| XSD validation ≥1 FS + ≥1 FSK | ✗ **Brak** — patrz W1 |
| Zero duplikacji helpers | ✓ `E()`, `v()`, `fmt_decimal()` → `xml_builder.py` |
| DI: core nie importuje tools | ✓ Late import w CLI |

## Odchylenia od planu — decyzje

### 1. StanPrzed/StanPo bez podsumowania → **APPROVE**

Plan proponował osobne `PodsumowanieVat` per stan. Implementacja słusznie podąża za XML FA(3) — jedno podsumowanie na root `Fa` (zawiera kwoty różnic), StanPrzed/StanPo tylko wiersze. Developer udokumentował w docstring `correction.py:7-11`.

### 2. Osobne `Pozycja` (FS) i `PozycjaKorekta` (FSK) → **APPROVE**

Plan sugerował wspólny typ. Pola się istotnie różnią:
- FS: `cena_netto_jedn` (P_9A), `wartosc_netto` (P_10)
- FSK: `cena_brutto_jedn` (P_9B), `wartosc_netto` (P_11A), `kwota_vat` (P_11Vat), `indeks`, `pkwiu`, `stan_przed`, `data_korekty`

Unifikacja wymagałaby 6+ Optional pól — traci type safety. Rozdzielenie jest czystsze architektonicznie.

### 3. Snapshot FSK: 1 (plan sugerował ≥2) → **APPROVE**

Tylko 1 FSK istnieje w produkcji. Byte-identical z realnym output/ksef/. 1 snapshot z prod data wystarczy do walidacji refaktoru.

### 4. Decimal HALF_UP zamiast float → **APPROVE**

Zamiana `f"{float(val):.2f}"` → `Decimal.quantize(HALF_UP)` poprawia precyzję. Byte-identical na 10 FS + 1 FSK — brak regresji, poprawka korektności.

## Findings

### Critical Issues (must fix)

Brak.

### Warnings (should fix)

**W1: Brak XSD regression test**
Plan wymagał: "Walidacja XSD dla ≥1 FS i ≥1 FSK: `valid=True`". `test_xsd_validator.py` testuje z minimalnym testowym XSD, nie z prawdziwym schematem FA(3). CLI ma pełną zdolność walidacji XSD (`--validate`), ale brak automatycznego testu regresji.

**Ryzyko:** Przyszłe zmiany w builderze mogą złamać compliance XSD bez detekcji.

**Fix:** Dodaj `test_fs_59_validates_against_fa3_xsd()` + analog dla FSK. XSD w `documents/Wzory plików/` lub wskazane przez usera. Jeśli XSD niedostępne — oznacz jako `@pytest.mark.skip("XSD not available")` z backlog entry.

**Nie bloker M0** — snapshot byte-identical potwierdza zgodność z obecnym (działającym) kodem. Ale wymagane przed M4 (SendInvoice) gdzie XML trafia na serwer KSeF.

**W2: `_build_fa_header` brak type annotations**
`xml_builder.py:119-121` — parametry `data_wyst` i `data_spr` nie mają typów. Reszta buildera jest typed. Minor inconsistency.

```python
# current
def _build_fa_header(self, fa, kod_waluty: str, data_wyst, numer: str, data_spr) -> None:

# fix
def _build_fa_header(self, fa: etree._Element, kod_waluty: str,
                     data_wyst: date, numer: str, data_spr: date | None) -> None:
```

### Suggestions (nice to have)

**S1: CLI 95 L vs target 40 L**
Oba CLIs ~2.5x cel. Excess to argparse + validate_and_report. Akceptowalne — thin wrapper z jasną strukturą. Jeśli pojawi się trzeci CLI (np. `ksef_generate_zal.py`), rozważ ekstrakcję wspólnego modułu.

**S2: `_iso()` duck typing**
`xml_builder.py:254-255` — `_iso(d)` sprawdza `hasattr(d, "isoformat")`. Wszystkie callery przekazują `date`. Można zastąpić `_iso(d: date) -> str: return d.isoformat()` dla explicit typing. Minor.

**S3: Brak logging w core/ksef/**
Plan wymagał "Zero `print()` — `logging`". Kod nie ma print() (dobrze), ale też nie ma logging. Dodanie loggerów byłoby L4 improvement — nie M0 scope.

**S4: Duplikacja _validate_and_report między CLIs**
`ksef_generate.py:97-109` i `ksef_generate_kor.py:94-106` — identyczne. DRY violation ale ekstrakcja wspólnego modułu dla ~15 linii to over-engineering. OK na razie; rozważ przy trzecim CLI.

## Architecture Assessment

### Module boundaries

```
tools/ksef_generate*.py (thin CLI)
    ↓ late import
    sql_query.run_query (ERP connector)
    ↓ DI
core/ksef/adapters/erp_reader.py (SQL → domain)
    ↓
core/ksef/domain/{invoice,correction}.py (frozen dataclasses)
    ↓
core/ksef/adapters/xml_builder.py (domain → XML bytes)
    ↓
core/ksef/adapters/xsd_validator.py (XML → bool)
```

Czyste warstwy. Domain ma zero import z adapters/tools. Adapters importują domain. Tools importują adapters. **Dependency direction correct.**

### Pattern compliance

| Pattern | Status |
|---|---|
| Validation at Boundary → Trust Internally | ✓ `_row_to_*` boundary, domain trusted |
| Repository (Persistence Separation) | ✓ Domain ≠ SQL (zero SQL w domain/) |
| Backward Compatibility Absolute | ✓ CLI args + .bat files unchanged |
| Incremental Migration | ✓ Block 3 = pure refactor, zero features |

### Anti-pattern check

| Anti-pattern | Status |
|---|---|
| Defensive Programming Hell | ✓ Clean — validate once at boundary |
| Mixed Dimensions | ✓ Clean — StanPrzed/StanPo/Pozycja each have clear scope |
| Big Bang Refactor | ✓ Avoided — byte-identical snapshots guarantee zero regression |
| Simpler solution exists? | No — domain+builder+reader is the standard pattern for this scope |

## Test Coverage Analysis

| File | Tests | Plan min | Status |
|---|---|---|---|
| test_xml_builder_snapshots.py | 5 | ≥4 | ✓ |
| test_xml_builder.py | 16 | ≥10 | ✓ |
| test_erp_reader.py | 12 | ≥8 | ✓ |
| test_xsd_validator.py | 3 | ≥3 | ✓ |
| **Total new** | **36** | **≥25** | ✓ |
| + Block 1+2 | 90 | 90 | ✓ |
| **Suite total** | **126** | **≥115** | ✓ |

**Fixtures quality:** `domain_samples.py` (226 L) — real production data, 4 factories, reusable helpers. Dobrze osadzony w cyklu snapshot regression.

## Recommended Actions

### Before commit (must):
- [ ] W2: Dodaj type annotations do `_build_fa_header` parametrów

### Backlog (non-blocking):
- [ ] W1: XSD regression test — wymagane przed M4 (SendInvoice)
- [ ] S3: Logging w core/ksef/ — L4 improvement
- [ ] Contribute pattern do PATTERNS.md: "Snapshot Regression Testing (byte-identical XML)"

## Verdict

**PASS.** Block 3 to wzorcowy refaktor: 766 linii → czysty domain model + adapters, 70%+ redukcja CLI, zero regresji (byte-identical snapshots), 36 nowych testów. Odchylenia od planu (1-4) wszystkie zatwierdzone — developer podejmował lepsze decyzje niż plan zakładał. Jeden Warning (W1: XSD test) nie blokuje M0, ale musi być rozwiązany przed M4 (SendInvoice).

Developer może commitować feat(ksef): block 3 po jednej poprawce (W2 type annotations).
