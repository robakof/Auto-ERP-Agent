
# Research: Orchestracja workflow dla agentów LLM

```yaml
research_id: workflow_orchestration
requested_by: architect
date: 2026-03-24
base_prompt: 00 RESEARCHER_BASE_PROMPT.md
output_path: documents/researcher/research/workflow_orchestration.md
related_research: workflow_compliance.md
```

## TL;DR

1. **Najbardziej dojrzały wzorzec runtime to: graf wykonania + trwały stan/checkpoint + osobne gate’y walidacyjne.** Tak działają dziś najsilniejsze frameworki orkiestracyjne: LangGraph (graph + checkpoints + interrupts), AutoGen GraphFlow (directed graph execution), CrewAI Flows (event-driven flow + state), Temporal (durable workflow execution z event history). **Siła dowodu: praktyczne / produkcyjne.** [S1][S2][S3][S5][S9]

2. **„Execution graph” i „message graph” to różne rzeczy i nie powinny być zlane w jedno.** AutoGen wprost rozdziela kolejność wykonania od tego, jakie wiadomości trafiają do którego agenta; to bardzo ważne dla incremental loading i kontroli context window. **Siła dowodu: praktyczne.** [S5]

3. **Najlepsza granularność chunkingu to zwykle poziom kroku domenowego, nie fazy i nie pojedynczego tool-calla.** Faza jest zbyt gruba dla walidacji, a micro-step jest zbyt kosztowny i zwiększa ryzyko thrashingu orchestratora. Micro-steps mają sens tylko przy operacjach ryzykownych, nieodwracalnych albo wymagających approval gate. **Siła dowodu: synteza na podstawie frameworków i workflow engine patterns.** [S1][S3][S5][S9][S10]

4. **Walidacja powinna być warstwowa:**  
   - input/contract validation,  
   - output validation,  
   - behavior validation (narzędzia, ścieżka, policy),  
   - quality validation (heurystyki / LLM-as-judge / human gate),  
   - transition validation (czy wolno przejść dalej).  
   **Siła dowodu: praktyczne + częściowo synteza.** [S3][S4][S10][S11][S12]

5. **State machine dla agentów powinna wspierać co najmniej:** sequential, conditional branch, bounded loop, parallel fan-out/fan-in, retry, timeout, pause/resume, final states oraz opcjonalnie history state. Statecharts opisują to czyściej niż płaski FSM, ale prostszy JSON graph bywa lepszy operacyjnie. **Siła dowodu: praktyczne.** [S5][S7][S8][S9]

6. **Rollback w workflow agentowym rzadko powinien oznaczać „cofnięcie stanu modelu”; częściej oznacza retry, compensation albo fork od checkpointu.** Temporal promuje compensating actions / saga, LangGraph promuje replay/fork/checkpoints. **Siła dowodu: praktyczne.** [S1][S6][S9]

7. **Validation-first design jest realnie wykonalny wtedy, gdy exit gate ma postać machine-checkable kontraktu.** Najmocniejsze wzorce pochodzą z typed schemas i osobnych checks (Prefect parameter/input validation, Dagster asset checks). **Siła dowodu: praktyczne.** [S10][S11][S12]

---

## Kontekst i zakres

Ten research odpowiada na brief dotyczący **orchestration runtime** dla workflow agentów LLM: chunking, validation, state, prompt streaming i proven orchestration patterns. Nie dotyczy pisania samych promptów workflow; to zgodnie z briefem należy do osobnego researchu (`workflow_compliance.md`). [BRIEF]

### Metoda
- Priorytet: oficjalna dokumentacja frameworków i workflow engines.
- Źródła wtórne: pojedyncza świeża praca badawcza o statycznej weryfikacji graph workflows.
- Oznaczenia siły dowodu:
  - **Empiryczne** – wyniki badań / benchmarków
  - **Praktyczne** – udokumentowane capability i patterny z dojrzałych narzędzi
  - **Spekulacja / synteza** – wniosek architektoniczny wyprowadzony z kilku źródeł

---

## Q1: Workflow chunking patterns

### Główne ustalenie
Frameworki produkcyjne nie promują „agent dostaje cały workflow”; promują **kawałkowanie wykonania** poprzez graf, subflows, child workflows, checkpoints i filtrowanie kontekstu. [S1][S3][S5][S9][S10]

### Pattern 1: Phase-level chunking
**Definicja:** agent dostaje cały etap (np. „research”, „synthesis”, „publish”), wewnątrz którego sam zarządza lokalnymi sub-krokami.

**Zalety**
- mniej przełączeń orchestratora,
- lepsza ciągłość reasoning,
- mniej narzutu na persistence i validation plumbing.

**Wady**
- słabsza obserwowalność,
- trudniejsze precyzyjne gate’y walidacyjne,
- większe ryzyko „step bleed”, czyli wykonywania zbyt dużo naraz.

**Kiedy działa**
- gdy etap jest względnie stabilny, ma niski risk surface i nie wymaga approval per sub-step.

**Evidence**
- Temporal zaleca zaczynać od pojedynczego workflow / activity decomposition i dopiero później dzielić większe workloady na child workflows. [S9]
- Prefect ostrzega, że zbyt gruby flow powoduje retry „od początku”, więc granularność pomaga dopiero do pewnego punktu. [S10]

