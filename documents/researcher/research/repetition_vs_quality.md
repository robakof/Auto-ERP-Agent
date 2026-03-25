# Research Results: Powtarzanie słów vs jakość dokumentu — wpływ na LLM

Date: 2026-03-24

Scope note: ten pass optymalizuje breadth over proof. Łączy źródła oficjalne (OpenAI, Anthropic, Google, papers) z ecosystem community (GitHub, Reddit, HN, blogi). To teren częściowo słabo ustandaryzowany; tam, gdzie evidence jest cienkie albo sprzeczne, oznaczam to jawnie.

## TL;DR — 5 High-Signal Directions

- **Samo powtarzanie słów kluczowych nie wygląda na główny mechanizm sterowania.** Znacznie mocniejszy sygnał z official docs i papers to: jasność instrukcji, struktura promptu, przykłady, delimitery i pozycja informacji.
- **„Duch” dokumentu bywa przenoszony implicitnie — ale nie w pełni.** Modele potrafią wyłapać wzorzec z przykładów, tonu i struktury, ale badania nad style imitation pokazują, że subtelny styl i „vibe” nadal są odtwarzane tylko częściowo.
- **Najbardziej obiecujący pattern to nie repetition vs quality, tylko kombinacja:** krótki, dobrze napisany dokument + 1–3 jawne nienegocjowalne zasady + 1–3 canonical examples.
- **Repetition ma sens głównie jako salience tool, nie jako młotek do wszystkiego.** Dublowanie instrukcji na początku i końcu długiego kontekstu, caps dla krytycznej reguły, przypomnienie po failure mode — to ma więcej sensu niż keyword stuffing.
- **Jest punkt nasycenia.** Zbyt dużo tekstu, edge cases, few-shotów albo reminderów może pogarszać wyniki, bo attention budget jest skończony. „Więcej” nie znaczy automatycznie „silniej”.

---

## Mapa terenu

### 1) Powtarzanie słów w promptach — co wiemy, a czego nie wiemy

#### Phase 1: Official ecosystem

- Nie znalazłem oficjalnych vendor guides, które mówiłyby: „powtórz słowo X trzy razy, a model będzie bardziej skupiony”. Oficjalne guidance konsekwentnie promuje **clarity, explicitness, structure, examples, delimiters, placement** zamiast czystego repetition.
- OpenAI sugeruje few-shot jako sposób, by model **implicitnie „pick up” pattern** z przykładów, a Anthropic nazywa przykłady jednym z **najbardziej reliable** sposobów sterowania formatem, tonem i strukturą.
- OpenAI realtime docs dopuszczają **caps/emphasis** dla ważnych reguł. To ważne: oficjalnie wspierana jest **emfaza**, nie ogólne „powtarzaj keyword wiele razy”.
- Anthropic i OpenAI oba sugerują, że przy długim kontekście warto dbać o **rozmieszczenie instrukcji**, a nie tylko o ich treść.

**Evidence strength:** strong

#### Phase 1: Academic / primary research

- Pojawia się świeży sygnał, że **pełne powtórzenie promptu** może pomagać w części ustawień. Paper *Prompt Repetition Improves Non-Reasoning LLMs* raportuje poprawy na wielu benchmarkach dla modeli non-reasoning.
- Ale inny paper, *Asking Again and Again*, raportuje, że **powtarzanie samego pytania** 1x / 3x / 5x nie daje istotnych statystycznie zysków overall.
- To sugeruje ważne rozróżnienie:
  - **repeating the full prompt / second pass over the whole input**
  - vs **powtarzanie jednego pytania / jednego keywordu**
- W praktyce to nie jest ten sam mechanizm. Pierwsze może zwiększać szansę, że model „zobaczy całość jeszcze raz”; drugie może być tylko dodatkowym tokenowym szumem.

**Evidence strength:** moderate

#### Phase 2: Community ecosystem

**Context switch: switching to community ecosystem. Teraz szukam eksperymentów, heurystyk i buzzu, nie endorsementów.**

