# Research: Rola PM w systemie multi-agent (Faza 2)

Data: 2026-03-26

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo / publiczna implementacja
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 7 najważniejszych wniosków

1. **1M context window nie usuwa problemu degradacji; tylko przesuwa granicę opłacalnej ciągłej sesji.** Anthropic nadal opisuje context rot, compaction i structured memory jako potrzebne techniki, a benchmarki long-context pokazują spadki jakości dużo wcześniej niż przy 1M tokenów, zwłaszcza na zadaniach wymagających precyzyjnego retrievalu lub naprawy kodu. **Siła dowodów: empiryczne + praktyczne.**
2. **Najmocniej podparty wzorzec lifecycle to hybryda:** długa sesja tam, gdzie model/harness dobrze znosi compaction, ale z trwałymi artefaktami stanu i gotowością do hard resetu przy stallach, loopach albo spadku koherencji. **Siła dowodów: praktyczne.**
3. **Magentic-One używa ledgera jako mechanizmu sterowania, nie tylko pamięci.** Outer task ledger przechowuje fakty/guesses/plan; inner progress ledger odpowiada co turę na 5 pytań o ukończenie, progres, pętlę, next speaker i instrukcję. Stall counter wyzwala re-plan i reset kontekstów agentów. **Siła dowodów: empiryczne + praktyczne.**
4. **Ledger pomaga, ale publiczne dowody nie izolują go czysto od innych mechanizmów.** Ablacja Magentic-One pokazuje ~31% spadku bez pełnego orchestratora/ledgerów, ale baseline usuwa jednocześnie progress tracking, loop detection i explicit instructions. To mocny sygnał „structured control > goła rozmowa”, ale nie czysty dowód „sam ledger > sama pamięć rozmowy”. **Siła dowodów: empiryczne.**
5. **Budżet tokenów w Anthropic API trzeba modelować jako miks limitów per-minute i limitu wydatków, nie jako prosty „reset co 5h/tydzień”.** Oficjalne API dokumentuje org-level monthly spend caps, RPM/ITPM/OTPM, acceleration limits i response headers; nie udało się potwierdzić w oficjalnej dokumentacji API stałych limitów „co 5h” ani „weekly” dla standardowego Messages API. **Siła dowodów: praktyczne.**
6. **Prompt caching radykalnie zmienia scheduler.** Dla większości modeli cache reads nie liczą się do ITPM; przy wysokim cache hit-rate realna przepustowość input może wzrosnąć wielokrotnie. To oznacza, że scheduler powinien zarządzać osobno: uncached input, cache writes, output i concurrency. **Siła dowodów: praktyczne.**
7. **Najdojrzalszy wzorzec autonomii jest warstwowy, nie binarny.** Pełna autonomia dla pracy odwracalnej i niskiego ryzyka; maker-checker dla jakości; approval gates dla high-stakes tool calls; eskalacja do człowieka przy wysokim ryzyku, braku precedensu, wyczerpywaniu budżetu albo powtarzających się stallach. **Siła dowodów: praktyczne + częściowo empiryczne.**

## Wyniki per temat

## Temat 1: Session lifecycle managera — ciągła sesja vs cykle z checkpointem

### 1.1. Przy 1M context — jak długo sesja pozostaje efektywna?

**Fakty ze źródeł**
- Anthropic wprost pisze, że wraz ze wzrostem liczby tokenów maleje zdolność modelu do trafnego przywoływania informacji z kontekstu („context rot”), a zjawisko to występuje na wszystkich modelach, choć z różną łagodnością. **Siła dowodów: praktyczne.**
- Anthropic udostępnia dziś 1M context dla Claude Opus 4.6 i Sonnet 4.6 przy standard pricing; dodatkowo w release notes pojawia się compaction API do „effectively infinite conversations”. **Siła dowodów: praktyczne.**
- Anthropic deklaruje też, że Opus 4.6 lepiej utrzymuje informacje na „hundreds of thousands of tokens” i ma mniej driftu niż Opus 4.5. To ważny sygnał poprawy, ale nadal jest to vendor claim, nie zewnętrzna ablacją. **Siła dowodów: praktyczne.**
- LongCodeBench testuje modele aż do 1M tokenów i pokazuje, że długie okna są nadal trudne: na zadaniach code repair jakość bywa niemonotoniczna, a na LongSWE-Bench Claude 3.5 Sonnet spada z 29% przy 32K do 3% przy 256K. **Siła dowodów: empiryczne.**
- Lost in the Middle pokazuje bardziej ogólny problem: modele często najlepiej radzą sobie, gdy istotna informacja jest na początku lub końcu kontekstu, a gorzej — gdy jest „w środku”. NoLiMa pokazuje, że klasyczne needle-in-a-haystack przeceniają realne zdolności long-context, bo usunięcie literalnych wskazówek nadal mocno psuje wyniki wielu modeli. **Siła dowodów: empiryczne.**

**Synteza**
- Nie ma publicznej, wiarygodnej odpowiedzi typu „sesja jest dobra do X godzin” lub „do Y tokenów”. Granica zależy od:
  - rodzaju zadania (retrieval / planning / coding / debugging),
  - gęstości istotnych informacji w kontekście,
  - tego, czy model ma externalized state poza rozmową,
  - tego, czy harness robi compaction / retrieval / checkpoints.
- Najbardziej uczciwy wniosek brzmi: **1M czyni „wieczną sesję” bardziej wiarygodną niż dawniej, ale nie usuwa potrzeby zarządzania pamięcią i resetów.** Szczególnie przy zadaniach wymagających precyzyjnego odwołania do dawnych decyzji albo weryfikowalnej poprawności nadal trzeba zakładać degradację.