### Pattern 2: Step-level chunking
**Definicja:** orchestrator udostępnia agentowi dokładnie jeden krok domenowy, np. `collect_sources`, `draft_summary`, `run_validation`, `publish_result`.

**Zalety**
- najlepsza zgodność z gate’ami walidacyjnymi,
- łatwe mapowanie na `step_id`,
- proste persisted transitions,
- dobre do audit trail i branchingu.

**Wady**
- większa liczba checkpointów i orchestrator transitions,
- potrzeba jawnego przekazywania artefaktów i kompaktowego stanu.

**Kiedy działa**
- jako domyślny pattern dla workflow, który ma być incremental, parseable i validation-gated.

**Evidence**
- LangGraph zapisuje checkpoint przy kolejnych super-steps i pozwala resume od konkretnego miejsca; to naturalnie wspiera krokowe execution boundaries. [S1]
- CrewAI Flows budują krokowość przez `@start` i `@listen`, z centralnym stanem przepływu. [S3]
- AutoGen GraphFlow modeluje agentów jako węzły, a execution flow jako edge’y z warunkami. [S5]

### Pattern 3: Micro-step / tool-step chunking
**Definicja:** osobny chunk per tool call, per I/O side effect lub per approval point.

**Zalety**
- maksymalna kontrola,
- silne behavior validation,
- łatwe human approval przed ryzykownym działaniem.

**Wady**
- wysoki narzut,
- ryzyko thrashingu,
- łatwo zgubić cel domenowy w serii zbyt małych kroków.

**Kiedy działa**
- przy operacjach destrukcyjnych / kosztownych / compliance-sensitive,
- gdy trzeba dokładnie zatwierdzać tool use.

**Evidence**
- CrewAI execution hooks pozwalają blokować lub aprobować konkretne LLM/tool calls. [S4]
- AutoGen intervention handler pokazuje approval dokładnie na poziomie tool execution. [S13]
- LangGraph zaleca separować side effects i dbać o idempotency wokół interrupts/resume. [S2]

### Pattern 4: Nested chunking / subflow chunking
**Definicja:** parent workflow emituje duży krok, ale wykonuje go jako subflow / child workflow / subgraph.

**Zalety**
- dobra równowaga między czytelnością top-level workflow a lokalną złożonością,
- lokalne retry / parallelism / conditional logic w subflow,
- wygodne do reużywalnych bloków.

**Wady**
- większa złożoność operacyjna,
- ryzyko nieczytelnych granic odpowiedzialności.

**Evidence**
- Temporal child workflows służą m.in. do partitioning dużych workloadów i oddzielania event histories. [S9]
- Prefect nested flows mają własny task runner i first-class observability. [S10]
- LangGraph ma subgraphs i checkpoint namespace. [S1]
- AutoGen GraphFlow wspiera cykle, branchingi i activation groups, co naturalnie wspiera zagnieżdżone logiki. [S5]

### Pattern 5: Artifact-first handoff
**Definicja:** między chunkami przekazywany jest przede wszystkim **typed state + artifact references**, a nie pełny transcript.

**Zalety**
- mały context footprint,
- łatwiejsza walidacja,
- lepsza stabilność niż przekazywanie pełnej rozmowy.

**Wady**
- wymaga jawnych schematów danych i storage layer.

**Evidence**
- AutoGen wprost rozdziela execution graph od message graph i pokazuje filtrowanie do ostatniej wiadomości z danego źródła. [S5]
- CrewAI Flow state oraz Prefect flow parameters / nested flow data passing wspierają przekazywanie danych zamiast pełnej historii. [S3][S10]

### Pattern 6: Filtered-context chunking
**Definicja:** agent wykonujący krok dostaje tylko:
- aktualny kontrakt kroku,
- minimalny stan wejściowy,
- wybrane artefakty,
- opcjonalnie mały summary poprzedniego kroku.

**Evidence**
- AutoGen MessageFilterAgent służy dokładnie do ograniczania model context do relewantnych wiadomości; dokumentacja podaje jako korzyści redukcję halucynacji, kontrolę memory load i focus na istotnych informacjach. [S5]

### Trade-off matrix

| Pattern | Context continuity | Validation precision | Runtime overhead | Best use |
|---|---:|---:|---:|---|
| Phase-level | wysoka | niska/średnia | niska | etapy niskiego ryzyka |
| Step-level | średnia | wysoka | średnia | domyślny workflow execution |
| Micro-step | niska | bardzo wysoka | wysoka | narzędzia ryzykowne, approvals |
| Nested subflow | średnia/wysoka | wysoka lokalnie | średnia | złożone reużywalne bloki |
| Artifact-first | średnia | wysoka | niska/średnia | długie workflows, małe context windows |

### Wniosek dla Q1
Najbardziej przenośny pattern to:
1. top-level **step-level chunking**,  
2. opcjonalne **nested subflows** dla kroków złożonych,  
3. **micro-step gates** tylko przy side effects / approvals,  
4. **artifact-first handoff** zamiast transcript-first handoff.  

**Siła dowodu:** praktyczne + synteza. [S1][S3][S5][S9][S10]

---

## Q2: Validation hooks design

### Główne ustalenie
Walidacja w orkiestracji agentów nie jest jednym mechanizmem. Dojrzałe systemy rozdzielają co najmniej:
- **validation of inputs/contracts**,
- **validation of execution behavior**,
- **validation of outputs**,
- **validation of transition eligibility**,
- **human review**, jeśli ocena jakości nie daje się wiarygodnie zautomatyzować. [S2][S4][S10][S11][S12][S13]

