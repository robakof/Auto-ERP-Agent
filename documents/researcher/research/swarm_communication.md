# Research: Wzorce komunikacji i pamięci w systemach wieloagentowych

**Data:** 2026-03-12
**Status:** Ukończony (wiedza treningowa, brak dostępu do live web)

---

## Cel

Zebrać wzorce architektoniczne klasy "shared cognitive space" — alternatywy dla message-passing między agentami LLM. Nie tutoriale — nazwy, wzorce, trade-offy.

---

## 1. Wzorce architektoniczne — klasyczne i nowoczesne

---

### Blackboard Architecture

**Źródło:** Newell & Simon (1972) — Human Problem Solving; rozwinięte w systemie HEARSAY-II (1980, CMU) do rozpoznawania mowy; skodyfikowane przez Hayes-Roth (1985). Wzorzec GoF nie obejmuje bezpośrednio, ale jest standardem w AI.

**Krótki opis:** Architektura, w której wiele niezależnych modułów ("knowledge sources") czyta i zapisuje dane na wspólną strukturę danych ("blackboard"). Żaden moduł nie komunikuje się bezpośrednio z innym — jedynym medium jest tablica. Kontroler (scheduler) decyduje, który moduł działa w danym momencie na podstawie stanu tablicy.

**Gdzie stosowane:**
- Klasyczne: HEARSAY-II (mowa), CRYSALIS (analiza białek), BB1 (planner)
- Nowoczesne systemy wieloagentowe LLM: LangGraph (state jako blackboard), niektóre implementacje AutoGen z SharedMemory, Semantic Kernel z shared context
- AgentOS, Voyager (Minecraft agent od Nvidia/CMU) — skill library jako wariant blackboardu

**Trade-offy:**
  ✓ Pełna decoupling między agentami — nikt nie zna adresu odbiorcy
  ✓ Naturalny audit trail — stan tablicy jest obserwowalny w każdym kroku
  ✓ Łatwo dodać nowego agenta bez zmiany innych (open/closed principle)
  ✓ Działa dobrze gdy problem jest "incremental refinement" — każdy agent dokłada fragment
  ✗ Wąskie gardło przy wysokiej częstotliwości zapisu — tablica staje się bottleneckiem
  ✗ Kontroler / scheduler jest trudny do projektowania — kto decyduje kto pisze?
  ✗ Brak gwarancji kolejności — race conditions jeśli nie ma synchronizacji
  ✗ Słaba skalowalność horyzontalna (klasyczna implementacja synchroniczna)

**Związek z naszą architekturą:** Warstwa "myśli" (shared memory tematyczna) to bezpośrednia implementacja blackboardu — agent zapisuje myśl bez adresata, inny odpytuje stan. Tablica = wspólna przestrzeń myśli. Różnica: brak centralnego kontrolera (agenci odpytują samodzielnie).

**Linki / źródła:**
- Hayes-Roth, B. (1985). "A blackboard architecture for control." Artificial Intelligence, 26(3), 251-321.
- Corkill, D.D. (1991). "Blackboard systems." AI Expert, 6(9), 40-47.
- Wikipedia: Blackboard (design pattern) — zawiera diagram komponentów

---

### Tuple Space / Linda Paradigm

**Źródło:** David Gelernter, Yale University (1985). Język koordynacyjny Linda opisany w: Gelernter (1985) "Generative communication in Linda." ACM TOPLAS 7(1).

**Krótki opis:** Współdzielona przestrzeń krotek (par klucz-wartość lub struktur typowanych), do której dowolny proces może zapisywać (`out`), odczytywać niedestrukcyjnie (`rd`) lub pobierać i usuwać (`in`). Dopasowanie jest pattern-matching po strukturze krotki, nie po adresie. Komunikacja jest całkowicie anonimowa i asynchroniczna — producent i konsument nie muszą istnieć w tym samym czasie.

**Gdzie stosowane:**
- Klasyczne: JavaSpaces (Sun/Jini, 1999), TSpaces (IBM), GigaSpaces
- Distributed computing: Apache River
- Nowoczesne LLM: brak bezpośrednich implementacji pod nazwą "tuple space", ale wzorzec jest obecny w: Redis jako shared store (pattern matching po kluczach), Apache Kafka (topics jako przestrzeń krotek czasowych), niektóre implementacje RAG gdzie vector store pełni rolę przestrzeni krotek semantycznych
- Akademicko: propozycje "LindaLLM" i "Space-based multi-agent" pojawiają się w literaturze 2023-2024

**Trade-offy:**
  ✓ Całkowita anonimowość — producent nie wie kto skonsumuje
  ✓ Time decoupling — można zapisać krotkę zanim konsument istnieje
  ✓ Pattern matching zamiast adresowania — naturalny dla semantycznego wyszukiwania
  ✓ Bardzo prosty model programowania (3 operacje: out/rd/in)
  ✗ Brak kolejności — jeśli wiele agentów robi `in` na ten sam wzorzec, który dostanie krotkę?
  ✗ "Lost update" problem — `in` usuwa krotkę, więc jest destruktywne
  ✗ Brak wbudowanego mechanizmu powiadamiania (polling vs event-driven)
  ✗ Słaba wydajność przy dużej przestrzeni krotek bez indeksowania