**Odpowiedź na pytanie badawcze**
- **Czy 1M zmienia kalkulację?** Tak — zdecydowanie zwiększa sens dłuższych sesji i zmniejsza presję na częste resety.
- **Czy eliminuje rot?** Nie.
- **Czy istnieje publiczny benchmark „bezpiecznej długości sesji” dla Claude 4.6 / Sonnet 4.6?** Nie udało się potwierdzić.

### 1.2. Konkretne mechanizmy checkpointingu agentów LLM

Najczęściej powtarzające się mechanizmy w źródłach:

#### A. File-based handoff / self-handoff
- `init.sh` lub równoważny script bootstrappingowy.
- progress log (`claude-progress.txt` albo analogiczny plik statusu).
- feature checklist w JSON z polem `passes`, zmienianym tylko po end-to-end verification.
- git history jako dodatkowy recovery layer.
- start każdej nowej sesji od odczytu progress file, git logu i feature listy.  
**Siła dowodów: praktyczne.**

To jest najczystsza odpowiedź na „self-handoff do bazy / pliku”: **stan nie jest „w głowie modelu”, tylko w artefaktach roboczych, które następny agent może szybko przeczytać.**

#### B. Structured memory tool
Anthropic memory tool opisuje wzorzec multi-session:
1. pierwsza sesja bootstrapuje artefakty pamięci,
2. kolejne sesje zaczynają od ich odczytu,
3. na końcu każdej sesji aktualizują progress log.  
**Siła dowodów: praktyczne.**

To jest formalizacja file-based handoffu w narzędziu pamięci.

#### C. Graph checkpoints / durable execution
LangGraph zapisuje checkpoint stanu grafu na każdym kroku wykonania, w threadach. Dodatkowo oferuje durability modes (`exit`, `async`, `sync`) i wznowienie po failure / interrupt.  
**Siła dowodów: praktyczne.**

To jest bardziej „workflow state checkpointing” niż „agent pisze pamiętnik”, ale dla PM-orchestratora jest bardzo ważne, bo pozwala wznowić execution bez powtarzania już ukończonych kroków.

#### D. Living plan / execution plan
OpenAI opisuje `PLANS.md` / `ExecPlan` jako living design document dla pracy wielogodzinnej; Codex loop aktualizuje plan/status w trakcie działania.  
**Siła dowodów: praktyczne.**

To jest wariant ledgera zorientowanego na plan wykonania.

### 1.3. Jak wygląda session rotation w praktyce?

**Najczęstsze wyzwalacze rotacji / checkpointu:**
1. **zbliżanie się do limitu kontekstu** → compaction albo reset,
2. **spadek koherencji / context anxiety** → hard reset ze structured handoff,
3. **stall / brak progresu / wykrycie loopa** → re-plan + nowy cykl,
4. **maksymalna liczba tur / run-limit** → stop lub eskalacja,
5. **failure / human interrupt / process crash** → resume z checkpointu,
6. **naturalne granice sprintu / feature chunku** → checkpoint nawet bez restartu.  
**Siła dowodów: praktyczne.**

**Kto decyduje?**
- W najlepiej udokumentowanych systemach decyzja jest zwykle **zewnętrzna albo hybrydowa**, nie w pełni pozostawiona samemu agentowi:
  - Anthropic: harness + compaction + artifacts,
  - Magentic-One: outer/inner loop + stall threshold,
  - LangGraph: checkpointer / interrupt / runtime,
  - LangChain middleware: model/tool call limit middleware.
- Nie udało się znaleźć mocnego dowodu, że „agent sam najlepiej wie kiedy umrzeć i odrodzić się” jest dziś wzorcem dominującym w produkcyjnych harnessach.

### 1.4. Co dokładnie Anthropic rekomenduje w „effective harnesses for long-running agents”?

Najbardziej konkretne rekomendacje, które da się przełożyć na implementację:

1. **Initializer agent + coding agent** zamiast jednej roli na wszystko.  
2. **Clear artifacts across sessions** — progress file, init script, initial git commit.  
3. **Feature list jako JSON**, z bardzo ograniczonym zakresem edycji (`passes` po weryfikacji).  
4. **One feature at a time** — unikanie szerokiego rozlewania scope.  
5. **Start sesji od recovery i weryfikacji stanu**, nie od implementacji kolejnej rzeczy.  
6. **End-to-end verification tools** (np. browser automation) jako część rutyny sesji.  
7. **Przy trudniejszych modelach lub taskach**: hard reset + handoff bywa skuteczniejszy niż sama compaction.  
8. **Przy nowszych modelach**: możliwa jest długa, jedna sesja z compaction, ale nadal z externalized state i evaluator/planner scaffoldem.  
**Siła dowodów: praktyczne.**

### 1.5. Czy istnieją wzorce hybrydowe?

Tak — i to właśnie one są najlepiej podparte.

#### Hybryda A: Continuous session + automatic compaction + externalized state
- Anthropic dla nowszego harnessu na Opus 4.5/4.6 opisał ciągłą sesję z automatic compaction.
- Nadal jednak utrzymywane są plan/spec/contracts/files jako externalized state.  
**Siła dowodów: praktyczne.**

#### Hybryda B: Long session + periodic self-checkpoint bez restartu
- session trwa dalej,
- ale agent co sprint / milestone aktualizuje status, plan, checklistę, artefakty,
- dzięki temu późniejszy reset jest tani, a bieżąca sesja nie trzyma wszystkiego „w rozmowie”.  
**Siła dowodów: praktyczne.**

#### Hybryda C: Hard reset tylko po triggerach jakości
- reset nie jest obowiązkowy co N minut,
- uruchamia się dopiero po stallach, loopach, context anxiety, awarii albo złych sygnałach jakości.  
**Siła dowodów: praktyczne + częściowo spekulacja.**

