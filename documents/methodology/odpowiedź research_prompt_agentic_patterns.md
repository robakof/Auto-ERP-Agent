Zbieram to jako katalog wzorców z kilku warstw naraz: dokumentacje frameworków, przeglądy naukowe i praktyki inżynierskie. Na końcu dam też osobną listę rzeczy, których nie udało się znaleźć jako nazwanych, dobrze opisanych wzorców.

Mam już dwa mocne zbiory źródeł: frameworki pokazują nazwy wzorców „w praktyce”, a surveye i benchmarki dają lepszą taksonomię i trade-offy. Teraz domykam warstwę bezpieczeństwa, nadzoru i ewaluacji, bo tam najłatwiej o marketing zamiast wzorców.

Mam już spójny obraz: część wzorców jest dobrze nazwana w frameworkach, ale kilka pytań z promptu ma odpowiedź „to istnieje jako heurystyka, nie jako ustabilizowany pattern”. To ważne, bo w architekturze ERP lepiej oprzeć się na wzorcach z udokumentowanymi konsekwencjami niż na modnych nazwach.

Thought for 17m 20s

Poniżej masz praktyczny katalog wzorców architektonicznych dla systemów wieloagentowych LLM, złożony z dokumentacji frameworków, przeglądów naukowych i benchmarków. Najważniejsza obserwacja: nie ma dziś jednej kanonicznej taksonomii dla „LLM agent architecture patterns”; najbliżej tego są: OpenAI (single vs multi-agent; manager vs decentralized), Microsoft Azure (sekencyjne, współbieżne, handoff, group chat, magentic), Google ADK (coordinator, pipeline, fan-out, critique, HITL), LangGraph (routing, parallelization, orchestrator-worker, evaluator-optimizer) oraz survey o mechanizmach współpracy (peer-to-peer, centralized, distributed, role-based, coordination protocols).

Dla Waszego przypadku — autonomiczna konfiguracja ERP z rolami specjalistycznymi i eskalacją — najbardziej stabilny punkt startowy to: płytka hierarchia supervisor→specialists, deterministyczna powłoka workflow wokół niedeterministycznych agentów, critic/review loop tylko tam, gdzie jakość jest ważniejsza niż latencja, HITL na akcjach nieodwracalnych, checkpointy stanu oraz trajectory evaluation, a nie tylko ocena końcowego wyniku. Google Research pokazał też w 2026, że multi-agent zyskuje głównie na zadaniach równoległych, a na sekwencyjnych bywa gorszy; to ważne ostrzeżenie dla procesów ERP z wieloma zależnościami.

1. Wzorce orchestracji
Single orchestrator / Manager-as-tools

Kategoria: orchestracja
Źródło: OpenAI practical guide; Azure orchestration patterns
Krótki opis: Jeden agent zarządza przebiegiem pracy i wywołuje wyspecjalizowanych agentów jako narzędzia. To najczytelniejszy wzorzec, gdy chcecie zachować jeden punkt kontaktu z użytkownikiem i jeden punkt odpowiedzialności za decyzje.
Gdzie stosowane w praktyce: OpenAI opisuje to jako manager pattern; Google ADK i CrewAI mają analogiczne układy manager/subagents.
Trade-offy:
✓ wysoka audytowalność, prostsza kontrola uprawnień, łatwiejsza ewaluacja
✓ dobre dopasowanie do workflow z centralną polityką biznesową
✗ centralny bottleneck poznawczy i wydajnościowy
✗ łatwo o “tool overload” i wzrost kosztu/latencji przy wielu hopach
✗ gdy manager staje się zbyt „sprytny”, traci się modularność
Relevancja dla naszego systemu: wysoka — ERP ma naturalny „policy brain”, który powinien decydować, a nie wykonywać wszystko sam.
Link / źródło: OpenAI manager pattern; Azure complexity ladder.

Hierarchical orchestration / Supervisor tree

Kategoria: orchestracja
Źródło: CrewAI hierarchical process; Google ADK multi-agent systems
Krótki opis: Orchestracja jest rozbita na poziomy: nadrzędny manager deleguje do menedżerów domenowych, a ci do wykonawców. Ten wzorzec poprawia skalowanie organizacyjne kosztem większej liczby przekazań kontekstu.
Gdzie stosowane w praktyce: CrewAI ma jawny hierarchical process; ADK opisuje hierarchie parent/sub-agents; LangGraph wspiera subgraphs i handoff między nimi.
Trade-offy:
✓ dobra separacja domen, odpowiedzialności i uprawnień
✓ pozwala oddzielić politykę biznesową od wykonania technicznego
✗ każdy dodatkowy poziom zwiększa latencję i ryzyko utraty/skrzywienia kontekstu
✗ trudniejsze debugowanie odpowiedzialności za błąd
✗ brak mocnej, formalnej reguły „ile poziomów jest optymalne”; praktycznie lepiej utrzymywać drzewo płytkie
Relevancja dla naszego systemu: wysoka — Wasze role już tworzą naturalną hierarchię, ale trzymałbym głębokość na 1–2 poziomach nadzoru.
Link / źródło: CrewAI hierarchical; ADK MAS; LangGraph handoffs/context engineering.

