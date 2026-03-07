# Zmiany do wdrożenia — workflow BI + refaktor tools/

## Status ERP_VIEW_WORKFLOW.md

Zrealizowane (commit 8c48561):
- Brudnopis SQL (drafts/), plan jako Excel, zasady tłumaczenia wartości
- Analiza kolumna po kolumnie, reguła pominięcia
- Jednorazowe zapytanie CDN.NazwaObiektu, progress log, ochrona dokumentacji

Do zrealizowania w ERP_VIEW_WORKFLOW.md — wymaga najpierw narzędzi (patrz niżej):
1. Aktualizacja tabeli kolumn planu: dodać Opis_w_dokumentacji, Przykladowe_wartosci, Komentarz_Usera
2. Instrukcja jak agent wypełnia Opis_w_dokumentacji i Przykladowe_wartosci przez search_docs.py
3. Krok "odczyt planu po edycji usera" via excel_read_rows.py (nowy tool)

---

# Plan refaktoru tools/ — modularyzacja + rename + excel_read_rows

## Cel

1. Wyekstrahować współdzieloną logikę do `tools/lib/` (SqlClient, ExcelWriter, ExcelReader)
2. Nadać toolsom nazwy domenowe (excel_*, docs_*, solutions_*, windows_*)
3. Dodać nowy tool `excel_read_rows.py`
4. Zaktualizować ARCHITECTURE.md
5. Całość TDD: testy lib/ przed implementacją, testy toolsów zaktualizowane

---

## Zmiany nazw toolsów

| Stara nazwa | Nowa nazwa | Uzasadnienie |
|---|---|---|
| `export_excel.py` | `excel_export.py` | domena Excel na przodzie |
| `export_bi_view.py` | `excel_export_bi.py` | domena Excel na przodzie |
| `read_excel_stats.py` | `excel_read_stats.py` | domena Excel na przodzie |
| *(nowy)* | `excel_read_rows.py` | domena Excel, nowa funkcja |
| `search_docs.py` | `docs_search.py` | domena docs |
| `build_index.py` | `docs_build_index.py` | domena docs |
| `search_solutions.py` | `solutions_search.py` | domena solutions |
| `save_solution.py` | `solutions_save.py` | domena solutions |
| `search_windows.py` | `windows_search.py` | domena windows |
| `update_window_catalog.py` | `windows_update.py` | domena windows |
| `sql_query.py` | `sql_query.py` | nazwa ok, bez zmian |
| `db.py` | `db.py` | wewnętrzny helper, bez zmian |

---

## Nowe moduły tools/lib/

### lib/sql_client.py — klasa SqlClient

Odpowiedzialność: połączenie z SQL Server, guardrails, wykonanie zapytania.

Używana przez: `sql_query.py`, `excel_export.py`, `excel_export_bi.py`

```
SqlClient
  .validate(sql) -> str | None           # błąd lub None gdy ok
  .execute(sql, inject_top) -> dict      # pełny pipeline: validate → connect → fetch → JSON
  .get_connection() -> pyodbc.Connection
```

Kontrakt `execute()` zwraca słownik ze standardowymi polami: `ok`, `columns`, `rows`,
`row_count`, `truncated`, `duration_ms`, `error`. Toolsy opakowują to w finalny JSON.

### lib/excel_writer.py — klasa ExcelWriter

Odpowiedzialność: tworzenie plików xlsx: nagłówki, dane, formatowanie, auto-width.

Używana przez: `excel_export.py`, `excel_export_bi.py`

```
ExcelWriter
  .add_sheet(name, columns, rows) -> None
  .save(path) -> None
```

Przenosi z toolsów: `_write_excel()`, stałe formatowania, `freeze_panes`, auto-width.

### lib/excel_reader.py — klasa ExcelReader

Odpowiedzialność: odczyt plików xlsx: statystyki i dane wierszami.

Używana przez: `excel_read_stats.py`, `excel_read_rows.py`

```
ExcelReader(path, sheet_name)
  .read_stats(max_unique, columns) -> dict     # obecna logika read_excel_stats
  .read_rows(columns) -> dict                  # nowe: zwraca wiersze jako JSON
```

---

