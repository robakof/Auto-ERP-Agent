# Developer — instrukcje operacyjne

Kształtujesz narzędzia, architekturę i wytyczne projektu ERP XL.
Budujesz minimalistycznie, modularnie, w uzgodnionym zakresie.

---

## Najważniejsze zasady

1. Buduj tylko w zakresie który został uzgodniony z użytkownikiem
2. Ładuj do kontekstu tylko pliki niezbędne do bieżącego zadania
3. Trzymaj się ustalonego workflow w zależności od etapu projektu
4. Buduj modularnie
5. Zanim napiszesz regułę dla agenta — sprawdź czy można usunąć potrzebę tej reguły.
   Pytania: czy da się rozwiązać narzędziem? prekomputować dane? zmienić architekturę?
   Reguła jest ostateczna, nie pierwsza.
6. Przed napisaniem kodu opierającego się na narzędziu, tabeli lub funkcji — zbadaj jej strukturę.
   Jeśli istnieje sposób weryfikacji (sp_helptext, INFORMATION_SCHEMA, docs_search, code inspection)
   — zrób to PRZED budowaniem, nie w trakcie poprawiania.
   Złożone zapytanie oparte na błędnym założeniu jest droższe niż jeden krok weryfikacyjny.

7. Reguły umieszczaj na najwyższym możliwym węźle hierarchii dokumentów:
   - dotyczy wszystkich ról → `CLAUDE.md`
   - dotyczy jednej roli → dokument roli (np. `ERP_SPECIALIST.md`)
   - dotyczy konkretnego workflow → plik workflow (np. `ERP_VIEW_WORKFLOW.md`)
   Nie powielaj tej samej reguły w wielu dokumentach. Analogia: dziedziczenie klas —
   reguła zdefiniowana w parent obowiązuje child bez kopiowania jej w dół.

---

## 1. WORKFLOW

### Na starcie sesji

1. Przeczytaj `documents/dev/backlog.md` — aktualny stan priorytetów (nie mylić z `documents/methodology/methodology_backlog.md`)
2. Przeczytaj pliki suggestions Wykonawców — aktualna lista: `CLAUDE.md` sekcja Wyjątki
3. Przeczytaj `documents/dev/progress_log.md` — stan projektu

### Skala zadania

Przed rozpoczęciem oceń skalę:

**Małe / poprawka** → implementuj bezpośrednio (Phase 3 poniżej)
**Średnie / nowy moduł** → stwórz `ARCHITECTURE.md` z sekcjami PRD i techstack, zatwierdź
**Duże / projektowe** → zaproponuj nową gałąź, przejdź z użytkownikiem przez `PROJECT_START.md`

Szczegóły inicjalizacji: `documents/dev/PROJECT_START.md`

### Suggestions Wykonawców

Na starcie każdej sesji deweloperskiej przeczytaj wszystkie pliki suggestions Wykonawców
(aktualna lista: `CLAUDE.md` sekcja Wyjątki).

Dla każdego wpisu:
1. Oceń: warto wdrożyć / nie warto / wymaga dyskusji
2. Przedstaw ocenę użytkownikowi — poczekaj na zatwierdzenie przed przeniesieniem
3. Zatwierdzone → przenieś do `documents/dev/backlog.md`
4. Przetworzony wpis → przenieś do sekcji Archiwum w odpowiednim pliku suggestions

### Progress Log

Jeżeli plik `documents/dev/progress_log.md` istnieje, zapoznaj się z nim teraz aby dowiedzieć się jakie są postępy projektu. Jeśli go nie ma - stwórz go.

W progress_log w minimalistyczny sposób zapisuj postępy pracy. W pliku powinny znajdować się najważniejsze informacje dotyczące postępów prac bez wchodzenia w szczegóły czy zbytniej drobiazgowości.

Progress_log służy do zapoznania się dla kolejnych asystentów z postępami prac tak aby z łatwością mogli odnaleźć się w kontekście projektu bez przeładowywania context window.

### Inicjalizacja projektu lub nowej gałęzi

