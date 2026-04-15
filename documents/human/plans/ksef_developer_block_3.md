# Developer Block 3 — KSeF M0 konsolidacja XML (domain + builder + reader)

Data: 2026-04-15
Autor: Architect
Dotyczy planu: `documents/human/plans/ksef_api_automation.md` (§5 M0)
Dla roli: Developer
Status: Ready to start
Prerequisites: Block 1 ✓ (commit 1566f94), Block 2 ✓ (po commit 90/90 tests)

---

## Cel bloku

Konsolidacja dwóch istniejących skryptów (`tools/ksef_generate.py` + `ksef_generate_kor.py`,
łącznie ~766 linii) w **jedną warstwę domenową + builder XML + reader ERP**. Eliminacja
duplikacji helpers (`E()`, `v()`, `fmt_decimal()`, `validate_xsd()`, `build_sql()`).

**Zero zmian funkcjonalnych** — refaktor gwarantowany przez snapshot testy (XML byte-identyczny
przed i po).

Po ukończeniu Block 3:
- CLI `tools/ksef_generate*.py` to cienkie wrappery (~30-50 linii każdy) nad `core/ksef/`
- Block 4 (M4 SendInvoice) dostaje typed `Faktura`/`Korekta` z `ErpReader` zamiast dict-hell
- Dodanie nowego pola XML = zmiana w jednym miejscu (domain + builder), nie dwóch

**Zero kontaktu z KSeF API, zero DB (Block 2 dla wysyłki — osobno), zero auth.**

---

## Decyzje zatwierdzone (2026-04-15)

| Decyzja | Wybór |
|---|---|
| Strategia walidacji refaktoru | **Snapshot test** — XML byte-identyczny z pre-refactor dla ≥3 FS + ≥2 FSK (plus 1 XSD validation per typ) |
| Źródło snapshotów | Istniejące `output/ksef/*.xml` (12 FS + 1 FSK) |
| Wejście refaktoru | SQL views bez zmian (`solutions/ksef/ksef_fs_draft.sql`, `ksef_fsk_draft.sql`) — są stabilne |
| Parametry CLI | Bez zmian (`.bat` działają) — `--gid`, `--date-from`, `--date-to`, `--validate`, `--dry-run`, `--output-dir` |
| Integracja z Block 2 DB | **Nie w tym bloku** — `repo.create(DRAFT)` będzie w Block 4 (SendInvoice use case) |
| Test framework | `pytest` + snapshot files w `tests/ksef/snapshots/` |

---

## Scope — co dokładnie powstaje

### Moduł: rozbudowa `core/ksef/`

```
core/ksef/
  domain/
    __init__.py
    shipment.py              # (istnieje z Block 2, nie dotykać)
    events.py                # (istnieje z Block 2, nie dotykać)
    invoice.py               # NOWY — Faktura, Pozycja, Podmiot, Adnotacje, Platnosc, Naglowek
    correction.py            # NOWY — Korekta (rozszerza/komponuje Faktura + DaneFaKorygowanej, StanPrzed/StanPo)
  adapters/
    http.py                  # (istnieje z Block 1)
    ksef_api.py              # (istnieje z Block 1)
    ksef_auth.py             # (istnieje z Block 1)
    repo.py                  # (istnieje z Block 2)
    erp_reader.py            # NOWY — SQL → Faktura | Korekta
    xml_builder.py           # NOWY — domain → XML bytes
    xsd_validator.py         # NOWY — XML + XSD → (bool, errors)
```

### Domain model — `core/ksef/domain/invoice.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum

class RodzajFaktury(str, Enum):
    VAT = "VAT"              # faktura zwykła
    KOR = "KOR"              # korekta (handled w correction.py)
    ZAL = "ZAL"              # zaliczkowa
    ROZ = "ROZ"              # rozliczeniowa

@dataclass(frozen=True)
class Podmiot:
    nip: str | None          # może być None dla klienta zagranicznego
    pelna_nazwa: str
    kod_kraju: str           # ISO2, domyślnie "PL"
    adres_l1: str
    adres_l2: str | None

@dataclass(frozen=True)
class Pozycja:
    nr_pozycji: int
    nazwa_towaru: str
    gtin: str | None
    jednostka_miary: str
    ilosc: Decimal           # 4 miejsca po przecinku, trailing zeros strip
    cena_netto_jedn: Decimal
    wartosc_netto: Decimal
    stawka_vat: str          # "23", "8", "5", "0", "zw", "np" (enum w future)

