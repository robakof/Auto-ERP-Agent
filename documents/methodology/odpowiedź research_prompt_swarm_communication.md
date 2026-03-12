Zbieram to w dwóch warstwach: najpierw klasyczne wzorce i taksonomię pamięci, potem sprawdzę jak to mapują współczesne frameworki LLM. Skupię się na źródłach pierwotnych: paperach, oficjalnej dokumentacji i repozytoriach.

Mam już dwa mocne wnioski. Po pierwsze, LangGraph nie jest „czystym shared memory” — rdzeń to współdzielony State, ale sam silnik grafu jest opisany jako message-passing; po drugie, Swarm/OpenAI pozostaje zasadniczo stateless i opiera się na handoffach oraz współdzielonym kontekście rozmowy, nie na czarnej tablicy czy tuple space.

Thought for 10m 5s

Poniżej masz syntetyczne rozpoznanie wzorców „shared cognitive space” dla systemów wieloagentowych LLM. Najkrótszy wniosek jest taki: najbliższymi odpowiednikami waszej warstwy „myśli” są dziś blackboard, global workspace i semantyczna pamięć zewnętrzna (vector/archival store). Tuple space/Linda to bardzo trafny przodek koncepcyjny, ale nie widzę dziś jego silnej, jawnie nazwanej adopcji w mainstreamowych frameworkach LLM. Stigmergy pasuje jako metafora i kierunek badawczy, lecz w LLM-ach pozostaje raczej niszą niż ustalonym patternem. W praktyce produkcyjnej dominują dziś trzy rozwiązania: shared state workflow (LangGraph), shared conversation context + handoffs (Swarm, AutoGen) oraz external memory / semantic retrieval (Letta, Mem0, CrewAI).

1) Wzorce architektoniczne
Blackboard architecture

Źródło: klasyczny AI; model blackboard wyrósł z systemów takich jak Hearsay-II. W nowszych pracach pojawia się też wprost w LLM multi-agent systems.

Krótki opis: Wzorzec polega na tym, że wiele wyspecjalizowanych „knowledge sources” czyta i zapisuje do wspólnej tablicy, a sterowanie wynika z aktualnego stanu tej tablicy, a nie z adresowanych wiadomości między komponentami. To jest niemal książkowy odpowiednik waszej warstwy „myśli”: zapis do wspólnej przestrzeni, a nie „wyślij do X”.

Gdzie stosowane:
W klasycznym AI: Hearsay-II i rodzina systemów blackboard. W LLM-ach pojawiają się już jawne implementacje, np. LbMAS („Exploring Advanced LLM Multi-Agent Systems Based on Blackboard Architecture”) oraz system do information discovery in data science, gdzie agenci pomocniczy monitorują wspólną tablicę i sami decydują, czy wziąć udział.

Trade-offy:
✓ bardzo dobre odsprzężenie agentów;
✓ naturalne opportunistic activation — agent reaguje, gdy widzi istotny wpis;
✓ dobrze wspiera heterogeniczne role i równoległość;
✓ bardzo blisko waszego modelu „tagowane myśli bez adresata”.
✗ potrzebuje polityki kontroli tablicy: priorytetów, arbitrażu, odśmiecania;
✗ rosną koszty tokenowe i runtime, jeśli wielu agentów stale „nasłuchuje” tablicy;
✗ trudniej pilnować spójności, duplikatów i provenance. W jednej pracy blackboard poprawiał jakość względem baseline’ów, ale koszt tokenowy był wyższy niż w układach RAG/master-slave.

Związek z waszą architekturą:
To jest najbliższy klasyczny odpowiednik warstwy 3. Jeśli chcecie „telepathy pattern”, blackboard jest najbardziej trafną nazwą historyczną i architektoniczną. Różnica: klasyczny blackboard zwykle zakłada też jakiś mechanizm sterowania/agendy, a nie tylko samą przestrzeń pamięci.

Źródła: Hearsay-II / blackboard literature; LbMAS; LLM blackboard for data science.

Tuple space / Linda paradigm