**Związek z naszą architekturą:** Warstwa myśli jako tuple space: agent zapisuje `(tag="rozrachunki", mysl="...", autor="ERP Specialist")`, inny agent robi `rd(tag="rozrachunki")`. Semantyczne wyszukiwanie po tagach = pattern matching. Kluczowa różnica w stosunku do klasycznej Lindy: nie chcemy destruktywnego `in` — myśli powinny być persistentne (rd, nie in).

**Linki / źródła:**
- Gelernter, D. (1985). "Generative communication in Linda." ACM TOPLAS, 7(1), 80-112.
- Carriero, N., & Gelernter, D. (1989). "Linda in context." CACM, 32(4), 444-458.
- Freeman, E., et al. (1999). "JavaSpaces Principles, Patterns, and Practice." Addison-Wesley.

---

### Stigmergy

**Źródło:** Pierre-Paul Grassé (1959) — obserwacje termitów. Nazwa pochodzi od greckiego: stigma (znak) + ergon (praca). Sformalizowane jako wzorzec inżynierii rojowej przez Dorigo i Bonabeau (2000).

**Krótki opis:** Forma pośredniej komunikacji, w której agent modyfikuje środowisko (zostawia "ślad"), a kolejny agent reaguje na zmiany środowiska, nie na wiadomość od poprzednika. Mrówki zostawiają feromon — inne mrówki nie "rozmawiają" z pierwszą, tylko reagują na feromony. Koordynacja wyłania się bez centralnego kontrolera.

**Gdzie stosowane:**
- Klasyczne: Ant Colony Optimization (ACO), algorytmy rojowe
- Nowoczesne AI: rzadko pod tą nazwą, ale wzorzec jest obecny w:
  - Systemy z shared memory gdzie agenci modyfikują stan (np. tabela priorytetów zadań jako "feromon")
  - Voyager (agent Minecraft) — skill library: agent zapisuje skrypt, inny agent "widzi" że skrypt istnieje i buduje na nim
  - Niektóre implementacje CrewAI gdzie task output jest dostępny dla kolejnych agentów (implicit stigmergy)
- Akademicko: Dorri et al. (2018) "Multi-Agent Systems: A Survey" wymienia stigmergy jako jeden z modeli koordynacji

**Trade-offy:**
  ✓ Zero coupling między agentami — nikt nikomu nic nie wysyła
  ✓ Emergentna koordynacja — zachowanie globalne wyłania się bez projektowania
  ✓ Odporność na awarie agentów (środowisko persystuje niezależnie od agentów)
  ✓ Naturalne dla problemów optymalizacyjnych (ścieżki, priorytety)
  ✗ Trudne do debugowania — dlaczego agent zachował się tak? Bo "feromon" był taki
  ✗ Brak gwarancji zbieżności — może prowadzić do lokalnych optimów
  ✗ Wymaga "ewaporacji" śladów — stare ślady muszą maleć, inaczej system utknął
  ✗ Dla LLM: nie ma naturalnego mechanizmu "ewaporacji" bez dodatkowej logiki

**Związek z naszą architekturą:** Warstwa myśli jako środowisko stigmergiczne: agent zostawia myśl jako "ślad", inny agent odpytuje środowisko i reaguje. Brakujący element: mechanizm "ewaporacji" — jak starzeją się myśli? Timestamp + TTL to odpowiednik ewaporacji feromonów.

**Linki / źródła:**
- Grassé, P.P. (1959). "La reconstruction du nid et les coordinations interindividuelles." Insectes Sociaux, 6(1), 41-80.
- Bonabeau, E., Dorigo, M., & Theraulaz, G. (1999). "Swarm Intelligence: From Natural to Artificial Systems." Oxford University Press.
- Dorri, A., Kanhere, S.S., & Jurdak, R. (2018). "Multi-Agent Systems: A Survey." IEEE Access, 6, 28573-28593.

---

### Global Workspace Theory (GWT)

**Źródło:** Bernard Baars (1988) — "A Cognitive Theory of Consciousness." Cambridge University Press. Zastosowanie do AI: Stan Franklin (1995, 2007) — system IDA/LIDA.

**Krótki opis:** Teoria świadomości jako "broadcast medium": mózg ma wiele wyspecjalizowanych, nieświadomych procesów (koalicje) które rywalizują o dostęp do globalnej przestrzeni roboczej. Ten kto wygra broadcast wysyła informację do wszystkich procesów jednocześnie. Świadomość = to co jest w global workspace. Franklin przełożył to na architekturę AI: LIDA (Learning Intelligent Distribution Agent) implementuje GWT jako model kognitywny.