Decentralized handoffs / Peer-to-peer delegation

Kategoria: orchestracja
Źródło: OpenAI practical guide; LangGraph handoffs
Krótki opis: Agenci działają jako równorzędni partnerzy i przekazują sobie sterowanie zależnie od kompetencji. To zwiększa lokalną autonomię i elastyczność, ale przenosi ciężar z centralnej kontroli na poprawne przekazywanie kontekstu.
Gdzie stosowane w praktyce: OpenAI opisuje to jako decentralized pattern; LangGraph ma handoff tools między agent nodes; AutoGen ma Swarm/handoff teams.
Trade-offy:
✓ mniej centralnego bottlenecku
✓ dobre dla front-office, supportu i zadań z naturalnym „przekazaniem sprawy”
✗ trudne context engineering
✗ gorsza audytowalność niż przy managerze
✗ łatwo o pętle, duplikację pracy i rozmycie odpowiedzialności
Relevancja dla naszego systemu: średnia — dobre na przekazania między domenami ERP, ale nie jako domyślny wzorzec dla zmian konfiguracyjnych.
Link / źródło: OpenAI decentralized; LangGraph handoffs.

Group chat / emergent orchestration

Kategoria: orchestracja
Źródło: Azure group chat; AutoGen teams; Anthropic subagent orchestration
Krótki opis: Kilku agentów współdzieli jeden wątek i „dochodzi do rozwiązania” przez dyskusję, debatę lub maker-checker loop. To działa najlepiej w ideacji, walidacji i review, a najgorzej w deterministycznych procesach wykonawczych.
Gdzie stosowane w praktyce: Azure group chat orchestration; AutoGen RoundRobin/SelectorGroupChat; Anthropic opisuje natural subagent orchestration, ale ostrzega przed overuse.
Trade-offy:
✓ transparentność i bogatsza deliberacja
✓ dobre do compliance review, QA, red-team/blue-team
✗ wysoki narzut tokenowy
✗ ryzyko braku jasnego warunku zakończenia
✗ słabe dopasowanie do działań mutujących stan systemu
Relevancja dla naszego systemu: średnia — bardzo dobra jako warstwa review/analizy ryzyka, słaba jako główny silnik konfiguracji ERP.
Link / źródło: Azure group chat; AutoGen teams; Anthropic subagent overuse warning.

Event-driven orchestration

Kategoria: orchestracja
Źródło: AutoGen Core; CrewAI Flows; NeMo Guardrails
Krótki opis: Agenci nie działają „na rozkaz”, lecz reagują na zdarzenia, zmiany stanu, approvale, timeouty albo wyniki innych agentów. To wzorzec bliższy systemom produkcyjnym, bo dobrze łączy się z asynchronicznością i integracją z zewnętrznymi systemami.
Gdzie stosowane w praktyce: AutoGen Core jest jawnie event-driven; CrewAI Flows są event-driven; NeMo Guardrails ma event loop oparty na zdarzeniach.
Trade-offy:
✓ naturalne dla approval queues, callbacków, retry i integracji z ERP
✓ dobra baza pod obserwowalność i odporność
✗ trudniejsze debugowanie i testowanie niż przy liniowym pipeline
✗ większe ryzyko wyścigów i niespójnego shared state
Relevancja dla naszego systemu: wysoka — szczególnie jeśli konfiguracja ERP ma być uruchamiana przez zdarzenia biznesowe i kolejki akceptacji.
Link / źródło: AutoGen Core; CrewAI Flows; NeMo event-driven runtime.

Deterministic workflow shell (sequential / routing / parallel / loop)

Kategoria: orchestracja
Źródło: Google ADK workflow agents; LangGraph workflows; Azure patterns
Krótki opis: To nie jeden wzorzec, tylko bardzo ważna rodzina: orchestracja jest deterministyczna, a tylko poszczególne kroki są „agentowe”. W praktyce to najczęściej najlepszy kompromis między autonomią a przewidywalnością.
Gdzie stosowane w praktyce: ADK ma workflow agents: sequential, parallel, loop; LangGraph ma routing, parallelization, orchestrator-worker; Azure opisuje sequential i concurrent orchestration.
Trade-offy:
✓ przewidywalny control flow i łatwiejsze testy
✓ dobre dopasowanie do procesów biznesowych i compliance
✗ mniej elastyczne przy nietypowych przypadkach
✗ może zbyt wcześnie „usztywnić” proces, jeśli domena jest nadal słabo poznana
Relevancja dla naszego systemu: bardzo wysoka — dla ERP to powinien być domyślny „szkielet”, w którym agenci są tylko inteligentnymi krokami.
Link / źródło: ADK workflow agents; LangGraph workflows; Azure orchestration patterns.

