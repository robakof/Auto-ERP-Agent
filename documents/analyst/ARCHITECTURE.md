# Analityk Danych — Architektura

---

## 1. Rola i zakres

Analityk Danych to osobna rola agenta — read-only inspektor jakości danych.
Nie konfiguruje ERP, nie buduje widoków, nie modyfikuje danych.

**Zakres wejściowy:**
- Widoki BI (`BI.*`) — źródło podstawowe
- Surowe tabele CDN — gdy widok nie istnieje lub problem leży głębiej niż widok

**Zakres wyjściowy:**
- Raport Excel z obserwacjami i konkretnymi rekordami do poprawki
- Docelowo: email z raportem (poza MVP)

**Czego analityk NIE robi:**
- Nie proponuje SQL korygującego dane (ominięcie logiki biznesowej ERP)
- Nie modyfikuje widoków ani schematu
- Nie ocenia architektury BI (to rola Developera)

---

## 2. SQLite jako lokalny obszar roboczy

Przed rozpoczęciem analizy agent eksportuje widok/tabelę do lokalnego pliku SQLite.
Cała dalsza praca odbywa się na SQLite — bez kolejnych połączeń do SQL Servera.

**Dlaczego SQLite:**
- Nieograniczone zapytania bez obciążenia bazy produkcyjnej
- Swobodne łączenie kolumn — cross-column analysis bez dodatkowych query
- Jeden plik = stan całej sesji (dane + znaleziska + rekordy do poprawki)
- SQLite już używany w projekcie (`bi_plan_generate.py`)

**Struktura pliku roboczego (`{Zakres}_workdb.db`):**

```
{Zakres}_workdb.db
├── tabela: dane        ← kopia widoku/tabeli (read-only podczas analizy)
├── tabela: findings    ← obserwacje agenta (jedna obserwacja = jeden wiersz)
└── tabela: records     ← konkretne brudne rekordy z identyfikatorami
```

---

## 3. Narzędzia

### Istniejące — bez zmian

| Narzędzie | Użycie w roli analityka |
|---|---|
| `docs_search.py` | Kontekst semantyczny kolumny przed analizą |
| `sql_query.py` | Jednorazowy eksport z SQL Servera (tylko przy inicjalizacji) |

### Nowe — do zbudowania

**`data_quality_init.py`** — eksport widoku lub tabeli CDN do SQLite.

```
python tools/data_quality_init.py \
  --source "BI.KntKarty" \
  --output "solutions/analyst/KntKarty/KntKarty_workdb.db"
```

Tworzy plik SQLite z tabelą `dane` (kopia źródła) oraz pustymi tabelami
`findings` i `records`. Jeśli plik istnieje — pyta czy nadpisać.

---

**`data_quality_query.py`** — query na lokalnym SQLite.

```
python tools/data_quality_query.py \
  --db "solutions/analyst/KntKarty/KntKarty_workdb.db" \
  --sql "SELECT Telefon, Email, COUNT(*) FROM dane WHERE Telefon LIKE '%@%' GROUP BY Telefon, Email"
```

Odpowiednik `sql_query.py` ale dla lokalnego SQLite. Obsługuje `--count-only` i `--quiet`.

---

**`data_quality_save.py`** — zapis obserwacji do tabeli `findings`.

```
python tools/data_quality_save.py \
  --db "solutions/analyst/KntKarty/KntKarty_workdb.db" \
  --column "Telefon" \
  --observation "47 rekordów zawiera znak '@' — prawdopodobne adresy email wpisane w pole telefonu." \
  --rows-affected 47
```

---

**`data_quality_records.py`** — zapis konkretnych rekordów do tabeli `records`.

```
python tools/data_quality_records.py \
  --db "solutions/analyst/KntKarty/KntKarty_workdb.db" \
  --column "Telefon" \
  --sql "SELECT Kod_Kontrahenta, Nazwa_Kontrahenta, Telefon FROM dane WHERE Telefon LIKE '%@%'"
```

Wykonuje query na SQLite i dopisuje wynik do tabeli `records`.
Agent dobiera identyfikatory rekordu samodzielnie (kod, nazwa, nr dokumentu — zależnie od kontekstu).

---

**`data_quality_report.py`** — generuje raport Excel z pliku SQLite.

```
python tools/data_quality_report.py \
  --db "solutions/analyst/KntKarty/KntKarty_workdb.db" \
  --output "solutions/analyst/KntKarty/KntKarty_report.xlsx"
```

Tworzy plik Excel z dwiema zakładkami:
- **Obserwacje** — tabela `findings` (co jest nie tak, ile rekordów)
- **Rekordy** — tabela `records` (konkretne wiersze z identyfikatorami do poprawki w ERP)

