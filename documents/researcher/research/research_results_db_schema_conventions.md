# Research: Best practices dla schematów SQLite w projektach multi-agent

Data: 2026-03-26

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 5 najważniejszych wniosków

1. **Nie udało się potwierdzić jednego konsensusu społeczności SQLite dla singular vs plural nazw tabel.** Najmocniejszy wzorzec, który da się potwierdzić w dojrzałych projektach, to: `lowercase` + najczęściej `snake_case` + wysoka spójność wewnątrz jednego schematu. Firefox, Android i Django pokazują różne decyzje co do liczby pojedynczej/mnogiej, ale podobny nacisk na konsekwencję nazewniczą. — **siła dowodów: praktyczne**

2. **Dojrzały wzorzec migracji dla SQLite to wersjonowane migracje + jawna historia schematu + gotowość na “table rebuild”, a nie poleganie wyłącznie na `ALTER TABLE`.** Oficjalne ograniczenia SQLite i praktyki Django/Alembic potwierdzają, że przy większych zmianach często kończy się na: utwórz nową tabelę → skopiuj dane → usuń starą → zmień nazwę. — **siła dowodów: praktyczne**

3. **W systemach multi-process WAL nie znosi podstawowego ograniczenia SQLite: nadal jest tylko jeden writer naraz na plik bazy.** Najbardziej potwierdzone dźwignie to: krótkie transakcje zapisu, `BEGIN IMMEDIATE` dla write pathów, oddzielenie readerów od writerów, świadome checkpointing/WAL housekeeping oraz read-only połączenia tam, gdzie to możliwe. — **siła dowodów: praktyczne**

4. **`CHECK` w SQLite nie zastępuje walidacji aplikacyjnej, ale jest bardzo sensowną warstwą ochrony dla invariantów, które mają obowiązywać wszystkich writerów.** Dotyczy to szczególnie systemów wieloagentowych i samego SQLite, który bez `STRICT`, `CHECK`, `NOT NULL`, `UNIQUE` i `FOREIGN KEY` jest dość liberalny typowo i semantycznie. `CHECK` dla stabilnych enumów nie wygląda na overkill; jest raczej standardową techniką ochrony domeny danych. — **siła dowodów: praktyczne**

5. **Dla nazw indeksów także nie ma jednego kanonu typu `idx_table_columns`.** Dojrzałe projekty używają raczej wzorców „czytelnych i globalnie unikalnych”: nazwa tabeli + kolumny lub nazwa tabeli + semantyczny sufiks (`uniqueindex`, `hostindex`, itp.). Najbardziej stabilny wspólny mianownik to nie prefix, tylko jednoznaczność, przewidywalność i brak kolizji nazw. — **siła dowodów: praktyczne**

---

## Wyniki per pytanie

### 1) Naming conventions dla SQLite — plural vs singular, snake_case vs camelCase

#### Co udało się potwierdzić

- **Nie udało się potwierdzić jednego, oficjalnego „SQLite community consensus” dla liczby pojedynczej vs mnogiej nazw tabel.** SQLite nie narzuca konwencji nazewniczej, a dojrzałe projekty idą różnymi drogami. — **siła dowodów: praktyczne**
- **`snake_case` / lowercase jest znacznie lepiej potwierdzone niż camelCase.** Firefox (`moz_places`, `moz_bookmarks`, `moz_anno_attributes`) używa lowercase + underscores i często liczby mnogiej. Android ContactsProvider również używa lowercase nazw tabel, ale miesza singular/plural (`data`, `presence`, `contacts`, `settings`). Django auto-generuje nazwy tabel w stylu `app_label_model`, też lowercase z underscore. — **siła dowodów: praktyczne**
- **Najsilniejsza praktyczna norma to spójność w obrębie projektu, a nie plural albo singular jako uniwersalna reguła.** Firefox jest relatywnie konsekwentny w kierunku plural/prefix; Android pokazuje, że duży i dojrzały projekt może mieszać oba style bez jednego absolutnego wzorca; Django pokazuje inny wariant: nazwy wynikające z modelu i app label. — **siła dowodów: praktyczne**

#### Jak robią to znane projekty

