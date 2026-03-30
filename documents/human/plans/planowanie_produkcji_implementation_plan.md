# Plan implementacji: planowanie_produkcji (pełne)

Date: 2026-03-30
Autor: Architect
ADR: documents/architecture/ADR-002-planowanie-produkcji.md

---

## Cel

Przebudowa modułu na pełne planowanie produkcji:
zamówienia CZNI (ERP) + BOM (Excel) + stany surowców (ERP) → gap analysis → Excel 4 arkusze

---

## Faza 1 — Cleanup (Developer, ~1h, natychmiast)

**1.1 Przenieść testy:**
```
mv tmp/test_planowanie_produkcji.py tests/test_planowanie_produkcji.py
```
Uruchomić: `pytest tests/test_planowanie_produkcji.py` → 5/5 PASS

**1.2 Uprościć filter_rows() — usunąć duplikaty:**

SQL już ma `CZNI%` i `Zamówienie%` w WHERE. Python nie musi ich powtarzać.
Nowa `filter_rows()`:
```python
def filter_rows(rows: list[dict], year: int) -> list[dict]:
    return [r for r in rows
            if r.get("Data_Realizacji") is not None
            and _year_of(r["Data_Realizacji"]) == year]
```

Zaktualizować testy: test_podstawowe_filtry sprawdza CZNI/Opis — te asercje stają się
nieaktualne (SQL to robi). Przepisać jako smoke test: "czy data_realizacji filtruje rok".

**Commit 1:** `refactor: planowanie_produkcji — testy do suite, uproszczenie filter_rows`

---

## Faza 2 — Modularyzacja (Developer, ~3h)

Wydzielić warstwy bez zmiany zewnętrznego działania CLI (--year nadal działa, output identyczny).

**tools/lib/pp_demand.py:**
```python
_SQL_PATH = PROJECT_ROOT / "solutions/erp_specialist/planowanie_produkcji_zamowienia_niepotwierdzone.sql"

def fetch_demand(year: int) -> list[dict]:
    """Pobiera zamówienia CZNI dla roku z ERP. Zwraca listę dict."""
    # przeniesiony kod z planowanie_produkcji.py (_fetch_all + filter_rows)
```

**tools/lib/pp_supply.py:**
```python
_SQL_PATH = PROJECT_ROOT / "solutions/erp_specialist/planowanie_produkcji_stany_mag_otorowo_surowce.sql"

def fetch_supply() -> dict[str, float]:
    """Zwraca stany surowców OTOR_SUR jako {surowiec_kod: stan}."""
    # nowy — używa istniejącego SQL
```

**planowanie_produkcji.py po Fazie 2:**
```python
def main():
    demand = fetch_demand(args.year)   # z pp_demand
    supply = fetch_supply()            # z pp_supply
    # Faza 3+: bom, gap, 4-arkuszowy export
    # Faza 2: nadal zapisuje tylko Arkusz 1 (jak dotąd)
    _export(demand, output_path)
```

**Testy Fazy 2:**
```
tests/test_pp_demand.py  — mockuje SqlClient, testuje filter_rows(rok)
tests/test_pp_supply.py  — mockuje SqlClient, testuje parsowanie stanów
```

**Commit 2:** `refactor: planowanie_produkcji — modularyzacja pp_demand + pp_supply`

---

## Faza 3 — BOM Reader (Developer, ~3h)

**tools/lib/pp_bom.py:**

Plik BOM: **ścieżka przekazywana z UI** — Developer decyduje o mechanizmie
(file picker w interfejsie, argument w oknie dialogowym, itp.)
Arkusz: `Wycena Zniczy`
Kolumny: B=czni_kod, F=grupa, H=surowiec_kod, I=surowiec_nazwa, J=mianownik

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BomEntry:
    czni_kod: str
    surowiec_kod: str
    surowiec_nazwa: str
    mianownik: float  # divisor: zapotrzebowanie = ilosc_czni / mianownik

def load_bom(xlsm_path: Path) -> dict[str, list[BomEntry]]:
    """Wczytuje BOM z arkusza 'Wycena Zniczy'. Klucz: czni_kod.
    Rzuca FileNotFoundError jeśli plik nie istnieje.
    Rzuca ValueError jeśli brak arkusza 'Wycena Zniczy'.
    """
```

**Reguły parsowania:**
- Nagłówki w wierszu 3, dane od wiersza 4
- Pomiń wiersz jeśli kolumna F (Grupa) zaczyna się od "Koszt" — to koszty, nie fizyczne surowce
- Pomiń wiersz jeśli kolumna H (surowiec_kod) jest None lub pusty
- Pomiń wiersz jeśli kolumna J (mianownik) to '#VALUE!', None lub nie jest liczbą → log warning
- Mianownik: float(str(J))
- Encoding: openpyxl read_only=True, keep_vba=False, data_only=True

**Ostrzeżenie UserWarning o Data Validation:** ignoruj (warnings.filterwarnings).

**Testy Fazy 3:**
```
tests/test_pp_bom.py  — test z mini-fixture (kilka wierszy) bez prawdziwego pliku,
                         + integration test z prawdziwym plikiem (skipif brak pliku)