**Wniosek dla tematu 1**
- **Dominujący dziś wzorzec nie jest ani czysto „wieczna sesja”, ani czysto „krótkie cykle”, tylko session-as-primary + checkpoints-as-safety-net.**  
**Siła dowodów: praktyczne.**

---

## Temat 2: Ledger-based control — implementacja dla managera

### 2.1. Jakie konkretnie pola ma ledger w Magentic-One?

### Task ledger (outer loop)
Paper podaje, że task ledger zawiera:
- **given or verified facts**
- **facts to look up**
- **facts to derive**
- **educated guesses**
- **task plan**  
Plan jest w natural language i obejmuje kroki oraz przypisania kroków do agentów.  
**Siła dowodów: empiryczne.**

### Progress ledger (inner loop)
Progress ledger odpowiada co iterację inner loop na 5 pytań:
1. **Is the request fully satisfied?**
2. **Is the team looping or repeating itself?**
3. **Is forward progress being made?**
4. **Which agent should speak next?**
5. **What instruction or question should be asked of this team member?**  
**Siła dowodów: empiryczne.**

### Dodatkowe szczegóły implementacyjne z publicznych śladów kodu
Publiczny issue z kodem orchestratora pokazuje, że progress ledger jest walidowany jako JSON z wymaganymi kluczami:
- `is_request_satisfied`
- `is_progress_being_made`
- `is_in_loop`
- `instruction_or_question`
- `next_speaker`

Każdy z tych elementów jest oczekiwany jako obiekt z polami:
- `answer`
- `reason`  
**Siła dowodów: praktyczne (publiczny kod / issue w repo).**

To bardzo ważny szczegół: **ledger nie jest w implementacji „luźną notatką”, tylko częściowo ustrukturyzowanym kontraktem sterowania.**

### 2.2. Jak ledger wpływa na jakość decyzji vs „pamięć rozmowy”?

**Co potwierdzono**
- Ablacja Magentic-One pokazuje, że zastąpienie pełnego orchestratora prostym baseline orchestrator skutkuje spadkiem performance o **31%** na GAIA validation.  
**Siła dowodów: empiryczne.**

**Ale ważne zastrzeżenie**
- Ten baseline usuwa jednocześnie:
  - progress tracking,
  - loop detection,
  - explicit instructions do innych agentów,
  - oraz pełne ledger-based orchestration.
- Zatem publiczny wynik nie izoluje samego ledgera jako pojedynczej zmiennej.  
**Siła dowodów: empiryczne.**

**Najuczciwsza interpretacja**
- Dane wspierają tezę: **structured orchestration state + explicit control loop > prosty turn-taking oparty na conversation context**.
- Dane **nie wystarczają**, by z pełną pewnością powiedzieć: **„sam ledger” jest dokładnie odpowiedzialny za X% poprawy**.  
**Siła dowodów: empiryczne.**

### 2.3. Inne systemy implementujące ledger pattern lub equivalent

#### A. Anthropic long-running harness
Equivalent ledgera:
- progress file,
- feature checklist,
- spec / sprint contract,
- git history jako audit trail.  
To nie jest nazwane „ledger”, ale funkcjonalnie spełnia tę samą rolę: externalized working memory + control state.  
**Siła dowodów: praktyczne.**

#### B. LangGraph shared state + checkpoints
Equivalent ledgera:
- wspólny graph state,
- checkpoint na każdym kroku,
- możliwość inspekcji, resume, human review.  
To jest bliżej „blackboard/shared state” niż „task ledger”, ale funkcjonalnie realizuje ten sam wzorzec: **manager nie polega wyłącznie na historii rozmowy**.  
**Siła dowodów: praktyczne.**

#### C. OpenAI PLANS.md / ExecPlans
Equivalent ledgera:
- żywy plan,
- explicit assumptions,
- design + milestone state,
- aktualizowany status pracy w trakcie długiego runu.  
**Siła dowodów: praktyczne.**

#### D. Systemy serving/scheduling
Papers typu Kairos, AI Metropolis, Justitia czy AgentRM nie używają słowa „ledger” w sensie promptowym, ale utrzymują:
- workflow analysis,
- dependency graph,
- predicted remaining cost,
- scheduler state,
- admission control state.  
To jest „machine ledger” zamiast „LLM-readable ledger”.  
**Siła dowodów: empiryczne.**

### 2.4. Jak manager aktualizuje ledger? Jakie są triggery?

Najbardziej powtarzalny wzorzec w źródłach to **event-driven updates**, nie stałe „co N tur”.

#### Magentic-One
- **task ledger**: tworzony na początku outer loop, a potem aktualizowany przy re-planie,
- **progress ledger**: aktualizowany każdą iterację inner loop,
- **re-plan**: po przekroczeniu progu stalli / wykryciu pętli / braku progresu.  
**Siła dowodów: empiryczne.**

#### Anthropic memory pattern
- odczyt pamięci na starcie sesji,
- update progress logu na końcu sesji,
- feature checklist aktualizowana po zweryfikowanym ukończeniu.  
**Siła dowodów: praktyczne.**

#### LangGraph
- checkpoint przy każdym kroku wykonania.  
**Siła dowodów: praktyczne.**

**Wniosek**
- Najmocniejszy wzorzec to:
  - **high-frequency update** dla local progress,
  - **lower-frequency update** dla plan/facts,
  - **trigger-based replanning**, a nie arbitralne „co 10 tur”.  
**Siła dowodów: praktyczne + empiryczne.**

### 2.5. Jak programowo wykrywać stuckness?

Źródła wskazują kilka klas sygnałów:

#### Sygnały bezpośrednie (control-loop)
- `is_progress_being_made = false`
- `is_in_loop = true`
- stall counter rośnie
- max_turns / max_stalls przekroczone  
**Siła dowodów: empiryczne + praktyczne.**

#### Sygnały behawioralne z error analysis
Magentic-One w error analysis pokazuje powtarzalne failure modes przydatne jako metryki stuckness:
- **suboptimal-task-reexecution** — powtarzanie działań bez nowego wyniku,
- **persistent-error-neglect** — ignorowanie powtarzających się błędów,
- **improper-task-finalization** — ogłaszanie sukcesu bez weryfikacji.  
**Siła dowodów: empiryczne.**

#### Użyteczne metryki operacyjne (synteza)
Najbardziej sensowny zestaw detektorów stuckness dla managera:
1. **brak nowego artefaktu** przez T czasu / N iteracji,
2. **powtórka tej samej akcji** z podobnym parametrem > K razy,
3. **powtarzające się błędy** bez zmiany strategii,
4. **brak zmiany ledgera** między iteracjami,
5. **niska novelty akcji** (kolejne kroki semantycznie bardzo podobne),
6. **task closed bez evidence** (brak testów, brak outputu, brak diffu).  
**Siła dowodów: częściowo empiryczne, częściowo spekulacja.**

**Wniosek dla tematu 2**
- Ledger pattern działa najlepiej wtedy, gdy **stan jest mały, jawny i akcyjny**: fakty, plan, progres, następny krok, powód. Gdy ledger staje się logiem wszystkiego, wraca problem context bloatu.  
**Siła dowodów: spekulacja oparta na źródłach.**

---

## Temat 3: Token budget scheduling — ciągłość pracy przy limitach

### 3.1. Jak wyglądają dokładne limity Anthropic API?

### Co udało się potwierdzić oficjalnie
Anthropic dokumentuje dwa typy limitów:
1. **spend limits** — maksymalny miesięczny koszt na organizację,
2. **rate limits** — maksymalne tempo użycia API.  
**Siła dowodów: praktyczne.**

Rate limits dla Messages API są mierzone jako:
- **RPM** — requests per minute,
- **ITPM** — input tokens per minute,
- **OTPM** — output tokens per minute.  
**Siła dowodów: praktyczne.**

Mechanizm limitowania to **token bucket**, więc capacity jest uzupełniana ciągle, a nie resetowana skokowo.  
**Siła dowodów: praktyczne.**

Oficjalna dokumentacja potwierdza też:
- org-level monthly spend caps per tier,
- automatyczne przejścia tierów wg progów wpłat,
- acceleration limits przy nagłym wzroście ruchu,
- standard account limits teraz obowiązują również dla 1M context na Opus 4.6 / Sonnet 4.6.  
**Siła dowodów: praktyczne.**

### Czego nie udało się potwierdzić
- Nie udało się potwierdzić w oficjalnej dokumentacji API stałych limitów „reset co 5h” ani „weekly quota” dla standardowego Messages API.
- To może wynikać z mieszania pojęć:
  - API rate/spend limits,
  - usage windows Claude Code / subskrypcyjnych planów,
  - enterprise custom limits.  
**Wniosek:** dla researchu o **Anthropic API** bezpieczniej opierać się na RPM/ITPM/OTPM + spend caps + headers, a nie na narracji „5h/weekly”.  
**Siła dowodów: praktyczne.**

### 3.2. Jak odczytywać pozostały budżet programmatycznie?

Anthropic zwraca response headers:
- `retry-after`
- `anthropic-ratelimit-requests-limit`
- `anthropic-ratelimit-requests-remaining`
- `anthropic-ratelimit-requests-reset`
- `anthropic-ratelimit-input-tokens-limit`
- `anthropic-ratelimit-input-tokens-remaining`
- `anthropic-ratelimit-input-tokens-reset`
- `anthropic-ratelimit-output-tokens-limit`
- `anthropic-ratelimit-output-tokens-remaining`
- `anthropic-ratelimit-output-tokens-reset`
- analogiczne headery dla Priority Tier.  
**Siła dowodów: praktyczne.**

Dodatkowe niuanse:
- remaining tokens są zaokrąglane do najbliższego tysiąca,
- ITPM dla większości modeli liczy tylko **uncached input + cache writes**, a nie cache reads,
- `input_tokens` w usage object nie oznacza pełnego inputu przy cachingu; trzeba liczyć:
  - `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`.  
**Siła dowodów: praktyczne.**

Anthropic ma też:
- **Usage and Cost API** przez Admin API,
- monitoring usage/cache w Console,
- telemetry / OTel w Claude Code.  
**Siła dowodów: praktyczne.**

### 3.3. Jakie wzorce throttlingu stosować, żeby nie spalić limitu naraz?

Źródła nie pokazują jednego dominującego „agent framework pattern”, ale z dokumentacji i papers wyłania się spójny zestaw:

#### A. Rate-limit-aware admission control
Zanim agent wystartuje:
- sprawdź headroom RPM / ITPM / OTPM,
- przewidź koszt requestu,
- przyjmij do wykonania tylko tyle prac, ile mieści się w bieżącym budżecie.  
**Siła dowodów: praktyczne + empiryczne.**

AgentRM wprost proponuje rate-limit-aware admission control; Kubernetes APF i AWS fairness dają analogiczne wzorce dla systemów przeciążeniowych.  
**Siła dowodów: empiryczne + praktyczne.**

#### B. Fair queuing / weighted queues
- oddziel kolejki per klasa pracy / per agent / per tenant,
- użyj fair queuing, żeby jeden „głodny” agent nie zagłodził reszty,
- dopuszczaj krótkie bursty, ale z limitowaną kolejką i backpressure.  
**Siła dowodów: empiryczne + praktyczne.**

