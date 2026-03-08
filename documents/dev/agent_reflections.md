# Refleksje nad pracą agenta

Plik roboczy — obserwacje i propozycje usprawnień zbierane w trakcie sesji.
Plik zawiera tylko pozycje **niezrealizowane**. Zrealizowane — w sekcji Archiwum na końcu.

---

## [Narzędzia] Propozycja: bi_discovery.py — automatyczny raport discovery

**Źródło:** agent (self-reflection) | **Sesja:** 2026-03-08

Faza discovery widoku BI to zawsze te same ~10 zapytań: TOP 1, COUNT baseline,
COUNT DISTINCT per kolumna, MIN/MAX na datach, GROUP BY na enumeracjach.

**Propozycja:**
```
python tools/bi_discovery.py CDN.NazwaTabeli [--pk Kolumna_GIDNumer] [--filter "warunek"]
```
Zwraca raport: baseline COUNT, pola stałe (COUNT DISTINCT = 1), klasyfikacja dat
(Clarion_DATE / Clarion_TIMESTAMP / SQL_DATE), enumeracje z listą wartości.

---

## [Architektura] Sygnatury narzędzi powielone w wielu miejscach

**Źródło:** user + developer | **Sesja:** 2026-03-08

Nazwy i sygnatury narzędzi zapisane w CLAUDE.md, ERP_VIEW_WORKFLOW.md,
ERP_COLUMNS_WORKFLOW.md, ERP_FILTERS_WORKFLOW.md i docstringach tools/*.py.
Po każdym rename trzeba ręcznie aktualizować wszystkie miejsca.

**Opcje:**
1. Generowanie sekcji Narzędzia w CLAUDE.md ze skryptów (docstring → gen_docs.py)
2. Jeden plik referencyjny `documents/agent/TOOLS.md` + dyscyplina aktualizacji
3. Test CI sprawdzający czy narzędzia w CLAUDE.md istnieją jako pliki w `tools/`

Opcja 3 najtańsza. Opcja 1 eliminuje problem u źródła.

---

---

# Archiwum — zrealizowane

## ✓ [Bugi] SqlClient — średnik w stringu + komentarze SQL
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
`_split_statements()`: iteracja po znakach z flagą in_string, obsługa `''`.
`_strip_comments()`: usuwa linie `--` przed walidacją. 187 testów.

## ✓ [Bugi] docs_search + wszystkie toolsy — encoding cp1250
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
`tools/lib/output.py`: `print_json()` z `sys.stdout.reconfigure(encoding='utf-8')`.
Zamieniono we wszystkich 10 toolsach. 191 testów.

## ✓ [Bezpieczeństwo] Komendy powłoki + Edit zamiast Read
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
`AI_GUIDELINES.md` sekcja 2: reguły Bash (zakaz `$()`, `python -c`, maks. 2 `&&`)
+ reguła Edit z minimalnym kontekstem zamiast Read całego pliku SQL.

## ✓ [Narzędzia] Nieoczywiste nazwy tabel — ERP_SCHEMA_PATTERNS.md
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
`ERP_SCHEMA_PATTERNS.md`: zasada `docs_search "[prefiks]GIDNumer"` + przykład OpeKarty.

## ✓ [Workflow] Auto-eksport Excel po każdej iteracji SQL
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
`sql_query.py --export` + reguła w ERP_VIEW_WORKFLOW.md (Faza 2).

## ✓ [Struktura] Pliki robocze widoku BI — jedna struktura per widok
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
`solutions/bi/{Widok}/` — wszystkie pliki widoku w jednym folderze.

## ✓ [Excel] Plan mapowania — Table object, nazwa arkusza, opis z col_label
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
ExcelWriter: Excel Table (styl Medium9), arkusz = nazwa widoku, opis z `col_label`.

## ✓ [SQL] Zapytanie CDN.NazwaObiektu — zapisywane do pliku
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
ERP_VIEW_WORKFLOW.md (Faza 0e): agent zapisuje do `{Widok}_objects.sql` przed wykonaniem.

## ✓ [Workflow] Plan mapowania — priorytetyzacja niespójności
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
ERP_VIEW_WORKFLOW.md (Faza 1): wykrywa niespójności przed SQL, zgłasza do rozstrzygnięcia.

## ✓ [Workflow] Agent używał błędnych nazw narzędzi
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
Poprawiono nazwy w dokumentach agenta i CLAUDE.md (~20 miejsc).

## ✓ [Workflow] Weryfikacja numerów dokumentów — dwuetapowa
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
ERP_VIEW_WORKFLOW.md (Faza 0e): krok 1 DISTINCT podtypów, krok 2 NazwaObiektu per podtyp.

## ✓ [Narzędzia] Mapa GIDTyp → tabela CDN — e_typy.html do indeksu
Sesja: 2026-03-08 | Wdrożone: 2026-03-08
`docs_build_index.py`: parsowanie `e_typy.html` (456 typów) → tabela `gid_types` + `gid_types_fts` w docs.db.
`docs_search.py`: `_search_gid_types()` + `data.gid_types[]` w odpowiedzi. 202 testy.
