# Plan implementacji — Kamień milowy 1 (tools/)

Data: 2026-02-27

---

## Zakres

Implementacja 6 skryptów CLI + modułu pomocniczego + zestawu testów.
Każdy skrypt przyjmuje argumenty z CLI, zwraca JSON na stdout zgodny z kontraktami z ARCHITECTURE.md.

---

## Struktura plików po implementacji

```
tools/
├── sql_query.py          ← narzędzie: zapytania SQL Server
├── build_index.py        ← budowa indeksu SQLite z XLSM
├── db.py                 ← wspólna logika połączenia SQLite
├── search_docs.py        ← przeszukiwanie indeksu FTS5
├── search_solutions.py   ← przeszukiwanie solutions/
├── search_windows.py     ← przeszukiwanie erp_windows.json
└── save_solution.py      ← zapis nowego rozwiązania do solutions/

tests/
├── conftest.py           ← wspólne fixtures
├── test_sql_query.py
├── test_build_index.py
├── test_search_docs.py
├── test_search_solutions.py
├── test_search_windows.py
└── test_save_solution.py

requirements.txt
```

---

## Moduł 0: requirements.txt (warunek wstępny)

Brakujący plik. Zawartość:

```
pyodbc>=5.0
python-dotenv>=1.0
openpyxl>=3.1
pytest>=8.0
```

---

## Moduł 1: sql_query.py

**Podstawa:** logika z `experiments/e04_mcp_tool.py` (w całości przetestowana).

**CLI:**
```
python tools/sql_query.py "SELECT TOP 5 ZaN_GIDNumer FROM CDN.ZamNag"
```
Wynik: JSON na stdout, kod wyjścia 0 nawet przy błędzie SQL (błąd w JSON).

**Funkcje publiczne:**
- `validate_query(sql: str) -> str | None` — zwraca komunikat błędu lub None
- `run_query(sql: str) -> dict` — wykonuje zapytanie, zwraca JSON-dict per kontrakt
- `main()` — entry point CLI: czyta `sys.argv[1]`, drukuje JSON

**Zmiany względem e04:**
- Dodanie `main()` z obsługą braku argumentu (błąd JSON zamiast wyjątku)
- `default=str` w `json.dumps` dla typów nieseryalizowalnych (datetime, Decimal)
- Konfiguracja połączenia wyłącznie przez `.env` (SQL_USERNAME/PASSWORD opcjonalne — fallback na SQL_TRUSTED_CONNECTION)
- Timeout sterownika pyodbc: 30 sekund (zamiast 10 z eksperymentu)

**Kontrakt wyjścia (bez zmian z ARCHITECTURE.md):**
```json
{
  "ok": true,
  "data": {"columns": [...], "rows": [...], "row_count": 42},
  "error": null,
  "meta": {"duration_ms": 142, "truncated": false}
}
```

**Testy (test_sql_query.py):**
- Mockowanie `pyodbc.connect` przez `unittest.mock.patch`
- Happy path: poprawny SELECT → JSON z rows i row_count
- TOP injection: SELECT bez TOP → dodane TOP 100
- Blokada DML: INSERT/DELETE/EXEC → ok=false, VALIDATION_ERROR
- Wielokrotne instrukcje (`;`) → VALIDATION_ERROR
- Błąd SQL (pyodbc.Error) → ok=false, SQL_ERROR z message
- Brak argumentu CLI → ok=false, MISSING_ARGUMENT
- Serializacja datetime/Decimal → bez wyjątku

---

## Moduł 2: db.py

**Odpowiedzialność:** jeden punkt tworzenia połączenia SQLite, używany przez build_index.py i search_docs.py.

**API:**
```python
def get_db(path: str | None = None) -> sqlite3.Connection
```
- Jeśli `path=None`: odczytuje `ERP_DOCS_PATH` z `.env`, konstruuje `{ERP_DOCS_PATH}/index/docs.db`
- Ustawia `row_factory = sqlite3.Row`
- Tworzy katalog nadrzędny jeśli nie istnieje

**Brak testów jednostkowych** — moduł jest trivialny; testowany pośrednio przez build_index i search_docs.

---

