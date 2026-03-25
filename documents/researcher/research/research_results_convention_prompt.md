# Research: Konwencje pisania promptów ról w systemach multi-agent

Data: 2026-03-25

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 3-5 najważniejszych wniosków

1. **Nie ma jednego uniwersalnego szablonu „promptu roli”.** Wiodące frameworki rozjeżdżają się w tym, czy rola ma być głównie wolnym tekstem (`system_prompt`), czy częścią szerszej specyfikacji agenta (`name`, `description`, `instructions`, `tools`, `model`, routing). Wspólny mianownik to zwykle: **tożsamość/misja, instrukcje operacyjne, polityka użycia narzędzi, format wyjścia oraz granice kompetencji**. — siła dowodów: **praktyczne**

2. **W produkcyjnych systemach prompt roli jest zwykle tylko jednym poziomem specyfikacji.** Dojrzałe ekosystemy rozdzielają: (a) prompt behawioralny, (b) metadane routingu/selekcji agenta, (c) konfigurację narzędzi i modelu, (d) stan/pamięć/kontekst. To sugeruje, że „konwencja promptów ról” powinna być pisana jako część większej konwencji specyfikacji agenta, a nie wyłącznie jako szablon jednego bloku tekstu. — siła dowodów: **praktyczne**

3. **Anthropic promuje strukturę segmentowaną i jawne sterowanie kontekstem bardziej niż „magiczne zdanie systemowe”.** Najmocniej powtarzające się zalecenia to: jasna rola w system prompt, wyraźne rozdzielenie sekcji (np. XML), przykłady jako stabilny sposób sterowania, jawne kryteria sukcesu, jawne instrukcje narzędziowe i ostrożność wobec działań destrukcyjnych. W agentach ciężar przesuwa się z samego promptu na **context engineering**. — siła dowodów: **praktyczne**

4. **Publicznie sformalizowane standardy istnieją, ale głównie w ekosystemie coding agents.** Najmocniejsze przykłady to: **Claude Code subagents**, **GitHub Copilot custom agents** oraz otwarty standard **AGENTS.md**. Nie udało się potwierdzić szeroko przyjętego, publicznego standardu „jak pisać prompty ról” dla ogólnych systemów multi-agent poza domeną agentów kodujących. — siła dowodów: **praktyczne**

5. **Empirycznie udokumentowane failure modes są dość spójne:** spadek skuteczności przy konfliktach instrukcji, zakopaniu reguł w długim kontekście, przeładowaniu promptu guardrailami/banlistami, zbyt długich instrukcjach agentycznych z warunkami i narzędziami oraz rozmyciu granicy „kto wydaje instrukcję”. To oznacza, że dobra konwencja promptów ról musi zarządzać nie tylko treścią, ale też **priorytetem, pozycją, długością i źródłem instrukcji**. — siła dowodów: **empiryczne**

## Wyniki per pytanie

## 1. Struktura promptów ról w frameworkach agentowych

### 1.1 LangChain / LangGraph

- **LangChain nie narzuca jednego szablonu promptu roli.** W `create_agent` system prompt jest de facto polem wolnego tekstu (`system_prompt`) i może być przekazywany statycznie lub dynamicznie przez middleware. Dokumentacja „context engineering” opisuje kontekst modelu szerzej: obejmuje on system prompt, wiadomości, narzędzia, model i format odpowiedzi. — siła dowodów: **praktyczne**

- **W Deep Agents prompt jest kompozycją wielu warstw, nie pojedynczym blokiem.** Dokumentacja pokazuje składanie finalnego promptu z: własnego `system_prompt`, bazowego promptu agenta, promptów pamięci, skills, filesystem, subagentów, middleware i human-in-the-loop. To ważne: w tym ekosystemie „rola” jest emergentnym wynikiem kilku źródeł instrukcji. — siła dowodów: **praktyczne**

