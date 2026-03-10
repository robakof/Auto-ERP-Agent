# Sugestie developera

Plik refleksji Developera — dopisywany podczas lub po sesji deweloperskiej.
Archiwizowany przez człowieka razem z Developerem.

Metodolog czyta ten plik i wyłuskuje z niego obserwacje metodologiczne
do własnego `methodology_suggestions.md`.

## Format wpisu

```
### [DATA] Krótki opis sesji / zadania

1. Czy decyzja architektoniczna którą podjąłem była trafna?
   Co bym zmienił?

2. Czy coś co zbudowałem było zbyt skomplikowane na aktualną potrzebę?

3. Czy zauważyłem coś o metodzie pracy lub strukturze projektu
   co nie wynika bezpośrednio z pracy agenta?
```

Jeśli odpowiedź na pytanie jest "nie" lub "nic" — pomiń pytanie.

---

## Wpisy

### [2026-03-09] P1–P4 + bi_discovery + docs_search refactor

1. **Decyzje architektoniczne:**

   `bi_verify.py` wywołuje `export_bi_view()` wewnętrznie (import funkcji, nie subprocess) —
   dobra decyzja, zero narzutu. Ale przez to test wymaga mockowania na poziomie SqlClient,
   co sprawia że testy są sprzężone z implementacją export_bi_view. Akceptowalne, ale warto mieć świadomość.

   `bi_discovery.py` — testy z `_make_multi_cursor` są kruche na kolejność zapytań wewnątrz funkcji.
   Zmiana kolejności GROUP BY / MIN-MAX łamie testy bez zmiany zachowania zewnętrznego.
   Alternatywa: testować przez asercje na outputcie, nie na kolejności calls — ale wymagałoby
   prawdziwej bazy testowej. Na razie akceptowalne.

2. **Zbyt skomplikowane:**

   Nic. Wszystkie narzędzia tej sesji są małe i jednocelowe. Żadnego over-engineeringu.

3. **Obserwacje o metodzie pracy:**

   Sesja była za długa. Wczytałem ~15 plików przez kontekst, 6 narzędzi, i skończyło się na
   przymusowym zamknięciu. Optymalny rytm to: plan → 2-3 narzędzia → commit → zamknięcie.
   Developer powinien sam proponować zamknięcie sesji po każdym logicznym bloku pracy —
   nie czekać aż kontekst się wyczerpie.

   Odkrycie `--useful-only` jako martwej funkcjonalności wyszło dopiero przy pytaniu usera
   o konkretne wywołanie. Takie "ciche założenia" (is_useful wypełnione) powinny być walidowane
   przy budowie narzędzia, a nie odkrywane w produkcji przez agenta.
   Lekcja: przy każdym nowym narzędziu które opiera się na danych zewnętrznych — sprawdź
   pokrycie tych danych zanim wbudujesz logikę filtrującą na ich podstawie.

### [2026-03-10] Analityk Danych — architektura + implementacja + refleksja metodologiczna

1. **Decyzje architektoniczne:**

   SQLite jako lokalny obszar roboczy analityka — dobra decyzja. Eliminuje wielokrotne
   połączenia do SQL Servera, umożliwia cross-column analysis bez dodatkowego kosztu,
   daje ciągłość stanu między sesjami. Warto rozważyć ten wzorzec przy przyszłych agentach
   potrzebujących dużego lokalnego zbioru danych.

   `data_quality_records.py` — serializacja każdego wiersza jako JSON do jednej kolumny `data`
   (zamiast dynamicznego schematu tabeli) — akceptowalne uproszczenie. Dynamiczny schemat
   byłby trudniejszy do generowania raportów i trudniejszy do testowania. Wadą jest brak
   możliwości łatwego filtrowania po konkretnym identyfikatorze w SQLite.

   Plik `COMMIT_EDITMSG` jako bufor wiadomości commitów — złe rozwiązanie w praktyce.
   Write tool pyta o nadpisanie za każdym razem. Właściwe rozwiązanie to `git_commit.py`.

2. **Zbyt skomplikowane:**

   Nic. 5 narzędzi, każde robi jedną rzecz, razem tworzą spójny pipeline. Dobry podział.

3. **Obserwacje o metodzie pracy:**

   Pojawienie się drugiej roli wykonawczej (Analityk) ujawniło lukę w metodologii:
   zakłada ona jeden poziom "Agent" z jednym plikiem refleksji. Przy dwóch rolach
   wykonawczych to przestaje działać — inne wzorce obserwacji, inna jednostka pracy,
   inne potrzeby ciągłości stanu. Handoff do Metodologa przygotowany.

   Hook bezpieczeństwa blokuje więcej wzorców niż dotychczas dokumentowano:
   `""` przed `--argumentem` (empty string bypass), `$(cat plik)` w argumentach,
   `cd "ścieżka ze spacjami" && komenda`. Każdy nowy wzorzec blokowania to koszt
   użytkownika — musi zatwierdzać lub sesja się zatrzymuje. Warto rozważyć systematyczny
   przegląd komend w AGENT.md i DEVELOPER.md pod kątem hook compliance zanim pojawią się
   w produkcji, nie po.

   Kontekst zużyty nierównomiernie — dużo poszło na czytanie dokumentacji przed implementacją
   (METHODOLOGY.md + AGENT.md = dobre, ale ciężkie). Przy kolejnych sesjach developerskich
   z nową rolą: załaduj tylko DEVELOPER.md na start, METHODOLOGY.md tylko gdy projekt dotyka
   granic metodologicznych — nie profilaktycznie.

   Progress_log pomijany w trakcie sesji — zaktualizowany dopiero gdy użytkownik zapytał.
   Powinien być aktualizowany automatycznie po każdym KM, nie na żądanie.

