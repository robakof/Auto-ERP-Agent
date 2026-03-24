# Research: najlepsze praktyki pisania promptów w systemach wieloagentowych

## 1. Kluczowe wzorce (top 5–7 praktyk z uzasadnieniem)

### 1. Rozbij prompt na warstwy, nie trzymaj wszystkiego w jednym „dokumencie roli”
**Rekomendacja:** traktuj prompt jako złożenie kilku warstw:
1. **shared base** – niezmienne zasady operacyjne wspólne dla wszystkich agentów,
2. **role block** – zakres odpowiedzialności, narzędzia, kryteria sukcesu danej roli,
3. **phase/workflow block** – tylko aktualna faza procesu,
4. **domain block** – wiedza dziedzinowa dobrana do konkretnego zadania,
5. **runtime context** – stan zadania, artefakty wejściowe, wyniki poprzednich kroków.

**Dlaczego:** to dokładnie odpowiada temu, jak produkcyjne systemy agentowe zaczynają wyglądać w praktyce. LangChain Deep Agents składa prompt z kilku części: custom system prompt, base agent prompt, prompt pamięci, prompt skills, promptów narzędzi i runtime contextu. Claude Code ma nie jeden prompt, tylko wiele warunkowo dokładanych promptów, osobne prompty subagentów i osobne opisy narzędzi. OpenAI/Codex idzie w stronę łańcucha instrukcji: globalne AGENTS.md + projektowe AGENTS.md + lokalne override’y.  
**Implikacja dla Ciebie:** migracja do `prompts` w SQLite jest dobrym kierunkiem; trzymaj bloki osobno i składaj je per `rola × faza × typ zadania`.

---

### 2. Minimalny shared base, maksimum reguł przenieś do bloków wywoływanych warunkowo
**Rekomendacja:** w shared base zostaw tylko to, co musi obowiązywać zawsze:
- eskalacja,
- logowanie,
- format wpisów do DB,
- zasady bezpieczeństwa i granice uprawnień,
- ogólna definicja „done”.

Całą resztę (workflow, SQL rules, ERP conventions, specyficzne wyjątki) ładuj tylko wtedy, gdy są potrzebne.

**Dlaczego:** Anthropic wprost rekomenduje dążyć do „minimal set of information that fully outlines expected behavior”, a OpenAI sugeruje prompt templates zamiast mnożenia wielkich promptów dla każdego use case’u. W praktyce wielki prompt pogarsza salience, utrudnia debugowanie i bardzo komplikuje ewaluację regresji.

---

### 3. Krytyczne gate’y zapisuj jako stan i checklistę maszynową, nie tylko prose
**Rekomendacja:** warunki wejścia/wyjścia z fazy powinny istnieć w dwóch formach:
1. **w promptcie** – krótka instrukcja decyzyjna,
2. **w stanie/artefakcie** – jawne pola typu `entry_checks_passed`, `required_artifacts_present`, `phase_exit_status`, `escalation_required`.

Najlepiej trzymaj to w DB lub JSON, nie wyłącznie w markdownzie.

**Dlaczego:** Anthropic w opisie harnessu dla long-running agents pokazuje praktykę, w której pierwszy agent tworzy ustrukturyzowane artefakty stanu, a kolejne sesje pracują inkrementalnie. Co ważne, ich zespół doszedł do tego, że JSON był bezpieczniejszy od Markdownu dla takich stanów – model rzadziej go „przepisuje kreatywnie”. OpenAI w przykładzie multi-agent workflow z Project Managerem pokazuje gating logic między agentami opartą o istnienie artefaktów przed handoffem.  
**Implikacja:** „Czy mogę przejść dalej?” nie powinno zależeć od pamiętania 17 linijek w środku promptu; powinno wynikać z jawnego stanu.

---

### 4. Specjalizuj agentów po granicach decyzji i narzędzi, nie po nazwach stanowisk
**Rekomendacja:** nowego agenta twórz wtedy, gdy:
- ma własny zestaw narzędzi lub danych,
- ma inny success criterion,
- ma inny model koszt/jakość,
- ma inną logikę eskalacji,
- obecny prompt zaczyna przypominać drzewo if-then-else.