2. Wzorce dekompozycji zadań
Plan-then-execute / Orchestrator-worker

Kategoria: dekompozycja
Źródło: LangGraph orchestrator-worker; Magentic-One
Krótki opis: Najpierw tworzony jest plan lub lista sekcji/subzadań, potem workery wykonują części, a orchestrator syntetyzuje wynik. To klasyczny wzorzec dla raportów, zmian wieloetapowych i transformacji wielu artefaktów.
Gdzie stosowane w praktyce: LangGraph ma jawny orchestrator-worker; Magentic-One utrzymuje Task Ledger i Progress Ledger, replanując gdy postęp jest słaby.
Trade-offy:
✓ dobra kontrola zakresu i postępu
✓ łatwo dodać checkpointy i walidację etapów
✗ jeśli plan początkowy jest zły, cały workflow może dryfować
✗ koszt planowania rośnie przy zbyt drobnej dekompozycji
Relevancja dla naszego systemu: bardzo wysoka — konfiguracja ERP prawie zawsze daje się rozbić na plan → zmiany → walidacja → synteza.
Link / źródło: LangGraph orchestrator-worker; Magentic-One architecture.

Sequential pipeline

Kategoria: dekompozycja
Źródło: CrewAI sequential; ADK sequential workflow
Krótki opis: Zadanie jest rozkładane na kroki wykonywane w stałej kolejności. To najbardziej konserwatywny wzorzec, ale bardzo dobrze pasuje do procesów z zależnościami i wymaganiami audytowymi.
Gdzie stosowane w praktyce: CrewAI Sequential Process; ADK Sequential Agents; Azure sequential orchestration.
Trade-offy:
✓ prostota, monitoring, testowalność
✓ mały koszt koordynacji
✗ słaba odporność na nieprzewidziane odgałęzienia
✗ każdy błąd wcześnie w pipeline może propagować dalej
Relevancja dla naszego systemu: wysoka — idealne dla fragmentów ERP, gdzie kolejność działań jest wymuszona przez logikę systemu.
Link / źródło: CrewAI sequential; ADK workflow agents; Azure orchestration patterns.

Router / classifier-to-specialist

Kategoria: dekompozycja
Źródło: LangGraph routing; LangGraph subagent registry
Krótki opis: Pierwszy krok to klasyfikacja typu zadania i skierowanie go do wyspecjalizowanego flow lub agenta. To wzorzec pośredni między jednym agentem z wieloma narzędziami a pełnym systemem wieloagentowym.
Gdzie stosowane w praktyce: LangGraph routing workflows; dynamiczne registry agentów; decision-tree style transitions w AutoGen FSM Group Chat.
Trade-offy:
✓ redukuje przeciążenie narzędzi i promptu
✓ poprawia specjalizację bez pełnej decentralizacji
✗ jakość całego systemu zależy od pierwszej decyzji routingu
✗ błędny routing bywa trudny do wykrycia po fakcie
Relevancja dla naszego systemu: wysoka — naturalnie rozdziela zadania na analitykę, konfigurację, development i metodologię.
Link / źródło: LangGraph routing; LangGraph subagent specs/registry; AutoGen FSM transitions.

Parallel fan-out / gather

Kategoria: dekompozycja
Źródło: LangGraph parallelization; ADK parallel agents; Google scaling study
Krótki opis: Niezależne subzadania są odpalane równolegle, a wyniki są później scalane. Wersja alternatywna uruchamia kilka niezależnych prób tego samego zadania, by zwiększyć pewność.
Gdzie stosowane w praktyce: LangGraph parallelization; ADK parallel workflow agents; Azure concurrent orchestration.
Trade-offy:
✓ redukcja czasu ściany i lepsze wykorzystanie specjalizacji
✓ może zwiększać confidence przez wielokrotne próby
✗ wymaga dobrego gather/synthesis
✗ ryzyko niespójności shared state i większego kosztu
✗ opłaca się głównie wtedy, gdy zadanie naprawdę jest równoległe
Relevancja dla naszego systemu: średnia do wysokiej — świetne dla analiz wariantów, walidacji i porównań, mniej dla sekwencyjnych zmian konfiguracyjnych.
Link / źródło: LangGraph parallelization; ADK workflow agents; Google scaling results.