---

### [2026-03-10] Poziom interwencji — symptom vs źródło

3. **Obserwacje o metodzie pracy:**

   Developer zbyt często naprawia na warstwie promptu i reguł ("powiedz agentowi żeby robił X lepiej")
   zamiast pytać "dlaczego agent w ogóle musi to robić?" i eliminować problem strukturalnie.

   Zasada do wbudowania w DEVELOPER.md:
   **Zanim napiszesz regułę dla agenta — sprawdź czy można usunąć potrzebę tej reguły.**

   Pytania diagnostyczne przed każdą interwencją:
   - Czy to problem który można rozwiązać narzędziem zamiast instrukcją?
   - Czy można precomputować dane tak żeby agent nie musiał ich odkrywać?
   - Czy zmiana architektury sprawia że problem nie ma prawa wystąpić?

   Przykłady z sesji 2026-03-10:
   - Weryfikacja numerów dokumentów → nie "lepszy prompt" ale `numeracja_wzorce.xlsx`
   - `$()` w komendach → nie "reguła w AGENT.md" ale `git_commit.py`
   - `docs_search ""` → nie "uwaga w instrukcji" ale fix w kodzie narzędzia

   Może mieć wymiar metodologiczny — warto rozważyć jako zasadę w METHODOLOGY.md.

---

### [2026-03-10] KM1 search_bi, git_commit, AIBI schema, plan Fazy 2

1. **Decyzje architektoniczne:**

   `git_commit.py` rozwiązało problem u źródła (Write tool → dialog) zamiast dokładać
   kolejną regułę w instrukcjach. Dobry przykład zasady "interwencja na właściwym poziomie"
   z poprzedniej sesji — tym razem zastosowanej w praktyce.

   `search_bi.py` — prosta iteracja po JSON z dopasowaniem tekstowym. Celowo bez FTS5
   na tym etapie (4 widoki). Gdy katalog urośnie > 20 widoków — rozważyć SQLite FTS5
   zgodnie z decyzją z TECHSTACK.md.

2. **Zbyt skomplikowane:**

   Nic. `search_bi.py` i `git_commit.py` są małe i jednocelowe.

3. **Obserwacje o metodzie pracy:**

   Ręczne kopiowanie aliasów kolumn z ZamNag.sql do catalog.json (100 kolumn) — duży błąd.
   Koszt: kontekst + czas + podatność na błąd. Powinien był zaproponować narzędzie zanim
   zaczął kopiować. Ogólna zasada: gdy agent ręcznie przetwarza strukturę pliku
   (regex, ekstrakcja, transformacja) — to sygnał że brakuje narzędzia.
   Pytanie diagnostyczne: "Czy to co właśnie robię manualnie mogłoby być jednym wywołaniem CLI?"
   Skierowane do backloga jako [Metodologia] — ma wymiar szerszy niż jeden narzędzie.

   Na starcie sesji wczytałem `methodology_backlog.md` (widoczny w git status jako zmodyfikowany)
   zamiast `documents/dev/backlog.md`. Skutek: błędne podsumowanie stanu backlogu.
   Naprawione przez dodanie noty w DEVELOPER.md — ale pierwotna przyczyna to zbyt mechaniczne
   podążanie za git status zamiast za instrukcją. Instrukcja miała pierwszeństwo.

---

### [2026-03-09] Porządki, bi_plan_generate, rename widoków

3. **Obserwacje o metodzie pracy:**

   Przy rename widoków używałem `git mv` per plik zamiast zwykłego `mv` + jeden commit na końcu.
   Generuje to niepotrzebne zatwierdzenia przez hook i frustruje usera. Zasada: `git` tylko raz —
   na końcu zadania, nigdy w środku jako narzędzie operacji na plikach.

   Hook bezpieczeństwa blokuje wzorzec `cd "ścieżka ze spacjami" && git commit`.
   Rozwiązanie: używać `git -C "ścieżka"` zamiast `cd && git` — nie wymaga zatwierdzenia.
   Warto dodać do DEVELOPER.md w sekcji "Komendy powłoki".

   Komenda `head -5 plik && echo && head -5 plik2` — hook blokuje jako "quoted characters in flag names".
   Alternatywa: odczytywać pliki przez narzędzie `Read` zamiast Bash dla operacji podglądu.

---

## Archiwum

*(brak wpisów)*