- Na Reddit i HN regularnie wraca intuicja typu: **„powiedz modelowi, żeby powtórzył pytanie”** albo **„IMPORTANT / MUST działa lepiej niż neutralne sformułowanie”**.
- W community widać też odróżnienie między:
  - „reminders” dodawanymi po zidentyfikowanym failure mode,
  - a „keyword chanting” bez testów.
- Prompt-tuning playbook (community GitHub, ~900 stars) wprost opisuje workflow: zacznij od prostego promptu, a potem dodawaj **konkretne reminders** po zaobserwowanych błędach, pojedynczo.
- Wątek community jest więc bardziej subtelny niż „powtarzaj więcej”: **powtarzaj tylko to, co naprawia konkretną porażkę**.

**Evidence strength:** exploratory do moderate

#### Stan mapy

- **Co wiemy:** repetition nie jest dobrze ugruntowaną „silver bullet”. Czasem pomaga, ale głównie w specyficznych setupach.
- **Czego nie wiemy:** nie znalazłem mocnych badań porównujących wprost: „1x minimalistyczna instrukcja niosąca ducha” vs „10x to samo słowo-klucz”.
- **Luka:** brak standardowego benchmarku na „semantic vibe transfer” i brak stabilnej teorii, kiedy repetition przechodzi z salience w noise.

---

### 2) Jakość dokumentu vs explicit instructions

#### Phase 1: Official ecosystem

- Oficjalne docs mocno wspierają tezę, że **dobrze napisany dokument ma znaczenie sam w sobie**:
  - jasne sekcje,
  - delimitery / XML / markdown headers,
  - konkretne oczekiwania,
  - canonical examples,
  - minimal high-signal context.
- Anthropic wręcz rekomenduje: zacznij od **minimal prompt**, potem dodawaj tylko to, co poprawia konkretne failure modes.
- To jest bardzo bliskie hipotezie, że **„duch” dokumentu lepiej przenosi jakość i spójność niż redundantne hasła**.
- OpenAI/Anthropic/Google konsekwentnie preferują przykład i strukturę nad verbose prose.

**Evidence strength:** strong

#### Phase 1: Academic / research

- Papers o in-context learning pokazują, że modele potrafią **wyłapywać wzorce z przykładów** i że jakość / dobór przykładów ma duży wpływ na wynik.
- Badania nad style imitation pokazują jednak, że **implicit style transfer ma limit**. LLM potrafi częściowo przybliżyć styl, ale subtelny, codzienny styl autora nadal często rozmywa się do „average generic tone”.
- W świeżych badaniach o style control w code generation widać ciekawy pattern:
  - **examples** dobrze ustawiają początkową formę,
  - **concise explicit instructions** lepiej utrzymują styl w czasie,
  - **combined** daje najlepszy efekt.

**Evidence strength:** moderate

#### Phase 2: Community ecosystem

- Community prompt engineers bardzo często intuicyjnie mówią: **„show the vibe, don’t describe the vibe”**.
- Blogi i repozytoria promptingowe często promują zasadę: zamiast pisać „bądź minimalistyczny”, lepiej **pokaż minimalistyczny output** albo daj zwięzły, dobrze skonstruowany prompt, który sam brzmi minimalistycznie.
- Jednocześnie community ostrzega, że czasem **„messy prompt” może outperformować „clean prompt”** na konkretnym modelu — czyli jakość dokumentu nie jest abstrakcyjną cnotą; musi być testowana na realnym checkpointcie.

**Evidence strength:** exploratory do moderate

#### Stan mapy

- **Co wiemy:** dokument jako artefakt stylu prawdopodobnie działa, szczególnie gdy zawiera spójny ton, strukturę i przykłady.
- **Czego nie wiemy:** jak duża część „ducha” pochodzi z samej stylistyki promptu, a jaka z jawnych instrukcji.
- **Luka:** mało badań A/B typu „minimalistyczny dokument bez słowa minimalizm” vs „chaotyczny dokument z 10x minimalizm”.

---

### 3) Show vs Tell w kontekście LLM