ReAct (Reason + Act)

Kategoria: dekompozycja
Źródło: ReAct paper
Krótki opis: Agent przeplata tok rozumowania z działaniem, dzięki czemu może aktualizować plan, obsługiwać wyjątki i pobierać dodatkowe informacje z otoczenia. To podstawowy wzorzec „agent loop” dla pojedynczego agenta, który bywa wpinany jako krok w większy system wieloagentowy.
Gdzie stosowane w praktyce: Większość agent frameworks implementuje de facto wariant ReAct loop przy tool use.
Trade-offy:
✓ naturalne sprzężenie planowania z obserwacją środowiska
✓ lepsza interpretowalność trajektorii niż czyste CoT
✗ w multi-agent łatwo mnoży koszt i długość trajektorii
✗ słabo działa bez limitów iteracji i dobrych narzędzi
Relevancja dla naszego systemu: średnia — dobra jako „silnik lokalny” specjalisty, ale nie jako jedyny wzorzec systemowy.
Link / źródło: ReAct abstract.

Tree search deliberation (ToT / LATS)

Kategoria: dekompozycja
Źródło: Tree of Thoughts; LATS
Krótki opis: System eksploruje wiele ścieżek rozumowania, sam ocenia odgałęzienia i może wracać/backtrackować. LATS idzie dalej i łączy to z Monte Carlo Tree Search, działaniem i self-reflection.
Gdzie stosowane w praktyce: Głównie research i zadania o wysokim koszcie błędu; rzadziej jako domyślny wzorzec frameworkowy.
Trade-offy:
✓ mocne dla złożonego planowania i problemów z wieloma alternatywami
✓ lepsze niż pojedyncza trajektoria, gdy trzeba szukać i porównywać
✗ bardzo drogie obliczeniowo
✗ trudne do operacjonalizacji w systemach produkcyjnych z SLA
✗ słabe dopasowanie do długich workflow z mutacją stanu zewnętrznego
Relevancja dla naszego systemu: średnia — dobre dla generowania i porównywania wariantów planu zmiany, nie dla codziennego execution path.
Link / źródło: ToT; LATS.

Speculative execution / Parallel plan racing

Kategoria: dekompozycja
Źródło: Interactive Speculative Planning; Parallelized Planning-Acting; parallel multi-agent sampling
Krótki opis: System uruchamia równolegle alternatywne plany lub instancje zespołów agentów; pierwszy sensowny wynik może wygrać, albo wyniki są agregowane. To wzorzec optymalizujący latencję albo success rate kosztem dodatkowych zasobów.
Gdzie stosowane w praktyce: Na razie głównie badania; nie jest to jeszcze „standardowy pattern” w głównych frameworkach.
Trade-offy:
✓ niższa latencja przy early termination
✓ wyższa skuteczność przy agregacji
✗ koszt rośnie niemal liniowo z liczbą spekulatywnych gałęzi
✗ problem side-effectów: przegrane gałęzie nie mogą zmieniać świata bez transakcyjnej osłony
✗ różnorodność planów nie zawsze daje zysk
Relevancja dla naszego systemu: średnia — sensowne dla planowania/analizy, ale tylko z mocnym sandboxem i bez bezpośrednich zapisów do ERP.
Link / źródło: speculative planning; parallelized planning-acting; parallel agents with early termination/aggregation.

3. Wzorce nadzoru i kontroli błędów
Evaluator-optimizer / Critic loop / Maker-checker

Kategoria: kontrola błędów
Źródło: LangGraph evaluator-optimizer; Google design patterns; Azure group chat
Krótki opis: Jeden agent generuje wynik, drugi ocenia go według kryteriów i odsyła do poprawy, aż warunek jakości zostanie spełniony. To najczyściej opisany wzorzec review w dzisiejszych frameworkach.
Gdzie stosowane w praktyce: LangGraph evaluator-optimizer; Azure maker-checker loops; ADK review/critique pattern; AutoGen critic examples.
Trade-offy:
✓ poprawa jakości i zgodności z kryteriami
✓ łatwo dołożyć człowieka jako finalnego recenzenta
✗ wysoka latencja i większy koszt tokenów
✗ bez dobrych kryteriów critic staje się losowy albo pedantyczny
Relevancja dla naszego systemu: bardzo wysoka — idealne dla przeglądu zmian konfiguracyjnych, walidacji wymagań i checków zgodności.
Link / źródło: LangGraph evaluator-optimizer; Google loop/review pattern; Azure group chat/maker-checker.

Self-critique / reflection with episodic memory