### Pattern A: Input / contract validation
Walidacja wejścia zanim krok w ogóle ruszy.

**Przykłady**
- Prefect waliduje parametry flow jeszcze przed przejściem do Running; nieważne parametry kończą run jako Failed bez wejścia w execution. [S10]
- Prefect `RunInput` i Pydantic validators pokazują machine-checkable input validation dla paused/resume workflows. [S11]

**Dobre zastosowania**
- sprawdzenie, czy wymagane artefakty istnieją,
- czy schema inputu jest zgodna,
- czy stan poprzedniego kroku jest kompletny.

### Pattern B: Output validation
Walidacja, czy rezultat kroku istnieje i spełnia formalne kryteria.

**Przykłady**
- Dagster asset checks: pojedynczy check powinien weryfikować jedną własność assetu; wynik może być blocking lub nieblocking. [S12]
- CrewAI before/after hooks pozwalają walidować i sanitizować wyniki tool calls i LLM calls. [S4]

**Machine-checkable criteria**
- plik istnieje,
- schema JSON zgodna,
- liczba rekordów > 0,
- wszystkie required fields obecne,
- referencjonowany artifact ma checksum / version / URI.

### Pattern C: Behavior validation
Walidacja, **jak** agent działał, nie tylko co zwrócił.

**Przykłady**
- CrewAI tool hooks: validate parameters, block dangerous operations, require approval. [S4]
- AutoGen intervention handler: przechwytuje FunctionCall i pyta o zgodę. [S13]

**Zastosowania**
- czy agent użył dozwolonego narzędzia,
- czy nie zrobił side effect bez approval,
- czy nie przekroczył iteracji,
- czy nie opuścił obowiązkowego sub-kroku.

### Pattern D: Quality validation
Walidacja jakości lub przydatności outputu.

**Najczęściej spotykane warianty**
1. **deterministyczne checks** – najlepsze, gdy możliwe,
2. **heuristics / scoring** – np. minimalna liczba źródeł,
3. **LLM judge** – tylko jako miękki gate lub repair signal,
4. **human-in-the-loop** – dla high-stakes i subiektywnej jakości.

**Evidence**
- CrewAI ma zarówno flow-based human feedback (`@human_feedback`), jak i webhook-based HITL dla async review. [S14][S15]
- LangGraph interrupts zapewniają pause/resume dokładnie w miejscu approval gate. [S2]

### Pattern E: Transition validation
Walidacja nie samego kroku, lecz prawa do przejścia do następnego stanu.

To kluczowe rozróżnienie:
- krok może wykonać się poprawnie technicznie,
- ale **workflow nie powinien jeszcze przejść dalej**, jeśli np. quality gate jest tylko częściowo spełniony.

**Najlepsza forma**
- validator zwraca **outcome enum**, np.:
  - `pass`,
  - `pass_with_warnings`,
  - `repair`,
  - `manual_review`,
  - `fail_terminal`.

### Hard gate vs soft gate

#### Hard gate
Blokuje przejście.

Stosować gdy:
- side effect jest nieodwracalny,
- compliance / security,
- missing required artifact,
- schema invalid,
- tool misuse,
- downstream krok nie ma sensu bez wyniku.

#### Soft gate
Pozwala przejść, ale zapisuje warning / debt / confidence flag.

Stosować gdy:
- jakość jest wystarczająca, ale nie idealna,
- problem ma niski koszt,
- istnieje późniejszy krok konsolidujący / naprawczy.

**Analog:** Dagster `blocking=True` vs nieblokujące checks. [S12]

### Partial success handling strategies

#### Strategy 1: Threshold gate
Przykład: 4/5 warunków = pass_with_warnings.

**Plus:** proste.  
**Minus:** bywa arbitralne.

#### Strategy 2: Critical/non-critical split
Każdy warunek ma severity:
- critical -> fail,
- major -> repair,
- minor -> warn.

To zwykle lepsze niż prosty scoring.

#### Strategy 3: Repair loop
Validator nie tylko zwraca fail, ale generuje structured repair payload:
```yaml
status: repair
missing_requirements:
  - citation_count_min_3
  - output_schema.references[0].url
next_action: revise_current_step
```

To dobrze pasuje do bounded loops w GraphFlow / statecharts. [S5][S7]

#### Strategy 4: Escalation gate
Jeśli automatyczna walidacja nie osiąga pewności, przejście następuje do `manual_review_required`, a nie do następnego kroku roboczego.

### Jak definiować success criteria, żeby były machine-checkable

Najlepsze formaty:
1. **typed input/output schemas**,
2. **boolean checks z opisem**,
3. **severity per check**,
4. **enumerated outcomes**,
5. **artifact existence + metadata checks**,
6. **behavior policies jako explicit rules**.

Przykład:
```yaml
verification:
  hard_checks:
    - id: output_exists
      type: artifact_exists
      artifact: summary_md
    - id: schema_valid
      type: json_schema
      target: result_json
      schema_ref: summary_result_v1
    - id: required_tools_only
      type: behavior_rule
      allowed_tools: [web_search, file_reader]
  soft_checks:
    - id: min_sources
      type: numeric_threshold
      field: source_count
      gte: 3
  outcomes:
    pass: "all hard_checks pass"
    pass_with_warnings: "all hard_checks pass AND at least one soft_check fails"
    repair: "one or more hard_checks fail but step is recoverable"
    manual_review: "quality_uncertain = true"
    fail_terminal: "policy_violation = true"
```

