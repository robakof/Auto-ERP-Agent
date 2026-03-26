# Research: Orchestracja workflow dla agentów LLM

```yaml
research_id: workflow_orchestration
requested_by: architect
date: 2026-03-24
base_prompt: 00 RESEARCHER_BASE_PROMPT.md
output_path: documents/researcher/research/workflow_orchestration.md
related_research: workflow_compliance.md
```

## Kontekst

Architektura docelowa Mrowiska:
- Agent dostaje **tylko bieżącą fazę/krok** workflow (nie całość)
- Po wykonaniu kroku → **hook walidacyjny** sprawdza czy agent zrobił wszystko zgodnie z WF
- Kolejna część workflow dostępna **dopiero po zatwierdzeniu poprzedniej**
- State machine: workflow jako graf kroków z walidowanymi przejściami

**Różnica od workflow_compliance.md:** Tamten research dotyczył "jak pisać prompty workflow".
Ten dotyczy "jak orchestrator zarządza workflow dla agenta" (chunking, validation, state).

## Constraints (Mrowisko-Specific)

1. **Agent-centric** — primary users to agenci LLM, nie ludzie
2. **Parseable** — workflow musi być parseable do struktur danych (DB, JSON)
3. **Incremental loading** — agent dostaje kawałki, nie całość
4. **Validation gates** — każdy chunk kończy się walidacją przed następnym
5. **Stateful execution** — orchestrator śledzi stan wykonania
6. **Lightweight format** — markdown z YAML, nie custom DSL

## Pytania badawcze

### Q1: Workflow chunking patterns

Jak dzielić workflow na części do sekwencyjnego ładowania?

**Sub-questions:**
- Granularność: faza vs krok vs sub-krok? Kiedy która?
- Jak przekazywać kontekst między chunkami (state, artifacts)?
- Jak obsługiwać dependencies między krokami (krok B potrzebuje outputu kroku A)?
- Ile kontekstu z poprzedniego kroku dawać (full output vs summary)?

**Expected output:**
- Patterns z nazwami (np. "Phase-level chunking", "Step-level chunking")
- Trade-offs każdego podejścia (context size vs continuity)
- Przykłady z frameworków (jak LangGraph/AutoGen dzielą execution)

---

### Q2: Validation hooks design

Jak projektować punkty walidacji w workflow?

**Sub-questions:**
- Co walidować: output (plik istnieje) vs behavior (agent użył właściwego narzędzia) vs quality (output spełnia kryteria)?
- Automated vs human-in-the-loop validation?
- Jak definiować success criteria w sposób machine-checkable?
- Jak obsługiwać partial success (3/5 warunków spełnionych)?
- Kiedy block (hard gate) vs warn (soft gate)?

**Expected output:**
- Validation patterns (output validation, behavior validation, quality validation)
- Machine-checkable criteria examples
- Partial success handling strategies

---

### Q3: Workflow state machine

Jak modelować workflow jako state machine dla orchestratora?

**Sub-questions:**
- Reprezentacja stanów i przejść (JSON, YAML, graph DSL)?
- Obsługa conditional paths (if/else, loops, parallel)?
- Rollback i retry patterns (cofnij do poprzedniego stanu)?
- Timeout i deadlock handling?
- Persistence (jak serializować stan do DB)?

**Expected output:**
- State representation formats (pros/cons)
- Common state machine patterns dla agentów
- Error recovery strategies

---

### Q4: Prompt streaming patterns

Jak streamować prompty do agenta w kontekście workflow?

**Sub-questions:**
- Ile kontekstu dawać agentowi na raz (current step only vs current + next preview)?
- Jak przekazywać wyniki poprzednich kroków (full output vs summary vs artifacts only)?
- Memory management — co agent "pamięta" między krokami?
- Context window optimization (jak zmieścić w limicie)?

**Expected output:**
- Context passing strategies
- Memory management patterns
- Context window budgeting examples

---

### Q5: Existing frameworks — orchestration focus

Jakie istniejące frameworki/wzorce obsługują agentic workflow orchestration?

**Sub-questions:**
- LangGraph, CrewAI, AutoGen — jak modelują workflow execution (nie definicję, a runtime)?
- State machines dla agentów (FSM, Statecharts)?
- Orchestration patterns (saga, choreography)?
- Jak frameworki dzielą workflow na kroki dla agenta?

**Expected output:**
- Framework comparison (orchestration capabilities)
- Patterns z produkcji (saga, choreography, centralized orchestrator)
- Proven implementations

---

### Q6: Validation-first workflow design

Jak projektować workflow "od walidacji"?

**Sub-questions:**
- Test-driven workflow design (najpierw kryteria sukcesu, potem kroki)?
- Jak pisać exit gate tak żeby był auto-walidowalny?
- Contract-first design (input/output schemas)?
- Jak definiować validation hooks w workflow document?

**Expected output:**
- Design patterns (validation-first, contract-first)
- Exit gate specification formats
- Schema-based validation examples

---

## Search strategy hints

### Phase 1: Broad exploration
- LangGraph execution model, interrupts, checkpoints
- AutoGen GraphFlow runtime, state persistence
- CrewAI Flow execution, step-by-step
- Temporal.io workflow patterns (saga, compensation)
- State machine libraries (XState, statecharts)

### Phase 2: Deep dive
- Academic papers: agentic workflows, LLM orchestration
- Production case studies: multi-step agent execution
- Validation patterns in workflow engines (Airflow, Prefect, Dagster)

## Output contract

**Lokalizacja:** `documents/researcher/research/workflow_orchestration.md`

**Struktura:**
1. **TL;DR** — 5-7 kluczowych wniosków (z siłą dowodów)
2. **Per question** — findings z evidence strength (empiryczne/praktyczne/spekulacja)
3. **Recommended patterns** — konkretne wzorce do wdrożenia w Mrowisku
4. **Anti-patterns** — czego unikać
5. **Open questions** — co wymaga dalszych badań lub eksperymentów
6. **Integration notes** — jak to łączy się z workflow_compliance.md findings

**Zakaz:** Nie oceniaj dopasowania do Mrowiska w warstwie "czy to dobre dla nas" — to osobny krok po researchu. Podaj fakty i patterns.

## Deadline context

Research potrzebny przed finalizacją CONVENTION_WORKFLOW — wpłynie na:
- Strukturę sekcji w workflow documents
- Format kroków (step_id, verification, etc.)
- Exit gate design
- Validation hooks specification