@dataclass(frozen=True)
class PodsumowanieVat:
    """Sumy per stawka — tylko te które występują."""
    vat_23_podstawa: Decimal | None
    vat_23_kwota: Decimal | None
    vat_8_podstawa: Decimal | None
    vat_8_kwota: Decimal | None
    vat_5_podstawa: Decimal | None
    vat_5_kwota: Decimal | None
    vat_0_podstawa: Decimal | None
    vat_0_kwota: Decimal | None
    zw_podstawa: Decimal | None
    np_podstawa: Decimal | None
    kwota_naleznosci: Decimal

@dataclass(frozen=True)
class Adnotacje:
    mpp: str                 # P_16
    # pozostałe pola na sztywno "2" (nie dotyczy) w obecnym kodzie — zachowujemy
    p_17: str = "2"
    p_18: str = "2"
    p_18a: str = "2"
    zwolnienie_p19n: str = "1"
    nst_p22n: str = "1"
    p_23: str = "2"
    p_marzy_n: str = "1"

@dataclass(frozen=True)
class Platnosc:
    termin_platnosci: date | None
    kod_formy_platnosci: str | None
    nr_rachunku_bankowego: str | None

@dataclass(frozen=True)
class Naglowek:
    kod_formularza: str = "FA"
    kod_systemowy: str = "FA (3)"
    wersja_schemy: str = "1-0E"
    wariant_formularza: str = "3"
    system_info: str = "Comarch ERP XL"
    # data_wytworzenia_fa wyliczana przy serializacji (datetime.now())

@dataclass(frozen=True)
class Faktura:
    gid_numer: int                    # ERP XL identyfikator
    naglowek: Naglowek
    podmiot1: Podmiot                 # sprzedawca
    podmiot2: Podmiot                 # nabywca
    kod_waluty: str
    data_wystawienia: date
    data_sprzedazy: date | None       # None gdy == data_wystawienia (pomija P_6)
    numer_faktury: str
    podsumowanie: PodsumowanieVat
    adnotacje: Adnotacje
    rodzaj: str                       # "VAT", "ZAL", "ROZ"...
    wiersze: tuple[Pozycja, ...]
    platnosc: Platnosc
```

### Domain model — `core/ksef/domain/correction.py`

```python
@dataclass(frozen=True)
class DaneFaKorygowanej:
    data_wystawienia_org: date
    numer_faktury_org: str

@dataclass(frozen=True)
class StanPrzed:
    """Sekcja StanPrzed korekty — wartości oryginalne."""
    podsumowanie: PodsumowanieVat
    wiersze: tuple[Pozycja, ...]

@dataclass(frozen=True)
class StanPo:
    """Sekcja StanPo korekty — wartości po korekcie."""
    podsumowanie: PodsumowanieVat
    wiersze: tuple[Pozycja, ...]

@dataclass(frozen=True)
class Korekta:
    gid_numer: int
    naglowek: Naglowek
    podmiot1: Podmiot
    podmiot2: Podmiot
    kod_waluty: str
    data_wystawienia: date
    numer_faktury: str                # nr korekty, nie oryginału
    dane_fa_korygowanej: DaneFaKorygowanej
    stan_przed: StanPrzed
    stan_po: StanPo
    adnotacje: Adnotacje
    przyczyna_korekty: str            # wymagane w FA(3)
    opis_korekty: str | None
    platnosc: Platnosc
```

### Adapter — `core/ksef/adapters/erp_reader.py`

```python
class ErpReader:
    """SQL → domain. Jedyne miejsce mapowania column_name → pole dataclass."""

    def __init__(self, run_query: Callable[[str], dict]) -> None:
        """run_query pobierany z istniejącego tools/sql_query.py (dependency injection)."""
        self._run_query = run_query

    def fetch_faktury(
        self,
        *,
        gids: list[int] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Faktura]:
        """Zwraca listę Faktura z SQL view. Grupuje rows po _GIDNumer."""

    def fetch_korekty(
        self,
        *,
        gids: list[int] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Korekta]: ...

    # internals
    def _row_to_podmiot1(self, row: dict) -> Podmiot: ...
    def _row_to_podmiot2(self, row: dict) -> Podmiot: ...
    def _row_to_pozycja(self, row: dict) -> Pozycja: ...
    def _rows_to_podsumowanie(self, row: dict) -> PodsumowanieVat: ...
    def _rows_to_faktura(self, rows: list[dict]) -> Faktura: ...
    def _rows_to_korekta_stan_przed(self, rows: list[dict]) -> StanPrzed: ...
    def _rows_to_korekta_stan_po(self, rows: list[dict]) -> StanPo: ...
