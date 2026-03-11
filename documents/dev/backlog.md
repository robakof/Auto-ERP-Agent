# Backlog developerski

Przetworzone i priorytetyzowane zadania developerskie.
Źródło: `agent_suggestions.md` + techniczne wątki z `developer_suggestions.md`.

Zarządza: Developer.

## Format wpisu

```
### [P{n}] Tytuł

**Źródło:** agent_suggestions | developer_suggestions
**Sesja:** data
**Wartość:** wysoka | średnia | niska
**Pracochłonność:** mała | średnia | duża

Opis problemu i propozycja rozwiązania.
```

---

## Aktywne

### [Dev] LOOM — publikacja na GitHub

**Źródło:** methodology_progress (przeniesione z otwartych wątków metodologicznych)
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Folder `_loom/` zawiera komplet plików gotowych do wypchnięcia jako osobne repo.

Kroki:
1. Utwórz repo GitHub (np. `CyperCyper/loom`)
2. Wypchnij zawartość `_loom/` jako root repo
3. Zaktualizuj placeholder URL w `_loom/seed.md`

---

### [Arch] Separacja pamięci między agentami wykonawczymi

**Źródło:** developer_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** średnia

Pojawienie się Analityka Danych obok Agenta ERP ujawniło dwa problemy:

**1. Nazwa poziomu "Agent" jest zbyt wąska.**
Mamy wiele ról wykonawczych (ERP, Analityk, potencjalnie więcej).
Poziom powinien mieć nazwę ogólną (np. "Executor" lub "Agenci").
Dotyczy: CLAUDE.md (tabela ról), METHODOLOGY.md (tabela poziomów), DEVELOPER.md.

**2. Współdzielona pamięć refleksji jest błędna.**
Obecny stan: Analityk i Agent ERP dzielą `agent_suggestions.md`.
Problem: różne role mają różne wzorce obserwacji — mieszanie zaszumi plik.
Każdy agent powinien mieć własny plik suggestions (np. `analyst_suggestions.md`).

**3. Progress log analityka — otwarte pytanie.**
Agent ERP: progress log na poziomie projektu (widok, filtr, kolumna).
Analityk: co jest jednostką pracy? Per zakres (widok/tabela)? Sesja?
Wymaga decyzji przed wdrożeniem.

**Uwaga:** punkty 1 i 2 mają wymiar metodologiczny — warto rozważyć eskalację
do sesji Metodologa przed wdrożeniem. Punkt 3 może być rozwiązany na poziomie Dev.

---

### [Agent] Baza wzorców numeracji dokumentów — usamodzielnienie agenta

**Źródło:** developer_suggestions + obserwacja użytkownika
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** średnia

**Problem:**
CEiM_Reader nie ma EXECUTE na CDN.NazwaObiektu — agent zawsze musi prosić usera
o uruchomienie zapytania przez SSMS. Każdy widok z numerami dokumentów = min. 1-2
round-tripy. Agent robi oszczędne weryfikacje (TOP 20, jeden wzorzec) bo nie widzi
pełnej różnorodności typów.

**Rozwiązanie:**
DBA uruchamia raz zapytanie zbiorcze przez CDN.NazwaObiektu — jeden przykład na każdą
unikalną kombinację (tabela, typ dokumentu, seria, rok). Wynik zapisany jako statyczny plik
referencyjny:

```
solutions/reference/numeracja_wzorce.xlsx
```

Kolumny: Tabela, Typ, Seria, Rok, NumerSystemowy, pola surowe (Numer, Miesiąc, Rok, Seria).

Agent ładuje plik przez `excel_read_rows` na starcie każdego widoku z numerami dokumentów.
Reguła do AGENT.md: "przed numeracją inline — sprawdź wzorce w solutions/reference/numeracja_wzorce.xlsx".

**Zakres prac:**
1. Developer pisze zapytanie zbiorcze pokrywające wszystkie tabele z numerami
   (TraNag, ZamNag, ProdZlecenia, MemNag, RozniceKursowe, ZapNag i inne)
2. User/DBA uruchamia przez SSMS i zapisuje wynik do solutions/reference/
3. Reguła w AGENT.md (chroniony plik — wymaga zatwierdzenia)