**Gdzie stosowane:**
- Akademicko: IDA (Intelligent Distribution Agent, US Navy), LIDA (Learning IDA)
- Nowoczesne LLM: rzadko bezpośrednio, ale:
  - Koncepcyjnie blisko AutoGen GroupChat — jeden agent "ma głos" w danym turze (broadcast)
  - Salesforce AgentVerse (2023) — cytuje GWT explicite jako inspirację
  - Cognitive Architectures for Language Agents (CoALA, Sumers et al. 2023) — taksonomia pamięci oparta na teorii kognitywnej bliskiej GWT
- Teoretycznie: Bengio (2017, 2019) proponował "consciousness prior" jako wariant GWT dla deep learning

**Trade-offy:**
  ✓ Broadcast rozwiązuje problem "kto powinien wiedzieć" — wszyscy wiedzą
  ✓ Naturalny mechanizm priorytyzacji (rywalizacja o global workspace)
  ✓ Oddziela "uwagę" od "przetwarzania" — tylko ważne rzeczy trafiają do workspace
  ✗ Broadcast jest kosztowny w systemach rozproszonych
  ✗ Mechanizm rywalizacji ("koalicje") jest trudny do implementacji bez centralnego arbitera
  ✗ Nie skaluje się prosto — ile agentów może słuchać broadcast?
  ✗ W LLM: "global workspace" to kontekst okna — skończony i drogi

**Związek z naszą architekturą:** GWT sugeruje, że nie każda "myśl" powinna trafiać do wspólnej przestrzeni — tylko te z wysokim "activation level". To wskazuje na potrzebę mechanizmu selekcji: agent nie dumuje wszystkiego do shared memory, tylko to co ocenia jako ważne dla innych.

**Linki / źródła:**
- Baars, B.J. (1988). "A Cognitive Theory of Consciousness." Cambridge University Press.
- Franklin, S., et al. (2007). "LIDA: A computational model of global workspace theory and developmental learning." AAAI Spring Symposium.
- Sumers, T.R., et al. (2023). "Cognitive Architectures for Language Agents." arXiv:2309.02427.

---

### Publish-Subscribe vs Shared Memory

**Źródło:** Pub/Sub: skodyfikowany w Enterprise Integration Patterns (Hohpe & Woolf, 2003). Shared Memory: klasyczna architektura OS (POSIX shared memory, System V IPC).

**Krótki opis:**
- **Pub/Sub:** Producent publikuje wiadomość do "topiku" bez znajomości konsumentów. Konsument subskrybuje topik. Broker (Kafka, RabbitMQ) pośredniczy. Wiadomości są ephemeral (jeśli nikt nie subskrybuje, wiadomość ginie) lub persisted (log).
- **Shared Memory:** Przestrzeń danych dostępna dla wielu procesów jednocześnie. Brak pośrednika. Odczyt/zapis bezpośrednio. Wymaga synchronizacji (mutex, semaphore).

**Praktyczne różnice w systemach agentowych:**

| Wymiar | Pub/Sub | Shared Memory |
|--------|---------|---------------|
| Coupling | Topic coupling (nie address coupling) | Brak couplingу między agentami |
| Timing | Asynchroniczny, ale konsument musi istnieć | Całkowity time decoupling |
| Skalowalność | Bardzo dobra (broker skaluje) | Ograniczona przez synchronizację |
| Query | Nie — subskrybent dostaje wszystko z topiku | Tak — można odpytywać stan |
| Historia | Zależy od brokera (Kafka: retention) | Brak wbudowanej historii |
| Dla LLM | AutoGen ConversableAgent, CrewAI tasks | LangGraph State, vector stores |

**Trade-offy Pub/Sub:**
  ✓ Łatwy onboarding nowych agentów (subscribe do topiku)
  ✓ Naturalna asynchroniczność
  ✗ Agent musi znać nazwy topików — to jest forma couplingу
  ✗ Trudno odpytywać historię bez specjalnego brokera (Kafka)

**Trade-offy Shared Memory:**
  ✓ Agent odpytuje kiedy chce, co chce
  ✓ Pełny obraz stanu w dowolnym momencie
  ✗ Race conditions bez synchronizacji
  ✗ Brak naturalnego mechanizmu powiadamiania o zmianach

**Związek z naszą architekturą:** Warstwa myśli to shared memory (nie pub/sub) — agent odpytuje po tagach kiedy chce, nie subskrybuje. To ważna decyzja architektoniczna: unikamy problemu "agent musi być online gdy wiadomość przychodzi".

**Linki / źródła:**
- Hohpe, G., & Woolf, B. (2003). "Enterprise Integration Patterns." Addison-Wesley.
- Eugster, P.T., et al. (2003). "The many faces of publish/subscribe." ACM Computing Surveys, 35(2), 114-131.

---

## 2. Implementacje w nowoczesnych frameworkach LLM

---

### LangGraph — Shared State

**Źródło:** LangChain Inc. (2024). LangGraph: library for building stateful, multi-actor applications with LLMs.