```

**Kontrakt:**
- Row mapping w jednym miejscu (`_row_to_*`) — boundary validation
- `Decimal` z SQL dict → `Decimal` w dataclass (nie `float`!)
- `None` w SQL → `None` w domain (zachowujemy semantykę)
- Pusty wynik SQL → `[]` (nie wyjątek)

### Adapter — `core/ksef/adapters/xml_builder.py`

```python
class XmlBuilder:
    """Domain → XML bytes. Jedyne miejsce konstrukcji drzewa lxml."""

    NS = "http://crd.gov.pl/wzor/2025/06/25/13775/"

    def build_faktura(self, faktura: Faktura) -> bytes:
        """Zwraca UTF-8 bytes z XML declaration + pretty-print."""

    def build_korekta(self, korekta: Korekta) -> bytes: ...

    # helpers — prywatne, reusable
    def _root(self) -> etree.Element: ...
    def _build_naglowek(self, parent, nag: Naglowek) -> None: ...
    def _build_podmiot(self, parent, p: Podmiot, *, tag: str, is_podmiot2: bool = False) -> None: ...
    def _build_fa_header(self, parent, faktura_or_korekta) -> None:
        """KodWaluty + P_1 + P_2 + P_6 (jeśli data_sprzedazy)."""
    def _build_podsumowanie(self, parent, p: PodsumowanieVat) -> None: ...
    def _build_adnotacje(self, parent, a: Adnotacje) -> None: ...
    def _build_wiersz(self, parent, pozycja: Pozycja) -> None: ...
    def _build_platnosc(self, parent, p: Platnosc) -> None: ...
    def _format_decimal(self, v: Decimal | None, places: int = 2) -> str | None: ...
    def _format_ilosc(self, v: Decimal) -> str: ...   # 4 places, strip trailing zeros
```

**Kontrakt:**
- `build_faktura` i `build_korekta` dzielą helpery (`_build_podmiot`, `_build_adnotacje`, etc.)
- Różnice FS vs FSK wyrażone przez struktury domain (Korekta ma `StanPrzed/StanPo`), nie przez `if/else` w builderze
- Output byte-identyczny z obecnym kodem (snapshot test)
- `DataWytworzeniaFa` = `datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"` — **wstrzykiwalny clock** dla deterministycznych testów (`XmlBuilder(clock=lambda: datetime(2026,4,15,...))`)

### Adapter — `core/ksef/adapters/xsd_validator.py`

```python
def validate(xml_bytes: bytes, xsd_path: Path) -> tuple[bool, list[str]]:
    """Waliduje XML przeciw XSD.
    Return: (is_valid, error_messages). Error messages format: f'Linia {line}: {msg}'.
    """
```

Funkcja modułowa (nie klasa — bezstanowa). Wyrzuca `FileNotFoundError` gdy XSD nie istnieje.

### CLI — `tools/ksef_generate.py` (refaktor)

Target ~40 linii. Struktura:

```python
def main() -> int:
    args = _parse_args()
    if args.dry_run:
        print(_build_sql_preview(args))
        return 0

    reader = ErpReader(run_query=_get_run_query())
    faktury = reader.fetch_faktury(gids=args.gid, date_from=args.date_from, date_to=args.date_to)
    if not faktury:
        print("Brak faktur dla podanych kryteriów.")
        return 0

    builder = XmlBuilder()
    out_dir = _resolve_output_dir(args.output_dir)
    errors = []
    for f in faktury:
        xml_bytes = builder.build_faktura(f)
        out_path = _compose_filename(out_dir, f)
        out_path.write_bytes(xml_bytes)
        print(f"  [OK] {f.numer_faktury} ({len(f.wiersze)} poz.) -> {out_path.name}")
        if args.validate:
            valid, errs = xsd_validator.validate(xml_bytes, Path(args.validate))
            # ... log
            if not valid:
                errors.append((f.numer_faktury, errs))
    print(f"\nWygenerowano {len(faktury)} faktur(y) w {out_dir}")
    return 2 if errors else 0
```