- **Wniosek syntetyczny:** w LangChain obowiązkowe są raczej **kanały kontekstowe**, nie konkretne sekcje promptu. W praktyce najbezpieczniejsze sekcje to: rola/cel, polityka narzędzi, format wyjścia i ograniczenia. — siła dowodów: **praktyczne**

### 1.2 CrewAI

- **CrewAI ma najbardziej jawną, „szablonową” konwencję promptu roli:** `role`, `goal`, `backstory`. Dokumentacja przedstawia to jako podstawowy wzorzec definiowania agenta. — siła dowodów: **praktyczne**

- **To nie jest tylko opis persony.** CrewAI automatycznie dokleja instrukcje systemowe związane z użyciem narzędzi i oczekiwanym formatem odpowiedzi, więc aktywny prompt jest szerszy niż trzy pola, które autor widzi. — siła dowodów: **praktyczne**

- **Implikacja:** CrewAI traktuje prompt roli jako kombinację: **kim jesteś / po co jesteś / jaki masz kontekst działania**, a szczegóły operacyjne i tool-use są częściowo standaryzowane przez framework. — siła dowodów: **praktyczne**

### 1.3 AutoGen

- **AutoGen rozdziela tożsamość agenta od jego promptu roboczego.** Wspólne dla agentów są m.in. `name` i `description`; `AssistantAgent` dodaje do tego `system_message`, konfigurację narzędzi, liczbę iteracji tool-use i opcjonalny typ wyjścia. — siła dowodów: **praktyczne**

- **`description` pełni funkcję routingu.** Dokumentacja podkreśla, że opis agenta służy także innym agentom/orchestratorowi do wyboru „kogo wywołać dalej”. To jest silny sygnał, że w systemach multi-agent trzeba rozdzielić **prompt wykonawczy** od **opisu selekcyjnego**. — siła dowodów: **praktyczne**

- **Implikacja:** w AutoGen sensowna konwencja roli ma co najmniej dwa poziomy: (1) opis do selekcji/routingu, (2) system message do zachowania podczas wykonania. — siła dowodów: **praktyczne**

### 1.4 Semantic Kernel

- **Semantic Kernel formalizuje rolę przez `name` + `instructions`, a w wersji deklaratywnej także `description`, narzędzia i parametry modelu.** Dokumentacja `ChatCompletionAgent` oraz YAML-owa specyfikacja agentów pokazują, że „prompt roli” jest częścią deklaratywnego obiektu agenta. — siła dowodów: **praktyczne**

- **Silny nacisk pada na audytowalność i reproducibility.** Deklaratywna specyfikacja pozwala przechowywać instrukcje, opisy i narzędzia w jednym dokumencie, co przypomina bardziej kontrakt konfiguracyjny niż luźny prompt. — siła dowodów: **praktyczne**

### 1.5 Co jest wspólne między frameworkami?

Najstabilniejsze, powtarzające się sekcje/warstwy to:

1. **Identity / Mission** — kim jest agent i za co odpowiada  
2. **Scope / Boundaries** — co wolno, czego nie wolno, kiedy eskalować lub przekazać dalej  
3. **Procedure / Workflow** — jak ma pracować krok po kroku  
4. **Tool Policy** — jakie narzędzia ma do dyspozycji, kiedy ich używać, kiedy nie  
5. **Output Contract** — format odpowiedzi, poziom szczegółowości, artefakty  
6. **Routing Metadata** — opis do selekcji agenta przez orchestrator  
7. **State / Memory Assumptions** — jaka pamięć/stany są dostępne, co trzeba aktualizować  

To jest **synteza z wielu źródeł**, nie pojedyncza deklaracja jednego frameworka. — siła dowodów: **praktyczne**

### 1.6 Trade-offy i alternatywy

