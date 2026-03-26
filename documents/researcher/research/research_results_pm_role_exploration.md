# Research: Rola Manager/Orchestrator w systemach multi-agent

Data: 2026-03-26

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 7 najważniejszych kierunków

1. **„Manager” nie jest jedną rolą, tylko rodziną wzorców.** W praktyce powtarzają się co najmniej cztery formy: (a) supervisor jako pełnoprawny agent, (b) workflow/runtime orchestrator, (c) selector/group-chat manager wybierający kolejnego wykonawcę, (d) warstwa handoff/interoperability między agentami. Najczęściej te wzorce współistnieją w jednym systemie. — siła dowodów: **praktyczne**
2. **Najważniejsze rozróżnienie architektoniczne brzmi: manager jako agent vs manager jako mechanizm frameworka.** LangChain/CrewAI/MetaGPT pokazują managera jako „rolę”, a LangGraph/ADK/Agent runtimes często przesuwają część obowiązków managera do warstwy wykonawczej, checkpointingu i routingu. — siła dowodów: **praktyczne**
3. **Długie horyzonty pracy prawie zawsze kończą się na tych samych wzorcach operacyjnych:** compaction/summarization, checkpointing, zewnętrzna pamięć, fresh-session handoff i/lub stan zapisywany poza samą rozmową. „Wieczna jedna sesja” nie wygląda na dominujący wzorzec produkcyjny. — siła dowodów: **praktyczne**
4. **Autonomiczna priorytetyzacja zwykle jest heurystyczna, a nie formalnie optymalizowana.** W dokumentacji i implementacjach dominują planowanie, task decomposition, kolejki, dependency-aware execution, selektory następnego agenta i retry/interrupt loops; mało jest solidnych, praktycznych dowodów na „uniwersalny” scheduler dla LLM-agentów. — siła dowodów: **praktyczne** z komponentem **empirycznym**
5. **Budżet tokenów/API jest traktowany jak zasób operacyjny systemu, ale literatura o ROI per agent/task jest jeszcze rzadka.** Frameworki dają rate limiting, call limits, prompt caching, model fallbacki, tracing i metryki, ale mało jest publicznych, zweryfikowanych metod liczenia „zwrotu” z pracy poszczególnych agentów. — siła dowodów: **praktyczne**
6. **Always-on systemy zwykle nie są „jedną niekończącą się rozmową”, tylko zestawem trwałych runtime’ów, kolejek, tasków asynchronicznych i healthchecków.** Często agent ma lifecycle spawn/run/checkpoint/idle/retry/resume, a nie jedną nieprzerwaną sesję konwersacyjną. — siła dowodów: **praktyczne**
7. **Skalowanie managera prowadzi do hierarchii planner → coordinator → workers albo root agent → subagents → remote agents.** Empiryczne prace (MAGIS, Magentic-One, Workforce/OWL, StackPlanner) sugerują, że centralna koordynacja nadal działa dobrze, ale wymaga pamięci, ledgerów albo warstwy runtime; ryzyko bottlenecku i centralnego punktu awarii pozostaje otwarte. — siła dowodów: **empiryczne** + **praktyczne**

## Wyniki per klaster

### Klaster 1: Manager agent w multi-agent systems