Kategoria: kontrola błędów
Źródło: Reflexion; Magentic-One; Anthropic prompting best practices
Krótki opis: Agent sam generuje refleksję o tym, co poszło źle lub co wymaga poprawy, i zapisuje to jako pamięć lub progress notes. To wzorzec bardziej „intra-agent” niż „inter-agent”, ale architektonicznie bardzo ważny.
Gdzie stosowane w praktyce: Reflexion; Magentic-One Progress Ledger; Anthropic rekomenduje self-critique i hypothesis/progress notes przy złożonych badaniach.
Trade-offy:
✓ poprawia uczenie się na błędach bez fine-tuningu
✓ dobre dla długich, wieloetapowych zadań
✗ może wzmacniać błędne interpretacje, jeśli feedback jest zły
✗ kosztuje dodatkowe wywołania i pamięć
Relevancja dla naszego systemu: wysoka — szczególnie dla Metodologa i Analityka, którzy powinni zostawiać ślady „dlaczego zmieniliśmy plan”.
Link / źródło: Reflexion; Magentic-One; Anthropic self-critique guidance.

Guardrail layer

Kategoria: kontrola błędów
Źródło: NeMo Guardrails; Google ADK callbacks; OpenAI guardrails cookbook
Krótki opis: Guardrails to nie „marketing”, tylko osobna warstwa reguł i kontroli działająca przed/po modelu, przed/po narzędziu lub na poziomie dialogu, retrievalu i execution. Dobrze zaprojektowane guardrails nie zastępują architektury, tylko ją uszczelniają.
Gdzie stosowane w praktyce: NeMo ma input/dialog/output/retrieval/execution rails; ADK callbacks pozwala blokować albo zastępować model/tool steps; OpenAI definiuje guardrail jako zestaw reguł i checków.
Trade-offy:
✓ separacja polityki bezpieczeństwa od logiki biznesowej
✓ łatwiej testować i stroić niezależnie od promptów agentów
✗ zbyt agresywne guardrails obniżają skuteczność
✗ przy złym projekcie robią się nieczytelne i „rozsmarowane” po systemie
Relevancja dla naszego systemu: bardzo wysoka — akcje ERP wymagają osobnej warstwy polityk, nie tylko dobrego promptu.
Link / źródło: NeMo rails categories; ADK callbacks; OpenAI guardrail definition.

Human-in-the-loop approval gates

Kategoria: kontrola błędów
Źródło: LangGraph HITL; Azure human participation; OpenAI practical guide
Krótki opis: System zatrzymuje się na określonych punktach i czeka na approve/edit/reject albo feedback loop. Najbardziej użyteczny wariant to nie „zatwierdzaj wszystko”, tylko gates scoped to high-risk tool calls.
Gdzie stosowane w praktyce: LangGraph middleware zatrzymuje tool calls i wspiera approve/edit/reject; Azure zaleca mandatory gates i checkpointing; OpenAI wskazuje high-risk actions jako naturalny trigger HITL.
Trade-offy:
✓ radykalnie obniża ryzyko na akcjach nieodwracalnych
✓ buduje ścieżkę audytową
✗ wąskie gardło operacyjne, jeśli gate’ów jest za dużo
✗ źle dobrane approval points zabijają autonomię
Relevancja dla naszego systemu: bardzo wysoka — krytyczne dla zapisów do ERP, zmian uprawnień, migracji danych i działań finansowych.
Link / źródło: LangGraph HITL; Azure HITL; OpenAI high-risk actions.

Checkpoints / time travel / rollback-friendly execution

Kategoria: kontrola błędów
Źródło: LangGraph persistence; Atomix
Krótki opis: System zapisuje stan na każdym kroku albo na wybranych checkpointach, by można było wznowić, przejrzeć trajektorię albo forkować alternatywny bieg. To jest dziś dobrze wspierane dla stanu wewnętrznego, ale rollback skutków w systemach zewnętrznych wymaga osobnej warstwy transakcyjnej lub kompensacyjnej.
Gdzie stosowane w praktyce: LangGraph checkpointers/time travel/fault tolerance; Atomix proponuje transakcyjną semantykę tool use dla side-effectów.
Trade-offy:
✓ mocny fundament pod HITL, recovery i debugowanie
✓ pozwala budować „resume instead of replay”
✗ checkpoint stanu rozmowy to nie to samo co rollback zmian w ERP
✗ pełna transakcyjność narzędzi jest dopiero obszarem rozwijającym się
Relevancja dla naszego systemu: bardzo wysoka — bez checkpointów i planu kompensacji nie puszczałbym agentów do produkcyjnego ERP.
Link / źródło: LangGraph persistence; Atomix transactional tool use.