- **Firefox / Places**: tabele takie jak `moz_places`, `moz_bookmarks`, `moz_annos`, `moz_anno_attributes`, `moz_places_metadata`; konwencja: prefiks produktu + lowercase + underscore, często plural. To jest silny przykład „namespace + spójność”, nie dowód na uniwersalne „plural zawsze”. — **siła dowodów: praktyczne**
- **Android ContactsProvider**: nazwy tabel i indeksów są lower-case, ale pluralizacja jest mieszana. Widać jednocześnie `contacts`, `presence`, `data`, `settings`, `aggregation_exceptions`. To mocny kontrprzykład dla tezy, że dojrzałe projekty SQLite mają jeden obowiązujący styl singular/plural. — **siła dowodów: praktyczne**
- **Django**: auto-generowane nazwy tabel są lower-case i oparte o `app_label` + nazwę modelu, np. `myapp_person`; dla indeksów i constraintów Django mocno naciska na unikalne nazwy. — **siła dowodów: praktyczne**
- **Homebrew**: w publicznie dostępnych źródłach nie udało się potwierdzić jednego, centralnego wzorca schematu SQLite porównywalnego do Firefox/Android/Django. — **siła dowodów: praktyczne**

#### Trade-offy i alternatywy

- **Plural**
  - plusy: lepiej brzmi dla tabel traktowanych jako zbiory rekordów (`users`, `jobs`, `events`)
  - minusy: większa liczba wyjątków językowych, mniej naturalne przy tabelach „słownikowych” lub systemowych
  - **siła dowodów: spekulacja**

- **Singular**
  - plusy: bliżej modelu encji (`user`, `task`, `agent`)
  - minusy: mniej naturalne dla części zespołów SQL-owych i mniej zgodne z praktyką części projektów open-source
  - **siła dowodów: spekulacja**

- **`snake_case`**
  - plusy: najlepiej potwierdzona praktyka w obserwowanych projektach, dobrze współgra z SQL, CLI, diffami i nazwami indeksów/constraintów
  - minusy: brak istotnych minusów technicznych; głównie kwestia estetyczna
  - **siła dowodów: praktyczne**

- **camelCase**
  - plusy: bywa preferowany w zespołach myślących modelami z kodu aplikacji
  - minusy: słabiej potwierdzony w badanych projektach SQLite, gorsza czytelność w długich nazwach SQL
  - **siła dowodów: spekulacja**

#### Wniosek syntetyczny

Najmocniej potwierdzony wniosek nie brzmi „używaj plural” ani „używaj singular”, tylko: **używaj jednego stylu w całym schemacie; lowercase/`snake_case` ma znacznie silniejsze potwierdzenie praktyczne niż camelCase.** — **siła dowodów: praktyczne**

---

### 2) Migration patterns dla SQLite single-file DB bez ORM

#### Co udało się potwierdzić

- **SQLite ma ograniczone wsparcie dla modyfikacji schematu in-place.** To jest twarde ograniczenie silnika i główny powód, dla którego dojrzałe narzędzia i frameworki mają specjalne ścieżki dla SQLite. — **siła dowodów: praktyczne**
- **W dojrzałych praktykach powtarza się wzorzec wersjonowania migracji oraz przechowywania historii zastosowanych zmian w tabeli metadanych.** Dbmate używa `schema_migrations(version PRIMARY KEY)`. Flyway utrzymuje schema history table jako audit trail z checksumami i statusem migracji. — **siła dowodów: praktyczne**
- **Dla SQLite dojrzałe narzędzia zakładają potrzebę „recreate table” dla części zmian.** Django robi to jawnie. Alembic używa batch mode, które dla SQLite w praktyce odtwarza tabelę. — **siła dowodów: praktyczne**
- **Istnieją co najmniej trzy dojrzałe rodziny podejść, żadna nie jest uniwersalnie najlepsza:**
  1. plain SQL files + tabela historii migracji,
  2. code-based upgrade steps w aplikacji,
  3. framework migracyjny z obsługą SQLite-specific batch mode.
  — **siła dowodów: praktyczne**

#### Potwierdzone wzorce

##### A. Wersjonowane pliki SQL + tabela historii migracji

To jest bardzo silnie potwierdzony wzorzec poza ORM-ami:

- **Dbmate**: plain SQL, pliki timestamp-versioned, migracje uruchamiane atomowo w transakcji, dodatkowo `schema.sql` do diffów i bootstrapu, oraz `schema_migrations` jako tabela stanu. — **siła dowodów: praktyczne**
- **Flyway**: schema history table jako pełny audit trail z informacją kto/kiedy/co odpalił, plus checksumy i wykrywanie dryfu po edycji już zastosowanych migracji. Flyway wspiera SQLite, ale jawnie zaznacza ograniczenie: brak concurrent migration dla SQLite. — **siła dowodów: praktyczne**
- **Goose**: dojrzały wzorzec katalogu migracji z timestamped/numbered SQL files. — **siła dowodów: praktyczne**

**Trade-offy:**
- plusy: czytelny audit trail, dobre code review, niezależność od języka aplikacji, łatwe uruchamianie przez CI/CD, dobre dopasowanie do „direct SQL in Python”
- minusy: trzeba samemu dyscyplinować kolejność, rollbacki i kompatybilność zmian SQLite; większa liczba zmian typu rebuild table wymaga ostrożnych, ręcznie pisanych skryptów
- **siła dowodów: praktyczne**

##### B. Code-based incremental upgrades w aplikacji

Android `SQLiteOpenHelper` jest mocnym dowodem, że to podejście jest dojrzałe i stosowane produkcyjnie. `onUpgrade()` wykonuje sekwencyjne kroki typu `if (oldVersion < X) upgradeToVersionX(db)`; Android dokumentuje też, że upgrade działa w transakcji i odsyła do wzorca „rename old table → create new → copy data” przy zmianach wykraczających poza prosty `ALTER TABLE`. — **siła dowodów: praktyczne**

**Trade-offy:**
- plusy: łatwe powiązanie migracji z kodem aplikacji, prosty deployment w jednym artefakcie, dobra kontrola nad migration logic i data migration w jednym miejscu
- minusy: słabsza audytowalność SQL-a jako osobnego artefaktu, trudniejsza współpraca wielu narzędzi/języków, tendencja do rozrastania długich łańcuchów `if oldVersion < ...`
- **siła dowodów: praktyczne**

##### C. Alembic / framework migracyjny z trybem SQLite-aware

Alembic jest możliwy, ale nie „za darmo”. Dla SQLite wymaga rozumienia batch mode i ograniczeń constraint reflection. Szczególnie ważne: **named `CHECK` constraints są uwzględniane w batch mode, ale unnamed `CHECK` constraints mogą zostać pominięte przy recreate table.** — **siła dowodów: praktyczne**

**Trade-offy:**
- plusy: dojrzały ekosystem, uporządkowane migracje, dobra ergonomia dla zespołów już używających SQLAlchemy/Alembic
- minusy: trzeba znać SQLite-specific caveats; część złożoności wynika z prób ukrycia ograniczeń SQLite, a nie z ich usunięcia
- **siła dowodów: praktyczne**

#### Czego nie potwierdziłem

- **Nie znalazłem mocnych źródeł, które wspierałyby podejście „inline `ALTER TABLE` w kodzie bez historii migracji” jako dojrzały pattern dla rosnącego schematu SQLite.** Pojawia się ono jako lokalna praktyka, ale nie jako najlepiej ugruntowany standard. — **siła dowodów: praktyczne**

#### Wniosek syntetyczny

Najmocniej potwierdzone wzorce dla rosnącego schematu SQLite bez ORM to:
- **pliki migracji SQL + tabela historii**,
- albo **jawne, wersjonowane upgrade steps w kodzie**,
- przy założeniu, że część zmian będzie wymagała **table rebuild**, nie tylko `ALTER TABLE`. — **siła dowodów: praktyczne**

---

### 3) Multi-agent / multi-process concurrent access do SQLite poza WAL i `busy_timeout`

#### Twarde ograniczenia, które kształtują wszystkie wzorce

- **SQLite nadal obsługuje tylko jednego writera naraz na plik bazy.** To nie jest detal konfiguracyjny, tylko fundament modelu współbieżności SQLite. — **siła dowodów: praktyczne**
- **W WAL readers i writer mogą działać równolegle, ale długie read transactions blokują postęp checkpointów i mogą powodować wzrost pliku WAL.** — **siła dowodów: praktyczne**
- **Shared-cache jest przestarzały i odradzany; oficjalna dokumentacja mówi wprost, że większość przypadków jest lepiej obsługiwana przez WAL.** — **siła dowodów: praktyczne**