**Trade-offy:**
- ✓ Agent samodzielny przy numerach — zero eskalacji do SSMS
- ✓ Jednorazowy koszt, odświeżanie raz na rok lub przy nowych typach dokumentów
- ✗ Statyczne — nowe typy nie pojawią się automatycznie
- ✗ Wymaga DBA do pierwszego uruchomienia

---

### [Bot] Reload konfiguracji bez restartu

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** mała

Przy każdej zmianie promptu lub `.env` wymagany restart bota.
Warto dodać mechanizm przeładowania konfiguracji bez restartu — np. komenda `/reload` przez Telegram (tylko dla admina) lub obserwowanie zmian w pliku `.env` przez watchdog.

---

### [Bot] Routing model — Haiku dla prostych pytań, Sonnet dla złożonych

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

Haiku wystarczy dla prostych pytań (NIP, email, prosta lista). Sonnet potrzebny dla analitycznych (GROUP BY, CASE WHEN, porównania r/r).
Rozwiązanie: classifier w Call 1 — krótki prompt na Haiku ocenia złożoność pytania i wybiera model do generowania SQL.

---

### [Bot] Fallback przy błędzie SQL — ponów z uproszczonym zapytaniem

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** średnia
**Pracochłonność:** średnia

**Problem:**
Gdy model generuje zbyt złożony SQL (np. HAVING z dzieleniem) i baza go odrzuci,
bot zwraca błąd zamiast spróbować uproszczonej wersji.

**Rozwiązanie:**
Gdy `execution_result.ok = False` — pipeline ponawia Call 1 z dodatkową instrukcją:
"Poprzedni SQL zwrócił błąd. Wygeneruj prostszą wersję bez HAVING, bez dzielenia."
Max 1 retry żeby nie generować pętli.

---

### [Bot] NO_SQL zbyt agresywne — częściowe odpowiedzi

**Źródło:** obserwacja sesji testowej
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

**Problem:**
Bot zwraca NO_SQL gdy pytanie zawiera dane częściowo niedostępne (np. "ilość i kwota zamówień" —
ilość jest, kwoty nie ma w widoku). Powinien odpowiedzieć na część pytania i poinformować
o braku pozostałych danych.

**Fix:**
Zmiana instrukcji w `SYSTEM_PROMPT_TEMPLATE` w `nlp_pipeline.py`:
- Obecne: "Jeśli pytanie jest poza zakresem → odpowiedz NO_SQL"
- Poprawione: "Jeśli pytanie jest częściowo poza zakresem → wygeneruj SQL dla dostępnej części
  i zaznacz w odpowiedzi co jest niedostępne. NO_SQL tylko gdy pytanie jest całkowicie poza zakresem."

---

### [Bot] Kontekst firmowy + prompt caching — optymalizacja kosztów i jakości

**Źródło:** obserwacja sesji testowej Haiku
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała–średnia

**Problem:**
Bot nie zna wartości słownikowych bazy (np. `Nazwa_Magazynu = 'Buszewo (WMS)'` zamiast `'Buszewo'`),
akronimów handlowców, ani innych faktów firmowych. Skutkuje błędnymi WHERE i zerowym row_count.
Dodatkowo koszty API są wysokie przy dużym system promptcie bez cachowania.

**Rozwiązanie:**
1. `bot/config/business_context.txt` — statyczny plik z faktami firmowymi (magazyny, handlowcy, słowniki)
2. Prompt caching (Anthropic `cache_control: ephemeral`) na system promptcie — kolejne zapytania kosztują ~10% ceny tokenów systemowych

**Zakres prac:**
1. Plik `business_context.txt` z kluczowymi faktami (do uzupełnienia przez usera)
2. Wstrzyknięcie do system promptu w `nlp_pipeline.py`
3. Dodanie `cache_control` do wywołań API (Call 1 i Call 2)

**Trade-offy:**
- ✓ Sonnet zna dokładne wartości → mniej błędnych zapytań
- ✓ Caching redukuje koszt ~10x dla statycznej części promptu
- ✗ Plik kontekstu trzeba ręcznie utrzymywać przy zmianach w bazie

---

### [Workflow] Obserwacje agenta z sesji BI.Rozrachunki (Faza 2–4)