**Dlaczego:** OpenAI zaleca maksymalnie wykorzystać pojedynczego agenta, ale dzielić system wtedy, gdy prompty robią się pełne warunków i agent myli narzędzia. LangGraph podkreśla, że grupowanie odpowiedzialności i narzędzi poprawia wyniki, a osobne prompty/few-shoty per agent ułatwiają ewaluację.  
**Praktycznie:** u Ciebie podział „Wykonawca → Developer → Metodolog” jest sensowny tylko wtedy, gdy każdy poziom ma realnie inne: wejścia, narzędzia, output i kryterium zakończenia.

---

### 5. Opis delegacji trzymaj oddzielnie od pełnego promptu roli
**Rekomendacja:** dla każdego agenta trzymaj krótki „routing descriptor” (2–6 zdań):
- kiedy go wywołać,
- kiedy go nie wywoływać,
- jaki artefakt zwraca,
- jakie są warunki handoffu.

**Dlaczego:** Claude Code używa osobnego pola `description`, które służy do automatycznej delegacji; body pliku jest dopiero system promptem. To bardzo ważny wzorzec: prompt do wykonywania zadania i prompt/opis do routingu to nie to samo.  
**Implikacja:** w Twojej DB dodaj osobne kolumny np. `routing_description` i `execution_prompt`. To zmniejsza ryzyko, że orkiestrator wybiera agenta po nieistotnych szczegółach zakopanych w długim promptcie.

---

### 6. Przykłady dawaj selektywnie i blisko reguły, którą mają „zapiec”
**Rekomendacja:** few-shoty stosuj tylko dla:
- trudnych decyzji granicznych,
- formatów odpowiedzi,
- krytycznych reguł narzędziowych,
- typowych błędów historycznych.

Nie wrzucaj 10 przykładów „na wszelki wypadek”.

**Dlaczego:** OpenAI zaleca zaczynać zero-shot i dopiero potem dodawać few-shot, a przykłady muszą być zgodne z instrukcjami. Dla skomplikowanych narzędzi OpenAI rekomenduje osobny `# Examples` section w system prompt, zamiast pchania przykładów do opisu narzędzia. Anthropic podobnie zaleca start od minimalnego promptu i dokładanie instrukcji oraz przykładów dopiero na podstawie rzeczywistych failure modes.  
**Implikacja:** dla SQL nie trzymaj 30 zasad i 15 przykładów inline; trzymaj mały zestaw „always-on”, a przykłady doładowuj tylko dla konkretnego patternu.

---

### 7. Prompt traktuj jak asset produkcyjny: wersja, test, rollout, rollback
**Rekomendacja:** każdy blok promptu powinien mieć:
- `prompt_id`,
- `version`,
- `status` (`draft/staging/prod/deprecated`),
- `compatible_models`,
- `scope_tags` (`role=developer`, `phase=analysis`, `domain=sql`),
- `eval_suite_version`,
- `effective_from`,
- `replaced_by`.

**Dlaczego:** OpenAI zaleca pinowanie snapshotów modeli i budowę evali przy każdej zmianie promptu/modelu. LangSmith, MLflow Prompt Registry i promptfoo pokazują ten sam trend: prompty przestają być stringami w kodzie, a stają się wersjonowanymi assetami z quality gates.  
**Implikacja:** nie porównuj „Developer prompt v3” z „v4” intuicyjnie – porównuj je przez eval suite i loguj, która wersja promptu była użyta w każdej sesji.

---

## 2. Salience i degradacja — co mówi literatura/prakseologia

### Co jest dobrze potwierdzone
Najmocniejszy wynik akademicki to **„Lost in the Middle”**: modele radzą sobie najlepiej, gdy ważna informacja jest na początku lub końcu kontekstu, a wyraźnie gorzej, gdy kluczowy fragment ląduje w środku. To dotyczy także modeli reklamowanych jako long-context.

### Czego nie znalazłem
Nie znalazłem wiarygodnej, powtarzalnej reguły typu „po 250 liniach agent zaczyna ignorować zasady”. Praktyka branżowa i literatura są zgodne raczej co do tego, że **problemem nie jest sama długość, tylko konkurencja o uwagę**:
- środek promptu jest mniej salience,
- konfliktujące instrukcje zwiększają chaos,
- zbyt wiele podobnych narzędzi lub reguł utrudnia wybór,
- nieistotna wiedza dziedzinowa „zanieczyszcza” bieżące zadanie.