4. Wzorce granicy autonomii
Confidence-based escalation

Kategoria: autonomia
Źródło: UQ survey; uncertainty propagation in agents; agentic confidence calibration
Krótki opis: Agent eskaluje, gdy jego oszacowana pewność sukcesu spada poniżej progu. To brzmi naturalnie, ale literatura 2025–2026 pokazuje, że naiwna samoocena agenta jest zawodna; lepsze wyniki dają metody process-centric, wykorzystujące sygnały z całej trajektorii.
Gdzie stosowane w praktyce: Bardziej research niż stabilny pattern frameworkowy; praktycznie łączone z retry limits, tool policies i HITL gates.
Trade-offy:
✓ daje formalny punkt wyjścia do selektywnej eskalacji
✓ dobrze łączy się z telemetryką trajektorii
✗ kalibracja confidence w multi-turn/multi-step nadal jest trudnym, nierozwiązanym problemem
✗ agentic overconfidence oznacza, że same self-reports nie wystarczą
Relevancja dla naszego systemu: średnia do wysokiej — warto używać, ale tylko jako jednego sygnału obok ryzyka akcji, liczby retry i jakości dowodów.
Link / źródło: UQ taxonomy; uncertainty propagation in agent systems; overconfidence/calibration papers.

Risk-gated autonomy / high-risk action gate

Kategoria: autonomia
Źródło: OpenAI practical guide; Azure human participation
Krótki opis: Zamiast pytać „czy agent jest pewny?”, pytacie „czy ta akcja jest odwracalna, kosztowna albo wrażliwa?”. W praktyce to dziś bardziej dojrzały wzorzec niż czysta confidence escalation.
Gdzie stosowane w praktyce: OpenAI zaleca human oversight dla sensitive, irreversible, high-stakes actions; Azure sugeruje tool-scoped mandatory gates.
Trade-offy:
✓ prostsze operacyjnie niż pełna kalibracja confidence
✓ dobrze pasuje do compliance i governance
✗ wymaga klasyfikacji akcji oraz polityki ryzyka
✗ nie wykrywa „cichych” błędów przy pozornie niskim ryzyku
Relevancja dla naszego systemu: bardzo wysoka — dla ERP to praktycznie podstawowa granica autonomii.
Link / źródło: OpenAI high-risk actions; Azure mandatory gates and tool-scoped approvals.

5. Wzorce ewaluacji systemu agentowego
Trajectory evaluation

Kategoria: ewaluacja
Źródło: Google ADK evaluate; ADK criteria; LangSmith
Krótki opis: Oceniany jest nie tylko wynik końcowy, ale ścieżka: jakie kroki wykonano, jakie narzędzia wybrano, czy kolejność była sensowna i efektywna. To dziś jedna z najbardziej dojrzałych odpowiedzi na problem „agent miał rację przypadkiem”.
Gdzie stosowane w praktyce: ADK wprost definiuje trajectory i porównanie actual vs ideal; ADK ma metryki tool trajectory, hallucinations, safety; LangSmith wspiera trajectory eval i testy CI/CD agentów.
Trade-offy:
✓ ujawnia błędy procesu, nie tylko wyniku
✓ bardzo przydatne przy długich workflow i compliance
✗ droższe i bardziej pracochłonne niż exact-match output eval
✗ wymaga referencyjnych trajektorii albo sensownych rubryk
Relevancja dla naszego systemu: bardzo wysoka — przy ERP ocena tylko finalnej odpowiedzi byłaby za słaba.
Link / źródło: ADK evaluate; ADK criteria; LangSmith eval tooling.

Topology-aware multi-agent benchmarking

Kategoria: ewaluacja
Źródło: MultiAgentBench; AgentBench; evaluation survey
Krótki opis: Ewaluacja obejmuje nie tylko trafność, ale też koordynację, komunikację, milestone progress i topologię komunikacji między agentami. To ważne, bo system wieloagentowy może mieć dobrą odpowiedź końcową, ale fatalny koszt koordynacji.
Gdzie stosowane w praktyce: MultiAgentBench mierzy coordination/competition i wspiera topologie star/chain/tree/graph; AgentBench daje interaktywne środowiska dla agentów; survey z 2025 porządkuje cele i procesy ewaluacji.
Trade-offy:
✓ bliższe rzeczywistości niż benchmarki single-agent
✓ pozwala porównywać wzorce architektoniczne, nie tylko modele
✗ benchmarki nadal słabo pokrywają długie enterprise workflows
✗ przenoszenie wyników benchmarków do konkretnego ERP wymaga ostrożności
Relevancja dla naszego systemu: wysoka — zwłaszcza jeśli będziecie porównywać manager pattern vs hierarchy vs event-driven shell.
Link / źródło: MultiAgentBench; AgentBench; evaluation survey.