### Wniosek dla Q2
Najstabilniejszy design to:
- **contract validation przed krokiem**,  
- **behavior hooks w trakcie**,  
- **output + quality validation po kroku**,  
- **transition gate jako osobna decyzja stanu**.  

**Siła dowodu:** praktyczne + synteza. [S2][S4][S11][S12][S13][S14]

---

## Q3: Workflow state machine

### Główne ustalenie
Dla orchestratora agentowego „workflow as state machine” jest dziś bardziej trafne niż „workflow as linear script”. Frameworki produkcyjne wspierają co najmniej stany, przejścia warunkowe, pętle, równoległość, pause/resume i persistence. [S1][S5][S7][S8][S9]

### Reprezentacje stanu i przejść

#### Option 1: Flat step-run ledger
Minimalny model:
- `execution_id`
- `current_step_id`
- `status`
- `artifacts`
- `retry_count`
- `last_validation_result`
- `updated_at`

**Plusy**
- prosty do serializacji w DB,
- łatwy do query i audit.

**Minusy**
- słabo modeluje zagnieżdżenia, parallel branches i history.

**Dobre dla**
- większości sekwencyjnych orchestratorów.

#### Option 2: Graph definition + runtime state
Definicja grafu osobno, runtime state osobno.

**Przykładowe elementy runtime**
- active nodes,
- completed nodes,
- blocked nodes,
- waiting_for_input,
- branch outcomes,
- checkpoints,
- artifact references,
- validation events.

To najlepiej odpowiada temu, co robią LangGraph, AutoGen GraphFlow i Temporal. [S1][S5][S9]

#### Option 3: Statecharts / hierarchical state machine
Najbogatsza semantyka:
- parent states,
- child states,
- parallel states,
- final states,
- history states,
- onDone,
- guards.

**Plusy**
- bardzo czyste modelowanie złożoności,
- eleganckie bounded loops, joins, composite phases.

**Minusy**
- większa złożoność implementacyjna,
- trudniejsze mapowanie 1:1 na prosty markdown workflow.

**Evidence**
- XState/Stately dokumentuje parent states, parallel states, final states, history states i `onDone`. [S7][S8]

### Common state machine patterns

#### 1. Sequential
`A -> B -> C -> done`

Najprostsze, dobre jako baseline.

#### 2. Conditional branch
`A -> (B | C)` zależnie od validatora lub routera.

**Evidence**
- LangGraph routing with structured output. [S1]
- AutoGen conditional edges. [S5]

#### 3. Bounded loop
`draft -> review -> repair -> review -> ... -> approved`

Klucz: loop musi mieć:
- explicit exit,
- max attempts,
- escalation path.

**Evidence**
- AutoGen GraphFlow wspiera conditional loops i activation groups. [S5]

#### 4. Parallel fan-out / fan-in
Np. dwa niezależne reviewery i join.

**Evidence**
- LangGraph parallelization. [S1]
- AutoGen parallel flow with join. [S5]
- Stately parallel states. [S8]

#### 5. Pause / resume
Stan oczekujący na:
- feedback,
- approval,
- external event,
- missing artifact.

**Evidence**
- LangGraph interrupts + thread_id/checkpointer. [S2]
- CrewAI `HumanFeedbackPending` + `resume()`. [S15]
- Prefect `pause_flow_run` / `suspend_flow_run`. [S11]

#### 6. Retry
Nie zmienia definicji workflow, ale zmienia runtime transition policy.

**Evidence**
- Temporal retry policy i timeouts. [S16]
- Prefect states/futures. [S10]

#### 7. Compensation / saga
Zamiast pełnego rollbacku: wykonaj kompensacje.

**Evidence**
- Temporal saga / compensating actions pattern. [S6]

### Conditional paths, loops, parallel

**Wniosek praktyczny:** minimalny runtime dla agentów powinien wspierać co najmniej:
- guard conditions,
- loop counter,
- join condition,
- timeout,
- manual interrupt,
- resumable checkpoints.

### Retry, rollback, error recovery

#### Retry patterns
- **Immediate retry** – dla transient failures
- **Backoff retry** – dla flaky external systems
- **Repair retry** – po walidacji jakości
- **Retry with modified context** – po human feedback

#### Rollback patterns
- **Logical rollback** – wróć do poprzedniego kroku i oznacz nowsze artefakty jako stale
- **Checkpoint fork** – wznowienie od starego checkpointu nową gałęzią
- **Compensation** – odwróć side effects

#### Anti-pattern
„Przywróć dokładnie poprzedni stan świata zewnętrznego” – zwykle nierealne; dlatego saga/compensation jest trafniejsze niż klasyczny rollback. [S6]

### Timeout i deadlock handling

#### Timeout
Powinny istnieć co najmniej trzy poziomy:
- step timeout,
- approval wait timeout,
- whole execution timeout.

Temporal pokazuje oddzielne timeouty dla activity execution i retry policy. [S16]

#### Deadlock / livelock guards
Minimalne bezpieczniki:
- `max_retries_per_step`
- `max_loop_iterations`
- `max_total_transitions`
- `stagnation_detector` (ten sam validator fail N razy)
- `no_progress_timeout`

