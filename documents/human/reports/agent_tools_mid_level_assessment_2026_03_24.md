# Assessment: Dlaczego kod narzędzi agentów to poziom mid, nie senior

**Data:** 2026-03-24  
**Adresat:** Architect  
**Autor:** Codex  
**Zakres:** warstwa `tools/` i `core/` związana z AgentBus, runnerem, hookami, parserem transcriptów i interfejsami CLI/API

---

## Executive Summary

**Ocena końcowa:** `mid+`, miejscami `senior-`, ale **nie stabilny senior**.

To nie jest kod juniora. Widać:
- świadomy podział na warstwy domenowe, repozytoria i adapter legacy,
- myślenie o kompatybilności wstecznej,
- transaction support,
- szeroki zestaw testów jednostkowych i integracyjnych,
- realne myślenie operacyjne: trace sesji, tool calls, runner, hooki, API.

Jednocześnie ten kod nie domyka jeszcze jakości, której oczekuje się od seniora. Główna różnica nie dotyczy "ładności" kodu, tylko **spójności kontraktów między warstwami**. Senior nie tylko projektuje dobrą strukturę, ale pilnuje, żeby granice między modułami były szczelne, a system był przewidywalny w negatywnych scenariuszach. Tutaj kilka takich granic nadal przecieka.

W skrócie:
- **architektura i intencja projektowa:** wyraźnie powyżej mida,
- **egzekucja end-to-end i domknięcie inwariantów:** jeszcze mid,
- **operacyjność i safety:** mid,
- **testy:** mid+.

Dlatego klasyfikacja `mid+` jest bardziej defensible niż `senior`.

---

## Dlaczego to nie jest junior

### 1. Autor rozumie separację odpowiedzialności

Kod nie jest zlepkiem skryptów. Widać świadomą próbę rozdzielenia:
- modelu domenowego w `core/entities/messaging.py`,
- persystencji w `core/repositories/*.py`,
- warstwy kompatybilności w `core/mappers/legacy_api.py`,
- adaptera/entrypointu w `tools/lib/agent_bus.py`,
- interfejsów dostępowych w `tools/agent_bus_cli.py` i `tools/agent_bus_server.py`.

To jest ważny sygnał dojrzałości. Junior zwykle buduje narzędzie "od końca", od CLI albo od SQL-a. Tutaj jest odwrotnie: widać próbę wprowadzenia warstw i utrzymania starego API bez rozrywania całego systemu.

### 2. Widać myślenie migracyjne, nie tylko feature coding

`LegacyAPIMapper` nie jest przypadkowym helperem. To jest świadoma próba utrzymania starego kontraktu przy jednoczesnym wprowadzaniu modelu domenowego. Tego typu decyzje są typowe dla kogoś, kto rozumie koszt refaktoru w systemie żyjącym.

Przykłady:
- mapowanie `flag_human -> escalation`,
- mapowanie `info -> direct`,
- mapowanie legacy statusów sugestii do nowych enumów.

To nie jest poziom junior, bo junior zwykle wybiera jedno z dwóch:
- albo przepisuje wszystko naraz,
- albo zostawia chaos bez warstwy przejściowej.

Tutaj jest świadomy kompromis.

### 3. Transaction support został potraktowany jako realny problem architektoniczny

`AgentBus.transaction()` i przekazywanie współdzielonego połączenia do repozytoriów pokazują, że autor rozumie atomowość jako cechę systemu, a nie detal implementacyjny.

To ważne, bo system ma operacje wieloetapowe:
- sugestia -> backlog -> update statusu,
- claim/unclaim taska,
- bulk update w CLI.

Junior często dodałby `conn.commit()` po każdej instrukcji. Tutaj jest próba kontrolowania transakcji na poziomie use case'a.

### 4. Testy są realnym elementem pracy, a nie dodatkiem

Repo ma sensowny zestaw testów dla:
- `AgentBus`,
- CLI,
- API FastAPI,
- parsera `.jsonl`,
- runnera,
- hooków `pre_tool_use` i `post_tool_use`,
- renderowania i `session_init`.

To oznacza, że autor nie pracuje wyłącznie intuicyjnie. Dla mida to jest bardzo dobry sygnał.

### 5. Widać myślenie o produkcyjnym użyciu

