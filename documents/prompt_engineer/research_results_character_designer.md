# Research: Wzorce projektowania persony i charakteru agentów AI

Data: 2026-03-22

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 5-7 najważniejszych wzorców/kierunków

1. **Najstabilniejszy wzorzec praktyczny to rozdzielenie “persony” od “reguł, narzędzi i orkiestracji”.** W dokumentacji OpenAI, Anthropic, LangChain i CrewAI persona jest elementem instrukcji/roli/backstory, ale nie zastępuje guardrails, handoffów, uprawnień i jawnych zasad eskalacji. **Siła dowodów:** praktyczne.  
   Źródła: [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/), [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html), [Anthropic prompt engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [CrewAI agents](https://docs.crewai.com/en/concepts/agents), [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

2. **Persona nie ma stabilnie potwierdzonego wpływu na poprawę trafności merytorycznej.** Są prace pokazujące zyski z role-play lub emotional framing na części benchmarków, ale są też prace pokazujące brak poprawy albo wręcz pogorszenie jakości rozumowania/faktografii przy personach w system promptach. **Siła dowodów:** empiryczne.  
   Źródła: [Better Zero-Shot Reasoning with Role-Play Prompting](https://arxiv.org/abs/2308.07702), [EmotionPrompt](https://arxiv.org/abs/2307.11760), [Personas in System Prompts Do Not Improve Performance](https://arxiv.org/abs/2311.10054), [Persona is a Double-edged Sword](https://arxiv.org/abs/2412.00804)

3. **W systemach wieloagentowych różnorodność stylów i heurystyk bywa cenna dla eksploracji, badań i generowania alternatyw, ale bez silnej orkiestracji łatwo przechodzi w chaos, redundancję albo “personality clash”.** Najczęściej działają układy supervisor + specjaliści albo agent-as-tool, z precyzyjnie opisanymi odpowiedzialnościami i zasadami delegacji. **Siła dowodów:** praktyczne + empiryczne.  
   Źródła: [OpenAI orchestration](https://openai.github.io/openai-agents-python/multi_agent/), [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents), [STORM](https://arxiv.org/abs/2402.14207), [Many Heads Are Better Than One](https://arxiv.org/abs/2410.09403), [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657)

4. **Najbardziej użyteczna persona to nie “powieść o charakterze”, tylko krótki profil operacyjny:** jak agent argumentuje, kiedy eskaluje, jak obchodzi się z niepewnością, jaki ma próg ryzyka, jak reaguje na konflikt i jaki ma styl współpracy. **Siła dowodów:** praktyczne + spekulacja.  
   Wprost ze źródeł: dokumentacje opisują rolę/backstory/system prompt jako sterowanie stylem, tonem i podejściem do zadania; synteza polegająca na sprowadzeniu tego do kontrolowanych wymiarów jest wnioskiem własnym opartym o te materiały.  
   Źródła: [OpenAI GPT builder help](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts), [Anthropic increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency), [CrewAI agents](https://docs.crewai.com/en/concepts/agents)

5. **Persona dryfuje w długich sesjach i przy dużym obciążeniu kontekstu.** Badania wskazują persona drift i identity drift już po kilku–kilkunastu rundach; praktyczne frameworki odpowiadają na to izolacją kontekstu (subagenci), przypomnieniami systemowymi, ewaluacją i ograniczaniem długości aktywnego kontekstu. **Siła dowodów:** empiryczne + praktyczne.  
   Źródła: [Identity Drift](https://arxiv.org/abs/2402.02896), [Measuring and Controlling Persona Drift](https://arxiv.org/html/2402.10962v1), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents), [CrewAI context window](https://docs.crewai.com/en/concepts/agents)

6. **Reguła nadrzędna: “charakter” powinien modulować sposób pracy, ale nie powinien być wyższego rzędu niż reguły bezpieczeństwa, zgodności i autoryzacji działań.** To jest spójne zarówno z dokumentacją modelową, jak i z praktykami agentowych frameworków. **Siła dowodów:** praktyczne.  
   Źródła: [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html), [Customizing ChatGPT Personality](https://help.openai.com/en/articles/11899719-customizing-your-chatgpt-personality), [Anthropic balancing autonomy and safety](https://docs.anthropic.com/en/docs/claude-code/iam#balancing-autonomy-and-safety)

## Wyniki per obszar badawczy

### 1. Wzorce projektowania persony agenta

**1.1. Najczęstszy framework praktyczny ma 5 warstw: rola, cel, persona, granice decyzyjne, przykłady zachowań.** **Siła dowodów:** praktyczne + spekulacja.  
Wprost ze źródeł:
- OpenAI modeluje agenta jako zestaw instrukcji, narzędzi, handoffów, guardrails i opcjonalnego output schema; sama persona mieści się zwykle w `instructions`, nie w warstwie narzędzi lub bezpieczeństwa.  
- CrewAI używa jawnie `role`, `goal`, `backstory`; backstory ma nadawać agentowi kontekst i osobowość.  
- Anthropic zaleca ustawić rolę w system prompt oraz dodać cechy, tło i oczekiwane reakcje w typowych scenariuszach.  
- LangChain opisuje multi-agent przede wszystkim jako problem context engineering; persona jest jednym z elementów promptu dla danego agenta, nie całym kontraktem architektonicznym.  
Źródła: [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/), [CrewAI agents](https://docs.crewai.com/en/concepts/agents), [Anthropic increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency), [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

**Syntetyczny wzorzec roboczy (wniosek własny na bazie źródeł):**
1. **Rola** — kim agent jest organizacyjnie.  
2. **Cel** — za co odpowiada.  
3. **Persona operacyjna** — jak pracuje pod presją, niepewnością i konfliktem.  
4. **Granice** — kiedy pyta, eskaluje, deleguje, odmawia.  
5. **Przykłady** — 2–5 scenariuszy referencyjnych.

**1.2. Warto kontrolować nie “cechy osobowości” same w sobie, tylko ich operacyjne odpowiedniki.** **Siła dowodów:** spekulacja oparta o praktykę.  
Najbardziej użyteczne wymiary do sterowania:
- **asertywność / poziom kwestionowania**  
- **evidentiary rigor / sceptycyzm dowodowy**  
- **kreatywność / dywergencyjność**  
- **ryzyko / ostrożność**  
- **autonomia / próg eskalacji**  
- **styl konfliktu** (konfrontacyjny, kooperacyjny, mediacyjny)  
- **jawność niepewności**  
- **planowanie vs improwizacja**  
To nie jest gotowy standard z jednej publikacji; to synteza wynikająca z tego, jak oficjalne frameworki opisują instrukcje, role i granice działania.  
Źródła: [OpenAI GPT builder help](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts), [CrewAI agents](https://docs.crewai.com/en/concepts/agents), [Anthropic increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)

**1.3. Empirycznie persona to narzędzie sterowania zachowaniem, nie gwarancja lepszego rozumowania.** **Siła dowodów:** empiryczne.  
Konflikt źródeł:
- [Role-Play Prompting](https://arxiv.org/abs/2308.07702) raportuje poprawę na części benchmarków reasoningowych względem zwykłego zero-shot.  
- [EmotionPrompt](https://arxiv.org/abs/2307.11760) pokazuje poprawę na części benchmarków po dodaniu emocjonalnych sygnałów mobilizujących.  
- [Personas in System Prompts Do Not Improve Performance](https://arxiv.org/abs/2311.10054) pokazuje brak systematycznej poprawy faktografii po dodaniu person w system promptach.  
- [Persona is a Double-edged Sword](https://arxiv.org/abs/2412.00804) pokazuje, że role/persony mogą poprawiać lub pogarszać wyniki zależnie od zadania, modelu i sposobu doboru persony.  
**Interpretacja konfliktu:** badania mierzą różne rzeczy: jedne — reasoning benchmarki lub instruction-following, inne — pytania faktograficzne. “Persona pomaga” nie jest tezą ogólną; bardziej trafne jest “persona zmienia heurystyki odpowiedzi, czasem korzystnie, czasem szkodliwie”.

**1.4. “Charakter” i “reguły” trzeba projektować jako osobne warstwy.** **Siła dowodów:** praktyczne.  
OpenAI opisuje hierarchię instrukcji (platforma → developer → user → guideline), a personalizacja nie ma unieważniać bezpieczeństwa i zasad wyższego rzędu. Anthropic explicite zaleca dodać jasne zasady, kiedy model ma prosić o potwierdzenie przed działaniami nieodwracalnymi lub ryzykownymi.  
Źródła: [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html), [Customizing ChatGPT Personality](https://help.openai.com/en/articles/11899719-customizing-your-chatgpt-personality), [Anthropic balancing autonomy and safety](https://docs.anthropic.com/en/docs/claude-code/iam#balancing-autonomy-and-safety)

**Trade-offy / alternatywy**
- **Persona cienka (1–2 zdania):** tańsza kontekstowo, mniej podatna na wewnętrzne sprzeczności, ale słabiej steruje zachowaniem w edge-case’ach.  
- **Persona średnia (krótki akapit + wymiary + przykłady):** najlepszy kompromis praktyczny.  
- **Persona długa / narracyjna:** może być ekspresyjna, ale zwykle zjada kontekst i utrudnia priorytetyzację instrukcji.

### 2. Persona w systemach wieloagentowych

**2.1. Persona wpływa na współpracę agent-agent głównie przez trzy mechanizmy: specjalizację, styl negocjacji i próg kwestionowania.** **Siła dowodów:** empiryczne + praktyczne.  
Wprost ze źródeł:
- Frameworki (OpenAI, LangChain, Anthropic, CrewAI) rozdzielają agentów według kompetencji, ale opisy ról/backstory/system promptów w praktyce nadają im także styl działania.  
- [LLM Agents in Interaction](https://arxiv.org/html/2408.08631v2) pokazuje, że agenci z różnymi profilami osobowości wykazują różny poziom spójności persony i odmienny poziom językowego dostrajania się do partnera w rozmowie.  
Źródła: [OpenAI orchestration](https://openai.github.io/openai-agents-python/multi_agent/), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents), [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents), [LLM Agents in Interaction](https://arxiv.org/html/2408.08631v2)

**2.2. “Team diversity” jest obiecująca, ale głównie dla eksploracji i twórczości, nie jako zasada uniwersalna.** **Siła dowodów:** empiryczne.  
- [STORM](https://arxiv.org/abs/2402.14207) pokazuje wartość wieloperspektywicznego zadawania pytań i syntezy przy tworzeniu artykułów opartych o research; raportuje poprawę organizacji i szerokości pokrycia względem baseline’u RAG.  
- [Many Heads Are Better Than One](https://arxiv.org/abs/2410.09403) pokazuje korzyści z wieloagentowego generowania idei naukowych.  
- [The Hidden Strength of Disagreement](https://arxiv.org/abs/2502.16565) sugeruje, że częściowe zachowanie różnorodności opinii zwiększa eksplorację i odporność zespołu.  
**Ograniczenie:** te wyniki nie znaczą, że każdy zespół agentów powinien być osobowościowo zróżnicowany; korzyści są najsilniejsze w zadaniach otwartych, badawczych i kreatywnych.

**2.3. Najbezpieczniejszy wzorzec to “komplementarność, nie antagonizm”.** **Siła dowodów:** praktyczne + spekulacja.  
Dokumentacje produkcyjne preferują komplementarne specjalizacje pod nadzorem orkiestratora:
- OpenAI pokazuje wzorzec manager + specjaliści / agent-as-tool.  
- LangChain opisuje supervisor + subagents.  
- Anthropic subagents mają własne prompty, narzędzia i ograniczenia.  
- CrewAI ma delegację jako opcję, domyślnie wyłączoną.  
To wspiera tezę, że lepiej projektować różnice typu “sceptyczny badacz” vs “syntezujący planista” niż “kłótliwy buntownik” vs “sztywny strażnik”, jeśli nie ma mechanizmu mediacji.  
Źródła: [OpenAI orchestration](https://openai.github.io/openai-agents-python/multi_agent/), [OpenAI portfolio collaboration example](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration.ipynb), [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents), [CrewAI agents](https://docs.crewai.com/en/concepts/agents)

**2.4. “Personality clash” zwykle nie jest wyłącznie problemem psychologicznym; to najczęściej problem słabego kontraktu komunikacyjnego i walidacji.** **Siła dowodów:** empiryczne + praktyczne.  
[Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) opisuje liczne failure modes w systemach wieloagentowych, w tym błędy specyfikacji, misalignment między agentami i problemy weryfikacji/terminacji. Wniosek praktyczny: sama poprawa opisów ról nie wystarcza; potrzebne są też protokoły przekazywania pracy, kryteria zakończenia i warstwa sprawdzająca.  
Źródła: [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657), [OpenAI handoffs](https://openai.github.io/openai-agents-python/handoffs/), [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

**2.5. Persona bazowa powinna być stabilna, a adaptacja — lokalna i kontrolowana.** **Siła dowodów:** spekulacja wsparta praktyką i badaniami o drift.  
Praktyka frameworków wskazuje na lokalne prompty per subagent i per task; badania o drift sugerują, że zbyt szeroka adaptacja zwiększa ryzyko rozjechania się zachowania. Sensowny kompromis:
- stała persona bazowa na poziomie agenta,
- kontekstowe “overrides” tylko dla trybu zadania (np. tryb audytu, tryb eksploracji, tryb krótkiej odpowiedzi),
- bez zmiany fundamentalnych granic ryzyka, eskalacji i rygoru dowodowego.  
Źródła: [OpenAI context management](https://openai.github.io/openai-agents-python/context/), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents), [Identity Drift](https://arxiv.org/abs/2402.02896)

### 3. Promptowanie persony

**3.1. Trwałą personę najlepiej umieszczać w najwyżej-priorytetowej warstwie instrukcji, a nie w efemerycznym user prompt.** **Siła dowodów:** praktyczne + empiryczne.  
- OpenAI opisuje `instructions` jako kanał wysokopoziomowego sterowania zachowaniem, tonem i celami.  
- Anthropic zaleca rolę w system prompt.  
- Badania o “position” wskazują, że pozycja promptu ma znaczenie dla siły efektu.  
Źródła: [OpenAI prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering), [Anthropic prompt engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Position is Power](https://arxiv.org/html/2505.21091v3)

**3.2. Najlepszy praktyczny format to osobna sekcja z jasnymi nagłówkami, nie rozsiana narracja.** **Siła dowodów:** praktyczne.  
Anthropic zaleca XML tags dla instrukcji, kontekstu, przykładów i wejścia. OpenAI zaleca nagłówki, wyraźne struktury, konkretne instrukcje i przykłady. Z punktu widzenia egzekwowalności persona powinna być sekcją równoległą do: mission, scope, critical rules, style, escalation.  
Źródła: [Anthropic prompt engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [OpenAI GPT builder help](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts)

**3.3. Jedno zdanie często wystarcza, by zmienić ton; ale zachowania graniczne wymagają bardziej konkretnego opisu i przykładów.** **Siła dowodów:** praktyczne.  
Anthropic wprost pisze, że nawet jednozdaniowe ustawienie roli potrafi zmienić zachowanie, ale jednocześnie zaleca dodanie osobowości, tła, cech oraz “common scenarios and expected responses” dla większej spójności. To sugeruje warstwowy wzorzec:
- **rdzeń:** 1–3 zdania o stylu pracy,
- **wymiary:** 3–7 kontrolowanych cech operacyjnych,
- **przykłady:** 2–5 sytuacji granicznych.  
Źródła: [Anthropic prompt engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [Anthropic increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)

**3.4. Few-shot examples są często skuteczniejsze od coraz dłuższego opisu persony.** **Siła dowodów:** praktyczne + spekulacja.  
Anthropic zaleca 3–5 przykładów. OpenAI również wskazuje przykłady jako silny mechanizm sterowania zachowaniem. To nie jest bezpośredni benchmark “opis vs przykłady”, ale praktyka dokumentacyjna jest spójna: lepiej pokazać 2–5 pożądanych reakcji niż dopisywać kolejne przymiotniki.  
Źródła: [Anthropic prompt engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [OpenAI GPT builder help](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts)

**3.5. Technik typu “take a deep breath”, emotional framing i role-play nie należy traktować jako uniwersalnych boosterów.** **Siła dowodów:** empiryczne.  
- [EmotionPrompt](https://arxiv.org/abs/2307.11760) pokazał zyski na części zadań.  
- [Role-Play Prompting](https://arxiv.org/abs/2308.07702) pokazał zyski na części benchmarków.  
- OpenAI dla modeli reasoningowych zaleca raczej proste, bezpośrednie instrukcje i ostrożność z nadmiarowym “think step by step”.  
- [Persona is a Double-edged Sword](https://arxiv.org/abs/2412.00804) pokazuje, że persona może również szkodzić.  
**Wniosek:** to techniki warunkowe, zależne od modelu i zadania.

**3.6. Długość sekcji persony powinna być minimalna, ale kompletna.** **Siła dowodów:** praktyczne + spekulacja.  
Nie udało się potwierdzić uniwersalnej liczby tokenów lub długości jako standardu branżowego. Da się jednak obronić praktyczny kompromis:
- 1 zdanie — zmiana tonu,
- 1 krótki akapit — zmiana stylu pracy,
- akapit + lista wymiarów + 2–5 przykładów — zachowania graniczne i większa spójność,
- pełna strona narracji — zwykle przerost formy nad sterowalnością.  
Źródła: [Anthropic prompt engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), [OpenAI reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)

### 4. Persona vs behavioral drift

**4.1. Persona zanika w długich sesjach — to zjawisko jest udokumentowane.** **Siła dowodów:** empiryczne.  
- [Identity Drift](https://arxiv.org/abs/2402.02896) pokazuje dryf tożsamości w rozmowach wieloturowych; przypisana persona nie rozwiązuje problemu automatycznie.  
- [Measuring and Controlling Persona Drift](https://arxiv.org/html/2402.10962v1) raportuje drift persony już po około 8 rundach i wiąże go z zanikiem uwagi na wcześniejsze instrukcje.  
Źródła: jw.

**4.2. Duże obciążenie kontekstu zwiększa ryzyko rozmycia persony i szczegółowych zasad.** **Siła dowodów:** praktyczne + empiryczne.  
- OpenAI Model Spec opisuje, że długie rozmowy mogą być obcinane/streszczane, a model ma ograniczony budżet kontekstowy.  
- CrewAI opisuje automatyczne streszczanie przy przepełnionym kontekście i ostrzega, że można stracić część szczegółów; w precyzyjnych domenach zaleca raczej RAG lub fail-fast niż agresywne streszczanie.  
- Badania o drift wspierają hipotezę, że to nie tylko problem “zmęczenia”, ale także mechaniki uwagi i pamięci w długim kontekście.  
Źródła: [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html), [CrewAI agents](https://docs.crewai.com/en/concepts/agents), [Measuring and Controlling Persona Drift](https://arxiv.org/html/2402.10962v1)

**4.3. Najsilniejsze praktyczne techniki anty-drift to: odświeżanie instrukcji, izolacja kontekstu i wyspecjalizowane subagenty.** **Siła dowodów:** praktyczne + empiryczne.  
- Badanie [Measuring and Controlling Persona Drift](https://arxiv.org/html/2402.10962v1) testuje m.in. system prompt repetition jako prostą technikę ograniczania driftu.  
- Anthropic i LangChain promują subagentów z własnym kontekstem i promptami; to redukuje mieszanie się długich historii rozmowy.  
- OpenAI oraz Anthropic zalecają dynamiczne lub wyspecjalizowane instrukcje/skills ładowane wtedy, gdy są potrzebne, zamiast trzymania wszystkiego stale w głównym promptcie.  
Źródła: [Measuring and Controlling Persona Drift](https://arxiv.org/html/2402.10962v1), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents), [OpenAI context management](https://openai.github.io/openai-agents-python/context/), [Anthropic CLAUDE.md guidance](https://www.anthropic.com/engineering/claude-code-best-practices)

**4.4. Warto walidować personę testami behawioralnymi, nie tylko subiektywnym wrażeniem.** **Siła dowodów:** spekulacja mocno wsparta literaturą ewaluacyjną.  
Praktyczny zestaw walidacji:
- scenariusze konfliktu, niepewności i presji czasu,
- testy “czy eskaluje za wcześnie / za późno”,
- testy “czy zachowuje rygor dowodowy pod naciskiem”,
- porównanie outputów z neutralną wersją agenta,
- oddzielny evaluator oceniający zgodność z personą po wymiarach.  
To nie jest jeden ustalony standard z dokumentacji, ale wynika wprost z badań o drift oraz z zaleceń OpenAI dotyczących evals i pinowania zachowania.  
Źródła: [OpenAI prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering), [Measuring and Controlling Persona Drift](https://arxiv.org/html/2402.10962v1)

### 5. Przykłady person w produkcyjnych systemach

**5.1. OpenAI: persona zwykle siedzi w `instructions`, a zespół agentów buduje się wokół specjalizacji i handoffów.** **Siła dowodów:** praktyczne.  
- Agents SDK opisuje agenta jako instrukcje + narzędzia + handoffs + guardrails.  
- Oficjalny cookbook z portfolio pokazuje managera oraz wyspecjalizowanych analityków (macro, fundamental, quantitative, execution), gdzie każdy pełni wyraźnie odmienną funkcję.  
To sugeruje, że w praktyce OpenAI promuje “charakter przez instrukcje i specjalizację”, a nie osobną formalną klasę personality.  
Źródła: [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/), [OpenAI orchestration](https://openai.github.io/openai-agents-python/multi_agent/), [Portfolio collaboration example](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration.ipynb)

**5.2. Anthropic: mocny nacisk na rolę/system prompt, scenariusze zachowań i subagentów z własnymi promptami i ograniczeniami.** **Siła dowodów:** praktyczne.  
Claude/Claude Code pokazują wzorzec, w którym subagent ma osobny kontekst, własny system prompt, opis delegacji i często ograniczony zestaw narzędzi. To bardzo silny wzorzec “persona jako lokalny profil operacyjny”.  
Źródła: [Anthropic increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents)

**5.3. CrewAI: persona jest jawnym, pierwszoklasowym elementem interfejsu projektowania agenta.** **Siła dowodów:** praktyczne.  
CrewAI wprost używa `role`, `goal`, `backstory`. W przykładach dominują archetypy w rodzaju: researcher, market analyst, writer, strategic planner. Backstory ma wpływać na podejście agenta do zadań.  
Źródła: [CrewAI agents](https://docs.crewai.com/en/concepts/agents), [CrewAI examples](https://github.com/crewAIInc/crewAI-examples)

**5.4. LangChain/LangGraph: persona jest słabiej sformalizowana niż w CrewAI, ale realnie obecna jako część promptu i podziału kontekstu.** **Siła dowodów:** praktyczne.  
LangChain opisuje supervisorów i workerów z indywidualnymi promptami; osobny tutorial z personal assistantem dzieli przestrzeń na specjalistów od kalendarza i emaila. Wzorzec jest bardziej architektoniczny niż psychologiczny, ale nadal zakłada odmienny styl działania per agent.  
Źródła: [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent), [LangChain personal assistant subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant)

**5.5. Najczęstsze archetypy w przykładach praktycznych**
- **researcher** — ciekawy, szeroki w eksploracji, dokładny w weryfikacji  
- **architect / planner** — systemowy, kompromisowy, pilnujący zależności  
- **analyst / critic** — sceptyczny, precyzyjny, nastawiony na ryzyka i niespójności  
- **developer / executor** — implementacyjny, pragmatyczny, krokowy  
**Siła dowodów:** praktyczne + spekulacja.  
To jest synteza z przykładów dokumentacyjnych i repozytoriów, nie wynik jednego benchmarku.  
Źródła: [CrewAI examples](https://github.com/crewAIInc/crewAI-examples), [OpenAI cookbook examples](https://github.com/openai/openai-cookbook), [LangChain open_deep_research](https://github.com/langchain-ai/open_deep_research)

**5.6. Nie udało się potwierdzić wielu twardych case studies produkcyjnych typu “ta persona zwiększyła KPI o X%”.** **Siła dowodów:** luka w wiedzy.  
Są liczne przykłady i repozytoria, ale mało publicznych, porównawczych case studies z produkcji pokazujących wpływ konkretnej persony na mierzalne KPI. To ważna luka.

### 6. Anti-patterns i pułapki

**6.1. Anty-wzorzec: traktowanie persony jako substytutu architektury lub polityki bezpieczeństwa.** **Siła dowodów:** praktyczne.  
Persona nie zastąpi guardrails, autoryzacji, kontroli narzędzi, kryteriów zakończenia ani walidacji. To wynika spójnie z dokumentacji OpenAI, Anthropic i LangChain.  
Źródła: [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/), [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html), [Anthropic sub-agents](https://code.claude.com/docs/en/sub-agents), [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

**6.2. Anty-wzorzec: nadmierna humanizacja.** **Siła dowodów:** empiryczne + spekulacja.  
Rozbudowana, emocjonalna albo teatralna persona może zwiększać ekspresję, ale nie ma mocnego dowodu, że poprawia trafność; część badań pokazuje wręcz szkody dla reasoning/faktografii. Dodatkowo mocne osadzenie cech demograficznych lub ideologicznych w system promptach może wzmacniać bias.  
Źródła: [Personas in System Prompts Do Not Improve Performance](https://arxiv.org/abs/2311.10054), [Persona is a Double-edged Sword](https://arxiv.org/abs/2412.00804), [Position is Power](https://arxiv.org/html/2505.21091v3)

**6.3. Anty-wzorzec: konflikt między personą a rolą techniczną.** **Siła dowodów:** spekulacja wsparta praktyką.  
Przykład: agent compliance z personą “wywrotowy buntownik” albo agent release-management z personą “ryzykant improwizator” bez jawnych ograniczeń. Taka persona może być użyteczna w eksploracji alternatyw, ale nie jako dominujący tryb agenta odpowiedzialnego za bezpieczeństwo, zgodność albo wykonanie zmian.  
Źródła: [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html), [Anthropic balancing autonomy and safety](https://docs.anthropic.com/en/docs/claude-code/iam#balancing-autonomy-and-safety)

**6.4. Anty-wzorzec: jednorodne zespoły z nadmiernym konformizmem.** **Siła dowodów:** empiryczne.  
Badania o multi-perspective research i o zachowaniu niezgody pokazują, że częściowa różnorodność może poprawić eksplorację. Jednorodny styl myślenia zwiększa ryzyko przedwczesnego konsensusu i pominięcia alternatyw.  
Źródła: [STORM](https://arxiv.org/abs/2402.14207), [The Hidden Strength of Disagreement](https://arxiv.org/abs/2502.16565)

**6.5. Anty-wzorzec: niekontrolowana różnorodność bez warstwy mediacji.** **Siła dowodów:** empiryczne + praktyczne.  
Zbyt silnie zróżnicowane persony bez supervisor-a, protokołu przekazywania pracy i kryteriów zakończenia zwiększają szansę na zapętlenia, konflikty i niespójne outputy.  
Źródła: [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657), [OpenAI handoffs](https://openai.github.io/openai-agents-python/handoffs/), [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)

**6.6. Są sytuacje, w których brak persony jest lepszy niż słaba persona.** **Siła dowodów:** spekulacja mocno wsparta konfliktami w badaniach.  
Dotyczy to zwłaszcza:
- zadań o wysokiej precyzji faktograficznej,
- agentów zgodności i bezpieczeństwa,
- agentów wykonujących wrażliwe działania,
- krótkich, jednorazowych zadań narzędziowych.  
W takich przypadkach neutralny, prosty prompt bywa bezpieczniejszy i bardziej przewidywalny niż barwna, niedostrojona persona.  
Źródła: [Personas in System Prompts Do Not Improve Performance](https://arxiv.org/abs/2311.10054), [OpenAI reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)

## Otwarte pytania / luki w wiedzy

- Nie udało się potwierdzić powszechnie przyjętego, formalnego frameworku branżowego dla “osobowości agenta” porównywalnego do np. standardowych wzorców architektury agentowej. W praktyce dominują lokalne schematy `instructions/role/backstory`.
- Brakuje publicznych, porównawczych case studies z produkcji pokazujących wpływ konkretnej persony na KPI (np. czas do rozwiązania, liczba eskalacji, jakość decyzji, satysfakcja użytkownika).
- Badania o wpływie persony są niespójne, bo mierzą różne cele: reasoning, faktografię, alignment, role-play consistency, social interaction. Nie ma jednej meta-konkluzji “persona działa / nie działa”.
- Nie udało się potwierdzić uniwersalnie optymalnej długości sekcji persony. Są tylko heurystyki praktyczne.
- Nie ma jeszcze mocnego, publicznego konsensusu, czy persony powinny być głównie statyczne, czy adaptacyjne; dane o drift sugerują ostrożność wobec zbyt swobodnej adaptacji.
- Wiele interesujących wyników w tym obszarze to preprinty arXiv, a nie dojrzałe standardy lub wielokrotnie zreplikowane wyniki.
- Nie udało się znaleźć solidnego, publicznego benchmarku stricte dla “multi-agent personality design” porównującego różne składy osobowości pod wspólnym protokołem.

## Źródła / odniesienia

### Oficjalna dokumentacja i materiały praktyczne

- [OpenAI Agents SDK — Agents](https://openai.github.io/openai-agents-python/agents/) — definicja agenta jako instrukcje + narzędzia + handoffs + guardrails; użyte do rozdzielenia persony od architektury i bezpieczeństwa.
- [OpenAI Agents SDK — Multi-agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/) — wzorce supervisor, handoffs, agents-as-tools; użyte do sekcji o współpracy agentów.
- [OpenAI Agents SDK — Handoffs](https://openai.github.io/openai-agents-python/handoffs/) — opis delegacji i znaczenia `handoff_description`; użyte przy wzorcach unikania clash.
- [OpenAI Agents SDK — Context management](https://openai.github.io/openai-agents-python/context/) — sposoby dostarczania kontekstu i instrukcji; użyte do sekcji o drift i adaptacji.
- [OpenAI Prompt Engineering Guide](https://developers.openai.com/api/docs/guides/prompt-engineering) — instrukcje, struktura promptu, przykłady, evals; użyte przy projektowaniu promptów persony.
- [OpenAI Reasoning Best Practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices) — zalecenia, by zachowywać prostotę i unikać pewnych triggerów; użyte przy technikach promptowania.
- [OpenAI Model Spec](https://model-spec.openai.com/2025-02-12.html) — hierarchia instrukcji i zasady nadrzędności; użyte przy rozdziale persona vs reguły.
- [Customizing Your ChatGPT Personality](https://help.openai.com/en/articles/11899719-customizing-your-chatgpt-personality) — explicite rozróżnia osobowość komunikacyjną od zasad bezpieczeństwa.
- [Creating and Editing GPTs](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts) — praktyczne wskazówki o instrukcjach, strukturze i przykładach.
- [Anthropic Prompt Engineering Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — XML tags, role prompt, przykłady; kluczowe dla sekcji o strukturze promptu.
- [Anthropic — Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — zalecenia o roli, osobowości, tle i typowych scenariuszach; użyte przy spójności persony.
- [Anthropic Claude Code — Sub-agents](https://code.claude.com/docs/en/sub-agents) — subagenci z własnym promptem, narzędziami i kontekstem; użyte przy izolacji persony i anti-drift.
- [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) — wskazówki o ograniczaniu bazowego kontekstu i ładowaniu wyspecjalizowanych instrukcji na żądanie.
- [Anthropic — Balancing autonomy and safety](https://docs.anthropic.com/en/docs/claude-code/iam#balancing-autonomy-and-safety) — zasady potwierdzania działań ryzykownych; użyte przy autonomii vs eskalacji.
- [CrewAI — Agents](https://docs.crewai.com/en/concepts/agents) — `role`, `goal`, `backstory`, delegacja, pamięć i zarządzanie kontekstem; podstawowe źródło praktyczne.
- [CrewAI Examples](https://github.com/crewAIInc/crewAI-examples) — przykłady ról i archetypów agentów.
- [LangChain — Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent) — wzorce kontekstowe i architektoniczne dla multi-agent.
- [LangChain — Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) — supervisor + subagents, context isolation; użyte przy sekcji o współpracy i drift.
- [LangChain — Personal Assistant with Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant) — przykład produkcyjnego podziału promptów i zadań.
- [OpenAI Cookbook — Multi-Agent Portfolio Collaboration](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration.ipynb) — oficjalny przykład managera i wyspecjalizowanych agentów.
- [LangChain Open Deep Research](https://github.com/langchain-ai/open_deep_research) — repozytorium pokazujące realny wzorzec supervisor/researcher dla research workflows.

### Badania i preprinty

- [Better Zero-Shot Reasoning with Role-Play Prompting](https://arxiv.org/abs/2308.07702) — benchmarki reasoningowe, gdzie role-play poprawia wyniki; użyte jako źródło “persona może pomagać”.
- [EmotionPrompt: Leveraging Psychology for Large Language Models Enhancement via Emotional Stimulus](https://arxiv.org/abs/2307.11760) — wpływ emocjonalnych triggerów na wyniki benchmarków; użyte ostrożnie jako dowód sąsiedni wobec persony.
- [Personas in System Prompts Do Not Improve Performance of Large Language Models](https://arxiv.org/abs/2311.10054) — brak ogólnej poprawy po dodaniu person w system promptach; kluczowe źródło kontrujące entuzjazm wobec person.
- [Persona is a Double-edged Sword: Mitigating Role-Play Degradation and Harnessing the Power of Neutral Personas](https://arxiv.org/abs/2412.00804) — pokazuje, że persona może szkodzić lub pomagać; użyte do sekcji o trade-offach i anti-patterns.
- [Identity Drift: How Personas Shift in Multi-Turn Conversations](https://arxiv.org/abs/2402.02896) — źródło o dryfie tożsamości i niestabilności persony.
- [Measuring and Controlling Persona Drift in Language Model Dialogues](https://arxiv.org/html/2402.10962v1) — benchmark i techniki ograniczania persona drift.
- [LLM Agents in Interaction: Measuring Personality Consistency and Linguistic Alignment in Collaborative Writing](https://arxiv.org/html/2408.08631v2) — wpływ profili osobowości na interakcję agent-agent.
- [Enhancing Persona Consistency for LLMs’ Role-Playing through Persona-Aware Contrastive Learning](https://arxiv.org/html/2503.17662v2) — źródło o poprawie spójności persony metodami treningowymi, nie tylko promptowaniem.
- [Dialogue Language Model with Large-Scale Persona Data Engineering](https://arxiv.org/html/2412.09034v1) — pokazuje, że dane/trening mogą poprawiać consistency i jakość odpowiedzi.
- [STORM: A Multi-perspective and Iterative Co-STORM Writing System for Knowledge Curation](https://arxiv.org/abs/2402.14207) — wartość wielu perspektyw w research i syntezie.
- [Many Heads Are Better Than One: Improving Scientific Idea Generation by Simulating Multi-agent Collaboration](https://arxiv.org/abs/2410.09403) — korzyści z wieloagentowej współpracy w zadaniach kreatywnych.
- [The Hidden Strength of Disagreement in Multi-Agent Collaboration](https://arxiv.org/abs/2502.16565) — argument za utrzymaniem częściowej różnorodności poglądów.
- [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) — failure modes systemów wieloagentowych; użyte przy sekcji o personality clash i walidacji.
- [PRISM: A Prompting-Routing-Internalizing Sequential Meta-framework for Role Prompting](https://arxiv.org/pdf/2603.18507) — bardzo świeży preprint sugerujący, że skuteczność ekspertowych person zależy od typu zadania, długości i umiejscowienia promptu; użyte ostrożnie jako sygnał badawczy.
- [The Impact of Role Design in In-Context Learning Messages](https://arxiv.org/pdf/2509.23501) — sygnał, że pozycja i rozkład instrukcji w wiadomościach mogą wpływać na wyniki; użyte pomocniczo.
- [Position is Power: System Prompts as a Vector of Demographic Bias in LLMs](https://arxiv.org/html/2505.21091v3) — użyte pomocniczo do tezy, że pozycja promptu wzmacnia efekt i może wzmacniać bias.

## Uwaga metodologiczna

- W części “praktycznej” preferowane były oficjalne dokumentacje frameworków i oficjalne repozytoria z przykładami.
- W części “empirycznej” istotna część materiału to preprinty arXiv. Tam, gdzie źródła się rozjeżdżają, konflikt został opisany jawnie zamiast uśredniania.
- Tam, gdzie nie udało się potwierdzić branżowego konsensusu lub publicznych case studies produkcyjnych, zaznaczono to jako lukę, a nie jako negatywny wynik.