**Krótki opis:** LangGraph modeluje przepływ agentów jako graf (nodes = agenci/funkcje, edges = przejścia). Kluczowy element: `State` — TypedDict który jest przekazywany przez wszystkie węzły. Każdy węzeł otrzymuje aktualny stan i zwraca delta (partial update). State jest współdzielony — to jest blackboard.

**Mechanizm shared memory:**
- `State` jako centralny blackboard: każdy agent pisze do swojego "pola" w State
- `Reducer` functions — jak łączyć równoległe zapisy (add vs replace)
- `checkpointer` — persystencja stanu (SQLite, PostgreSQL, Redis) — umożliwia long-running memory
- `MemorySaver` — in-memory checkpointer dla testów
- Human-in-the-loop przez przerwanie grafu w dowolnym punkcie i modyfikację State

**Architektura:**
```
Node A → State → Node B
Node A → State ← Node C  (równoległe, reducer łączy)
```

**Trade-offy:**
  ✓ State jako explicite blackboard — czytelny, debugowalny
  ✓ Reducer functions rozwiązują problem równoległych zapisów
  ✓ Checkpointer = automatyczna persystencja między sesjami
  ✗ State jest typowany — dodanie nowego pola wymaga zmiany TypedDict
  ✗ Graf jest statyczny — dynamiczne dodawanie węzłów wymaga obejść
  ✗ State może urosnąć nieograniczenie — brak wbudowanego mechanizmu czyszczenia

**Związek z naszą architekturą:** LangGraph State to najbliższy istniejący odpowiednik naszej warstwy myśli. Różnica: LangGraph State jest strukturalny (TypedDict), nasza warstwa myśli jest bardziej elastyczna (tagowane wpisy w czasie).

**Linki / źródła:**
- https://langchain-ai.github.io/langgraph/concepts/
- LangGraph paper: nie ma osobnego paper — dokumentacja i blog LangChain

---

### AutoGen (Microsoft) — Model komunikacji

**Źródło:** Wu, Q., et al. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation Framework." arXiv:2308.08155.

**Krótki opis:** AutoGen modeluje agentów jako `ConversableAgent` — komunikacja odbywa się przez wiadomości (message passing). Podstawowy model: pary agentów (initiator + responder). Grupowa komunikacja: `GroupChat` z `GroupChatManager` jako moderatorem.

**Mechanizm shared memory:**
- Domyślnie: brak shared memory — każdy agent ma własną historię konwersacji
- `GroupChat`: historia czatu jako de facto shared memory (wszyscy agenci widzą tę samą historię)
- `ConversableAgent.register_reply()` — hook pozwalający agentowi reagować na wiadomości innych
- AutoGen 0.4 (nowa architektura): wprowadza `AgentChat` z `BaseMemory` i persystencją
- Zewnętrzne integracje: mem0, ChromaDB jako vector memory przez `register_function`

**Co jest poza message passing:**
- `UserProxyAgent` może wykonywać kod — wynik jest "wiadomością" ale treść pochodzi z rzeczywistości
- Shared workspace przez filesystem (agenci piszą pliki, inni czytają) — implicit stigmergy
- W praktycznych implementacjach: Redis/Postgres jako external state — nie jest to wbudowane

**Trade-offy:**
  ✓ Prosty model mentalny — wiadomości jak w czacie
  ✓ Łatwe debugowanie — historia konwersacji = pełny log
  ✗ Brak natywnej shared memory — trzeba integrować zewnętrznie
  ✗ GroupChat history rośnie — kosztowny kontekst przy długich sesjach
  ✗ Agent musi "czekać na swoją kolej" w GroupChat — nie może asynchronicznie odpytywać stanu

**Związek z naszą architekturą:** AutoGen nie implementuje warstwy myśli — jest czystym message passing. Zewnętrzna integracja z vector store byłaby potrzebna do uzyskania analogicznego efektu.

**Linki / źródła:**
- arXiv:2308.08155 — oryginalny paper AutoGen
- https://microsoft.github.io/autogen/docs/concepts/

---

### CrewAI — Knowledge sharing

**Źródło:** João Moura (2023). CrewAI: framework for orchestrating role-playing AI agents. Open source, MIT license.

**Krótki opis:** CrewAI modeluje agentów jako "crew" (załoga) z rolami, celami i backstory. Zadania (`Task`) mają `context` — można explicite wskazać które wyniki poprzednich tasków są inputem dla danego taska. Agent może mieć `memory` (short-term, long-term, entity, user).

**Mechanizm shared memory — 4 typy:**
1. **Short-term memory:** RAG z embeddings na wyniki zadań w bieżącej sesji (ChromaDB domyślnie)
2. **Long-term memory:** SQLite — persystentne wyniki i "learnings" między sesjami
3. **Entity memory:** wyodrębnione encje (osoby, miejsca, organizacje) z bieżącej sesji
4. **User memory:** informacje o użytkowniku persystowane między sesjami (mem0 integration)

