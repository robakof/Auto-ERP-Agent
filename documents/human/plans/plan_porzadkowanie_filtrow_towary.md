# Plan porządkowania filtrów — Okno Towary

Data: 2026-03-26

Dotyczy obu widoków: **Towary według grup** i **Towary według EAN**
(struktura identyczna — działania wykonać równolegle w obu).

---

## Obecna sytuacja

### Filtry z konwencją `NN [KATEGORIA]` — docelowa struktura, zostawiamy:
| Plik | Opis |
|---|---|
| `00 [SZUKAJ] Towary – kod, nazwa, EAN, sezon` | 4 pola: Kod / Nazwa / EAN / Sezon |
| `01 [JAKOŚĆ] Kartoteki – braki, duplikaty, niespójności` | braki jpg, duplik. EAN, niespójne JM, mobilna |
| `02 [FIN] VAT – sprzedaż i zakupy` | stawka VAT sprzedaży + zakupu |
| `03 [DOSTĘPNOŚĆ] Dostępność, zamawialność i stany` | stan mag, mobilna, wyprzedane, Buszewo |
| `05 [ROZJAZDY] Rozbieżności handlowo-magazynowe` | stan handlowy ≠ magazynowy |

### Filtry bez konwencji — wymagają decyzji:
| Plik | Stan | Propozycja |
|---|---|---|
| `super filtr` | Aktywnie używany — Szukaj + Status ofertowy + Sezon + Archiwalny + Stan mag + Mobilna | **Przemianować** → `00 [SZUKAJ+] Szybki filtr wielokryteriowy` |
| `Towary Wyprzedane` / `Towary wyprzedane` | Pokryte przez `03 [DOSTĘPNOŚĆ]` | **Usunąć** (parametr Wyprzedane jest w `03`) |
| `wyprzedane do archiwizacji` | Osobna logika: wyprzedane BEZ zasobu — podzbiór `03` | **Usunąć** (można wyszukać przez `03`: Wyprzedane=Tak + stan=Brak) |
| `Brak na Buszewie` | Pokryte przez `03 [DOSTĘPNOŚĆ]` | **Usunąć** (parametr Buszewo jest w `03`) |
| `Stawka Vat (Sprzedaż)` / `Stawka VaT (Zakupy)` / `Stawka VAT (Sprzedaż)` | Stare, pokryte przez `02 [FIN]` | **Usunąć** |
| `Wyszukiwanie po kodzie, nazwie, EAN-ie` / `Wyszukiwanie po kodzie, nazwie, EAN` | Stara wersja jednego pola, pokryte przez `00 [SZUKAJ]` | **Usunąć** |
| `brak jpg` | Pokryte przez `01 [JAKOŚĆ]` | **Usunąć** |
| `Towary bez zdjęcia` | Pokryte przez `01 [JAKOŚĆ]` | **Usunąć** |
| `Zdublowane EAN-y` / `Zdublowane Eany` (dwa pliki – literówka) | Pokryte przez `01 [JAKOŚĆ]` | **Usunąć oba** |
| `Udostępnianie w mobilnej sprzedaży` / `Udostępnienie w moblinej sprzedaży` (literówka) | Pokryte przez `03 [DOSTĘPNOŚĆ]` lub `super filtr` | **Usunąć oba** |
| `archiwalny` | Jeden parametr, pokryte przez `super filtr` | **Usunąć** |
| `sezon po nazwie` | Inny mechanizm niż `00 [SZUKAJ]`? Wymaga weryfikacji | **Sprawdzić treść** |
| `data utworzenia kartoteki` | Nie ma odpowiednika w NN — osobna użyteczność | **Przemianować** → `07 [HISTORIA] Data utworzenia kartoteki` |
| `stan handlowy różny niż magazynowy` / `stan hndlowy magazynowy` (literówka) | Pokryte przez `05 [ROZJAZDY]`? Wymaga weryfikacji | **Sprawdzić treść** |
| `filtr.sql` (główny) | Stary domyślny — wymaga weryfikacji | **Sprawdzić treść** |

---

## Docelowa struktura (po porządkowaniu)

```
Okno towary / Towary według grup / filters/
  00 [SZUKAJ] Towary – kod, nazwa, EAN, sezon.sql
  00 [SZUKAJ+] Szybki filtr wielokryteriowy.sql    ← przemianowany "super filtr"
  01 [JAKOŚĆ] Kartoteki – braki, duplikaty, niespójności.sql
  02 [FIN] VAT – sprzedaż i zakupy.sql
  03 [DOSTĘPNOŚĆ] Dostępność, zamawialność i stany.sql
  05 [ROZJAZDY] Rozbieżności handlowo-magazynowe.sql
  07 [HISTORIA] Data utworzenia kartoteki.sql       ← przemianowany
  (do ustalenia po weryfikacji: sezon po nazwie, stan hndlowy, filtr.sql)
```

---

## Kroki do wykonania

1. **Weryfikacja 3 plików** przed podjęciem decyzji:
   - `sezon po nazwie.sql` — czy logika różni się od `00 [SZUKAJ]`?
   - `stan handlowy różny niż magazynowy.sql` — czy pokryte przez `05 [ROZJAZDY]`?
   - `filtr.sql` (główny) — czy aktywnie używany?

2. **Przemianować** (zmiana nazwy pliku):
   - `super filtr.sql` → `00 [SZUKAJ+] Szybki filtr wielokryteriowy.sql`
   - `data utworzenia kartoteki.sql` → `07 [HISTORIA] Data utworzenia kartoteki.sql`

3. **Usunąć** (po potwierdzeniu przez użytkownika):
   - `Towary Wyprzedane.sql` / `Towary wyprzedane.sql`
   - `wyprzedane do archiwizacji.sql`
   - `Brak na Buszewie.sql`
   - `Stawka Vat (Sprzedaż).sql` / `Stawka VaT (Zakupy).sql` / `Stawka VAT (Sprzedaż).sql`
   - `Wyszukiwanie po kodzie, nazwie, EAN-ie.sql` / `Wyszukiwanie po kodzie, nazwie, EAN.sql`
   - `brak jpg.sql`
   - `Towary bez zdjęcia.sql`
   - `Zdublowane EAN-y.sql` / `Zdublowane Eany.sql`
   - `Udostępnianie w mobilnej sprzedaży.sql` / `Udostępnienie w moblinej sprzedaży.sql`
   - `archiwalny.sql`

4. Wykonać te same działania dla widoku **Towary według EAN**.

---

## Pytanie otwarte

Czy numer `04` jest zarezerwowany? Aktualnie brak `04 [...]` w strukturze.
Można by go wykorzystać np. na `04 [ATRYBUTY] Status ofertowy, sezon`.
