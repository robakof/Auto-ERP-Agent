# Progress Log

## Status projektu: Inicjalizacja

---

### 2026-02-26 — Inicjalizacja projektu

- Utworzono PRD.md
- Skonfigurowano AI_GUIDELINES.md (dostosowany do kontekstu projektu)
- Utworzono strukturę folderów projektu
- Utworzono README.md

**Kolejny krok:** Weryfikacja dokumentacji przez użytkownika, potem EXPERIMENTS_PLAN.md i IMPLEMENTATION_PLAN.md

---

### 2026-02-26 — TECHSTACK.md

- Zapoznano się ze strukturą dokumentacji: plik `.xlsm` (12 arkuszy, ~90k wierszy łącznie) + tysiące plików HTML
- Uzgodniono stack: Claude Code + MCP, pyodbc, openpyxl → SQLite FTS5, pliki .sql + index.json
- Utworzono TECHSTACK.md

### 2026-02-26 — ARCHITECTURE.md i CLAUDE.md

- Uzgodniono Model A (skrypty CLI) dla narzędzi MCP
- Uzgodniono model współdzielonego folderu sieciowego (solutions/, erp_docs/, erp_windows.json)
- Zaprojektowano katalog okien ERP (erp_windows.json) + narzędzie search_windows.py
- Zaprojektowano 4-warstwową strategię nawigacji po tabelach (okno → własne nazwy → słowniki → żywa baza)
- Utworzono ARCHITECTURE.md i CLAUDE.md
- Status: dokumentacja przekazana do weryfikacji

### 2026-02-26 — Rewizja ARCHITECTURE.md po code review

Uwzględniono 3 z 8 punktów recenzji (priorytet przed eksperymentami):
- Baza rozwiązań: jeden plik .json per rozwiązanie zamiast centralnego index.json (eliminacja race condition)
- Bezpieczeństwo sql_query.py: 3 warstwy (read-only DB user, blokada DML/EXEC, TOP 100 + timeout)
- Kontrakty JSON: zdefiniowano schemat wyjścia dla wszystkich 5 narzędzi

**Kolejny krok:** Wykonanie eksperymentów z EXPERIMENTS_PLAN.md, następnie IMPLEMENTATION_PLAN.md

### 2026-02-26 — Repo Git + EXPERIMENTS_PLAN.md

- Zainicjalizowano repo Git, wypchnięto na GitHub (CyperCyper/Auto-ERP-Agent)
- Utworzono EXPERIMENTS_PLAN.md — 5 eksperymentów (pyodbc, xlsm parsing, FTS5, MCP tool, format ERP)
- Kolejność: E-01 blokujący; E-02 i E-04 równolegle; E-03 po E-02; E-05 wymaga dostępu do ERP

### 2026-02-27 — Eksperymenty E-01 do E-03 zakończone

- E-01 SUKCES: pyodbc działa, CEiM_Reader read-only potwierdzone, 1403 tabele widoczne
- E-02 SUKCES: openpyxl data_only=True zwraca wartości (0% formuł), header Kolumny na wierszu 5
- E-04 SUKCES: SELECT+JSON, TOP 100, blokada DML, output 90KB — wszystko OK
- E-03 SUKCES: FTS5 działa z unicode61 remove_diacritics=2 + prefix matching (kontrah* zamow*)
  - Wniosek: agent musi budować zapytania jako rdzeń+* nie pełne formy
  - Wniosek: własne nazwy z Excela krytyczne — bez nich wyniki słabe
  - Zaktualizowano ARCHITECTURE.md o strategię formułowania zapytań

### 2026-02-27 — E-05 + rewizja struktury solutions/

- E-05 SUKCES: format SQL odkryty z przykładów w solutions/
  - Kolumny: SELECT z aliasami [NAZWA] + JOINy + placeholder {filtrsql}
  - Filtry: sam warunek WHERE + opcjonalny system @PAR (typy S/D/R)
  - filtr.sql = kotwica widoku (główny filtr kontekstu)
- Odkryto faktyczną strukturę solutions/ (hierarchia: Okno > Widok > columns/filters)
  — inna niż pierwotnie zakładana (płaska)