**Knowledge sharing mechanizm:**
- `task.context = [previous_task]` — explicite przekazywanie outputu
- `agent.allow_delegation = True` — agent może delegować podzadania do innych agentów
- `crew.knowledge_sources` (CrewAI 0.86+) — wspólna baza wiedzy dla całego crew (dokumenty, URL, tekst)
- Shared memory przez RAG: agent1 pisze wynik → embedding → agent2 odpytuje semantycznie

**Trade-offy:**
  ✓ Taksonomia pamięci jest jasna i gotowa (short/long/entity/user)
  ✓ `knowledge_sources` to gotowy shared blackboard
  ✗ Memory jest opcjonalna — domyślnie wyłączona, trzeba explicite włączyć
  ✗ Koszt embeddings przy każdym zapisie i odpytaniu
  ✗ Brak kontroli nad tym "co trafia" do memory — wszystkie outputy tasków

**Związek z naszą architekturą:** CrewAI `knowledge_sources` to najbliższy gotowy odpowiednik warstwy myśli — wspólna przestrzeń dla wszystkich agentów crew, odpytywalna semantycznie. Taksonomia 4 typów pamięci jest użyteczna jako punkt odniesienia.

**Linki / źródła:**
- https://docs.crewai.com/concepts/memory
- https://docs.crewai.com/concepts/knowledge

---

### OpenAI Swarm — Architektura

**Źródło:** OpenAI (2024). "Swarm: An ergonomic, lightweight multi-agent orchestration framework." GitHub openai/swarm. Eksperymentalny, edukacyjny.

**Skąd nazwa i co oznacza architektonicznie:**
- Nazwa nawiązuje do swarm intelligence (inteligencji rojowej) i jej właściwości: brak centralnego kontrolera, emergence, simple rules → complex behavior
- Architektonicznie jednak Swarm NIE implementuje klasycznego rojowego modelu — to uproszczony orchestrator
- Kluczowe koncepcje: `Agent` (instructions + functions) i `handoff` (przekazanie kontroli do innego agenta)
- Przepływ: jeden agent działa w danym momencie → może wywołać funkcję → jeśli funkcja zwraca innego agenta, kontrola przechodzi

**Model komunikacji:**
- Nie ma shared memory — stan jest przekazywany jako `context_variables` (dict) przez handoff
- `context_variables` to jedyne "shared" — przekazywane do każdego agenta w chain
- Brak asynchroniczności — agenci działają sekwencyjnie
- Bardzo prosty: celowo nie implementuje routing, memory, multi-tenancy

**Trade-offy:**
  ✓ Niezwykle prosty model mentalny — jeden agent aktywny, handoff jako "pałeczka"
  ✓ `context_variables` jako lightweight shared state
  ✗ Sekwencyjny — brak równoległości
  ✗ Brak shared memory — historia nie jest dostępna dla "poprzednich" agentów
  ✗ Eksperymentalny — nie do produkcji (OpenAI tak to opisuje)
  ✗ Nazwa myląca — nie implementuje swarm intelligence

**Związek z naszą architekturą:** Swarm `context_variables` to prymitywna wersja shared state — mutable dict przekazywany przez łańcuch agentów. Nie jest to warstwa myśli (brak trwałości, brak semantycznego wyszukiwania, brak równoległości).

**Linki / źródła:**
- https://github.com/openai/swarm
- OpenAI cookbook: multi-agent orchestration patterns

---

### mem0 — System pamięci dla agentów

**Źródło:** Taranjeet Singh, et al. (2024). mem0 (dawniej EmbedChain). Open source + SaaS. arXiv:2504.19413 (MemoryOS paper, powiązany).

**Krótki opis:** mem0 to warstwa pamięci dla agentów LLM działająca jako serwis. Automatycznie ekstrakt i przechowuje "wspomnienia" z konwersacji. Trzy warstwy przechowywania: vector store (semantyczne), graph store (relacje między encjami), key-value (szybki dostęp).

**Taksonomia pamięci w mem0:**
- **User-level memory:** co wiemy o konkretnym użytkowniku (preferencje, historia)
- **Session-level memory:** kontekst bieżącej sesji
- **Agent-level memory:** wiedza specyficzna dla agenta (nie dla użytkownika)
- Brak explicite episodic/semantic/procedural — mem0 nie używa tej taksonomii

**Mechanizm:**
1. Konwersacja → LLM ekstraktuje "fakty" → zapisuje do vector store
2. Odpytanie: `memory.search(query, user_id)` → zwraca relevantne wspomnienia
3. Integracja z AutoGen, LangChain, CrewAI przez `@tool` wrapper

**Trade-offy:**
  ✓ Automatyczna ekstrakcja — agent nie musi decydować co zapamiętać
  ✓ Multi-level (user/session/agent) — granularność
  ✓ Graph store wykrywa relacje między encjami automatycznie
  ✗ LLM call do ekstrakcji = koszt przy każdej interakcji
  ✗ Automatyczna ekstrakcja może zachowywać błędne lub nadmiarowe fakty
  ✗ Graph store wymaga Neo4j (nie lightweight)