Justitia pokazuje virtual-time fair queuing dla task-parallel LLM agents; Kubernetes APF i AWS Builders Library pokazują tę samą ideę na systemach produkcyjnych.  
**Siła dowodów: empiryczne + praktyczne.**

#### C. Dependency-aware dispatch
- nie odpalaj wszystkiego round-robin,
- najpierw zadania, które realnie odblokowują kolejne kroki,
- eliminuj false dependencies.  
**Siła dowodów: empiryczne.**

AI Metropolis pokazuje, że śledzenie realnych zależności i out-of-order execution daje 1.3×–4.15× speedup względem global synchronization.  
**Siła dowodów: empiryczne.**

#### D. Work-conserving scheduling
- jeśli istnieje bezpieczna praca do wykonania i budżet nie jest pusty, worker nie powinien bezczynnie czekać,
- ale work-conserving musi być połączony z fair admission control; inaczej zapełnisz system pracą niskiej wartości.  
**Siła dowodów: empiryczne.**

### 3.4. Jak planować pracę, by wykorzystać ~100% budżetu bez przekroczeń?

Najlepsza praktyka z punktu widzenia PM-schedulera to **predykcyjny scheduler z feedback loop z headers**.

#### Minimalny model planowania pojemności
Dla każdej klasy pracy utrzymuj EWMA / rolling stats:
- uncached input tokens / task,
- cache write tokens / task,
- output tokens / task,
- wall-clock latency / task,
- success rate / stall rate.

Następnie w każdej pętli:
1. odczytaj remaining i reset z headers,
2. przelicz headroom do „bezpiecznej przepustowości” na najbliższe okno,
3. przydziel concurrency tylko do poziomu, który mieści się jednocześnie w:
   - RPM,
   - ITPM,
   - OTPM,
   - lokalnym limicie równoległości,
4. zostaw rezerwę na retry / replanning / human escalation.  
**Siła dowodów: spekulacja oparta na źródłach.**

**Wniosek praktyczny**
- **Round-robin bez predykcji kosztu jest zbyt prymitywny.**
- Najlepszy kompromis to:
  - priority classes,
  - predicted token cost,
  - fair queuing,
  - admission control,
  - dynamiczne przeliczanie na podstawie headers.  
**Siła dowodów: empiryczne + praktyczne.**

### 3.5. Prompt caching — jak bardzo zmienia kalkulację?

Bardzo mocno.

Oficjalne fakty:
- default TTL to **5 minut**, odświeżany przy użyciu;
- dostępny jest też **1-hour cache**;
- cache obejmuje pełny prefix promptu;
- cache reads kosztują ułamek ceny base input;
- dla większości modeli cache reads nie liczą się do ITPM.  
**Siła dowodów: praktyczne.**

Anthropic daje wręcz przykład:
- przy limicie **2,000,000 ITPM** i **80% cache hit rate** można efektywnie przetworzyć **10,000,000 total input tokens/min**.  
**Siła dowodów: praktyczne.**

**Implikacja dla schedulera**
- Nie wystarczy mierzyć „tokens/task”.
- Trzeba mierzyć przynajmniej cztery osobne strumienie:
  1. uncached input,
  2. cache creation writes,
  3. cache reads,
  4. output.
- Bez tego scheduler będzie mylnie uznawał duże, ale cache-friendly zadania za „droższe” niż są naprawdę.  
**Siła dowodów: praktyczne + spekulacja.**

### 3.6. Jak mierzyć i raportować zużycie per agent / per task?

Najbardziej sensowny zestaw metryk:

#### Kosztowe
- input cost / task
- output cost / task
- total cost / task
- total cost / agent
- total cost / workflow  
**Siła dowodów: praktyczne.**

#### Tokenowe
- uncached input tokens / task
- cache write tokens / task
- cache read tokens / task
- output tokens / task
- tokens / successful completion
- tokens / verified completion  
**Siła dowodów: praktyczne + spekulacja.**

#### Wydajnościowe
- queue wait time
- execution latency
- throughput (tasks/hour lub verified tasks/hour)
- retry count
- stall count
- TTFT / token latency tam, gdzie to ma znaczenie operacyjne po stronie runtime / serwera.  
**Siła dowodów: empiryczne + praktyczne.**

#### Jakościowe
- pass rate po weryfikacji,
- rate „improper finalization”,
- escalation rate,
- % zadań ukończonych bez udziału człowieka.  
**Siła dowodów: częściowo empiryczne, częściowo spekulacja.**

Anthropic ma do tego narzędzia:
- Usage and Cost API,
- Console usage page,
- Claude Code telemetry przez OTel (cost counter, token counter, API request events, tool decision events).  
**Siła dowodów: praktyczne.**

### 3.7. Graceful degradation, gdy limit się kończy

Najbardziej sensowne wzorce:

1. **Queue remaining work** i nie startuj nowych drogich branchy.  
2. **Reduce parallelism** do poziomu, który mieści się w remaining headroom.  
3. **Prefer tasks with highest unblock / value density**.  
4. **Switch model** na tańszy / szybszy tam, gdzie ryzyko jest akceptowalne.  
5. **Checkpoint + pause** zamiast brute-force retry spam.  
6. **Escalate / notify human** tylko gdy:
   - zadanie ma deadline,
   - wymaga decyzji biznesowej,
   - dalsze czekanie degraduje wartość.  
**Siła dowodów: praktyczne + częściowo empiryczne.**

LangChain ma gotowe middleware dla:
- human-in-the-loop,
- model fallback,
- model call limit,
- tool call limit.  
To nie jest pełny scheduler, ale daje gotowe klocki do graceful degradation.  
**Siła dowodów: praktyczne.**