Źródło: David Gelernter, Linda, 1985.

Krótki opis: Linda wprowadza generative communication przez współdzieloną przestrzeń krotek. Procesy nie komunikują się bezpośrednio; zamiast tego wykonują operacje typu out, in, read na tuple space, czyli anonimowej, współdzielonej przestrzeni danych.

Gdzie stosowane:
Historycznie i w systemach rozproszonych/multi-agent jako model asynchronicznej, anonimowej, content-based komunikacji; później także w implementacjach typu JavaSpaces i TSpaces. Wprost w LLM multi-agent frameworks nie znalazłem dziś prominentnego frameworka, który jawnie nazywałby swój model Linda/tuple space. Najbliższe odpowiedniki to blackboardy, współdzielone store’y i vector DB pełniące rolę content-addressable shared memory.

Trade-offy:
✓ bardzo mocne odsprzężenie w czasie i przestrzeni;
✓ naturalne dla anonymous coordination;
✓ dobrze wspiera content-based retrieval zamiast routingu po adresatach.
✗ bezpieczeństwo i governance są trudne: otwarte tuple space ułatwia podsłuchiwanie/fałszowanie wpisów;
✗ trzeba pilnować schematów, TTL/lease, garbage collection i polityk dostępu;
✗ dopasowywanie po wzorcach może być kosztowne lub nieprecyzyjne.

Związek z waszą architekturą:
Koncepcyjnie to bardzo silny przodek waszej warstwy „myśli”: zapisujesz treść do wspólnej przestrzeni i inni ją znajdują po treści/wzorcu, nie po adresacie. Jeśli chcecie nazwę bardziej „systems/distributed computing” niż „AI/cognitive”, Linda jest bardzo dobrym odniesieniem — nawet jeśli dzisiejsze frameworki LLM rzadko używają tej etykiety.

Źródła: Gelernter 1985; survey/overview Linda in MAS.

Stigmergy

Źródło: pojęcie wprowadzone przez Grassé; później rozwijane w swarm intelligence i MAS.

Krótki opis: Stigmergia to pośrednia koordynacja przez środowisko: agent zostawia ślad, a ślad wpływa na zachowanie kolejnych agentów. Komunikacja nie biegnie kanałem wiadomości, tylko przez modyfikację współdzielonego środowiska.

Gdzie stosowane:
Klasycznie w swarm systems, robotyce, manufacturing control i distributed coordination. Istnieją także ujęcia typu virtual stigmergy i cognitive stigmergy dla agentów bardziej „poznawczych”. Natomiast wprost dla LLM multi-agent systems nie widzę dziś silnego, szeroko przyjętego nurtu implementacyjnego pod tą nazwą; to raczej rama interpretacyjna niż dominujący pattern frameworków.

Trade-offy:
✓ skrajnie dobre odsprzężenie i asynchroniczność;
✓ brak potrzeby routingu i centralnego koordynatora;
✓ dobrze skaluje się przy lokalnych regułach reagowania na ślady.
✗ słaba jawność intencji i provenance;
✗ ryzyko „zanieczyszczenia środowiska” starymi śladami;
✗ trudniej debugować, dlaczego agent zareagował na dany stan;
✗ w LLM-ach brak jeszcze stabilnych, standardowych implementacji i benchmarków.

Związek z waszą architekturą:
Jeśli wasza warstwa 3 ma działać tak, że agent „zostawia feromon” w pamięci współdzielonej, a inni to wykrywają po tagach/semantyce, to stigmergia jest bardzo dobrą metaforą badawczą. Jako nazwa architektoniczna dla LLM systemu byłbym ostrożny: dziś łatwiej obronić termin blackboard albo shared memory / global workspace.

Źródła: definicje stigmergii; virtual/cognitive stigmergy.

Global Workspace Theory

Źródło: Bernard Baars; później inspiracja dla cognitive architectures i niektórych systemów LLM.

Krótki opis: GWT modeluje poznanie jako mechanizm, w którym wybrane treści trafiają do global workspace i są „broadcastowane” do wyspecjalizowanych modułów. Historycznie jest to blisko spokrewnione z blackboard architecture.