#### Najlepiej potwierdzone praktyki poza WAL i `busy_timeout`

##### A. Skracanie write transactions i jawne sterowanie początkiem transakcji

- **`BEGIN IMMEDIATE`** jest oficjalnie zalecanym sposobem, aby nie wpadać w `SQLITE_BUSY` w środku transakcji. Jeśli `BEGIN IMMEDIATE` się powiedzie, SQLite gwarantuje brak `SQLITE_BUSY` aż do `COMMIT` dla tej samej transakcji. — **siła dowodów: praktyczne**
- To wspiera ogólny wzorzec: **rezerwuj writer lock wcześnie dla ścieżek, które na pewno będą pisały, zamiast odkrywać konflikt dopiero w połowie pracy.** — **siła dowodów: praktyczne**

##### B. Rozdzielenie readerów od writerów

- **Read-only connections** są dobrze wspierane: można otwierać bazę np. z `mode=ro`, a dodatkowo `PRAGMA query_only=ON` blokuje operacje mutujące na poziomie connection. — **siła dowodów: praktyczne**
- `query_only` nie czyni bazy „naprawdę” read-only, ale chroni przed przypadkowymi zapisami z danego połączenia. — **siła dowodów: praktyczne**
- `immutable=1` istnieje, ale oficjalna dokumentacja wiąże go z naprawdę niezmiennym snapshotem/read-only use case; nie jest to bezpieczna opcja dla żywej, mutującej bazy. — **siła dowodów: praktyczne**

##### C. Świadome zarządzanie checkpointami i rozmiarem WAL

- `PRAGMA wal_autocheckpoint=N` steruje progiem auto-checkpointu; auto-checkpointy są zawsze `PASSIVE`. — **siła dowodów: praktyczne**
- SQLite domyślnie checkpointuje przy ~1000 stron WAL, ale oficjalna dokumentacja podkreśla, że aplikacje wymagające większej kontroli powinny same używać checkpoint API / pragma. — **siła dowodów: praktyczne**
- `FULL` i `RESTART` checkpointy próbują dokończyć pracę agresywniej niż `PASSIVE`; to przydatne, gdy trzeba zarządzać narastającym WAL, ale zwiększa napięcie z aktywnymi readerami. — **siła dowodów: praktyczne**
- `journal_size_limit` może pomóc ograniczać rozmiar pozostawionych plików WAL/journali po checkpointach. — **siła dowodów: praktyczne**

##### D. Dobór `synchronous`

- Oficjalna dokumentacja SQLite mówi wprost, że w WAL tryb **`synchronous=NORMAL` daje najlepszy balans bezpieczeństwa i wydajności dla większości aplikacji**; jest bezpieczny od strony spójności, ale może tracić ostatnio zatwierdzone transakcje po awarii zasilania/systemu. — **siła dowodów: praktyczne**
- `synchronous=FULL` zwiększa koszt commitów, ale poprawia trwałość po power loss. — **siła dowodów: praktyczne**

##### E. Foreign keys i ustawienia połączenia per proces

- **`PRAGMA foreign_keys=ON` musi być włączone per connection**, bo w SQLite FK są domyślnie wyłączone. W systemie multi-process to bardzo ważny szczegół operacyjny: brak jednego globalnego „przełącznika projektu”. — **siła dowodów: praktyczne**
- W Python `sqlite3`, `timeout`, `autocommit`/`isolation_level` i ostrożne zarządzanie transakcjami są realnymi dźwigniami zachowania pod lock contention. — **siła dowodów: praktyczne**

#### Connection pooling — co udało się potwierdzić, a czego nie

- **Nie udało się potwierdzić prostego konsensusu „pooling pomaga” albo „pooling szkodzi” dla file-based SQLite.** — **siła dowodów: praktyczne**
- Historycznie SQLAlchemy dla file-based SQLite wybierał `NullPool`, argumentując, że koszt otwierania połączeń jest niski, a coarse-grained locking sprawia, że agresywne ponowne używanie połączeń nie jest konieczne. — **siła dowodów: praktyczne**
- W 2025 SQLAlchemy zmienił domyślne zachowanie na `QueuePool` dla file-based SQLite, powołując się na obserwowalny negatywny wpływ `NullPool` na wydajność w pewnych workloadach. — **siła dowodów: praktyczne**
- **Wniosek:** pooling nie usuwa ograniczenia „one writer at a time”; jego wartość zależy od konkretnego workloadu, modelu drivera i kosztów otwierania/zamykania połączeń. Dokumentacja SQLite nie przedstawia pooling jako głównej odpowiedzi na write contention. — **siła dowodów: praktyczne**