- search_solutions.py będzie odkrywać pliki przez traversal katalogów, metadane z ścieżki
- Zaktualizowano ARCHITECTURE.md

**Wszystkie eksperymenty zakończone.**

### 2026-02-27 — ERP_SQL_SYNTAX.md + IMPLEMENTATION_PLAN.md

- Utworzono ERP_SQL_SYNTAX.md — składnia kolumn, filtrów, parametrów @PAR (S/D/R), konwersja dat
- Utworzono IMPLEMENTATION_PLAN.md — 5 kamieni milowych: tools/, erp_windows.json, CLAUDE.md, MVP test, deployment
- Zaktualizowano CLAUDE.md o referencje do nowych dokumentów

- Zmieniono nazwę IMPLEMENTATION_PLAN.md → MVP_IMPLEMENTATION_PLAN.md
- Zaktualizowano przypadek testowy MVP: filtr "brak załączników .jpg" w Towary według EAN
- Zaktualizowano CLAUDE.md o referencje do ERP_SQL_SYNTAX.md i MVP_IMPLEMENTATION_PLAN.md

**Kolejny krok: Implementacja — Kamień milowy 1 (tools/)**
**Status fazy: Phase 1 (Dokumentacja) i Phase 2 (Eksperymenty) — ZAKOŃCZONE**

---

### 2026-02-27 — Kamień milowy 1 ZAKOŃCZONY (tools/)

Zaimplementowano wszystkie 6 narzędzi CLI + moduł pomocniczy + testy:

| Moduł | Opis |
|-------|------|
| `sql_query.py` | SELECT na SQL Server, blokada DML, TOP 100, timeout, JSON |
| `db.py` | Shared SQLite connection helper |
| `build_index.py` | Parsowanie XLSM → SQLite FTS5 (Tabele/Kolumny/Relacje/Słownik/Przykładowe) |
| `search_docs.py` | FTS5 prefix matching, filtr --table/--useful-only |
| `search_solutions.py` | Traversal solutions/, filtr_sql z filtr.sql widoku w każdym wyniku |
| `search_windows.py` | Wyszukiwanie po nazwie/aliasie z erp_windows.json |
| `save_solution.py` | Zapis .sql do hierarchii solutions/, flaga --force |

Łącznie: 92 testy jednostkowe, wszystkie zielone. Zewnętrzne zależności mockowane.
Zaktualizowano `.env.example` o zmienną `XLSM_PATH`.

**Następny krok: Kamień milowy 2 — katalog okien ERP (erp_windows.json)**

---

### 2026-02-27 — Kamień milowy 2 ZAKOŃCZONY (erp_windows.json)

Utworzono `solutions/erp_windows.json` z pierwszym wpisem:

- Okno towary (`okno_towary`) — primary_table: CDN.TwrKarty
  related_tables: CDN.TwrGrupy, CDN.Atrybuty
  aliases: towary, kartoteki towarowe

Pokrywa oba istniejące widoki w solutions/ (Towary według EAN, Towary według grup).
search_windows.py działa poprawnie — wyszukiwanie po nazwie i aliasach.

Dodano `update_window_catalog.py` — agent zarządza erp_windows.json w całości:
upsert wpisów, dopisywanie aliasów z rozmowy (case-insensitive dedup).
Usunięto `related_tables` z schematu — redundantne, relacje są w docs.db.
13 nowych testów, łącznie 105 zielonych.

**Następny krok: Kamień milowy 3 — ERP_AGENT.md (instrukcje operacyjne agenta)**

---

### 2026-02-27 — Kamień milowy 3 ZAKOŃCZONY (ERP_AGENT.md)

Stworzono `ERP_AGENT.md` — instrukcje operacyjne dla agenta roboczego ERP.
Oddzielony od `CLAUDE.md` (agent deweloperski). Przy deploymencie (KM5)
kopiowany jako `CLAUDE.md` do folderu współdzielonego.

Zawartość: sygnatury 7 narzędzi, 9-krokowy workflow, zarządzanie katalogiem okien,
reguły FTS5, reguły eskalacji, pointer do ERP_SQL_SYNTAX.md.

**Następny krok: Kamień milowy 4 — MVP end-to-end**

