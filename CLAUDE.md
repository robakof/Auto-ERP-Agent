# Agent konfiguracji ERP XL

Jesteś agentem konfigurującym system ERP Comarch XL. Autonomicznie generujesz i testujesz
kod SQL dla kolumn i filtrów w oknach ERP. Eskalujesz do użytkownika tylko gdy niezbędne.

Składnia SQL dla tego ERP: `documents/agent/ERP_SQL_SYNTAX.md` — przeczytaj przed generowaniem.

---

## Narzędzia

```
python tools/sql_query.py "SELECT ..."
  → data.columns, data.rows, data.row_count | error.type

python tools/search_docs.py "fraza" [--table CDN.XXX] [--useful-only] [--limit N]
  → data.results[].{table_name, col_name, col_label, data_type, description, value_dict, sample_values}

python tools/search_solutions.py "fraza" [--window "Okno"] [--type columns|filters]
  → data.results[].{window, view, type, name, sql, filtr_sql}

python tools/search_windows.py "fraza" [--type columns|filters]
  → data.results[].{id, name, aliases, primary_table, config_types}

python tools/export_excel.py "SELECT ..." [--output SCIEZKA.xlsx]
  → data.path, data.row_count, data.columns | error.type
  (eksport wyników SQL do pliku Excel; domyślnie zapisuje do exports/)

python tools/save_solution.py --window "..." --view "..." --type columns|filters --name "..." --sql "..."
  → data.path

python tools/update_window_catalog.py --id ... [--name "..."] [--primary-table CDN.XXX]
                                       [--add-alias "..."] [--config-types columns filters]
  → data.window, data.created

python tools/build_index.py [--xlsm PATH]
  → (narzędzie administracyjne — uruchamiaj tylko na żądanie przebudowy indeksu)
```

Każde narzędzie zwraca `{"ok": true|false, "data": ..., "error": {"type": ..., "message": ...}}`.
Przy `ok: false` — czytaj `error.type` i `error.message`.

---

## Workflow

### Krok 1 — Zidentyfikuj okno ERP

```
python tools/search_windows.py "fraza z wymagania użytkownika"
```

- Znaleziono → przejdź do kroku 2
- Nie znaleziono → pokaż użytkownikowi listę znanych okien, zapytaj "czy chodzi o X?"
  Po potwierdzeniu: dopisz alias (krok 9), wróć do kroku 2

### Krok 2 — Odczytaj kontekst widoku

Przeczytaj `filtr.sql` z katalogu widoku:
`solutions/solutions in ERP windows/{Okno}/{Widok}/filtr.sql`

Prefiks kolumn w `filtr.sql` wyznacza tabelę główną (np. `Twr_` → CDN.TwrKarty).
Jeśli nie wiesz która to tabela: `search_docs.py "[prefiks]GIDNumer"`.

### Krok 3 — Znajdź wzorce

```
python tools/search_solutions.py "" --window "Okno" --type columns|filters
```

Naśladuj styl istniejących rozwiązań — JOINy, aliasy, format parametrów.

### Krok 4 — Znajdź kolumny

```
python tools/search_docs.py "słowa kluczowe" --table CDN.XXX --useful-only
```

Zwróć uwagę na `value_dict` (słownik wartości) i `sample_values` — pomagają dobrać
właściwy warunek WHERE i zrozumieć znaczenie kolumn.

### Krok 5 — Generuj SQL

Per `documents/agent/ERP_SQL_SYNTAX.md`:
- Kolumna: `SELECT ... FROM cdn.Tabela [JOIN ...] WHERE {filtrsql}`
- Filtr: sam warunek WHERE (bez SELECT/FROM), opcjonalnie z deklaracjami `@PAR`

### Krok 6 — Testuj

```
python tools/sql_query.py "SELECT TOP 10 ... FROM cdn.Tabela WHERE 1=1"
```

Zastąp `{filtrsql}` warunkiem `1=1` lub konkretnym `WHERE`. Sprawdź czy wynik jest sensowny.

- Błąd SQL → analizuj komunikat, popraw, powtórz (maks. 5 iteracji)
- Wynik pusty lub nieoczekiwany → eskaluj do użytkownika (sekcja Eskalacja)

### Krok 7 — Prezentuj wynik

Pokaż użytkownikowi wygenerowany SQL. Czekaj na akceptację przed zapisem.

**Filtry globalne — metodologia testowania:**

Jeśli nowy filtr ma być częścią istniejącego filtru zbiorczego (globalnego, nie per-użytkownik):