**Związek z naszą architekturą:** mem0 mógłby implementować warstwę myśli — semantyczne wyszukiwanie po tagach to odpowiednik `memory.search`. Różnica: mem0 jest zorientowany na "fakty o użytkowniku", nasza warstwa myśli to współpraca agentów, nie personalizacja.

**Linki / źródła:**
- https://docs.mem0.ai/
- arXiv:2504.19413 (MemoryOS: Empowering AI Agents with Operating System-Inspired Memory Management)

---

### Letta (MemGPT) — Hierarchiczna pamięć

**Źródło:** Packer, C., et al. (2023). "MemGPT: Towards LLMs as Operating Systems." arXiv:2310.08560. Przemianowany na Letta w 2024.

**Krótki opis:** MemGPT/Letta traktuje LLM jak OS zarządzający pamięcią. Inspiracja: wirtualna pamięć OS — dane "stronicowane" między szybką (kontekst okna) a wolną pamięcią (external storage). Agent sam decyduje kiedy "zapisać do dysku" i "wczytać z dysku" przez funkcje narzędziowe.

**Taksonomia pamięci w Letta:**
- **In-context memory (working):** to co aktualnie jest w oknie kontekstu LLM
  - `core memory` (system prompt): persystentny, zawsze w kontekście — persona agenta, informacje o użytkowniku
  - `recall memory` (conversation): historia konwersacji, przeszukiwalna przez wyszukiwanie
- **Out-of-context memory (external):**
  - `archival memory`: nieograniczona, przeszukiwana semantycznie przez embedding search
  - Agentowe operacje: `core_memory_append`, `core_memory_replace`, `archival_memory_insert`, `archival_memory_search`

**Kluczowy mechanizm:** Agent sam wywołuje funkcje zarządzania pamięcią — to nie jest automatyczne. LLM decyduje "powinienem zapamiętać ten fakt" i wywołuje `archival_memory_insert`. To procedural memory management jako explicit tool use.

**Trade-offy:**
  ✓ Agent ma kontrolę nad własną pamięcią — metacognition
  ✓ Nieograniczona archival memory (przez vector search)
  ✓ Taksonomia jest czysta i zrozumiała
  ✗ Agent musi "zdecydować" co zapamiętać — promptowanie ma znaczenie krytyczne
  ✗ Archival memory search = dodatkowy LLM call lub embedding call
  ✗ Multi-agent: każdy agent ma SWOJĄ archival memory — nie ma natywnej shared memory

**Związek z naszą architekturą:** Letta archival memory to "myśli agenta" ale prywatne, nie współdzielone. Shared memory między agentami wymaga zewnętrznego archival storage wspólnego dla wielu agentów — Letta obsługuje to przez `shared_memory` blok (dodane w 2024).

**Linki / źródła:**
- arXiv:2310.08560 — oryginalny MemGPT paper
- https://docs.letta.com/concepts/memory

---

## 3. Taksonomia pamięci agentów LLM

---

### Taksonomia CoALA (Cognitive Architectures for Language Agents)

**Źródło:** Sumers, T.R., Ye, S., Wortman Vaughan, J., Griffiths, T.L. (2023). "Cognitive Architectures for Language Agents." arXiv:2309.02427. Aktualny konsensus akademicki.

**Krótki opis:** Najbardziej cytowana taksonomia (2023-2024). Oparta na kognitywistycznych teoriach pamięci (Tulving, Anderson). Wyróżnia 4 typy pamięci:

| Typ | Analogia kognitywna | Zawartość | Format |
|-----|---------------------|-----------|--------|
| **Episodic** | Pamięć epizodyczna (Tulving) | Konkretne przeszłe zdarzenia, interakcje | Logi, przykłady, trajektorie |
| **Semantic** | Pamięć semantyczna | Fakty o świecie, wiedza ogólna | Tekst, grafy wiedzy, bazy danych |
| **Procedural** | Pamięć proceduralna | Jak wykonywać zadania | Wagi modelu, prompty systemowe, kod |
| **Working** | Pamięć robocza (Baddeley) | Aktualny kontekst, stan zadania | Okno kontekstu LLM |

**Ważne rozróżnienia:**
- Working memory = kontekst okna — ograniczona, ulotna
- Episodic: "co zrobiłem przy tym zadaniu" — baza przykładów few-shot
- Semantic: "co wiem o świecie" — RAG nad dokumentami
- Procedural: jak działam — prompty i wagi (nie modyfikowane w runtime)

**Czy jest konsensus?** Taksonomia CoALA jest najszerzej cytowana w 2023-2025. Jednak frameworki używają własnej terminologii:
- mem0: user/session/agent
- Letta: working/recall/archival/core
- CrewAI: short-term/long-term/entity/user
- LangGraph: nie ma typologii — State jest jedna

**Wspólny mianownik:**
- Wszyscy rozróżniają "w kontekście" vs "poza kontekstem" (in-context vs external)
- Wszyscy mają "semantyczne wyszukiwanie" do zewnętrznej pamięci
- Różnice głównie w granularności i nazewnictwie