#### Phase 1: Official ecosystem

- To jest obszar z najsilniejszym sygnałem. OpenAI, Anthropic i Google są bardzo zgodni: **examples work**.
- Anthropic mówi wprost, że przykłady są jedną z najbardziej niezawodnych metod sterowania outputem.
- OpenAI prompt guides również wskazują few-shot jako mechanizm, dzięki któremu model „łapie wzorzec”.
- Anthropic context engineering idzie jeszcze dalej: zamiast laundry list of edge cases, lepiej dobrać **diverse, canonical examples**.

**Evidence strength:** strong

#### Phase 1: Academic / primary research

- Paper *Show, Don’t Tell* pokazuje, że **demonstrated feedback** może przewyższać prompt-only alignment oraz kilka innych baseline’ów przy personalizacji.
- Papers o in-context examples pokazują, że jakość i dobór przykładów mają duży wpływ na wynik.
- W pracy o stylu w multi-turn code generation examples ustawiają „form”, a instrukcje stabilizują „discipline”; combined działa najlepiej.

**Evidence strength:** strong do moderate

#### Phase 2: Community ecosystem

- Community od dawna operuje heurystyką: **„don’t tell the model to be great; show what great looks like.”**
- HN/blogi regularnie wskazują, że role typu „you are an expert” są słabsze niż dobrze dobrany kontekst, sample phrases lub przykład docelowego outputu.
- Duże community repos (DAIR Prompt Engineering Guide ~72.2k stars; Awesome Prompt Engineering ~5.6k stars) wzmacniają ten pattern: examples, templates, decomposition, delimiters, output schemas.

**Evidence strength:** moderate

#### Stan mapy

- **Co wiemy:** „show vs tell” działa dla wielu form steeringu.
- **Czego nie wiemy:** kiedy examples stają się zbyt kosztowne tokenowo i kiedy ich styl zaczyna nadmiernie „zakotwiczać” model.
- **Luka:** mało badań porównujących „example only” vs „style-consistent prose only” na zadaniach nieformalnych, nie tylko coding / classification.

---

### 4) Attention, salience i pozycja w dokumencie

#### Phase 1: Official ecosystem

- OpenAI i Anthropic sugerują, że **pozycja instrukcji** ma znaczenie, zwłaszcza w long context.
- OpenAI GPT-4.1 guide zaleca, by przy długim kontekście umieszczać instrukcje **na początku i końcu** dostarczonego kontekstu; jeśli mają być tylko raz, lepiej wyżej niż niżej.
- Anthropic long-context best practices sugerują: duże dokumenty u góry, query na końcu; XML i wyraźne sekcje pomagają ograniczać misinterpretation.
- OpenAI realtime docs dopuszczają **capitalization** do wzmacniania ważnych reguł.

**Evidence strength:** strong

#### Phase 1: Academic / primary research

- *Lost in the Middle* daje bardzo mocny sygnał: informacje na początku i końcu są zwykle wykorzystywane lepiej niż w środku.
- *Attention Instruction* sugeruje, że zwykłe wskazówki pozycyjne nie zawsze działają, ale **semantyczne / absolutne wskazówki uwagowe** mogą poprawiać attention do konkretnego fragmentu.
- *Order Effect* i *POSIX* pokazują, że LLM-y są wrażliwe na prompt template i kolejność elementów. Nawet drobne różnice w układzie mogą wpływać na jakość.

**Evidence strength:** strong do moderate

#### Phase 2: Community ecosystem

- Community prompt builders bardzo często dublują krytyczne constraints właśnie dlatego, że **nie ufają środkowi promptu**.
- W agent tooling rośnie moda na „context engineering”: sekcje, delimitery, selektywne retrieval, notes, minimal token footprint. Repo `context-engineering-kit` (~703 stars, 262 commits) jest sygnałem adopcji tego kierunku.
- Buzz wyraźnie przesuwa się z „magicznych fraz” do **salience architecture**: co pokazać, gdzie, jak odseparować, jak skrócić.

**Evidence strength:** moderate

#### Stan mapy