#### Write queue / single writer / proxy / sharding

- **Write queue / dedicated writer process**: to bardzo logiczny wzorzec wynikający z modelu „one writer at a time”, ale nie znalazłem oficjalnej strony SQLite mówiącej wprost: „dla multi-process local workloads zawsze użyj single writer queue”. To jest **silna synteza z ograniczeń silnika**, nie dosłowna norma z jednego źródła. — **siła dowodów: spekulacja**
- **Proxy pattern** ma już mocniejsze oparcie w oficjalnych materiałach SQLite dla scenariuszy sieciowych: SQLite rekomenduje, by jeśli wiele maszyn ma korzystać z jednej bazy, silnik bazy działał przy pliku, a ruch zdalny szedł przez proxy. — **siła dowodów: praktyczne**
- **Sharding**: nie znalazłem oficjalnego „best practice” SQLite, który promowałby sharding jako domyślny wzorzec. To raczej architektoniczna ucieczka od limitu jednego writera, kiedy workload przestaje mieścić się w charakterystyce SQLite. — **siła dowodów: spekulacja**

#### Wniosek syntetyczny

Poza WAL i `busy_timeout`, najlepiej potwierdzone praktyki to:
- krótkie write transactions,
- `BEGIN IMMEDIATE` dla write pathów,
- read-only/query-only połączenia tam, gdzie można,
- per-connection enforcement (`foreign_keys`, transakcyjność, timeouty),
- aktywne zarządzanie checkpointami i rozmiarem WAL,
- unikanie shared-cache.

Pooling, write queue i sharding nie mają jednego wspólnego „community consensus”; ich sens jest bardziej workload-dependent. — **siła dowodów: praktyczne + spekulacja**

---

### 4) `CHECK` constraints vs application-level validation

#### Co udało się potwierdzić

- **W SQLite `CHECK` na poziomie kolumny i tabeli „in practice it makes no difference”.** — **siła dowodów: praktyczne**
- **`CHECK` jest weryfikowany przy `INSERT`/`UPDATE`, nie przy odczycie.** — **siła dowodów: praktyczne**
- **`CHECK` nie może zawierać subquery.** — **siła dowodów: praktyczne**
- **`CHECK` enforcement może być tymczasowo wyłączony przez `PRAGMA ignore_check_constraints=ON`.** — **siła dowodów: praktyczne**
- **`STRICT` tables (SQLite 3.37+) usztywniają typowanie, ale nie zastępują `CHECK`, `NOT NULL`, `UNIQUE` ani `FOREIGN KEY`.** — **siła dowodów: praktyczne**
- **`FOREIGN KEY` są domyślnie wyłączone per connection**, więc referencyjność w SQLite wymaga świadomego włączenia. — **siła dowodów: praktyczne**

#### Kiedy DB-level validation ma najmocniejsze uzasadnienie

- **Invarianty domenowe, które muszą obowiązywać wszystkich writerów**, niezależnie od procesu/agenta: zakresy liczb, dozwolone wartości enum, `NOT NULL`, unikalność, integralność referencyjna. — **siła dowodów: praktyczne**
- **Systemy wieloagentowe** wzmacniają sens DB-level constraints, bo walidacja tylko w jednej warstwie aplikacji nie chroni przed innym writerem, skryptem administracyjnym albo błędem innego procesu. — **siła dowodów: praktyczne**
- **SQLite bez dodatkowych constraintów jest liberalny typowo**, więc DB-level guardrails mają większą wartość niż w silnikach z bardziej restrykcyjnym systemem typów. — **siła dowodów: praktyczne**

#### Kiedy application-level validation pozostaje potrzebna

- **Walidacje zależne od kontekstu biznesowego**, stanu zewnętrznych usług, polityk czasowych, komunikatów UX i bogatych błędów użytkownika. — **siła dowodów: spekulacja**
- **Walidacje cross-row / cross-table**, które trudno lub nie da się elegancko zapisać w SQLite `CHECK` (szczególnie że `CHECK` nie przyjmuje subquery). — **siła dowodów: praktyczne**
- **Walidacja „miękka” lub ostrzegawcza**, która ma prowadzić do logów/warningów, a nie odrzucać zapis. — **siła dowodów: spekulacja**