---

### 2026-02-27 — Sesja robocza (refaktoryzacja + KM2 + KM3)

Dodatkowe zmiany poza kamieniami milowymi:

- Refaktoryzacja tools/: search_docs.py, search_solutions.py, save_solution.py
  (wyekstrahowanie funkcji pomocniczych, usunięcie zagnieżdżeń)
  Poprawka bugu: brak conn.close() przy pustej frazie w search_docs.py
- 105 testów, 100% zielonych

**Następny krok: Kamień milowy 4 — MVP end-to-end**
Przypadek testowy: "Dodaj filtr do Okna Towary/Towary według EAN który wskaże
kartoteki towarowe nie posiadające załączników w formacie .jpg"

---

### 2026-02-27 — Kamień milowy 4 ZAKOŃCZONY (MVP end-to-end)

Agent wykonał pełny cykl autonomicznie, pierwszy shot, zero iteracji:
- Zidentyfikował okno, odczytał filtr.sql, znalazł wzorce
- Samodzielnie przebudował pusty docs.db (build_index.py) bez eskalacji
- Odkrył łańcuch CDN.TwrKarty → CDN.DaneObiekty → CDN.DaneBinarne
- Wygenerował filtr NOT EXISTS z LOWER() i Twr_GIDTyp z kolumny
- Przetestował na żywej bazie, zapisał, zweryfikowany w ERP

Nowe rozwiązania w solutions/: brak jpg.sql + wyprzedane do archiwizacji.sql
(w obu widokach Towary według EAN i Towary według grup)

Znany bug: build_index.py exit code 1 przy polskich znakach w końcowym print
(dane ładują się poprawnie, błąd tylko w wyjściu).

**Następny krok: Kamień milowy 5 — Deployment**

---

### 2026-02-28 — Import kolumn z CDN.DefinicjeKolumn do solutions/

Odkryto tabelę CDN.DefinicjeKolumn — przechowuje kolumny SQL analogicznie do CDN.Filtry.
Kluczowe różnice: DFK_IDFormatki = FIL_ProcID (to samo ID okna), ale DFK_IDListy
ma inną numerację niż FIL_ListaID.

Ustalono mapowanie (IDFormatki, IDListy) → (okno, widok) przez analizę SQL + weryfikację w ERP.
Dodano import_columns.py — dedupl. po treści SQL (kolumny per-operator → jeden plik).

Zaimportowano 35 unikalnych kolumn SQL do solutions/:

| Okno | Widoki |
|------|--------|
| Okno kontrahenci | Grupy, Wg akronimu |
| Okno towary | Towary według EAN (+3), Towary według grup (+4) |
| Okno dokumenty | Handlowe (+8), Magazynowe (+2), Elementy (+5) |
| Okno historia towaru | Transakcje - Chronologicznie (+3) |
| Okno lista zamówień sprzedaży | Zamówienia (+4) |
| Okno zamówienie | Zamówienie (+2) |

Pominięto: zakresy 2900–2997 (duplikaty EAN per-formatka dokumentu),
okna nierozpoznane (2305/Retro, 2640/Samochody, 2760/Trasy, 8615/Memo, 30499).

ERP_SQL_SYNTAX.md — rozbudowana sekcja kolumn:
- {filtrsql} KRYTYCZNE — brak = ładowanie całej tabeli per wiersz (udokumentowane)
- Wzorce: AND {filtrsql}, GROUP BY po filtrsql, TOP 1 (1:N), aliasy tej samej tabeli
- Tabela mapowania DFK_IDListy ≠ FIL_ListaID dla tych samych okien
- Marża.sql dodana do sekcji znanych problemów (brak filtrsql)

**Następny krok: test generowania nowych kolumn przez agenta ERP**

---

### 2026-02-28 — Import filtrów z CDN.Filtry do solutions/

Odkryto strukturę tabeli CDN.Filtry: (FIL_ProcID, FIL_ListaID) = (okno, zakładka).
Zbudowano mapowanie ProcID → nazwa okna na podstawie analizy SQL + weryfikacji w ERP.

Zaimportowano 70 filtrów SQL do hierarchii solutions/:

| Okno | Widoki |
|------|--------|
| Okno kontrahenci | Grupy, Wg akronimu |
| Okno towary | Towary według EAN (+9 nowych), Towary według grup (+5 nowych) |
| Okno rejestr VAT | Rejestr VAT |
| Okno dokumenty | Handlowe (20), Magazynowe (4), Elementy (2) |
| Okno zapisy bankowe | Zapisy bankowe |
| Okno historia kontrahenta | Transakcje - Zbiorczo/Chronologicznie/Dla towaru |
| Okno historia towaru | Transakcje - Chronologicznie/Dla kontrahenta/Wg kontrahentow, Magazyn |
| Okno lista zamówień sprzedaży | Zamówienia |
| Okno zamówienie | Zamówienie |
| Okno dokument | Dokument |

Pominięto 20 filtrów bez mapowania (zakres 2900–2997: identyczne picki towarowe
w formatce dokumentu + 2 okna nieznane: 8503, 8615).

Dodano import_filters.py — narzędzie do ponownego importu z flagą --force.
Mapowanie w pliku: Mapowanie okien i filtrów.

---

### 2026-02-28 — erp_windows.json + ERP_SQL_SYNTAX.md po analizie filtrów

erp_windows.json: rozszerzony o 9 nowych okien (kontrahenci, dokumenty, rejestr VAT,
zapisy bankowe, historia kontrahenta, historia towaru, lista zamówień sprzedaży,
zamówienie, dokument).

ERP_SQL_SYNTAX.md — nowe wzorce z analizy 70 zaimportowanych filtrów:
- @O (opcje/radio), @n (numeryczny), @U() (uppercase), @RL/@RH (zakresy)
- cdn.NazwaObiektu(typ, numer, 0, 2) — funkcja nazwy dokumentu
- Daty w TraNag (TrN_Data2) = SQL date, nie Clarion
- Nowe tabele: TrNOpisy, ZaNOpisy, OpeKarty, TraPlat, ZamNag/ZamElem, Zapisy
- Prefiks Kontrahenci/Grupy: KnG_ (nie Knt_)
- 3 uszkodzone filtry zidentyfikowane (Wystawiający w Zamówieniach, Sezon Magazynowe, stary format Zapisy bankowe)

---

### 2026-03-01 — Kamień milowy 5 ZAKOŃCZONY (Deployment)

Model deploymentu: Git clone na każdej maszynie. Agent commituje zmiany lokalnie,
developer pushuje nowe funkcjonalności, inni git pull.

Zmiany:
- .gitignore: odblokowano erp_docs/index/ → docs.db trackowany w git
- erp_docs/index/docs.db (6.7 MB) dodany do repo — inni nie muszą uruchamiać build_index.py
- README.md: pełne przepisanie (stary opisywał architekturę sprzed KM1)
- INSTALL.md: instrukcja instalacji na nowej maszynie Windows (Git, Python, ODBC, Node.js, Claude Code, VS Code)
- .env.example: usunięto 4 zbędne zmienne (tools używają hardcoded defaults)

**Wszystkie 5 kamieni milowych MVP zakończone.**

---

### 2026-03-01 — Porządki w projekcie

- Usunięto: import_columns.py, import_filters.py, experiments/ (5 plików), solutions/index.json, changes_propositions.md, CHANGELOG.md
- Archiwum (documents/dev/archive/): EXPERIMENTS_PLAN.md, MVP_IMPLEMENTATION_PLAN.md, ARCHITECTURE_REVIEW.md, session_26_02.md
- Dodano: verify.py — skrypt weryfikacji instalacji (3 testy: docs.db, solutions/, SQL Server)
- INSTALL.md: zastąpiono experiments/ przez verify.py jako krok weryfikacji
- Naprawiono nazwy plików w solutions/: filr.sql, brakujące .sql, podwójna kropka

**Następny krok: praca bieżąca — rozbudowa bazy rozwiązań, nowe okna ERP**

---

### 2026-03-04 — tools/export_excel.py + rozbudowa ERP_SQL_SYNTAX.md