- **Free-form prompt (LangChain)** daje elastyczność, ale utrudnia audyt, porównywanie ról i automatyczne lintowanie. — siła dowodów: **praktyczne**
- **Triada rola-cel-backstory (CrewAI)** jest łatwa do standaryzacji, ale „backstory” nie jest powszechnie uznawane za obowiązkowe; inne frameworki radzą sobie bez niego. — siła dowodów: **praktyczne**
- **Specyfikacja agenta jako YAML/frontmatter + body (Semantic Kernel, GitHub, Claude Code)** jest bardziej audytowalna i nadaje się do review, ale rozdziela logikę na więcej pól i wymaga dyscypliny konfiguracji. — siła dowodów: **praktyczne**
- **Oddzielenie promptu wykonawczego od opisu routingu** poprawia dobór agenta, ale tworzy ryzyko driftu między „tym, jak agent jest reklamowany” a „tym, jak naprawdę działa”. — siła dowodów: **spekulacja**

## 2. Best practices Anthropic dla promptów systemowych

### 2.1 Co da się potwierdzić w publicznych materiałach Anthropic?

- **Anthropic konsekwentnie rekomenduje jasność i bezpośredniość instrukcji.** Model należy traktować jak „błyskotliwego nowego pracownika”, któremu trzeba jasno rozpisać zadanie, oczekiwany wynik i kryteria jakości. — siła dowodów: **praktyczne**

- **Rekomenduje segmentowanie promptu tagami XML.** Oficjalne guide’y sugerują oddzielanie instrukcji, kontekstu, przykładów i danych wejściowych znacznikami oraz utrzymywanie czytelnej hierarchii sekcji. — siła dowodów: **praktyczne**

- **Rekomenduje jawne nadanie roli w system prompt.** To jest wprost opisane jako skuteczny sposób ustawiania zachowania modelu. — siła dowodów: **praktyczne**

- **Rekomenduje przykłady jako jeden z najbardziej niezawodnych sposobów sterowania.** Guide’y sugerują zwykle 3–5 dobrze dobranych przykładów i konsekwentne ich opakowanie w osobne sekcje. — siła dowodów: **praktyczne**

- **Dla narzędzi i agentów Anthropic zaleca jawne instrukcje operacyjne zamiast ukrytych domysłów.** Dokumentacja pokazuje, że trzeba wprost opisać kiedy używać narzędzi, kiedy pytać o zgodę i jakie działania traktować jako ryzykowne lub destrukcyjne. — siła dowodów: **praktyczne**

- **W materiałach agentowych Anthropic centralne staje się „context engineering”.** Ich engineering post podkreśla, że skuteczność agentów zależy nie tylko od treści promptu, ale od całego pakietu kontekstu: instrukcji systemowych, narzędzi, zewnętrznych danych, historii i stanu. — siła dowodów: **praktyczne**

### 2.2 Co wnosi Constitutional AI / Constitution?

- **Constitutional AI daje ważną zasadę projektową: reguły powinny być jawne, tekstowe i krytykowalne.** To nie jest gotowy szablon promptu roli, ale wzmacnia ideę, że ważne normy mają być zapisane explicite, a nie ukryte w domysłach modelu. — siła dowodów: **praktyczne**

- **W konstytucji Claude pojawia się szczególnie ważna zasada dla systemów multi-agent:** wyjścia subagentów, jeśli wracają do orchestratora, powinny być traktowane jako **input konwersacyjny**, a nie jako instrukcje od uprzywilejowanego nadawcy. To jest jedno z najmocniejszych publicznych potwierdzeń, że w architekturze multi-agent trzeba rozróżniać **źródło treści** od **źródła autorytetu**. — siła dowodów: **praktyczne**

### 2.3 Czego nie udało się potwierdzić?

- **Nie udało się potwierdzić publicznego dokumentu Anthropic o randze analogicznej do OpenAI Model Spec, który byłby oficjalnym standardem „jak pisać prompt systemowy” dla API i agentów.** Najbliższe temu są: prompting best practices, Constitution oraz materiały Claude Code / engineering posts. — siła dowodów: **praktyczne**

### 2.4 Trade-offy i alternatywy

