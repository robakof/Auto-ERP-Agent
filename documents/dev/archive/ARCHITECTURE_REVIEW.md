## Review 1:
Recenzja projektu: Automatyczny Konfigurator Systemu ERP

Co działa dobrze
1. Bardzo dobrze zdefiniowany problem i proces AS-IS/TO-BE
PRD precyzyjnie identyfikuje bolączki obecnego procesu — mechaniczne przeklejanie między narzędziami, brak pamięci między sesjami, ryzyko błędów. Tabela AS-IS z 7 krokami pokazuje, że rozumiesz gdzie tracisz czas. To solidna podstawa do mierzenia sukcesu.
2. Pragmatyczny dobór technologii
Decyzje w TECHSTACK są dobrze uzasadnione i minimalistyczne:

pyodbc bez ORM — słusznie, bo agent tylko czyta
SQLite FTS5 zamiast embeddingów — przy 18k kolumn z dobrymi opisami to wystarczy, a oszczędzasz 500MB zależności i czas inicjalizacji
Pliki .sql + index.json zamiast bazy — przy 50-200 rozwiązaniach to rozsądne, a Git działa naturalnie

3. Wzorzec "thin tools, smart agent"
Architektura gdzie narzędzia są głupie (wejście → wyjście), a logika po stronie agenta — to dokładnie jak powinno się projektować MCP tools. Ułatwia debugowanie i testowanie każdego narzędzia w izolacji.
4. Mechanizm bezpieczeństwa read-only
Jawne odrzucanie DML/DDL w sql_query.py przed wysłaniem do bazy to krytyczne zabezpieczenie. Dobrze, że jest na poziomie narzędzia, nie tylko "umowy" z agentem.
5. Katalog okien ERP (erp_windows.json)
To eleganckie rozwiązanie problemu mapowania języka użytkownika ("okno zamówień") na struktury SQL. Bez tego agent błądziłby po 1647 tabelach.
6. Warstwowa strategia nawigacji
Okno → flagi użyteczności → słowniki → weryfikacja na żywej bazie — to przemyślana ścieżka zawężania przestrzeni poszukiwań.

Co wymaga uwagi
1. Brak specyfikacji formatu CLAUDE.md — krytyczne dla MCP
W ARCHITECTURE wspominasz o pliku CLAUDE.md jako "instrukcje dla agenta (kontekst startowy)", ale nigdzie nie ma jego struktury ani zawartości. To jest najważniejszy plik w całym projekcie — definiuje jak agent ma używać narzędzi, w jakiej kolejności, kiedy eskalować.
Sugestia: Dodaj dokument CLAUDE_MD_SPEC.md z:

Listą dostępnych narzędzi i ich sygnaturami
Workflow domyślnym (eksploracja → dokumentacja → wzorce → generowanie → test)
Regułami eskalacji (po ilu iteracjach, przy jakich błędach)
Przykładami promptów wejściowych i oczekiwanych zachowań

2. Współbieżność zapisu do index.json — niedoszacowane ryzyko
Piszesz "akceptowalne przy małej liczbie użytkowników", ale nawet przy 3 osobach może dojść do utraty danych gdy dwie zapiszą rozwiązanie w podobnym czasie. JSON nie ma mechanizmu upsert.
Sugestia: Rozważ jedną z opcji:

Plik lockfile przy zapisie (index.json.lock)
SQLite zamiast JSON (ma wbudowane locki)
Rozdzielenie na osobne pliki per rozwiązanie (UUID.json) i generowanie indeksu dynamicznie

3. Brak obsługi błędów sieciowych do współdzielonego folderu
Co się dzieje gdy \\serwer\erp-agent\ jest niedostępny? Narzędzia prawdopodobnie rzucą wyjątek, ale agent nie będzie wiedział jak zareagować.
Sugestia: Dodaj w specyfikacji narzędzi jawny format błędu (np. {"error": "NETWORK_UNAVAILABLE", "path": "..."}) i instrukcję w CLAUDE.md jak agent ma reagować.
4. Brak wersjonowania rozwiązań
Gdy ktoś zaktualizuje istniejące rozwiązanie w solutions/columns/xyz.sql, poprzednia wersja znika. Przy współdzielonym folderze bez Gita to ryzyko.
Sugestia:

Albo: folder solutions/ jako repo Git z commitami per zapis
Albo: append-only z timestampem (xyz_20260226.sql) i indeks wskazujący na najnowszą wersję

5. Nieokreślony format wyjścia narzędzi
Piszesz "wyniki zwracane do agenta w formacie czytelnym (JSON lub tabela)" — to zbyt ogólne. Claude Code potrzebuje przewidywalnego formatu żeby parsować odpowiedzi.
Sugestia: Zdefiniuj schemat JSON dla każdego narzędzia, np.:
json// sql_query.py output
{
  "success": true,
  "columns": ["col1", "col2"],
  "rows": [["val1", "val2"], ...],
  "row_count": 42,
  "truncated": false
}
6. Brak limitu wielkości wyników SQL
Co gdy sql_query.py zwróci 10 000 wierszy? Agent dostanie ścianę tekstu, przekroczy kontekst.
Sugestia: Domyślny LIMIT 100 lub TOP 100 dodawany przez narzędzie + flaga truncated: true w odpowiedzi + możliwość jawnego override przez agenta.
7. Nieopisany proces budowania erp_windows.json
Piszesz "tworzony i rozszerzany ręcznie przez developera" — ale skąd developer ma wiedzieć jakie okna istnieją? Czy jest źródło (dokumentacja ERP, eksport z systemu)?
Sugestia: Dodaj sekcję w dokumentacji opisującą jak katalogować nowe okno — nawet jeśli to proces ręczny.
8. Metryki sukcesu trudne do zmierzenia automatycznie
"≥80% kroków procesu AS-IS wykonywanych przez agenta" — jak to zmierzysz? Kto liczy kroki?
Sugestia: Dodaj konkretne metryki mierzalne z logów:

Średnia liczba iteracji do sukcesu
% sesji zakończonych bez eskalacji
Czas od wymagania do gotowego SQL


Pytania do autora

Jak wygląda "kod wklejany do ERP"? — W PRD pytasz czy to SQL, XML, VBA. Od tego zależy czy agent generuje gotowy produkt, czy półprodukt wymagający transformacji.
Czy dokumentacja Excel jest unikalna dla Twojej instalacji ERP? — Pytam, bo struktura arkuszy (Tabele, Kolumny, Relacje...) wygląda na customową. Jeśli tak, build_index.py będzie silnie sprzężony z tym formatem.
Co z aktualizacjami schematu ERP? — Gdy dostawca ERP doda nowe tabele/kolumny, jak trafiają do Twojego indeksu? Ręczny re-eksport Excel → rebuild?
Jak testujesz poprawność wygenerowanego SQL? — PRD mówi o "podzapytaniach testujących", ale nie definiuje co to znaczy. Czy agent ma sprawdzać że wynik nie jest pusty? Że typy się zgadzają? Że JOINy zwracają sensowną liczbę wierszy?
Gdzie są gotowe fragmenty SQL od firmy wdrożeniowej? — Masz je już w formacie gotowym do zaimportowania, czy wymagają obróbki?


Ocena: 7.5 / 10
Uzasadnienie:
Dokumentacja jest ponadprzeciętna jak na fazę przed implementacją — jasno zdefiniowany problem, pragmatyczne decyzje technologiczne, przemyślana architektura z katalogiem okien i warstwową nawigacją.
Punkty odjęte za:

Brak specyfikacji CLAUDE.md — to krytyczny element dla MCP, a go nie ma (-1)
Niedospecyfikowane formaty I/O narzędzi (-0.5)
Brak obsługi edge cases (współbieżność, limity, błędy sieciowe) (-0.5)
Metryki sukcesu trudne do weryfikacji (-0.5)

