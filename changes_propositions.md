# Plan refaktoryzacji — tools/

Data: 2026-02-27

---

## Diagnoza

Trzy pliki z rzeczywistymi problemami. Pozostałe (`sql_query.py`, `db.py`,
`search_windows.py`, `build_index.py`) są akceptowalne — bez zmian.

---

## 1. search_docs.py

**Problem:** `search_docs()` — 78 linii, dwa zagnieżdżone `try/except`,
budowanie klauzuli WHERE inline w środku funkcji.

```
# Obecna struktura:
def search_docs(...):           # 78 linii
    try:
        conn = get_db(...)
    except:
        return {...}            # zagnieżdżenie 1

    # budowanie WHERE inline (10 linii)

    try:
        rows = conn.execute(...).fetchall()
    except:
        return {...}            # zagnieżdżenie 2
    finally:
        conn.close()
    # formatowanie wyników (10 linii)
```

**Refaktoryzacja:**

- `_build_where(table_filter, useful_only) -> tuple[str, list]`
  Buduje klauzulę WHERE i listę parametrów. Czysta funkcja, testowalnie izolowana.

- `_execute_fts(conn, where, params, limit) -> list`
  Wykonuje zapytanie FTS5, zwraca wiersze. Rzuca wyjątek przy błędzie (obsługa
  jednym try/except w wywołującym).

- `search_docs()` skraca się do ~25 linii:
  otwiera połączenie → buduje WHERE → pobiera wiersze → formatuje wyniki.

---

## 2. search_solutions.py

**Problem:** `get_filtr_sql()` zdefiniowana jako zagnieżdżona funkcja wewnątrz
`search_solutions()` — przechwytuje `filtr_cache` przez closure.

```
# Obecna struktura:
def search_solutions(...):
    filtr_cache = {}

    def get_filtr_sql(view_dir):   # zagnieżdżona definicja
        if view_dir not in filtr_cache:
            ...
        return filtr_cache[view_dir]

    for sql_path in ...:
        ...
```

**Refaktoryzacja:**

- Wynieś na poziom modułu jako `_get_filtr_sql(view_dir: Path, cache: dict) -> str | None`
- Parametr `cache` zastępuje przechwycenie przez closure
- `search_solutions()` tworzy `filtr_cache: dict = {}` i przekazuje dalej

---

## 3. save_solution.py

**Problem:** `main()` — 40 linii z if/elif/else + dwa inline słowniki błędu.

```
# Obecna struktura:
def main():
    ...
    if args.sql:
        sql = args.sql
    elif args.sql_file:
        try:
            sql = Path(args.sql_file).read_text(...)
        except Exception as e:
            print(json.dumps({...}))   # inline dict błędu
            return
    else:
        print(json.dumps({...}))       # inline dict błędu
        return

    result = save_solution(...)
    print(json.dumps(result, ...))
```

**Refaktoryzacja:**

- Wyekstrahuj `_read_sql_content(args) -> tuple[str | None, dict | None]`
  Czyta SQL z `args.sql` lub `args.sql_file`. Zwraca `(sql, None)` lub
  `(None, error_dict)`. Obsługuje wyjątek przy odczycie pliku.

- `main()` skraca się do ~15 linii:
  ```
  sql, error = _read_sql_content(args)
  if error:
      print(json.dumps(error))
      return
  result = save_solution(...)
  print(json.dumps(result, ...))
  ```

---

## Wpływ na testy

Brak — refaktoryzacja czysto strukturalna. Publiczne API funkcji
(sygnatury i zwracane wartości) bez zmian.

---

## Poza zakresem

- `build_index.py`: `parse_value_dicts`/`parse_sample_values` mają podobną
  strukturę (DRY), ale obie ~15 linii i są czytelne — nie zmieniamy
- Wspólny helper odpowiedzi JSON — nie wyciągamy do osobnego modułu

---

*Plan przygotowany: 2026-02-27*