Ta warstwa nie tylko "działa lokalnie". Ona ma:
- rejestr instancji agentów,
- heartbeat,
- claim tasków,
- session trace,
- logowanie conversation events,
- hooki wpinane w cykl życia agenta,
- API do odczytu danych przez człowieka.

To jest produktowe myślenie, nie tylko implementacja funkcji.

---

## Dlaczego to jeszcze nie jest senior

Kluczowy argument: senior-level implementation nie kończy się na dobrej strukturze katalogów. Senior domyka **spójność kontraktów**, **negatywne scenariusze**, **safety boundaries** i **operacyjną przewidywalność**. W tym kodzie właśnie tam widać największe braki.

### 1. System stanów nie jest domknięty end-to-end

Najmocniejszy przykład to `messages.status`.

Warstwa runnera i `AgentBus` wprowadza stan `claimed`, ale model domenowy wiadomości zna tylko:
- `unread`,
- `read`,
- `archived`.

To oznacza, że jedna warstwa zapisuje stan, którego druga warstwa nie umie odczytać bez błędu.

**Evidence:**
- `tools/lib/agent_bus.py` zapisuje `status = 'claimed'` w `claim_task()`
- `core/entities/messaging.py` nie ma `MessageStatus.CLAIMED`
- `core/repositories/message_repo.py` mapuje `row["status"]` bez fallbacku

To nie jest błąd "pojedynczej literówki". To jest błąd jakości architektonicznej: **granica między warstwą domenową a operacyjną nie ma wspólnej definicji inwariantu**.

Senior zwykle zrobiłby jedno z trzech:
- dodałby `claimed` do oficjalnego state machine,
- rozdzieliłby `claim` od `status` do osobnego pola/encji,
- albo jasno oznaczyłby, że runner działa poza domain model i nie może być czytany przez repo bez adaptera.

Tutaj tego domknięcia nie ma.

**Wniosek dla architekta:** autor umie budować warstwy, ale jeszcze nie pilnuje ich pełnej spójności.

### 2. Inwarianty są rozproszone, a polityka błędów jest niespójna

W tej warstwie są różne strategie zachowania:
- czasem fail-fast,
- czasem silent ignore,
- czasem fallback do defaultu,
- czasem mapowanie legacy,
- czasem brak jawnej decyzji.

Przykłady:
- `add_suggestion()` przy nieznanym typie robi fallback do `observation`,
- `update_backlog_status()` przy nieznanym statusie po prostu wychodzi,
- hooki łapią prawie wszystkie wyjątki i zapisują je cicho do plików,
- repozytoria próbują tłumaczyć wyjątki SQLite na domenowe,
- jednocześnie część warstwy `AgentBus` dalej robi direct SQL i omija te same zasady.

To jest bardzo charakterystyczne dla mocnego mida: dobra intuicja, ale jeszcze brak jednej spójnej polityki na granicach systemu.

Senior-level kod zwykle ma tu jasną odpowiedź:
- gdzie jesteśmy strict,
- gdzie wspieramy legacy,
- gdzie degradujemy graceful,
- gdzie błąd ma się zatrzymać natychmiast.

Tutaj to jest jeszcze miks wzorców.

### 3. Instrumentacja jest użyteczna, ale nie ma single source of truth

`tool_calls` są logowane:
- live przez `tools/hooks/post_tool_use.py`,
- post-session przez `tools/hooks/on_stop.py` + `tools/jsonl_parser.py`.

Obie ścieżki zapisują do tej samej tabeli i nie ma deduplikacji.

Konsekwencja:
- statystyki narzędzi mogą być zawyżone,
- trace sesji może być niespójny,
- człowiek oglądający raport nie ma pewności, czy widzi "raw facts" czy "facts + replay".

To jest bardzo ważny sygnał poziomu. Mid buduje telemetry. Senior pilnuje, żeby telemetry miało **jeden kontrakt semantyczny**.

Innymi słowy: tu jest dobra intencja i dobra energia implementacyjna, ale nadal brakuje ostatecznego pytania:
"która ścieżka jest źródłem prawdy?"

### 4. Safety gate jest praktyczny, ale nadal za szeroki

`pre_tool_use.py` słusznie normalizuje input i blokuje część niebezpiecznych komend. To jest dobra decyzja projektowa. Problem w tym, że allowlista dopuszcza też komendy destrukcyjne:
- `rm`,
- `del`,
- `rmdir`.