Rekomendacja: Przed implementacją uzupełnij specyfikację CLAUDE.md i zdefiniuj schematy JSON dla narzędzi. To pozwoli uniknąć przeróbek gdy agent zacznie się zachowywać nieprzewidywalnie.

## Review 2
Poniżej moja recenzja na podstawie całości materiału (PRD + Techstack + Architektura). 

PRD

 

TECHSTACK

 

ARCHITECTURE

Co działa dobrze (mocne strony)

Dobrze uchwycony problem i metryki sukcesu. AS-IS vs TO-BE jest czytelne, a kryteria akceptacji są mierzalne (redukcja kroków, skuteczność bez eskalacji, zero DML/DDL). To rzadkość w projektach “AI-agentowych”. 

PRD

Architektura “thin tools, smart agent” jest trafiona dla MVP. Proste, deterministyczne narzędzia CLI (wejście → wyjście) minimalizują powierzchnię błędów i ułatwiają debug. 

ARCHITECTURE

Rozsądne decyzje techniczne pod skale danych. SQLite + FTS5 to pragmatyczny wybór dla ~18k kolumn / ~1.6k tabel, bez wprowadzania ciężkich embeddingów na start. 

TECHSTACK

Bezpieczeństwo jako default (read-only). Koncepcja blokowania DML/DDL przed wysłaniem do bazy jest właściwą linią obrony na poziomie narzędzia. 

ARCHITECTURE

Bardzo dobry wątek “katalogu okien ERP”. Rozpoznanie, że użytkownik mówi o oknach, a nie tabelach, jest kluczowe. To realnie ograniczy tokeny, czas i liczbę ślepych strzałów. 

ARCHITECTURE

Myślenie o współdzieleniu wiedzy (shared folder) i reużyciu rozwiązań jest sensowne w organizacji. 

ARCHITECTURE

Co wymaga uwagi (konkretne ryzyka + sugestie)
1) “SELECT-only” to za mało jako kontrola bezpieczeństwa

Problem: Samo wykrywanie słów kluczowych w SQL jest łatwe do obejścia (komentarze, dynamic SQL, EXEC, sp_executesql, OPENROWSET, ;WITH + wstrzyknięcia w stringach, wielostatement, itp.). Dodatkowo nawet “SELECT” może być destrukcyjny operacyjnie (ciężkie skany, blokady, SELECT INTO, tempdb pressure).

Sugestie:

W sql_query.py wymuś:

połączenie użytkownikiem DB o uprawnieniach read-only (to musi być główna bariera, nie regex).

timeouty (query timeout + connection timeout) i limit wierszy (np. automatyczne dopisywanie TOP (N) do testów eksploracyjnych).

blokadę wielu statementów (np. zezwól na pojedyncze zapytanie; odrzucaj ; poza końcem).

blokadę EXEC, sp_executesql, OPENQUERY/OPENROWSET, SELECT INTO oraz innych “escape hatches”.

Rozważ tryb “explain first”: najpierw SET SHOWPLAN_XML ON / estimated plan dla ciężkich zapytań (jeśli polityka DB pozwala), dopiero potem wykonanie.

2) Brakuje specyfikacji kontraktów narzędzi (formatów JSON) i walidacji

Problem: Narzędzia mają zwracać JSON, ale nie ma ustalonego schematu odpowiedzi, kodów błędów, ani stabilnych pól. Agent będzie “zgadywał” strukturę i to szybko się rozpadnie przy rozwoju.

Sugestie:

Zdefiniuj minimalny contract dla każdego toola:

ok: bool, data: ..., error: {type, message, details}, meta: {duration_ms, row_count, truncated}.

Dorzuć walidację wyjścia po stronie narzędzi (nawet prostą) i testy “golden files”.

