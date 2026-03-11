# Backlog developerski

Przetworzone i priorytetyzowane zadania developerskie.
Źródło: `agent_suggestions.md` + techniczne wątki z `developer_suggestions.md`.

Zarządza: Developer.

## Przegląd

| # | Tytuł | Obszar | Wartość | Praca |
|---|---|---|---|---|
| 1 | LOOM — publikacja na GitHub | Dev | średnia | mała |
| 2 | Baza wzorców numeracji dokumentów | ERP Specialist | wysoka | średnia |
| 3 | Reload konfiguracji bez restartu | Bot | średnia | mała |
| 4 | Routing model Haiku/Sonnet | Bot | średnia | średnia |
| 5 | Fallback przy błędzie SQL | Bot | średnia | średnia |
| 6 | NO_SQL zbyt agresywne | Bot | wysoka | mała |
| 7 | Kontekst firmowy + prompt caching | Bot | wysoka | mała–średnia |
| 8 | bi_catalog_add.py — wyciąganie kolumn z SQL | Dev | wysoka | mała |
| 9 | Sygnatury narzędzi powielone w wielu miejscach | Arch | średnia | mała/duża |
| 10 | arch_check.py — walidator ścieżek w dokumentach | Arch | średnia | mała |
| 11 | Analityk jako weryfikator konwencji widoku | Analityk | wysoka | średnia |
| 12 | Informacja o kontekście na końcu wiadomości | Dev | wysoka | mała |
| 13 | Sygnatury narzędzi powielone w wielu miejscach | Arch | średnia | mała/duża |
| 14 | arch_check.py — walidator ścieżek w dokumentach | Arch | średnia | mała |

---

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


### [Arch] Brak backlogu per-rola

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała–średnia

Wszystkie zadania trafiają do jednego `backlog.md`. Przy wielu rolach wykonawczych
(ERP Specialist, Analityk) zadania domenowe mieszają się z architektonicznymi.

Opcje: osobne pliki backlog per-rola, lub tagi domenowe w istniejącym pliku.
Eskalować do Metodologa.

---

### [ERP] Sesja inspekcji schematu CDN

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Niezbadane: inne funkcje użytkowe w schemacie CDN (poza NazwaObiektu/NumerDokumentu),
widoki CDN.* vs tabele, tabele słownikowe powtarzalne w każdym widoku BI.

Propozycja: krótka sesja inspekcji przed kolejnym widokiem BI — INFORMATION_SCHEMA
+ sp_helptext na kluczowych funkcjach. Nie blokuje bieżącej pracy.

---


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

### [Analityk] Analityk jako weryfikator konwencji widoku

**Źródło:** obserwacja sesji 2026-03-11
**Sesja:** 2026-03-11
**Wartość:** wysoka
**Pracochłonność:** średnia

Analityk sprawdza gotowy widok (po Fazie 3 ERP Specialist, przed wdrożeniem) pod kątem
zgodności z konwencjami projektu. Konwencje zdefiniowane w `ERP_VIEW_WORKFLOW.md`.

Do ustalenia:
- Checklist konwencji (GID, Typ_Dok, nullowalność, nazewnictwo) — osobny plik czy sekcja w ANALYST.md?
- Wynik: lista uwag → ERP Specialist poprawia → ponowny przegląd czy jednorazowo?
- Punkt wejścia: plik brudnopisu `.sql` czy eksport Excel?

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



### [Arch] arch_check.py — walidator ścieżek w dokumentach

**Źródło:** obserwacja sesji 2026-03-11 (refaktor erp_specialist)
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Skanuje pliki `.md` w poszukiwaniu wzorców `` `documents/...` `` i sprawdza czy ścieżki istnieją na dysku.
Uruchamiany przed commitem po każdym refaktorze struktury katalogów.

Do wdrożenia przy kolejnym dużym refaktorze — nie teraz.

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

**[Workflow] Obserwacje z BI.Rozrachunki (8+10) + komendy hook (11)** — zrealizowane 2026-03-11
(ERP_SCHEMA_PATTERNS: UpoNag/KB/TraNag-prefiks/Rozrachunki; ERP_VIEW_WORKFLOW: Typ_Dok/artefakt/brudnopis/verify-query; docs_search phrase opcjonalny)

**[Metodologia] Ręczne przetwarzanie struktury = sygnał dla narzędzia** — zrealizowane przez Metodologa 2026-03-11 (dodane do METHODOLOGY.md sekcja Pętla meta-obserwacji)

**[Dev] bi_catalog_add.py** — WONTDO 2026-03-11 (narzędzie istnieje; problem był w braku kroku w Faza 4 ERP_VIEW_WORKFLOW — naprawione)

**[Agent] Baza wzorców numeracji** — częściowo zrealizowane 2026-03-11 (pliki reference gotowe; otwarte: reguła w ERP_SPECIALIST.md)

**[Dev] Zasada "zbadaj strukturę przed budowaniem"** — zrealizowane 2026-03-11 (DEVELOPER.md zasada #6)

**[Dev] Agent edytuje pliki chronione bez jawnego zatwierdzenia** — zrealizowane 2026-03-11 (CLAUDE.md: protokół pytania przed edycją)

**[Arch] Kanał Developer → ERP Specialist** — częściowo zrealizowane 2026-03-11 (plik `documents/erp_specialist/developer_notes.md` gotowy; otwarte: dodać odczyt tego pliku do ERP_SPECIALIST.md na starcie sesji — wymaga zatwierdzenia)

**[Dev] Kontekst na końcu wiadomości + węzłowość reguł** — zrealizowane 2026-03-11
(CLAUDE.md: reguła kontekstu; DEVELOPER.md: zasada węzłowości; methodology_suggestions: refleksja dla Metodologa)

**[Arch] Separacja pamięci między agentami wykonawczymi** — zrealizowane 2026-03-11
(analyst_suggestions.md, progress log per-zakres, etykieta "Wykonawcy" w CLAUDE.md/METHODOLOGY.md)


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
