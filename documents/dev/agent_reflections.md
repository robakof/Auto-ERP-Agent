# Refleksje nad pracą agenta

Plik roboczy — obserwacje i propozycje usprawnień zbierane w trakcie sesji.
Nie wszystko musi być adresowane od razu. Plik służy do gromadzenia materiału
przed kolejną sesją developerską lub metodologiczną.

Format wpisu:
- **Kategoria:** (Excel / SQL / Narzędzia / Workflow / Bugi / Bezpieczeństwo / Struktura)
- **Źródło:** kto zaobserwował (user / agent)
- **Opis:** co konkretnie nie działało lub co można poprawić
- **Propozycja:** co zmienić (dokument / narzędzie / workflow)

---

## [Workflow] Agent nie eksportuje Excela automatycznie po każdej iteracji SQL

**Źródło:** user
**Sesja:** 2026-03-08

Podczas pracy nad widokiem BI agent iteruje zapytanie SELECT — zmienia kolumny, JOINy,
warunki. Wynik każdej iteracji jest widoczny tylko w czacie (JSON). User musi osobno
poprosić o eksport do Excela, żeby zobaczyć dane w wygodnej formie.

**Propozycja:**
- `ERP_VIEW_WORKFLOW.md` (Faza 2): każda zmiana brudnopisu SQL kończąca się testem
  `sql_query.py` powinna automatycznie wywołać `excel_export.py --output {Widok}/{Widok}_export.xlsx`
- Bez pytania, bez czekania na popchnięcie — eksport jest częścią kroku testowania
- Plik nadpisywany in-place (stała ścieżka bez timestampu) — nie zaśmieca folderu

---

## [Struktura] Pliki robocze widoku BI — rozrzucone w 3 miejscach

**Źródło:** user
**Sesja:** 2026-03-08

Pliki jednego widoku BI są dziś w różnych folderach według typu:
- `solutions/bi/drafts/Rezerwacje.sql` — brudnopis SQL
- `solutions/bi/drafts/Rezerwacje_progress.md` — progress log
- `solutions/bi/plans/Rezerwacje_plan.xlsx` — plan mapowania
- `exports/Rezerwacje_TIMESTAMP.xlsx` — wynik eksportu
- (plus potencjalnie `drafts/Rezerwacje_objects.sql`)

Przy pracy nad widokiem trzeba nawigować między folderami. Trudno ogarnąć co należy do danego widoku.

**Propozycja — jedna struktura per widok:**
```
solutions/bi/
└── Rezerwacje/
    ├── Rezerwacje_draft.sql          ← brudnopis SQL (iterowany in-place)
    ├── Rezerwacje_progress.md        ← log faz discovery/plan/sql/export
    ├── Rezerwacje_plan.xlsx          ← plan mapowania (edytowany przez usera)
    ├── Rezerwacje_objects.sql        ← zapytanie weryfikujące CDN.NazwaObiektu
    └── Rezerwacje_export.xlsx        ← ostatni wynik eksportu (nadpisywany)
```

Zmiany do wprowadzenia:
- `ERP_VIEW_WORKFLOW.md`: zaktualizować ścieżki w całym dokumencie
- `excel_export_bi.py`: `--output` domyślnie do folderu widoku
- Obecne foldery `solutions/bi/drafts/` i `solutions/bi/plans/` — przenieść zawartość, usunąć

---

## [Excel] Plan mapowania — arkusz i tabela bez znaczących nazw

**Źródło:** user
**Sesja:** 2026-03-08

Arkusz z planem mapowania dostał nazwę "dane" — nic nie mówi o zawartości.
Kolumna z opisem kolumny zawierała nazwę własną kolumny zamiast opisu z dokumentacji.
Tabela w arkuszu nie była sformatowana jako Excel Table (brak możliwości filtrowania).

**Propozycja:**
- `ERP_VIEW_WORKFLOW.md`: arkusz planu powinien mieć nazwę = nazwa widoku (np. "Rezerwacje")
- Tabela Excel powinna być sformatowana jako Table (Insert → Table) z nazwą np. `Plan_Rezerwacje`
- Kolumna Opis: agent musi brać opis z `docs_search` (`col_label` lub `description`),
  nie `col_name`
- Do weryfikacji: czy `excel_export_bi.py` tworzy tabelę Excel (Table object) czy tylko zakres

---

## [SQL] Zapytanie CDN.NazwaObiektu — nie zapisywane do pliku

**Źródło:** user
**Sesja:** 2026-03-08

Zapytanie weryfikujące typy obiektów (CDN.NazwaObiektu, CDN.Obiekty) jest generowane
w czacie i wykonywane jednorazowo. User nie może go łatwo przekopiować ani do niego wrócić.

**Propozycja:**
- `ERP_VIEW_WORKFLOW.md` (Faza 0e): agent MUSI zapisać zapytanie weryfikujące typy
  dokumentów do pliku `{Widok}/Widok_objects.sql` przed wykonaniem