## Moduł 3: build_index.py

**Cel:** jednorazowa (idempotentna) budowa `docs.db` z XLSM.

**CLI:**
```
python tools/build_index.py [--xlsm PATH] [--db PATH]
```
- `--xlsm`: domyślnie z `.env` `ERP_DOCS_PATH/raw/` (pierwsza znaleziona `*.xlsm`)
- `--db`: domyślnie przez `db.get_db()`
- Zawsze buduje od zera (DROP IF EXISTS + CREATE)
- Wynik: informacja tekstowa na stdout (nie JSON — narzędzie administracyjne)

**Schemat SQLite:**

```sql
CREATE TABLE tables (
    table_id   INTEGER PRIMARY KEY,
    table_name TEXT NOT NULL,   -- CDN.XXX
    table_label TEXT,           -- Nazwa własna tabeli
    prefix     TEXT,
    description TEXT
);

CREATE TABLE columns (
    col_id       INTEGER,
    table_name   TEXT NOT NULL,
    col_name     TEXT NOT NULL,  -- SQL name
    col_label    TEXT,           -- Nazwa własna kolumny
    role         TEXT,
    is_useful    TEXT,
    preferred    TEXT,
    data_type    TEXT,
    description  TEXT,
    value_dict   TEXT,           -- Słownik wartości kolumn
    sample_values TEXT           -- Przykładowe wartości kolumn
);

CREATE TABLE relations (
    source_table TEXT,
    source_col   TEXT,
    target_table TEXT,
    target_col   TEXT
);

CREATE VIRTUAL TABLE columns_fts USING fts5(
    table_name,
    table_label,
    col_name,
    col_label,
    description,
    is_useful    UNINDEXED,
    preferred    UNINDEXED,
    data_type    UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 2'
);
```

**Parsowane arkusze XLSM:**
- `Tabele` — header wiersz 1, kolumny per e03 (COL_TABELE)
- `Kolumny` — header na wierszu z "Numer tabeli" (COL_KOLUMNY), per e03
- `Relacje` — do zweryfikowania indeksów podczas implementacji
- `Słownik wartości kolumn` — do zweryfikowania indeksów podczas implementacji
- `Przykładowe wartości kolumn` — do zweryfikowania indeksów podczas implementacji

**Uwaga:** Indeksy kolumn arkuszy Relacje, Słownik i Przykładowe wymagają inspekcji przed implementacją
(dodamy skrypt `experiments/e06_xlsm_sheet_inspection.py` jako krok zerowy).
Jeśli inspekcja wykaże nieoczekiwaną strukturę — plan dostosowujemy.

**Łączenie danych:** value_dict i sample_values łączone z kolumnami przez (table_name, col_name).

**Testy (test_build_index.py):**
- Fixture: minimalne dane in-memory (dict z tabelami i kolumnami, bez realnego Excel)
- Test budowy schematu SQLite: tabele i FTS5 istnieją po wywołaniu
- Test parsowania: poprawne mapowanie kolumn Excel → SQLite
- Test idempotentności: dwukrotne wywołanie → brak błędu, dane nadpisane
- Test FTS5: po budowie — wyszukiwanie `kontrah*` zwraca wyniki

---

## Moduł 4: search_docs.py

**CLI:**
```
python tools/search_docs.py "kontrahent zamowienie" [--table CDN.ZamNag] [--useful-only] [--limit 10]
```

**Logika:**
1. Otwórz `docs.db` przez `db.get_db()`
2. Tokenizuj frazę — każdy token zamieniaj na `token*` (prefix matching per E-03)
3. Złóż zapytanie FTS5: `columns_fts MATCH 'token1* token2*'`
4. Opcjonalny filtr: `AND table_name = ?` jeśli `--table`
5. Opcjonalny filtr: `AND is_useful NOT IN ('', 'None', 'Relacja', 'Nie')` jeśli `--useful-only`
6. Limit: domyślnie 20