### Co zwiększa salience w praktyce
1. **Jawne sekcje** (`# Role`, `# Rules`, `# Workflow`, `# Output`, `# Examples`) albo XML tags.  
2. **Krótkie reguły w formie afirmatywnej**, nie zawoalowane zakazy.  
3. **Krytyczne reguły na krawędziach promptu** – na początku jako „governing rules” i na końcu jako „final checklist”.  
4. **Reguły zdeterminowane przez stan** – np. zamiast „zawsze sprawdź artefakty”, pole `required_artifacts_missing=true`.  
5. **Cytowanie/przywoływanie źródła przed decyzją** – Anthropic dla zadań long-context rekomenduje najpierw wyciągać relewantne cytaty z dokumentów, a dopiero potem wykonywać zadanie.

### Jak formatować gate’y workflow
Najskuteczniejszy wzorzec dla agentów operacyjnych nie wygląda jak „opis procesu”, tylko jak **mikro-kontrakt fazy**:

```text
PHASE: schema_design

ENTRY CONDITIONS
- business_requirements_confirmed = true
- source_tables_profiled = true

YOU MUST NOT CONTINUE IF
- any required field is unknown
- schema conflict is unresolved

REQUIRED OUTPUTS
- proposal.sql
- migration_notes.md
- db.backlog item status updated

EXIT CHECK
Return JSON:
{
  "phase_complete": true|false,
  "missing_inputs": [...],
  "artifacts_created": [...],
  "needs_escalation": true|false,
  "next_phase": "..."
}
```

To jest lepsze niż długi prose workflow z trzeciego akapitu strony 4, bo:
- jest lokalnie czytelne,
- łatwo zewaluować,
- łatwo sparsować,
- daje twarde stop conditions.

### Ważny niuans
OpenAI zauważa, że przy konfliktach GPT-4.1 ma tendencję do podążania za instrukcją bliżej końca promptu. To nie znaczy, że wszystko trzeba wkładać na koniec. Lepszy wzorzec to:
- **na początku**: konstytucja / shared invariants,
- **w środku**: bieżący materiał i szczegóły,
- **na końcu**: aktualna instrukcja wykonawcza + checklista wyjścia.

---

## 3. Dynamiczne prompty — wzorce i trade-offy

### Najlepszy wzorzec dla Twojego use case’u
Nie „jeden wielki prompt” i nie „wszystko dynamiczne”, tylko **hybryda**:

#### A. Always-on base
Krótki blok ładowany zawsze:
- zasady eskalacji,
- format wpisów do DB,
- ogólne bezpieczeństwo,
- definicja odpowiedzialności i ograniczeń,
- standard błędu/niepewności.

#### B. Role overlay
Blok roli:
- cel roli,
- dopuszczalne działania,
- niedozwolone działania,
- expected artifacts,
- routing/handoff criteria.

#### C. Phase overlay
Tylko dla aktualnej fazy:
- wejścia,
- kroki,
- gate’y,
- warunki wyjścia,
- checklista.

#### D. Retrieved domain pack
Na żądanie:
- tylko te zasady SQL/schema/ERP, które są relewantne dla aktualnego zadania,
- 1–3 przykłady graniczne,
- ewentualne wyjątki.

#### E. Runtime state
- backlog item,
- inbox message,
- ostatnie decyzje,
- poprzednie artefakty,
- known issues / prior fixes.

### Dlaczego to działa
To jest zgodne z kilkoma niezależnymi liniami praktyki:
- Anthropic: fixed + variable content w prompt templates, RAG dla dużej ilości statycznego/dynamicznego kontekstu;
- OpenAI: template z policy variables zamiast wielu promptów per use case; RAG jako osobna dźwignia optymalizacji;
- Cognition/Devin: repo jest indeksowane, a prompt jest dopasowywany do zadania;
- Claude harness: pierwszy kontekst ma inny prompt niż późniejsze okna, a stan jest przenoszony przez artefakty;
- LangGraph/Claude Code: osobne prompty dla subagentów i narzędzi.

### Trade-off: jeden duży prompt vs wiele małych promptów