```
Test kluczowych przypadków:
- mianownik '#VALUE!' → pominięty, warning
- Grupa 'Koszt' → pominięty
- mianownik 0.98 → float 0.98
- produkt z 12 surowcami → 12 BomEntry

**Commit 3:** `feat: planowanie_produkcji — pp_bom (odczyt BOM z Wycena PQ.xlsm)`

---

## Faza 4 — Gap Analysis i Excel 4-arkuszowy (Developer, ~4h)

**tools/lib/pp_gap.py:**
```python
@dataclass
class GapRow:
    surowiec_kod: str
    surowiec_nazwa: str
    potrzeba: float   # SUM(ilosc_czni / mianownik) for all orders
    dostepne: float   # z OTOR_SUR, 0.0 jeśli brak
    brak: float       # max(0, potrzeba - dostepne)

def compute_gap(
    demand: list[dict],
    bom: dict[str, list[BomEntry]],
    supply: dict[str, float],
) -> tuple[list[GapRow], list[str]]:  # (gaps, warnings)
```

Uwaga: produkty CZNI z zamówień bez BOM w słowniku → **warning + kontynuuj**.
Komunikat stderr: "[WARN] Brak BOM dla CZNI99999 — pominięto w gap analysis."
Produkt pojawia się w Arkuszu 1 (Zamówienia), ale jest pomijany w Arkuszach 2 i 4.
Uzasadnienie: stop blokuje workflow zanim użytkownik może uzupełnić BOM.

**tools/lib/pp_export.py — 4 arkusze:**

Arkusz 1: "Zamówienia CZNI"
  - Kolumny: Nr_Zamowienia, Data_Realizacji, Kontrahent_Kod, Kontrahent_Nazwa,
             Towar_Kod, Towar_Nazwa, Ilosc, Jednostka, Opis
  - Sortowanie: Data_Realizacji ASC (None na końcu)

Arkusz 2: "Zapotrzebowanie surowców"
  - Kolumny: Surowiec_Kod, Surowiec_Nazwa, Ilosc_Potrzebna
  - Agregacja: SUM(ilosc_czni / mianownik) GROUP BY surowiec_kod
  - Sortowanie: Surowiec_Kod ASC

Arkusz 3: "Stany OTOR_SUR"
  - Kolumny: Towar_Kod, Towar_Nazwa, Jednostka, Stan
  - Sortowanie: Towar_Kod ASC

Arkusz 4: "Gap Analysis"
  - Kolumny: Surowiec_Kod, Surowiec_Nazwa, Potrzeba, Dostepne, Brak
  - Highlight: cały wiersz czerwony gdzie Brak > 0 (PatternFill)
  - Sortowanie: Brak DESC (największe braki na górze)

**Testy Fazy 4:**
```
tests/test_pp_gap.py    — compute_gap z mockowanymi danymi, edge cases
tests/test_pp_export.py — czy tworzy xlsx z 4 arkuszami (openpyxl weryfikacja)
```

**Commit 4:** `feat: planowanie_produkcji — gap analysis + Excel 4 arkusze`

---

## Faza 5 — CLI update (Developer, ~1h)

**Nowy interface:**
```bash
# Pełne planowanie (domyślne)
py tools/planowanie_produkcji.py --year 2026

# Z niestandardowym plikiem BOM
py tools/planowanie_produkcji.py --year 2026 --bom-file "D:/pliki/Wycena PQ.xlsm"

# Tylko zamówienia (backward compat)
py tools/planowanie_produkcji.py --year 2026 --mode orders-only
```

**Ostrzeżenia na stderr (nie przerywają):**
```
[WARN] Brak BOM dla CZNI99999 — pominięto w gap analysis
[WARN] Mianownik #VALUE! dla CZNI12345 / SZ0xxx — pominięto
```

**Commit 5:** `feat: planowanie_produkcji — CLI --bom-file, --mode, warnings`

---

## Decyzje projektowe (rozstrzygnięte)

**Ścieżka pliku wyceny:** przekazywana z UI — Developer decyduje o mechanizmie
(file picker, pole tekstowe, itp.). Nie ma stałej ani .env.

**Brak BOM dla CZNI:** warning + kontynuuj (pomiń w gap analysis, zostaw w Arkuszu 1).
Uzasadnienie: niekompletny gap analysis → błędna decyzja zakupowa.

---

## Kryteria akceptacji całości

- [ ] pytest tests/test_planowanie_produkcji.py — PASS (min. 5 testów)
- [ ] pytest tests/test_pp_demand.py — PASS
- [ ] pytest tests/test_pp_supply.py — PASS
- [ ] pytest tests/test_pp_bom.py — PASS
- [ ] pytest tests/test_pp_gap.py — PASS
- [ ] pytest tests/test_pp_export.py — PASS
- [ ] pytest tests/ — zero regresji (wszystkie inne testy PASS)
- [ ] Excel output ma dokładnie 4 arkusze
- [ ] Arkusz 4 "Gap Analysis": wiersze z Brak>0 mają czerwone tło
- [ ] CLI: --year jedyny wymagany parametr
- [ ] CZNI bez BOM: warn na stderr, nie crash