#### Czy `CHECK` na każdym enum field to overkill?

- **Nie udało się potwierdzić tezy, że to overkill „by default”.** Raczej odwrotnie: dla małych, stabilnych i zamkniętych zbiorów wartości jest to bardzo typowy use case dla `CHECK`, szczególnie w SQLite. — **siła dowodów: praktyczne**
- **Overkill zaczyna się raczej tam, gdzie domena enum szybko się zmienia albo gdzie constraints utrudniają migracje bardziej niż pomagają jakości danych.** To nie jest jednak specyfika samego `CHECK`, tylko dynamiki domeny i narzędzi migracyjnych. — **siła dowodów: spekulacja**
- **Istotny caveat migracyjny:** w Alembic/SQLite nazwane `CHECK` constraints są lepiej obsługiwane niż nienazwane; unnamed `CHECK` mogą wypaść przy batch recreate. To oznacza, że problemem nie jest samo istnienie `CHECK`, lecz sposób ich prowadzenia i migracji. — **siła dowodów: praktyczne**

#### Wniosek syntetyczny

Najlepiej potwierdzony podział jest taki:
- **DB constraints** dla twardych invariantów współdzielonych przez wszystkich writerów,
- **application validation** dla semantyki biznesowej, UX i logiki wykraczającej poza możliwości/ergonomię SQLite.

`CHECK` dla enumów wygląda na **standardową, rozsądną praktykę**, nie na domyślny overkill. — **siła dowodów: praktyczne**

---

### 5) Index naming conventions — `idx_table_columns` vs inne

#### Co udało się potwierdzić

- **Nie ma jednego potwierdzonego standardu nazewniczego indeksów w SQLite community.** — **siła dowodów: praktyczne**
- **Dojrzałe projekty używają różnych stylów, ale wszystkie potrzebują nazw jednoznacznych i stabilnych.** — **siła dowodów: praktyczne**

#### Jak robią to dojrzałe projekty

- **Firefox**: makro tworzy nazwy w stylu `table_suffix`, np. `moz_places_url_hashindex`, `moz_places_hostindex`; dla indeksów unikalnych występują też sufiksy typu `uniqueindex`. To pokazuje wzorzec „table-prefixed descriptive suffix”, nie `idx_...`. — **siła dowodów: praktyczne**
- **Android ContactsProvider**: nazwy są jeszcze mniej jednorodne: `presenceIndex2`, `aggregation_exception_index1`, `raw_contacts_source_id_account_id_index`. To mocny sygnał, że praktyka produkcyjna nie sprowadza się do jednego prefixu. — **siła dowodów: praktyczne**
- **Django**: wymaga unikalnych nazw indeksów; jeśli nazwa nie jest podana, auto-generuje ją. Dokumentacja pokazuje też jawny wzorzec typu `'%(app_label)s_%(class)s_title_index'`. — **siła dowodów: praktyczne**

#### Co wydaje się najsilniej ugruntowane praktycznie

- **Nazwa indeksu powinna zawierać przynajmniej identyfikację tabeli i/lub kolumn/purpose.** — **siła dowodów: praktyczne**
- **Dla composite indexes dobrze, gdy nazwa odzwierciedla kolejność kolumn, bo kolejność ma znaczenie semantyczne i wydajnościowe.** — **siła dowodów: spekulacja**
- **Dla unique indexes warto, aby nazwa semantycznie zdradzała unikalność (`unique`, `uniq`, `ux`) albo była spójna z nazwami constraintów/autoindexów w projekcie.** — **siła dowodów: spekulacja**
- **Dla partial indexes najważniejsze jest, żeby nazwa była unikalna i rozróżniała indeksy o tym samym zestawie kolumn, ale innych predykatach.** Nie znalazłem jednak oficjalnego SQLite standardu nazwy partial indexów. — **siła dowodów: praktyczne**

#### Pole możliwości, nie jedna odpowiedź

Na podstawie źródeł widać co najmniej trzy sensowne rodziny nazewnicze:

1. **`idx_<table>_<col1>_<col2>` / `ux_<table>_<col1>_<col2>`**
   - zaleta: szybka rozpoznawalność typu obiektu
   - wada: nie jest to wzorzec oficjalnie uprzywilejowany przez SQLite ani potwierdzony jako dominujący w badanych projektach
   - **siła dowodów: spekulacja**

2. **`<table>_<col1>_<col2>_index` / `<table>_<col1>_<col2>_unique`**
   - zaleta: blisko stylu Django/Android
   - wada: dłuższe nazwy
   - **siła dowodów: praktyczne**

3. **`<table>_<semantic_suffix>`** (np. styl Firefoxa)
   - zaleta: krótsze, często czytelniejsze tam, gdzie indeks ma dobrze znany cel biznesowy (`guid_uniqueindex`, `hostindex`)
   - wada: wymaga lokalnej dyscypliny, bo mniej oczywiste bez znajomości domeny
   - **siła dowodów: praktyczne**

#### Wniosek syntetyczny

Nie ma mocnego dowodu, że `idx_table_columns` jest „standardem SQLite”. Najbardziej ugruntowana praktyka to **konwencja czytelna, przewidywalna i globalnie unikalna**, zwykle z nazwą tabeli i informacją o kolumnach albo celu indeksu. — **siła dowodów: praktyczne**

---

## Otwarte pytania / luki w wiedzy

- **Nie udało się potwierdzić jednego oficjalnego konsensusu społeczności SQLite** dla singular vs plural nazw tabel ani dla nazewnictwa indeksów.
- **Nie udało się potwierdzić mocnym, pierwotnym źródłem jednego najlepszego patternu connection poolingu** dla SQLite pod bardzo dużą konkurencją wielu procesów. Źródła praktyczne pokazują raczej, że to zależy od drivera i workloadu.
- **Nie znalazłem peer-reviewed benchmarku**, który bezpośrednio porównywałby: single writer queue vs wiele niezależnych writerów vs pooling vs sharding dla jednego pliku SQLite w realnym multi-process workloadzie 50–100+ procesów.
- **Homebrew nie dał się zweryfikować jako wyraźny, porównywalny case study schematu SQLite** w taki sposób jak Firefox/Android/Django.
- **Źródła rozjeżdżają się pośrednio w kwestii poolingu**: starsza praktyka (np. historyczne domyślne ustawienia SQLAlchemy) traktowała pooling jako mało potrzebny dla SQLite file DB, podczas gdy nowsze wydania SQLAlchemy raportują mierzalny zysk z `QueuePool` w części workloadów. To wygląda na różnicę nie „doktrynalną”, lecz zależną od środowiska wykonania i kosztów zarządzania połączeniami.
- **Nie udało się potwierdzić oficjalnego standardu nazewnictwa partial indexes** ani jawnej reguły dla rozróżniania unique/composite/partial indeksów poza ogólnym wymogiem unikalności i czytelności nazw.

---

## Źródła / odniesienia

### Oficjalne źródła SQLite