**Odkryte projekty/frameworki:**
- [LangChain / supervisor pattern](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant) — supervisor jest osobnym agentem koordynującym wyspecjalizowanych workerów; manager utrzymuje kontekst i deleguje zadania do specjalistów. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [LangChain / Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent) — framework opisuje managera bardziej jako wzorzec orkiestracji niż jedną konkretną klasę; nacisk na wybór patternu zależnie od granic kontekstu i narzędzi. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [CrewAI / Hierarchical Process](https://docs.crewai.com/en/learn/hierarchical-process) — manager może być automatycznie tworzony przez framework albo wskazany explicite jako `manager_agent`; deleguje, waliduje i nadzoruje outcome’y. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [CrewAI / Custom Manager Agent](https://docs.crewai.com/en/learn/custom-manager-agent) — manager jest pełnoprawnym agentem-rolą, którą można zapromptować i skonfigurować jak resztę zespołu. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [AutoGen / Group Chat](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/group-chat.html) — manager grupy wybiera kolejnego mówcę/agenta; wzorzec bardziej „selector/coordinator” niż klasyczny PM. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [AutoGen / Magentic-One](https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/magentic-one.html) — lead agent „Orchestrator” planuje, śledzi postęp, przeplanowuje i kieruje wyspecjalizowanymi agentami narzędziowymi. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Google ADK / Multi-agent systems](https://google.github.io/adk-docs/agents/multi-agents/) — ADK rozróżnia agentów LLM, workflow agents i custom agents; manager może być agentem-LLM albo deterministycznym workflow managerem. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [OpenAI Agents SDK / Agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/) — formalizuje dwa tryby: orchestracja LLM-driven albo code-driven; manager może być agentem albo kodem otaczającym agentów. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [OpenAI Agents SDK / Handoffs](https://openai.github.io/openai-agents-python/handoffs/) — handoff jest reprezentowany jako narzędzie; pokazuje wzorzec „triage/dispatcher managera” raczej niż pełnego PM. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [MetaGPT](https://docs.deepwisdom.ai/main/en/guide/get_started/introduction.html) — jawnie modeluje role organizacyjne (product manager, architect, project manager, engineer) i SOP-y zespołu LLM. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [A2A Protocol](https://a2a-protocol.org/latest/) — nie definiuje „managera” jako roli, ale tworzy warstwę interoperacyjności dla delegacji i współpracy agentów między frameworkami; ważne dla manager-of-managers i agentów zdalnych. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Anthropic: multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — opisuje lead agenta, który analizuje zadanie, tworzy strategię i spawnuje subagentów równolegle. To bardziej case study niż framework. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [MAGIS](https://openreview.net/forum?id=qevq3FZ63J&referrer=%5Bthe+profile+of+Wenqiang+Zhang%5D%28%2Fprofile%3Fid%3D~Wenqiang_Zhang1%29) — empiryczny framework z rolami Manager / Repository Custodian / Developer / QA. Manager koordynuje cały proces rozwiązywania issue. — siła dowodu: **empiryczne** — relevance: **wysoka**

**Kluczowe koncepcje/wzorce:**
- **Supervisor** — centralny agent utrzymujący wysokopoziomowy kontekst i delegujący do specjalistów; mocny wzorzec w LangChain i CrewAI. — źródła: LangChain supervisor, CrewAI hierarchical — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Selector / next-speaker manager** — manager wybiera, kto mówi/pracuje dalej, zamiast sam wykonywać planowanie domenowe; typowe dla AutoGen Group Chat / Selector Group Chat. — źródła: AutoGen Group Chat, Selector Group Chat — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Orchestrator with ledgers** — manager utrzymuje explicite plan/postęp/fakty/hipotezy, zamiast polegać wyłącznie na „pamięci rozmowy”; silnie widoczne w Magentic-One. — źródła: Magentic-One paper, AutoGen Magentic-One docs — siła dowodu: **empiryczne** — relevance: **wysoka**
- **Workflow manager** — manager nie musi być LLM-em; może być deterministycznym wykonawcą sekwencji/paralelizmu/pętli, a tylko subagenci są LLM-ami. — źródła: ADK workflow agents, OpenAI code-driven orchestration, LangGraph — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Handoff / transfer** — manager może przekazać odpowiedzialność innemu agentowi (OpenAI handoff, ADK sub-agent transfer), zamiast tylko wywołać go jako narzędzie. — źródła: OpenAI Handoffs, ADK AgentTool docs — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Shared thread vs isolated context** — część systemów koordynuje przez wspólny wątek wiadomości (AutoGen Group Chat), a część przez izolowane konteksty i zwracanie tylko streszczeń (LangChain subagents, Anthropic subagents). — źródła: AutoGen Group Chat, LangChain subagents, Anthropic context engineering — siła dowodu: **praktyczne** — relevance: **wysoka**

**Wątki do głębszego zbadania (Faza 2):**
- Jakie obowiązki managera są stabilnie przypisywane agentowi, a jakie runtime’owi? — to kluczowy podział architektoniczny, który przewija się przez prawie wszystkie frameworki.
- Kiedy lepszy jest handoff (przekazanie kontroli), a kiedy „agent as tool” (utrzymanie kontroli przez managera)? — to wpływa na granice odpowiedzialności i format komunikacji.
- Czy są empiryczne porównania supervisor vs workflow orchestrator vs selector group chat na tych samych benchmarkach? — brak bezpośrednich, produkcyjnie istotnych porównań.

**Luki:**
- Nie udało się potwierdzić jednej powszechnie przyjętej taksonomii ról manager/supervisor/coordinator/planner/dispatcher/scheduler.
- Mało publicznych opisów managera stricte jako „PM 24/7” dla zespołu długowiecznych agentów; większość źródeł opisuje orchestration pattern, nie rolę operacyjną w czasie ciągłym.

### Klaster 2: Long-running LLM sessions

**Odkryte projekty/frameworki:**
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — opisuje context jako zasób ograniczony; wskazuje compaction, structured note-taking i multi-agent architectures jako praktyczne mechanizmy dla długich zadań. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Claude Code: Manage costs effectively](https://docs.anthropic.com/en/docs/claude-code/costs) — pokazuje auto-compaction, prompt caching, `/clear`, `/resume`, delegację do subagentów i koszt mnożący się wraz z liczbą aktywnych agentów/team mates. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Claude Code: Hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) — wspiera re-injection krytycznego kontekstu po compaction przez `SessionStart` hook z matcherem `compact`. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Claude Code: Common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows) — dokumentuje resume, session naming i zarządzanie sesjami; pokazuje, że praca rozciągnięta w czasie jest wspierana jako wzorzec użytkowy. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — stan grafu jest checkpointowany na każdym kroku; wątki (`thread_id`) i checkpointy są obiektem pierwszej klasy. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [CrewAI / Crews](https://docs.crewai.com/en/concepts/crews) — expose’uje pamięć, cache, callbacki, planning i `max_rpm`; sugeruje utrzymywanie stanu poza pojedynczą rozmową. — siła dowodu: **praktyczne** — relevance: **średnia–wysoka**
- [CrewAI / Replay tasks](https://docs.crewai.com/en/learn/overview) — replay i odtwarzanie kontekstu z poprzednich kickoffów sugerują handoff między uruchomieniami, nie jedną ciągłą sesję. — siła dowodu: **praktyczne** — relevance: **średnia–wysoka**
- [AutoGen runtime + state](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/framework/agent-and-agent-runtime.html) — runtime zarządza lifecycle’em agentów, komunikacją i środowiskiem wykonania; wspiera wzorzec „żyje runtime, niekoniecznie jedna konwersacja”. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Amazon Bedrock AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html) — explicit support dla async/long-running tasks, statusów `Healthy` / `HealthyBusy` i sesji auto-terminowanej po idle. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — nowsza warstwa praktyk dla agentów pracujących przez wiele context windows; ważny sygnał, że problem jest aktywnie nierozwiązany i operacyjnie istotny. — siła dowodu: **praktyczne** — relevance: **wysoka**

**Kluczowe koncepcje/wzorce:**
- **Compaction / summarization boundary** — po zapełnieniu kontekstu system kompresuje historię i wstrzykuje skrót zamiast trzymać pełną rozmowę. — źródła: Anthropic context engineering, Claude Code costs/hooks — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Checkpointing** — zapisywanie stanu po każdym kroku lub ważnym przejściu, by umożliwić resume, time-travel debugging i crash recovery. — źródła: LangGraph persistence, CrewAI persist/replay, AutoGen state/runtime — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Fresh-context subagents** — zamiast doklejać wszystko do jednej rozmowy, nowe subagenty startują z czystym kontekstem i oddają tylko wynik/streszczenie. — źródła: Anthropic multi-agent research system, LangChain subagents, Claude Code docs — siła dowodu: **praktyczne** — relevance: **wysoka**
- **External memory / filesystem handoff** — stan i artefakty są zapisywane poza rozmową (pliki, pamięć, traces, task state), a nie wyłącznie w message history. — źródła: Anthropic multi-agent research system, LangGraph persistence, ADK artifacts — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Session rotation / resume** — system wraca do wcześniejszych sesji albo odtwarza je z checkpointu, zamiast utrzymywać nieskończony context window. — źródła: Claude Code common workflows, Bedrock AgentCore, LangGraph — siła dowodu: **praktyczne** — relevance: **wysoka**

**Wątki do głębszego zbadania (Faza 2):**
- Jakie informacje powinny przechodzić przez handoff między sesjami tego samego agenta, a jakie powinny być rekonstruowane z zewnętrznego stanu? — to fundamentalne dla długiego horyzontu.
- Jak mierzyć „context rot” i drift operacyjny na wielogodzinnych/wielodniowych sesjach? — dużo praktyk, mało jawnych metryk.
- Jakie są najskuteczniejsze schematy checkpointów: po narzędziu, po tasku, po etapie planu, po przekroczeniu token threshold? — obecnie to rozproszone praktyki.

**Luki:**
- Nie udało się znaleźć stabilnego, publicznego wzorca „handoff między sesjami tego samego agenta” opisanego tak rygorystycznie jak np. checkpointing w workflow engine.
- Mało porównań empirycznych między „jedna długa sesja + compaction” vs „wiele krótszych sesji + explicit handoff”.

### Klaster 3: Autonomiczna priorytetyzacja i scheduling

**Odkryte projekty/frameworki:**
- [Magentic-One paper](https://arxiv.org/abs/2411.04468) — Orchestrator utrzymuje outer task ledger i inner progress ledger, re-planing i corrective actions; to jeden z najlepiej opisanych wzorców autonomicznego decydowania „co dalej”. — siła dowodu: **empiryczne** — relevance: **wysoka**
- [OWL / Workforce](https://openreview.net/forum?id=MBJ46gd1CT) — hierarchia Planner → Coordinator → Workers; silny wątek rozdzielenia strategicznego planowania od egzekucji domenowej. — siła dowodu: **empiryczne** — relevance: **wysoka**
- [StackPlanner](https://arxiv.org/abs/2601.05890) — centralny manager steruje pamięcią taskową i doświadczeniem; interesujące połączenie schedulingu z memory control. — siła dowodu: **empiryczne** — relevance: **wysoka**
- [OpenAI Agents SDK / orchestration](https://openai.github.io/openai-agents-python/multi_agent/) — eksplikuje dwa tryby sterowania przepływem: LLM-driven i code-driven, czyli scheduler może być heurystyczny/modelowy albo deterministyczny/kodowy. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [CrewAI / processes](https://docs.crewai.com/en/concepts/processes) — sekwencyjny, hierarchiczny i hybrydowy sposób wykonywania tasków; manager może tworzyć i delegować zadania w structured chain-of-command. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [LangGraph / durable execution + interrupts](https://docs.langchain.com/langsmith/core-capabilities) — harmonogram pracy może być osadzony w grafie z kolejkami, retry, background runs, cron i human interrupts. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Anthropic: multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — lead agent ocenia zapytanie, projektuje strategię i spawnuje subagentów równolegle; pokazuje praktyczny scheduler oparty na decompozycji i równoległości. — siła dowodu: **praktyczne** — relevance: **wysoka**

**Kluczowe koncepcje/wzorce:**
- **Planner / Coordinator / Workers split** — strategiczna priorytetyzacja jest oddzielona od wykonania; to najmocniej powtarzający się wzorzec w źródłach empirycznych. — źródła: Workforce/OWL, StackPlanner, MAGIS — siła dowodu: **empiryczne** — relevance: **wysoka**
- **Ledger-based control** — zamiast „intuicyjnej” kolejnej decyzji manager utrzymuje jawne rejestry: fakty, hipotezy, plan, status, stuckness, next action. — źródła: Magentic-One paper — siła dowodu: **empiryczne** — relevance: **wysoka**
- **Dependency-aware scheduling** — kolejność działań wynika z tego, które capability muszą odblokować następne kroki; często realizowane przez workflow graphs lub sekwencyjnych managerów. — źródła: ADK SequentialAgent, CrewAI processes, LangGraph — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Parallel fan-out + synthesis** — manager odpala kilka równoległych agentów na niezależnych podzadaniach, a potem syntezuje wynik. — źródła: Anthropic multi-agent research system, LangChain subagents, ADK ParallelAgent — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Human interrupt / approval gate** — autonomia bywa płynna: system pracuje sam, ale runtime dopuszcza zatrzymanie, akceptację lub poprawkę człowieka. — źródła: LangGraph persistence, OpenAI Agents human-in-the-loop/tracing, CrewAI docs — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Termination / stuck detection** — scheduler musi wykrywać zapętlenie, brak postępu i przekroczenia budżetu; jest to jawnie modelowane np. w Magentic-One. — źródła: Magentic-One paper, AutoGen termination/state docs — siła dowodu: **empiryczne** — relevance: **wysoka**

**Wątki do głębszego zbadania (Faza 2):**
- Jakie heurystyki priorytetyzacji pojawiają się najczęściej w praktyce: value/effort, dependency depth, recency, risk, deadline, unblockers? — eksploracja pokazała wzorce, ale nie ustandaryzowaną taksonomię.
- Jak implementacje rozwiązują repriorytetyzację „w locie” po nowych faktach, failure albo zmianie celu? — w dokumentacji jest to obecne, ale rzadko rozpisane operacyjnie.
- Jak wygląda graceful degradation autonomii: od pełnej autonomii do approval gates? — dużo deklaracji, mało precyzyjnych mechanizmów porównanych na wspólnych scenariuszach.

**Luki:**
- Nie udało się potwierdzić publicznego „standard scheduler benchmark” dla systemów wieloagentowych LLM.
- Mało źródeł pokazuje, jak dokładnie godzić priorytety człowieka z dynamiczną autonomią managera w produkcyjnym backlogu.

### Klaster 4: Token/API budget management

**Odkryte projekty/frameworki:**
- [Anthropic API: rate limits](https://docs.anthropic.com/en/api/rate-limits) — jawnie opisuje input/output token per minute, nagłówki limitów i podział capacity między workspaces/organizację. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Anthropic: prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — caching jest traktowany jako pierwszy mechanizm ograniczania kosztów i ponownego użycia wspólnego kontekstu. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Claude Code: costs](https://docs.anthropic.com/en/docs/claude-code/costs) — dokumentuje praktyki obniżania kosztu: utrzymywanie małego kontekstu, subagenci, model selection, compaction, narzut agent teams. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Claude Code Analytics API](https://docs.anthropic.com/en/api/claude-code-analytics-api) — daje programatyczny dostęp do usage analytics; istotne dla monitoringu budżetu, nie tylko dla samej konwersacji. — siła dowodu: **praktyczne** — relevance: **średnia–wysoka**
- [CrewAI / Crews](https://docs.crewai.com/en/concepts/crews) — exposes `max_rpm`, planning, callbacks, output logs i pamięć; sugeruje throttling i budżetowanie na poziomie crew. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [CrewAI / Agents](https://docs.crewai.com/en/concepts/agents) — agent-level `max_rpm`, `max_iter`, `max_execution_time`, `respect_context_window`; budżet jest sterowalny lokalnie, nie tylko centralnie. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [LangChain middleware / model & tool call limits](https://docs.langchain.com/oss/python/langchain/multi-agent) — w ekosystemie LangChain pojawiają się middleware ograniczające liczbę wywołań modelu i narzędzi; to budżetowanie przez guardrails. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [OpenAI Agents SDK / tracing](https://openai.github.io/openai-agents-python/tracing/) — tracing obejmuje generacje, handoffy, narzędzia i usage, co daje podstawę do rozliczania kosztu przepływu. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [AutoGen Core](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/index.html) — event-driven runtime i cache/token-limiting patterny wskazują, że koszt i przepustowość są częścią architektury, nie tylko promptu. — siła dowodu: **praktyczne** — relevance: **średnia–wysoka**

**Kluczowe koncepcje/wzorce:**
- **Central capacity planning** — limity są rozdzielane między użytkowników/workspaces/agenty, a nie tylko pilnowane „per request”. — źródła: Anthropic rate limits, Claude Code costs — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Prompt caching as budget primitive** — cache redukuje koszt i presję na limity, zwłaszcza przy powtarzalnych system promptach, narzędziach i wspólnym kontekście. — źródła: Anthropic prompt caching, web-search caching docs — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Context quarantine** — drogie/hałaśliwe operacje są wypychane do subagentów, żeby główny agent nie płacił za ich pełny transcript. — źródła: Claude Code costs, LangChain subagents, Anthropic multi-agent research system — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Budget guardrails** — ograniczenia na model calls, tool calls, runtime duration, iteration count i RPM pełnią rolę schedulerów kosztu. — źródła: CrewAI agents/crews, LangChain middleware, OpenAI tracing — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Observability-before-optimization** — tracing, analytics i logi pojawiają się przed „inteligentnym” ROI per agent; praktyka najpierw mierzy koszt, dopiero potem optymalizuje. — źródła: OpenAI tracing, Anthropic analytics API, AgentOps/ADK observability — siła dowodu: **praktyczne** — relevance: **wysoka**

**Wątki do głębszego zbadania (Faza 2):**
- Jak liczyć ROI per agent/task w systemie wieloagentowym: per token, per koszt, per latency, per sukces, per unblocker? — eksploracja ujawniła lukę, nie gotową odpowiedź.
- Jak projektować „token scheduling” dla wielu agentów pracujących równolegle pod wspólnym limitem organizacji? — dokumentacja daje prymitywy, ale mało wzorców sterowania.
- Jak kontynuować pracę przy odnawialnych limitach (okna 5h/tydzień itp.) bez zatrzymania całości systemu? — wymaga połączenia throttlingu, kolejek i checkpointów.

**Luki:**
- Nie udało się znaleźć publicznego, dojrzałego wzorca liczenia zwrotu z budżetu tokenów na poziomie poszczególnych ról agentowych.
- Mało empirycznych badań porównujących polityki budżetowania dla multi-agent LLM w warunkach produkcyjnych.

### Klaster 5: Always-on agent systems

**Odkryte projekty/frameworki:**
- [LangSmith / core capabilities](https://docs.langchain.com/langsmith/core-capabilities) — background runs, cron jobs, retry policies, queueing concurrent input i trwałość przez restarty/infrastructure failures. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — baza dla durable execution i resume, potrzebna do systemów działających stale. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Amazon Bedrock AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html) — explicit session lifecycle z `Healthy` / `HealthyBusy`, async tasks i auto-termination po idle. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [Anthropic: multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — case study opisuje systemy działające niemal ciągle i operacyjne problemy deploy/restart/parallelism. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [CrewAI docs overview](https://docs.crewai.com/en/learn/overview) — async kickoff, long-running workflows, replay i persistence sugerują architekturę bliższą automations/runtime niż czatowi ad hoc. — siła dowodu: **praktyczne** — relevance: **średnia–wysoka**
- [Claude Code Remote Control](https://docs.anthropic.com/en/docs/claude-code/remote-control) — pokazuje ograniczenie „session must stay running locally”; ważne jako kontrprzykład: nie każdy agent runtime jest natywnie durable. — siła dowodu: **praktyczne** — relevance: **średnia**
- [Claude Code Common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows) — scheduled runs istnieją, ale są nadal mocno związane z lifecycle’em konkretnego środowiska uruchomienia. — siła dowodu: **praktyczne** — relevance: **średnia**

**Kluczowe koncepcje/wzorce:**
- **Spawn → run → checkpoint → idle → resume** — lifecycle agenta częściej przypomina job/workflow engine niż niekończący się czat. — źródła: LangSmith core capabilities, Bedrock AgentCore, LangGraph persistence — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Healthcheck / ping semantics** — always-on systemy expose’ują jawny stan zdrowia i obciążenia, żeby odróżnić „żyje, ale pracuje” od „żyje i czeka”. — źródła: Bedrock AgentCore `/ping`, LangSmith deployment docs — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Retry + durable queue** — odporność bierze się z kolejek, ponowień i checkpointów, a nie z wiary w nieprzerwaną sesję modelu. — źródła: LangSmith core capabilities, CrewAI persist, Anthropic research system — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Idle policy** — systemy albo usypiają sesję po idle, albo kończą ją i polegają na resume/restart; „wiecznie aktywny” proces jest raczej wyjątkiem niż regułą. — źródła: Bedrock AgentCore, Claude Remote Control docs — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Deployment continuity** — always-on wymaga mechanizmu bezpiecznych deployów, które nie zabijają trwających agentów. — źródła: Anthropic multi-agent research system (rainbow deployments) — siła dowodu: **praktyczne** — relevance: **wysoka**

**Wątki do głębszego zbadania (Faza 2):**
- Jakie runtime’y realnie wspierają długotrwałe taski, restart po awarii i bezpieczne wdrożenia bez utraty pracy? — potrzeba porównania na poziomie operacyjnym, nie tylko API docs.
- Jak projektować idle behavior: polling, event-driven wake-up, sleep, proactive discovery? — eksploracja pokazała wzorce, ale nie ich koszty/trade-offy.
- Jak wygląda crash recovery dla agentów z narzędziami o skutkach ubocznych? — to krytyczny temat dla systemów autonomicznych.

**Luki:**
- Nie udało się znaleźć wielu publicznych opisów systemów „24/7” z dokładnym opublikowanym playbookiem restart/failover/rollback dla LLM-agentów.
- Monitoring/healthcheck jest opisany narzędziowo, ale mało jest opisów SRE-style dla agent teams.

### Klaster 6: Hierarchia i skalowanie managerów

**Odkryte projekty/frameworki:**
- [AutoGen / Group Chat + nested teams](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/group-chat.html) — group chat może być zagnieżdżany; to początek manager-of-managers przez kompozycję zespołów. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [OWL / Workforce](https://openreview.net/forum?id=MBJ46gd1CT) — Planner → Coordinator → Workers to jawna, modularna hierarchia z rozdziałem strategii i domenowej egzekucji. — siła dowodu: **empiryczne** — relevance: **wysoka**
- [StackPlanner](https://arxiv.org/abs/2601.05890) — scentralizowana hierarchia wzbogacona o task memory i experience memory; ważny trop dla bottlenecków centralnego managera. — siła dowodu: **empiryczne** — relevance: **wysoka**
- [Google ADK / Multi-agent](https://google.github.io/adk-docs/agents/multi-agents/) — hierarchia parent/child jest elementem modelu frameworka; sub-agenci, workflow agents i custom agents można kompozycjonować. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [ADK / Agent-as-a-Tool](https://google.github.io/adk-docs/tools-custom/function-tools/) — manager może delegować bez oddawania pełnej kontroli, co jest wzorcem ograniczania bottlenecków przez silniejsze lokalne autonomy workerów. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [A2A Protocol](https://a2a-protocol.org/latest/) — umożliwia składanie agentów z różnych frameworków i dostawców; istotne dla manager-of-managers poza jednym runtime’em. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [MetaGPT](https://docs.deepwisdom.ai/main/en/guide/get_started/introduction.html) — role firmy software’owej i SOP-y sugerują hierarchię organizacyjną, nie tylko techniczną. — siła dowodu: **praktyczne** — relevance: **wysoka**
- [MAGIS](https://openreview.net/forum?id=qevq3FZ63J&referrer=%5Bthe+profile+of+Wenqiang+Zhang%5D%28%2Fprofile%3Fid%3D~Wenqiang_Zhang1%29) — 4-role hierarchy z managerem centralnym; przydatne jako empiryczny punkt odniesienia dla małej hierarchii specjalistów. — siła dowodu: **empiryczne** — relevance: **wysoka**
- [Anthropic: multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — lead agent + parallel subagents; wskazuje, że przy większej skali bezpośredni synchronous fan-out może stać się bottleneckiem. — siła dowodu: **praktyczne** — relevance: **wysoka**

**Kluczowe koncepcje/wzorce:**
- **Manager-of-managers** — hierarchia nie musi kończyć się na jednym managerze; zespoły mogą być komponowane i delegowane dalej. — źródła: AutoGen nested groups, A2A, ADK hierarchies — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Strategic center, operational edges** — centralny planner ustala kierunek, ale execution jest rozproszone u workerów/subagentów. — źródła: Workforce/OWL, StackPlanner, Anthropic research system — siła dowodu: **empiryczne** — relevance: **wysoka**
- **Delegation without full transfer** — manager może zlecić podzadanie bez utraty własnej odpowiedzialności za całość; ważny mechanizm skalowania. — źródła: ADK AgentTool, OpenAI Agents-as-tools, CrewAI hierarchical — siła dowodu: **praktyczne** — relevance: **wysoka**
- **Central bottleneck mitigation by memory and protocol** — gdy manager staje się bottleneckiem, rozwiązaniem bywa silniejsza pamięć, lepszy routing lub delegacja do zdalnych agentów zamiast jednego wspólnego kontekstu. — źródła: StackPlanner, A2A, Anthropic context engineering — siła dowodu: **empiryczne/praktyczne**
- **Hierarchia organizacyjna vs hierarchia runtime** — role typu PM/Architect/Developer nie muszą mapować 1:1 na warstwę wykonawczą; część „hierarchii” może być promptowa, część infrastrukturalna. — źródła: MetaGPT, ADK, LangGraph/OpenAI orchestration — siła dowodu: **praktyczne** — relevance: **wysoka**

**Wątki do głębszego zbadania (Faza 2):**
- Kiedy centralny manager przestaje skalować i trzeba przejść do manager-of-managers? — brak jasnych progów, dużo intuicji, mało danych.
- Jakie granice delegacji działają najlepiej: domena, budżet, geografia, horyzont czasowy, ownership narzędzi? — eksploracja ujawniła kilka osi, ale nie ranking.
- Jak projektować approval gates i limity budżetu w hierarchii wielopoziomowej? — ważne dla kontroli ryzyka i konfliktów kompetencyjnych.

**Luki:**
- Nie udało się znaleźć wielu empirycznych badań porównujących jedno-poziomowe i wielopoziomowe hierarchie na tych samych taskach.
- Manager-of-managers jest częściej sugerowany przez architekturę frameworka niż dokładnie opisany jako wzorzec operacyjny.

## Mapa Fazy 2 — priorytetyzowana

1. **Porównanie manager-as-agent vs manager-as-runtime** — najbardziej fundamentalny podział; wpływa na pamięć, obserwowalność, failure modes i granice odpowiedzialności.
2. **Wzorce handoff między długimi sesjami** — checkpointy, session rotation, structured summaries, filesystem/state handoff; kluczowe dla agentów długowiecznych.
3. **Scheduler/autonomia managera** — planner/coordinator/worker, ledger loops, stuck detection, repriorytetyzacja, approval gates.
4. **Token budgeting i capacity planning dla wielu agentów** — limity organizacyjne, throttling, cache, per-agent budgets, fairness i burst handling.
5. **Always-on runtime patterns** — durable queues, retries, cron, idle policies, health checks, crash recovery, deploy continuity.
6. **Hierarchie i bottlenecki** — kiedy przechodzić do manager-of-managers, jak dzielić zakres odpowiedzialności, jak minimalizować centralny punkt awarii.
7. **Format komunikacji między agentami** — shared thread vs isolated context vs event bus vs protocol (A2A) vs artifacts/shared state.
8. **Empiryczne benchmarki architektur multi-agent** — które prace realnie porównują style orkiestracji, a które tylko prezentują pojedynczy system.

## Otwarte pytania / luki w wiedzy

- Nie udało się potwierdzić dojrzałej, wspólnej nomenklatury dla manager/supervisor/coordinator/orchestrator/planner/scheduler/dispatcher.
- Nie udało się znaleźć szeroko przyjętego publicznego benchmarku dla autonomicznej priorytetyzacji i schedulingu w systemach multi-agent LLM.
- Słabo opisane publicznie pozostają: ROI per agent/task, multi-agent token scheduling pod wspólnym limitem, i polityki fairness między agentami.
- Niewiele źródeł opisuje produkcyjny failover/restart/playbook dla agentów 24/7 z tool use i skutkami ubocznymi.
- Mało porównań empirycznych między: shared-thread orchestration, isolated subagents, workflow graphs i protocol-based remote agents.
- Wiele frameworków deklaruje „human-in-the-loop”, ale mniej źródeł precyzuje skalę autonomii, approval gates i mechanizmy graceful degradation.

## Źródła / odniesienia

- [LangChain: Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent) — bazowa dokumentacja patternów multi-agent i granic kontekstu; użyte do mapowania supervisor vs tool-calling.
- [LangChain: Build a personal assistant with subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant) — konkretny przykład supervisor pattern z centralnym agentem.
- [LangGraph: Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — checkpointing, thready i fault tolerance; kluczowe dla długich przebiegów i resume.
- [LangSmith: Core capabilities](https://docs.langchain.com/langsmith/core-capabilities) — background runs, cron, retries i durable execution; użyte do klastra always-on.
- [CrewAI: Hierarchical Process](https://docs.crewai.com/en/learn/hierarchical-process) — opis managera w strukturze hierarchicznej.
- [CrewAI: Custom Manager Agent](https://docs.crewai.com/en/learn/custom-manager-agent) — pokazuje managera jako pełnoprawnego agenta.
- [CrewAI: Processes](https://docs.crewai.com/en/concepts/processes) — sekwencyjne i hierarchiczne wykonanie z managerem.
- [CrewAI: Crews](https://docs.crewai.com/en/concepts/crews) — pamięć, cache, planning, callbacks, `max_rpm`; użyte do budżetu i długich runów.
- [AutoGen: Group Chat](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/design-patterns/group-chat.html) — wspólny wątek wiadomości i selector/manager wzorca grupowego.
- [AutoGen: Agent and Agent Runtime](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/framework/agent-and-agent-runtime.html) — runtime jako warstwa zarządzania lifecycle’em i komunikacją.
- [AutoGen: Core](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/index.html) — event-driven, distributed, resilient agent systems; użyte jako tło dla always-on/runtime.
- [AutoGen: Magentic-One docs](https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/magentic-one.html) — praktyczny opis Orchestratora i roli wyspecjalizowanych agentów.
- [Magentic-One paper](https://arxiv.org/abs/2411.04468) — kluczowe źródło empiryczne o Orchestratorze, ledgerach i recovery loops.
- [Google ADK: Multi-agent systems](https://google.github.io/adk-docs/agents/multi-agents/) — parent/child hierarchie, subagenci, workflow agents.
- [Google ADK: Agent-as-a-Tool](https://google.github.io/adk-docs/tools-custom/function-tools/) — delegacja bez pełnego oddania kontroli.
- [Google Cloud blog: Building Collaborative AI with ADK](https://cloud.google.com/blog/topics/developers-practitioners/building-collaborative-ai-a-developers-guide-to-multi-agent-systems-with-adk) — zwięzła taksonomia agentów LLM/workflow/custom.
- [A2A Protocol](https://a2a-protocol.org/latest/) — agent interoperability i delegacja ponad frameworkami.
- [OpenAI Agents SDK: Agent orchestration](https://openai.github.io/openai-agents-python/multi_agent/) — LLM-driven vs code-driven orchestration.
- [OpenAI Agents SDK: Handoffs](https://openai.github.io/openai-agents-python/handoffs/) — przekazywanie odpowiedzialności między agentami.
- [OpenAI Agents SDK: Tracing](https://openai.github.io/openai-agents-python/tracing/) — observability dla handoffów, narzędzi i przebiegów.
- [OpenAI Agents SDK: Sessions](https://openai.github.io/openai-agents-python/sessions/) — pamięć sesji jako prymityw.
- [MetaGPT: Introduction](https://docs.deepwisdom.ai/main/en/guide/get_started/introduction.html) — role organizacyjne i SOP-y zespołu LLM.
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — case study lead agenta, parallel subagents i problemów operacyjnych.
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — compaction, context rot, note-taking i multi-agent jako strategie dla długich zadań.
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — nowsze praktyki dla agentów pracujących przez wiele context windows.
- [Claude Code Docs: Manage costs effectively](https://docs.anthropic.com/en/docs/claude-code/costs) — token budgeting, subagenci, compaction, teams cost.
- [Claude Code Docs: Hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) — reiniekcja kontekstu po compaction i hooki lifecycle.
- [Claude Code Docs: Common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows) — resume, session management i scheduled usage.
- [Claude Code Docs: Remote Control](https://docs.anthropic.com/en/docs/claude-code/remote-control) — ograniczenia i zachowanie długich lokalnych sesji.
- [Anthropic API: Rate limits](https://docs.anthropic.com/en/api/rate-limits) — input/output token limits i capacity planning.
- [Anthropic API: Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — cache jako mechanizm kosztowy i wydajnościowy.
- [Anthropic API: Claude Code Analytics API](https://docs.anthropic.com/en/api/claude-code-analytics-api) — usage analytics do monitoringu kosztów.
- [Amazon Bedrock AgentCore Runtime: long running agents](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html) — async tasks, lifecycle i health states.
- [MAGIS](https://openreview.net/forum?id=qevq3FZ63J&referrer=%5Bthe+profile+of+Wenqiang+Zhang%5D%28%2Fprofile%3Fid%3D~Wenqiang_Zhang1%29) — empiryczny framework z rolą Managera na SWE-bench.
- [OWL / Workforce](https://openreview.net/forum?id=MBJ46gd1CT) — planner/coordinator/workers i wyniki na GAIA; kluczowe dla schedulingu i hierarchii.
- [StackPlanner](https://arxiv.org/abs/2601.05890) — centralna hierarchia z task memory i experience memory; ważne dla długiego horyzontu i bottlenecków managera.