### Persistence do DB

Najpraktyczniejszy model:
1. **Workflow definition table** – definicja kroków i przejść  
2. **Execution table** – bieżący status  
3. **Checkpoint table** – snapshot stanu  
4. **Event log table** – append-only historia przejść  
5. **Artifact table** – URI, typ, checksum, producer_step

To łączy zalety:
- szybkiego odczytu bieżącego stanu,
- pełnego audytu,
- resume/fork/debug.

### Wniosek dla Q3
Najlepszy kompromis:
- definicja workflow jako **parseable graph**,  
- runtime jako **state ledger + checkpoints + event log**,  
- semantyka przejść inspirowana **statecharts**, ale niekoniecznie pełny statechart DSL.  

**Siła dowodu:** praktyczne + synteza. [S1][S5][S7][S8][S9][S16]

---

## Q4: Prompt streaming patterns

### Główne ustalenie
Nowoczesne frameworki pokazują, że **co agent widzi** powinno być sterowane osobno od tego, **jaki krok właśnie wykonuje**. To najmocniejszy argument przeciw transcript-first prompting w długich workflows. [S5]

### Strategy 1: Current step only
Agent dostaje tylko:
- instrukcję bieżącego kroku,
- jawny input schema,
- minimalny stan wejściowy,
- referencje do artefaktów.

**Kiedy używać**
- domyślnie, gdy workflow jest deterministyczny i validator-driven.

**Plusy**
- mały context,
- najmniejsze ryzyko leakage kolejnych kroków,
- najlepsza kontrola.

**Minusy**
- agent może słabiej optymalizować pod downstream.

### Strategy 2: Current step + compact carryover
Do bieżącego kroku dodawany jest krótki summary poprzedniego wyniku.

**Kiedy używać**
- gdy krok wymaga miękkiej ciągłości, ale nie pełnej historii.

**Dobre carryover fields**
- `previous_step_id`
- `previous_outcome`
- `key_findings_summary`
- `artifact_refs`

### Strategy 3: Current step + next gate preview
Agent widzi bieżący krok oraz skrócony opis najbliższego validatora / exit gate.

**Zaleta**
- agent wie, jak będzie oceniany,
- ale nie zna całego workflow.

To bardzo dobry kompromis dla validation-first design.

### Strategy 4: Filtered transcript
Zamiast pełnej historii dajesz:
- last message from required source,
- first user request,
- final reviewer note,
- selected memory keys.

**Evidence**
- AutoGen GraphFlow message filtering i `PerSourceFilter`. [S5]

### Full output vs summary vs artifacts only

#### Full output
Dobre tylko gdy:
- output jest krótki,
- downstream musi operować na pełnym tekście,
- koszt tokenów jest akceptowalny.

#### Summary
Dobry default dla reasoning continuity.

#### Artifacts only
Najlepsze gdy downstream krok działa na pliku / strukturze danych, nie na transcript.

### Memory management patterns

#### Pattern A: Working memory per execution
Krótki stan bieżący:
- current step inputs,
- validator feedback,
- branch decisions,
- unresolved issues.

#### Pattern B: Artifact memory
Zewnętrzne pliki/rekordy przechowywane poza promptem.

#### Pattern C: Policy memory
Stałe zasady workflow ładowane jako oddzielny policy block, a nie powtarzane w każdym kroku.

#### Pattern D: Checkpoint memory
Stan przywracalny dla resume/debug/fork.

**Evidence**
- LangGraph threads/checkpoints. [S1][S2]
- AutoGen save/load state dla agents i teams. [S17]
- CrewAI automatycznie persistuje paused flow state przy human feedback. [S15]

### Context window optimization — praktyczne heurystyki

To jest **synteza**, nie capability jednego frameworka:

1. **Nie przekazuj pełnej historii, jeśli downstream może działać na artifact refs.**
2. **Traktuj prompt jako widok na stan, nie jako stan sam w sobie.**
3. **Przechowuj pełny execution log poza modelem, w orchestratorze.**
4. **Przekazuj pełny output tylko ostatniego kroku, starsze kroki jako summary/refs.**
5. **Oddziel:**
   - policy/instructions,
   - current task contract,
   - minimal carryover state,
   - artifact refs,
   - validator expectations.

### Przykładowy budżet promptu (heurystyka)
Dla długich workflows:
- 40–50%: current step contract + policy,
- 20–30%: selected prior state,
- 20–30%: artifacts or extracted excerpts,
- 0–10%: next-gate preview.

### Wniosek dla Q4
Najsilniejszy pattern to:
- **execution graph != message graph**,  
- **prompt = minimalny widok na stan**,  
- **history = w persistence layer**, nie w transcript dumpie.  

**Siła dowodu:** praktyczne + synteza. [S1][S5][S15][S17]

---

## Q5: Existing frameworks — orchestration focus

### Porównanie