Gdzie stosowane:
W klasycznej kognitywistyce i cognitive architectures; w LLM-ach są już przykłady inspirowane GWT, np. Sibyl, gdzie global workspace zarządza wiedzą i historią konwersacji dla wielu modułów, oraz CogniPair, które jawnie opisuje implementację inspirowaną GWT.

Trade-offy:
✓ daje czytelny model broadcast medium;
✓ dobrze wspiera selektywne „uświadamianie” istotnych treści dla wielu modułów;
✓ naturalny most między blackboard a bardziej poznawczą narracją.
✗ zwykle wymaga mechanizmu selekcji: co trafia do workspace, kto może czytać, z jakim priorytetem;
✗ łatwo przeciążyć workspace zbyt dużą ilością treści;
✗ w praktyce LLM jest to nadal raczej nisza badawcza niż standard frameworków.

Związek z waszą architekturą:
Jeżeli chcecie opisać warstwę 3 bardziej „poznawczo” niż „systemowo”, global workspace jest mocnym kandydatem. Różnica wobec tuple space: GWT akcentuje raczej broadcast/shared awareness, a Linda — anonymous shared coordination by content.

Źródła: Baars-inspired systems; Sibyl; CogniPair.

Publish-subscribe vs shared memory

Źródło: klasyczne distributed systems; dla shared-memory/content-based coordination dobrym punktem odniesienia są Linda i blackboard.

Krótki opis:
Publish-subscribe to zdarzeniowy model push: nadawca publikuje event na topic, a broker dostarcza go subskrybentom. Shared memory/blackboard/tuple space to model pull/read-write: agenci czytają i aktualizują wspólny stan lub wspólną przestrzeń danych.

Gdzie stosowane:
Pub-sub dominuje tam, gdzie ważne są reakcje na zdarzenia, streaming i luźne powiązanie nadawca–odbiorca. Shared memory dominuje tam, gdzie liczy się stan współdzielony, content-based lookup, późne wiązanie i opportunistic coordination.

Trade-offy:
✓ Pub-sub: prostsze dla eventing, naturalne dla triggerów, łatwiejszy auditing eventów.
✗ Pub-sub: nadal jest to komunikacja „o czymś do kogoś/subskrybentów”; gorzej nadaje się do wspólnej pamięci semantycznej i do późnego odkrywania treści.
✓ Shared memory: lepsze dla wspólnej wiedzy, semantycznego szukania i pracy na aktualnym stanie.
✗ Shared memory: trudniejsze zarządzanie konfliktem, wersjonowaniem, garbage collection i jakością pamięci.

Związek z waszą architekturą:
Wasza warstwa 2 to raczej message passing / pub-sub / handoff, a warstwa 3 to shared memory. W praktyce wiele dobrych architektur robi hybrydę: shared memory dla „myśli” i pub-sub tylko dla zdarzeń wymagających niskiej latencji.

Źródła: pub-sub decoupling; Linda/shared-space communication; blackboard practice.

2) Nowoczesne frameworki LLM
LangGraph

Źródło: oficjalna dokumentacja LangGraph i LangMem.

Krótki opis: LangGraph buduje agenty jako graf stanów. Każdy node czyta i aktualizuje współdzielony State, a short-term memory jest zwykle thread-scoped i persystowana przez checkpointer; long-term memory może być trzymana w store’ach i namespace’ach współdzielonych między wątkami. Jednocześnie sam silnik jest jawnie opisywany jako graph execution z korzeniami w message passing / Pregel-like semantics.

Gdzie stosowane:
Workflow agents, multi-agent graphs, deterministic orchestration, subgraphs, handoffs i pamięć długoterminowa w ekosystemie LangChain/LangGraph.