## Nowy tool: excel_read_rows.py

```
python tools/excel_read_rows.py --file PATH.xlsx [--sheet NAZWA] [--columns col1,col2]
  → data.rows[], data.columns[], data.row_count | error
```

Przeznaczenie: agent odczytuje plan Excel po edycji przez usera (kolumna Komentarz_Usera).
Bez `--columns` zwraca wszystkie kolumny. Brak limitu wierszy (plan ma ~50–80 wierszy).

---

## Struktura po refaktorze

```
tools/
├── lib/
│   ├── __init__.py
│   ├── sql_client.py
│   ├── excel_writer.py
│   └── excel_reader.py
│
├── sql_query.py              ← używa lib/sql_client.py
├── excel_export.py           ← używa lib/sql_client.py + lib/excel_writer.py
├── excel_export_bi.py        ← używa lib/sql_client.py + lib/excel_writer.py
├── excel_read_stats.py       ← używa lib/excel_reader.py
├── excel_read_rows.py        ← używa lib/excel_reader.py (NOWY)
├── docs_search.py
├── docs_build_index.py
├── solutions_search.py
├── solutions_save.py
├── windows_search.py
├── windows_update.py
├── db.py
└── (stare nazwy usunięte)
```

---

## Testy

### Nowe pliki testów (TDD — pisane PRZED implementacją lib/)

| Plik testu | Testuje |
|---|---|
| `tests/test_lib_sql_client.py` | SqlClient.validate, SqlClient.execute (mock pyodbc) |
| `tests/test_lib_excel_writer.py` | ExcelWriter.add_sheet, ExcelWriter.save |
| `tests/test_lib_excel_reader.py` | ExcelReader.read_stats, ExcelReader.read_rows |

### Zaktualizowane testy (po refaktorze)

| Stary plik | Nowy plik | Zmiana |
|---|---|---|
| `test_export_excel.py` | `test_excel_export.py` | import + mockowanie na poziomie lib/ |
| `test_export_bi_view.py` | `test_excel_export_bi.py` | import + mockowanie na poziomie lib/ |
| `test_read_excel_stats.py` | `test_excel_read_stats.py` | import |
| `test_sql_query.py` | bez zmiany nazwy | mockowanie na poziomie SqlClient |
| `test_search_docs.py` | `test_docs_search.py` | import |
| `test_build_index.py` | `test_docs_build_index.py` | import |
| `test_search_solutions.py` | `test_solutions_search.py` | import |
| `test_save_solution.py` | `test_solutions_save.py` | import |
| `test_search_windows.py` | `test_windows_search.py` | import |
| `test_update_window_catalog.py` | `test_windows_update.py` | import |

Nowy plik: `tests/test_excel_read_rows.py`

### Duplikacja make_mock_conn

Funkcja `make_mock_conn` jest teraz w `test_sql_query.py` i `test_export_excel.py`.
Po refaktorze przenosi się do `tests/conftest.py` jako wspólny fixture.

---

## CLAUDE.md

Zaktualizować sygnatury narzędzi (nowe nazwy plików).
Kolumny planu Excel: dodać `Opis_w_dokumentacji`, `Przykladowe_wartosci`, `Komentarz_Usera`.

---

## ARCHITECTURE.md

Zaktualizować sekcję 1.2 (tabela toolsów) oraz dodać podsekcję opisującą `tools/lib/`
jako warstwę współdzieloną. Pozostałe sekcje (bot, BI, deployment) bez zmian.

---

## Kolejność implementacji

1. Testy lib/sql_client.py → implementacja SqlClient
2. Testy lib/excel_writer.py → implementacja ExcelWriter
3. Testy lib/excel_reader.py (w tym read_rows) → implementacja ExcelReader
4. Refaktor sql_query.py → używa SqlClient; zaktualizuj test_sql_query.py
5. Refaktor excel_export.py + test; excel_export_bi.py + test; excel_read_stats.py + test
6. Nowy excel_read_rows.py + test
7. Rename pozostałych toolsów (docs_*, solutions_*, windows_*) + rename testów
8. Usuń stare pliki toolsów
9. ARCHITECTURE.md + CLAUDE.md
10. Wszystkie testy zielone → commit