### CLI — `tools/ksef_generate_kor.py` (refaktor)

Analogicznie do `ksef_generate.py`, używa `fetch_korekty` + `build_korekta`.

### Testy

#### Snapshot regression — `tests/ksef/test_xml_builder_snapshots.py`

**Cel:** gwarancja że XML po refaktorze jest byte-identyczny z pre-refactor dla realnych danych produkcyjnych.

```
tests/ksef/
  snapshots/
    ksef_FS-59_04_26_SPKR_2026-04-14.xml    # kopia z output/ksef/
    ksef_FS-60_04_26_SPKR_2026-04-14.xml
    ksef_FS-73_04_26_FRA_2026-04-14.xml     # ≥3 FS
    ksef_kor_FSK-1_04_26_SPKRK_2026-04-14.xml  # ≥1 FSK (mamy tylko 1 — plan wymagał 2, zgłoś do Architekta jeśli blokujące)
```

Fixture: tworzy `Faktura`/`Korekta` z hardcoded dict (z realnego row SQL, zapisanego jako fixture), przekazuje przez builder, porównuje bytes.

```python
def test_fs_59_matches_snapshot():
    rows = _load_fixture("fs_59_rows.json")         # dump z SQL
    faktura = ErpReader(_mock_query(rows)).fetch_faktury(gids=[59])[0]
    builder = XmlBuilder(clock=lambda: datetime(2026, 4, 14, 12, 0, 0))
    actual = builder.build_faktura(faktura)
    expected = (SNAPSHOTS / "ksef_FS-59_04_26_SPKR_2026-04-14.xml").read_bytes()
    assert actual == expected
```

**Uwaga o `DataWytworzeniaFa`** — obecne snapshoty mają jakąś konkretną wartość timestamp. Przy refaktorze:
- Albo regenerujemy snapshoty z mock clock (preferowane — deterministyczne)
- Albo strippujemy `DataWytworzeniaFa` z XML przed porównaniem (łatwiej ale mniej restrykcyjne)
- **Zdecydować przy pisaniu — zarekomenduj w handoff**

Minimum: 3 FS + 1 FSK (jest tylko 1 dostępny). Developer może wygenerować więcej FSK ręcznie na Demo jeśli to uzna za potrzebne.

#### Unit tests — `tests/ksef/test_erp_reader.py`

- `_row_to_pozycja` — happy path z Decimal
- `_row_to_podmiot1/2` — z `None` adres_l2
- `_rows_to_podsumowanie` — tylko obecne stawki (pozostałe None)
- `fetch_faktury` z pustym SQL → `[]`
- `fetch_faktury` grupuje wiele rows na jednej fakturze (pozycje)
- `fetch_korekty` oddziela `StanPrzed` i `StanPo` rows

#### Unit tests — `tests/ksef/test_xml_builder.py`

- `_format_decimal(None)` → `None`
- `_format_ilosc(Decimal("1.5000"))` → `"1.5"` (strip trailing zeros)
- `_format_ilosc(Decimal("2.0000"))` → `"2"` (strip trailing zeros and dot)
- `_build_podmiot` z NIP None → element `<DaneIdentyfikacyjne>` bez `<NIP>`
- `build_faktura` z `data_sprzedazy == data_wystawienia` → brak `<P_6>`
- `build_korekta` z `StanPrzed.wiersze` pusty → zachowanie do zdefiniowania (raise lub empty section? sprawdź w current code)

#### Unit tests — `tests/ksef/test_xsd_validator.py`

- Valid XML + valid XSD → `(True, [])`
- Invalid XML + valid XSD → `(False, ['Linia N: ...'])`
- Missing XSD path → `FileNotFoundError`

#### Minimum testów

- Snapshot: ≥4 (3 FS + 1 FSK)
- ErpReader: ≥8 unit
- XmlBuilder: ≥10 unit
- XsdValidator: ≥3 unit
- **Total:** ≥25 nowych testów + zachowane 90 z Block 1+2 = ≥115 PASS

---

## Acceptance criteria