Trade-offy:
✓ bardzo czytelny shared state model;
✓ dobra kontrola przepływu, checkpointing i durability;
✓ łatwo dobudować pamięć długoterminową i namespace’y.
✗ to nie jest „otwarta telepatia” z definicji;
✗ bliżej mu do stateful workflow engine niż do czystego blackboard;
✗ zbyt duży kontekst i zbyt dużo pamięci pogarsza koszt i może rozpraszać model.

Związek z waszą architekturą:
LangGraph bardzo dobrze obsługuje warstwę 2 i „lokalny shared state”, ale dla warstwy 3 trzeba zwykle dołożyć własny store/pattern wyszukiwania po tagach/semantyce. To raczej shared state orchestration niż blackboard.

Źródła: LangGraph overview; memory docs; LangMem concepts.

AutoGen (Microsoft)

Źródło: oficjalna dokumentacja AutoGen.

Krótki opis: AutoGen pozostaje zasadniczo message-centric: teamy, group chat, selector group chat, swarm, handoffs. Agenci są jednak stateful, a framework ma też warstwę pamięci z protokołem add/query/update_context, więc komunikacja nie kończy się na samych wiadomościach.

Gdzie stosowane:
GroupChat/SelectorGroupChat, Swarm, GraphFlow, RAG i memory adapters. Wariant swarm w AutoGen jest opisywany jako wspólny kontekst rozmowy i lokalne decyzje agentów o przejęciu prowadzenia przez handoff.

Trade-offy:
✓ wygodne dla klasycznego dialogu między agentami;
✓ wspiera handoffs i współdzielony kontekst rozmowy;
✓ ma hooki pamięciowe poza czystym chatem.
✗ rdzeń nadal jest chat/team orchestration, nie blackboard;
✗ shared memory jest dodatkiem, nie główną metaforą architektoniczną;
✗ przy dużych teamach łatwo rośnie koszt wspólnego kontekstu.

Związek z waszą architekturą:
AutoGen dobrze wspiera warstwę 2. Warstwę 3 da się dobudować przez memory/RAG, ale nie jest to jego domyślny idiom.

Źródła: AutoGen memory docs; swarm docs; stateful agents docs.

CrewAI

Źródło: oficjalna dokumentacja CrewAI.

Krótki opis: CrewAI łączy jawne delegation/Q&A między agentami z warstwą pamięci i knowledge sources. W nowszym API pamięć jest ujednolicona w obiekcie Memory, a ranking wspomnień łączy semantykę, recency i importance.

Gdzie stosowane:
Crew-level collaboration, task delegation, crew memory, knowledge sources współdzielone przez załogę agentów. Dokumentacja opisuje też, że pamięć crew może być domyślnie współdzielona między agentami, z możliwością scope’owania.

Trade-offy:
✓ praktyczny model „zespół agentów + wspólna pamięć”;
✓ pamięć ma już scoring i retrieval, więc dobrze wspiera kontekst;
✓ knowledge sources dobrze wspierają wspólną bazę wiedzy.
✗ sama współpraca między agentami nadal jest w dużej mierze explicit delegation;
✗ shared memory pełni rolę retrieval substrate, nie klasycznej blackboard agenda;
✗ mniej eleganckie dla czystego „myśli bez adresata” niż blackboard/tuple-space.

Związek z waszą architekturą:
CrewAI jest bliżej modelu „warstwa 2 + wspólne zaplecze pamięciowe” niż pełnej warstwy 3 jako centralnego mechanizmu koordynacji.

Źródła: CrewAI memory & collaboration docs.

Swarm (OpenAI)

Źródło: repozytorium i dokumentacja OpenAI Swarm; odniesienia w AutoGen.

Krótki opis: Swarm to lekki, edukacyjny framework oparty na routines i handoffs. Jest jawnie opisany jako stateless between calls, więc sam z siebie nie jest frameworkiem blackboard/shared-memory; pamięć trzeba dołożyć zewnętrznie albo utrzymywać we współdzielonym kontekście rozmowy.

Gdzie stosowane:
Jako prosty model wieloagentowy z przełączaniem odpowiedzialności między wyspecjalizowanymi agentami; koncepcyjnie zainspirował także „swarm” pattern w AutoGen.