- **Co wiemy:** jeśli chcesz, by model coś naprawdę „zauważył”, często lepiej zmienić pozycję i strukturę niż liczbę powtórzeń.
- **Czego nie wiemy:** które techniki salience najlepiej generalizują między modelami.
- **Luka:** mało vendor-level benchmarków typu bold vs caps vs headings vs duplication.

---

### 5) Prompt engineering best practices — repetition vs quality

#### Phase 1: Official ecosystem

- Official docs są dość zgodne:
  - **bądź clear i direct**,
  - używaj **structured sections**,
  - dawaj **few-shot examples**,
  - testuj **placement**,
  - trzymaj context **tight**, nie bloated,
  - nie zakładaj, że model „sam się domyśli”.
- Nie ma równoległej, równie silnej oficjalnej linii typu: „repetition is your main lever”.
- To samo sugeruje emerging terminologia: mniej „prompt engineering jako copywriting”, bardziej **context engineering** jako projektowanie salience i retrievalu.

**Evidence strength:** strong

#### Phase 1: Academic / primary research

- Sensitivity papers pokazują, że prompting jest bardzo wrażliwe na szczegóły template’u.
- Few-shot pomaga, ale może mieć **diminishing returns**, a czasem wręcz szkodzić przy over-promptingu.
- Prompting pozostaje mocno **empirical**: te same ruchy nie działają identycznie na wszystkich modelach i zadaniach.

**Evidence strength:** moderate

#### Phase 2: Community ecosystem

- Community heurystyki są zaskakująco zbieżne z oficjalnymi:
  - zaczynaj prosto,
  - nie spamuj modelu detalami bez potrzeby,
  - gdy „letter” nie łapie „spirit”, dodaj examples,
  - dodawaj reminders po realnych błędach,
  - trzymaj prompt maintainable.
- W community żyje też mocne przekonanie, że prompting jest częściowo „alchemy”, czyli że lokalne hacki potrafią działać mimo braku teorii. To nie jest downgrade, tylko realistyczny opis stanu praktyki.

**Evidence strength:** moderate

#### Stan mapy

- **Co wiemy:** best practices przesuwają się w stronę quality + structure + examples + evaluation.
- **Czego nie wiemy:** czy da się zbudować uniwersalny ranking technik steeringu niezależny od modelu.
- **Luka:** niewiele bezpośrednich head-to-head benchmarków repetition vs document quality.

---

### 6) Emerging patterns: vibe-based prompting, context engineering, „wyczuwanie intencji”

#### Phase 1: Official ecosystem

- Oficjalne źródła rzadko używają języka „vibe-based prompting”, ale coraz częściej używają pojęć bliskich temu problemowi: persona, style steering, prompt personalities, context engineering.
- OpenAI prompt personality guides traktują ton, charakter i styl odpowiedzi jako sterowalne przez odpowiednio zaprojektowane instrukcje.
- Anthropic przesuwa rozmowę z samego promptu na **szerszy kontekst, retrieval i organizację informacji**.

**Evidence strength:** strong

#### Phase 2: Community ecosystem

- „Vibe prompting” jest realnym community termem, ale na razie bardziej jako buzzword niż twardo zdefiniowana technika.
- Część community używa go pozytywnie: szybkie, intuicyjne ustawianie kierunku. Inna część ustawia go jako kontrast do bardziej rygorystycznego **spec-driven / context-engineering** podejścia.
- Sygnał z blogów i repos: dla lekkich zadań „vibe” bywa wystarczający; dla jakości krytycznej rośnie presja na **examples, specs, evals, structured context**.

**Evidence strength:** exploratory

#### Stan mapy

- **Co wiemy:** model potrafi „wyczuć intencję” z kontekstu częściej, niż chcieliby minimaliści formalizmu.
- **Czego nie wiemy:** gdzie kończy się realna implicit steering, a zaczyna projekcja użytkownika.
- **Luka:** brak stabilnej metody mierzenia „vibe transfer”.

---

## Hipotezy