**Wniosek dla tematu 3**
- W praktyce „token budget scheduling” jest bardziej problemem **systems engineering** niż prompt engineering. Najlepsze wzorce pochodzą dziś głównie z serving/scheduling papers, a nie z samych frameworków agentowych.  
**Siła dowodów: empiryczne + praktyczne.**

---

## Temat 4: Autonomiczna priorytetyzacja — heurystyki i eskalacja

### 4.1. Jakie heurystyki priorytetyzacji pojawiają się w źródłach?

Nie ma jednego standardu „PM heuristic benchmark”, ale z materiału wyłaniają się powtarzalne heurystyki:

#### A. Unblocker-first / dependency-aware
- preferuj zadania, które odblokowują inne,
- nie serializuj sztucznie pracy, jeśli zależności są fałszywe,
- używaj dependency graph / workflow analysis.  
**Siła dowodów: empiryczne.**

AI Metropolis i Kairos wspierają dokładnie ten kierunek: scheduler powinien widzieć zależności i remaining latency, nie tylko FIFO.  
**Siła dowodów: empiryczne.**

#### B. Highest verified value per cost
- zadania z wysoką wartością i niskim przewidywanym kosztem idą wyżej,
- szczególnie jeśli poprawiają stan wspólny (spec, test harness, blocker fix).  
**Siła dowodów: częściowo spekulacja, ale zgodna z praktyką harnessów.**

Anthropicowy wzorzec „wybierz najwyższy priorytet niedokończonej feature z checklisty” jest prostą wersją tej heurystyki.  
**Siła dowodów: praktyczne.**

#### C. Quality-gated priority
- prace, które muszą zostać zweryfikowane zanim system ruszy dalej, dostają wyższy priorytet niż kolejne exploratory subtasks.  
**Siła dowodów: praktyczne.**

Maker-checker i evaluator loops właśnie temu służą.  
**Siła dowodów: praktyczne.**

#### D. Fair-share priority
- jeden agent / tenant / branch nie może monopolizować całego budżetu,
- potrzebny jest limit udziału i fair queuing.  
**Siła dowodów: empiryczne + praktyczne.**

### 4.2. Jak definiować granice autonomii managera?

Najmocniejszy wzorzec w źródłach to **policy-based autonomy boundaries**.

#### Manager może decydować samodzielnie, gdy:
- działanie jest odwracalne,
- koszt jest niski,
- precedens jest znany,
- acceptance criteria są obiektywne,
- failure nie niesie dużego ryzyka.  
**Siła dowodów: praktyczne + spekulacja.**

#### Powinien eskalować do człowieka, gdy:
- działanie jest high-stakes (np. write, payment, external side effect),
- compliance wymaga human approval,
- brak obiektywnego kryterium ukończenia,
- task wszedł w nietypową strefę bez precedensu,
- budżet / deadline / policy threshold zostają przekroczone,
- system wielokrotnie stalluje lub ignoruje błędy.  
**Siła dowodów: praktyczne.**

LangChain HITL daje dokładny model decyzji:
- `approve`
- `edit`
- `reject`  
**Siła dowodów: praktyczne.**

Azure orchestration patterns mówią wprost o approval gates, human reviewers i fallback behavior po iteration cap.  
**Siła dowodów: praktyczne.**

### 4.3. Graceful degradation of autonomy

Najbardziej przekonujący model to **tiered autonomy**:

#### Poziom 0 — full autonomy
- standardowe, odwracalne, niskokosztowe zadania.

#### Poziom 1 — autonomy with verification
- agent działa sam, ale checker / evaluator musi zatwierdzić wynik.

#### Poziom 2 — approval-required
- agent przygotowuje akcję, człowiek approve/edit/reject przed wykonaniem.

#### Poziom 3 — human takes over
- agent zatrzymuje execution i przekazuje stan + rekomendację.  
**Siła dowodów: praktyczne + spekulacja.**

To jest lepsze niż prosty podział „autonomia vs HITL”, bo pozwala płynnie reagować na ryzyko, koszty i niepewność.

### 4.4. Jak manager radzi sobie z repriorytetyzacją w locie?

**Najlepiej potwierdzony wzorzec:**
1. wykryj event (nowy bloker, brak progresu, nowy task, zmiana celu),
2. zaktualizuj shared state / ledger,
3. przelicz plan,
4. ewentualnie przerwij lub zdegraduj inne branch’e,
5. przekaż nowe instrukcje agentom.  
**Siła dowodów: empiryczne + praktyczne.**

Magentic-One robi to przez:
- stall detection,
- powrót do outer loop,
- reflection/self-refinement,
- update task ledger,
- revised plan,
- restart inner loop.  
**Siła dowodów: empiryczne.**

Kairos i AI Metropolis pokazują analogiczny mechanizm po stronie workflow/scheduling:
- priorytet nie jest stały,
- wynika z remaining latency i real dependencies.  
**Siła dowodów: empiryczne.**

### 4.5. Jak unikać „busy work”?

Źródła sugerują kilka bardzo mocnych guardrails:

#### A. Explicit done criteria
- feature checklist,
- sprint contract,
- checker z pass/fail criteria,
- task nie może być „complete”, jeśli nie ma evidence.  
**Siła dowodów: praktyczne + empiryczne.**

#### B. Iteration / call limits
- model call limit,
- tool call limit,
- max iteration limit,
- max stalls before replan.  
**Siła dowodów: praktyczne.**

#### C. No new task without value signal
- nowy agent / branch tylko gdy istnieje:
  - blokada do zdjęcia,
  - brakująca kompetencja,
  - przewidywana poprawa jakości / czasu,
  - albo wymóg weryfikacji.  
**Siła dowodów: spekulacja zgodna z praktyką.**

