# ADR-002: Architektura modułu planowanie_produkcji

Date: 2026-03-30
Status: Accepted

---

## Context

Użytkownik potwierdził: moduł ma realizować **pełne planowanie produkcji**, nie tylko eksport zamówień.

### Trzy źródła danych (zweryfikowane)

| Źródło | Lokalizacja | Format | Stan |
|---|---|---|---|
| Zamówienia (popyt) | CDN.ZamNag + ZamElem + KntKarty + ZaNOpisy | SQL → rows | SQL gotowe |
| BOM (skład produktu) | `documents/human/ar/dokumenty/Wycena 2026 Otorowo PQ.xlsm` → arkusz "Wycena Zniczy" | Excel → cols B, H, J | 471 produktów, gotowe do odczytu |
| Stany surowców (podaż) | CDN.TwrZasobyMag, MAG_GIDNumer=4 (OTOR_SUR) | SQL → rows | SQL gotowe |

### BOM — szczegóły (arkusz "Wycena Zniczy")

Kolumny:
- B: Akronim produktu (CZNI kod)
- H: Akronim surowca (kod surowca z ERP, np. SZ0324, DK0003)
- J: Mianownik przeliczenia

**Jednostka zamówień:** `ZaE_Ilosc` jest zawsze w sztukach (szt.) — bez wyjątków.
Brak przelicznika jednostek — `ZaE_JmZ` można ignorować w gap analysis.

**Semantyka mianownika:**
```
zapotrzebowanie_na_surowiec = ilosc_czni / mianownik

Przykłady dla CZNI43147, 1000 szt:
  Wkład WK0003:   mianownik=1    → 1000/1    = 1000 szt
  Szkło SZ0324:   mianownik=0.98 → 1000/0.98 = 1021 szt  (naddatek na tłuczenie)
  Folia FO0003:   mianownik=125  → 1000/125  = 8 rolek
  Folia FO0004:   mianownik=480  → 1000/480  = 2.1 rolek
  Paleta PAL004:  mianownik=672  → 1000/672  = 1.49 palety
```

Plik: `.xlsm` (macro-enabled), openpyxl odczytuje z `keep_vba=False, data_only=True`.
Ostrzeżenie o Data Validation — pomijalne.

---

## Decision

### Architektura modułu

```
CLI: py tools/planowanie_produkcji.py --year 2026 [--bom-file PATH]
                        │
           ┌────────────▼────────────┐
           │   planowanie_produkcji  │  orchestrator
           └──┬──────────┬──────────┬┘
              │          │          │
    ┌─────────▼──┐  ┌────▼──────┐  ┌▼────────────────┐
    │ pp_demand  │  │ pp_supply │  │   pp_bom        │
    │ SQL → ERP  │  │ SQL → ERP │  │ Excel → BOM     │
    │ zamówienia │  │ stany mag │  │ czni→[surowiec] │
    └─────────┬──┘  └────┬──────┘  └┬────────────────┘
              └──────────┴──────────┘
                         │
                ┌────────▼────────┐
                │   pp_gap        │
                │ demand × BOM    │
                │ vs supply       │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │   pp_export     │
                │ Excel 4 arkusze │
                └─────────────────┘
```

### Lokalizacja plików

```
tools/
  planowanie_produkcji.py      ← CLI orchestrator (refactor)
  lib/
    pp_demand.py               ← nowy moduł
    pp_supply.py               ← nowy moduł
    pp_bom.py                  ← nowy moduł
    pp_gap.py                  ← nowy moduł
    pp_export.py               ← nowy moduł
```

### pp_bom.py — odczyt BOM z Excel

Strategia: **bezpośredni odczyt z pliku Excel na każdym uruchomieniu** (read-only, data_only).
Brak cache SQLite — plik 5.6MB, ~8000 wierszy, odczyt ReadOnly ~2-3s. Plik zmienia się
(nowe produkty, aktualizacje BOM) → zawsze świeże dane.

Ścieżka do pliku: **przekazywana z UI** — Developer decyduje o mechanizmie przekazania
(pole w interfejsie, file picker, CLI arg). Nie ma stałej ani .env.
Błąd gdy plik nie istnieje lub nie ma arkusza "Wycena Zniczy": jasny komunikat.

