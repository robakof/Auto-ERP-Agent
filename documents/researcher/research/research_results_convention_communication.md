# Research: Konwencje komunikacji agent-agent w systemach multi-agent

Data: 2026-03-25

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 5 najważniejszych wniosków

1. **Klasyczne ACL-e (FIPA ACL, KQML, JADE) standaryzują bogaty “envelope” wiadomości, ale nowoczesne frameworki LLM-agentowe (AutoGen, CrewAI) upraszczają go do: typ/akcja wiadomości + nadawca + odbiorca/cel + payload + kontekst korelacyjny.** W praktyce to właśnie te 4–6 rodzin pól powtarza się najczęściej między paradygmatami. — siła dowodów: **praktyczne**
2. **Najszersze katalogi performatives istnieją w FIPA i KQML, ale nawet FIPA nie wymaga większości z nich.** W praktyce stale wraca mały rdzeń: inform/report, request/delegate, query/ask, propose, accept/reject/refuse, error/not-understood/failure, notify/publish. Reszta bywa potrzebna tylko w wyspecjalizowanych protokołach. — siła dowodów: **praktyczne + spekulacja (w części “co jest naprawdę użyteczne”)**
3. **Dojrzałe systemy redukują narastający backlog głównie przez deduplikację, grupowanie powiązanych zdarzeń, suppress/inhibit, batch triage i wygaszanie nieaktywnych elementów z wyjątkami.** Twardych dowodów na to, że “numeric priority decay” jest dominującą praktyką, nie udało się potwierdzić. — siła dowodów: **praktyczne**, częściowo **empiryczne**
4. **Najlepiej udokumentowane antywzorce komunikacyjne to przeciążanie węzłów (overloader/overloaded), izolowane agenty, zbyt dużo back-and-forth i pętle delegacji.** Część starszej literatury wiąże je z gorszym QoS i dłuższym czasem odpowiedzi; nowsze frameworki opisują je jako praktyczne problemy operacyjne. — siła dowodów: **empiryczne + praktyczne**
5. **Deduplikacja nie oznacza “wyrzucania duplikatów”.** W literaturze bug-reportowej i w narzędziach operacyjnych powtarza się wzorzec: łączyć elementy w jeden rekord roboczy, ale zachowywać dodatkowy kontekst, historię i sygnały diagnostyczne. — siła dowodów: **empiryczne + praktyczne**

## Wyniki per pytanie

### 1) Standardy formatu wiadomości w MAS

#### Co standaryzują klasyczne ACL-e

- **FIPA ACL definiuje bogaty model wiadomości obejmujący m.in.** `performative`, `sender`, `receiver`, `reply-to`, `content`, `language`, `encoding`, `ontology`, `protocol`, `conversation-id`, `reply-with`, `in-reply-to`, `reply-by`. W samej specyfikacji tylko część pól jest obowiązkowa kontekstowo; formalnie najsilniej wymagany jest `performative`, a pozostałe mogą być pominięte w szczególnych przypadkach. W praktyce jednak pełniejsze envelope są normą w implementacjach interoperacyjnych. — **siła dowodów: praktyczne; pewność: wysoka**
- **FIPA rozdziela warstwę transportowo-kontekstową od warstwy semantycznej.** `ontology`, `language` i `encoding` opisują, jak rozumieć treść; `conversation-id`, `reply-with`, `in-reply-to`, `reply-by` służą do korelacji i zarządzania dialogiem; `protocol` wskazuje, w jakim protokole interakcji wiadomość występuje. — **siła dowodów: praktyczne; pewność: wysoka**
- **JADE nie tworzy osobnego standardu — operacjonalizuje FIPA ACL.** Dokumentacja i API JADE pokazują, że odpowiedzi dziedziczą kluczowe pola konwersacyjne (np. `language`, `ontology`, `protocol`, `conversation-id`, `in-reply-to`, `reply-with`) przez mechanizmy typu `createReply()`. To ważny sygnał praktyczny: bogaty envelope ma sens głównie wtedy, gdy framework aktywnie pomaga utrzymać spójność konwersacji. — **siła dowodów: praktyczne; pewność: wysoka**
- **KQML również używa wiadomości z performative na początku i par keyword/value dalej.** Często pojawiają się `sender`, `receiver`, `reply-with`, `in-reply-to`, `language`, `ontology`, `content`. W porównaniu z FIPA, KQML historycznie eksponuje bardzo szeroki katalog performatives i silniej splata format z warstwą speech-act. — **siła dowodów: praktyczne; pewność: wysoka**