- **Silna struktura XML** poprawia czytelność i rozdzielenie sekcji, ale zwiększa długość promptu i może pogarszać saliency przy bardzo rozbudowanych promptach. — siła dowodów: **praktyczne**
- **Przykłady zwiększają sterowalność**, ale nadmiar przykładów może działać jak distractor w długim kontekście. To napięcie ma częściowe wsparcie empiryczne w badaniach o distractorach i pozycji instrukcji, choć nie jest to bezpośrednio zbadane w guide’ach Anthropic. — siła dowodów: **empiryczne + praktyczne**
- **Silne instrukcje autonomii narzędziowej** przyspieszają wykonanie, ale rośnie ryzyko niepożądanych działań, dlatego Anthropic wprost zaleca pytanie o zgodę przy działaniach ryzykownych, destrukcyjnych lub o zewnętrznych skutkach. — siła dowodów: **praktyczne**

## 3. Prompt convention w dużych projektach multi-agent

### 3.1 Claude Code (Anthropic)

- **Claude Code ma jawny, produkcyjny standard definiowania subagentów.** Plik agenta zawiera YAML frontmatter (`name`, `description`, `model`, `tools`, itd.) oraz markdown body, które staje się system promptem. — siła dowodów: **praktyczne**

- **`description` jest traktowane jako pole krytyczne dla routingu.** Oficjalny materiał podkreśla, że to najważniejsze pole dla wyboru właściwego agenta i zaleca opisywać nie tylko kompetencję, ale i sytuacje wywołania, przykłady triggerów i przeciw-przypadki. — siła dowodów: **praktyczne**

- **Anthropic publikuje też wzorce samego system promptu.** W materiałach pomocniczych dla Claude Code pojawia się powtarzalna struktura: rola, odpowiedzialności, proces, standardy jakości, format wyjścia, edge cases. — siła dowodów: **praktyczne**

### 3.2 GitHub Copilot custom agents

- **GitHub sformalizował agent profiles jako pliki markdown z YAML frontmatter.** Dokumentacja opisuje pola typu `name`, `description`, `prompt`, `tools`, opcjonalnie MCP servers. — siła dowodów: **praktyczne**

- **GitHub rozdziela poziom repozytorium i poziom agenta.** `AGENTS.md` / repo instructions służą do instrukcji wspólnych, a `.agent.md` do roli wyspecjalizowanej. To jest istotny wzorzec skalowania: **shared policy + per-agent specialization** zamiast kopiowania wszystkiego do każdej roli. — siła dowodów: **praktyczne**

### 3.3 AGENTS.md jako otwarta konwencja

- **AGENTS.md to realny, publiczny standard między narzędziami.** Strona projektu deklaruje przenośny format instrukcji dla agentów kodujących i opisuje zasady lokalności/preferencji plików bliższych katalogowi roboczemu. — siła dowodów: **praktyczne**

- **To nie jest standard promptów ról sensu stricto, lecz standard środowiskowych instrukcji dla agentów.** Mimo to ma znaczenie dla pytania badawczego, bo pokazuje, że praktyka rynkowa idzie w stronę **jawnych plików konwencji**, reviewowanych jak kod. — siła dowodów: **praktyczne**

### 3.4 Dokumenty pokrewne, ale nie tożsame

- **OpenAI Model Spec** jest ważnym punktem odniesienia dla hierarchii instrukcji (platforma / developer / user) i rozróżnienia źródeł autorytetu, ale nie jest standardem „jak pisać prompt roli” w sensie sekcji promptu. Bardziej przypomina **governance spec** niż style guide promptów ról. — siła dowodów: **praktyczne**

### 3.5 Najmocniejsza synteza

Publiczne standardy, które rzeczywiście da się wskazać, układają się w dwa poziomy:

1. **Agent spec** — `name`, `description`, `tools`, `model`, czasem MCP/plugins  
2. **Role prompt body** — misja, workflow, quality bar, output contract, edge cases  