| Framework / pattern | Runtime model | Persistence | Pause / HITL | Branch/loop/parallel | Validation hooks | Najmocniejsza lekcja |
|---|---|---|---|---|---|---|
| LangGraph | graph + state + checkpoints | mocne | interrupts | tak | pośrednio przez nodes/tasks/guards | durable, checkpointed graph execution [S1][S2] |
| AutoGen GraphFlow/Core | directed graph + actor/event model | średnie/dobre | intervention / HITL / save_state | tak | intervention handlers | oddziel execution graph od message graph [S5][S13][S17] |
| CrewAI Flows | event-driven flow + shared state | dobre | human_feedback / webhook HITL | tak | before/after LLM & tool hooks | hooks jako runtime gates [S3][S4][S14][S15] |
| Temporal | durable workflows + event history | bardzo mocne | signals/cancel/terminate | tak | nie „LLM-native”, ale silne control primitives | compensation, retries, durable execution [S6][S9][S16] |
| Prefect | flows/tasks/states | dobre | pause/suspend/input validation | nested flows, concurrency | validation głównie contract/state-level | input contracts i explicit run states [S10][S11] |
| Dagster | data/workflow checks | dobre | nie centralny feature agentowy | downstream blocking | asset checks | checks jako first-class objects [S12] |
| Statecharts / XState | formal state machine semantics | zależne od implementacji | model-level | parent/parallel/history/final | guards/onDone | najlepsza semantyka złożonych przejść [S7][S8] |

### LangGraph
**Mocne strony**
- checkpointing przy krokach,
- thread-based state,
- durable execution,
- interrupts,
- routing i parallelization.

**Lekcja**
- runtime agentowy powinien być traktowany jak **resumable graph execution**, nie jak jednorazowy prompt chain. [S1][S2]

### AutoGen
**Mocne strony**
- GraphFlow daje strict execution control,
- Core opiera się o actor/event model,
- intervention handlers pozwalają budować approval gates,
- state save/load dla agentów i teams,
- message filtering jako osobny wymiar.

**Lekcja**
- bardzo ważne jest jawne rozdzielenie:
  - kto ma wykonać następny krok,
  - jakie wiadomości ma zobaczyć. [S5][S13][S17]

### CrewAI
**Mocne strony**
- prosty event-driven flow model,
- shared state,
- human feedback in flows,
- execution hooks dla LLM i tools.

**Lekcja**
- validation hooks najlepiej działają jako **interceptory runtime**, a nie tylko jako końcowy validator po fakcie. [S3][S4][S14][S15]

### Temporal
**Mocne strony**
- bardzo silna semantyka durability, retries, timeouts, event history,
- child workflows do partitioning,
- compensation/saga.

**Lekcja**
- dla side effects i długich procesów trzeba myśleć event-history-first oraz compensation-first. [S6][S9][S16]

### State machines / statecharts
**Mocne strony**
- formalny model parent/child/parallel/history/final/onDone.

**Lekcja**
- nawet jeśli nie używasz pełnego statechart DSL, semantyka statecharts jest dobrym wzorcem do projektowania przejść i composite phases. [S7][S8]

### Orchestration patterns z produkcji

#### Centralized orchestrator
Jeden runtime zarządza stanem i przejściami.
- Najbardziej zgodny z wymaganiami incremental loading + validation gates.
- Najłatwiejszy do audytu.

#### Choreography
Agenci publikują eventy i sami „układają się” w przepływ.
- Elastyczne, ale słabsze dla silnych gate’ów i compliance.
- Bardziej naturalne w event-driven multi-agent runtimes, mniej w deterministic workflow engines.

#### Saga / compensation
Dla side effects i distributed actions.
- Nie jest to LLM-specific pattern, ale bardzo trafny dla agentów wykonujących operacje zewnętrzne. [S6]

### Wniosek dla Q5
W kontekście orchestration runtime najmocniejsze wzorce dziś pochodzą z połączenia:
- **LangGraph / AutoGen / CrewAI** dla agent-native execution control,
- **Temporal / Prefect / Dagster** dla durability, state, checks i lifecycle semantics,
- **statecharts** dla modelowania złożonych przejść.  

**Siła dowodu:** praktyczne.

---

## Q6: Validation-first workflow design

### Główne ustalenie
Validation-first nie oznacza „dodaj walidację na końcu”. Oznacza:
1. najpierw zdefiniuj **stan końcowy i warunki przejścia**,  
2. dopiero potem zaprojektuj krok,  
3. krok istnieje po to, żeby doprowadzić stan do postaci przechodzącej gate.  

### Pattern 1: Exit-gate-first design
Najpierw definiujesz:
- co ma istnieć po kroku,
- jak to zmierzyć,
- czy wynik jest binary / graded / human-reviewed.

Dopiero potem tworzysz prompt/krok.

### Pattern 2: Contract-first design
Każdy krok ma:
- input schema,
- output schema,
- artifact contract,
- validation contract,
- transition contract.

**Evidence**
- Prefect param schemas i `RunInput` oparte o Pydantic. [S10][S11]
- LangGraph structured routing i typed state. [S1]
- Dagster checks jako first-class testable contracts. [S12]

### Pattern 3: Validator-as-first-class node
Zamiast „ukrytej” walidacji w kodzie:
- potraktuj validator jako jawny etap / hook / transition rule.

To daje:
- obserwowalność,
- metrics,
- łatwe retry/repair,
- audit.

### Pattern 4: Outcome enums instead of booleans
`pass/fail` jest za ubogie.

Lepsze:
- `pass`
- `pass_with_warnings`
- `repair`
- `manual_review`
- `fail_terminal`

### Pattern 5: Repair payloads
Validator nie powinien zwracać tylko „nie”.
Powinien zwrócić:
- co nie przeszło,
- jaka jest severity,
- czy da się naprawić,
- jaki krok naprawczy uruchomić.