Regexy blokują tylko część przypadków skrajnych, np. `rm -rf /`, ale nie blokują wielu realnie niebezpiecznych scenariuszy roboczych, np. kasowania katalogu projektu albo tymczasowych artefaktów, które w praktyce mogą być ważne.

To nie jest detal bezpieczeństwa. W tej warstwie hook pełni rolę approval gate. Jeśli gate jest zbyt szeroki, to cały model zaufania staje się mniej wiarygodny.

Senior-level podejście byłoby bardziej rygorystyczne:
- deny-by-default dla komend destrukcyjnych,
- osobna allowlista dla "read-only" i "mutating",
- albo dedykowane narzędzie zamiast przepuszczania `rm`.

Tutaj widać pragmatyzm, ale jeszcze nie pełną dyscyplinę bezpieczeństwa.

### 5. Runner jest sensowny, ale nie jest jeszcze operacyjnie szczelny

`mrowisko_runner.py` rozwiązuje realny problem:
- rejestruje instancję,
- robi heartbeat,
- atomowo claimuje taski,
- odpala subprocess,
- loguje koszt i liczbę tur.

To jest dobry fundament. Problem pojawia się w zachowaniu runtime:
- timeout jest oparty o `proc.wait(timeout=TIMEOUT_SEC)`,
- ale dopiero po zakończeniu pętli czytającej `proc.stdout`.

Jeżeli proces przestanie sensownie odpowiadać, ale nadal utrzyma otwarty stdout, kontrola czasu może nie zadziałać tak, jak intuicyjnie oczekujemy. To oznacza, że mechanizm "mam timeout" nie jest w pełni równoważny "na pewno się nie zawiesimy".

Senior-level różni się tutaj od mida tym, że nie zakłada, iż "normalna ścieżka" wyczerpuje problem operacyjny.

### 6. Testy są szerokie, ale wciąż bardziej potwierdzają implementację niż kontrakty między modułami

To jest ważne rozróżnienie.

Testy są liczne i to trzeba zaliczyć na plus. Natomiast z perspektywy dojrzałości architektonicznej brakuje testów na granicach:
- co się dzieje, gdy wiadomość ma status `claimed` i przechodzi przez repo,
- czy live logging i parsing transcriptu nie dublują `tool_calls`,
- czy runner timeout faktycznie zrywa zawieszony stream,
- czy allowlista hooka nie przepuszcza komend, które powinny wymagać explicit approval,
- czy polityka legacy/fail-fast jest spójna dla całego `AgentBus`.

To jest typowy profil `mid+`:
- testy istnieją,
- obejmują dużo scenariuszy,
- ale jeszcze nie łapią wszystkich failure modes wynikających z przecięcia modułów.

Senior zwykle ma obsesję właśnie na punkcie tych przecięć.

### 7. Część kodu nadal nosi ślady "adaptacji w locie"

Najbardziej widać to w `AgentBus`.

To jest jednocześnie:
- adapter do nowego domain modelu,
- warstwa legacy API,
- warstwa direct SQL dla sesji, trace i instancji,
- orchestrator use case'ów,
- częściowo façade dla CLI/API.

To jeszcze nie jest zły kod. To jest nawet praktyczny kod przejściowy. Ale właśnie "przejściowość" jest tutaj słowem kluczowym.

Senior-level implementacja zwykle ma w takim miejscu już wyraźne rozdzielenie:
- które use case'y są domenowe,
- które infrastrukturalne,
- które tylko legacy compatibility,
- a które powinny zostać wydzielone do osobnych serwisów.

Tutaj widać architektoniczną intencję, ale jeszcze nie pełne domknięcie refaktoru.

---

## Najmocniejsza teza do obrony przed architektem

Najuczciwsza klasyfikacja tego kodu brzmi:

> **Autor potrafi projektować i budować architekturę na poziomie wyraźnie powyżej juniora, ale jeszcze nie utrzymuje w sposób konsekwentny systemowych inwariantów na wszystkich granicach modułów.**

To jest właśnie definicja mocnego mida:
- dobrze widzi strukturę,
- potrafi wdrożyć sensowne wzorce,
- rozumie trade-offy,
- ale jeszcze od czasu do czasu zostawia niespójność między warstwami, szczególnie w operational edge cases.

Senior-level byłby tu uzasadniony dopiero wtedy, gdy te granice byłyby domknięte:
- wspólny model stanów,
- jedna semantyka telemetry,
- spójna polityka błędów,
- szczelniejszy safety gate,
- testy na przecięciach modułów.

