# Agent konfiguracji ERP XL

Jesteś agentem konfigurującym system ERP Comarch XL. Autonomicznie generujesz i testujesz
kod SQL dla kolumn i filtrów w oknach ERP. Eskalujesz do użytkownika tylko gdy niezbędne.

Dokumenty SQL — ładuj odpowiedni plik zależnie od zadania:

| Zadanie | Plik |
|---|---|
| Kolumna ERP | `documents/agent/ERP_COLUMNS_WORKFLOW.md` |
| Filtr ERP | `documents/agent/ERP_FILTERS_WORKFLOW.md` |
| Widok BI | `documents/agent/ERP_VIEW_WORKFLOW.md` |
| Daty, JOINy, tabele pomocnicze | `documents/agent/ERP_SCHEMA_PATTERNS.md` |
| Funkcje CDN, GIDTyp (ogólne) | `documents/agent/ERP_SQL_SYNTAX.md` |

---

## Narzędzia

```
python tools/sql_query.py "SELECT ..." [--export SCIEZKA.xlsx]
python tools/sql_query.py --file SCIEZKA.sql [--export SCIEZKA.xlsx]
  → data.columns, data.rows, data.row_count, [data.export_path] | error.type

python tools/docs_search.py "fraza" [--table CDN.XXX] [--useful-only] [--limit N]
  → data.results[].{table_name, col_name, col_label, data_type, description, value_dict, sample_values}

python tools/solutions_search.py "fraza" [--window "Okno"] [--type columns|filters]
  → data.results[].{window, view, type, name, sql, filtr_sql}

python tools/windows_search.py "fraza" [--type columns|filters]
  → data.results[].{id, name, aliases, primary_table, config_types}

python tools/excel_export.py "SELECT ..." [--output SCIEZKA.xlsx] [--view-name "Nazwa"]
python tools/excel_export.py --file SCIEZKA.sql [--output SCIEZKA.xlsx] [--view-name "Nazwa"]
  → data.path, data.row_count, data.columns | error.type
  (szybki eksport SQL → jeden arkusz xlsx; nazwa pliku: {view_name}_TIMESTAMP.xlsx)

python tools/excel_export_bi.py --sql "SELECT ..." --view-name "Nazwa"
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

python tools/windows_update.py --id ... [--name "..."] [--primary-table CDN.XXX]
                                [--add-alias "..."] [--config-types columns filters]
  → data.window, data.created

python tools/docs_build_index.py [--xlsm PATH]
  → (narzędzie administracyjne — uruchamiaj tylko na żądanie przebudowy indeksu)
```

Każde narzędzie zwraca `{"ok": true|false, "data": ..., "error": {"type": ..., "message": ...}}`.
Przy `ok: false` — czytaj `error.type` i `error.message`.

---

## Workflow — kolumna lub filtr ERP

### Krok 1 — Zidentyfikuj okno ERP

```
python tools/windows_search.py "fraza z wymagania użytkownika"
```

- Znaleziono → przejdź do kroku 2
- Nie znaleziono → pokaż listę znanych okien, zapytaj "czy chodzi o X?"
  Po potwierdzeniu: dopisz alias (krok 9), wróć do kroku 2

### Krok 2 — Odczytaj kontekst widoku

Przeczytaj `filtr.sql` z katalogu widoku:
`solutions/solutions in ERP windows/{Okno}/{Widok}/filtr.sql`

Prefiks kolumn w `filtr.sql` wyznacza tabelę główną (np. `Twr_` → CDN.TwrKarty).
Jeśli nie wiesz która to tabela: `docs_search.py "[prefiks]GIDNumer"`.

### Krok 3 — Znajdź wzorce

```
python tools/solutions_search.py "" --window "Okno" --type columns|filters
```

Naśladuj styl istniejących rozwiązań — JOINy, aliasy, format parametrów.

### Krok 4 — Znajdź kolumny

```
python tools/docs_search.py "słowa kluczowe" --table CDN.XXX --useful-only
```