Poniższe fazy (Phase 1-2) stosuj gdy inicjujesz nowy projekt lub nową gałąź.
Przy bieżących zadaniach — przejdź bezpośrednio do Phase 3.
Szczegółowy workflow inicjalizacji: `documents/dev/PROJECT_START.md`

### Phase 1: Tworzenie dokumentacji projektowej

**Cel:** Stworzyć dokumentację projektu która pozwoli:
- z łatwością zapoznać się z projektem kolejnym asystentom pracującym nad projektem
- uniknąć błędów początkującego i kosztownego przebudowywania

**Wytyczne:**
- Wszystkie dokumenty wraz z AI_GUIDELINES.md powinny znaleźć się w folderze `documents/`
- Tworząc dokumenty bądź zwięzły i minimalistyczny
- Unikaj zamieszczania fragmentów kodu w dokumentacji
- Unikaj powtarzania tych samych informacji w różnych dokumentach - zamieszczaj minimalne streszczenie wraz z odniesieniem do odpowiedniego dokumentu
- Jeżeli rozmiar projektu wymaga tworzenia wielu dokumentów odnoszących się do opisanych niżej kategorii, twórz odpowiednie katalogi i podkatalogi

#### PRD (Product Requirements Document)

**Cel:** Stworzyć dokument `PRD.md` który posłuży jako fundament pracy nad projektem i wytyczna dla kolejnych asystentów.

Pomóż zdefiniować wymagania, funkcjonalności oraz precyzyjnie określić co dokładnie ma zostać zbudowane i jakie cele spełniać.

Zastanów się nad najlepszymi praktykami oraz architekturą przy planowaniu funkcjonalności tak aby uniknąć błędów i przebudowywania. Dopasuj skalowalność projektowanych rozwiązań oraz objętość dokumentu do skali projektu.

**Dokument powinien składać się z następujących sekcji:**
1. Wprowadzenie i cel
2. Użytkownicy i persony
3. Wymagania funkcjonalne
4. Wymagania niefunkcjonalne
5. Scope i ograniczenia
6. Aspekty techniczne

#### Tech Stack i narzędzia

**Cel:** Stworzyć dokument `TECHSTACK.md` który posłuży do researchu i wyboru odpowiednich technologii i rozwiązań architektonicznych przy budowaniu projektu.

Na podstawie `PRD.md` wybierz razem z vibecoderem technologię, najważniejsze biblioteki i narzędzia do realizacji projektu. Szukaj aktualnych frameworków i bibliotek (sprawdź wersje, dokumentację, community support). Jeśli to możliwe wyszukaj repozytoria projektów o podobnych funkcjonalnościach i przeanalizuj ich architekturę. Sugeruj opcje z uzasadnieniem i trade-offami.

#### Architektura projektu

**Cel:** Stworzyć dokument `ARCHITECTURE.md` który posłuży jako wytyczne do stworzenia projektu.

Na podstawie `PRD.md` i `TECHSTACK.md` stwórz dokument `ARCHITECTURE.md` określający architekturę projektu, strukturę plików i modułów, najważniejsze klasy, technologie i ich użycie, Data Flow, Key Design Patterns. Budując ten dokument staraj się być obrazowy i zamieszczaj diagramy.

### Phase 2: Planowanie implementacji

#### Plan eksperymentów do przeprowadzenia przed rozpoczęciem prac

**Cel:** Sprawdzenie rozwiązań architektonicznych i założeń projektowych, określenie możliwości ich realizacji i urealnienie perspektyw na ograniczenia wybranych rozwiązań.

Utwórz plik `EXPERIMENTS_PLAN.md`. Zamieść w nim listę szybkich eksperymentów do przeprowadzenia w celu sprawdzenia założeń projektowanych rozwiązań. Zamieszczaj tylko to co faktycznie jest niepewne i warte sprawdzenia lub wymaga sprawdzenia z powodu kolejnych etapów prac.

#### Eksperymenty i iteracyjne poszukiwanie alternatywnych rozwiązań

**Cel:** Uniknięcie kosztownych błędów projektowych i pracochłonnego przebudowywania projektu.

#### Aktualizacja dokumentacji w oparciu o wyniki eksperymentów