Azure wprost ostrzega przed dokładaniem agentów bez meaningful specialization i przed group chatem bez obiektywnego completion signal.  
**Siła dowodów: praktyczne.**

#### D. Verify before expand
- przed rozpoczynaniem nowej feature sprawdź, czy poprzedni stan jest zdrowy,
- Anthropic rekomenduje uruchomić podstawowy end-to-end test na początku sesji, zanim agent zacznie nową pracę.  
**Siła dowodów: praktyczne.**

**Wniosek dla tematu 4**
- Najbardziej dojrzały PM nie jest „sprytnym generatorem zadań”, tylko **policy engine + scheduler + verifier router**. Jeśli nie ma jasnych acceptance criteria, ograniczeń kosztowych i triggerów eskalacji, łatwo przechodzi w busy work albo faux-autonomy.  
**Siła dowodów: praktyczne + spekulacja.**

---

## Trade-offy kluczowych decyzji

| Decyzja | Opcja A | Opcja B | Kiedy A | Kiedy B | Główne koszty / ryzyka |
|---|---|---|---|---|---|
| Lifecycle sesji | Jedna długa sesja + compaction | Cykle reset/resume + checkpoint | Gdy model dobrze znosi long context, a task wymaga ciągłości i szybkiego sterowania | Gdy rośnie stall rate, context anxiety, rot albo task trwa wiele godzin / dni | A: drift i zbyt duży implicit state. B: overhead orchestration i handoff |
| Checkpointing | File/memory artifacts | Graph-level durable execution | Gdy ważne jest szybkie „odzyskanie stanu poznawczego” przez następny agent | Gdy ważne jest techniczne wznowienie workflow po crashu/interrupt | A: mniej deterministyczne resume runtime. B: większa złożoność workflow |
| Pamięć managera | Conversation history | Ledger / shared state | Dla krótkich, prostych zadań | Dla zadań wieloetapowych, repriorytetyzacji, recovery | History szybko puchnie; ledger wymaga dyscypliny struktury |
| Scheduler | FIFO / round-robin | Fair + priority + admission control | Przy małej skali i niskim ryzyku | Przy wielu agentach, wspólnym budżecie i nierównych kosztach tasków | FIFO jest proste, ale źle używa budżetu |
| Priorytetyzacja | Value-only | Value + dependency + cost + fairness | Gdy prace są niezależne i podobne kosztowo | Gdy istnieją blokery, shared budget i branch competition | Single-score heurystyki łatwo generują busy work |
| Autonomia | Full autonomy | Tiered autonomy z approval gates | Dla odwracalnych i niskiego ryzyka akcji | Dla high-stakes tools, compliance, niepewności i nowych sytuacji | Full autonomy zwiększa ryzyko kosztów ubocznych |
| Caching | Traktowany jako detal kosztowy | Traktowany jako 1st-class scheduler signal | Gdy prompty są małe i mało powtarzalne | Gdy system ma duże stałe prefixy i wiele podobnych zadań | Ignorowanie cache prowadzi do złych decyzji schedulingowych |
| Replanning | Co stały interwał | Event-driven na sygnałach stuckness | Gdy system jest bardzo prosty | Gdy workflow jest nieregularny i kosztowny | Interwały stałe są łatwe, ale często spóźnione albo zbyt częste |

---

## Otwarte pytania / luki w wiedzy

1. **Brak publicznego, niezależnego benchmarku dla Claude 4.6 / Sonnet 4.6 mierzącego „ile realnie wytrzymuje jedna sesja” na zadaniach PM/orchestration.** Są vendor claims i ogólne benchmarki, ale nie ma mocnego external study dokładnie dla tego przypadku.
2. **Nie znaleziono czystej ablacją „ledger vs sama conversation memory”** w systemie Magentic-One lub podobnym. Publiczne ablację mieszają kilka mechanizmów naraz.
3. **Nie udało się potwierdzić oficjalnie pełnej tabeli per-model, per-tier RPM/ITPM/OTPM w zrenderowanej postaci z dokumentacji webowej** w tym środowisku; oficjalne docs potwierdzają same kategorie limitów, headery i zasady, ale nie udało się niezawodnie wyciągnąć wszystkich liczb tabelarycznych.
4. **Nie udało się potwierdzić w oficjalnej dokumentacji API stałych limitów “co 5h” ani “weekly”** dla standardowego Messages API. Jeśli te okna są ważne projektowo, trzeba je zweryfikować osobno dla konkretnego produktu/planów (API vs Claude Code vs plan użytkownika vs enterprise contract).
5. **Brakuje standardowego benchmarku „PM scheduler quality”** analogicznego do GAIA/WebArena, mierzącego jakość repriorytetyzacji, eskalacji i użycia budżetu.
6. **Wyniki serving papers (Justitia, Kairos, AgentRM, Autellix) są obiecujące, ale dotyczą głównie warstwy runtime/serving**, a nie prompt-level PM agentów; transfer do orchestratora LLM wymaga ostrożności.
7. **Brakuje dobrych publicznych danych o relacji między compaction quality a control quality**: kiedy summary/compaction jeszcze wystarcza, a kiedy trzeba robić twardy reset.

---

## Źródła / odniesienia

### Oficjalne / pierwotne

