# Research: Software Architect role for AI agents
Data: 2026-03-21

## TL;DR — 3-5 najbardziej obiecujących kierunków

1. **Architekt jako agent planująco-gubernujący, nie „coder of record”**  
   W publicznych wzorcach „architect” najczęściej projektuje strukturę systemu, analizuje trade-offy, pilnuje zasad i ocenia zgodność z architekturą, a nie wykonuje główną implementację. Częsty wzorzec to **read-only architect / reviewer** oraz osobny implementer lub optimizer do wprowadzania zmian. [S10] [S11] [S19] [S20] [S21]

2. **Prompty architekta mają zwykle stały „szkielet”**  
   Najczęstsze sekcje to: rola i misja, analiza stanu obecnego, wymagania funkcjonalne i niefunkcjonalne, propozycja projektu, trade-off analysis, zasady architektoniczne, checklista oraz format decyzji / ADR. W praktyce wiele frameworków nie daje „oficjalnego promptu architekta”, ale daje prymitywy do zbudowania takiej roli. [S4] [S6] [S7] [S10] [S15] [S20] [S21]

3. **Granica Developer vs Architect przebiega po „blast radius” decyzji**  
   Z zebranych wzorców wynika, że do Architekta trafiają decyzje przekrojowe: granice komponentów/usług, interfejsy, modele danych, NFR-y, poważne refaktoryzacje i decyzje trudne do odwrócenia. Developer zostaje właścicielem implementacji w zatwierdzonych ramach, lokalnych refaktorów, testów i zmian o małym zasięgu. To jest głównie **synteza praktyk**, nie sztywna norma branżowa. [S3] [S4] [S5] [S22] [S27] [S28]

4. **AI code review działa najlepiej jako pipeline: diff/context → structured findings → weryfikacja → ewentualny handoff do implementera**  
   Najmocniejsze publiczne wzorce to: analiza różnicy i zmienionych plików, pełniejszy kontekst repo/PR, feedback z priorytetami lub severity, oraz rozdzielenie review od implementacji poprawek. [S10] [S11] [S13] [S14] [S19]

5. **ADR-y są naturalnym outputem roli Architect**  
   W materiałach o architekturze i w repozytoriach z agentami ADR pojawia się jako lekki, repozytoryjny zapis: **Context / Decision / Consequences** plus często status, opcje rozważane i trade-offy. Często to właśnie Architekt tworzy lub syntetyzuje ADR, a Developer wdraża decyzję. [S17] [S21] [S23] [S24] [S25] [S26]

## 1. Terminologia i słownictwo

### Najczęstsze czasowniki i frazy w promptach architekta

W publicznych promptach i specyfikacjach dla agentów architektonicznych dominują słowa: **design, evaluate, propose, review, analyze, recommend, document, align, identify, plan, assess, validate**. W praktyce te czasowniki grupują się w 4 klastry:

- **Projektowanie**: design system architecture, component responsibilities, service boundaries, API contracts, data models, integration patterns. [S15] [S20] [S21]
- **Ocena**: evaluate technical trade-offs, assess scalability limitations, review architecture alignment, identify bottlenecks, inspect technical debt. [S20] [S21]
- **Decyzje**: choose patterns, compare alternatives, justify rationale, record decisions, prefer reversible decisions, make ADRs. [S17] [S21] [S23] [S24]
- **Ewolucja systemu**: propose refactoring, plan future growth, evolution strategy, recalibration, consistency across codebase. [S17] [S20] [S21]

W promptach architektonicznych regularnie pojawiają się też pojęcia „**trade-offs**”, „**architectural principles**”, „**quality attributes**”, „**bounded contexts**”, „**decision records**”, „**failure modes**”, „**constraints**”, „**integration points**”, „**consistency**”, „**scalability**”, „**maintainability**”, „**observability**”, „**reversibility**”. [S17] [S20] [S21]

### Typowe sekcje promptów architektonicznych

Najczęściej powtarzający się układ promptu lub profilu agenta:

1. **Identity / Role** — kim jest agent i z jakiego typu decyzjami pracuje. [S6] [S10] [S15] [S20] [S21]  
2. **Mission / Responsibilities** — co ma robić: projektować, oceniać, porównywać opcje, dokumentować decyzje. [S15] [S20] [S21]  
3. **Current State Analysis** — analiza istniejącej architektury, konwencji, długu technicznego. [S20]  
4. **Requirements** — funkcjonalne i niefunkcjonalne wymagania, integracje, przepływy danych. [S20]  
5. **Design Proposal** — komponenty, granice, interfejsy, modele danych, wzorce integracji. [S20] [S21]  
6. **Trade-off Analysis** — plusy, minusy, alternatywy, finalna decyzja i rationale. [S20] [S21] [S24]  
7. **Principles / Rules** — np. separation of concerns, high cohesion / low coupling, domain first, reversibility matters, no architecture astronautics. [S20] [S21]  
8. **Output contract** — checklista, plan, ADR, structured feedback, severity levels. [S10] [S15] [S19] [S20] [S21]

### Język odróżniający „architect” od „developer”

W praktyce promptowej różnica nie polega tylko na seniority, ale na typie odpowiedzialności:

- **Architect**: „design”, „evaluate”, „review alignment”, „recommend patterns”, „document ADRs”, „analyze implications”, „plan evolution”. [S17] [S20] [S21]
- **Developer / Implementer**: „implement”, „fix”, „write tests”, „scaffold”, „apply changes”, „make tests pass”. [S3] [S10] [S15] [S29]

Ciekawe jest to, że oficjalne materiały OpenAI, Anthropic, LangChain i CrewAI częściej opisują **mechanikę specjalizacji agentów** niż gotową, kanoniczną personę „Software Architect”. Oznacza to, że w ekosystemie praktycznym bardziej utrwalił się **wzorzec budowania roli** niż jeden standard promptu. [S1] [S4] [S6] [S10] [S15]

Siła dowodów: **praktyczne**

## 2. Gotowe prompty — wzorce

### Co istnieje publicznie

Nie widać jednego dominującego „oficjalnego” promptu Software Architect od OpenAI lub Anthropic. Oficjalne dokumentacje dają raczej **ramy**: subagent z własnym promptem, profile agentów, role-goal-backstory, handoffy, narzędzia, ograniczenia uprawnień. [S4] [S6] [S10] [S15]

Najbardziej użyteczne publiczne wzorce pochodzą z:

- dokumentacji narzędzi agentowych (Anthropic, GitHub Copilot, CrewAI, LangChain), [S4] [S6] [S10] [S15]
- repozytoriów z gotowymi agentami / promptami architektonicznymi, [S17] [S18] [S19] [S20] [S21] [S22]
- repozytoriów opisujących workflow wieloagentowy dla software delivery. [S27] [S28] [S29]

### Wzorce promptów / profili agentów

#### A. Anthropic / Claude Code: subagent jako wyspecjalizowany worker

Claude Code dokumentuje subagentów jako osobne konteksty z własnym system promptem, tool access i permissions. Oficjalny przykład `code-reviewer` pokazuje strukturę YAML frontmatter + prompt i bardzo wyraźne ograniczenie odpowiedzialności. [S10]

Co istotne dla roli Architect:
- można zbudować agenta z **izolowanym kontekstem**,
- można narzucić **tylko odczyt** albo bardzo wąski zestaw narzędzi,
- można łańcuchować agentów, np. reviewer → optimizer. [S10]

To jest silny wzorzec dla Architekta jako **review / governance / design** zamiast implementera. [S10]

#### B. GitHub Copilot: custom agent profiles

GitHub pozwala definiować custom agent profile jako pliki Markdown z frontmatterem opisującym **name, description, tools, model, prompt**. Oficjalny przykład `implementation-planner` jest bliski roli architektonicznej: ma tworzyć techniczne specyfikacje, architekturę, plany wdrożenia i dokumentację, „focus on creating thorough documentation rather than implementing code”. [S15]

To ważny sygnał praktyczny: w jednym z dużych ekosystemów agentowych „planowanie” i „architektura” są formalnie modelowane jako **oddzielny agent od implementera**. [S15]

#### C. CrewAI: role-goal-backstory

CrewAI nie daje gotowego „architect” promptu, ale bardzo mocno normalizuje wzorzec:
- `role`
- `goal`
- `backstory`
- ewentualnie `allow_delegation`
- osobno dobrze zdefiniowane taski i expected output. [S6] [S7] [S8]

To praktycznie zachęca do zbudowania Architekta jako agenta, którego „osobowość robocza” jest oddzielona od wykonawcy. CrewAI jednocześnie podkreśla, że task design bywa ważniejszy od samej persony agenta. [S7]