- [Appropriate Uses For SQLite](https://sqlite.org/whentouse.html) — oficjalne ograniczenia i „sweet spot” SQLite; kluczowe dla wniosku o jednym writerze i granicach skalowalności.
- [Isolation In SQLite](https://sqlite.org/isolation.html) — oficjalny opis serializacji write’ów i modelu izolacji.
- [Write-Ahead Logging](https://sqlite.org/wal.html) — źródło o współbieżności read/write w WAL, checkpointach i problemie długich readerów.
- [PRAGMA statements](https://sqlite.org/pragma.html) — źródło dla `synchronous`, `wal_autocheckpoint`, `query_only`, `journal_size_limit`.
- [Result and Error Codes](https://sqlite.org/rescode.html) — źródło dla praktyki `BEGIN IMMEDIATE` jako sposobu na unikanie `SQLITE_BUSY` w środku transakcji.
- [CREATE TABLE](https://sqlite.org/lang_createtable.html) — źródło dla semantyki `CHECK`, `UNIQUE`, oraz faktu, że `CHECK` nie może zawierać subquery.
- [STRICT Tables](https://www.sqlite.org/stricttables.html) — źródło dla `STRICT` tables i ich ograniczeń/korzyści.
- [SQLite Foreign Key Support](https://sqlite.org/foreignkeys.html) — źródło dla faktu, że foreign keys są domyślnie wyłączone per connection.
- [Opening A New Database Connection](https://sqlite.org/c3ref/open.html) — źródło dla `mode=ro`, URI options i trybów otwierania połączeń.
- [SQLite Shared-Cache Mode](https://sqlite.org/sharedcache.html) — źródło dla tezy, że shared-cache jest obsolete/discouraged.
- [SQLite Over a Network, Caveats and Considerations](https://sqlite.org/useovernet.html) — źródło dla proxy pattern w scenariuszach zdalnych i argumentu „DB engine przy pliku”.

### Python / driver / praktyka połączeń

- [Python `sqlite3` documentation](https://docs.python.org/3/library/sqlite3.html) — źródło dla `timeout`, `check_same_thread`, `isolation_level`, `autocommit` i zachowania połączeń w Pythonie.
- [SQLAlchemy SQLite 1.3 docs](https://docs.sqlalchemy.org/en/13/dialects/sqlite.html) — historyczna praktyka: file-based SQLite + `NullPool`, argument o niskim koszcie połączeń i coarse-grained locking.
- [SQLAlchemy SQLite 2.1 changelog](https://docs.sqlalchemy.org/en/21/changelog/changelog_20.html) — nowsza zmiana domyślnego poola na `QueuePool` dla file-based SQLite z powodu mierzalnego wpływu wydajnościowego.
- [SQLAlchemy SQLite 2.1 dialect docs](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html) — dodatkowy kontekst o lockach i transaction control w SQLite.

### Migracje i narzędzia

- [Django migrations](https://docs.djangoproject.com/en/6.0/topics/migrations/) — źródło dla wzorca recreate-table przy SQLite i DDL transactions.
- [Django model indexes](https://docs.djangoproject.com/en/6.0/ref/models/indexes/) — źródło dla wymogu unikalnych nazw indeksów i przykładowego stylu nazewniczego.
- [Django constraints](https://docs.djangoproject.com/en/6.0/ref/models/constraints/) — źródło dla wymogu unikalnych nazw constraintów.
- [Django raw SQL / table names](https://docs.djangoproject.com/en/6.0/topics/db/sql/) — źródło dla auto-generacji nazw tabel typu `app_label_model`.
- [Alembic: Running “Batch” Migrations for SQLite](https://alembic.sqlalchemy.org/en/latest/batch.html) — źródło dla batch mode oraz caveatów named vs unnamed `CHECK` constraints.
- [Dbmate README](https://github.com/amacneil/dbmate) — źródło dla `schema_migrations`, timestamp-versioned plain SQL, atomic transactions i `schema.sql` dump.
- [Flyway schema history table](https://documentation.red-gate.com/fd/flyway-schema-history-table-273973417.html) — źródło dla audit trail, checksumów i wykrywania dryfu migracji.
- [Flyway SQLite support](https://documentation.red-gate.com/flyway/reference/database-driver-reference/sqlite) — źródło dla wsparcia SQLite i ograniczenia „no concurrent migration”.
- [Goose documentation](https://pressly.github.io/goose/documentation/cli-commands/) — źródło dla dojrzałego wzorca katalogu migracji i wersjonowanych plików.

### Przykłady dojrzałych projektów open-source

- [Firefox Places tables (`nsPlacesTables.h`)](https://searchfox.org/firefox-main/source/toolkit/components/places/nsPlacesTables.h) — realny schemat Firefoxa; użyte do oceny stylu nazw tabel.
- [Firefox Places indexes (`nsPlacesIndexes.h`)](https://searchfox.org/firefox-main/source/toolkit/components/places/nsPlacesIndexes.h) — realne nazwy indeksów Firefoxa.
- [Android ContactsProvider `ContactsDatabaseHelper.java`](https://android.googlesource.com/platform/packages/providers/ContactsProvider/%2B/master/src/com/android/providers/contacts/ContactsDatabaseHelper.java) — realny przykład dużego schematu SQLite, nazw tabel, indeksów i code-based upgrade path.
- [Android `SQLiteOpenHelper.java`](https://android.googlesource.com/platform/frameworks/base/%2B/HEAD/core/java/android/database/sqlite/SQLiteOpenHelper.java) — oficjalna implementacja / dokumentacja wzorca `onUpgrade`, `onConfigure`, transakcyjności migracji.