**Kontrakt wyjścia:**
```json
{
  "ok": true,
  "data": {
    "results": [
      {
        "table_name": "CDN.ZamNag",
        "table_label": "Nagłówki zamówień",
        "col_name": "ZaN_KntGIDNumer",
        "col_label": "ID Kontrahenta",
        "data_type": "INTEGER",
        "is_useful": "Tak",
        "description": "...",
        "value_dict": "...",
        "sample_values": "..."
      }
    ]
  },
  "error": null,
  "meta": {"duration_ms": 12, "truncated": false}
}
```

**Testy (test_search_docs.py):**
- Fixture: in-memory SQLite z seed data (3-5 tabel, 10-15 kolumn)
- FTS prefix: `kontrah*` → wyniki zawierające "kontrahent"
- Remove diacritics: `kontrach*` pasuje do "kontrachent" (bez ogonków)
- Filtr --table: zwraca tylko z danej tabeli
- Filtr --useful-only: brak kolumn bez flagi
- Brak wyników: ok=true, results=[]
- Brak bazy (docs.db nie istnieje) → ok=false, NOT_FOUND

---

## Moduł 5: search_solutions.py

**CLI:**
```
python tools/search_solutions.py "kontrahent" [--window "Okno towary"] [--type columns|filters]
```

**Logika:**
1. Traversal `SOLUTIONS_PATH/solutions in ERP windows/` rekurencyjnie
2. Dla każdego `.sql` który nie jest `filtr.sql`:
   - Wyodrębnij `window` i `view` ze ścieżki
   - Wyodrębnij `type` ("columns" lub "filters") ze ścieżki
   - Wyodrębnij `name` z nazwy pliku (bez `.sql`)
   - Wczytaj treść pliku
3. Filtruj: szukaj frazy (case-insensitive) w: name + content + window + view
4. Opcjonalny filtr `--window` (case-insensitive match w ścieżce)
5. Opcjonalny filtr `--type`
6. Limit: 20 wyników

**Kontrakt wyjścia (uproszczony relative to ARCHITECTURE.md):**
```json
{
  "ok": true,
  "data": {
    "results": [
      {
        "path": "solutions in ERP windows/Okno towary/Towary według EAN/filters/archiwalny.sql",
        "window": "Okno towary",
        "view": "Towary według EAN",
        "type": "filters",
        "name": "archiwalny",
        "sql": "twr_archiwalny = 1",
        "filtr_sql": "(Twr_GIDNumer=3282)"
      }
    ]
  },
  "error": null,
  "meta": {"duration_ms": 5, "truncated": false}
}
```

`filtr_sql` — treść `filtr.sql` z katalogu widoku. Zawiera kotwicę definiującą tabelę źródłową widoku
(np. `Twr_GIDNumer=3282`). Agent odczytuje ją, żeby wiedzieć jaka tabela jest punktem startu
przed generowaniem SQL dla danego okna. Wartość `null` jeśli `filtr.sql` nie istnieje.

Odchylenie od kontraktu z ARCHITECTURE.md: `window`/`view`/`name`/`filtr_sql` zamiast `window_id`/`keywords`/`status`
— window_id i status będą możliwe po wdrożeniu erp_windows.json (KM2).

**Testy (test_search_solutions.py):**
- Fixture: `tmp_path` z minimalną strukturą (2 okna, 2 widoki, 3 pliki .sql + filtr.sql per widok)
- Wyszukiwanie słowa z nazwy pliku → trafienie
- Wyszukiwanie słowa z treści .sql → trafienie
- Filtr --window: zawęża do konkretnego okna
- Filtr --type: tylko columns lub tylko filters
- `filtr_sql` w wyniku odpowiada treści filtr.sql z katalogu widoku
- `filtr_sql` = null gdy widok nie ma pliku filtr.sql
- Pusty wynik → ok=true, results=[]
- Brak katalogu solutions → ok=false, NOT_FOUND

---

## Moduł 6: search_windows.py

**CLI:**
```
python tools/search_windows.py "towary ean" [--type columns|filters]
```

**Logika:**
1. Wczytaj `SOLUTIONS_PATH/erp_windows.json`
2. Dla każdego wpisu: szukaj frazy (case-insensitive) w `name` + `aliases`
3. Opcjonalny filtr: `config_types` zawiera `--type`
4. Zwróć pasujące okna per kontrakt