6. Wzorce bootstrapu i inicjalizacji roli
Layered prompt composition / instruction inheritance

Kategoria: bootstrap
Źródło: Codex Prompting Guide; Anthropic prompt templates; Claude subagents
Krótki opis: Instrukcje są warstwowane: globalne zasady, zasady repo/projektu, potem lokalne instrukcje domenowe, zwykle w ustalonej kolejności. To praktyczny sposób rozwiązania „bootstrap paradox”: agent nie „odkrywa” swojej roli sam, tylko dostaje ją z wersjonowanego, kompozycyjnego kontekstu.
Gdzie stosowane w praktyce: Codex wstrzykuje AGENTS.md root-to-leaf; Anthropic promuje prompt templates; Claude subagents dziedziczą model, narzędzia i permission context.
Trade-offy:
✓ przewidywalność, testowalność i łatwe różnicowanie ról
✓ pozwala zarządzać instrukcjami jak konfiguracją systemu
✗ konfliktujące warstwy promptu mogą być trudne do diagnozy
✗ zbyt wiele warstw utrudnia rozumienie „co naprawdę obowiązuje”
Relevancja dla naszego systemu: bardzo wysoka — role typu ERP Specialist / Developer / Metodolog powinny być budowane właśnie warstwowo.
Link / źródło: root-to-leaf injection; prompt templates/version control; inheritance in subagents.

Agent registry bootstrap (enumeration / enum / discovery)

Kategoria: bootstrap
Źródło: LangGraph subagents
Krótki opis: Supervisor musi wiedzieć, jakie role istnieją i kiedy ich używać. LangGraph opisuje tu bardzo praktyczną mini-taksonomię: system prompt enumeration dla małych, stałych zespołów; enum-constrained dispatch dla jawnych, walidowanych wyborów; tool-based discovery dla większych, dynamicznych rejestrów agentów.
Gdzie stosowane w praktyce: LangGraph subagents; podobne mechaniki pojawiają się w narzędziach typu dispatcher/router.
Trade-offy:
✓ czytelny sposób rozwiązania problemu „agent musi znać role, zanim zacznie delegować”
✓ enum/discovery dobrze skaluje governance
✗ enumeracja promptowa szybko starzeje się przy zmianach zespołu
✗ discovery dodaje złożoność i kolejną warstwę decyzji
Relevancja dla naszego systemu: wysoka — dla Waszego stałego zestawu ról sensowny jest enum-constrained dispatch albo mały registry tool.
Link / źródło: LangGraph subagent specs and registry methods.

Prompt registry / versioned role definitions

Kategoria: bootstrap
Źródło: MLflow Prompt Registry; Anthropic prompt templates
Krótki opis: Prompty i instrukcje agentów są traktowane jak wersjonowane artefakty z commit message, tagami i evalami. To wzorzec operacyjny, ale dla systemów agentowych jest architektonicznie kluczowy, bo bez niego role dryfują i trudno robić rollback.
Gdzie stosowane w praktyce: MLflow Prompt Registry i prompt evaluation; Anthropic podkreśla korzyści z szablonów i version control.
Trade-offy:
✓ odtwarzalność eksperymentów i łatwiejsze porównywanie wersji ról
✓ dobra baza pod CI/CD dla agentów
✗ dodatkowy overhead procesowy
✗ nie rozwiązuje sam konfliktów między promptem a tool policy
Relevancja dla naszego systemu: wysoka — przy długim życiu projektu i wielu rolach to powinno być obowiązkowe.
Link / źródło: MLflow prompt registry; Anthropic prompt templates/version control.

7. Wzorce przy długoterminowej pracy agenta
Context compaction / summary windows

Kategoria: długoterminowość
Źródło: Google ADK context compaction; OpenAI Codex compaction; LangGraph memory
Krótki opis: Starsza historia jest okresowo kompresowana do podsumowań lub skondensowanego stanu, by utrzymać wydajność i zapobiec przeciążeniu kontekstu. To dziś podstawowy wzorzec dla długich trajektorii.
Gdzie stosowane w praktyce: ADK ma sliding-window compaction; Codex ma /compact; LangGraph rozróżnia short-term state i long-term memory.
Trade-offy:
✓ kontrola kosztu i latencji
✓ mniejsze ryzyko, że stary szum przykryje aktualny problem
✗ kompresja może zgubić niuanse potrzebne do późniejszego audytu
✗ wymaga rozdzielenia: co streszczamy, a co przechowujemy dokładnie
Relevancja dla naszego systemu: bardzo wysoka — bez compaction agent po kilkudziesięciu sesjach ERP zacznie się dusić własną historią.
Link / źródło: ADK compaction; Codex compaction; LangGraph memory model.