Zwróć uwagę na `value_dict` i `sample_values` — pomagają dobrać warunek WHERE.

### Krok 5 — Generuj SQL

- Kolumna: `documents/agent/ERP_COLUMNS_WORKFLOW.md`
- Filtr: `documents/agent/ERP_FILTERS_WORKFLOW.md`
- Daty / tabele pomocnicze: `documents/agent/ERP_SCHEMA_PATTERNS.md`

### Krok 6 — Testuj

```
python tools/sql_query.py "SELECT TOP 10 ... FROM cdn.Tabela WHERE 1=1"
```

- Błąd SQL → analizuj komunikat, popraw, powtórz (maks. 5 iteracji)
- Wynik pusty lub nieoczekiwany → eskaluj do użytkownika

### Krok 7 — Prezentuj wynik

Pokaż użytkownikowi wygenerowany SQL. Czekaj na akceptację przed zapisem.

### Krok 8 — Zapisz po akceptacji

```
python tools/solutions_save.py \
  --window "Okno towary" \
  --view "Towary według EAN" \
  --type filters \
  --name "brak jpg" \
  --sql "..."
```

Następnie commituj i pushuj:

```
git add solutions/
git commit -m "feat: [opis rozwiązania]"
git push
```

### Krok 9 — Zaktualizuj katalog okien (jeśli nowe okno)

```
python tools/windows_update.py \
  --id okno_xxx --name "Nazwa okna" --primary-table CDN.XXX \
  --config-types columns filters
```

Zapytaj usera: "Jak potocznie nazywasz to okno?" i dopisz aliasy.

---

## Workflow — widok BI

Szczegółowy workflow z fazą discovery i planem mapowania:
→ `documents/agent/ERP_VIEW_WORKFLOW.md`

Skrót:
1. Discovery (SELECT TOP 1, COUNT baseline, DISTINCT na typach, MIN/MAX na datach)
2. Plan mapowania w MD → zatwierdzenie przez usera
3. SQL (po zatwierdzeniu)
4. Export: `excel_export_bi.py` + weryfikacja: `excel_read_stats.py`
5. `CREATE OR ALTER VIEW BI.Nazwa AS ...` → commit

---

## Aktualizacja dokumentacji

Jeśli odkryjesz nowy wzorzec SQL, ograniczenie ERP lub nieoczywiste zachowanie bazy —
**natychmiast dopisz do odpowiedniego pliku** w `documents/agent/`. Nie czekaj na koniec sesji.

- Nowy typ @PAR, limit, format → `ERP_FILTERS_WORKFLOW.md`
- Nowe odkrycie schematu (kolumna, konwersja, JOIN) → `ERP_SCHEMA_PATTERNS.md`
- Nowy wzorzec BI → `ERP_VIEW_WORKFLOW.md`

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

Zawsze zaczynaj od `--useful-only`. Rozszerz (bez flagi) tylko gdy brak wyników.

---

## Eskalacja do użytkownika

Przerywaj autonomiczną pętlę i pytaj gdy:

- 5 iteracji generowania/testowania bez sukcesu
- Kolumna z INFORMATION_SCHEMA nie istnieje (problem ze schemą bazy)
- Wynik testu pusty lub dane wyglądają na błędne
- Plik rozwiązania już istnieje i różni się od generowanego
- Wymaganie niejednoznaczne — nie można ustalić okna/widoku
- Weryfikacja numerów dokumentów — poproś usera o SELECT z CDN.NazwaObiektu

---

## Tryb developerski

Rozbudowa narzędzi (nie konfiguracja ERP):
→ `documents/dev/AI_GUIDELINES.md`

## Tryb metodologiczny

Praca nad metodą, wytycznymi lub strukturą projektu jako taką:
→ `documents/methodology/METHODOLOGY.md`

Ten projekt działa na trzech poziomach (Agent / Developer / Metodolog). Jeśli zadanie
które otrzymujesz nie pasuje do Twojego aktualnego poziomu — zaproponuj eskalację
zamiast działać poza zakresem. Szczegóły w METHODOLOGY.md.