**Źródło:** agent_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

Sześć obserwacji do wdrożenia w dokumentacji agenta:

1. **CDN.UpoNag (typ 2832)** → `ERP_SCHEMA_PATTERNS.md`: nowa tabela dla not odsetkowych,
   format numeru `NO-YY/Numer`, typ 2832 wykluczyć z NOT IN dla TraNag.

2. **Artefakt wyścigu czasowego** → `ERP_VIEW_WORKFLOW.md`: małe liczby NULL w Nr_Dok
   przy eksporcie z bazy produkcyjnej to nowe rekordy między zapytaniem a eksportem — nie błąd SQL.
   Weryfikacja: `SELECT WHERE COALESCE(...) IS NULL`.

3. **sql_query blokuje CREATE OR ALTER VIEW** → `ERP_VIEW_WORKFLOW.md`: walidacja widoku
   możliwa tylko przez brudnopis (sam SELECT). Nigdy nie porzucaj brudnopisu przed Fazą 4.

4. **Sprawdź że widok istnieje na bazie** → `AGENT.md`: przed użyciem widoku AIBI wykonaj
   `SELECT COUNT(*) FROM AIBI.NazwaWidoku` — widok musi być wdrożony przez DBA.

5. **Reguła GID w widokach BI** → `ERP_SCHEMA_PATTERNS.md` lub `ERP_VIEW_WORKFLOW.md`:
   GIDFirma → pomiń; GIDTyp → tłumacz przez CASE; GIDNumer → zostaw; GIDLp → pomiń.

6. **Typ_Dok — pełne nazwy od Fazy 1** → `ERP_VIEW_WORKFLOW.md`: w planie kolumna Typ_Dok
   domyślnie z pełną nazwą (nie skrótem PA/FS/FSK) — widok BI służy też osobom spoza systemu.

---

### [Metodologia] Wzorzec: ręczne przetwarzanie struktury pliku = sygnał dla narzędzia

**Źródło:** developer_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała (jako reguła) / zależy od implementacji

Obserwacja z sesji: agent ręcznie przepisał ~100 aliasów kolumn z pliku `.sql` do `catalog.json`.
Koszt: duży (kontekst + czas + podatność na błędy). Narzędzie `bi_catalog_add.py` rozwiązuje
konkretny przypadek, ale obserwacja jest szersza:

**Za każdym razem gdy agent ręcznie przetwarza strukturę pliku (regex, ekstrakcja, transformacja)
— to sygnał że brakuje narzędzia.**

Pytanie diagnostyczne: "Czy to co właśnie robię manualnie mogłoby być jednym wywołaniem CLI?"
Jeśli tak i jeśli sytuacja powtarza się lub jest kosztowna — napisz narzędzie.

Potencjalny wymiar metodologiczny: czy ta zasada powinna być zapisana w metodologii jako
ogólna reguła dla Developera? Handoff do Metodologa przygotowany.

---

### [Dev] bi_catalog_add.py — automatyczne wyciąganie kolumn z widoku SQL

**Źródło:** obserwacja sesji
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

Ręczne kopiowanie aliasów kolumn z pliku `.sql` do `catalog.json` jest drogie kontekstowo i podatne na błędy.

Narzędzie `tools/bi_catalog_add.py`:
- Czyta plik widoku `.sql`
- Wyciąga kolumny regexem `AS (\w+)`
- Generuje szkielet wpisu JSON (name, file, columns) gotowy do uzupełnienia o description/example_questions
- Opcjonalnie: dodaje wpis bezpośrednio do `catalog.json`

---

### [Workflow] ERP_SCHEMA_PATTERNS + ERP_VIEW_WORKFLOW — odkrycia z sesji BI.Rozrachunki

**Źródło:** agent_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

**ERP_SCHEMA_PATTERNS.md — nowe wzorce:**

1. KB (784) → CDN.Zapisy: kolumna `KAZ_NumerDokumentu` zawiera gotowy string numeru.
   Nie trzeba budować inline — bezpośredni SELECT na CDN.Zapisy.