Consolidated long-term memory (state + notes + searchable memory)

Kategoria: długoterminowość
Źródło: OpenAI context personalization; ADK MemoryService; LangGraph long-term memory
Krótki opis: Zamiast replayować całą historię, system utrzymuje oddzielny stan długoterminowy: profil, notatki sesyjne, skonsolidowane notatki globalne i pamięć przeszukiwalną. To wzorzec „write → consolidate → retrieve”.
Gdzie stosowane w praktyce: OpenAI Agents SDK cookbook pokazuje state-based long-term memory; ADK MemoryService wspiera ingest/search; LangGraph ma stores dla memory cross-session.
Trade-offy:
✓ dużo lepsze skalowanie niż pełen replay
✓ ułatwia utrzymanie spójnych założeń przez wiele sesji
✗ wymaga polityk deduplikacji, konflikt resolution i priorytetów
✗ zła konsolidacja pamięci powoduje dryf systemowy
Relevancja dla naszego systemu: bardzo wysoka — szczególnie do trzymania uzgodnień projektowych, słownika klienta i wcześniejszych decyzji konfiguracyjnych.
Link / źródło: OpenAI long-term memory pattern; ADK MemoryService; LangGraph long-term memory.

Externalized state + isolated workspaces

Kategoria: długoterminowość
Źródło: OpenAI long-horizon Codex; Claude subagent isolation
Krótki opis: Długi bieg agenta opiera się nie na „gigantycznym promptcie”, lecz na pętli operującej na zewnętrznym stanie: plikach, repo, logach, worktrees, artefaktach. Izolowane workspace’y redukują interferencję między równoległymi zadaniami.
Gdzie stosowane w praktyce: Codex podkreśla externalized state i isolated runs; Claude subagents mogą działać w osobnych git worktrees.
Trade-offy:
✓ lepsza koherencja długich zadań i prostszy review diffs
✓ ogranicza “cross-run contamination”
✗ wymaga dyscypliny w zarządzaniu artefaktami i cleanup
✗ nie zastępuje pamięci semantycznej — tylko ją uzupełnia
Relevancja dla naszego systemu: wysoka — plan zmian, diff konfiguracji, log walidacji i artefakty migracji powinny być poza promptem.
Link / źródło: Codex long-horizon loop; Claude isolated worktrees.

Czego nie znalazłem jako ustabilizowanych, dobrze nazwanych wzorców

Blast radius assessment jako formalnie nazwany, szeroko przyjęty pattern architektoniczny dla LLM agentów — znalazłem raczej praktykę governance: high-risk action gates, reversibility checks i tool-scoped approvals, niż jedno ustalone pojęcie. Najbliższe temu są policy gates oraz transakcyjno-kompensacyjne podejście do tool use.

Periodic alignment jako osobny, uznany wzorzec — są praktyki regularnych review, evals i checkpointów, ale nie znalazłem stabilnej literatury traktującej to jako nazwany pattern na poziomie architektury agentowej.

Role injection vs role inheritance jako formalna para pojęć architektonicznych — „inheritance” pojawia się w dokumentacjach narzędzi/modelu/uprawnień, a „injection” raczej w prompt templating i skill loading, ale nie jako ustandaryzowana taksonomia wzorców ról.

Bootstrap paradox jako nazwany pattern — frameworki rozwiązują go pragmatycznie przez layered prompts, static registries, enum dispatch i preloaded skills, nie przez jedną formalną konstrukcję teoretyczną.

Rollback pełnego stanu świata zewnętrznego jako dojrzały standard frameworkowy — dobrze wspierane są checkpointy grafu i resume, ale rollback skutków ubocznych w systemach zewnętrznych dopiero wchodzi w bardziej formalne ujęcia typu transactional tool use.

Jedna kanoniczna taksonomia wzorców orchestracji dla LLM — nie znalazłem. Zamiast tego istnieje kilka częściowo nakładających się katalogów: OpenAI, Azure, ADK, LangGraph i survey o collaboration mechanisms.

Najkrótszy wniosek projektowy: dla ERP stawiałbym na płytką hierarchię + deterministyczny workflow shell + critic loop + HITL na high-risk actions + checkpointed state + trajectory eval + compaction i pamięć skonsolidowaną. Swarm/emergent orchestration traktowałbym jako narzędzie do analizy i review, nie jako domyślny silnik wykonawczy.

Mogę też z tego zrobić drugą warstwę: mapę decyzji architektonicznych dla Waszego systemu ERP w stylu „kiedy użyć którego wzorca i kiedy go nie używać”.