To nie jest pojedynczy standard branżowy, ale powtarzalny wzorzec w kilku niezależnych ekosystemach. — siła dowodów: **praktyczne**

### 3.6 Trade-offy i alternatywy

- **Plikowa, reviewowalna specyfikacja agenta** ułatwia governance i audyt, ale jest mniej wygodna do szybkich eksperymentów. — siła dowodów: **praktyczne**
- **Repo-wide instructions + per-agent role prompts** skalują się lepiej niż duplikowanie zasad w każdej roli, ale wymagają jasnej polityki precedence. — siła dowodów: **praktyczne**
- **Standard przenośny (AGENTS.md)** poprawia interoperacyjność między narzędziami, ale zwykle ma niższą ekspresywność niż format natywny dla konkretnej platformy. — siła dowodów: **praktyczne**

## 4. Empirycznie udokumentowane anti-patterns

### 4.1 Zakopywanie krytycznych reguł w długim lub odległym kontekście

- **To jest dobrze udokumentowany failure mode.** W IHEval wyniki spadają, gdy ograniczenia formatowania są przeniesione do system message zamiast być przy bieżącym user query, a spadają dalej, gdy między system promptem a bieżącą odpowiedzią pojawia się dodatkowa tura rozmowy. — siła dowodów: **empiryczne**

- **To jest spójne z szerszą literaturą o pozycji informacji.** „Lost in the Middle” pokazuje, że modele lepiej wykorzystują informację z początku i końca długiego kontekstu niż ze środka. — siła dowodów: **empiryczne**

- **Implikacja dla konwencji:** krytycznych reguł nie należy zakładać jako „bezpiecznie zapamiętanych tylko dlatego, że są w system prompt”. Jeśli są kluczowe dla konkretnego kroku, trzeba zadbać o ich saliency lub lokalne przypomnienie. — siła dowodów: **empiryczne + spekulacja**

### 4.2 Sprzeczne instrukcje i słaba internalizacja hierarchii

- **Modele mają wyraźny problem z konfliktami instrukcji.** IHEval pokazuje duże spadki jakości w settingach konfliktowych; dodatkowo zaostrzenie instrukcji konfliktowej pogarsza wyniki. — siła dowodów: **empiryczne**

- **Samo dopisanie „przestrzegaj hierarchii instrukcji” nie wystarcza.** Autorzy IHEval raportują, że dodatkowy prompt wyjaśniający priorytet instrukcji nie daje wyraźnej poprawy, co sugeruje, że problem nie jest trywialnie naprawialny samą treścią promptu. — siła dowodów: **empiryczne**

- **Implikacja:** anti-patternem jest poleganie na niejawnej lub nawet jawnie dopisanej hierarchii bez osobnych mechanizmów kontroli konfliktu. — siła dowodów: **empiryczne + spekulacja**

### 4.3 Przeładowanie promptu guardrailami / banlistami

- **„A Closer Look at System Prompt Robustness” pokazuje, że wiele guardraili naraz szybko degraduje skuteczność.** W tzw. Monkey Island stress test wydajność modeli spada wraz z liczbą guardraili, a autorzy wprost piszą, że zbyt wiele guardraili może przeciążać „working memory” modelu. — siła dowodów: **empiryczne**

- **To jest szczególnie istotne dla style guide’ów promptów ról.** Anti-patternem nie jest samo posiadanie reguł, lecz pakowanie zbyt wielu drobnych zakazów i wyjątków do jednego promptu bez priorytetyzacji. — siła dowodów: **empiryczne + spekulacja**

### 4.4 Zbyt długie instrukcje agentyczne z warunkami i narzędziami

- **AgentIF pokazuje, że agentyczne instruction-following jest kruche zwłaszcza dla constraintów warunkowych i narzędziowych.** Najtrudniejsze są przypadki wymagające poprawnego sprawdzenia warunku, użycia konkretnego narzędzia i poprawnego doboru parametrów. — siła dowodów: **empiryczne**