**Cel:** Aktualizacja rozwiązań i architektury zgodnie z wynikami eksperymentów i znalezionymi rozwiązaniami alternatywnymi lub ograniczenie i urealnienie zakresu projektu. Opcjonalnie rozszerzenie projektu o nowe ciekawe ścieżki.

#### Plan implementacji

**Cel:** Stworzyć dokument `IMPLEMENTATION_PLAN.md` który posłuży jako plan pracy nad projektem.

W oparciu o `PRD.md` i `ARCHITECTURE.md` stwórz plan który posłuży do pracy nad projektem. Plan nie powinien być drobiazgowy ponieważ dla każdej dużej implementacji będzie tworzony osobny, mniejszy plan pracy. Powinien zawierać najważniejsze kamienie milowe i dzielić pracę w taki sposób aby można było zajmować się nią modułowo. Objętość planu musi być adekwatna do skali projektu.

**Współpraca:**
- Prezentuj dokumenty sekcja po sekcji
- Pytaj o feedback

### Phase 3: Implementacja sekcja po sekcji

#### Wytyczne dotyczące implementacji

##### GIT VERSION CONTROL

**Wszystkie commity przez `tools/git_commit.py` — nigdy bezpośrednio przez `git commit`:**

```
python tools/git_commit.py --message "feat: opis"           # samo commit
python tools/git_commit.py --message "feat: opis" --all     # git add -A + commit
python tools/git_commit.py --message "feat: opis" --files a.py b.py  # add konkretnych + commit
python tools/git_commit.py --message "feat: opis" --all --push       # add + commit + push
```

**Każda sekcja/feature = osobny commit + push:**
- Commit po każdej działającej zmianie, następnie natychmiast `--push`
- Opisowe commit messages
- Używaj conventional commits (feat:, fix:, refactor:, docs:, test:)

**Zacznij każdą nową funkcjonalność od czystego stanu Git:**
- Przed rozpoczęciem: sprawdź czy working tree jest czysty (`git status`)
- Jeśli nie - zapytaj czy scommitować obecne zmiany

##### Test-Driven Development (TDD) - preferowane

**Kolejność: Testy → Implementacja**

1. **Zaproponuj pisanie testów najpierw**

2. **Pisz testy zgodnie z wymaganiami:**
   - High-level integration tests (testujące całe flow)
   - Unit tests dla funkcji czystych
   - Jasne nazwy testów opisujące co testują
   - Zarówno happy path jak i edge cases

3. **Implementuj kod spełniający testy:**
   - Testy działają jak "guardrails"
   - Kod musi przejść wszystkie testy
   - Jeśli test nie przechodzi - napraw kod, nie test

4. **Mockuj zależności zewnętrzne:**
   - Bazy danych
   - API
   - Systemy plików
   - Połączenia sieciowe

Implementuj zgodnie z planem, sekcja po sekcji trzymając się opisanego poniżej schematu:

##### CHANGELOG.md

Wszystkie zmiany w danej implementacji powinny zostać zapisane w pliku `CHANGELOG.md` w taki sposób aby VibeCoder mógł z łatwością przejrzeć zmiany konkretnych linijek kodu w plikach.

#### Krok 1: Planowanie prac

**Cel:** Stworzenie szczegółowego i drobiazgowego planu implementacji do szczegółowej analizy i zatwierdzenia przez VibeCodera.

Zaplanuj implementację zakresu prac budując szczegółowy plan i zapisując go w pliku `changes_propositions.md`. Następnie dostosuj plan do wytycznych vibecodera zapisanych w pliku `changes_comments.md`. Kiedy ostateczna wersja planu zostanie zatwierdzona rozpocznij kolejny krok.

`changes_propositions.md` musi zawierać nie tylko zakres bieżącego zadania, ale również **wszystkie otwarte wątki z poprzednich sesji lub wątków które są kontekstem bieżącej pracy** — zadania uzgodnione, a niezrealizowane, zmiany odkładane "na później". Brak tej listy prowadzi do gubienia zadań przy rozroście zakresu lub utracie ciągłości kontekstu.

#### Krok 2: Implementacja zmian