2. Prefiks numeru TraNag — zweryfikowana formuła:
   - `(Z)` → TrN_Stan & 2 = 2 AND typ korekty (FSK/FZK/PAK/FKE)
   - `(A)` → TrN_GenDokMag = -1 AND typ zakupowy (FZ/FZK/PZ)
   - `(s)` → TrN_GenDokMag = -1 AND pozostałe
   - brak → standard
   Miesiąc z wiodącym zerem: `RIGHT('0' + CAST(MM AS VARCHAR(2)), 2)`.

3. CDN.Rozrachunki — struktura GIDLp=1/2: każde rozliczenie = 2 lustrzane wiersze.
   Widok bierze GIDLp=1. TRP = strona 1 (faktura/paragon), KAZ = strona 2 (płatność KB).

**ERP_VIEW_WORKFLOW.md — sekcja e) weryfikacja numerów:**

4. Przy pierwszym odczycie formatów z objects.sql — od razu buduj query porównujące
   NumerSystemowy vs NumerInline. Nie czekaj na feedback usera żeby dopiero wtedy
   zaproponować verify query. Jedna runda zamiast dwóch.

---

### [Dev] Komendy agenta blokowane przez hook

**Źródło:** developer_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

Dwa wzorce blokowane u agenta ERP:

1. `python tools/docs_search.py "" --table CDN.X` — pusty string `""` przed `--table`.
   Fix: zrobić argument `fraza` opcjonalnym w `docs_search.py` (nargs='?', default='').
   Wtedy: `python tools/docs_search.py --table CDN.X` bez cudzysłowów.

2. `$(cat plik.sql)` zamiast `--file` przy sql_query.py.
   Fix: reguła w `AGENT.md` — zawsze używaj `--file`, nigdy `$(cat ...)`.

---

### [Dev] Informacja o kontekście na końcu każdej wiadomości

**Źródło:** developer_suggestions
**Sesja:** 2026-03-10
**Wartość:** wysoka
**Pracochłonność:** mała

Agent powinien kończyć każdą wiadomość informacją o aktualnym zużyciu kontekstu
(np. "Kontekst: ~54%"). Cel: świadomość co zużywa kontekst, sygnał do optymalizacji,
bezpieczeństwo przy długich sesjach. Wpisać jako regułę do DEVELOPER.md.

---

### [Arch] Sygnatury narzędzi powielone w wielu miejscach

**Źródło:** developer_suggestions
**Sesja:** 2026-03-08
**Wartość:** średnia
**Pracochłonność:** mała (opcja 3) / duża (opcja 1)

Nazwy i sygnatury narzędzi zapisane w AGENT.md, ERP_VIEW_WORKFLOW.md,
ERP_COLUMNS_WORKFLOW.md, ERP_FILTERS_WORKFLOW.md i docstringach tools/*.py.

Opcje:
1. gen_docs.py generuje sekcję Narzędzia z docstringów (eliminuje problem u źródła)
2. Jeden plik referencyjny TOOLS.md + dyscyplina
3. Test CI sprawdzający czy narzędzia w AGENT.md istnieją jako pliki w tools/

---

## Archiwum

**[Dev] git_commit.py** — zrealizowane 2026-03-10 (--all, --files, --push, --push-only, 14 testów)

*(przeniesione z agent_reflections.md — zrealizowane)*

Pozycje #1–#10 z sesji 2026-03-08: zrealizowane, szczegóły w `agent_reflections.md`.

**[P1] excel_export_bi.py — brak --file** — zrealizowane 2026-03-09
**[P2] sql_query.py — --count-only + --quiet** — zrealizowane 2026-03-09
**[P3] bi_verify.py** — zrealizowane 2026-03-09
**[P4] solutions_save_view.py** — zrealizowane 2026-03-09
**[Prompt] Agent edytuje pliki dokumentacji bez zgody** — zrealizowane przez Metodologa
**[Narzędzia] bi_discovery.py** — zrealizowane 2026-03-09
**[Dev] Komendy powłoki** — zrealizowane 2026-03-09 (git -C, mv zamiast git mv, Read zamiast head/cat)
**[Workflow] ERP_VIEW_WORKFLOW + ERP_SCHEMA_PATTERNS** — zrealizowane 2026-03-10 (zasada pominięcia pola, bi_verify/sql_query, excel_read_rows, TrN_ZaNNumer, format roku przez NazwaObiektu)
