# ADR-003: Harmonogram produkcji — moce produkcyjne i priorytetyzacja

Date: 2026-03-30
Status: Proposed

---

## Context

Moduł `planowanie_produkcji` (ADR-002) realizuje gap analysis — wylicza braki surowców.
Następny krok: **planowanie czasu produkcji** — ile godzin zajmie realizacja zamówień
i w jakiej kolejności produkować (harmonogram dzienny + priorytetyzacja).

### Dane wejściowe (zweryfikowane)

| Źródło | Lokalizacja | Co daje |
|---|---|---|
| Wydajność (szt/h) | Wycena Zniczy, wiersz `Roboczogodzina Otorowo`, col J = mianownik | Ile sztuk/godz. produkuje 1 osoba |
| Moce produkcyjne | `moce produkcyjne.xlsx`, kolumny: Data, Godziny pracy, Nadgodziny, Osoby, Ilość godzin na dzień | Godziny dostępne **per data** (= Godziny × Osoby + Nadgodziny) |
| Już wyprodukowane | ERP: PW o nazwie `P_P Otorowo*` | Ile sztuk przyjęto na stan z produkcji |
| Zamówienia + priorytety | CDN.ZamNag + ZamElem (istniejące pp_demand.py) + kolumna Priorytet | Popyt + ręczna priorytetyzacja |

### Reguły harmonogramu

1. **Deadline hard** — `Data_Realizacji` musi być dotrzymana
2. **Priorytet ręczny** — zamówienie oznaczone priorytetem przesuwa się wyżej (produkowane wcześniej)
3. **Agregacja** — ten sam kod CZNI agregujemy jeśli terminy na to pozwalają; rozdzielamy gdy deadline tego wymaga
4. **Odejmowanie produkcji** — PW `P_P Otorowo*` odejmuje od zapotrzebowania; jeśli produkt w pełni pokryty → znika z harmonogramu

### Priorytetyzacja — flow

```
Run 1 (bez priorytetów):
  → Excel arkusz "Zamówienia" z pustą kolumną Priorytet

Użytkownik edytuje Excel:
  → wpisuje "1" przy priorytetowych zamówieniach

Run 2 (z priorytetami):
  → --priority-file PATH_DO_EXCELA
  → harmonogram uwzględnia priorytety
```

Granulacja priorytetu: **Nr_Zamowienia** (nie kod CZNI) — użytkownik myśli zamówieniami, nie kodami.

---

## Decision

### Nowe moduły

```
tools/lib/
  pp_capacity.py      ← NOWY: odczyt moce_produkcyjne.xlsx → hours_per_day: float
  pp_produced.py      ← NOWY: query ERP PW P_P Otorowo* → dict[czni_kod, qty_produced]
  pp_schedule.py      ← NOWY: algorytm harmonogramu → list[ScheduleSlot]
  pp_bom.py           ← ROZSZERZENIE: wyciągnij też Roboczogodzina → dict[czni_kod, units_per_hour]
  pp_export.py        ← ROZSZERZENIE: dodaj arkusze Harmonogram + Gantt, Priorytet w Zamówieniach
```

### pp_capacity.py

Plik `moce produkcyjne.xlsx` ma kolumny:
`Data | Godziny pracy | Nadgodziny | Osoby | Ilość godzin na dzień`

gdzie: `Ilość godzin na dzień = Godziny pracy × Osoby + Nadgodziny` (pre-wyliczone w pliku).

Capacity **różna per data** — obsada i nadgodziny zmieniają się dziennie.

```python
@dataclass
class DayCapacity:
    date: date
    hours_per_day: float          # = Godziny pracy × Osoby + Nadgodziny
    persons: int
    regular_hours: float
    overtime_hours: float

def load_capacity(xlsx_path: Path) -> dict[date, DayCapacity]:
    """
    Wczytuje moce produkcyjne z pliku xlsx.
    Klucz: data. Wartość: DayCapacity z pre-wyliczonymi godzinami.
    """
```

Scheduler używa `capacity[current_date].hours_per_day` dla każdego dnia osobno.
Jeśli daty brak w pliku → użyj ostatniej dostępnej wartości lub 0 (warn).

### pp_bom.py — rozszerzenie

Obecnie filtruje wiersze `Roboczogodzina Otorowo` (kolumna F = "Koszt*").
Rozszerzenie: wyciągnij je jako **wydajność**, nie koszt.

```python
@dataclass
class EfficiencyEntry:
    czni_kod: str
    units_per_hour: float   # col J (mianownik) = szt/h dla 1 osoby

def load_efficiency(xlsm_path: Path) -> dict[str, EfficiencyEntry]:
    """
    Z arkusza 'Wycena Zniczy' wyciąga wiersze gdzie:
    - col F = 'Robocizna' (nie 'Roboczogodzina Otorowo' — faktyczna wartość w pliku)
    - col B = czni_kod, col J = units_per_hour
    Klucz: czni_kod

    Uwaga: per CZNI są 2 wiersze Robocizna:
      J=1      → stawka kosztowa (ignoruj)
      J=30-70  → właściwa wydajność szt/h
    Implementacja bierze max(J) per CZNI — eliminuje J=1.
    """
```

### pp_produced.py

```python
@dataclass
class ProducedQty:
    czni_kod: str
    qty: float

def fetch_produced(year: int) -> dict[str, float]:
    """
    Query ERP: PW o nazwie LIKE 'P_P Otorowo%' dla danego roku.
    Zwraca {czni_kod: suma_qty}.
    DEPENDENCY: ERP Specialist dostarcza SQL.
    """
```

### pp_schedule.py — algorytm