### Jak pisać exit gate, żeby był auto-walidowalny

Zamiast:
> „Wynik powinien być dobrej jakości i kompletny.”

Lepiej:
```yaml
exit_gate:
  required_artifacts:
    - id: summary_md
      type: markdown
    - id: source_manifest
      type: json
  hard_checks:
    - type: artifact_exists
      artifact: summary_md
    - type: schema_valid
      target: source_manifest
      schema_ref: source_manifest_v1
    - type: field_nonempty
      target: summary_md.sections.tldr
  soft_checks:
    - type: min_items
      target: source_manifest.sources
      gte: 3
  human_review:
    required_when:
      - confidence_lt: 0.7
      - conflicting_sources: true
```

### Jak definiować validation hooks w workflow document

Najpraktyczniejsze sekcje per step:
```yaml
step_id: draft_summary
inputs:
  artifacts: [source_notes]
  state_fields: [research_goal]
outputs:
  artifacts: [summary_md, source_manifest]
execution:
  allowed_tools: [web_search, file_reader]
  max_attempts: 2
verification:
  preconditions:
    - source_notes.exists == true
  hard_checks:
    - summary_md.exists == true
    - source_manifest.schema == source_manifest_v1
  soft_checks:
    - source_manifest.source_count >= 3
  escalation:
    manual_review_if:
      - conflicting_sources == true
transitions:
  on_pass: publish_summary
  on_pass_with_warnings: publish_summary
  on_repair: revise_summary
  on_manual_review: human_review_summary
  on_fail_terminal: abort
```

### Test-driven workflow design
To sensowne podejście dla agent workflows:
1. napisz exit gate,
2. napisz przykłady pass/fail,
3. dopiero potem prompt kroku,
4. uruchom testy na validatorze niezależnie od modelu.

### Wniosek dla Q6
Validation-first design najlepiej działa, gdy:
- kontrakty są typed,
- gate’y są jawne,
- walidacja jest osobnym obiektem runtime,
- przejścia zależą od outcome enum, nie od ukrytego if-a w promptach.  

**Siła dowodu:** praktyczne + synteza. [S10][S11][S12]

---

## Recommended patterns

Poniżej wzorce, które wynikają z researchu jako najbardziej stabilne i najczęściej potwierdzone przez praktykę frameworków.

### 1. Graph + state + gate trifecta
Workflow definition:
- parseable graph of steps

Runtime:
- persisted execution state
- explicit validation gates per transition

### 2. Step-level default, nested-subflow optional
- top-level: krok domenowy
- wewnątrz złożonego kroku: subflow / child workflow / subgraph
- micro-step: tylko dla approvals i side effects

### 3. Separate execution graph from message graph
- execution graph mówi **kto i kiedy działa**
- message graph mówi **co agent widzi**

### 4. Artifact-first context passing
- transcript only by exception
- domyślnie: state fields + artifact refs + minimal summary

### 5. Validator outcomes as finite states
Walidator powinien zwracać stan, nie tylko bool.

### 6. Transition guards as first-class runtime rules
Nie chowaj warunków przejścia w promptach.

### 7. Bounded loops only
Każda pętla musi mieć:
- exit condition,
- max attempts,
- escalation path.

### 8. Compensation for side effects
Dla operacji zewnętrznych:
- retry jeśli transient,
- compensation jeśli partial side effects,
- manual review jeśli high-risk inconsistency.

### 9. Checkpointed pause/resume
Approval i feedback powinny być realizowane jako pause/resume na persisted state, nie jako „napisz później jeszcze raz cały prompt”.

### 10. Contract-first workflow document
Per step:
- inputs
- outputs
- allowed tools
- verification
- transitions

---

## Anti-patterns

### 1. Full-workflow-in-context
Dawanie agentowi całego workflow naraz:
- zwiększa leakage,
- utrudnia kontrolę,
- osłabia gate’y incrementalne.

### 2. Transcript-first handoff
Przekazywanie całej rozmowy między krokami zamiast typed state + artifacts.

### 3. Hidden validation
Walidacja tylko „mentalnie” w promptach, bez jawnego runtime checka.

### 4. Bool-only validation
`true/false` bez severity, bez repair payload, bez escalation.

### 5. Unbounded self-repair loops
„Poprawiaj aż będzie dobrze” bez liczników i timeoutów.

### 6. Side effects before checkpoint-safe boundary
Zwłaszcza przy pause/resume i replay.

### 7. Using child workflows / subflows only for code organization
Temporal wprost ostrzega, że child workflows nie są po prostu narzędziem do porządkowania kodu. [S9]

### 8. Treating orchestration state as prompt history
Stan powinien być w orchestratorze, nie wyłącznie w rozmowie modelu.

### 9. Parallelizing dependent branches
Parallel fan-out tylko dla faktycznie niezależnych prac.

### 10. Overfitting to one framework’s API
Warto czerpać z semantyk (graph, checkpoints, validation hooks, statecharts), a nie kopiować 1:1 konkretne API.

---

## Open questions

1. **Jak daleko automatyzować quality validation?**  
   Machine-checkable output i behavior checks są jasne, ale ocena „jakości merytorycznej” pozostaje częściowo heurystyczna.

2. **Czy validator quality powinien być osobnym agentem, regułą kodową, czy hybrydą?**  
   Research sugeruje hybrydę, ale nie daje jednego dominującego standardu.

