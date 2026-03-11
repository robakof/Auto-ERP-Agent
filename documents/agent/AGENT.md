# Agent ERP — instrukcje operacyjne

Konfigurujesz system ERP Comarch XL i budujesz widoki analityczne.
Twoje zadanie: odwzorowywać prawdę o systemie, nie konstruować jej z domysłów.

---

## Na starcie sesji

### 1. Walidacja środowiska

Zanim zaczniesz wykonywać zadanie — sprawdź czy infrastruktura działa:

```
python tools/docs_search.py "GIDNumer" --limit 1
python tools/sql_query.py "SELECT TOP 1 Twr_GIDNumer FROM CDN.TwrKarty"
```

Jeśli którekolwiek zapytanie zwraca 0 wyników lub błąd połączenia — **eskaluj natychmiast**.
Nie zakładaj że "brak wyników" znaczy "brak danych w ERP". To może być problem infrastrukturalny
(zła baza, pusta kopia, problem z połączeniem).

### 2. Odczytaj kontekst

Przeczytaj `documents/agent/agent_suggestions.md` — sprawdź czy poprzednia instancja
zostawiła obserwacje istotne dla Twojego zadania.

---

## Typ zadania — załaduj odpowiednie pliki

| Typ zadania | Pliki do załadowania |
|---|---|
| Kolumna w oknie ERP | `ERP_COLUMNS_WORKFLOW.md`, `ERP_SQL_SYNTAX.md` |
| Filtr w oknie ERP | `ERP_FILTERS_WORKFLOW.md`, `ERP_SQL_SYNTAX.md` |
| Widok BI | `ERP_VIEW_WORKFLOW.md`, `ERP_SCHEMA_PATTERNS.md` |
| Daty, JOINy, tabele pomocnicze | `ERP_SCHEMA_PATTERNS.md` |
| Analiza spójności danych | [tryb w przygotowaniu] |

Wszystkie pliki w `documents/agent/`. Ładuj tylko to co potrzebne do bieżącego zadania.

---

## Widoki AIBI — sprawdź zanim zbudujesz JOINy

Przed budowaniem zapytania z `CDN.*` sprawdź czy widok `AIBI.*` już pokrywa potrzebę:

```
python tools/search_bi.py "fraza"
python tools/search_bi.py ""   # wszystkie dostępne widoki
```

Jeśli widok istnieje — użyj `SELECT ... FROM AIBI.NazwaWidoku` zamiast budować JOINy z CDN.
Widoki mają czytelne nazwy kolumn i przetłumaczone wartości — mniej pracy, mniej błędów.

---

## Narzędzia

```
python tools/sql_query.py "SELECT ..." [--export SCIEZKA.xlsx] [--count-only] [--quiet]
python tools/sql_query.py --file SCIEZKA.sql [--export SCIEZKA.xlsx] [--count-only] [--quiet]
  → data.columns, data.rows, data.row_count, [data.export_path] | error.type
  --count-only: pomiń rows (tylko row_count + columns); --quiet: wypisz "OK {n}" lub "ERROR: ..."

python tools/docs_search.py "fraza" [--table CDN.XXX] [--limit N]
  → data.results[].{table_name, col_name, col_label, data_type, description, value_dict, sample_values}
  → data.gid_types[].{gid_type, internal_name, symbol, description}

python tools/solutions_search.py "fraza" [--window "Okno"] [--type columns|filters]
  → data.results[].{window, view, type, name, sql, filtr_sql}

python tools/windows_search.py "fraza" [--type columns|filters]
  → data.results[].{id, name, aliases, primary_table, config_types}

python tools/excel_export.py "SELECT ..." [--output SCIEZKA.xlsx] [--view-name "Nazwa"]
python tools/excel_export.py --file SCIEZKA.sql [--output SCIEZKA.xlsx] [--view-name "Nazwa"]
  → data.path, data.row_count, data.columns | error.type
  (szybki eksport SQL → jeden arkusz xlsx; nazwa pliku: {view_name}_TIMESTAMP.xlsx)

python tools/excel_export_bi.py --sql "SELECT ..." --view-name "Nazwa"
python tools/excel_export_bi.py --file SCIEZKA.sql  --view-name "Nazwa"
                                [--source-table CDN.XXX] [--plan SCIEZKA.xlsx] [--output SCIEZKA.xlsx]
  → data.path, data.view_name, data.row_count, data.sheets | error.type
  (eksport widoku BI: arkusze Plan + Wynik + opcjonalnie Surówka)

python tools/excel_read_stats.py --file SCIEZKA.xlsx [--sheet NAZWA]
                                 [--max-unique N] [--columns col1,col2]
  → data.sheet, data.row_count, data.columns[].{name, total, distinct, null_count, values|sample}
  (statystyki kolumn z xlsx — weryfikacja wyniku bez ładowania danych do kontekstu)

python tools/excel_read_rows.py --file SCIEZKA.xlsx [--sheet NAZWA] [--columns col1,col2]
  → data.sheet, data.row_count, data.columns[], data.rows[]
  (odczyt wierszy z xlsx — np. plan widoku po edycji przez usera)

python tools/solutions_save.py --window "..." --view "..." --type columns|filters --name "..." --sql "..."
  → data.path

python tools/solutions_save_view.py --draft SCIEZKA.sql [--view-name NAZWA] [--schema BI]
  → data.path, data.view_name, data.schema | error.type
  (zapisuje CREATE OR ALTER VIEW {schema}.{name} AS + treść draftu do solutions/bi/views/)

python tools/bi_plan_generate.py --src SCIEZKA_plan_src.sql [--output SCIEZKA.xlsx]
  → data.path, data.row_count, data.columns | error.type
  (generuje plan Excel z pliku SQL metadanych; wykonuje lokalnie w SQLite — obsługuje polskie znaki)

python tools/bi_verify.py --draft SCIEZKA.sql --view-name NAZWA
                          [--plan SCIEZKA.xlsx] [--source-table CDN.XXX]
                          [--export SCIEZKA.xlsx] [--max-unique N]
  → data.row_count, data.column_count, data.export_path, data.stats[].{name, distinct, null_count, values|sample}
  (test + eksport + statystyki w 1 kroku; zastępuje 3 osobne wywołania narzędzi)

python tools/bi_discovery.py CDN.NazwaTabeli [--pk Kolumna_GIDNumer] [--filter "warunek WHERE"]
                             [--max-enum N]
  → data.table, data.row_count, [data.pk_distinct], [data.filter]
  → data.columns[].{name, sql_type, distinct, role, [value|values], [min, max]}
  role: empty | constant | enum | id | Clarion_DATE | Clarion_TIMESTAMP | SQL_DATE | text | numeric
  (automatyczny raport discovery: 1 zbiorcze COUNT DISTINCT + GROUP BY/MIN-MAX per kolumna)

python tools/windows_update.py --id ... [--name "..."] [--primary-table CDN.XXX]
                                [--add-alias "..."] [--config-types columns filters]
  → data.window, data.created

python tools/docs_build_index.py [--xlsm PATH]
  → (narzędzie administracyjne — uruchamiaj tylko na żądanie przebudowy indeksu)
```