Dla sql_query.py rozważ zwracanie zawsze także nagłówków kolumn i typów (przydaje się do weryfikacji typu danych i późniejszych joinów).

3) Iteracyjny loop (max 5) jest opisany, ale brakuje strategii “jak testować”

Problem: “Podzapytania testujące” są krytyczne, a obecnie to hasło. Bez jasnej strategii agent będzie losowo odpalał kosztowne selekty albo robił testy, które nic nie mówią.

Sugestie:

Zrób prostą “bibliotekę testów” (w narzędziach lub w instrukcjach agenta):

test istnienia kolumny/tabeli (metadata),

test join cardinality (czy join nie multiplikuje wierszy),

test null-rate dla kolumny,

test przykładowych wartości (TOP 20),

test wydajności (czas + rowcount + ostrzeżenie o braku indeksu jeśli potrafisz wykryć).

W logach zapisuj nie tylko SQL, ale też czas wykonania i rowcount, żeby móc optymalizować.

4) Rozwiązania w solutions/ i index.json: ryzyko jakości + driftu

Problem: “Baza rozwiązań” będzie rosnąć i z czasem stanie się śmietnikiem lub duplikatami bez procesu higieny. Dodatkowo wspólny folder i równoległe zapisy do index.json to proszenie się o uszkodzenia (race condition). 

ARCHITECTURE

Sugestie:

Zamiast edycji jednego index.json rozważ:

jeden plik metadanych per rozwiązanie (.json obok .sql), a indeks buduj “na żądanie” lub jako cache,

albo przenieś metadane do SQLite (nawet jeśli kod zostaje w plikach) – wtedy współbieżność jest rozwiązywalna.

Wprowadź minimalny proces jakości:

status: draft/approved/deprecated,

właściciel/autor,

test query / przykładowy wynik,

tag “okno ERP” (powiązanie z erp_windows.json).

5) Indeks dokumentacji: FTS jest OK, ale brakuje normalizacji i podejścia do aktualizacji

Problem: Excel ma wiele arkuszy, dużo pól “opisowych”, flagi użyteczności itd. Bez jasnych kluczy i normalizacji w SQLite może się okazać, że relacje są niejednoznaczne, a wyszukiwanie zwraca dużo śmieci.

Sugestie:

W docs.db trzymaj:

klucze jednoznaczne: table_id, column_id (np. CDN.KntKarty|Knt_Nazwa1),

pola do “rankingowania” (np. is_useful, is_preferred_for_reports), aby search_docs.py mógł sortować wyniki sensownie. 

ARCHITECTURE

Doprecyzuj strategię reindeksacji i kompatybilności wersji:

wersja schematu indeksu,

kiedy przebudowa jest wymagana,

jak wykrywasz zmianę źródeł (mtime, hash).

6) Brakuje jasnej granicy: “co jest wynikiem”, a “co jest wdrożeniem”

Problem: PRD mówi, że out-of-scope to pełne wdrożenie bez akceptacji, ale nadal kluczowe jest: jaki dokładnie artefakt agent produkuje (SQL do wklejenia gdzie?), jak wygląda walidacja “gotowe”.

Sugestie:

Zdefiniuj format “deliverable”:

blok SQL + krótka instrukcja wklejenia,

oczekiwany efekt w ERP,

checklistę: okno, kolumna/filtr/raport, zależności.

Dodaj “diff / summary” przed zapisaniem rozwiązania i przed eskalacją (już wspomniane w ryzykach, warto ująć jako wymaganie). 

PRD

7) Observability / debug: logi są, ale brakuje korelacji i powtarzalności

Problem: “Odtwarzalność” jest wymaganiem, ale bez identyfikatorów kroków, wersji indeksu, wersji narzędzi, parametrów środowiska trudno to będzie naprawdę odtworzyć. 

PRD

Sugestie:

W logach sesji zapisuj:

session_id, timestamp, git commit hash (jeśli repo),

wersję docs.db/hash źródeł,