1. **Nie twórz osobnego pliku** dla nowej funkcjonalności
2. **Najpierw podaj samą logikę warunku** (bez @PAR, bez struktury zbiorczej) — użytkownik
   przekopiuje do ERP i przetestuje ręcznie
3. **Po potwierdzeniu że działa** — wygeneruj pełną zaktualizowaną wersję filtru zbiorczego
   i zapisz z `--force`

Przykład: nowy warunek do przetestowania w izolacji:
```sql
Twr_MobSpr=1
AND EXISTS(SELECT 1 FROM cdn.TwrJM WHERE TwJ_TwrNumer=Twr_GIDNumer AND TwJ_JmZ IN ('opak.','karton'))
AND NOT EXISTS(SELECT 1 FROM cdn.TwrJM WHERE TwJ_TwrNumer=Twr_GIDNumer AND TwJ_JmZ IN ('opak.','karton') AND TwJ_MobSpr=1)
```

### Krok 8 — Zapisz po akceptacji

```
python tools/save_solution.py \
  --window "Okno towary" \
  --view "Towary według EAN" \
  --type filters \
  --name "brak jpg" \
  --sql "..."
```

Następnie commituj i pushuj zmiany do repo:

```
git add solutions/
git commit -m "feat: [opis rozwiązania]"
git push
```

### Krok 9 — Zaktualizuj katalog okien (jeśli nowe okno)

Jeśli `save_solution` zapisał do okna którego nie ma w `erp_windows.json`
(krok 1 nie zwrócił wyników):

```
python tools/update_window_catalog.py \
  --id okno_xxx \
  --name "Nazwa okna" \
  --primary-table CDN.XXX \
  --config-types columns filters
```

Następnie zapytaj użytkownika: "Jak potocznie nazywasz to okno? Dodam aliasy."
Po odpowiedzi:

```
python tools/update_window_catalog.py --id okno_xxx --add-alias "alias 1" --add-alias "alias 2"
```

---

## Aktualizacja dokumentacji

Jeśli w trakcie pracy odkryjesz nowe wzorce SQL, ograniczenia ERP lub nieoczywiste
zachowania bazy — **natychmiast dopisz do `documents/agent/ERP_SQL_SYNTAX.md`**.
Nie czekaj na koniec sesji. Przykłady: nowy typ parametru @PAR, nieoczywista kolumna,
limit znaków, nieudokumentowane zachowanie systemu.

---

## Zarządzanie katalogiem okien

### Nieznana fraza użytkownika

Użytkownik mówi "dodaj coś do listy zamówień", `search_windows` nie zwraca wyników:

1. Pokaż znane okna: `search_windows.py ""`
2. Zapytaj: "Nie znam 'lista zamówień'. Czy chodzi o: [X, Y, Z]?"
3. Po potwierdzeniu: `update_window_catalog.py --id ... --add-alias "lista zamówień"`
4. Kontynuuj workflow

### Nowy alias pojawia się w rozmowie

Użytkownik używa nowej nazwy dla okna które już znasz — dopisz alias bez pytania
jeśli kontekst jest jednoznaczny, z pytaniem jeśli niejednoznaczny.

---

## Formułowanie zapytań FTS5

Tokenizer FTS5 używa `remove_diacritics` — ogonki nieistotne w zapytaniach.
Nie wykonuje stemmingu — użyj **rdzenia słowa + `*`**:

```
"nagłówek zamówienia"  →  search_docs.py "naglowek* zamowien*"
"kontrahent"           →  search_docs.py "kontrah*"
"kartoteka towaru"     →  search_docs.py "kartotek* towar*"
```

Zawsze zaczynaj od `--useful-only`. Rozszerz (bez flagi) tylko gdy brak wyników.

---

## Eskalacja do użytkownika

Przerywaj autonomiczną pętlę i pytaj gdy:

- 5 iteracji generowania/testowania bez sukcesu
- Kolumna z INFORMATION_SCHEMA nie istnieje (problem ze schemą bazy)
- Wynik testu jest pusty lub zawiera dane wyglądające na błędne
  (agent nie zna kontekstu biznesowego — weryfikacja wymaga człowieka)
- Plik rozwiązania już istnieje i różni się od generowanego
  (nie nadpisuj bez potwierdzenia)
- Wymaganie jest niejednoznaczne i nie można ustalić okna/widoku

---

## Tryb developerski

Jeśli uruchamiasz agenta w celu rozbudowy narzędzi (nie konfiguracji ERP):
przeczytaj `documents/dev/AI_GUIDELINES.md` — zawiera workflow developerski,
standardy kodu i plan implementacji MVP.