#### Jeden duży prompt
**Plusy**
- jedna prawda,
- mniejsze ryzyko błędu w kompozycji,
- łatwiej zagwarantować wspólne zasady.

**Minusy**
- większe ryzyko spadku salience,
- wyższy koszt tokenów,
- trudniejsze debugowanie „który fragment zadziałał?”,
- większe prompt pollution,
- trudniej robić eksperymenty A/B.

#### Wiele małych promptów składanych dynamicznie
**Plusy**
- lepsza trafność kontekstu,
- mniejsze zużycie tokenów,
- łatwiejsze wersjonowanie i rollout,
- możliwość niezależnej ewaluacji bloków,
- łatwiejsza specjalizacja agentów.

**Minusy**
- ryzyko, że retrieval/selection pominie ważny blok,
- więcej infrastruktury,
- trzeba pilnować zgodności między blokami,
- łatwo zbudować „kompozycyjny chaos”, jeśli nie ma registry i testów.

### Moja rekomendacja architektoniczna
W Twoim przypadku wybór powinien być **na korzyść dynamicznej kompozycji**, ale z twardą zasadą:
- **shared base i safety/logging rules nie są retrieve’owane** – one są stałe,
- retrieve’owane są tylko role, fazy i domain packs.

Inaczej mówiąc: **nie retrieve’uj konstytucji; retrieve’uj komentarze do konstytucji**.

---

## 4. Wytyczne dziedzinowe — najskuteczniejszy sposób wstrzykiwania

### Co gdzie trzymać

#### W system/shared prompt
Tylko zasady, które muszą obowiązywać stale:
- „zawsze loguj do session_log”,
- „gdy brak danych wejściowych, eskaluj zamiast zgadywać”,
- „nie wykonuj zmian produkcyjnych bez spełnionych gate’ów”.

#### W bloku domenowym ładowanym dynamicznie
Wiedza potrzebna tylko dla konkretnego zadania:
- SQL dialect specifics,
- naming conventions dla schematu,
- ERP field mapping patterns,
- typowe antywzorce i wyjątki.

#### Jako few-shot examples
Tylko przypadki, których nie da się dobrze opisać jedną regułą:
- edge cases,
- subtelne rozróżnienia,
- historycznie częste pomyłki,
- poprawny format artefaktu końcowego.

### Jak uniknąć prompt pollution przy 30+ zasadach SQL
Najlepszy wzorzec jest trójwarstwowy:

#### 1. Always-on invariants (5–8 zasad)
Np.:
- nie używaj `SELECT *`,
- jawnie kwalifikuj aliasy,
- każda migracja musi być odwracalna,
- każda propozycja SQL musi wskazać wpływ na indeksy i locki.

#### 2. Retrieved rule subset
Dobierany po tagach zadania:
- `domain=sqlserver`,
- `task_type=schema_migration`,
- `risk=high`,
- `erp_module=inventory`.

Z 30 reguł w prompt trafia np. 6–10.

#### 3. Deterministic validator
To, co da się sprawdzić parserem/linterem/regułą kodową, nie powinno żyć wyłącznie w promptcie.  
**Przykład:** styl SQL, forbidden constructs, naming regex, brak `NOLOCK`, wymagane komentarze migracji – to warto walidować automatycznie po wygenerowaniu.

### Kiedy few-shot, a kiedy nie
- **Zero-shot najpierw** dla reasoning models i prostych zadań.
- **Few-shot** dopiero, gdy chcesz wymusić konkretny format albo agent stale myli jeden typ decyzji.
- Few-shoty muszą być spójne z zasadami; niespójne przykłady rozwalają prompt bardziej niż ich brak.

### Praktyczna reguła
Dla każdego domain packa trzymaj:
- `rules_compact.md` – 5–10 zasad do promptu,
- `examples.md` – 1–3 przykłady doładowywane selektywnie,
- `validator.py/sql` – test deterministyczny po generacji.

---

## 5. Multi-agent consistency — shared base vs per-rola

### Co powinno być w shared base
To, co ma być identyczne dla wszystkich agentów:
- model współpracy przez DB,
- zasady eskalacji,
- standard logowania,
- standard niepewności,
- polityka „nie zgaduj, gdy brak danych”,
- format statusów i outcome,
- reguły bezpieczeństwa i granic systemu,
- minimalny standard jakości artefaktu.