- Wzorzec: `SELECT OB_GIDTyp, OB_Nazwa, OB_Skrot FROM CDN.Obiekty WHERE OB_GIDTyp IN (...)`

---

## [Bezpieczeństwo] Agent pisze komendy powłoki zbyt złożone — hook blokuje

**Źródło:** user
**Sesja:** 2026-03-08

Hook bezpieczeństwa blokuje komendy zawierające:
- `$()` command substitution
- `""` w ciągach (potencjalny obfuscation)
- `python -c "..."` z komentarzami `#` w środku
- `find . ... 2>/dev/null | head` z `cd` na początku
- Długie łańcuchy `&&`

User musi zatwierdzać zbyt wiele skomplikowanych komend. Część z nich można uprościć.

**Propozycja:**
- `AI_GUIDELINES.md` (nowa sekcja: reguły pisania komend powłoki):
  1. Nie używać `$()` — zamiast tego zapisać SQL do pliku i podać ścieżkę
  2. Nie używać `python -c` z wieloliniowym kodem — zapisać do pliku tymczasowego
  3. Nie łączyć `&&` więcej niż 2 komendy w jednej linii
  4. Pusty string `""` jako argument — zastąpić spacją lub innym znakiem
  5. `find` z `2>/dev/null` — użyć Glob tool zamiast Bash

---

## [Narzędzia] Propozycja: bi_discovery.py — automatyczny raport discovery

**Źródło:** agent (self-reflection)
**Sesja:** 2026-03-08

Faza discovery widoku BI to zawsze te same ~10 zapytań:
- `SELECT TOP 1 *` — struktura kolumn
- `COUNT(*), COUNT(DISTINCT PK)` — baseline
- `COUNT(DISTINCT col)` dla każdej kolumny — stałość pól
- `MIN/MAX` na kolumnach dat — klasyfikacja Clarion DATE vs TIMESTAMP
- `GROUP BY` na kolumnach z małą liczbą unikalnych wartości — enumeracje

**Propozycja:**
```
python tools/bi_discovery.py CDN.NazwaTabeli [--pk Kolumna_GIDNumer] [--filter "warunek"]
```
Zwraca raport:
- baseline COUNT
- lista pól stałych (COUNT DISTINCT = 1) → kandydaci do pominięcia w planie
- klasyfikacja dat: Clarion_DATE / Clarion_TIMESTAMP / SQL_DATE
- enumeracje (< N unikalnych) z listą wartości

Oszczędność: ~10 zapytań → 1 round-trip. Szczególnie wartościowa klasyfikacja dat.

---

## [Bugi] excel_export.py — walidacja SQL dzieli po średniku w stringach

**Źródło:** agent (self-reflection)
**Sesja:** 2026-03-08

`SqlClient.validate()` dzieli SQL po `;` bez uwzględnienia kontekstu string literal.
Tekst planu zawierający `;` w uzasadnieniach (np. `Klucz obcy do CDN.TwrKarty; zachowany`)
powoduje błąd — agent musi ręcznie usuwać średniki z tekstu.

**Propozycja:**
- Poprawić regex: `re.split(r';(?=(?:[^\']*\'[^\']*\')*[^\']*$)', sql)`
- Alternatywnie: przyjmować ścieżkę do pliku SQL jako argument zamiast inline string
- Dotyczy: `tools/lib/SqlClient` (metoda validate)

---

## [Bugi] docs_search — błąd encodingu cp1250 na niektórych wynikach

**Źródło:** agent (self-reflection)
**Sesja:** 2026-03-08

`docs_search` zwraca błąd encodingu (cp1250) przy niektórych frazach. Błąd nie jest
widoczny dla wszystkich zapytań — psuje się niewidocznie tylko przy pewnych wynikach.
Agent musiał obejść problem przez bezpośredni dostęp do SQLite (python -c).

**Propozycja:**
- Zlokalizować miejsce: prawdopodobnie wynik z FTS5 zawiera znak poza zakresem cp1250
- Naprawić: jawne `encode/decode` lub `errors='replace'` w output
- Sprawdzić czy problem dotyczy też innych toolsów (solutions_search, windows_search)

---

## [Workflow] Agent czyta plan proceduralnie zamiast priorytetyzować niespójności

**Źródło:** agent (self-reflection)
**Sesja:** 2026-03-08

Przy odczycie planu Excel agent przetwarza wiersze jeden po drugim. Niespójności
(Komentarz_Usera ≠ Uwzglednic) są wykrywane dopiero przy implementacji, nie na starcie.

**Propozycja:**
- `ERP_VIEW_WORKFLOW.md` (Faza 1, odczyt planu): agent powinien NAJPIERW zidentyfikować
  wiersze gdzie `Komentarz_Usera` jest wypełniony LUB `Uwzglednic` różni się od domyślnego
  i zgłosić je jako listę do rozstrzygnięcia PRZED generowaniem SQL