#### D. Publiczne repozytoria z promptami architekta

Najciekawsze konkretne przykłady:

- **everything-claude-code / architect.md** — sekcje: role, architecture review process, requirements, design proposal, trade-off analysis, principles, ADR, checklista system design. [S20]
- **agency-agents / Software Architect Agent** — język DDD, bounded contexts, trade-off matrices, ADR, evolution strategy, „no architecture astronautics”, „reversibility matters”. [S21]
- **spring-ai-agent-utils** — „Plan” jako software architect agent od implementation plans i trade-offs; obok osobny read-only `code-reviewer`. [S19]
- **mitsuhiko/agent-prompts** — `software_architect_agent` jako entrypoint do całego pipeline’u PoC engineering. [S18]
- **codenamev/ai-software-architect** — pełny framework: create ADR, architecture review, specialist review, architecture status, principles, reviews, recalibration. [S17]
- **Gaia** — jawny podział własności artefaktów: `docs/` jako architect-owned, `src/` i `tests/` jako developer-owned. [S22]

### Wniosek z porównania wzorców

W praktyce najczęściej spotykany prompt Architect:
- **nie jest promptem „napisz kod”**, tylko promptem „zaproponuj strukturę, oceń opcje, zapisz decyzję, sprawdź zgodność i wskaż konsekwencje”. [S15] [S17] [S20] [S21]
- często zawiera **sekcję trade-offs**, **sekcję ADR**, oraz **sekcję zasad**. [S17] [S20] [S21]
- częściej ma narzędzia typu **Read / Search / Grep / Glob**, rzadziej pełne uprawnienia do edycji. [S10] [S19] [S20]

Siła dowodów: **praktyczne**

## 3. Responsibility boundaries — Developer vs Architect

### Co wynika bezpośrednio ze źródeł

OpenAI zaleca najpierw maksymalizować możliwości pojedynczego agenta, a dopiero potem rozbijać system na wiele ról, gdy pojawia się złożona logika lub „tool overload”. To sugeruje, że rozdział ról powinien wynikać z **realnych triggerów decyzyjnych**, nie z chęci odtworzenia org chart. [S1] [S2]

LangChain opisuje subagentów jako wzorzec z centralnym koordynatorem i dobrze dobranymi nazwami/opisami agentów. Nazwy i opisy agentów są „prompting levers”, które mają mówić kiedy delegować. [S5]  
CrewAI pokazuje z kolei, że koordynatorzy mogą mieć `allow_delegation=True`, a wyspecjalizowani wykonawcy często sensownie działają z `allow_delegation=False`, żeby uniknąć pętli i rozmycia odpowiedzialności. [S8]

OpenAI w przewodniku dla zespołów AI-native rozdziela warstwy odpowiedzialności: agent może zrobić first pass feasibility / architectural analysis, ale zespół zachowuje własność decyzji architektonicznych. [S3]

### Syntetyczne granice odpowiedzialności (na podstawie praktyk)

Poniżej **synteza** z promptów, dokumentacji i repozytoriów:

| Typ decyzji | Bardziej Developer | Bardziej Architect | Uwagi |
|---|---|---|---|
| Implementacja funkcji w istniejącym module | ✅ |  | jeśli nie zmienia kontraktów i wzorców |
| Lokalny refactor w obrębie komponentu | ✅ |  | o ile nie zmienia granic modułów |
| Testy, fixy, plumbing, scaffolding | ✅ |  | typowy execution loop |
| Zmiana API contracts / event contracts |  | ✅ | wpływ przekrojowy |
| Zmiana modelu danych / integracji |  | ✅ | zwykle ADR-worthy |
| Nowy wzorzec architektoniczny (np. event-driven, CQRS) |  | ✅ | decyzja o dużym blast radius |
| Skalowalność, bezpieczeństwo, niezawodność, observability |  | ✅ | NFR-y to typowy zakres Architect |
| Zgodność kodu z architekturą docelową |  | ✅ | review / governance |
| Dobór biblioteki lokalnej pomocniczej | często ✅ | czasem ✅ | zależy od wpływu architektonicznego |
| Struktura folderów repo | małe zmiany: ✅ | duży reorg: ✅ | zwykle zależy od skali |

### Decision triggers — kiedy Developer powinien eskalować do Architekta

Najbardziej spójne triggery, które przewijają się pośrednio lub bezpośrednio w źródłach:

1. **Zmiana przecina wiele modułów / bounded contexts / usług**. [S5] [S20] [S21]  
2. **Decyzja dotyczy NFR-ów**: performance, security, scalability, reliability, observability. [S20] [S21]  
3. **Trzeba wybrać lub zmienić wzorzec systemowy**: modular monolith vs microservices, event-driven, CQRS itd. [S20] [S21]  
4. **Pojawia się decyzja trudna do odwrócenia lub kosztowna operacyjnie**, więc warto ją zapisać w ADR. [S21] [S23] [S26]  
5. **Implementacja zaczyna rozmijać się z zasadami / dokumentacją architektoniczną**. [S11] [S17]  
6. **Potrzebny jest trade-off, a nie tylko „najlepsza praktyka”**. [S20] [S21]

### Jak praktycznie rozgranicza się „architectural decision” vs „implementation detail”

W publicznych materiałach nie ma jednej formalnej definicji, ale mocno powtarza się heurystyka:

- **Architectural decision** = decyzja o znaczącym wpływie na strukturę systemu, kontrakty, jakość systemu, ewolucję i koszty zmiany. [S23] [S24] [S26]
- **Implementation detail** = sposób zrealizowania zaakceptowanej decyzji w ramach już ustalonych granic. [S3] [S15] [S22]

To rozróżnienie nie jest „prawem branżowym”, tylko praktyczną granicą wynikającą z dokumentacji i promptów. W małych zespołach ta granica bywa bardziej płynna; w systemach wieloagentowych jest zwykle opłacalne, by była bardziej jawna. [S1] [S5] [S8] [S28]

Siła dowodów: **praktyczne**

## 4. Code review workflows dla AI agents

### Co sprawdzać — checklisty

Najsilniej powtarzające się elementy checklisty review:

- **poprawność funkcjonalna** i czy zmiana rozwiązuje właściwy problem, [S14]
- **zgodność z kontekstem i architekturą projektu**, [S14]
- **czytelność i maintainability**, naming, duplication, code clarity, [S10] [S19]
- **error handling**, input validation, edge cases, [S10] [S19]
- **security** (sekrety, podatności, bezpieczne domyślne zachowania), [S10] [S11] [S14]
- **dependencies** i ryzyka zewnętrzne, [S14]
- **test coverage / test adequacy**, [S10] [S11] [S14]
- **performance / regressions**, [S10] [S11] [S19]

GitHub w tutorialu o review AI-generated code podaje prosty porządek: functional checks → context and intent → code quality → dependencies → AI-specific pitfalls → collaborative reviews → automation. [S14]  
Anthropic w przykładowym `code-reviewer` subagencie daje checklistę: readability, naming, duplication, error handling, secrets, input validation, tests, performance. [S10]

### Format outputu

Najczęstsze publiczne formaty feedbacku:

- **severity / priority buckets**: Critical issues / Warnings / Suggestions albo Normal / Nit / Pre-existing. [S10] [S11] [S19]
- **inline comments** na konkretnych liniach PR-a. [S11] [S13]
- **konkretny fix guidance**, a nie tylko opis problemu. [S10] [S13]
- **krótkie rationale / reasoning**, czasem rozwijane dopiero po kliknięciu. [S11]

Claude Code review oznacza findings severity i nie blokuje merge samym review; GitHub Copilot review także nie zostawia approve/request changes, tylko komentarzowy review. To wspólny wzorzec: **AI reviewer doradza, nie jest formalnym gatekeeperem procesu merge**. [S11] [S13]

### Jak agent przekazuje feedback: raport czy bezpośrednia edycja?

Publiczne wzorce rozchodzą się na dwa tryby:

#### 1. Reviewer jest read-only, a naprawy robi osobny agent lub człowiek
To wzorzec bardzo mocny w Anthropic subagents i w przykładach społecznościowych. Reviewer ma ograniczone narzędzia i oddzielny prompt; po review można uruchomić optimizer / implementer. [S10] [S19]

Zalety:
- mniej rozmyta odpowiedzialność,
- łatwiejszy audyt,
- mniejsze ryzyko, że reviewer „naprawi po cichu” problem, którego źle zrozumiał.

#### 2. Reviewer może przekazać sugestię do coding agenta
GitHub Copilot code review potrafi przekazać sugestie do coding agenta i utworzyć kolejny PR z poprawkami. [S13]  
Claude Code review / GitHub Actions również wspiera tryby, w których Claude po komentarzu lub wzmiance w issue/PR może implementować zmiany. [S11] [S12]