**Trade-offy taksonomii CoALA:**
  ✓ Zakorzeniona w kognitywistyce — stabilna teoretycznie
  ✓ Episodic/semantic/procedural to różne mechanizmy dostępu — uzasadnione architektonicznie
  ✗ Procedural memory (wagi) nie jest modyfikowalna w runtime — to bardziej "frozen knowledge"
  ✗ Nie rozróżnia pamięci prywatnej agenta od współdzielonej

**Linki / źródła:**
- arXiv:2309.02427 — CoALA paper (cytowane ~500 razy wg Google Scholar 2025)

---

## 4. Semantic search jako wspólna pamięć

---

### Vector Store jako Shared Memory

**Źródło:** Wzorzec wyłonił się z praktyki RAG (2022-2023). Nie ma jednego paper definiującego go jako "wzorzec architektoniczny" — raczej industryjna praktyka.

**Krótki opis:** Agenci zapisują "myśli" lub wyniki jako embeddingi do wspólnego vector store (np. ChromaDB, Pinecone, Qdrant, pgvector). Inni agenci odpytują semantycznie: `search("jak rozwiązać problem X")` zwraca najbardziej podobne wcześniejsze myśli, niezależnie od tego który agent je zapisał.

**Gdzie stosowane:**
- CrewAI short-term memory (ChromaDB)
- LangChain Memory z VectorStoreRetrieverMemory
- mem0 (vector + graph)
- Custom implementacje w AutoGen przez tool use
- Microsoft GraphRAG (2024) — graph + vector hybrid

**Ograniczenia wzorca:**
  ✓ Semantyczne wyszukiwanie = brak potrzeby znajomości tagów — "pythonowe wyszukiwanie" zamiast SQL
  ✓ Skaluje się do milionów dokumentów
  ✓ Time decoupling — można szukać myśli sprzed tygodnia
  ✗ Brak deterministyczności — "podobne" nie znaczy "poprawne"
  ✗ Embedding drift — model embeddingowy aktualizowany → stare embeddingi niekompatybilne
  ✗ Brak explicit semantyki — nie wiadomo "co" jest w bazie bez próbkowania
  ✗ Wymagany model embeddingowy — zależność od API lub lokalnego modelu
  ✗ Brak wbudowanej kontroli dostępu — wszystkie agenty widzą wszystko

**Jako wzorzec architektoniczny:** Brak nazwy własnej w literaturze. Najbliższe:
- "Memory-Augmented LLM Agents" (ogólna kategoria)
- "External Memory with Retrieval" w CoALA
- Analogia do Tuple Space: embedding = "typowany" tuple, ANN search = pattern matching po strukturze semantycznej

**Związek z naszą architekturą:** To jest implementacyjny rdzeń warstwy myśli. Pytanie projektowe: tagi explicite (metadata filter + semantic) vs pure semantic. Hybryda (tagi jako metadata filter, treść semantycznie) jest lepsza — zmniejsza szum w wynikach.

**Linki / źródła:**
- Nie ma kanonicznego paper — praktyka przemysłowa
- Johnson, J., et al. (2021). "Billion-scale similarity search with GPUs." IEEE TPAMI (FAISS)
- CoALA (arXiv:2309.02427) — sekcja External Memory

---

## 5. Stigmergy w AI — implementacje

---

### Stigmergy dla LLM agentów — stan badań

**Źródło:** Brak kanonicznego paper dla LLM stigmergy. Przegląd: Picard, R., et al. (2024) — notatki z ACL/EMNLP 2024 warsztatów multi-agent.

**Czy ktoś to implementuje:**

**Bezpośrednie implementacje stigmergy dla LLM:** Brak głównonurtowych frameworków implementujących stigmergy explicite dla LLM (stan na początku 2025).

**Implicit stigmergy w praktyce:**
1. **Voyager (Wang et al., 2023):** agent Minecraft zapisuje skill (JavaScript funkcja) do "skill library". Kolejny agent widzi dostępne skille i buduje na nich. To stigmergy: środowisko (skill library) koordynuje, nie wiadomości.
2. **SWE-agent i podobne:** agenci modyfikują pliki na dysku — kolejny agent "widzi" zmiany. Filesystem jako medium stigmergiczne.
3. **Devin (Cognition AI):** long-running agent modyfikuje repo git, obserwuje wyniki testów. Środowisko (repo + CI) jako stigmergiczne medium.

**Akademickie propozycje:**
- Marro, S., et al. (2024). "A Scalable Communication Protocol for Networks of Large Language Models." arXiv:2410.11905 — nie jest to stigmergy ale adresuje podobny problem skalowalności
- Ogólne: ACO-inspired LLM routing — kilka prac z 2024 używa metafory feromonów do priorytetyzacji zadań w pipeline