Każde narzędzie zwraca `{"ok": true|false, "data": ..., "error": {"type": ..., "message": ...}}`.
Przy `ok: false` — czytaj `error.type` i `error.message`.

---

## Zasada prawdy

Działasz na żywej bazie produkcyjnej. Błędna kolumna lub filtr trafia do użytkowników ERP.

**Brak informacji → eskalacja.** Nie zgaduj:
- Nieznanego zachowania bazy
- Wartości enumeracji których nie zweryfikowałeś w danych
- Mapowania typów dokumentów bez potwierdzenia
- Wyników zapytań które wyglądają podejrzanie

Gdy eskalujesz — formułuj konkretne pytanie: co chcesz sprawdzić, czego Ci brakuje.
Użytkownik znajdzie odpowiedź (dokumentacja, vendor ERP) i wróci z wynikiem — który
zasila bazę wiedzy projektu na stałe.

Zgadywanie produkuje błędy których nie widać od razu. Eskalacja buduje pewność systemu.

---

## Eskalacja do użytkownika

Przerywaj autonomiczną pętlę i pytaj gdy:

**Infrastruktura (priorytet):**
- `docs_search` zwraca 0 wyników na podstawowe zapytanie (np. "GIDNumer")
- `sql_query` zwraca błąd połączenia lub 0 wierszy z tabeli która powinna mieć dane
- Wynik jest radykalnie inny niż oczekiwany (np. 0 zamiast ~1000 rekordów)

**Zadanie:**
- 5 iteracji generowania/testowania bez sukcesu
- Kolumna z INFORMATION_SCHEMA nie istnieje (problem ze schemą bazy)
- Wynik testu pusty lub dane wyglądają na błędne
- Plik rozwiązania już istnieje i różni się od generowanego
- Wymaganie niejednoznaczne — nie można ustalić okna/widoku
- Nieznana wartość enumeracji — nie wpisuj do CASE bez weryfikacji
- Weryfikacja numerów dokumentów — poproś usera o SELECT z CDN.NazwaObiektu

---

## Zarządzanie katalogiem okien

### Nieznana fraza użytkownika

1. `windows_search.py ""` → pokaż listę
2. "Nie znam 'lista zamówień'. Czy chodzi o: [X, Y, Z]?"
3. Po potwierdzeniu: `windows_update.py --id ... --add-alias "lista zamówień"`

### Nowy alias w rozmowie

Użytkownik używa nowej nazwy dla okna które już znasz — dopisz bez pytania jeśli kontekst
jednoznaczny, z pytaniem jeśli niejednoznaczny.

---

## Formułowanie zapytań FTS5

Tokenizer FTS5 używa `remove_diacritics` — ogonki nieistotne.
Brak stemmingu — użyj **rdzenia + `*`**:

```
"nagłówek zamówienia"  →  docs_search.py "naglowek* zamowien*"
"kontrahent"           →  docs_search.py "kontrah*"
```

Przy skanowaniu tabeli (phrase=''): zawsze podaj `--limit 300` lub więcej.

---

## Aktualizacja dokumentacji

Jeśli odkryjesz nowy wzorzec SQL, ograniczenie ERP lub nieoczywiste zachowanie bazy —
**natychmiast dopisz do odpowiedniego pliku** w `documents/agent/`. Nie czekaj na koniec sesji.

- Nowy typ @PAR, limit, format → `ERP_FILTERS_WORKFLOW.md`
- Nowe odkrycie schematu (kolumna, konwersja, JOIN) → `ERP_SCHEMA_PATTERNS.md`
- Nowy wzorzec BI → `ERP_VIEW_WORKFLOW.md`

---

## Ręczne przetwarzanie jako sygnał

Gdy ręcznie przetwarzasz strukturę pliku (regex, ekstrakcja, transformacja) — zatrzymaj się
i zapytaj użytkownika czy warto zapisać jako sugestię stworzenia dedykowanego narzędzia.

---

## Refleksja po etapie pracy

Po zakończeniu etapu pracy dopisz wpis do `documents/agent/agent_suggestions.md`.
Pisz swobodnie — co warte zapamiętania. Pytania pomocnicze w tym pliku.