### H1. „Duch” dokumentu jest przenoszony bardziej przez **strukturę + examples + ton całości** niż przez czyste keyword repetition.

- Uzasadnienie: official docs i sporo badań mocniej wspierają few-shot, structure, delimiters i placement niż powtarzanie słów.
- Kontrargument: w części setupów pełne powtórzenie promptu pomaga, więc repetition nie jest zerowym sygnałem.

**Evidence strength:** strong

### H2. Powtarzanie działa głównie jako **salience amplifier**, ale tylko do pewnego punktu.

- Uzasadnienie: caps, dublowanie instrukcji na początku/końcu, reminder po failure mode mają sens; nadmiar tokenów zużywa attention budget.
- Kontrargument: próg nasycenia jest model- i task-dependent.

**Evidence strength:** moderate

### H3. „Show don’t tell” jest lepsze niż „tell don’t show” wtedy, gdy chcesz przekazać **format, styl, ton lub spirit**, a nie tylko pojedynczą regułę logiczną.

- Uzasadnienie: examples i demonstrated feedback są bardzo mocne w steeringu stylu/formatu.
- Kontrargument: same examples nie zawsze utrzymują zachowanie w dłuższym przebiegu; explicit directives stabilizują.

**Evidence strength:** strong

### H4. Najlepszy pattern to zwykle **kombinacja implicit i explicit**.

- Praktyczna postać:
  - dokument sam brzmi tak, jak ma brzmieć output,
  - zawiera 1–3 jawne constraints,
  - ma 1–3 canonical examples,
  - kluczowe reguły są w miejscach wysokiej salience.
- To jest zgodne z badaniami style-control i z praktyką vendor/community.

**Evidence strength:** moderate do strong

### H5. „Vibe-based prompting” jest realne jako zjawisko praktyczne, ale bez dobrego eval loop łatwo je przecenić.

- Uzasadnienie: community realnie tego używa, ale bardziej jako heurystyki niż naukę.
- Kontrargument: bez benchmarku łatwo pomylić prawdziwy steering z pojedynczym lucky runem.

**Evidence strength:** exploratory

---

## Wzorce z praktyki — co robią inni

### Pattern 1: Minimal prompt + reminders po failure mode

- Start od najprostszego promptu.
- Gdy model zawodzi, dodać jeden reminder adresujący konkretną porażkę.
- Nie dodawać 10 zasad na zapas.

**Kto to robi:** Anthropic context engineering, community `prompt-tuning-playbook`.

**Evidence strength:** strong (official) + moderate (community)

### Pattern 2: Example-driven steering zamiast abstrakcyjnych przymiotników

- Zamiast pisać „bądź minimalistyczny / elegancki / precyzyjny”, pokazać 1–3 fragmenty lub sample outputs, które ucieleśniają ten styl.
- Często dodaje się też anti-example albo krótkie contrastive pair.

**Kto to robi:** Anthropic prompting docs, OpenAI docs, liczne prompt repos, blogi.

**Evidence strength:** strong

### Pattern 3: Krytyczne rzeczy duplikowane w miejscach wysokiej salience

- Najważniejsze constraints trafiają:
  - do system promptu,
  - do sekcji output contract,
  - czasem na początek i koniec długiego kontekstu.
- To nie jest keyword stuffing; to raczej **architected repetition**.

**Kto to robi:** official long-context guidance, agent prompts, enterprise templates.

**Evidence strength:** strong do moderate

### Pattern 4: Structure beats prose mass

- Sekcje, nagłówki, XML, delimitery, jawny output format.
- Community i vendorzy są tu zgodni: dobrze odseparowany prompt zwykle wygrywa z „ładnym akapitem o wszystkim”.

**Kto to robi:** OpenAI, Anthropic, Google, duże prompt guides.

**Evidence strength:** strong

### Pattern 5: Few-shot only when the letter misses the spirit

- Community playbook trafnie to nazywa: few-shot jest szczególnie przydatny, gdy literalna instrukcja nie łapie ducha zadania.
- To dobrze mapuje Twój problem badawczy: jeśli chcesz przenieść „minimalizm”, przykłady mogą działać lepiej niż samo słowo „minimalizm”.