### Co powinno być per rola
To, co odróżnia agenta:
- zakres kompetencji,
- dopuszczalne narzędzia i dane,
- success criteria,
- typ artefaktów,
- heurystyki domenowe,
- kiedy delegować / kiedy eskalować.

### Co powinno być per faza
To, co zmienia się w czasie workflow:
- entry conditions,
- required inputs,
- steps,
- exit conditions,
- walidacje,
- expected next handoff.

### Wzorzec dziedziczenia
Najbardziej praktyczny model dla Twojej architektury:

```text
shared_base
  -> role_base
    -> phase_block
      -> task_specific_context
        -> domain_pack(s)
```

To jest bardzo bliskie temu, jak działa:
- AGENTS.md w Codexie (global → project → nested override),
- LangChain Deep Agents (custom prompt + base + memory + skills + tools),
- Claude Code subagents (metadata + system body + ograniczony zestaw tools/model).

### Wersjonowanie między sesjami
Ponieważ agent nie ma trwałej pamięci, wersjonowanie promptów musi żyć **poza agentem**:
- prompt registry,
- prompt version id w każdym `session_init`,
- prompt version id zapisany do `session_log`,
- prompt version id dopięty do artefaktów lub backlog itemów,
- changelog „co się zmieniło i jakie failure modes naprawia”.

### Dodatkowa rekomendacja
Zapisuj do DB nie tylko `prompt_version`, ale też:
- `assembled_prompt_fingerprint`,
- listę bloków użytych w sesji,
- `model_id`,
- `tool_schema_version`.

To bardzo ułatwi korelację regresji z konkretną zmianą.

---

## 6. Ewaluacja — jak mierzyć jakość promptu

### Najważniejsza zasada
Nie oceniaj tylko odpowiedzi końcowej. Dla agentów operacyjnych trzeba oceniać:
1. **outcome** – co zmieniło się w środowisku,
2. **transcript/trajectory** – jak agent do tego doszedł,
3. **policy adherence** – czy nie złamał zasad,
4. **efficiency** – ile tur, narzędzi, tokenów i czasu zużył.

Anthropic bardzo mocno podkreśla rozróżnienie między **transcript** a **outcome** oraz potrzebę wielokrotnych triali dla jednego zadania.

### Zestaw metryk polecany dla Twojego systemu

#### A. Rule adherence
- % sesji bez naruszenia shared base,
- % sesji z poprawnym formatem logów,
- % sesji z poprawnym zastosowaniem domain rules.

#### B. Gate adherence
- % przypadków, w których agent **nie przeszedł dalej**, gdy brakowało wejścia,
- % przypadków, w których stworzył wymagane artefakty przed handoffem,
- % fałszywych pozytywów („uznał fazę za zamkniętą, choć gate nie był spełniony”).

#### C. Escalation quality
Nie sama „escalation rate”, tylko:
- **precision**: z ilu eskalacji faktycznie była potrzebna,
- **recall**: ile sytuacji wymagających eskalacji agent przeoczył,
- **unnecessary escalation rate**.

#### D. Task completion
- % backlog items ukończonych poprawnie,
- % ukończonych bez poprawek rework,
- % ukończonych z wymaganym zestawem artefaktów.

#### E. Repeat-defect rate
Bardzo ważne dla Twojego bólu:
- % zadań, w których agent powtórzył wcześniej naprawiony błąd,
- czas do ponownego wystąpienia regresji po zmianie promptu.

#### F. Efficiency
- średnia liczba tur,
- liczba tool calls,
- tokeny/sesję,
- latency do first correct artifact.

### Jak automatycznie wykrywać prompt decay
Najlepszy praktyczny zestaw:

#### 1. Regression suite na historycznych failure modes
Każda poprawka promptu dodaje test.  
Jeśli agent kiedyś:
- pominął gate,
- wygenerował zły SQL,
- przeszedł fazę bez artefaktu,
to ten przypadek staje się stałym testcase’em.

#### 2. Multi-trial eval
Każdy test uruchamiaj kilka razy. Anthropic rekomenduje wiele triali, bo pojedyncze uruchomienie jest zbyt szumne.