W praktyce publiczne produkty coraz częściej wspierają oba tryby, ale **read-only review + osobny implementer** jest bardziej czytelnym wzorcem organizacyjnym.

### Czy reviewer powinien mieć dostęp do git history, diff, PR context?

Najsilniejsze dowody są za tym, że reviewer powinien mieć co najmniej:

- **git diff / recent changes**, [S10]
- **PR context** (tytuł, opis, scope zmiany), [S13]
- **repo / full project context**, jeśli to możliwe. [S11] [S13]

Anthropicowy przykład mówi wprost: zacznij od `git diff` i skup się na modified files. [S10]  
GitHub Copilot code review łączy code changes z additional context oraz oferuje full project context gathering. [S13]

Natomiast **pełne git history** nie pojawia się tak jednoznacznie jako standard. Jest raczej opcjonalnym rozszerzeniem, przydatnym w trudnych analizach regresji lub przy zrozumieniu, „dlaczego” coś istnieje, ale nie znalazłem mocnego publicznego konsensusu, że każdy AI reviewer musi je zawsze czytać.

### Dodatkowy wzorzec: review customizowane repo instructions

W praktycznych produktach review da się kierować przez repo files:
- `CLAUDE.md` / `REVIEW.md` w Claude Code, [S11]
- custom instructions w GitHub Copilot code review. [S13] [S16]

To oznacza, że część „review polityki” może żyć poza promptem agenta i być zarządzana jak artefakt repo.

Siła dowodów: **empiryczne / praktyczne**

## 5. Architecture Decision Records (ADR)

### Czy agent architektoniczny powinien dokumentować decyzje jako ADR?

Najkrócej: **tak, to bardzo częsty i dobrze uzasadniony wzorzec**, ale nie ma jednej normy, kto dokładnie „musi” pisać ADR. [S17] [S21] [S23] [S26]

ADR-y są opisywane jako lekkie dokumenty repozytoryjne zapisujące pojedynczą decyzję architektoniczną wraz z rationale, trade-offami i konsekwencjami. [S23] [S24] [S25] [S26]

W praktyce agentowej ADR dobrze pasuje do roli Architect, bo:
- zamyka wynik analizy w trwałym artefakcie,
- oddziela „dlaczego” od samego kodu,
- pomaga później reviewować zgodność implementacji z wcześniejszą decyzją. [S17] [S21] [S26]

### Najczęstsze formaty ADR

#### Minimalny rdzeń (Nygard)
- Title
- Status
- Context
- Decision
- Consequences [S25]

To jest najczęściej spotykany „minimal core”.

#### Rozszerzony wariant (MADR)
MADR podkreśla:
- options considered,
- pros/cons,
- metadata,
- decision makers / confirmation,
- trade-off analysis. [S24]

#### Wariant praktyczny z governance
Martin Fowler opisuje lekkie ADR-y z:
- title,
- status,
- decision,
- context,
- options considered,
- consequences,
- advice. [S26]

To jest szczególnie interesujące dla systemów wieloagentowych, bo „advice” można interpretować jako miejsce na zapis wkładu różnych ról / agentów.

### Czy ADR to output Architekta czy Developer implementuje po decyzji Architekta?

Z zebranych materiałów wynika kilka modeli:

1. **Architect authors / synthesizes ADR; Developer implements**  
   To najczytelniejszy i najczęściej spotykany wzorzec w repozytoriach architektonicznych. [S17] [S21]

2. **AI assistant może wygenerować ADR bezpośrednio**  
   Np. `Create ADR for [topic]` w `ai-software-architect`. [S17]

3. **Developer aktualizuje ADR, jeśli implementacja odkryje nowe constrainty**  
   Taki workflow jest logicznie zgodny z praktykami decision log / ExecPlans, ale publiczne materiały rzadziej opisują go wprost. OpenAI w ExecPlans zaleca zapisywanie decyzji i zmian kursu w Decision Log. [S9]

Najuczciwiej: **nie ma jednego uniwersalnego standardu własności ADR**, ale publiczne praktyki silnie wspierają model „Architect prowadzi decyzję; implementacja może później wymusić rewizję”.

### Pokrewne artefakty architektoniczne