```python
# BomEntry — wynik parsowania
@dataclass
class BomEntry:
    czni_kod: str
    surowiec_kod: str
    surowiec_nazwa: str
    mianownik: float  # divisor: zapotrzebowanie = ilosc_czni / mianownik

def load_bom(xlsm_path: Path) -> dict[str, list[BomEntry]]:
    """Wczytuje BOM z arkusza 'Wycena Zniczy'. Klucz: czni_kod."""
```

Filtry przy odczycie:
- Pomiń wiersze gdzie H (surowiec_kod) to None lub nie zaczyna się od litery
- Pomiń wiersze gdzie J (mianownik) to '#VALUE!' lub nie jest liczbą
- Pomiń surowce z grupy "Koszt" (kolumna F = "Koszt*") — koszty robocizny, nie fizyczne surowce

### gap_analysis.py — formuła

```python
for czni_kod, orders in demand.items():
    total_czni_qty = sum(o.ilosc for o in orders)
    for bom_entry in bom[czni_kod]:
        needed = total_czni_qty / bom_entry.mianownik
        total_needed[bom_entry.surowiec_kod] += needed

for surowiec_kod, needed in total_needed.items():
    available = supply.get(surowiec_kod, 0.0)
    brak = max(0.0, needed - available)
    gap_rows.append(GapRow(surowiec_kod, needed, available, brak))
```

### Excel output — 4 arkusze

```
Arkusz 1: "Zamówienia CZNI"
  kolumny: Nr_Zamowienia, Data_Realizacji, Kontrahent_Kod, Towar_Kod, Towar_Nazwa, Ilosc, Jednostka, Opis
  sortowanie: Data_Realizacji ASC

Arkusz 2: "Zapotrzebowanie surowców"
  kolumny: Surowiec_Kod, Surowiec_Nazwa, Ilosc_Potrzebna
  źródło: SUM(ilosc_czni / mianownik) GROUP BY surowiec
  sortowanie: Surowiec_Kod ASC

Arkusz 3: "Stany OTOR_SUR"
  kolumny: Towar_Kod, Towar_Nazwa, Jednostka, Stan
  źródło: pp_supply (bez zmian)

Arkusz 4: "Gap Analysis"
  kolumny: Surowiec_Kod, Surowiec_Nazwa, Potrzeba, Dostepne, Brak
  Brak = max(0, Potrzeba - Dostepne)
  highlight czerwony: wiersze gdzie Brak > 0
  sortowanie: Brak DESC
```

---

## Consequences

### Zyskujemy
- Moduł realizuje deklarowany cel: pełne planowanie z gap analysis
- BOM bezpośrednio z pliku wyceny — jeden plik, jedno źródło prawdy
- Gap Analysis → konkretna lista braków dla zaopatrzenia
- Warstwy rozdzielone: zmiana BOM nie wymaga zmiany kodu (tylko plik Excel)

### Tracimy / Ryzyko
- Ścieżka do pliku `.xlsm` musi być stabilna lub przekazywana przez CLI
- Jeśli BOM jest niekompletny dla produktu z zamówienia → GapRow z warn
- Surowce z grupy "Koszt" (robocizna, energia) wykluczone z gap analysis — poprawne
- Mianowniki `#VALUE!` w pliku Excel → surowiec pominięty w gap analysis → warn

### Zależności
- Developer: fazy 1-4 wg planu implementacji
- Developer: zapyta o domyślną ścieżkę pliku wyceny (stała vs .env vs arg)
- ERP Specialist: weryfikacja czy kody surowców w BOM (np. SZ0324) odpowiadają
  kodom w CDN.TwrZasobyMag (OTOR_SUR) — muszą być identyczne dla poprawnego join

---

## Otwarte pytania

1. Domyślna ścieżka pliku wyceny — gdzie powinna leżeć?
   Obecnie: `documents/human/ar/dokumenty/Wycena 2026 Otorowo PQ.xlsm`
   Stabilna lokalizacja do ustalenia z użytkownikiem.

2. Co z produktami CZNI z zamówień które NIE mają BOM w pliku wyceny?
   **Decyzja: warning + kontynuuj.**
   Komunikat stderr: "[WARN] Brak BOM dla [CZNI_KOD] — pominięto w gap analysis."
   Produkt pojawia się w Arkuszu 1 (Zamówienia) ale nie w Arkuszach 2/4 (gap analysis).
   Uzasadnienie: stop blokuje workflow zanim użytkownik może zweryfikować/uzupełnić BOM.