Trade-offy:
✓ bardzo prosty model sterowania;
✓ dobry do handoffs i podziału kompetencji;
✓ mały narzut architektoniczny.
✗ brak wbudowanej shared memory;
✗ nie jest to telepathy/blackboard pattern;
✗ przy większych systemach szybko trzeba dobudować pamięć i governance poza frameworkiem.

Związek z waszą architekturą:
Swarm dobrze mapuje się na warstwę 2, ale nie na warstwę 3. Sama nazwa „swarm” opisuje raczej styl współpracy wielu wyspecjalizowanych agentów niż konkretny mechanizm shared memory.

Źródła: OpenAI Swarm repo/docs; AutoGen swarm docs.

mem0

Źródło: dokumentacja mem0 i OpenMemory.

Krótki opis: mem0 to framework pamięci dla agentów, który wyróżnia m.in. factual, episodic i semantic memory. OpenMemory rozwija to w stronę shared persistent memory layer z ujednoliconymi operacjami pamięciowymi (add, search, list, delete) i integracją przez MCP.

Gdzie stosowane:
Jako external memory subsystem dla agentów i narzędzi; także jako workspace/team memory across projects and agents.

Trade-offy:
✓ bardzo blisko modelu „semantic shared memory”;
✓ stateful memory zamiast czysto stateless RAG;
✓ dobre jako warstwa 3 niezależna od konkretnego orchestratora.
✗ to nie jest pełny orchestration framework;
✗ wymaga polityki zapisu, aktualizacji i deduplikacji;
✗ bez dobrego write-path łatwo zapchać pamięć mało wartościowymi wpisami.

Związek z waszą architekturą:
mem0 to jeden z najbliższych współczesnych odpowiedników waszej warstwy „myśli jako shared memory”.

Źródła: mem0 docs; OpenMemory docs.

Letta / MemGPT

Źródło: Letta docs i MemGPT paper/overview.

Krótki opis: Letta rozwija ideę MemGPT: agent ma kilka warstw pamięci, z których część jest pinned in-context (core memory / memory blocks), a część jest archival memory — semantycznie przeszukiwalną bazą długoterminową. Istotne dla was: Letta wspiera też shared memory blocks pomiędzy wieloma agentami.

Gdzie stosowane:
Persistent agents, multi-agent shared memory, memory blocks, files, archival memory i external DB przez tool calling. Archival memory jest opisana jako vector DB z operacjami insert/search.

Trade-offy:
✓ bardzo dojrzały model rozróżnienia pamięci „gorącej” i „archiwalnej”;
✓ shared blocks są mocnym odpowiednikiem wspólnej przestrzeni roboczej;
✓ archival memory dobrze wspiera semantic retrieval.
✗ trzeba pilnować konkurencyjnych aktualizacji shared blocks;
✗ pamięć archiwalna sama z siebie nie rozwiązuje arbitrażu i kontroli jakości;
✗ rozdział między „co trzymać pinned”, a „co odłożyć do archiwum” wymaga polityki.

Związek z waszą architekturą:
Letta daje chyba najczystszy praktyczny odpowiednik waszych trzech warstw:
dyrektywy ≈ procedural/core memory,
wiadomości ≈ conversation/tool calls/handoffs,
myśli ≈ shared blocks + archival memory.

Źródła: Letta memory architecture docs; shared memory blocks docs; MemGPT overview.

3) Taksonomia pamięci agentów LLM
Czy istnieje standard?

Wniosek: nie ma jednego, w pełni ustalonego standardu, ale widać dziś dwie dominujące linie klasyfikacji. Recent work wskazuje z jednej strony linię „kognitywną” (working / semantic / episodic / procedural), z drugiej — linię „inżynierską” (message buffer / core memory / archival memory i podobne hierarchie storage).

Taksonomia kognitywna: working / episodic / semantic / procedural

Źródło: CoALA; później LangMem/LangGraph docs.