**Evidence strength:** moderate

### Pattern 6: Vibe prompting for ideation, context engineering for reliability

- W lekkiej eksploracji ludzie używają bardziej miękkiego, intuicyjnego promptowania.
- Gdy liczy się powtarzalna jakość, przechodzą na structured context, specs, test cases i evals.

**Evidence strength:** exploratory do moderate

---

## Otwarte pytania

- Czy istnieje stabilny threshold, po którym powtarzanie keywordu przechodzi z helpful salience w noise? Nie znalazłem uniwersalnej odpowiedzi.
- Jak rozdzielić wpływ **stylu dokumentu** od wpływu **semantycznej treści instrukcji**? Brakuje dobrych head-to-head papers.
- Czy „duch” jest głównie przenoszony przez few-shot examples, czy przez samą prozę i strukturę promptu? Dane sugerują „oba”, ale proporcje są niejasne.
- Jak bardzo wnioski zależą od typu modelu: reasoning vs non-reasoning, open-weight vs frontier API?
- Czy salience lepiej zwiększa: caps, duplication, headings, XML, czy placement? Oficjalne docs sugerują kilka naraz, ale nie ma jednego benchmarku porównawczego.
- Searched for direct vendor studies comparing **minimalist document quality vs repeated keyword count**: **not found**.
- Searched for robust research specifically on **"vibe-based prompting"** as a formally defined technique: **not found**; mainly buzz, tooling, blog discourse.

---

## Rekomendacje wstępne

> To nie jest final fit-evaluation, tylko exploratory heuristics: co warto próbować.

1. **Nie traktuj repetition jako głównego lewara.** Najpierw dopracuj strukturę, sekcje, delimitery, output contract i placement.
2. **Dla „ducha dokumentu” preferuj show over tell.** Jeśli chcesz minimalizmu, pokaż minimalistyczny dokument / output, zamiast tylko powtarzać słowo „minimalizm”.
3. **Dodaj 1–3 explicit anchors.** Przykład:
   - „Pisz oszczędnie.”
   - „Nie dodawaj ozdobników.”
   - „Preferuj krótkie akapity i tylko niezbędne listy.”
4. **Duplikuj tylko rzeczy krytyczne.** Nie cały prompt. Raczej: jedna reguła w sekcji zasad + przypomnienie przy output contract, ewentualnie caps dla jednego twardego constraintu.
5. **W długim kontekście graj pozycją.** Najważniejsze constraints umieszczaj na początku i/lub końcu, nie zakopuj ich w środku.
6. **Few-shot traktuj jako nośnik ducha.** Gdy instrukcja nie łapie vibe’u, dodaj 1–3 canonical examples zamiast 10 nowych przymiotników.
7. **Zakładaj diminishing returns.** Każdy nowy token powinien mieć pracę do wykonania. Jeśli kolejna reguła nie naprawia konkretnego błędu, prawdopodobnie tylko zwiększa koszt i ryzyko rozmycia.
8. **Testuj na konkretnym modelu.** To obszar silnie empiryczny. Ten sam prompt może zachowywać się inaczej między modelami i wersjami.

---

## Sources

### Official ecosystem / vendor docs

- OpenAI — Prompt engineering guide  
  https://developers.openai.com/api/docs/guides/prompt-engineering/
- OpenAI — GPT-4.1 Prompting Guide  
  https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide
- OpenAI — Realtime prompting guide  
  https://developers.openai.com/api/docs/guides/realtime-models-prompting
- OpenAI — Prompt Personalities  
  https://developers.openai.com/cookbook/examples/gpt-5/prompt_personalities
- OpenAI — GPT-5.1 Prompting Guide  
  https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-1_prompting_guide
- OpenAI — GPT-5.2 Prompting Guide  
  https://developers.openai.com/cookbook/examples/gpt-5/gpt-5-2_prompting_guide
- OpenAI Help Center — Key guidelines for writing instructions for custom GPTs  
  https://help.openai.com/fr-ca/articles/8554397