```python
@dataclass
class ScheduleSlot:
    date: date                  # dzień produkcji
    czni_kod: str
    czni_nazwa: str
    qty: float                  # ilość do wyprodukowania
    hours_needed: float         # qty / units_per_hour
    order_numbers: list[str]    # zamówienia pokryte przez ten slot
    deadline: date              # najwcześniejszy deadline z pokrytych zamówień
    priority: bool              # czy jakieś zamówienie ma priorytet

def build_schedule(
    demand: list[OrderRow],
    efficiency: dict[str, EfficiencyEntry],
    produced: dict[str, float],
    capacity: CapacityConfig,
    priorities: set[str],       # numery zamówień z Priorytet=1
    start_date: date,
) -> list[ScheduleSlot]:
```

**Algorytm (Earliest Deadline First z priorytetami):**

```
1. Odejmij już wyprodukowane (PW) od popytu per czni_kod
2. Jeśli remaining_qty <= 0 → produkt znika z harmonogramu
3. Agreguj zamówienia per czni_kod gdzie deadlines w tym samym przedziale
4. Sortuj zadania:
   a. priorytet=True → na górę (sort key: (0, deadline))
   b. reszta → (1, deadline)
5. Przydzielaj sloty dzień po dniu:
   remaining_hours = hours_per_day
   for task in sorted_tasks:
       hours_needed = task.qty / efficiency[task.czni_kod].units_per_hour
       while hours_needed > 0 and deadline nie przekroczona:
           today_hours = min(hours_needed, remaining_hours)
           emit ScheduleSlot(date=current_day, ...)
           hours_needed -= today_hours
           remaining_hours -= today_hours
           if remaining_hours == 0: next day
```

### pp_export.py — rozszerzenie (Excel output)

Dodatkowe arkusze do istniejących 4:

```
Arkusz 5: "Zamówienia z priorytetem"
  kolumny: Nr_Zamowienia, Data_Realizacji, Kontrahent_Kod, Towar_Kod, Towar_Nazwa, Ilosc, Priorytet
  Priorytet: pusta kolumna w Run 1; wczytana z --priority-file w Run 2
  Cel: użytkownik edytuje i przekazuje jako --priority-file do Run 2

Arkusz 6: "Harmonogram"
  kolumny: Data, CZNI_Kod, CZNI_Nazwa, Ilosc, Godziny, Zamowienia, Deadline, Priorytet
  sortowanie: Data ASC
  highlight: wiersze z Priorytet=True → żółte

Arkusz 7: "Gantt"
  wiersze: CZNI_Kod (jeden per wiersz)
  kolumny: kolejne daty (od start_date)
  wartość komórki: ilość godzin w danym dniu
  highlight: zielony = normalne, żółty = priorytet, czerwony = slot przekracza deadline
```

### CLI — zmiany

```
py tools/planowanie_produkcji.py \
  --year 2025 \
  --bom-file PATH \
  --capacity-file PATH \           ← NOWE: moce produkcyjne.xlsx
  [--priority-file PATH]           ← NOWE: Excel z kolumną Priorytet (Run 2)
  [--start-date YYYY-MM-DD]        ← NOWE: od kiedy planujemy (default: dziś)
  [--mode gap|schedule|all]        ← ROZSZERZENIE: schedule = harmonogram
```

---

## Consequences

### Zyskujemy
- Pełny harmonogram dzienny — kto produkuje co i kiedy
- Priorytetyzacja per zamówienie — intuicyjna (nr zamówienia, nie kod)
- Auto-odjęcie już wyprodukowanych — harmonogram zawsze aktualny
- Gantt w Excelu — widok dla kierownika produkcji
- Agregacja kodów CZNI — minimalizacja przezbrojeń

### Tracimy / Ryzyko
- Algorytm zakłada jednorodność fabryki (wszystkie linie pracują tak samo)
  Ryzyko: jeśli różne produkty idą na różne linie z różną wydajnością → niedoszacowanie
- `units_per_hour` z Wyceny to wydajność **1 osoby** — trzeba znać ile osób pracuje naraz
  **OTWARTE: ile osób jednocześnie na linii? Czy to też z moce produkcyjne.xlsx?**
- PW query wymaga SQL od ERP Specialist (zależność blokująca pp_produced.py)
- Priorytet file wymaga dwóch runów — UX dwuetapowy

### Zależności
- **ERP Specialist** — SQL dla PW `P_P Otorowo*`: tabele, kolumny, filtr roku
- **Użytkownik** — potwierdzenie: ile osób jednocześnie na linii (stała czy z pliku)?
- **Developer** — implementacja faz 1-5 wg tego ADR

---

## Otwarte pytania

1. **SQL dla PW** — ERP Specialist musi dostarczyć zapytanie dla `P_P Otorowo*`.

2. **Agregacja — próg?** Jak blisko muszą być deadlines żeby agregować?
   Propozycja: jeśli wszystkie deadline w obrębie tego samego tygodnia → agreguj.

---

## Fazy implementacji (dla Developera)

```
Faza 1: pp_capacity.py + pp_bom.py rozszerzenie (efficiency)
  Output: load_capacity(), load_efficiency() — unit testy

Faza 2: pp_produced.py (czeka na SQL od ERP Specialist)
  Output: fetch_produced() — integration test z ERP

Faza 3: pp_schedule.py — algorytm EDF + priorytet + agregacja
  Output: build_schedule() — unit testy (mock demand/efficiency/capacity)

Faza 4: pp_export.py — arkusze 5-7 (Zamówienia z priorytetem, Harmonogram, Gantt)
  Output: Excel z 7 arkuszami

Faza 5: CLI rozszerzenie + integracja end-to-end
  Output: py planowanie_produkcji.py --mode schedule end-to-end PASS
```