#### Jak standaryzują to nowoczesne frameworki agentów LLM

- **AutoGen upraszcza warstwę ACL.** W dokumentacji core wiadomości są „jedynym środkiem komunikacji”, ale mają być po prostu serializowalnymi dataclass/Pydantic models. Dla `TextMessage` minimalnie wymagane są `source` i `content`; inne pola (`id`, `metadata`, `created_at`, `models_usage`) są pomocnicze, nie semantycznie centralne. Semantyka przepływu przenosi się z performative do: typu wiadomości, routingu, topiców/subskrypcji oraz jawnych handoffów (`target`, opcjonalny `context`). — **siła dowodów: praktyczne; pewność: wysoka**
- **CrewAI nie ma ogólnego ACL w stylu FIPA/KQML.** Zamiast tego standaryzuje współpracę przez konkretne narzędzia i obiekty zadań. Współpraca agent-agent jest modelowana przez operacje typu „delegate work” i „ask question”, które przyjmują proste pola: `task/question`, `context`, `coworker`. Równolegle `Task` niesie `description`, `expected_output`, `agent`, `context` itd. — **siła dowodów: praktyczne; pewność: wysoka**
- **Różnica paradygmatyczna jest wyraźna:** klasyczne MAS standaryzują **semantykę wypowiedzi** na poziomie wiadomości, a nowoczesne frameworki częściej standaryzują **strukturę danych, routing i orkiestrację**. — **siła dowodów: praktyczne + spekulacja (synteza); pewność: wysoka**

#### Jakie pola wracają najczęściej między systemami

Na poziomie syntezy, niezależnie od epoki i frameworka, powtarza się następujący rdzeń pól:

1. **Typ wiadomości / performative / akcja** — np. `request`, `inform`, `delegate`, `ask`, `handoff`. — **siła dowodów: praktyczne**
2. **Nadawca (`sender`, `source`)** — identyfikacja autora komunikatu. — **siła dowodów: praktyczne**
3. **Odbiorca lub cel (`receiver`, `target`, `coworker`)** — adresat bezpośredni lub cel handoffu. — **siła dowodów: praktyczne**
4. **Payload (`content`, `task`, `question`, `context`)** — właściwa treść. — **siła dowodów: praktyczne**
5. **Korelacja konwersacji (`conversation-id`, `reply-with`, `in-reply-to`, powiązanie task-context)** — wiązanie odpowiedzi, follow-upów i wątków. — **siła dowodów: praktyczne**
6. **Atrybuty czasowo-lifecycle’owe (`reply-by`, `created_at`)** — deadline lub czas utworzenia. — **siła dowodów: praktyczne**
7. **Warstwa interpretacji (`ontology`, `language`, `protocol`)** — silna w FIPA/KQML, słabsza i często zastępowana schematem danych w frameworkach LLM. — **siła dowodów: praktyczne**
8. **Metadane operacyjne (`metadata`, fingerprint, usage, trace`)** — rzadziej formalizowane w klasycznych ACL-ach, ale mocno obecne w nowoczesnych systemach produkcyjnych. — **siła dowodów: praktyczne + spekulacja (synteza między domenami)**

#### Najważniejszy trade-off

- **Bogaty envelope** ułatwia interoperacyjność, śledzenie konwersacji i jawne protokoły, ale zwiększa koszt implementacji i ryzyko „ceremonialnej” złożoności. — **siła dowodów: praktyczne + spekulacja**
- **Minimalny envelope** upraszcza implementację i jest zgodny z praktyką nowoczesnych frameworków, ale bez jawnej korelacji i routingu łatwo prowadzi do osieroconych odpowiedzi, trudnego debugu i duplikatów semantycznych. — **siła dowodów: praktyczne + spekulacja**

---

### 2) Ontologie komunikacji i speech acts

#### Jakie ontologie / semantyki istnieją

- **Mentalistyczna / speech-act-based** — klasyczny model KQML i FIPA ACL: wiadomość ma wyrażać akt mowy i odnosi się do stanów mentalnych typu belief/intention/commitment nadawcy i odbiorcy. — **siła dowodów: praktyczne + empiryczne; pewność: wysoka**
- **Commitment-based / social semantics** — semantyka przeniesiona z „co agent myśli” na publicznie obserwowalne zobowiązania między stronami. Literatura commitment-based powstała m.in. dlatego, że w otwartych systemach trudno zakładać dostęp do prawdziwych stanów mentalnych heterogenicznych agentów. — **siła dowodów: empiryczne; pewność: wysoka**
- **Protocol-based / conversation-based** — znaczenie wiadomości wynika przede wszystkim z miejsca w protokole i możliwych przejść dialogu, a nie z introspekcji stanów mentalnych. — **siła dowodów: empiryczne; pewność: wysoka**

#### Co jest dobrze ugruntowane

- **Krytyka “czystej” semantyki speech-act jest dobrze znana w literaturze.** Kilka źródeł podkreśla, że trudno nadać satysfakcjonującą, obliczalną semantykę aktom mowy, jeśli odwołują się one do nieobserwowalnych stanów wewnętrznych agentów. To jeden z głównych powodów rozwoju podejść commitment-based i protocol-based. — **siła dowodów: empiryczne; pewność: wysoka**
- **FIPA Communicative Act Library jest bogata, ale sama specyfikacja nie wymusza używania większości aktów.** Oprócz `not-understood` i tego, co potrzebne do zarządzania agentami, biblioteka działa raczej jako katalog dostępnych opcji niż minimalny obowiązkowy zestaw. — **siła dowodów: praktyczne; pewność: wysoka**
- **KQML ma jeszcze szerszy, historycznie bardzo ekspansywny zestaw performatives** (np. `ask-if`, `ask-all`, `tell`, `insert`, `achieve`, `advertise`, `broker`, `recruit`, `recommend`, `standby`, `next`, `rest`, `discard`). To pokazuje, jak łatwo ontologia komunikacji może rozrosnąć się ponad to, co większość implementacji realnie potrzebuje. — **siła dowodów: praktyczne; pewność: wysoka**

#### Które kategorie wiadomości wydają się naprawdę użyteczne w praktyce

To nie jest jednoznacznie rozstrzygnięte w jednym benchmarku cross-framework; poniżej jest **synteza** z klasycznych standardów i nowoczesnych frameworków:

1. **Inform / report / observation** — przekazywanie faktu, wyniku, stanu lub obserwacji. Występuje praktycznie wszędzie. — **siła dowodów: praktyczne; pewność: wysoka**
2. **Request / task / delegate** — zlecenie działania, często najważniejszy typ wiadomości roboczej. — **siła dowodów: praktyczne; pewność: wysoka**
3. **Query / ask** — pytanie o stan, referencję, dane lub opinię. — **siła dowodów: praktyczne; pewność: wysoka**
4. **Propose / suggest / bid** — propozycja planu, rozwiązania, oferty lub ścieżki działania. — **siła dowodów: praktyczne; pewność: wysoka**
5. **Accept / reject / refuse** — zamknięcie pętli decyzyjnej; przydatne zwłaszcza gdy agent może odmówić lub zaakceptować warunkowo. — **siła dowodów: praktyczne; pewność: wysoka**
6. **Error / failure / not-understood / escalate** — sygnalizowanie niepowodzenia, niezrozumienia lub potrzeby eskalacji. — **siła dowodów: praktyczne; pewność: wysoka**
7. **Notify / publish / broadcast** — sygnały publikacyjne, asynchroniczne, do wielu odbiorców. — **siła dowodów: praktyczne; pewność: średnia-wysoka**
8. **Acknowledge / ready / handoff accepted** — nie zawsze konieczne, ale użyteczne tam, gdzie trzeba odróżnić “odebrałem” od “wykonałem”. — **siła dowodów: praktyczne + spekulacja; pewność: średnia**

#### Co wygląda na over-engineering poza wyspecjalizowanymi protokołami

- **Rozróżnianie wielu subtelnych wariantów pytań i odpowiedzi** (np. `query-if` vs `query-ref`, `confirm` vs `disconfirm`) bywa cenne w formalnych protokołach, ale w praktyce często może być zakodowane w payloadzie lub schemacie danych zamiast w osobnym performative. — **siła dowodów: praktyczne + spekulacja; pewność: średnia**
- **Performatives brokerowe/facylitacyjne** (`broker`, `recruit`, `recommend`, `proxy`, `propagate`) są sensowne, gdy architektura naprawdę ma pośredników lub rynki usług; poza tym często pozostają nieużywanym ciężarem poznawczym. — **siła dowodów: praktyczne + spekulacja; pewność: średnia**
- **Akty sterujące wieloetapowym streamingiem** (`standby`, `next`, `rest`, `discard`) wyglądają jak over-engineering, jeśli system nie ma realnego strumieniowania odpowiedzi lub złożonych protokołów sekwencyjnych. — **siła dowodów: praktyczne + spekulacja; pewność: średnia**

#### Najważniejszy trade-off

- **Ontologia bogata semantycznie** daje większą jawność i możliwość formalnej weryfikacji protokołów. — **siła dowodów: empiryczne + praktyczne**
- **Ontologia mała i operacyjna** jest zwykle łatwiejsza do wdrożenia, lepiej pasuje do routingu zdarzeń i schematów danych, ale mniej nadaje się do formalnego modelowania złożonych kontraktów komunikacyjnych. — **siła dowodów: praktyczne + spekulacja**

---

### 3) Zarządzanie backlogiem obserwacji / sugestii

#### Co jest najmocniej potwierdzone w praktyce

- **Deduplikacja po stabilnym kluczu/fingerprint to praktyka pierwszego rzędu.** PagerDuty używa `incident key` / `dedup_key`, Sentry używa `fingerprint`, Alertmanager deduplikuje i grupuje alerty. To najczyściej potwierdzony wzorzec ograniczania szumu. — **siła dowodów: praktyczne; pewność: wysoka**
- **Grupowanie powiązanych elementów jest równie ważne jak dedup.** W systemach alertowych chodzi nie tylko o identyczne duplikaty, ale o grupowanie alertów powiązanych czasowo, topologicznie lub przez wspólną przyczynę. Alertmanager wspiera grouping/silencing/inhibition; PagerDuty grupuje alerty w incydent; prace badawcze nad agregacją alertów używają klastrów czasowo-przestrzennych i śledzenia przyczyny źródłowej. — **siła dowodów: praktyczne + empiryczne; pewność: wysoka**
- **Suppress / inhibit zamiast kasowania** to dojrzały wzorzec operacyjny. PagerDuty wyraźnie rozróżnia deduplication od suppression i zachowuje suppressed alerts do forensics/context. Alertmanager używa inhibit/silence, aby nie zalewać operatora alertami wtórnymi. — **siła dowodów: praktyczne; pewność: wysoka**
- **Batch triage / bulk actions są standardową odpowiedzią na narastający backlog.** Sentry dostarcza bulk mutate dla issue’ów; dokumentacja issue triage opisuje filtrowanie, statusy i pracę na listach. To silny sygnał, że dojrzałe systemy nie polegają na ręcznym przeglądaniu elementów jeden po drugim. — **siła dowodów: praktyczne; pewność: wysoka**
- **TTL / stale / auto-close z wyjątkami to dojrzała praktyka dla “zimnych” elementów.** GitHub pokazuje wzorzec: po okresie bezczynności oznacz jako stale, później zamknij, z wyjątkami dla labeli, assignee, milestone itp. To nie jest to samo co dedup, ale jest dobrze udokumentowaną metodą kontrolowania długiego ogona backlogu. — **siła dowodów: praktyczne; pewność: wysoka**
- **Opóźnienie notyfikacji w celu agregacji też działa w praktyce.** W dokumentacji PagerDuty pojawia się wzorzec notification delay, który pozwala najpierw skleić podobne zdarzenia, a dopiero potem powiadamiać. — **siła dowodów: praktyczne; pewność: średnia-wysoka**

#### Co pokazują badania empiryczne

- **Alert triage i redukcja fałszywych alarmów mają realny wpływ na zmniejszanie alert fatigue.** NODOZE pokazuje, że ranking prawdziwych alertów ponad false alarms i zwięzłe wyjaśnienia pomagają operatorom; nowsze prace nad agregacją alertów oraz AlertGuardian raportują duże redukcje alertów przez dedup, threshold tuning i analizę czasową. — **siła dowodów: empiryczne; pewność: średnia-wysoka**
- **W duplicate bug report detection proste techniki bywają konkurencyjne wobec bardziej złożonych.** Przegląd DBRD pokazuje, że prostsze metody potrafią wygrywać z bardziej wyrafinowanymi i że praktyki przemysłowe (np. Mozilla, VSCode) bywają porównywalne z nowszymi metodami badawczymi. To ważny sygnał przeciwko odruchowemu “dokładaniu inteligencji” bez benchmarku. — **siła dowodów: empiryczne; pewność: wysoka**
- **Duplikaty nie są wyłącznie szkodliwe.** Starsze badanie o duplicate bug reports sugeruje, że dodatkowe duplikaty mogą wnosić użyteczny kontekst i pomagać w szybszym rozwiązaniu problemu, więc sensowniejsze bywa ich scalanie niż brutalne odrzucanie. — **siła dowodów: empiryczne; pewność: średnia**

#### Co działa, a czego nie udało się twardo potwierdzić

- **Działa dobrze potwierdzone:** dedup, grouping, inhibit/suppress, batch triage, stale/TTL z wyjątkami, opóźnienie notyfikacji do agregacji. — **siła dowodów: praktyczne + empiryczne**
- **Częściowo potwierdzone:** uczenie reguł redukcji szumu i triage z feedbacku operatorów (np. AlertGuardian). Obiecujące, ale część źródeł jest nowa lub przedrecenzyjna. — **siła dowodów: empiryczne; pewność: średnia**
- **Nie udało się potwierdzić jako dominującej praktyki:** jawny, liczbowy **priority decay** stosowany szeroko jako podstawowy mechanizm zarządzania backlogiem agentowym. Znalazłem silne analogie (stale timers, inactivity windows, suppression, aging przez brak aktywności), ale nie mocne źródła pierwotne pokazujące, że duże systemy standardowo zarządzają backlogiem właśnie przez ciągły matematyczny spadek priorytetu. — **wynik negatywny / luka w wiedzy**

#### Najważniejsze trade-offy

- **Twarda deduplikacja** zmniejsza szum, ale może ukryć nową informację diagnostyczną, jeśli rekord nadrzędny nie zachowuje śladu i dodatkowego kontekstu. — **siła dowodów: empiryczne + praktyczne**
- **TTL / stale auto-close** skraca backlog, ale może usuwać wolno dojrzewające, nadal ważne sygnały; dlatego praktyczne systemy stosują wyjątki, etykiety i resety timera przy aktywności. — **siła dowodów: praktyczne**
- **Silne suppression/inhibition** chroni operatora, ale może też ukrywać zmianę rozkładu problemów, jeśli nie zachowuje się suppressed items do późniejszej analizy. — **siła dowodów: praktyczne + spekulacja**

---

### 4) Anti-patterns w komunikacji agent-agent

#### Co jest empirycznie udokumentowane jako szkodliwe

- **Overloader / overloaded / isolated agents** to najlepiej nazwane antywzorce komunikacyjne w literaturze MAS. Prace metryczne pokazują, że niezbalansowana komunikacja pogarsza QoS i czas odpowiedzi; gdy wiele agentów stale wybiera ten sam węzeł, ten staje się hotspotem, a reszta zasobów pozostaje niedowykorzystana. — **siła dowodów: empiryczne; pewność: wysoka**
- **Nadmierna liczba komunikatów sama w sobie jest problemem projektowym.** Starsza literatura o metrykach komunikacji MAS traktuje wzorce wymiany wiadomości jako kluczowy czynnik wydajności, nie detal implementacyjny. — **siła dowodów: empiryczne; pewność: wysoka**

#### Co jest bardzo dobrze opisane praktycznie w nowoczesnych frameworkach

- **Too much back-and-forth** — CrewAI wprost wskazuje, że agenci potrafią zadawać sobie nadmiar pytań, co spowalnia wykonanie i rozmywa postęp. — **siła dowodów: praktyczne; pewność: wysoka**
- **Delegation loops** — CrewAI dokumentuje pętle delegacji jako realny problem i sugeruje ograniczanie re-delegation oraz wyraźniejszą hierarchię odpowiedzialności. — **siła dowodów: praktyczne; pewność: wysoka**
- **Niewłaściwy kanał komunikacyjny do danego celu** — AutoGen wyraźnie rozróżnia direct messaging (dla request/response) od publish/broadcast (bez odpowiedzi zwrotnej). Użycie broadcast/pub-sub do zadań wymagających odpowiedzi jest więc praktycznym antywzorcem: traci się naturalny return path i kontrolę błędów. — **siła dowodów: praktyczne; pewność: wysoka**

#### Antywzorce wynikające z syntezy źródeł

- **Brak korelacji wiadomości** (`conversation-id`, `in-reply-to`, dedup key, fingerprint) sprzyja osieroconym odpowiedziom, wielokrotnemu podejmowaniu tego samego wątku i słabemu audytowi. Klasyczne ACL-e traktują te pola poważnie; systemy operacyjne robią analogiczną rzecz przez klucze deduplikacji i fingerprinty. — **siła dowodów: praktyczne + spekulacja; pewność: wysoka**
- **Fan-out bez grupowania lub inhibit/suppress** prowadzi do alert storms i do utraty sygnału ważności w szumie. To jest dobrze wspierane przez dokumentację alertingową i badania agregacji alertów. — **siła dowodów: praktyczne + empiryczne; pewność: wysoka**
- **Zbyt ekspansywna ontologia komunikacyjna bez egzekwowalnych protokołów** zwiększa koszt poznawczy i spory o znaczenie bez gwarancji lepszej operacyjności. To nie jest mocno udokumentowane jako osobny eksperyment “A/B”, ale wynika z krytyki speech-act semantics i z uproszczeń obecnych w nowoczesnych frameworkach. — **siła dowodów: empiryczne + praktyczne + spekulacja; pewność: średnia**
- **Brak pamięci wspólnej / collective memory** zwiększa koszt odtwarzania kontekstu i liczbę pytań wtórnych. Nowsze prace i dokumentacje (CrewAI memory, badania nad structured communication / collective memory) sugerują, że strukturyzacja komunikacji i pamięci pomaga redukować przeciążenie poznawcze, choć baza dowodowa jest jeszcze młodsza niż dla klasycznych antywzorców obciążenia. — **siła dowodów: praktyczne + empiryczne; pewność: średnia**

#### Co wydaje się szczególnie szkodliwe operacyjnie

1. **Hotspoty komunikacyjne** — wiele źródeł wskazuje na degradację wydajności. — **siła dowodów: empiryczne**
2. **Pętle delegacji i nadmiar dopytań** — dobrze opisane praktycznie, łatwo zamieniają komunikację w szum. — **siła dowodów: praktyczne**
3. **Broadcast tam, gdzie potrzebny jest kontrakt request/response** — prowadzi do utraty odpowiedzialności i ścieżki zwrotnej. — **siła dowodów: praktyczne**
4. **Deduplikacja bez merge semantics** — redukuje liczbę rekordów, ale może zubażać informację. — **siła dowodów: empiryczne + praktyczne**

## Otwarte pytania / luki w wiedzy

- **Nie udało się potwierdzić jednego, szeroko przyjętego standardu dla “obowiązkowych pól” we współczesnych frameworkach LLM-agentowych.** AutoGen i CrewAI pokazują raczej minimalne kontrakty danych niż wspólny ACL w stylu FIPA.
- **Nie udało się znaleźć mocnego, pierwotnego źródła pokazującego numeric priority decay jako dominującą, sprawdzoną praktykę zarządzania backlogiem obserwacji agentowych.** Najbliższe analogie to stale timers, inactivity windows i suppression.
- **Nie znalazłem dobrego bezpośredniego benchmarku porównującego skuteczność różnych ontologii speech acts w produkcyjnych systemach agentowych.** Wnioski o “over-engineering” są więc częściowo syntetyczne, nie rozstrzygnięte eksperymentalnie.
- **Nowoczesne frameworki (AutoGen, CrewAI) dokumentują komunikację bardziej na poziomie API i orkiestracji niż na poziomie formalnej semantyki.** To utrudnia 1:1 porównanie z FIPA/KQML.
- **Część najciekawszych wyników o alert triage i multi-agent rule refinement pochodzi z nowych prac i preprintów.** Są użyteczne jako sygnał kierunku, ale słabsze dowodowo niż wieloletnia dokumentacja narzędzi produkcyjnych.
- **Konflikt źródeł dot. duplikatów nie polega na prostym “duplikaty są dobre/złe”.** Bardziej wiarygodna synteza brzmi: są kosztowne jako osobne jednostki robocze, ale niosą informację, więc najlepszą praktyką bywa merge + zachowanie kontekstu, a nie ślepe kasowanie.

## Źródła / odniesienia

### Standardy wiadomości i ontologie komunikacji

- [FIPA ACL Message Structure Specification](https://www.yumpu.com/en/document/view/32755962/fipa-acl-message-structure-specification) — specyfikacja pól wiadomości FIPA ACL; użyta do ustalenia, jakie elementy envelope są formalnie przewidziane.
- [FIPA Communicative Act Library Specification](https://jmvidal.cse.sc.edu/library/XC00037H.pdf) — oficjalna biblioteka communicative acts FIPA; użyta do mapy performatives i do tezy, że FIPA nie wymusza większości aktów.
- [JADE ACLMessage API](https://jade.tilab.com/doc/api/jade/lang/acl/ACLMessage.html) — praktyczna implementacja FIPA ACL w JADE; użyta do potwierdzenia zgodności JADE z FIPA i znaczenia pól konwersacyjnych.
- [KQML as an Agent Communication Language](https://dl.acm.org/doi/pdf/10.1145/191246.191322) — klasyczny opis KQML jako języka i protokołu komunikacji agentów; użyty do porównania z FIPA.
- [A Proposal for a new KQML Specification](https://www.csee.umbc.edu/csee/research/KQML/papers/kqml97.pdf) — specyfikacja KQML z listą performatives i parametrów; użyta do oceny szerokości ontologii KQML.
- [Message and Communication — AutoGen](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/framework/message-and-communication.html) — oficjalny opis komunikacji w AutoGen core; użyty do pokazania, że wiadomości są serializowanymi danymi.
- [autogen_agentchat.messages — AutoGen](https://microsoft.github.io/autogen/stable//reference/python/autogen_agentchat.messages.html) — referencja typów wiadomości w AutoGen; użyta do identyfikacji realnych pól (`source`, `content`, `target`, `metadata`, `created_at`).
- [Collaboration — CrewAI](https://docs.crewai.com/en/concepts/collaboration) — dokumentacja narzędzi delegation/ask-question; użyta do pokazania, jak CrewAI standaryzuje współpracę agentów.
- [Tasks — CrewAI](https://docs.crewai.com/en/concepts/tasks) — dokumentacja obiektów Task; użyta do pokazania, że współpraca jest modelowana zadaniowo, a nie przez ACL.
- [Memory — CrewAI](https://docs.crewai.com/en/concepts/memory) — opis pamięci i recall; użyty przy wątku shared memory/collective context.
- [Event Listeners — CrewAI](https://docs.crewai.com/en/concepts/event-listener) — dokumentacja event bus / observability; użyta do pokazania komunikacji zdarzeniowej i monitoringu.
- [On the Formal Semantics of Speech-Act Based Communication in an Agent-Oriented Programming Language](https://jomifred.github.io/mas/leituras/SpeechActs-AOP.pdf) — krytyka trudności semantyki speech-act i prób jej ugruntowania obliczalnego.
- [Operational Specification of a Commitment-Based Agent Communication Language](https://people.lu.usi.ch/fornaran/papers/AAMAS02_fornara_colombetti.pdf) — kluczowe źródło podejścia commitment-based; użyte do pokazania alternatywy wobec mentalistycznej semantyki.
- [A Protocol-Based Semantics for an Agent Communication Language](https://www.ijcai.org/Proceedings/99-1/Papers/070.pdf) — klasyczne źródło podejścia protocol-based; użyte do opisania semantyki opartej na protokołach.
- [A Social Semantics for Agent Communication Languages](https://www.csc2.ncsu.edu/faculty/mpsingh/papers/mas/ijcai-99-acl.pdf) — społeczne/commitment-based ujęcie znaczenia komunikacji; użyte do triangulacji wobec speech-act.

### Backlog, triage, dedup i redukcja szumu

- [PagerDuty Event Management](https://support.pagerduty.com/main/docs/event-management) — oficjalny opis deduplication vs suppression; użyty do praktyk noise reduction.
- [PagerDuty Event Orchestration](https://support.pagerduty.com/main/docs/event-orchestration) — dokumentacja `dedup_key` i standaryzacji triage; użyta do potwierdzenia merge-by-key.
- [PagerDuty Alerts](https://support.pagerduty.com/main/docs/alerts) — opis agregacji alertów w incydenty; użyty do wątku grouping.
- [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) — oficjalny opis dedup, grouping, routing, silencing, inhibition.
- [Prometheus Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/) — konfiguracja inhibition i routingu; użyta do potwierdzenia mechanizmów suppress/inhibit.
- [Sentry Issue Grouping](https://docs.sentry.io/concepts/data-management/event-grouping/) — oficjalny opis fingerprintingu i grupowania issue’ów.
- [Sentry Bulk Mutate a List of Issues](https://docs.sentry.io/api/events/bulk-mutate-a-list-of-issues/) — API do batch triage; użyte do potwierdzenia bulk operations.
- [Sentry Issues](https://docs.sentry.io/product/issues/) — dokumentacja issue triage i filtrowania list; użyta jako dowód praktyk pracy na backlogu.
- [Closing inactive issues — GitHub Docs](https://docs.github.com/en/actions/use-cases-and-examples/project-management/closing-inactive-issues) — oficjalna praktyka stale/auto-close po bezczynności.
- [actions/stale](https://github.com/actions/stale) — referencyjna implementacja stale workflow; użyta do szczegółów wyjątków i resetów timerów.
- [NODOZE: Combatting Threat Alert Fatigue with Automated Provenance Triage and Analysis](https://www.ndss-symposium.org/wp-content/uploads/2019/02/ndss2019_03B-1-3_UlHassan_paper.pdf) — badanie empiryczne alert triage i redukcji alert fatigue.
- [Temporal–Spatial Alert Aggregation and Large Language Model–Based Root Cause Tracing](https://www.mdpi.com/2079-9292/13/22/4425) — badanie agregacji alertów przez klastrowanie i root-cause tracing.
- [AlertGuardian](https://arxiv.org/pdf/2601.14912) — nowy preprint o redukcji alertów i iteracyjnym ulepszaniu reguł; użyty jako sygnał kierunku, nie jako jedyny fundament.
- [Duplicate Bug Report Detection: How Far Are We?](https://arxiv.org/abs/2212.00548) — porównanie metod DBRD i obserwacja, że proste techniki bywają bardzo konkurencyjne.
- [Exploring the Role of Automation in Duplicate Bug Report Detection: An Industrial Case Study](https://greg4cr.github.io/pdf/24duplicates.pdf) — nowsze studium przypadku o kosztach duplikatów i roli automatyzacji.
- [Duplicate bug reports considered harmful… really?](https://researchportal.hkust.edu.hk/en/publications/duplicate-bug-reports-considered-harmful-really-2) — kontrapunkt pokazujący, że duplikaty mogą wnosić użyteczną informację i warto je scalać zamiast bezwzględnie usuwać.

### Antywzorce komunikacyjne w MAS

- [A Metrics Suite for the Communication of Multi-agent Systems](https://pdfs.semanticscholar.org/b9c1/3fee37b829de16336a0bbc0e820178cd8820.pdf) — zestaw metryk do wykrywania niezbalansowanej komunikacji; użyty do klasycznych antywzorców obciążenia.
- [Detection of Undesirable Communication Patterns in Multi-agent Systems](https://www.sciencedirect.com/science/article/abs/pii/S0952197610001697) — praca o wzorcach typu overloader/overloaded/isolated; użyta do części empirycznej o szkodliwych wzorcach.
- [CrewAI Collaboration](https://docs.crewai.com/en/concepts/collaboration) — źródło praktycznych antywzorców typu too much back-and-forth i delegation loops.
- [AutoGen Message and Communication](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/framework/message-and-communication.html) — użyte do rozróżnienia direct request/response vs publish/broadcast.
- [AutoGen Topic and Subscription Example Scenarios](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/cookbook/topic-subscription-scenarios.html) — cookbook komunikacji broadcastowej; użyty do kontrastu z direct messaging.
- [CoThinker: Incentivizing Communication and Participation in Multi-Agent Collaborative Reasoning under Cognitive Load](https://arxiv.org/html/2506.06843v1) — nowsze źródło o structured communication / collective memory; użyte ostrożnie jako uzupełnienie, nie fundament.