Oprócz samych ADR-ów często pojawiają się:
- principles.md / architectural principles, [S17]
- reviews/ z review architektury, [S17]
- recalibration plans, [S17]
- docs/ i decision logs, [S17] [S23]
- diagramy C4 i contracts / API docs. [S20] [S21]

To sugeruje, że rola Architect w systemie agentowym zwykle nie kończy się na jednym promptcie — częściej ma własny **pakiet artefaktów**.

Siła dowodów: **praktyczne**

## 6. Anti-patterns — czego unikać

### 1. Overlap z Developer / duplikacja ról

Najczęstszy błąd: Architect i Developer mają prawie te same kompetencje i oba agenty robią trochę wszystkiego. Repozytoria z bardziej dojrzałym workflow akcentują **focused role**, **no overlap**, **clear boundaries**, **architect-owned docs vs developer-owned src/tests**. [S22] [S28]

Efekt uboczny overlapu:
- większy chaos decyzyjny,
- trudniejsze handoffy,
- spadek odpowiedzialności za wynik,
- wyższy koszt prompt engineering i ewaluacji.

### 2. Analysis paralysis / zbyt szybkie przejście do multi-agentów

OpenAI wprost ostrzega, że multi-agent architecture wprowadza dodatkową złożoność i nondeterminism, a decyzja o rozbiciu ról powinna wynikać z evals. [S2]  
Również przewodnik OpenAI o budowie agentów zaleca maksymalizować single agent first. [S1]

W kontekście Architekta oznacza to ryzyko „ivory workflow”: osobny architect agent powstaje za wcześnie i generuje koszt koordynacji większy niż wartość.

### 3. Ivory tower syndrome / architecture astronautics

Bardzo charakterystyczny motyw w publicznych promptach architektonicznych:  
- „no architecture astronautics”, [S21]
- „domain first, technology second”, [S21]
- decyzje muszą uzasadniać swój koszt i być odwracalne, [S21]
- review powinno patrzeć na rzeczywisty kod i kontekst, nie tylko na abstrakcyjne diagramy. [S10] [S14]

To mocna wskazówka, że dobry agent Architect ma być **pragmatyczny i constraint-aware**, a nie tylko generować „ładne wzorce”.

### 4. Scope creep — wchodzenie w zadania innych ról

Jeśli Architect zaczyna:
- implementować większość zmian,
- pisać pełne feature’y zamiast projektować,
- robić research domenowy bez celu architektonicznego,
- przejmować QA lub PM,
to rola przestaje być czytelna.

Publiczne systemy przeciwdziałają temu przez:
- ograniczenie narzędzi, [S10] [S19]
- oddzielne profile agentów, [S15]
- jawny workflow / własność artefaktów. [S22] [S29]

### 5. Delegation loops i zbyt dużo back-and-forth

CrewAI dokumentuje wprost problemy:
- agents not collaborating,
- too much back-and-forth,
- delegation loops. [S8]

Rozwiązania:
- lepszy kontekst,
- jaśniejsze role,
- wyraźny hierarchy / manager,
- brak re-delegacji dla niektórych specjalistów. [S8]

To ważne dla Architecta: rola koordynacyjna bez jasnych granic łatwo zamienia się w agent, który stale pyta, ale nic nie zamyka.

### 6. Ukrywanie zasad wyłącznie w promptach

Claude Code i GitHub Copilot pokazują silny trend: reguły review i standards warto trzymać w repo jako `CLAUDE.md`, `REVIEW.md` lub instruction files, nie tylko w „magicznych” promptach. [S11] [S13] [S16]

Anti-pattern: agent „wie”, ale repo tego nie dokumentuje.  
Skutek: wiedza jest nietrwała, trudna do audytu i trudna do przeniesienia między narzędziami.

Siła dowodów: **praktyczne**

## Co nierozwiązane / otwarte pytania

1. **Brak jednego kanonicznego promptu „Software Architect” od głównych vendorów**  
   OpenAI, Anthropic i GitHub dają mechanikę specjalizacji agentów, ale nie publikują jednego referencyjnego promptu architekta, który stałby się standardem. [S1] [S10] [S15]

2. **Mało twardych danych ilościowych o ROI architekta-agent vs planner/reviewer split**  
   Są praktyki i produkty, ale mało publicznych benchmarków pokazujących, kiedy osobny Architect daje lepsze wyniki niż np. Planner + Reviewer. [S2] [S27]