---

## Kontrargument na wypadek opinii: "Ale przecież architektura jest seniorowa"

To prawda tylko częściowo.

Architektura jako **zamiar** jest miejscami seniorowa:
- domain model,
- repositories,
- mapper legacy,
- transaction-aware adapter,
- testability,
- operacyjne trace.

Ale architekt ocenia nie tylko zamiar, tylko **jakość domknięcia systemu**.

Senior-level implementation oznacza, że:
- warstwa A nie zapisuje stanów, których warstwa B nie umie czytać,
- telemetry nie ma dwóch równoległych źródeł prawdy bez deduplikacji,
- safety gate nie wpuszcza destrukcyjnych przypadków przez zbyt szeroką allowlistę,
- timeout naprawdę ogranicza zawieszenia,
- testy pilnują kontraktów między modułami, nie tylko zachowania pojedynczych funkcji.

Właśnie tych cech tu jeszcze brakuje.

Dlatego poprawna ocena brzmi nie "to nie jest senior, bo kod nieładny", tylko:

> **to jeszcze nie jest senior, bo kluczowe kontrakty systemowe nie są w pełni zintegrowane end-to-end.**

---

## Rekomendacja klasyfikacyjna

### Rekomendowana etykieta

**`mid+`**

To jest najlepsza etykieta, bo:
- nie zaniża realnej jakości architektury,
- nie myli potencjału z gotowością senior-level,
- dobrze oddaje profil: silny projektowo, jeszcze nierówny w domykaniu granic systemu.

### Czego brakuje do senior

Żeby ten sam obszar uczciwie sklasyfikować jako `senior`, oczekiwałbym następujących zmian:

1. Ujednolicenie modelu stanów wiadomości
   - `claimed` musi być albo częścią domain modelu, albo zostać wydzielony poza `status`.

2. Jedna strategia dla telemetry
   - albo live logging jest source of truth,
   - albo transcript replay jest source of truth,
   - albo istnieje jawna deduplikacja i semantyka obu ścieżek.

3. Spójna polityka błędów i kompatybilności
   - jasno zdefiniowane: gdzie fail-fast, gdzie fallback, gdzie silent ignore.

4. Twardszy safety model
   - destrukcyjne komendy nie powinny być auto-allow przez sam prefix.

5. Testy na granicach modułów
   - szczególnie dla stanów pośrednich, duplikacji logów, timeoutów i bezpieczeństwa.

Po domknięciu tych punktów ten obszar można już bronić jako `senior-` lub `senior`, zależnie od jakości finalnej egzekucji.

---

## Final Position

Jeśli raport ma służyć jako stanowisko wobec architekta, proponuję bronić następującej formuły:

> Kod narzędzi agentów jest na poziomie **mocnego mida (`mid+`)**.  
> Nie jest juniorem, bo zawiera świadomą architekturę, transakcje, kompatybilność wsteczną, testy i myślenie operacyjne.  
> Nie jest jeszcze seniorem, bo w kilku krytycznych miejscach nie domyka kontraktów między warstwami: state machine, telemetry, safety i edge-case operability.

To jest ocena technicznie uczciwa, łatwa do obrony i zgodna z tym, co faktycznie widać w kodzie.

---

## Appendix: główne referencje w kodzie

- `tools/lib/agent_bus.py`
- `tools/agent_bus_cli.py`
- `tools/agent_bus_server.py`
- `tools/mrowisko_runner.py`
- `tools/jsonl_parser.py`
- `tools/hooks/pre_tool_use.py`
- `tools/hooks/post_tool_use.py`
- `tools/hooks/on_stop.py`
- `core/entities/messaging.py`
- `core/repositories/message_repo.py`
- `core/repositories/suggestion_repo.py`
- `core/mappers/legacy_api.py`
- `tests/test_agent_bus.py`
- `tests/test_agent_bus_cli.py`
- `tests/test_agent_bus_server.py`
- `tests/test_jsonl_parser.py`
- `tests/test_mrowisko_runner.py`
- `tests/test_post_tool_use.py`
- `tests/test_pre_tool_use.py`

**Nota metodologiczna:** raport opiera się na przeglądzie kodu i istniejących testów. W tym środowisku nie było możliwe uruchomienie testów, bo brak aktywnego interpretera Python.