- [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — główne źródło do initializer/coding agent, `init.sh`, progress file, feature list JSON, one-feature-at-a-time i recovery between sessions.
- [Anthropic — Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) — źródło do porównania context reset vs compaction, trójrolowej architektury planner/generator/evaluator i praktyki continuous session na nowszych modelach.
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — źródło do pojęcia context rot, finite attention budget, hybrid context strategies.
- [Anthropic Docs — Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows) — oficjalne guidance o multi-session state artifacts, compaction i zarządzaniu oknem kontekstowym.
- [Anthropic Docs — Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) — formalny multi-session software development pattern: progress log, feature checklist, startup script reference.
- [Anthropic Docs — Rate limits](https://platform.claude.com/docs/en/api/rate-limits) — oficjalne źródło o RPM/ITPM/OTPM, token bucket, response headers, cache-aware ITPM i spend limits.
- [Anthropic Docs — Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — cache TTL, pricing multipliers, cache semantics, 1h cache, usage fields.
- [Anthropic Docs — Pricing](https://platform.claude.com/docs/en/about-claude/pricing) — 1M context pricing, batch discounts, long context pricing dla starszych modeli.
- [Anthropic Docs — Models overview](https://platform.claude.com/docs/en/about-claude/models/overview) — aktualne modele, context windows i ceny bazowe.
- [Anthropic Docs — Release notes](https://platform.claude.com/docs/en/release-notes/overview) — aktualny status 1M context, compaction API, usage/cost API.
- [Anthropic — Claude Opus 4.6 launch](https://www.anthropic.com/news/claude-opus-4-6) — vendor claim o lepszym long-context retrieval i mniejszym drift.
- [Microsoft Research — Magentic-One paper (PDF)](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/11/Magentic-One.pdf) — źródło do outer/inner ledger loop, ablation 31%, stall threshold i error analysis.
- [LangGraph Docs — Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — checkpointing per step, threads, HITL i fault tolerance.
- [LangGraph Docs — Durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution) — durability modes `exit/async/sync`.
- [LangChain Docs — Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop) — approve/edit/reject i pause/resume execution.
- [LangChain Docs — Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) — model fallback, model/tool call limits, human-in-the-loop.
- [Azure Architecture Center — AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) — maker-checker loops, approval gates, unikanie group chat bez completion criteria, max iteration limit.
- [OpenAI Developers — Run long horizon tasks with Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex/) — plan→implement→validate→repair→update docs loop i rola externalized state.
- [OpenAI Cookbook — Using PLANS.md for multi-hour problem solving](https://developers.openai.com/cookbook/articles/codex_exec_plans/) — living plan document, brak pamięci wcześniejszych planów, explicit executable spec.
- [OpenAI Cookbook — Session memory / context trimming](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory) — trimming session jako formalny pattern zarządzania krótką pamięcią.

### Empiryczne / papers

- [LongCodeBench: Evaluating Coding LLMs at 1M Context Windows](https://arxiv.org/abs/2505.07897) — benchmark długiego kontekstu dla code comprehension i repair, ważny dla pytania o realną opłacalność 1M context.
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) — klasyczny paper o degradacji retrievalu, gdy istotna informacja jest w środku kontekstu.
- [NoLiMa: Long-Context Evaluation Beyond Literal Matching](https://arxiv.org/abs/2502.05167) — benchmark pokazujący, że wiele long-context modeli nadal słabo radzi sobie bez literalnych wskazówek.
- [Justitia: Fair and Efficient Scheduling of Task-parallel LLM Agents](https://arxiv.org/abs/2510.17015) — fair queuing, memory-centric cost model, wyniki o skróceniu completion time przy zachowaniu fairness.
- [Kairos: Low-latency Multi-Agent Serving with Shared LLMs](https://arxiv.org/abs/2508.06948) — workflow-aware priority scheduler i memory-aware dispatcher.
- [AI Metropolis: Scaling LLM Multi-Agent Simulation with Out-of-Order Execution](https://arxiv.org/pdf/2411.03519) — dependency-aware scheduling i eliminacja false dependencies.
- [Throughput-Optimal Scheduling Algorithms for LLM Inference and AI Agents](https://arxiv.org/abs/2504.07347) — argument za work-conserving scheduling jako zasadą projektową.
- [AgentRM: An OS-Inspired Resource Manager for LLM Agent Systems](https://arxiv.org/abs/2603.13110) — rate-limit-aware admission control, MLFQ scheduler, context lifecycle manager.
- [Autellix: An Efficient Serving Engine for LLM Agents as General Programs](https://arxiv.org/abs/2502.13965) — scheduling z awareness program-level context i priorytetyzacją zależną od wcześniej ukończonych wywołań.

### Publiczne implementacyjne ślady / repo issues

- [microsoft/autogen #6599](https://github.com/microsoft/autogen/issues/6599) — publiczny fragment kodu pokazujący walidację progress ledgera jako JSON z `answer`/`reason` i required keys.
- [microsoft/autogen #5127](https://github.com/microsoft/autogen/issues/5127) — potwierdza publiczny interfejs `MagenticOneGroupChat(..., max_turns=..., max_stalls=...)`, przydatny dla triggerów replanu.

## Krótka mapa claim → source

- **Context rot istnieje mimo dużych context windows** → Anthropic context engineering + Lost in the Middle + NoLiMa + LongCodeBench.
- **Hybrid lifecycle (continuous session + artifacts + resets on trouble) jest dziś najsensowniejszy** → Anthropic harnesses + memory tool + LangGraph durable execution.
- **Magentic-One ledger ma dwa poziomy i 5 pytań progress ledgera** → Magentic-One paper + publiczny issue z walidacją JSON.
- **Bez pełnego orchestratora/ledgerów performance spada ~31%** → Magentic-One ablation.
- **Anthropic API scheduler musi patrzeć na RPM/ITPM/OTPM, spend limit i headers** → Anthropic rate limits docs.
- **Prompt caching zmienia efektywną przepustowość o rząd wielkości** → Anthropic rate limits + prompt caching docs.
- **Tiered autonomy / approval gates / maker-checker to najdojrzalszy wzorzec eskalacji** → Azure orchestration patterns + LangChain HITL.