- Anthropic — Claude prompting best practices  
  https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Anthropic — Effective context engineering for AI agents  
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Google — Gemini API prompt design strategies  
  https://ai.google.dev/gemini-api/docs/prompting-strategies
- Google Cloud — Vertex AI prompt design strategies  
  https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/prompt-design-strategies

### Academic / research papers

- Lost in the Middle: How Language Models Use Long Contexts  
  https://arxiv.org/html/2307.03172v1
- Attention Instruction: Amplifying Attention in the Middle via Prompting  
  https://arxiv.org/html/2406.17095v1
- Prompt Repetition Improves Non-Reasoning LLMs  
  https://arxiv.org/html/2512.14982v1
- Asking Again and Again: Exploring LLM Robustness to Repeated Questions  
  https://arxiv.org/html/2412.07923v3
- Question-Analysis Prompting Improves LLM Performance in Reasoning Tasks  
  https://arxiv.org/abs/2407.03624
- POSIX: A Prompt Sensitivity Index For Large Language Models  
  https://arxiv.org/html/2410.02185v2
- The Order Effect: Investigating Prompt Sensitivity to Input Order in LLMs  
  https://arxiv.org/html/2502.04134v2
- The Few-shot Dilemma: Over-prompting Large Language Models  
  https://arxiv.org/html/2509.13196v1
- What Makes Good In-Context Examples for GPT-3?  
  https://openreview.net/forum?id=HzkvBbbiml
- Show, Don’t Tell: Aligning Language Models with Demonstrated Feedback  
  https://arxiv.org/html/2406.00888v1
- Catch Me If You Can? Not Yet: LLMs Still Struggle to Imitate the Implicit Writing Styles of Everyday Authors  
  https://arxiv.org/html/2509.14543v1
- Show and Tell: Prompt Strategies for Style Control in Multi-Turn LLM Code Generation  
  https://arxiv.org/html/2511.13972v1
- StyleAdaptedLM: Enhancing Instruction Following Models with Efficient Stylistic Transfer  
  https://arxiv.org/html/2507.18294v1
- Controlling Chat Style in Language Models via Single-Direction Editing  
  https://arxiv.org/html/2603.03324v1
- From Prompts to Templates: A Systematic Prompt Template Analysis for Real-world LLMapps  
  https://arxiv.org/html/2504.02052v2

### Community ecosystem

- DAIR Prompt Engineering Guide (repo, high adoption)  
  https://github.com/dair-ai/prompt-engineering-guide
- DAIR Prompt Engineering Guide — prompts intro page  
  https://github.com/dair-ai/Prompt-Engineering-Guide/blob/main/guides/prompts-intro.md
- Awesome Prompt Engineering (repo)  
  https://github.com/promptslab/awesome-prompt-engineering
- Prompt Tuning Playbook (repo)  
  https://github.com/varungodbole/prompt-tuning-playbook
- Context Engineering Kit (repo)  
  https://github.com/NeoLabHQ/context-engineering-kit
- Hacker News — Prompt engineering discussion  
  https://news.ycombinator.com/item?id=38657029
- Hacker News — discussion around OpenAI prompt engineering examples  
  https://news.ycombinator.com/item?id=38657591
- Reddit / r/LocalLLaMA — Prompt Repetition Improves Non-Reasoning LLMs  
  https://www.reddit.com/r/LocalLLaMA/comments/1qeuh0z/prompt_repetition_improves_nonreasoning_llms_a/
- Reddit / r/LocalLLaMA — “Repeat the Question” observation  
  https://www.reddit.com/r/LocalLLaMA/comments/1cvpjxu/tell_the_llm_to_repeat_the_question_an/
- Haskell for all — Prompting 101: Show, don’t tell  
  https://haskellforall.com/2026/01/prompting-101-show-dont-tell
- DEV Community — From Vibe Prompting to Context Engineering  
  https://dev.to/drguthals/working-effectively-with-claude-from-vibe-prompting-to-context-engineering-for-technical-content-46gl