#### 3. Outcome-heavy grading
Nie karz agenta za inną kolejność kroków, jeśli wynik jest poprawny – **chyba że** chodzi o krytyczny gate bezpieczeństwa.  
Dla safety-critical flow dodaj twarde checki tool/state.

#### 4. Transcript review sampling
Automatyka nie wystarczy. Anthropic wprost pisze, że trzeba czytać transkrypty; inaczej nie odróżnisz złego agenta od złego grader’a.

#### 5. Canary suite po każdej zmianie promptu/modelu
Uruchamiaj:
- mały szybki zestaw po każdym commicie promptu,
- pełny nightly suite,
- oddzielnie suite dla każdego agenta i dla całego workflow.

### Narzędzia warte rozważenia
- **promptfoo** – szybkie testy regresyjne promptów i CI,
- **LangSmith** – wersjonowanie promptów, testy i trace’y,
- **MLflow Prompt Registry** – centralny rejestr promptów z aliasami środowisk,
- **OpenAI Evals / własny harness** – jeśli chcesz standaryzować grading.

Dla Twojego stacku prawdopodobnie najlepiej zacząć od **własnego harnessu w Pythonie + SQLite + YAML testcases**, a dopiero potem podpinać zewnętrzne narzędzia.

---

## 7. Implikacje dla architektury (co zmienić w obecnym systemie)

### Co bym zmienił najpierw

#### 1. Zamień monolityczne `.md` na registry bloków
Tabela `prompts`:
- `id`
- `kind` (`shared_base`, `role`, `phase`, `domain`, `example`, `routing`)
- `role`
- `phase`
- `task_type`
- `domain`
- `model_family`
- `content`
- `version`
- `status`
- `tags`
- `eval_suite_version`

#### 2. Dodaj tabelę kompozycji promptu
Tabela `prompt_assemblies`:
- `assembly_id`
- `role`
- `phase`
- `task_type`
- `selected_prompt_ids`
- `model_id`
- `assembled_hash`
- `created_at`

To pozwoli odtworzyć dokładny prompt użyty w sesji.

#### 3. Rozdziel routing od execution
Niech każdy agent ma:
- **routing_description** – kiedy go użyć,
- **execution_prompt** – jak ma pracować.

To wzorzec zgodny z Claude Code subagents i bardzo pomaga orkiestratorowi.

#### 4. Przenieś gate’y z prose do stanu
Dodaj tabelę lub JSON dla `phase_contracts`:
- `phase_name`
- `entry_requirements`
- `required_artifacts`
- `exit_requirements`
- `escalation_conditions`
- `output_schema`

Niech agent musi zwracać status zgodny z tym kontraktem.

#### 5. Zbuduj „memory of repairs”, ale jako retrieval, nie jako dopisek do roli
Z Twojego opisu wynika, że agent „powtarza błędy, które już były naprawione”.  
Nie doklejaj całej historii napraw do role promptu. Zamiast tego:
- trzymaj bazę `known_failures`,
- taguj po `role`, `phase`, `task_type`, `schema/module`,
- retrieve’uj 1–3 najbardziej podobne naprawione przypadki do bieżącego zadania,
- wstrzykuj jako krótki blok `historical_pitfalls`.

#### 6. Dodaj explicit phase-end JSON
Każda faza kończy się nie tylko tekstem do DB, ale też strukturą:
```json
{
  "phase": "analysis",
  "complete": false,
  "missing_inputs": ["supplier lead time"],
  "artifacts_created": ["analysis_note.md"],
  "next_recommended_phase": "data_request",
  "needs_escalation": true,
  "reason": "cannot estimate reorder policy without lead time"
}
```

#### 7. Oddziel to, co deterministyczne, od tego, co zostawiasz modelowi
Jeżeli coś da się sprawdzić kodem, sprawdzaj to kodem:
- kompletność artefaktów,
- zgodność formatu,
- SQL lint,
- obecność wymaganych wpisów w DB,
- nazewnictwo,
- forbidden commands.

Prompt ma sterować decyzją, a nie zastępować walidator.

### Docelowy model działania
Najbardziej sensowny target dla Twojego systemu wygląda tak:

1. `session_init.py` pobiera `shared_base`.
2. Dobiera `role_base`.
3. Dobiera `phase_block`.
4. Na podstawie zadania retrieve’uje `domain_pack` i `historical_pitfalls`.
5. Dokłada `runtime_state`.
6. Po odpowiedzi uruchamia walidatory.
7. Jeśli walidacja failuje – agent dostaje krótki corrective prompt albo następuje eskalacja.
8. Każda sesja zapisuje pełny fingerprint promptu, wersje bloków i wynik eval metrics.

To powinno uderzyć dokładnie w Twój obecny problem: degradacja nie zniknie całkowicie, ale przestanie być ukrytym skutkiem „promptu 400 linii”, a stanie się mierzalna na poziomie bloków, faz i reguł.

---

## 8. Źródła (linki do dokumentacji, artykułów, repozytoriów)

### Dokumentacja i artykuły vendorów
- Anthropic — Prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Anthropic — Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic — Effective harnesses for long-running agents: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic — Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Anthropic — Writing effective tools for agents: https://www.anthropic.com/engineering/writing-tools-for-agents
- Anthropic — Demystifying evals for AI agents: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

- OpenAI — Prompting guide: https://developers.openai.com/api/docs/guides/prompting
- OpenAI — Prompt engineering guide: https://developers.openai.com/api/docs/guides/prompt-engineering
- OpenAI — GPT-4.1 Prompting Guide: https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide
- OpenAI — Reasoning best practices: https://developers.openai.com/api/docs/guides/reasoning-best-practices
- OpenAI — Optimizing LLM Accuracy: https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy
- OpenAI — A practical guide to building agents: https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
- OpenAI — Agents SDK docs: https://developers.openai.com/api/docs/guides/agents-sdk
- OpenAI — Safety in building agents: https://developers.openai.com/api/docs/guides/agent-builder-safety
- OpenAI — AGENTS.md: https://developers.openai.com/codex/guides/agents-md/
- OpenAI — Using skills to accelerate OSS maintenance: https://developers.openai.com/blog/skills-agents-sdk
- OpenAI — Building Consistent Workflows with Codex CLI & Agents SDK: https://developers.openai.com/cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk/

### Frameworki i repozytoria
- LangChain Deep Agents customization: https://docs.langchain.com/oss/python/deepagents/customization
- LangChain Deep Agents harness: https://docs.langchain.com/oss/python/deepagents/harness
- LangChain subagents: https://docs.langchain.com/oss/python/langchain/multi-agent/subagents
- LangChain supervisor/subagents example: https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant
- LangGraph multi-agent workflows: https://blog.langchain.com/langgraph-multi-agent-workflows/
- AutoGen multi-agent concepts: https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/core-concepts/agent-and-multi-agent-application.html
- AutoGen AssistantAgent docs: https://microsoft.github.io/autogen/0.2/docs/reference/agentchat/assistant_agent/
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Piebald Claude Code system prompts repo: https://github.com/Piebald-AI/claude-code-system-prompts
- Cognition — How Cognition Uses Devin to Build Devin: https://cognition.ai/blog/how-cognition-uses-devin-to-build-devin

### Badania / literatura
- Liu et al. — Lost in the Middle: How Language Models Use Long Contexts (TACL 2024): https://aclanthology.org/2024.tacl-1.9/
- Survey / context for prompt engineering methods: https://arxiv.org/html/2407.12994v1

### Prompt management / eval tooling
- promptfoo prompt configuration: https://www.promptfoo.dev/docs/configuration/prompts/
- promptfoo CI/CD: https://www.promptfoo.dev/docs/integrations/ci-cd/
- LangSmith prompt management: https://docs.langchain.com/langsmith/manage-prompts
- LangSmith prompt concepts: https://docs.langchain.com/langsmith/prompt-engineering-concepts
- MLflow Prompt Registry: https://mlflow.org/prompt-registry

---

## Krótka konkluzja

Dla Twojego systemu największy zysk nie przyjdzie z „lepiej napisanego jednego promptu”, tylko z **przejścia z prompt engineering do context/prompt management**:

- mały shared base,
- role i fazy jako osobne bloki,
- domain knowledge retrieve’owane per task,
- gate’y zapisane jako stan i artefakty,
- prompt registry z wersjonowaniem,
- eval harness oparty o historyczne failure modes.

To jest dokładnie ten kierunek, w którym idą dziś praktyki produkcyjne agentów.