- [ ] `core/ksef/domain/invoice.py` + `correction.py` — dataclasses frozen, Decimal dla kwot
- [ ] `core/ksef/adapters/erp_reader.py` — row→domain w jednym miejscu
- [ ] `core/ksef/adapters/xml_builder.py` — domain→XML, helpery dzielone FS/FSK
- [ ] `core/ksef/adapters/xsd_validator.py` — funkcja modułowa
- [ ] `tools/ksef_generate.py` — ~40 linii, cienka powłoka CLI
- [ ] `tools/ksef_generate_kor.py` — ~40 linii, cienka powłoka CLI
- [ ] `.bat` files (`ksef_generuj.bat`, `ksef_generuj_fs.bat`, `ksef_generuj_kor.bat`) działają bez zmian
- [ ] Snapshot tests: ≥3 FS + ≥1 FSK byte-identical (z mock clock dla `DataWytworzeniaFa`)
- [ ] Unit tests: ≥21 nowych (ErpReader 8 + XmlBuilder 10 + XsdValidator 3)
- [ ] Cały suite PASS: ≥115 tests (90 Block 1+2 + ≥25 Block 3)
- [ ] Walidacja XSD dla ≥1 FS i ≥1 FSK: `valid=True` (regresja vs current behavior)
- [ ] Zero duplikacji helpers — `E()`, `v()`, `fmt_decimal()` istnieją tylko w `xml_builder.py`
- [ ] `tools/sql_query.py` import przez dependency injection (ErpReader dostaje callable), nie bezpośredni import w core/

### Jakość kodu (L3 Senior — kontynuacja z Block 1+2)

- Funkcje ≤15 linii (helpery buildera mogą być dłuższe — realny trade-off z czytelnością)
- Frozen dataclasses w domain — zero mutacji
- `Decimal` nie `float` dla kwot (zaokrąglenia → konsekwentne)
- `from __future__ import annotations` + PEP 604
- Typed throughout; mypy clean dla `core/ksef/domain/` i `core/ksef/adapters/{erp_reader,xml_builder,xsd_validator}.py`
- Zero `print()` w `core/ksef/` — `logging`
- Row mapping w `_row_to_*` (boundary validation pattern z Block 1)

---

## Out of scope w Block 3 (świadomie)

- **Zapis do shadow DB** — to Block 4 (M4 SendInvoice use case). Block 3 tylko czyta ERP i generuje XML.
- **Szyfrowanie XML (AES-256-CBC)** — Block 4 (wymóg KSeF 2.0 online session).
- **KSeF API calls** — Block 1 już je ma, tu nie używamy.
- **Refaktor SQL views** (`ksef_fs_draft.sql`, `ksef_fsk_draft.sql`) — stabilne, nie dotykamy.
- **Nowe pola XML** — refaktor 1:1, zero nowych features.
- **Bulk optimization** — nadal ładujemy wszystko do pamięci; 20-30 dok/dzień to trywialne.
- **Historia wersji XSD / migracja schemy KSeF** — M6.

---

## Punkty uwagi dla Developera

1. **Decimal dyscyplina** — SQL Server zwraca `decimal.Decimal` przy NUMERIC. Nie konwertuj na `float` w locie — zaokrąglenia będą inne niż w obecnym kodzie (`f"{float(val):.2f}"`). Używaj `Decimal.quantize(Decimal('0.01'))` dla dokładnie 2 miejsc. Pokryj testem: `Decimal('1.005')` → ? (current: `1.01` przez float quirk; po refaktorze chcemy zachowanie identyczne — sprawdź konkretny case).

2. **`DataWytworzeniaFa` w snapshotach** — obecny kod używa `datetime.now()`. Snapshot musi mieć zamrożony timestamp. **Preferowane:** regeneruj snapshoty z mock clock (np. `datetime(2026, 4, 14, 12, 0, 0)`), dokumentuj ten czas w README snapshotów. Strippowanie przed porównaniem jest OK jako fallback, ale słabsze.

3. **SQL views i `sql_query`** — nie przerabiaj SQL. Dependency injection:
   ```python
   from tools.sql_query import run_query   # wolno importować w tools/
   reader = ErpReader(run_query=run_query) # ErpReader nie importuje sql_query
   ```
   `core/ksef/adapters/erp_reader.py` **nie importuje** `tools/sql_query.py` — DI. Umożliwi to mock w testach bez bazy.

4. **Ilość pozycji — format "1.5" nie "1.5000"** — `_format_ilosc` musi robić `rstrip("0").rstrip(".")` jak w obecnym kodzie (linia ksef_generate.py:196-197). Test dla `Decimal('2')` → `"2"`, `Decimal('1.5')` → `"1.5"`, `Decimal('1.0050')` → `"1.005"`.