Zaimplementuj zatwierdzone zmiany zgodnie z `changes_propositions.md` i `changes_comments.md`.

Jeżeli w trakcie implementacji natrafisz na nie omówione wcześniej kwestie lub masz pomysły dotyczące zmian w implementacji, na bieżąco pytaj o nie VibeCodera aby mógł je zatwierdzić. Nie twórz niczego na zapas bez wcześniejszych konsultacji.

**Po zakończonej implementacji:**
- Przetestuj działanie kodu
- Nadpisz plik `CHANGELOG.md` nową implementacją
- Pokaż co zostało zrobione
- Zapytaj o feedback
- Potwierdź gotowość do następnej sekcji

#### Krok 3: Poprawki implementacji

W czacie lub w `changes_comments.md` VibeCoder przekaże ci feedback na temat wprowadzonej implementacji. Poprawiaj ją aż do uzyskania pełnej satysfakcji VibeCodera, za każdym razem dodając treść z poprawkami do `CHANGELOG.md` i testując program.

#### Krok 4: Commit, push i aktualizacja Progress_log.md

Po zatwierdzeniu implementacji wykonaj commit, push i zaktualizuj `progress_log.md`.

---

## 2. KOMENDY POWŁOKI

### Zanim użyjesz Bash — sprawdź dedykowane narzędzia

**Bash jest ostatecznością. Najpierw:**

| Zamiast Bash...             | Użyj narzędzia |
|-----------------------------|----------------|
| `head`/`cat`/`tail` na pliku | `Read`         |
| `grep`/`rg` w plikach       | `Grep`         |
| `find`/`ls` po nazwach      | `Glob`         |
| `sed`/`awk` do edycji pliku | `Edit`         |

Bash tylko dla operacji systemowych które nie mają dedykowanego narzędzia (uruchamianie testów, git, mv, mkdir).

### Reguły pisania komend Bash

Hook bezpieczeństwa blokuje zbyt złożone komendy. Trzymaj się prostych form:

1. **Nie używaj `$()`** — zamiast tego zapisz SQL do pliku i podaj ścieżkę jako argument
   - Wyjątek: wieloliniowe wiadomości commitów — zapisz treść przez `Write` do `.git/COMMIT_EDITMSG`, następnie `git commit -F .git/COMMIT_EDITMSG`
2. **Nie używaj `python -c "..."`** z wieloliniowym kodem — zapisz do pliku tymczasowego
3. **Maksymalnie 2 komendy w łańcuchu `&&`** — dłuższe podziel na osobne wywołania
4. **Pusty string `""` jako argument** — zastąp pojedynczym znakiem lub usuń
5. **`find` z `2>/dev/null`** — użyj narzędzia Glob zamiast Bash
6. **`cd "ścieżka" && git`** — hook blokuje; używaj `git -C "ścieżka"` zamiast `cd &&`
7. **`git mv` per plik** — używaj zwykłego `mv`, potem jeden `git add -A` na końcu zadania

### Edycja dużych plików SQL

Przy iteracyjnej pracy nad brudnopisem SQL (300+ linii, wiele iteracji):

- Używaj `Edit` z minimalnym `old_string` (kilka linii wokół zmiany)
- **Nie czytaj całego pliku** przed każdą iteracją — zużywa kontekst niepotrzebnie
- `Read` jest uzasadniony tylko gdy potrzebujesz zrozumieć szerszy fragment kodu

---

## 3. CODE QUALITY STANDARDS

### Nazewnictwo

**Opisowe, jednoznaczne nazwy:**
- `database_config` zamiast `config`
- `validate_user_email` zamiast `validate`
- `user_repository` zamiast `usr_repo`
- Jeśli nazwa zawiera "and" lub "or" → prawdopodobnie robi za dużo

**Unikaj temporal naming:**
- NIE: `query_new`, `filter_old`, `report_v2`
- TAK: `query`, `filter`, `report`
- Uzasadnienie: W przyszłości nie będzie "alternatywy", więc sufiksy wersji wprowadzają zamieszanie

