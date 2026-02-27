# CHANGELOG — Kamień milowy 1 (tools/)

Data: 2026-02-27

---

## Nowe pliki

### tools/sql_query.py
- `validate_query(sql)` — blokada DML/DDL/EXEC/XP_, wielokrotne instrukcje, non-SELECT
- `run_query(sql)` — SELECT na SQL Server, auto-inject TOP 100, timeout 30s
- `main()` — CLI entry point, JSON na stdout, `default=str` dla datetime/Decimal
- Połączenie: wyłącznie SQL auth (SQL_USERNAME/PASSWORD z .env)

### tools/db.py
- `get_db(path=None)` — połączenie SQLite, ścieżka domyślna z ERP_DOCS_PATH/.env

### tools/build_index.py
- Parsery arkuszy XLSM: `parse_tables`, `parse_columns`, `parse_relations`,
  `parse_value_dicts`, `parse_sample_values`
- `build_schema(conn)` — DROP IF EXISTS + CREATE (idempotentne)
- `insert_data(conn, ...)` — wstawia dane + buduje FTS5 z unicode61 remove_diacritics=2
- `build_index(xlsm_path, db_path)` — główna funkcja CLI
- FTS5: `columns_fts` z polami `value_dict` i `sample_values` jako UNINDEXED

### tools/search_docs.py
- `build_fts_query(phrase)` — prefix matching (token*)
- `search_docs(phrase, table_filter, useful_only, limit, db_path)` — FTS5 query
- Filtr `--table CDN.XXX` i `--useful-only`

### tools/search_solutions.py
- `search_solutions(phrase, window_filter, type_filter, limit, solutions_path)`
- Traversal `solutions in ERP windows/`, parsowanie ścieżki → window/view/type/name
- `filtr_sql` w każdym wyniku (treść filtr.sql z katalogu widoku)
- Cache filtr.sql — czytany raz per widok

### tools/search_windows.py
- `search_windows(phrase, type_filter, solutions_path)`
- Wyszukiwanie po `name` + `aliases` (case-insensitive)
- Brak pliku erp_windows.json → puste wyniki (nie błąd)

### tools/save_solution.py
- `save_solution(window, view, sol_type, name, sql, force, solutions_path)`
- Tworzy katalogi automatycznie
- Ochrona przed nadpisaniem bez `--force`
- CLI: `--sql` (inline) lub `--sql-file PATH`

### experiments/e06_xlsm_inspect.py
- Inspekcja struktury arkuszy Relacje/Słownik/Przykładowe
- Wynik inspekcji użyty do ustalenia COL_* w build_index.py

## Zmodyfikowane pliki

### .env.example
- Usunięto `SQL_TRUSTED_CONNECTION` (używamy wyłącznie SQL auth)
- Dodano `XLSM_PATH` (wymagane przez build_index.py)

### tests/conftest.py
- Wspólne fixtures: `make_ws()`, `TABELE_ROWS`, `KOLUMNY_ROWS`, itd.

## Nowe pliki testowe

- `tests/test_sql_query.py` — 23 testy (walidacja, TOP injection, błędy SQL, CLI)
- `tests/test_build_index.py` — 27 testów (parsery, schemat, insert, FTS5)
- `tests/test_search_docs.py` — 13 testów (FTS prefix, filtry, edge cases)
- `tests/test_search_solutions.py` — 15 testów (traversal, filtr_sql, limity)
- `tests/test_search_windows.py` — 9 testów (alias, type_filter, brak pliku)
- `tests/test_save_solution.py` — 5 testów (zapis, katalogi, --force)

**Łącznie: 92 testy, 100% zielone.**