- Szablon: "Zanim zacznę — znalazłem N wierszy z potencjalnymi niespójnościami: ..."

---

## [Architektura] Sygnatury narzędzi powielone w wielu miejscach — brak single source of truth

**Źródło:** user + developer
**Sesja:** 2026-03-08

Nazwy i sygnatury narzędzi są zapisane w:
- `CLAUDE.md` (sekcja Narzędzia)
- `ERP_VIEW_WORKFLOW.md` (przykłady wywołań)
- `ERP_COLUMNS_WORKFLOW.md`, `ERP_FILTERS_WORKFLOW.md` (przykłady)
- docstringi w samych plikach `tools/*.py`

Po każdym rename lub zmianie parametrów trzeba ręcznie aktualizować wszystkie miejsca.
Przy refaktorze tools/ (2026-03-07) pominięto dokumenty agenta — błędy wykryto dopiero
w kolejnej sesji.

**Opcje do rozważenia:**
1. **Generowanie sekcji Narzędzia w CLAUDE.md ze skryptów** — każdy tool ma docstring
   w standardowym formacie, skrypt `tools/gen_docs.py` buduje sekcję automatycznie
2. **Jeden plik referencyjny** `documents/agent/TOOLS.md` — importowany/cytowany przez
   pozostałe dokumenty (wymaga dyscypliny, nie eliminuje duplikacji technicznie)
3. **Test CI** — test sprawdzający czy narzędzia wymienione w CLAUDE.md faktycznie istnieją
   jako pliki w `tools/` (szybki, nie wymaga zmiany architektury)

Opcja 3 jest najtańsza i łapie problem automatycznie. Opcja 1 eliminuje problem u źródła.

---

## [Workflow] Agent używał błędnych nazw narzędzi

**Źródło:** agent (self-reflection)
**Sesja:** 2026-03-08

Wywołano `tools/search_docs.py` zamiast `tools/docs_search.py` — file not found.
Nazwy po refaktorze (prefiks domenowy) różnią się od nazw zapamiętanych przez agenta.

**Propozycja:**
- Sprawdzić czy wszystkie przykłady w dokumentach agenta używają nowych nazw toolsów
  (`docs_search`, `solutions_search`, `windows_search`, `excel_export`, `excel_export_bi`)
- Rozważyć: alias lub wrapper ze starą nazwą zwracający błąd ze wskazówką na nową nazwę

---

## [Workflow] Weryfikacja numerów dokumentów — agent pomijał drugi etap

**Źródło:** agent (self-reflection)
**Sesja:** 2026-03-08

Agent zweryfikował format numeru dokumentu tylko dla jednego podtypu (ZW dla type=960)
i założył jednorodność. Dopiero uwaga usera ("coś się nie zgadza") ujawniła drugi podtyp
(ZaN_ZamTyp) — inne numery dla ZS vs ZZ. Efekt: SQL z błędnie wygenerowanymi numerami.

Prawidłowa kolejność weryfikacji:
1. `SELECT DISTINCT ZaN_ZamTyp` wewnątrz tabeli źródłowej — najpierw sprawdź ile podtypów
2. Dla każdego podtypu osobno: `CDN.NazwaObiektu(typ, numer, 0, 2)` na próbce

Dodatkowa obserwacja: istnienie funkcji `CDN.NazwaObiektu` jest sygnałem, że logiki
numeracji **nie da się odtworzyć inline** (system ją enkapsuluje właśnie dlatego).
Próba inżynierii wstecznej jest kosztowna i zawodna. Gdy taka funkcja istnieje —
używaj jej, nie obchodź.

**Propozycja:**
- `ERP_VIEW_WORKFLOW.md` (Faza 0e): weryfikacja numerów dokumentów = zawsze dwuetapowa:
  krok 1: `SELECT DISTINCT` wszystkich podtypów z tabeli źródłowej,
  krok 2: próbka `CDN.NazwaObiektu` dla **każdego** podtypu osobno
- Reguła ogólna: gdy funkcja CDN enkapsuluje logikę — używaj funkcji; eskaluj do usera
  z konkretnym pytaniem zamiast próbować odtworzyć logikę samodzielnie

---

## [Workflow] Błędna nazwa tabeli — CDN.Operatorzy zamiast CDN.OpeKarty

**Źródło:** agent (self-reflection)
**Sesja:** 2026-03-08

Agent wywołał `JOIN CDN.Operatorzy` → SQL error 208 (tabela nie istnieje).
Poprawna nazwa to `CDN.OpeKarty`. Stracono 2 zapytania na diagnozę.

**Propozycja:**
- `ERP_SCHEMA_PATTERNS.md`: dodać sekcję "Nieoczywiste nazwy tabel":
  `CDN.OpeKarty` (nie Operatorzy), i podobne pułapki
- Zasada: gdy JOIN na tabeli nieznanej — najpierw `docs_search "prefiks_GIDNumer"`,
  nie zgaduj nazwy

---