**Dlaczego stigmergy trudna dla LLM:**
  ✗ LLM nie ma "zmysłów" — musi explicite odczytać środowisko przez tool call
  ✗ Brak naturalnej "ewaporacji" — stare ślady nie gasną bez dodatkowej logiki
  ✗ LLM jest deterministycznie promptowany — trudno uzyskać emergentne zachowanie
  ✗ Debugging prawie niemożliwy — dlaczego agent podjął decyzję X?

**Wyniki istniejących implementacji:**
- Voyager: sukces w skill acquisition — implicit stigmergy działa
- Filesystem-based: działa ale wymaga struktury katalogów jako "pheromone trails"
- Czysta stigmergy bez żadnego message passing: brak dojrzałych implementacji

**Związek z naszą architekturą:** Warstwa myśli może być interpretowana jako stigmergiczne medium — ale tylko jeśli agenci reagują na treść myśli bez explicite bycia do nich adresowanymi. Mechanizm TTL/decay wpisów w shared memory = ewaporacja feromonów.

**Linki / źródła:**
- Wang, G., et al. (2023). "Voyager: An Open-Ended Embodied Agent with Large Language Models." arXiv:2305.16291.
- arXiv:2410.11905 — scalable communication protocol

---

## Podsumowanie i wnioski dla architektury

### Mapa wzorców do warstw architektury

| Warstwa | Wzorzec | Najlepsza implementacja | Uwagi |
|---------|---------|------------------------|-------|
| Dyrektywy | Procedural memory (CoALA) | System prompt / wagi | Statyczne, nie modyfikowane w runtime |
| Wiadomości | Message passing / Pub/Sub | AutoGen ConversableAgent | Standard — adresowane, point-to-point |
| Myśli | Blackboard / Tuple Space / Stigmergy | Vector store + metadata tags | Brak gotowego frameworku — do zbudowania |

### Kluczowe decyzje projektowe dla warstwy myśli

1. **Tagi explicite vs pure semantic:** Hybryda — tagi jako metadata filter (deterministyczny), treść jako semantic search (probabilistyczny). Zmniejsza szum.

2. **Destruktywne vs niedestruktywne czytanie:** Wzorzec Lindy (`in` vs `rd`). Dla myśli: niedestruktywne (`rd`) — myśli persystują, nie znikają po przeczytaniu.

3. **Ewaporacja / TTL:** Odpowiednik feromonów. Bez TTL: shared memory rośnie nieograniczenie. Z TTL: stare myśli gasną. Alternatywa: explicit `archive` status zamiast usuwania.

4. **Kto może pisać / czytać:** Brak kontroli = Tuple Space (wszyscy). Kontrola per tag = Blackboard (kontroler). Dla naszego przypadku: wszyscy agenci piszą i czytają, ale tagi określają relevancję.

5. **Mechanizm powiadamiania:** Polling (agent odpytuje co turę) vs event-driven (nowa myśl wyzwala callback). Polling prostszy, event-driven efektywniejszy.

### Zalecany wzorzec dla warstwy myśli

Hybryda **Blackboard + Tuple Space** z semantycznym wyszukiwaniem:
- Blackboard: wspólna przestrzeń, bez adresata, audio trail
- Tuple Space: pattern matching (tagi) zamiast adresów, time decoupling
- Vector store: semantyczne wyszukiwanie zamiast exact match
- TTL: opcjonalna ewaporacja wzorowana na stigmergy

Najbliższy istniejący model: **CrewAI knowledge_sources + short-term memory** — ale wymaga customizacji dla inter-agent sharing i TTL.

---

## Wzorce których nie znalazłem (lub brak wystarczających danych)

- **Implementacje GWT w produkcyjnych systemach LLM 2024-2025:** Salesforce AgentVerse cytuje GWT, ale brak szczegółów technicznych w dostępnych źródłach (brak dostępu do live web w tej sesji).
- **"LindaLLM" lub analogiczne projekty:** Wzorzec Tuple Space dla LLM wydaje się być akademicką propozycją 2023-2024, ale brak konkretnych implementacji znanych z treningu.
- **Standardowa taksonomia mem0 vs Letta vs CrewAI:** Brak konsensusu między frameworkami — każdy używa własnej nomenklatury. CoALA (arXiv:2309.02427) jest najbliższe standardu akademickiego.
- **Czyste stigmergy dla LLM bez implicit filesystem:** Brak dojrzałych implementacji z mierzalnymi wynikami.
- **Global Workspace jako produkcyjny system LLM:** Koncepcyjnie obecne (Bengio, Franklin/LIDA), ale brak implementacji w głównych frameworkach (LangChain, AutoGen, CrewAI).

---

**Uwaga metodologiczna:** Research przeprowadzony na wiedzy treningowej (cutoff: sierpień 2025). WebFetch był niedostępny w tej sesji. Linki podane są jako referencyjna informacja o źródłach — nieweryfikowane live. Wersje frameworków: LangGraph ~0.2, AutoGen ~0.4, CrewAI ~0.86, mem0 ~1.x, Letta ~0.6. Stan na przełomie 2024/2025.