3. **Jak reprezentować parallel branches w lekkim markdown+YAML bez wejścia w pełny DSL?**  
   Statecharts są semantycznie mocne, ale mogą być za ciężkie dla lekkiej specyfikacji.

4. **Jak mierzyć i egzekwować behavior validation w model-agnostic sposób?**  
   Szczególnie dla „czy agent użył właściwej strategii”, nie tylko „czy użył właściwego toola”.

5. **Jak łączyć checkpoint fork/time-travel z prostą semantyką biznesową?**  
   LangGraph i Temporal pokazują techniki, ale nie rozwiązują UX/spec ergonomics automatycznie.

6. **Na ile message filtering powinien być deklaratywny w workflow doc, a na ile konfigurowany przez orchestrator?**

7. **Czy w workflow document powinny istnieć osobne sekcje dla execution graph i message graph?**  
   Research mocno sugeruje, że tak, ale to wymaga dalszego eksperymentu dokumentacyjnego.

---

## Integration notes

Na podstawie briefu, a nie treści `workflow_compliance.md` (którego zawartość nie była dostępna w tym zadaniu), sensowne rozdzielenie warstw wygląda tak: [BRIEF]

### Warstwa 1: Workflow authoring / compliance
To, co najpewniej powinno opisywać `workflow_compliance.md`:
- jak pisać kroki,
- jak formułować instrukcje dla agenta,
- jak nazywać sekcje i pola,
- jak zapisać verification/constraints w dokumencie.

### Warstwa 2: Workflow orchestration runtime
To, co wynika z tego researchu:
- jak interpretować dokument jako graf i stan,
- jak dawkować kontekst agentowi,
- jak wykonywać walidację,
- jak robić pause/resume/retry/repair/escalation,
- jak persistować execution state.

### Najważniejsze punkty styku
1. **`step_id`** – powinno być stabilnym kluczem runtime.
2. **`inputs/outputs`** – powinny być schema-friendly.
3. **`verification`** – powinno być rozbijalne na hard/soft/manual.
4. **`transitions`** – powinny być jawne i machine-readable.
5. **`allowed_tools` / policy** – powinny wspierać behavior validation.
6. **`exit_gate`** – powinien być możliwy do uruchomienia jako validator hook lub validator node.

### Praktyczna implikacja
Jeśli `workflow_compliance.md` ustali konwencję dokumentu, ten research sugeruje, żeby konwencja zawierała nie tylko opis kroku, ale też minimalne metadane runtime:
- identyfikator kroku,
- kontrakt I/O,
- verification,
- transitions,
- opcjonalnie context policy / visibility policy.

---

## Źródła

### Primary / official docs
- [S1] LangGraph overview, persistence, durable execution, workflows/routing/parallelization  
  - https://docs.langchain.com/oss/python/langgraph/overview  
  - https://docs.langchain.com/oss/python/langgraph/persistence  
  - https://docs.langchain.com/oss/python/langgraph/durable-execution  
  - https://docs.langchain.com/oss/python/langgraph/workflows-agents

- [S2] LangGraph interrupts  
  - https://docs.langchain.com/oss/python/langgraph/interrupts

- [S3] CrewAI Flows  
  - https://docs.crewai.com/en/concepts/flows

- [S4] CrewAI Execution Hooks  
  - https://docs.crewai.com/en/learn/execution-hooks

- [S5] AutoGen GraphFlow + managing state + core docs  
  - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html  
  - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/state.html  
  - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html  
  - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/sequential-workflow.html

- [S6] Temporal saga compensating actions  
  - https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas

- [S7] Stately / XState parent states, final states, history states  
  - https://stately.ai/docs/parent-states  
  - https://stately.ai/docs/final-states  
  - https://stately.ai/docs/history-states

- [S8] Stately / XState parallel states, persistence  
  - https://stately.ai/docs/parallel-states  
  - https://stately.ai/docs/persistence

- [S9] Temporal workflow execution, child workflows, interruption, failure detection  
  - https://docs.temporal.io/workflow-execution  
  - https://docs.temporal.io/child-workflows  
  - https://docs.temporal.io/evaluate/development-production-features/interrupt-workflow  
  - https://docs.temporal.io/develop/python/failure-detection

- [S10] Prefect flows  
  - https://docs.prefect.io/v3/concepts/flows

- [S11] Prefect interactive workflows / pause / suspend / typed input validation  
  - https://docs.prefect.io/v3/advanced/interactive

- [S12] Dagster asset checks  
  - https://docs.dagster.io/guides/test/asset-checks

- [S13] AutoGen intervention handler for tool approval  
  - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/tool-use-with-intervention.html

- [S14] CrewAI HITL overview  
  - https://docs.crewai.com/en/learn/human-in-the-loop

- [S15] CrewAI human feedback in flows  
  - https://docs.crewai.com/en/learn/human-feedback-in-flows

- [S16] Temporal retry policy / timeouts (Python SDK)  
  - https://docs.temporal.io/develop/python/failure-detection

- [S17] AutoGen state save/load and persistence examples  
  - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/state.html

### Research / secondary
- [S18] Agentproof: Static Verification of Agent Workflow Graphs (2026)  
  - https://arxiv.org/abs/2603.20356

### Brief
- [BRIEF] Uploaded research brief for this task.