listę wywołań narzędzi (wejście + skrót wyjścia + czas).

Rozważ “replay mode”: odpalenie sesji na podstawie logów (nawet częściowo) – to turbo przyspiesza rozwój.

Pytania do autora (rzeczy do doprecyzowania)

Jak agent ma się uwierzytelniać do SQL Server? Czy zakładacie osobnego użytkownika read-only / osobną rolę? (To kluczowe dla bezpieczeństwa, ważniejsze niż filtr słów w SQL). 

PRD

Co dokładnie znaczy “wklejenie finalnego kodu do systemu ERP”? Gdzie ten SQL trafia (definicja kolumny? zapytanie raportu? konfiguracja filtra?) i jakie są ograniczenia składniowe ERP? 

PRD

Czy środowiska DEV/TEST/PROD są przewidziane od początku? Jak zabezpieczycie, żeby agent nie odpalał ciężkich zapytań na PROD (nawet jeśli read-only)? 

PRD

Jakie są wymagania wydajnościowe na bazie ERP? Czy macie limity czasu zapytań, zakazy skanów, ograniczenia w godzinach pracy?

Jak będziecie rozwiązywać konflikty przy współdzielonym index.json i zapisie rozwiązań? “Akceptowalne” przy małej liczbie userów – OK, ale ile to jest “mała” i jak zareagujecie przy pierwszym uszkodzeniu pliku? 

ARCHITECTURE

Czy search_windows.py jest już w scope MVP? W architekturze jest opisany jako kluczowy dla niejednoznaczności wymagań, ale w PRD/roadmapie nie jest wyraźnie ujęty jako must-have. 

ARCHITECTURE

 

PRD

Ocena (1–10)

8/10.
Kierunek architektury i dobór technologii są bardzo pragmatyczne i dobrze “dowożą MVP”. Największe punkty ryzyka to bezpieczeństwo wykonywania zapytań (realne, nie “na regexie”), kontrakty narzędzi/formaty danych oraz higiena współdzielonej bazy rozwiązań (w tym współbieżność). Jeśli dopracujesz te trzy obszary, projekt będzie naprawdę solidny.

Jeśli chcesz, mogę w kolejnym kroku zaproponować konkretny kontrakt JSON dla wszystkich narzędzi + “minimalny standard” logów sesji (tak, żeby agent był przewidywalny i łatwy do debugowania).

## Review 3:
Cześć! Przyjrzałem się Twojej dokumentacji (PRD, Techstack, Architecture). To bardzo dojrzałe podejście do automatyzacji powtarzalnych zadań w specyficznym środowisku ERP. Wybranie podejścia „Thin tools, smart agent” (chude narzędzia, mądry agent) zamiast budowania ciężkiego frameworka to świetna decyzja architektoniczna, która drastycznie skraca czas do MVP.

Zanim przejdę do szczegółowej oceny, mam kilka pytań, które pomogą mi lepiej zrozumieć wyzwania implementacyjne:

Pytania do autora:
Konkurencja w zapisie: Planujesz przechowywać index.json bazy rozwiązań na folderze sieciowym. Jak zamierzasz rozwiązać problem jednoczesnego zapisu przez dwóch użytkowników? (Przy prostym pliku JSON ostatni zapis wygrywa, co może prowadzić do utraty danych).

Walidacja semantyczna: Agent testuje kod przez uruchomienie go w bazie. Czy planujesz narzucić mu ograniczenie TOP N (np. TOP 10) na każde zapytanie testowe, aby uniknąć przypadkowego obciążenia serwera przy próbie pobrania miliona rekordów z dużej tabeli transakcyjnej?

Wersjonowanie dokumentacji: Skąd agent będzie wiedział, że docs.db jest nieaktualne względem źródłowego pliku Excel? Czy planujesz automatyczny hash-check przy starcie?