- **Praktyczna implikacja:** anti-patternem jest scalanie wielu warunków, wyjątków i polityk tool-use w jeden długi blok bez decompozycji albo bez zewnętrznych guardów. — siła dowodów: **empiryczne + spekulacja**

### 4.5 Rozmycie granicy ról / źródeł instrukcji (prompt injection jako role confusion)

- **Nowsze badania opisują prompt injection jako problem „role confusion”.** Modele potrafią traktować treść wyglądającą jak instrukcja jako bardziej uprzywilejowaną, niż powinna być, bo rozpoznają rolę po stylu i treści, a nie po zaufanym źródle. — siła dowodów: **empiryczne**

- **To bezpośrednio uderza w systemy multi-agent.** Jeśli output innego agenta lub narzędzia bywa wstrzykiwany bez oznaczenia i bez boundary handling, model może odczytać go jako instrukcję, a nie dane. — siła dowodów: **empiryczne + praktyczne**

### 4.6 Zakładanie, że feedback i korekty „utrzymają się same” przez wiele tur

- **RefuteBench pokazuje, że modele potrafią stopniowo zapominać feedback i wracać do swojej uprzedniej wiedzy po kilku niezwiązanych turach rozmowy.** — siła dowodów: **empiryczne**

- **Implikacja:** anti-patternem jest wpisanie krytycznej poprawki raz i zakładanie, że będzie równie silna po dalszej rozmowie i delegacjach. — siła dowodów: **empiryczne**

### 4.7 Co było trudne do potwierdzenia

- **Nie udało się znaleźć mocnego, bezpośredniego benchmarku pokazującego „brak confirmation gates” jako osobny failure mode promptu roli.** To zalecenie pojawia się często w dokumentacji praktycznej, ale nie znalazłem równie mocnego, dedykowanego paperu jak dla konfliktów instrukcji czy prompt injection. — siła dowodów: **praktyczne**
- **Nie udało się też potwierdzić jednego uniwersalnego progu długości promptu, po którego przekroczeniu prompt staje się zawodny.** Są wyniki o degradacji przy złożoności i długości, ale brak prostego, przenośnego limitu. — siła dowodów: **empiryczne**

## Otwarte pytania / luki w wiedzy

- **Brak bezpośredniego porównania frameworków** (LangChain vs CrewAI vs AutoGen vs Semantic Kernel) na wspólnym benchmarku jakości promptów ról. Dokumentacja mówi, jak konfigurować agentów, ale nie porównuje skuteczności tych konwencji.
- **Mało publicznych standardów poza coding-agent ecosystems.** Nie udało się potwierdzić szeroko stosowanego, publicznego „prompt style guide for multi-agent roles” w dużych projektach enterprise spoza domeny agentów kodujących.
- **Brak zgody co do tego, czy „backstory” jest elementem obowiązkowym.** CrewAI traktuje je jako element pierwszej klasy; pozostałe frameworki nie.
- **Brak silnego publicznego dokumentu Anthropic o randze analogicznej do OpenAI Model Spec** dla samego projektowania promptów API; trzeba triangulować między prompting guides, Constitution i materiałami Claude Code.
- **Niedostatecznie zbadane są interaction effects** między: długością promptu, liczbą narzędzi, routingiem między agentami i pamięcią stanu.
- **Część zaleceń „best practice” pozostaje praktyczna, nie empiryczna.** Dotyczy to zwłaszcza confirmation gates, dokładnej struktury workflow i sposobu zapisu quality bar.

## Źródła / odniesienia

### Frameworki agentowe

- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents) — oficjalna dokumentacja `create_agent`, `system_prompt`, dynamicznego promptu i podstawowej struktury agenta.
- [LangChain Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart) — użyte do potwierdzenia roli system promptu, praktyk „specific and actionable” oraz tego, że narzędzia stają się częścią kontekstu modelu.
- [LangChain Context Engineering](https://docs.langchain.com/oss/python/langchain/context-engineering) — kluczowe źródło do tezy, że prompt roli jest tylko jednym elementem pełnego kontekstu.
- [LangChain Deep Agents: Context Engineering](https://docs.langchain.com/oss/python/deepagents/context-engineering) — użyte do pokazania kompozytowego promptu składanego z wielu warstw.
- [CrewAI: Crafting Effective Agents](https://docs.crewai.com/en/guides/agents/crafting-effective-agents) — źródło triady `role`, `goal`, `backstory`.
- [CrewAI: Customizing Prompts](https://docs.crewai.com/en/guides/advanced/customizing-prompts) — użyte do potwierdzenia auto-injection instrukcji systemowych i tool-use.
- [AutoGen Agents](https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/tutorial/agents.html) — użyte do rozdzielenia `name`/`description` od `system_message`, narzędzi i output type.
- [Semantic Kernel ChatCompletionAgent](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-types/chat-completion-agent) — użyte do struktury `name` + `instructions` oraz deklaratywnego opisu agenta.

### Anthropic

- [Claude Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — główne źródło publicznych rekomendacji Anthropic: XML tags, role prompting, examples, tool-use, autonomy/safety.
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — ważne dla przesunięcia akcentu z prompt engineering na context engineering.
- [Claude’s Constitution (Jan 2026 PDF)](https://www-cdn.anthropic.com/cffd979fd050fbc0d8874b8c58b24cc10554e208/claudes-constitution_webPDF_26-01.26a.pdf) — użyte do zasady autorytetu/źródeł instrukcji i traktowania outputów subagentów jako conversational input.

### Publiczne standardy / duże projekty

- [Claude Code agent-development SKILL](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/agent-development/SKILL.md?plain=1) — oficjalny, produkcyjny wzorzec plików subagentów i wskazówki routingu.
- [Claude Code system-prompt design patterns](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/agent-development/references/system-prompt-design.md?plain=1) — użyte do sekcji typu responsibilities / process / quality bar / output format / edge cases.
- [GitHub Copilot: About custom agents](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-custom-agents) — formalna struktura custom agents.
- [GitHub Copilot: Creating custom agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents) — szczegóły `.agent.md`, frontmatter i zachowania.
- [AGENTS.md](https://agents.md/) — przykład otwartego, między-narzędziowego standardu instrukcji dla agentów.
- [OpenAI Model Spec (2025-04-11)](https://model-spec.openai.com/2025-04-11.html) — użyte jako dokument pokrewny dla hierarchii instrukcji i źródeł autorytetu; nie jako bezpośredni standard promptów ról.

### Empiryczne anti-patterns / failure modes

- [A Closer Look at System Prompt Robustness](https://arxiv.org/pdf/2502.12197) — kluczowe źródło o przeciążeniu guardrailami, distractorach i zawodności system promptów.
- [IHEval: Evaluating Language Models on Following the Instruction Hierarchy](https://aclanthology.org/2025.naacl-long.425.pdf) — najważniejsze źródło o konfliktach instrukcji, spadku skuteczności przy odległych instrukcjach i ograniczeniach promptowego „uczenia” hierarchii.
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) — źródło do pozycyjnego spadku użyteczności informacji w długim kontekście.
- [Prompt Injection as Role Confusion](https://arxiv.org/html/2603.12277v2) — źródło do tezy, że prompt injection można rozumieć jako błąd rozpoznania roli/źródła instrukcji.
- [AgentIF: Benchmarking Instruction Following of Large Language Models in Agentic Scenarios](https://arxiv.org/html/2505.16944v1) — użyte do failure modes związanych z warunkami, narzędziami i złożonością instrukcji agentycznych.
- [RefuteBench](https://aclanthology.org/2024.findings-acl.818.pdf) — użyte do tezy o zaniku wpływu feedbacku i korekt w kolejnych turach rozmowy.