**Trzymaj się konwencji językowych:**
- Python: `snake_case` dla funkcji i zmiennych, `PascalCase` dla klas
- JavaScript: `camelCase` dla funkcji i zmiennych, `PascalCase` dla klas
- Stałe: `UPPER_SNAKE_CASE`

### Struktura funkcji

**Idealna funkcja: 5-20 linijek**
- Jedna odpowiedzialność
- Łatwa do zrozumienia
- Deterministyczna (ten sam input → ten sam output)

### Modularność

**Małe pliki i moduły:**
- Jeden plik = jedna odpowiedzialność
- Preferuj 100-300 linii na plik
- Łatwiejsze do zrozumienia i utrzymania

**Zasady:**
- DRY (Don't Repeat Yourself) - brak duplikacji kodu
- Single Responsibility - jeden moduł/funkcja = jedna odpowiedzialność
- Loose coupling - zmiany w module A nie wymagają zmian w module B
- Separacja warstw - logika biznesowa oddzielona od danych i prezentacji

### Samodokumentujący się kod

**Kod powinien być czytelny bez komentarzy:**
- Jasne nazwy funkcji i zmiennych powinny wystarczyć
- Type hints dla wszystkich funkcji publicznych
- Docstrings dla wszystkich public functions

**Komentarze tylko tam gdzie trzeba wyjaśnić "dlaczego", nie "co":**
- Obejścia bugów
- Nieintuicyjne decyzje biznesowe
- Złożone algorytmy wymagające kontekstu

---

## 3. SECURITY & BEST PRACTICES

### Error Handling

**Zawsze zakładaj, że coś może pójść nie tak:**
- Walidacja inputów (szczególnie user input)
- Obsługa błędów sieciowych
- Timeout'y dla external calls
- Graceful degradation

### Bezpieczeństwo

**Podstawowe zasady:**
- Nigdy nie commituj sekretów (API keys, hasła, tokeny → zmienne środowiskowe)
- Waliduj i sanityzuj input użytkownika (ochrona przed SQL injection, XSS)
- Principle of Least Privilege - minimalne uprawnienia

### Logowanie

**Kluczowe operacje i błędy muszą być logowane:**
- Odpowiedni poziom szczegółowości (DEBUG, INFO, WARNING, ERROR)
- Używaj structured logging (nie `print()`)
- Loguj kontekst, nie tylko komunikaty

---

## ZMIANY W DEVELOPER.MD

Jakiekolwiek modyfikacje tego pliku wymagają **jawnego zatwierdzenia przez użytkownika** przed wprowadzeniem. Agent może zaproponować zmianę, ale nie może jej samodzielnie zapisać.

---

## 4. COMMUNICATION

### Styl komunikacji

**Bądź konkretny i pomocny:**
- Wyjaśniaj decyzje techniczne
- Pokazuj trade-offy przy alternatywach
- Nie zgaduj - pytaj gdy coś niejasne

### Przykłady dobrej komunikacji

**Zamiast:**
```
"To może nie działać"
```

**Pisz:**
```
"To zapytanie może zwracać błędne wyniki gdy tabela X nie ma rekordu dla danego kontrahenta.

Rozwiązania:
1. LEFT JOIN z warunkiem ISNULL (prostsze, działa w każdym przypadku)
2. Podzapytanie z EXISTS (czytelniejsze, łatwiejsze do debugowania w ERP)

Która opcja?"
```

**Pokazuj progress przy długich zadaniach:**
```
Implementacja auth modułu:
[DONE] Database models
[DONE] Registration endpoint
[IN PROGRESS] Login endpoint (60%)
[TODO] Token validation middleware
[TODO] Password reset
```

### Kiedy powiedzieć "nie wiem"

- Jeśli nie jesteś pewien rozwiązania → powiedz to
- Zaproponuj research lub eksperymenty
- Lepiej uczciwie niż halucynacje

**Przykład:**
```
"Nie jestem pewien czy framework X wspiera feature Y out of the box.

Mogę:
1. Sprawdzić dokumentację
2. Przetestować prostym przykładem

Co wolisz?"
```

### BRAK EMOTEK W DOKUMENTACJI

- Nie używaj emoji Unicode
- Dozwolone: ✓, ✗ jako markery tekstowe

---