**Kontrakt:** per ARCHITECTURE.md section 11 (bez zmian).

**Uwaga:** erp_windows.json powstaje w KM2. Narzędzie zwróci ok=true, results=[] jeśli plik nie istnieje jeszcze — zamiast błędu.

**Testy (test_search_windows.py):**
- Fixture: minimalne erp_windows.json (2 okna) w `tmp_path`
- Dopasowanie po nazwie (case-insensitive)
- Dopasowanie po aliasie
- Filtr --type
- Plik nie istnieje → ok=true, results=[]
- Plik istnieje ale JSON niepoprawny → ok=false, PARSE_ERROR

---

## Moduł 7: save_solution.py

**CLI:**
```
python tools/save_solution.py \
  --window "Okno towary" \
  --view "Towary według EAN" \
  --type filters \
  --name "brak jpg" \
  --sql "Twr_GIDNumer NOT IN (SELECT ...)"
```

Dla długiego SQL: `--sql-file PATH` jako alternatywa.

**Logika:**
1. Złóż ścieżkę: `SOLUTIONS_PATH/solutions in ERP windows/{window}/{view}/{type}/{name}.sql`
2. Jeśli plik istnieje → błąd (nie nadpisuje bez `--force`)
3. Utwórz katalogi jeśli nie istnieją
4. Zapisz treść SQL do pliku
5. Zwróć JSON z pełną ścieżką

**Kontrakt wyjścia:**
```json
{
  "ok": true,
  "data": {"path": "solutions in ERP windows/Okno towary/..."},
  "error": null,
  "meta": {"duration_ms": 3, "truncated": false}
}
```

**Testy (test_save_solution.py):**
- Zapis nowego pliku → plik istnieje, treść poprawna
- Zapis do nieistniejącego katalogu → katalog tworzony automatycznie
- Plik już istnieje bez --force → ok=false, FILE_EXISTS
- Plik już istnieje z --force → nadpisany
- Brakujące wymagane argumenty → ok=false, MISSING_ARGUMENT

---

## Krok zerowy: inspekcja arkuszy XLSM

Przed build_index.py: skrypt `experiments/e06_xlsm_inspect.py` drukuje
nagłówki i 2 przykładowe wiersze arkuszy Relacje, Słownik wartości kolumn,
Przykładowe wartości kolumn. Wyniki determinują mapowanie kolumn w build_index.py.

---

## Kolejność implementacji

```
[1] requirements.txt
[2] sql_query.py + test_sql_query.py        ← niezależny od SQLite
[3] db.py                                   ← warunek dla 4 i 5
[4] e06_xlsm_inspect.py                     ← inspekcja, potem build_index
[5] build_index.py + test_build_index.py    ← wymaga e06 + db.py
[6] search_docs.py + test_search_docs.py    ← wymaga db.py
[7] search_solutions.py + test_search_solutions.py
[8] search_windows.py + test_search_windows.py
[9] save_solution.py + test_save_solution.py
```

Commit po każdym kroku (conventional commits: `feat:`, `test:`).

---

## Otwarte pytania

1. **Arkusze XLSM (Relacje, Słownik, Przykładowe):** Struktura nieznana — weryfikacja w kroku zerowym (e06).

2. **SQL Windows Authentication:** `.env.example` ma `SQL_TRUSTED_CONNECTION=yes`.
   Jak powinno wyglądać połączenie gdy SQL_USERNAME jest pusty — Trusted Connection przez Kerberos/NTLM?
   *(Do potwierdzenia przed implementacją sql_query.py)*

3. **XLSM path:** Obecnie hardcoded w e02/e03 jako pełna ścieżka absolutna.
   Proponuję: `ERP_DOCS_PATH/raw/` + auto-detekcja pierwszego `.xlsm` w folderze.
   Alternatywa: jawna zmienna `XLSM_PATH` w `.env`. Które podejście?

4. **search_solutions.py — kodowanie wyników:** Kontrakt w ARCHITECTURE.md zawiera `window_id` i `keywords` (pole z e02 centralnego index.json, który odrzuciliśmy). Proponuję uproszczony format opisany wyżej — czy OK?

---

*Plan przygotowany: 2026-02-27*