5. **FSK model StanPrzed/StanPo** — obecny `ksef_generate_kor.py` ma konkretny kształt XML z sekcjami. Przenieś 1:1 do `build_korekta`. Nie próbuj "ulepszać" struktury. Jeśli coś wygląda dziwnie — dokumentuj w kodzie, nie zmieniaj.

6. **Grupowanie po `_GIDNumer`** — obecny kod robi `groupby(all_rows, key=itemgetter("_GIDNumer"))`. To dzieje się w ErpReader (`_rows_to_faktura` / `_rows_to_korekta`). Każda `Faktura` to jedna grupa rows. Sort przed groupby obowiązkowy.

7. **Snapshot fixtures** — zapisz dumpy SQL jako JSON w `tests/ksef/fixtures/fs_N_rows.json`. Format: lista dictów, Decimal jako string (przy deserializacji → Decimal). Alternatywa: plik Python z literałem dict — mniej elegancko ale bez de/ser.

8. **Regresja XSD** — obecny kod czasem waliduje się poprawnie. Snapshot test nie wystarczy — dodaj **1 test XSD per typ** (`test_fs_59_validates_against_xsd` + analog dla FSK). XSD w `documents/Wzory plików/` lub wskaż ścieżkę użytkownikowi.

9. **`core/__init__.py`** — już istnieje z Block 1. Domain/__init__.py może eksportować `Faktura, Korekta, ...` dla wygody importu w testach.

10. **Kolejność pracy (rekomendacja):**
    1. Fixtures z SQL dumps (bez kodu — ręcznie wyciągnij z prod DB albo z existing snapshots)
    2. Domain dataclasses (bez zależności)
    3. XmlBuilder + snapshot tests (czerwone → zielone)
    4. ErpReader (fixtures karmione w testach)
    5. XsdValidator
    6. Refaktor CLI — ostatnie, gdy warstwy gotowe
    7. Verify `.bat` files na realnej DB

---

## Workflow i handoff z powrotem

Developer realizuje przez `workflow_developer_tool` (refaktor modułów).

Po ukończeniu — handoff do Architekta na `workflow_code_review`:

```
py tools/agent_bus_cli.py handoff \
  --from developer --to architect \
  --phase "ksef_block_3_review" --status PASS \
  --summary "Block 3 zaimplementowany: domain (Faktura/Korekta+deps), ErpReader, XmlBuilder, XsdValidator, refaktor CLI. Snapshots PASS dla N FS + M FSK. 115+ tests PASS." \
  --next-action "Code review — core/ksef/domain/, adapters/{erp_reader,xml_builder,xsd_validator}.py, tools/ksef_generate*.py, tests/ksef/test_{xml_builder_snapshots,erp_reader,xml_builder,xsd_validator}.py"
```

Po PASS → Block 4 (M4 SendInvoice + encryption) lub M3 enrollment — decyzja człowieka.

---

## Ryzyka Block 3

| Ryzyko | Mitygacja |
|---|---|
| Subtelna zmiana formatowania Decimal łamie snapshot | Decimal konsekwentnie przez całą ścieżkę; test dla problematic cases (1.005, 1.0050, etc.) |
| `datetime.now()` w builderze → niestabilne snapshoty | Clock injection w XmlBuilder; snapshoty z deterministycznym timestampem |
| XSD FAIL po refaktorze (subtelny drift) | Osobny test XSD regresji (nie tylko snapshot byte-compare) |
| Regresja na mniej testowanych path-ach (np. zagraniczny klient bez NIP) | Fixture dla takiego case jeśli istnieje w produkcji; jeśli brak — dokumentuj jako untested |
| Mock `run_query` w ErpReader nie pokrywa realnej struktury row | Integration test na prawdziwej DB (opcjonalny, `@pytest.mark.integration`) |
| `tools/sql_query.py` się zmieni, DI zepsute | Test `test_sql_query_callable_contract` — sprawdza że run_query zwraca `{'ok': bool, 'data': {'columns': [...], 'rows': [...]}}` |
| FSK snapshot tylko 1 egzemplarz — plan wymagał ≥2 | Developer zgłasza w handoff, Architect decyduje czy blocker. Minimum 1 FSK jest akceptowalne jeśli wygenerowanie 2. jest drogie (wymaga ERP access). |