---

## 4. Workflow

### Inicjalizacja sesji

1. Ustal zakres: widok BI lub tabela CDN
2. Eksportuj do SQLite:
   ```
   python tools/data_quality_init.py --source "BI.KntKarty" --output "...workdb.db"
   ```
3. Jeśli plik SQLite już istnieje — przeczytaj tabelę `findings` (wznowienie po przerwie)

### Przegląd planu widoku (opcjonalnie, gdy widok BI ma plan)

Jeśli analizowany zakres to widok BI z istniejącym planem:

```
python tools/excel_read_rows.py \
  --file "solutions/bi/{Zakres}/{Zakres}_plan.xlsx" \
  --columns CDN_Pole,Uwzglednic,Transformacja,Alias_w_widoku
```

Skrzyżuj plan z danymi w SQLite — szukaj rozbieżności:
- kolumna oznaczona `Nie` ale faktycznie wypełniona w większości rekordów
- alias lub transformacja nie odpowiadająca rzeczywistym wartościom
- kolumna uwzględniona ale w danych stale pusta lub stała

Znaleziska zapisuj identycznie jak przy analizie danych (`data_quality_save.py`).

### Analiza

Dla każdej kolumny (lub grupy kolumn gdy kontekst tego wymaga):

**Krok 1 — zrozum co kolumna powinna zawierać:**
```
python tools/docs_search.py "{nazwa_kolumny}" --table {tabela}
```
Na podstawie nazwy, opisu, sample values — agent formuje hipotezę co powinno być w polu.

**Krok 2 — zbadaj dane przez SQLite:**
```
python tools/data_quality_query.py --db "...workdb.db" --sql "..."
```
Agent dobiera zapytanie samodzielnie. Może łączyć dowolne kolumny bez dodatkowego kosztu
połączenia. Nie ma stałego zestawu zapytań — agent decyduje co i jak sprawdzić.

**Krok 3 — jeśli znaleziono problem:**
```
# Zapisz obserwację
python tools/data_quality_save.py --db "...workdb.db" --column "..." --observation "..." --rows-affected N

# Zapisz konkretne rekordy z identyfikatorami
python tools/data_quality_records.py --db "...workdb.db" --column "..." --sql "SELECT ..."
```

Jeśli kolumna wygląda poprawnie — przejdź do następnej bez zapisu.

### Generowanie raportu

```
python tools/data_quality_report.py \
  --db "solutions/analyst/{Zakres}/{Zakres}_workdb.db" \
  --output "solutions/analyst/{Zakres}/{Zakres}_report.xlsx"
```

Pokaż użytkownikowi ścieżkę do pliku i podsumowanie (ile obserwacji, ile rekordów do poprawki).

---

## 5. Struktura plików

```
solutions/analyst/
└── {Zakres}/
    ├── {Zakres}_workdb.db      ← SQLite: dane + findings + records
    └── {Zakres}_report.xlsx    ← raport końcowy (generowany na żądanie)
```

`{Zakres}` = nazwa widoku BI lub tabeli CDN (np. `KntKarty`, `ZamNag`).

---

## 6. Format raportu Excel

### Zakładka: Obserwacje

| Kolumna | Zawartość |
|---|---|
| `Kolumna` | nazwa kolumny której dotyczy obserwacja |
| `Obserwacja` | opis problemu w naturalnym języku |
| `Liczba_rekordów` | ile wierszy dotyczy |
| `Data_analizy` | data sesji |

### Zakładka: Rekordy

Kolumny zmienne — agent dobiera identyfikatory do kontekstu tabeli
(np. `Kod_Kontrahenta`, `Nazwa_Kontrahenta`, `Telefon` dla KntKarty;
`Numer_Zamowienia`, `Kontrahent`, `Data` dla ZamNag).

Stałe kolumny: `Kolumna` (której dotyczy problem), `Wartość_problematyczna`.

---

## 7. Zarządzanie kontekstem

- Eksport do SQLite odbywa się raz — potem agent nie wraca do SQL Servera
- Analiza kolumna po kolumnie (lub mała grupa kolumn) — nie ładuj wyników wszystkich naraz
- `findings` w SQLite = stan sesji — przy wznowieniu zacznij od ich przeczytania
- `docs_search` przed query — najpierw hipoteza, potem weryfikacja

---

## 8. Poza MVP

- Wysyłka email z raportem
- Analiza trendów między sesjami
- Integracja z workflow BI (automatyczne uruchomienie po Fazie 4)
