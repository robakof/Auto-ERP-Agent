# Research: Wzorce projektowania roli Researcher

Data: 2026-03-22

Legenda siły dowodów:
- **empiryczne** — paper/survey/benchmark lub badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, repo wdrożeniowe
- **spekulacja** — rekomendacja syntetyczna; sensowna, ale nie wprost potwierdzona przez źródło

## TL;DR — 5 najważniejszych wzorców/kierunków

1. **Najlepsze implementacje rozdzielają `Scope → Research → Write` zamiast robić „search-and-write” jednym promptem.** Ten podział pojawia się zarówno w badaniach nad STORM (pre-writing i outline przed pisaniem), jak i w nowoczesnych open-source’owych deep research agentach oraz cookbookach OpenAI/LangChain. [STORM](https://aclanthology.org/2024.naacl-long.347/), [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch), [Deep Research API with the Agents SDK](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api_agents/)
2. **Researcher powinien działać pętlą: szerokie rozpoznanie → identyfikacja luk → pogłębianie.** STORM robi to przez multi-perspective question asking, Co-STORM przez rozmowę wielu agentów i dynamiczną mind mapę, a Local Deep Researcher przez cykl search → summarize → reflect on gaps → re-query. [STORM](https://aclanthology.org/2024.naacl-long.347/), [Co-STORM](https://arxiv.org/abs/2408.15232), [Local Deep Researcher](https://github.com/langchain-ai/local-deep-researcher)
3. **Weryfikacja źródeł nie może być etapem „na końcu” — musi być częścią pętli badawczej.** Najmocniejsze wzorce to: potwierdzanie kluczowych tez w wielu niezależnych źródłach, jawne mapowanie claim → source, obsługa sprzecznych źródeł i oznaczanie niepewności/syntezy. [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Web search | OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search/), [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
4. **Dla zadań wielowątkowych lepszy jest supervisor + wyspecjalizowani researcherzy niż jeden monolit.** W praktyce najlepiej działa delegacja niezależnych wątków do osobnych agentów z izolacją kontekstu, równoległością tylko tam, gdzie nie ma zależności, i jawnie ograniczonym dostępem do narzędzi. [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch), [Agents SDK](https://developers.openai.com/api/docs/guides/agents-sdk/), [Prompting best practices | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Create custom subagents | Anthropic](https://code.claude.com/docs/en/sub-agents)
5. **Dobry output researchera jest warstwowy: TL;DR, findings, trade-offy, poziom pewności, luki i źródła.** Dokumentacja Anthropic/OpenAI wzmacnia wagę cytowań, structured outputs i śledzenia kroków pośrednich; obserwowalność i evale stają się częścią architektury, nie dodatkiem. [Increase output consistency | Anthropic](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency), [Introduction to deep research in the OpenAI API](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api/), [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation), [CrewAI Tracing](https://docs.crewai.com/en/observability/tracing)

## Wyniki per obszar badawczy

### 1. Struktura i workflow

**Dominujący wzorzec: `Scope → Research → Write`.**
LangChain opisuje deep research wprost jako 3-fazową architekturę: najpierw doprecyzowanie zakresu, potem research, a na końcu raport. W STORM analogiczny nacisk pada na **pre-writing stage**: zbadanie tematu i przygotowanie outline’u przed właściwym pisaniem. OpenAI w cookbooku do Deep Research Agents również pokazuje pipeline’y single- i multi-agentowe, w których jakość rośnie po wzbogaceniu briefu użytkownika przed uruchomieniem właściwego researchu. **Siła dowodów: praktyczne + empiryczne.** [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch), [STORM](https://aclanthology.org/2024.naacl-long.347/), [Deep Research API with the Agents SDK](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api_agents/)

**Przed uruchomieniem searchu warto wygenerować jawny brief badawczy.**
Najbardziej konkretne, powtarzalne wdrożeniowo podejście daje LangChain: etap `User Clarification and Brief Generation` używa structured output do decyzji, czy trzeba dopytać użytkownika, a następnie zamienia rozmowę w uporządkowane pytania badawcze. To jest dobry wzorzec planningu: z briefu powinny wynikać zakres, kryteria aktualności, ograniczenia, oczekiwany format i poziom dowodu. **Siła dowodów: praktyczne.** [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)

**Szerokość vs głębokość: start szeroko, potem schodź głęboko w luki lub sporne tezy.**
STORM poprawia breadth/depth przez odkrywanie różnych perspektyw i kierowanie pytaniami z wielu punktów widzenia. Co-STORM przesuwa ten pomysł dalej: zamiast wymagać od użytkownika zadania wszystkich pytań, kilka agentów eksploruje temat i buduje dynamiczną mapę pojęć, co jest szczególnie dobre dla „unknown unknowns”. Z kolei Local Deep Researcher materializuje praktyczny workflow: wyszukiwanie, podsumowanie, refleksja nad lukami, nowa kwerenda, kolejne iteracje. **Siła dowodów: empiryczne + praktyczne.** [STORM](https://aclanthology.org/2024.naacl-long.347/), [Co-STORM](https://arxiv.org/abs/2408.15232), [Local Deep Researcher](https://github.com/langchain-ai/local-deep-researcher)

**Kiedy iść szeroko?**
Idź szeroko, gdy temat jest eksploracyjny, użytkownik nie zna jeszcze dobrej struktury problemu, albo istnieje ryzyko pominięcia ważnej perspektywy. W tych sytuacjach lepiej wygenerować kilka kierunków pytań lub 3–5 zapytań startowych niż od razu pogłębiać pierwszy trop. Właśnie tak działa przykładowy CrewAI Deep Research Flow, który po klasyfikacji intencji generuje kilka kwerend i dopiero wtedy uruchamia researchera. **Siła dowodów: praktyczne.** [Deep Research Flow](https://github.com/crewAIInc/template_deep_research), [STORM](https://aclanthology.org/2024.naacl-long.347/), [Co-STORM](https://arxiv.org/abs/2408.15232)

**Kiedy iść głęboko?**
Idź głęboko, gdy odpowiedź zależy od wąskiej, ryzykownej lub sprzecznej tezy; gdy domena jest regulowana; albo gdy kilka źródeł podaje różne wersje faktu. Survey Deep Research podkreśla, że zaawansowane systemy przechodzą od prostych heurystyk reputacyjnych do jawnego modelowania niepewności, wykrywania sprzeczności i evidential reasoning. **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)

**Multi-hop reasoning najlepiej implementować jako dekompozycję + osobne retrievale + syntezę.**
OpenAI opisuje file search jako narzędzie, które potrafi przepisać pytanie pod search, rozbić złożone zapytanie na kilka wyszukiwań uruchamianych równolegle, uruchomić jednocześnie keyword i semantic search, a potem rerankować wyniki. LangChain pokazuje osobno wariant supervisor + worker agents z delegacją i izolacją kontekstu dla niezależnych tematów. To razem daje dobry wzorzec multi-hop: najpierw rozbij pytanie, potem obsłuż hop’y własnymi retrievalami, a dopiero na końcu zrób syntezę. **Siła dowodów: praktyczne.** [Assistants File Search](https://developers.openai.com/api/docs/assistants/tools/file-search/), [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)

**Równoległość jest dobra tylko dla niezależnych wątków.**
Anthropic bardzo jasno rozróżnia dwa tryby: gdy wywołania są niezależne, warto je maksymalnie równoleglić; gdy parametry jednego kroku zależą od poprzedniego, trzeba iść sekwencyjnie i nie wolno zgadywać brakujących parametrów. LangChain w deep_research_from_scratch robi podobny podział na async orchestration dla koordynacji równoległej i synchronous simplicity tam, gdzie zależy nam na niezawodności. **Siła dowodów: praktyczne.** [Prompting best practices | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)

**Rekomendowany minimalny workflow researchera:**
1. Clarify/brief — doprecyzuj cel, zakres, recency, oczekiwany output. **Siła dowodów: praktyczne.** [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)
2. Breadth pass — wygeneruj kilka perspektyw / zapytań startowych. **Siła dowodów: empiryczne + praktyczne.** [STORM](https://aclanthology.org/2024.naacl-long.347/), [Deep Research Flow](https://github.com/crewAIInc/template_deep_research)
3. Gap-driven deepening — iteracyjnie zamykaj luki i sporne wątki. **Siła dowodów: praktyczne + empiryczne.** [Local Deep Researcher](https://github.com/langchain-ai/local-deep-researcher), [Co-STORM](https://arxiv.org/abs/2408.15232)
4. Verification pass — potwierdź kluczowe tezy niezależnie. **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
5. Synthesis/write — rozdziel sourced facts od własnej syntezy. **Siła dowodów: empiryczne + praktyczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Increase output consistency | Anthropic](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)

### 2. Jakość i wiarygodność źródeł

**Nowoczesne research agents oceniają nie tylko reputację źródła, ale też cechy treści i zgodność z inną wiedzą.**
Survey Deep Research opisuje przejście od prostych heurystyk reputacyjnych do bardziej zaawansowanych frameworków oceny, które biorą pod uwagę cechy źródła, cechy treści oraz zgodność z ustaloną wiedzą; wymienia też explicit uncertainty modeling, contradiction detection i evidential reasoning. **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)

**Najmocniejszy wzorzec weryfikacji to triangulacja w wielu niezależnych źródłach.**
Survey wskazuje wprost, że wiodące implementacje stosują jawne mechanizmy source validation, a OpenAI/DeepResearch potwierdza informacje w wielu niezależnych źródłach przed włączeniem ich do odpowiedzi. Anthropic i OpenAI jednocześnie mocno akcentują cytowania i grounding. **Siła dowodów: empiryczne + praktyczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Web search | OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search/), [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool), [Customer support agent | Anthropic](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat)

**W konflikcie źródeł nie należy „uśredniać” odpowiedzi — trzeba wyjaśnić naturę konfliktu.**
Survey opisuje wzorzec explicit conflict identification and resolution: różnice metodologiczne, czynniki kontekstowe i próby pojednania sprzecznych wyników. To prowadzi do ważnej rekomendacji: researcher nie powinien chować konfliktu, tylko opisać *dlaczego* źródła się rozjeżdżają i który typ dowodu jest mocniejszy. **Siła dowodów: empiryczne + spekulacja.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)

**Claim → source mapping powinno być jawne, a synteza oznaczona jako synteza.**
Survey zwraca uwagę, że jawne mapowanie teza → źródło poprawia weryfikowalność, a przy insightach syntetyzowanych z wielu źródeł potrzebne są specjalne praktyki atrybucji: wskazanie wielu źródeł wkładowych i odróżnienie informacji wprost potwierdzonej od połączenia wygenerowanego przez system. **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)

**W praktyce warto używać polityki preferencji źródeł, nie jednej skali „good/bad”.**
Rozsądny porządek preferencji to: (1) źródła pierwotne i oficjalne dokumenty, (2) recenzowane papers / raporty metodologiczne, (3) dokumentacja frameworka, (4) repozytoria i cookbooki, (5) wtórne streszczenia. Anthropic dodatkowo pozwala ograniczać domeny przez `allowed_domains` i `blocked_domains`, a search result zwraca nawet `page_age`, co ułatwia polityki jakości i recency. **Siła dowodów: praktyczne + spekulacja.** [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)

**Proponowana, praktyczna skala siły dowodów dla outputu researchera:**
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją, oficjalne dane pierwotne.
- **praktyczne** — oficjalna dokumentacja, cookbook, repo z działającą implementacją, ale bez twardej ewaluacji jakości researchu.
- **spekulacja** — inferencja architektoniczna, hipoteza, heurystyka zespołu, rekomendacja nieprzetestowana na benchmarkach.
To nie jest standard z jednego źródła, ale bardzo użyteczny wzorzec oznaczania pewności i rodzaju dowodu w raportach researchowych. **Siła dowodów: spekulacja.**

**Minimalny standard jakości dla researchera:**
- potwierdzaj kluczowe tezy w ≥2 niezależnych źródłach, a w domenach ryzykownych w ≥3; **Siła dowodów: empiryczne + spekulacja.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- przy każdej ważnej tezie trzymaj link do źródła i krótką notę, skąd teza pochodzi; **Siła dowodów: empiryczne + praktyczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
- zaznaczaj, czy wniosek jest „wprost ze źródła”, czy jest „syntezą z wielu źródeł”; **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- w przypadku konfliktu pokazuj rozbieżność zamiast ją ukrywać. **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)

### 3. Synteza i output

**Najbardziej użyteczny output jest wielowarstwowy, nie jednowarstwowy.**
Co-STORM kończy pracę raportem opartym o dynamicznie budowaną mapę pojęć, a OpenAI Deep Research API udostępnia kroki pośrednie (reasoning, web search, code execution), które można wykorzystać do debugowania i wizualizacji konstrukcji odpowiedzi. To wspiera wzorzec: najpierw executive summary, potem rozwinięcie tematyczne, a na końcu pełna ścieżka dowodowa. **Siła dowodów: empiryczne + praktyczne.** [Co-STORM](https://arxiv.org/abs/2408.15232), [Introduction to deep research in the OpenAI API](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api/)

**TL;DR i pełny raport powinny być świadomie rozdzielone.**
Anthropic zaleca precyzyjne definiowanie formatu wyjściowego i używanie structured outputs dla silnej spójności schematu. To bardzo dobrze pasuje do researchera: TL;DR odpowiada na „co najważniejsze?”, a pełny raport na „dlaczego tak uważamy?”. **Siła dowodów: praktyczne.** [Increase output consistency | Anthropic](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)

**Trade-offy i alternatywy powinny być jawne, nie schowane w narracji.**
Survey Deep Research podkreśla wagę confidence estimation, feedback i komunikowania granic pewności. W praktyce oznacza to, że dobry raport nie kończy się jedną rekomendacją, tylko pokazuje 2–3 realne warianty wraz z kosztami, ryzykami i warunkami, w których każdy z nich wygrywa. **Siła dowodów: empiryczne + spekulacja.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)

**Luki w wiedzy powinny być pierwszorzędnym elementem outputu.**
Iteracyjny research oparty o zamykanie knowledge gaps zakłada, że brak danych nie jest porażką, tylko wynikiem. Lokalny researcher LangChain wprost wykorzystuje refleksję nad lukami do kolejnych iteracji; ten sam sygnał warto wyeksponować w finalnym raporcie jako sekcję „czego nadal nie wiemy / czego nie udało się zweryfikować”. **Siła dowodów: praktyczne.** [Local Deep Researcher](https://github.com/langchain-ai/local-deep-researcher)

**Rekomendowany format końcowy dla researchera:**
1. **TL;DR (3–7 punktów)** — najważniejsze wnioski i ich status dowodowy. **Siła dowodów: praktyczne + spekulacja.** [Increase output consistency | Anthropic](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)
2. **Findings per theme** — grupowanie wyników wg pytań badawczych, nie wg kolejności searchu. **Siła dowodów: spekulacja.**
3. **Trade-offy / alternatywy** — co działa, kiedy działa, czego nie rozwiązuje. **Siła dowodów: empiryczne + spekulacja.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
4. **Poziom pewności / typ dowodu** — empiryczne / praktyczne / spekulacja. **Siła dowodów: spekulacja.**
5. **Open questions / gaps** — brak danych, konflikty źródeł, rzeczy do doprecyzowania. **Siła dowodów: praktyczne.** [Local Deep Researcher](https://github.com/langchain-ai/local-deep-researcher)
6. **Źródła z krótkim opisem** — nie sama lista linków, ale po co dane źródło zostało użyte. **Siła dowodów: empiryczne + praktyczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)

### 4. Narzędzia i integracje

**Najczęstszy współczesny stack research agenta składa się z czterech warstw: retrieval, orchestration, memory/cache i observability.**
OpenAI daje wprost web search, file search i Agents SDK; Anthropic udostępnia tool use, web search, subagents i prompt caching; LangChain/LangGraph skupia się na grafach agentów, RAG i MCP; CrewAI na rolach, knowledge, memory, cachingu i flows. **Siła dowodów: praktyczne.** [Web search | OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search/), [File search | OpenAI](https://developers.openai.com/api/docs/guides/tools-file-search/), [Agents SDK](https://developers.openai.com/api/docs/guides/agents-sdk/), [Tool use with Claude](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Retrieval | LangChain](https://docs.langchain.com/oss/python/langchain/retrieval), [Knowledge | CrewAI](https://docs.crewai.com/en/concepts/knowledge), [Crews | CrewAI](https://docs.crewai.com/en/concepts/crews)

**W ekosystemie OpenAI praktyczny punkt ciężkości jest dziś po stronie Responses API + Agents SDK.**
Oficjalne materiały OpenAI opisują Responses jako nowszy i prostszy interfejs do aplikacji wielonarzędziowych; jednocześnie dokumentacja Assistants nadal istnieje i pokazuje te same klasy capability, np. file search. W praktyce oznacza to, że przy projektowaniu researchera warto czytać Assistants głównie jako materiał referencyjny dla capability, a Responses/Agents SDK jako główny tor architektoniczny. **Siła dowodów: praktyczne.** [Web Search and States with Responses API](https://developers.openai.com/cookbook/examples/responses_api/responses_example/), [Doing RAG on PDFs using File Search in the Responses API](https://developers.openai.com/cookbook/examples/file_search_responses/), [Assistants API deep dive](https://developers.openai.com/api/docs/assistants/deep-dive/)

**Łączenie web search z RAG ma trzy dobre wzorce.**
- **RAG-first, web-fallback** — gdy lokalne dokumenty są głównym źródłem prawdy, a web potrzebny jest tylko do recency lub kontekstu zewnętrznego. **Siła dowodów: praktyczne.** [Build a custom RAG agent with LangGraph](https://docs.langchain.com/oss/python/langgraph/agentic-rag), [Multi-Tool Orchestration with RAG approach using OpenAI's Responses API](https://developers.openai.com/cookbook/examples/responses_api/responses_api_tool_orchestration)
- **Web-first, local grounding** — gdy pytanie jest szerokie rynkowo lub badawczo, ale trzeba je doważyć dokumentami lokalnymi. **Siła dowodów: praktyczne.** [Multi-Tool Orchestration with RAG approach using OpenAI's Responses API](https://developers.openai.com/cookbook/examples/responses_api/responses_api_tool_orchestration)
- **Arbitration / intelligent routing** — agent decyduje, czy w ogóle potrzebny jest retrieval, a jeśli tak, to który. To dokładnie pokazuje agentic RAG w LangGraph. **Siła dowodów: praktyczne.** [Build a custom RAG agent with LangGraph](https://docs.langchain.com/oss/python/langgraph/agentic-rag)

**Do searchu zewnętrznego najczęściej spotkasz: natywne web search OpenAI/Anthropic, Tavily/Serper/Firecrawl oraz Exa.**
CrewAI ma osobną kategorię Search & Research tools i przykłady użycia Google search API przez Serper; ich template deep research wykorzystuje Firecrawl. LangChain ma gotowe integracje z Exa, która jest projektowana jako wyszukiwarka „dla LLM-ów”. LangChain Open Deep Research domyślnie używa Tavily, ale wspiera też MCP i natywne web search OpenAI/Anthropic. **Siła dowodów: praktyczne.** [Overview | CrewAI Search & Research](https://docs.crewai.com/en/tools/search-research/overview), [Deep Research Flow](https://github.com/crewAIInc/template_deep_research), [Exa search integration | LangChain](https://docs.langchain.com/oss/python/integrations/tools/exa_search), [Open Deep Research](https://github.com/langchain-ai/open_deep_research)

**Cache’owanie i unikanie powtórnych wyszukiwań to nie detal, tylko część architektury.**
OpenAI opisuje prompt caching dla dłuższych prefiksów oraz extended retention do 24h; Anthropic pozwala cache’ować narzędzia, system message, wiadomości, dokumenty oraz tool results; CrewAI ma cache wyników narzędzi wprost opisany w docs i domyślnie włączony w sequential process. OpenAI tool search dodatkowo ładuje narzędzia dopiero wtedy, gdy model ich potrzebuje, oraz zachowuje cache przez wstrzykiwanie narzędzi na końcu kontekstu. **Siła dowodów: praktyczne.** [Prompt caching | OpenAI](https://developers.openai.com/api/docs/guides/prompt-caching/), [Prompt Caching 101 | OpenAI](https://developers.openai.com/cookbook/examples/prompt_caching101/), [Prompt caching | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [Sequential Processes | CrewAI](https://docs.crewai.com/en/learn/sequential-process), [Crews | CrewAI](https://docs.crewai.com/en/concepts/crews), [Tool search | OpenAI](https://developers.openai.com/api/docs/guides/tools-tool-search/)

**Obserwowalność i evale powinny być spięte z research agentem od początku.**
OpenAI Deep Research API udostępnia intermediate steps; LangSmith rekomenduje ewaluację krytycznych komponentów osobno (LLM calls, retrieval, tools, formatting) oraz monitorowanie online; CrewAI ma własny tracing i szeroki dział observability. **Siła dowodów: praktyczne.** [Introduction to deep research in the OpenAI API](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api/), [LangSmith Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts), [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation), [CrewAI Tracing](https://docs.crewai.com/en/observability/tracing), [CrewAI Observability Overview](https://docs.crewai.com/en/observability/overview)

### 5. Persona i zachowania

**Optymalna persona researchera jest jednocześnie otwarta eksploracyjnie i sceptyczna dowodowo.**
Źródła praktyczne nie definiują tego jednym zdaniem, ale łącznie sugerują taki balans: najpierw szerokie odkrywanie tropów, potem rygor weryfikacji, cytowania i ograniczania niepewności. Survey Deep Research kładzie nacisk na explicit verification strategies, contradiction detection i confidence boundaries; Anthropic zaleca grounding i fact-checking. **Siła dowodów: empiryczne + praktyczne + spekulacja.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Customer support agent | Anthropic](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat)

**Dokładność vs szybkość najlepiej balansować architekturą, nie jednym suwakiem.**
Anthropic ostrzega przed overthinking i nadmierną agresją eksploracyjną; zaleca bardziej celowane instrukcje i niższy effort, jeśli agent robi zbyt dużo. Jednocześnie równoległość ma sens tylko przy niezależnych zadaniach. LangChain pokazuje ten sam trade-off jako „async orchestration vs synchronous simplicity”. **Siła dowodów: praktyczne.** [Prompting best practices | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)

**Brak danych trzeba obsługiwać jawnie, a nie maskować płynnością odpowiedzi.**
Survey opisuje explicit uncertainty modeling jako element ograniczania halucynacji; w praktyce researcher powinien umieć powiedzieć: „nie udało się potwierdzić”, „źródła są sprzeczne”, „to jest inferencja, nie cytat”. **Siła dowodów: empiryczne + spekulacja.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)

**Dobre zachowania researchera:**
- dopytuje, gdy scope jest niejasny; **Siła dowodów: praktyczne.** [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)
- nie zgaduje brakujących parametrów narzędzi; **Siła dowodów: praktyczne.** [Prompting best practices | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- preferuje źródła pierwotne i ogranicza domeny, gdy to możliwe; **Siła dowodów: praktyczne + spekulacja.** [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
- rozdziela sourced facts od własnych połączeń/syntezy; **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- potrafi pracować jako wyspecjalizowana rola, z ograniczonym zestawem narzędzi. **Siła dowodów: praktyczne.** [Create custom subagents | Anthropic](https://code.claude.com/docs/en/sub-agents), [Agents | CrewAI](https://docs.crewai.com/en/concepts/agents)

**Anti-patterns, które przewijają się najczęściej:**
- **Monolityczny agent bez planowania i bez specjalizacji.** Survey opisuje przejście od monolitycznych agentów do ról wyspecjalizowanych z koordynacją. **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- **Over-reliance on first result / source reputation only.** To dokładnie kierunek, od którego współczesne systemy odchodzą, dodając contradiction detection i content-based assessment. **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- **„Cytatologia” bez weryfikowalnego powiązania teza → źródło.** Survey i docs o web search/citations wskazują, że sama lista linków nie zastępuje mapowania claims do źródeł. **Siła dowodów: empiryczne + praktyczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
- **Nadmierna autonomia przy słabym safety/verification layer.** Historyczne AutoGPT i BabyAGI są ważne jako inspiracje dla task decomposition, ale nie są najlepszymi wzorcami dla evidence-grounded research. AutoGPT Classic opisuje rozbijanie celu na zadania i chaining działań, a BabyAGI samo ostrzega, że obecna wersja nie jest przeznaczona do produkcji; oryginalny model pracy skupiał się na task loopie, nie na jakości dowodu. **Siła dowodów: praktyczne + spekulacja.** [AutoGPT Classic](https://github.com/significant-gravitas/autogpt/blob/master/classic/README.md), [BabyAGI](https://github.com/yoheinakajima/babyagi), [BabyAGI Archive](https://github.com/yoheinakajima/babyagi_archive), [Task-driven Autonomous Agent](https://yoheinakajima.com/task-driven-autonomous-agent-utilizing-gpt-4-pinecone-and-langchain-for-diverse-applications/)
- **Over-prompting narzędzi / bezmyślna agresja searchu.** Anthropic wprost ostrzega, że zbyt mocne instrukcje typu „if in doubt, use tool” prowadzą do overtriggeringu. **Siła dowodów: praktyczne.** [Prompting best practices | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)

### 6. Przykłady implementacji

**OpenAI**
Najmocniejszy publiczny wzorzec OpenAI to dziś kombinacja **Responses API + web search/file search + Agents SDK + traces/intermediate steps**. Agents SDK kładzie nacisk na handoffs, traces i specjalizację agentów, a cookbook Deep Research pokazuje zarówno single-agent, jak i multi-agent research workflows oraz łączenie web search z MCP/internal file search. To podejście jest mocne, gdy zależy Ci na długich workflowach, wielonarzędziowości i transparentnym śledzeniu kroków pośrednich. **Siła dowodów: praktyczne.** [Agents SDK](https://developers.openai.com/api/docs/guides/agents-sdk/), [Building agents](https://developers.openai.com/tracks/building-agents/), [Introduction to deep research in the OpenAI API](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api/), [Deep Research API with the Agents SDK](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api_agents/)

**Anthropic**
Anthropic nie oferuje jednego „research frameworka” w tym samym sensie, ale ma bardzo dojrzały zestaw klocków pod researchera: tool use, web search z zawsze włączonymi citations, prompt caching, subagents z allowlist/denylist narzędzi, domain filtering oraz wskazówki dot. parallel vs sequential tool use. To wyróżnia Anthropic tam, gdzie ważne są bezpieczne specjalizacje ról i kontrola dostępu do narzędzi. **Siła dowodów: praktyczne.** [Tool use with Claude](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool), [Prompt caching | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [Create custom subagents | Anthropic](https://code.claude.com/docs/en/sub-agents), [Common workflows | Anthropic](https://code.claude.com/docs/en/common-workflows)

**LangChain / LangGraph**
LangChain i LangGraph dają dziś chyba najpełniejszy publiczny „warsztat” do budowy research agentów: klasyczne agent loops, agentic RAG, supervisor patterns, MCP, izolacja kontekstu, async orchestration, evaluation przez LangSmith oraz gotowe repo typu `deep_research_from_scratch`, `open_deep_research` i `local-deep-researcher`. To wyróżnia LangChain wśród open source: nie pojedynczy demo-agent, tylko cały katalog wzorców architektonicznych. **Siła dowodów: praktyczne.** [Agents | LangChain](https://docs.langchain.com/oss/javascript/langchain/agents), [Build a custom RAG agent with LangGraph](https://docs.langchain.com/oss/python/langgraph/agentic-rag), [LangGraph overview](https://docs.langchain.com/oss/javascript/langgraph/overview), [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch), [Open Deep Research](https://github.com/langchain-ai/open_deep_research), [Local Deep Researcher](https://github.com/langchain-ai/local-deep-researcher)

**CrewAI**
CrewAI buduje researchera przez role i workflowy: Researcher + Writer to podstawowy wzorzec, a dodatkowo dostajesz memory, cache, knowledge, collaboration, tracing i flow-based routing. Oficjalny template `template_deep_research` pokazuje bardzo konkretny pattern: rozróżnienie casual chat vs search, generowanie kilku kwerend, agent z Firecrawl i odpowiedź z cytowaniami. To wyróżnia CrewAI jako framework bliski „operacyjnej orkiestracji” zespołu agentów. **Siła dowodów: praktyczne.** [Build Your First Crew](https://docs.crewai.com/en/guides/crews/first-crew), [Agents | CrewAI](https://docs.crewai.com/en/concepts/agents), [Tools | CrewAI](https://docs.crewai.com/en/concepts/tools), [Collaboration | CrewAI](https://docs.crewai.com/en/concepts/collaboration), [Crews | CrewAI](https://docs.crewai.com/en/concepts/crews), [Knowledge | CrewAI](https://docs.crewai.com/en/concepts/knowledge), [Deep Research Flow](https://github.com/crewAIInc/template_deep_research)

**STORM / Co-STORM**
To nadal jedne z najciekawszych badań stricte o research workflow, a nie ogólnie o agentach. STORM wnosi pre-writing, perspective-guided question asking i outline-first. Co-STORM wnosi rozmowę wielu agentów, dynamikę unknown unknowns i dynamiczną mind mapę; w human eval uczestnicy preferowali Co-STORM nad search engine i nad RAG chatbotem. Jeśli szukasz „naukowo uzasadnionych” wzorców dla researchera, to ten duet jest bardzo ważny. **Siła dowodów: empiryczne.** [STORM](https://aclanthology.org/2024.naacl-long.347/), [Co-STORM](https://arxiv.org/abs/2408.15232)

**AutoGPT / BabyAGI**
To ważne historycznie punkty odniesienia: AutoGPT popularyzował goal decomposition i chaining działań, a BabyAGI pętlę task creation → execution → reprioritization. Problem polega na tym, że te wzorce są znacznie bliższe „autonomicznemu task runnerowi” niż nowoczesnemu, źródłowo ugruntowanemu researcherowi. Warto je znać jako genealogię agentów, ale dziś nie są najlepszymi wzorcami dla research-by-default. **Siła dowodów: praktyczne + spekulacja.** [AutoGPT Classic](https://github.com/significant-gravitas/autogpt/blob/master/classic/README.md), [BabyAGI Archive](https://github.com/yoheinakajima/babyagi_archive), [Task-driven Autonomous Agent](https://yoheinakajima.com/task-driven-autonomous-agent-utilizing-gpt-4-pinecone-and-langchain-for-diverse-applications/)

**Co odróżnia najlepsze implementacje od przeciętnych?**
- mają jawny etap scoping/briefing; **Siła dowodów: praktyczne.** [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)
- nie kończą na searchu — mają osobny verification loop; **Siła dowodów: empiryczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- używają specjalizacji ról i ograniczeń narzędzi; **Siła dowodów: empiryczne + praktyczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Create custom subagents | Anthropic](https://code.claude.com/docs/en/sub-agents)
- potrafią połączyć web + local docs + cache + evals; **Siła dowodów: praktyczne.** [Multi-Tool Orchestration with RAG approach using OpenAI's Responses API](https://developers.openai.com/cookbook/examples/responses_api/responses_api_tool_orchestration), [Knowledge | CrewAI](https://docs.crewai.com/en/concepts/knowledge), [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)
- pokazują nie tylko odpowiedź, ale też źródła, poziom pewności i luki. **Siła dowodów: empiryczne + praktyczne.** [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594), [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)

## Otwarte pytania / luki w wiedzy

- **Brakuje jednego, powszechnie przyjętego benchmarku jakości research reportów.** Survey Deep Research pokazuje wielowymiarowość ewaluacji (task completion, retrieval quality, usability, interactive evaluation), ale nadal nie ma jednego standardu dominującego we wszystkich use case’ach. [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- **Attribution dla insightów syntetyzowanych z wielu źródeł pozostaje trudne.** To jest jawnie wskazane w surveyu jako osobna klasa problemu. [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- **Obsługa sprzecznych źródeł jest opisana lepiej niż znormalizowana.** Wiemy, że potrzebne są conflict identification, evidence weighting i confidence estimation, ale brakuje jeszcze de facto standardu, jak to raportować między frameworkami. [A Comprehensive Survey of Deep Research](https://arxiv.org/pdf/2506.12594)
- **Kosztowo optymalna polityka weryfikacji nie jest jeszcze dobrze skodyfikowana.** Dokumentacje opisują równoległość, caching i lazy tool loading, ale nie ma jednego „best known policy” dla tego, ile verify robić per typ zadania. [Prompt caching | OpenAI](https://developers.openai.com/api/docs/guides/prompt-caching/), [Prompt caching | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [Tool search | OpenAI](https://developers.openai.com/api/docs/guides/tools-tool-search/)
- **Publiczne dowody przewagi multi-agent nad dobrze zaprojektowanym single-agent są obiecujące, ale nadal częściowe.** Co-STORM pokazuje konkretne wyniki, a wiele frameworków promuje supervisor/worker patterns, lecz wyniki są nadal mocno zależne od domeny, narzędzi i sposobu ewaluacji. [Co-STORM](https://arxiv.org/abs/2408.15232), [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch)

## Źródła / odniesienia

- [Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models (STORM)](https://aclanthology.org/2024.naacl-long.347/) — paper o pre-writing, multi-perspective question asking i outline-first research.
- [Into the Unknown Unknowns: Engaged Human Learning through Participation in Language Model Agent Conversations (Co-STORM)](https://arxiv.org/abs/2408.15232) — paper o multi-agent research discourse, unknown unknowns, dynamic mind map i finalnym raporcie.
- [A Comprehensive Survey of Deep Research: Systems, Methodologies, and Applications](https://arxiv.org/pdf/2506.12594) — szeroki survey systemów deep research; bardzo dobry do workflowów, wiarygodności, konfliktów źródeł i ewaluacji.
- [Web search | OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search/) — oficjalny opis web search z cytowaniami.
- [File search | OpenAI](https://developers.openai.com/api/docs/guides/tools-file-search/) — oficjalny opis retrievalu po własnych plikach / vector stores.
- [Agents SDK | OpenAI](https://developers.openai.com/api/docs/guides/agents-sdk/) — oficjalny przewodnik po handoffs, traces i budowie agentów.
- [Building agents | OpenAI](https://developers.openai.com/tracks/building-agents/) — syntetyczny przewodnik po agent loop, handoffs i guardrails.
- [Introduction to deep research in the OpenAI API](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api/) — cookbook pokazujący Deep Research API i intermediate steps.
- [Deep Research API with the Agents SDK](https://developers.openai.com/cookbook/examples/deep_research_api/introduction_to_deep_research_api_agents/) — praktyczny przykład budowy single- i multi-agent research workflows w OpenAI.
- [Multi-Tool Orchestration with RAG approach using OpenAI's Responses API](https://developers.openai.com/cookbook/examples/responses_api/responses_api_tool_orchestration/) — wzorzec łączenia web search, function tools i RAG.
- [Doing RAG on PDFs using File Search in the Responses API](https://developers.openai.com/cookbook/examples/file_search_responses/) — przykład łączenia PDF-ów, vector store i retrievalu.
- [Prompt caching | OpenAI](https://developers.openai.com/api/docs/guides/prompt-caching/) — aktualne zasady cache’owania promptów i retention.
- [Tool search | OpenAI](https://developers.openai.com/api/docs/guides/tools-tool-search/) — dynamiczne ładowanie narzędzi i zachowanie cache.
- [Assistants File Search | OpenAI](https://developers.openai.com/api/docs/assistants/tools/file-search/) — bardzo konkretny opis retrieval best practices: query rewrite, parallel searches, hybrid retrieval, reranking.
- [Web Search and States with Responses API](https://developers.openai.com/cookbook/examples/responses_api/responses_example/) — pokazuje współczesny kierunek OpenAI wokół Responses API.
- [Tool use with Claude](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) — oficjalne wzorce tool use, parallel/sequential calls.
- [Web search tool | Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool) — web search z zawsze włączonymi citations, domain filtering i result metadata.
- [Prompt caching | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — cache’owanie tools, messages, documents i tool results.
- [Prompting best practices | Anthropic](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — bardzo użyteczne wskazówki dot. parallelism, over-promptingu i effort.
- [Increase output consistency | Anthropic](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — structured outputs, retrieval grounding i chain prompts dla spójnego outputu.
- [Customer support agent | Anthropic](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat) — praktyczne wskazówki o grounding, citations i fact-checkingu.
- [Create custom subagents | Anthropic](https://code.claude.com/docs/en/sub-agents) — wzorce specjalizacji agentów i ograniczania tool access.
- [Common workflows | Anthropic](https://code.claude.com/docs/en/common-workflows) — plan mode i subagenci jako element workflowu.
- [Agents | LangChain](https://docs.langchain.com/oss/javascript/langchain/agents) — produkcyjny agent loop na LangGraph.
- [Retrieval | LangChain](https://docs.langchain.com/oss/python/langchain/retrieval) — fundamenty retrieval/RAG.
- [Build a custom RAG agent with LangGraph](https://docs.langchain.com/oss/python/langgraph/agentic-rag) — agentic RAG i routing „retrieve or answer”.
- [LangGraph overview](https://docs.langchain.com/oss/javascript/langgraph/overview) — durable execution, streaming, human-in-the-loop.
- [Exa search integration | LangChain](https://docs.langchain.com/oss/python/integrations/tools/exa_search) — przykład integracji search engine projektowanego dla LLM-ów.
- [LangSmith Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) — jak rozbijać jakość na komponenty i budować evale.
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation) — offline/online evaluation i production monitoring.
- [LangSmith home](https://docs.langchain.com/langsmith/home) — observability i debugging agentów niezależnie od stacku.
- [Agents | CrewAI](https://docs.crewai.com/en/concepts/agents) — role agentów; Researcher jako wyspecjalizowany członek zespołu.
- [Tools | CrewAI](https://docs.crewai.com/en/concepts/tools) — narzędzia, delegacja i capabilities.
- [Knowledge | CrewAI](https://docs.crewai.com/en/concepts/knowledge) — grounding w zewnętrznych źródłach i utrzymanie kontekstu.
- [Crews | CrewAI](https://docs.crewai.com/en/concepts/crews) — memory i cache utilization.
- [Sequential Processes | CrewAI](https://docs.crewai.com/en/learn/sequential-process) — pamięć, caching i callbacks.
- [Collaboration | CrewAI](https://docs.crewai.com/en/concepts/collaboration) — delegacja i praca zespołowa agentów.
- [Build Your First Crew | CrewAI](https://docs.crewai.com/en/guides/crews/first-crew) — oficjalny przykład research crew.
- [Deep Research Flow (CrewAI template)](https://github.com/crewAIInc/template_deep_research) — publiczny template routujący chat vs search i tworzący odpowiedzi z cytowaniami.
- [CrewAI Tracing](https://docs.crewai.com/en/observability/tracing) — built-in tracing dla crews i flows.
- [CrewAI Observability Overview](https://docs.crewai.com/en/observability/overview) — metryki jakości, kosztu i wydajności.
- [AutoGPT Classic](https://github.com/significant-gravitas/autogpt/blob/master/classic/README.md) — historyczny wzorzec goal decomposition i chaining działań.
- [BabyAGI](https://github.com/yoheinakajima/babyagi) — aktualny eksperymentalny framework; ważny historycznie, słaby jako produkcyjny wzorzec research-by-default.
- [BabyAGI Archive](https://github.com/yoheinakajima/babyagi_archive) — oryginalny loop task creation/execution/reprioritization.
- [Task-driven Autonomous Agent Utilizing GPT-4, Pinecone, and LangChain for Diverse Applications](https://yoheinakajima.com/task-driven-autonomous-agent-utilizing-gpt-4-pinecone-and-langchain-for-diverse-applications/) — opis genezy task-driven autonomous agents.
- [Deep Research From Scratch](https://github.com/langchain-ai/deep_research_from_scratch) — najlepszy publiczny materiał edukacyjny do scoping, MCP, supervisora i pełnego research workflow.
- [Open Deep Research](https://github.com/langchain-ai/open_deep_research) — otwarty deep research agent z wieloma modelami, search APIs i MCP.
- [Local Deep Researcher](https://github.com/langchain-ai/local-deep-researcher) — prosty, bardzo czytelny wzorzec iteracyjnego researchu opartego o knowledge gaps.