**tools/export_excel.py** (nowe narzędzie agenta):
- SQL → .xlsx: guardrails identyczne z sql_query.py (blokada DML, TOP 1000 default)
- Auto-timestamp w nazwie pliku gdy brak `--output`
- Formatowanie: bold header, frozen row 1, auto-szerokość kolumn (max 50 zn.)
- 21 testów jednostkowych, wszystkie zielone (łącznie 126)
- Dodano do CLAUDE.md (sekcja Narzędzia)

**ERP_SQL_SYNTAX.md — rozbudowa:**
- Sekcja 6: parametry AI_ChatERP (pełna tabela procedur + @ZakresDaty)
- Sekcja 6: tabela funkcji konwersji dat CDN (DateToClarion, DateToTS, itd.)
- Sekcja 7: arytmetyka Clarion inline (pierwszy/ostatni dzień miesiąca, N dni temu)
- Sekcja 11 (nowa): wzorce projektowe widoków BI (nazewnictwo, daty, numery dok., JOIN-y, catalog.json)

**Skan dokumentacji HTML:**
- 2549 plików HTML w erp_docs/raw/
- Zidentyfikowano 342 funkcje, 708 procedur, 27 widoków CDN
- Kluczowe: formuła DateToClarion = `DATEDIFF(dd,'1800-12-28',@dt)` potwierdzona

**BI.Rezerwacje — praca iteracyjna (4 wersje):**
- Odkrycia kluczowe: ZaN_ZamTyp (960=ZS, 1152=ZZ) — nie ZaN_GIDTyp (zawsze 960)
- Clarion TIMESTAMP: Rez_DataRezerwacji = sekundy od 1990-01-01 (nie dni od 1800-12-28)
- CDN.Obiekty: 960="Zamowienie", 2592="Rezerwacja u dostawcy", 14346="Zasob procesu produkcyjnego"
- Filtr techniczny: `WHERE Rez_TwrNumer > 0` (wyklucza 1102 rekordy bez towaru)
- v4: 28 kolumn, 1426 wierszy (baza live), format numerów ZS/ZZ z zero-padded miesiącem
- Export: exports/query_20260304_062910.xlsx

---

### 2026-03-04 — Plan restrukturyzacji wytycznych agenta

Na podstawie retrospektywy pracy nad BI.Rezerwacje uzgodniono zestaw zmian:

**Zmiany programistyczne:**
1. `tools/export_bi_view.py` (nowe) — wieloarkuszowy Excel: Plan mapowania + Wynik SQL + Surówka z tabeli
   Parametry: `--sql`, `--view-name`, `--plan PATH.md`, `--source-table CDN.XXX`
2. `tools/read_excel_stats.py` (nowe) — statystyki kolumn z pliku xlsx bez ładowania danych do kontekstu
   Parametry: `--file`, `--sheet`, `--max-unique N` (def. 20), `--columns`
   Output: per kolumna: total, distinct, null_count, values (jeśli ≤ max-unique) lub sample (10)
3. `tools/export_excel.py` — drobna zmiana: dodać opcjonalny `--view-name` do nazwy pliku

**Restrukturyzacja dokumentacji agenta:**
Podzielić `documents/agent/ERP_SQL_SYNTAX.md` na 5 plików:
- `ERP_SQL_SYNTAX.md` — skrócony rdzeń: ograniczenia SQL, {filtrsql} obowiązek, GIDTyp, funkcje CDN (bez workflow)
- `ERP_COLUMNS_WORKFLOW.md` — workflow dopisywania kolumn ERP (obecna sekcja 2 + wskazówki)
- `ERP_FILTERS_WORKFLOW.md` — workflow tworzenia filtrów ERP (sekcje 3–5 + wskazówki)
- `ERP_VIEW_WORKFLOW.md` — workflow tworzenia widoków BI: checklist discovery, szablon planu mapowania, reguły nazewnictwa, weryfikacja
- `ERP_SCHEMA_PATTERNS.md` — wzorce schematu: daty Clarion (2 typy), JOIN kontrahent/magazyn, CDN.Obiekty, numeracja dokumentów, tabele pomocnicze

Zaktualizować CLAUDE.md — wskazania który plik ładować przy jakim zadaniu.

**Następny krok: implementacja według planu powyżej**

---