Krótki opis:
To dziś najbliższy kandydat na „quasi-standard”. CoALA porządkuje agenta wokół working memory, long-term memory i działania, a w pamięci długoterminowej wyróżnia episodic, semantic i procedural. Ten sam podział pojawia się potem bardzo wyraźnie w LangMem.

Znaczenia:

Working memory — bieżący stan roboczy utrzymywany między wywołaniami modelu.

Episodic memory — zapis doświadczeń, trajektorii i przebiegów działań agenta.

Semantic memory — fakty, profile, preferencje, uogólniona wiedza o świecie i użytkowniku.

Procedural memory — reguły zachowania, polityki, instrukcje, „how to behave”.

Trade-offy:
✓ bardzo czytelne mapowanie do psychologii poznawczej;
✓ dobrze rozdziela „co agent wie” od „jak agent działa”;
✓ przydatne projektowo dla waszych 3 warstw.
✗ w praktyce granice się zacierają;
✗ frameworki różnią się implementacją i namingiem;
✗ procedural memory bywa ryzykowna do automatycznych zapisów, bo wpływa na politykę zachowania agenta.

Związek z waszą architekturą:
To bardzo ładnie mapuje się na wasz model:
warstwa 1 „dyrektywy” ≈ procedural,
warstwa 2 „wiadomości” ≈ część working memory / interaction history,
warstwa 3 „myśli” ≈ głównie episodic + semantic.

Źródła: CoALA; LangMem conceptual guide.

Taksonomia inżynierska: buffer / core / archival / files / external store

Źródło: Letta / MemGPT.

Krótki opis:
To bardziej praktyczna taksonomia implementacyjna: co jest w kontekście modelu, co jest przypiętą pamięcią roboczą, a co jest archiwum semantycznie przeszukiwalnym. Letta dodatkowo wprost wspiera memory blocks, files i external DB.

Trade-offy:
✓ świetna dla system design i kosztów;
✓ pomaga rozdzielić „hot memory” od „cold memory”;
✓ naturalna dla produkcyjnych agentów z ograniczonym context window.
✗ mniej elegancka poznawczo;
✗ mniej przenośna między frameworkami jako nomenklatura teoretyczna.

Związek z waszą architekturą:
Dla projektowania systemu jest często użyteczniejsza niż czysta taksonomia psychologiczna. Wasza warstwa 3 prawdopodobnie potrzebuje właśnie takiego podziału: shared hot memory + archival semantic store.

4) Semantic search jako wspólna pamięć
Semantic retrieval / vector store as shared memory

Źródło: Letta archival memory; mem0/OpenMemory; Generative Agents; survey pamięci agentów.

Krótki opis:
Wzorzec polega na tym, że agenci zapisują obserwacje, fakty lub „myśli” do zewnętrznego store’a, a inni agenci odczytują je przez semantic search. W dokumentacji bywa to opisywane jako archival memory, memory store, shared persistent memory albo shared conversational memory pool; rzadziej jako formalnie nazwany pattern architektoniczny.

Gdzie stosowane:

Letta: archival memory jako semantycznie przeszukiwalna vector DB.

mem0/OpenMemory: shared persistent memory layer.

Generative Agents: retrieval łączy relevance, recency i importance dla memory stream.

badawczo: wspólne memory pools i collaborative memory with private/shared scopes.

Trade-offy:
✓ bardzo naturalne dla warstwy „myśli”;
✓ content-based access bez adresata;
✓ dobrze skaluje się dla dużej liczby wpisów i agentów;
✓ pozwala oddzielić krótką pamięć roboczą od długiej.
✗ problem precision/recall retrievalu: zbyt agresywna ekstrakcja obniża precyzję, zbyt oszczędna — recall;
✗ długi lub zanieczyszczony kontekst rozprasza model i zwiększa koszt;
✗ trzeba rozwiązać write filtering, contradiction handling, privacy/governance i aktualizację pamięci.

Związek z waszą architekturą:
To jest dziś najbardziej praktyczna implementacja warstwy 3. Architektonicznie nazwałbym to raczej shared semantic memory albo archival/shared memory layer niż formalny, powszechnie uznany „pattern” jednej nazwy.