Ocena projektu
Co działa dobrze (Mocne strony)
Strategia RAG bez „ML-owego narzutu”: Wykorzystanie SQLite FTS5 do przeszukiwania dokumentacji z Excela to strzał w dziesiątkę. Przy skali 18k kolumn tradycyjne embeddingi semantyczne mogłyby być mniej precyzyjne niż wyszukiwanie pełnotekstowe po technicznych nazwach i aliasach.

Architektura MCP (Model Context Protocol): Wykorzystanie standardu Claude Code pozwala skupić się na logice narzędzi (sql_query.py, search_docs.py), a nie na budowaniu samej pętli myślenia agenta. To bardzo „lean”.

Bezpieczeństwo (Read-only): Hardkodowane odrzucanie słów kluczowych DML (INSERT, UPDATE) w sql_query.py to kluczowy bezpiecznik, który pozwoli na wdrożenie narzędzia w środowisku produkcyjnym/deweloperskim bez strachu o integralność danych.

Katalog Okien ERP (erp_windows.json): To kluczowe ogniwo łączące świat biznesowy (użytkownik widzi „okno”) ze światem technicznym (SQL widzi tabele). Bez tego mapowania agent „utonąłby” w 1600 tabelach.

Co wymaga uwagi (Obszary do poprawy)
1. Ryzyko współdzielonego folderu sieciowego
Przechowywanie index.json dla bazy rozwiązań na folderze sieciowym przy wielu użytkownikach jest ryzykowne.

Sugestia: Zmień bazę rozwiązań na mały plik SQLite. SQLite obsługuje blokowanie plików na poziomie systemu operacyjnego, co pozwoli na bezpieczny dostęp współbieżny wielu agentów jednocześnie bez ryzyka uszkodzenia pliku.

2. Ochrona wydajności SQL
Agent w fazie testowania może wygenerować poprawne składniowo, ale zabójcze wydajnościowo zapytanie (np. CROSS JOIN na wielkich tabelach).

Sugestia: W narzędziu sql_query.py dodaj automatyczne wstrzykiwanie SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED (aby uniknąć lockowania tabel w ERP) oraz wymuś limit czasowy (timeout) dla zapytania na poziomie sterownika pyodbc.

3. Problem „Halucynacji Sukcesu”
Agent może uznać, że zapytanie jest poprawne, bo nie zwróciło błędu SQL, mimo że logicznie zwraca złe dane (np. zły JOIN).

Sugestia: W instrukcjach dla agenta (CLAUDE.md) dodaj protokół weryfikacji: „Zawsze porównaj wynik zapytania z przykładowymi wartościami z search_docs”. Jeśli kolumna ma zawierać NIP, a zapytanie zwraca nazwę firmy — agent musi umieć to wychwycić przed prezentacją kodu człowiekowi.

4. Utrzymanie erp_windows.json
Ręczne utrzymywanie mapowania 1600 tabel do okien będzie wąskim gardłem.

Sugestia: Dodaj narzędzie analyze_schema.py, które na podstawie kluczy obcych i statystyk (liczba rekordów) podpowiada developerowi, które tabele są „główne” i powinny znaleźć się w katalogu okien.

Podsumowanie i ocena
Projekt jest bardzo solidnie przemyślany pod kątem inżynierskim. Nie goni za nowinkami (jak wektorowe bazy danych tam, gdzie nie są potrzebne), tylko rozwiązuje realny problem przy użyciu najprostszych skutecznych narzędzi.

Ocena: 8.5/10

Dlaczego nie 10? Brakuje mi mechanizmu obsługi konfliktów przy współdzieleniu bazy rozwiązań oraz twardych limitów wydajnościowych na zapytania testowe (timeout/row-limit). Po zaadresowaniu tych dwóch punktów system będzie gotowy do bezpiecznego wdrożenia w zespole konfiguratorów.

Czy chciałbyś, abym przygotował dla Ciebie szkic skryptu sql_query.py z uwzględnieniem tych zabezpieczeń (timeout, top N, read-uncommitted)?