3. **Nie ma konsensusu, gdzie dokładnie przebiega granica przy „średnich” decyzjach**  
   Np. wybór biblioteki, layout repo, naming konwencji. Źródła sugerują zależność od blast radius, ale nie dają jednolitej reguły. To obszar do dalszej polityki wewnętrznej.

4. **Mało publicznych wzorców specyficznie dla ERP / enterprise configuration agents**  
   Większość materiałów dotyczy ogólnego software engineering, code review i multi-agent orchestration, a nie agentów pracujących na konfiguracji ERP jako domenie.

## Źródła / odniesienia

### Oficjalna dokumentacja / vendor docs

- [S1] OpenAI — *A practical guide to building agents*  
  https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/

- [S2] OpenAI — *Evaluation best practices*  
  https://developers.openai.com/api/docs/guides/evaluation-best-practices/

- [S3] OpenAI — *Building an AI-Native Engineering Team – Codex*  
  https://developers.openai.com/codex/guides/build-ai-native-engineering-team/

- [S4] LangChain — *Multi-agent*  
  https://docs.langchain.com/oss/python/langchain/multi-agent

- [S5] LangChain — *Subagents*  
  https://docs.langchain.com/oss/python/langchain/multi-agent/subagents

- [S6] CrewAI — *Customizing Prompts*  
  https://docs.crewai.com/en/guides/advanced/customizing-prompts

- [S7] CrewAI — *Crafting Effective Agents*  
  https://docs.crewai.com/en/guides/agents/crafting-effective-agents

- [S8] CrewAI — *Collaboration*  
  https://docs.crewai.com/en/concepts/collaboration

- [S9] OpenAI Cookbook — *Using PLANS.md for multi-hour problem solving*  
  https://developers.openai.com/cookbook/articles/codex_exec_plans

- [S10] Anthropic / Claude Code — *Create custom subagents*  
  https://code.claude.com/docs/en/sub-agents

- [S11] Anthropic / Claude Code — *Code Review*  
  https://code.claude.com/docs/en/code-review

- [S12] Anthropic / Claude Code — *Common workflows*  
  https://code.claude.com/docs/en/common-workflows

- [S13] GitHub Docs — *About GitHub Copilot code review*  
  https://docs.github.com/en/copilot/concepts/agents/code-review

- [S14] GitHub Docs — *Review AI-generated code*  
  https://docs.github.com/en/copilot/tutorials/review-ai-generated-code

- [S15] GitHub Docs — *Creating custom agents for Copilot coding agent*  
  https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents

- [S16] GitHub Docs — *Using custom instructions to unlock the power of Copilot code review*  
  https://docs.github.com/en/copilot/tutorials/use-custom-instructions

### Repozytoria / community patterns

- [S17] codenamev — *AI Software Architect*  
  https://github.com/codenamev/ai-software-architect

- [S18] mitsuhiko — *agent-prompts*  
  https://github.com/mitsuhiko/agent-prompts

- [S19] spring-ai-community — *spring-ai-agent-utils*  
  https://github.com/spring-ai-community/spring-ai-agent-utils

- [S20] affaan-m — *everything-claude-code / architect.md*  
  https://github.com/affaan-m/everything-claude-code/blob/main/agents/architect.md

- [S21] msitarzewski — *agency-agents / engineering-software-architect.md*  
  https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-software-architect.md

- [S22] frostaura — *Gaia*  
  https://github.com/frostaura/ai.toolkit.gaia

- [S27] niksacdev — *AI Agents in Software Development: Practical Patterns*  
  https://github.com/niksacdev/multi-agent-system/blob/main/docs/agent-based-development.md

- [S28] centricconsulting — *agent-architecture.md*  
  https://github.com/centricconsulting/ai-coding-workshop/blob/main/docs/design/diagrams/agent-architecture.md

- [S29] meta-pytorch — *OpenEnv / CLAUDE.md*  
  https://github.com/meta-pytorch/OpenEnv/blob/main/CLAUDE.md

### ADR / architecture practice

- [S23] ADR GitHub Org — *Architectural Decision Records*  
  https://adr.github.io/

- [S24] ADR GitHub Org — *ADR Templates*  
  https://adr.github.io/adr-templates/

- [S25] joelparkerhenderson — *Decision record template by Michael Nygard*  
  https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md

- [S26] Martin Fowler — *Scaling the Practice of Architecture, Conversationally*  
  https://martinfowler.com/articles/scaling-architecture-conversationally.html