Źródła: Letta docs; mem0/OpenMemory; Generative Agents; memory survey.

5) Stigmergy w AI i LLM — czy ktoś to naprawdę próbuje?
Stigmergic / shared-pool coordination in AI

Źródło: stigmergy literature; virtual stigmergy; shared conversational memory pool papers.

Krótki opis:
Tak — w AI/MAS stigmergia jest realnie używana jako idea pośredniej koordynacji przez środowisko. W LLM-ach widzę dziś raczej stigmergy-adjacent rozwiązania: shared memory pool, collaborative memory, blackboard-like cooperation, a nie szeroko przyjęty framework otwarcie brandowany jako „stigmergic LLM system”.

Gdzie stosowane:
W klasycznych MAS, swarm robotics, manufacturing i virtual stigmergy. Dla LLM — bardziej jako inspiracja: async memory sharing, blackboard cooperation, collaborative memory.

Trade-offy:
✓ świetna intuicja projektowa dla „telepathy pattern”;
✓ dobrze wspiera emergent coordination bez jawnej orkiestracji;
✓ może być bardzo elastyczna.
✗ mało ustabilizowanych benchmarków LLM;
✗ governance i interpretowalność są trudne;
✗ ryzyko chaosu rośnie wraz z liczbą agentów i śladów.

Związek z waszą architekturą:
Jako termin badawczy — tak, bardzo trafny. Jako nazwa, którą łatwo zrozumie inżynier systemów lub recenzent architektury — zwykle lepiej zadziała blackboard, global workspace albo shared semantic memory.

Źródła: stigmergy references; virtual stigmergy; asynchronous shared-memory papers.

Najważniejsze odpowiedzi na twoje priorytety
1. Blackboard + Tuple space

Najmocniejsza odpowiedź brzmi: blackboard ma już współczesne implementacje LLM i jest najbliższą klasyczną nazwą dla waszej warstwy „myśli”. Tuple space/Linda jest równie trafna koncepcyjnie, ale dziś wygląda bardziej jak historyczny i teoretyczny przodek niż aktywnie brandowany pattern w mainstreamowych frameworkach LLM.

2. Taksonomia pamięci

Najbliższy „konsensus” to dziś: working / episodic / semantic / procedural — szczególnie po CoALA i jego adopcji w ekosystemie LangGraph/LangMem. Równolegle istnieje praktyczna taksonomia inżynierska w duchu Letta/MemGPT: context/core vs archival/external memory.

3. LangGraph / AutoGen / CrewAI

LangGraph: shared state + stores, ale execution model jest bliżej workflow/message passing niż blackboard.

AutoGen: głównie team chat, group chat, handoffs; pamięć jest dodatkiem, nie główną metaforą.

CrewAI: delegation plus shared memory/knowledge sources; shared memory jest retrieval substrate, nie centralnym mechanizmem koordynacji.

4. Stigmergy

Tak jako inspiracja; nie jako obecny mainstream framework pattern dla LLM. Najbliższe praktyczne wcielenia to blackboard i shared memory pool.

Rekomendacja nazewnicza dla waszego projektu

Gdybym miał nazwać waszą warstwę 3 w sposób najmocniej osadzony w literaturze i jednocześnie zrozumiały technicznie, to ranking byłby taki:

1. Blackboard memory / blackboard coordination
Najlepsze, jeśli chcecie podkreślić wspólną przestrzeń roboczą i opportunistic coordination.

2. Shared semantic memory / archival shared memory
Najlepsze, jeśli implementacja jest oparta głównie na vector store i semantic retrieval.

3. Global workspace
Najlepsze, jeśli chcecie język bardziej poznawczy niż systemowy.

4. Stigmergic coordination
Dobre jako framing badawczy, ale dziś słabsze jako nazwa „mainstreamowa”.

Jeśli chcesz, mogę w następnym kroku przerobić to na krótką tabelę porównawczą 1-stronicową: pattern → mechanizm → kiedy używać → kiedy nie używać.