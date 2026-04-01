# ADR-002: Workflow Enforcement via State Machine Pattern

**Status:** Accepted
**Date:** 2026-03-27
**Authors:** Architect
**Deciders:** Dawid (human), Architect, Developer
**Consulted:** Prompt Engineer, Dispatcher

---

## Context

### Problem: agenci nie przestrzegają workflow

Agenci znają reguły (cytują je w handoffach), ale pomijają kroki gdy user mówi "zrób".
Prompt nie wygra z bezpośrednią instrukcją — PE udokumentował 6 nieudanych prób
wzmocnienia promptów (msg #405, klasyfikacja: `outside_prompt_layer`).

Chronologia eskalacji:
1. **2026-03-16** — research tool selection enforcement → wdrożono PreToolUse hook (sukces)
2. **2026-03-25** — Architect pominął Fazę 2 convention_creation, błędna interpretacja handoff
3. **2026-03-26** — PE: "Agent ZNA reguły ale pomija je gdy user mówi zrób"
4. **2026-03-26** — Architect zaproponował git_commit gate → user odrzucił:
   "Gate na końcu jest za późno. Agent zrobi 2h pracy bez workflow, potem backfilluje
   step-logi byle jak. Facade compliance, zero value."
5. **2026-03-26** — Decyzja: research → ADR → implementacja

### Obecny stan systemu

**Co istnieje:**
- `workflow_execution` + `step_log` tabele w DB (backlog #153, done)
- CLI: `workflow-start`, `step-log`, `workflow-end` w agent_bus_cli
- CONVENTION_WORKFLOW v1.4 z HANDOFF_POINT (13R)
- PreToolUse hook (tool selection enforcement — działa)
- 10 workflow w `workflows/` (markdown, advisory)
- Reguła "Workflow gate" w CLAUDE.md (advisory)

**Co nie działa:**
- Agenci nie wywołują `workflow-start` — nikt nie wymusza
- `step-log` jest dobrowolny — agent loguje lub nie
- Kolejność kroków nie jest walidowana — można zalogować Step 4 bez Step 3
- Self-monitoring degeneruje do "compliance theatre" (research: sekcja 5)
- Incentive: system premiuje output, nie proces (research: sekcja 6)

### Constraints

1. **Nie prompt-level** — udowodniono nieskuteczność (6 prób PE)
2. **Nie checkpoint końcowy** — user odrzucił explicite ("za późno, facade compliance")
3. **Nie facade** — agent nie może logować byle co i przejść dalej
4. **Musi być programistyczne** — hook/code, nie tekst
5. **Incremental** — nie wymaga Fazy 3 (prompty w DB) ani pełnego orchestratora
6. **Koszt** — nie może drastycznie spowalniać pracy agenta

---

## Decision

**Wdrażamy State Machine Enforcement Pattern z enforcement na granicach wykonania (hooks).**

### Architektura: 3 warstwy enforcement

```
┌─────────────────────────────────────────────────────┐
│                  WARSTWA 1: GATE                     │
│         PreToolUse hook + on_user_prompt hook         │
│                                                       │
│  Agent wywołuje narzędzie → hook sprawdza:            │
│  1. Czy agent jest w aktywnym workflow?                │
│  2. Czy bieżący krok pozwala na to narzędzie/akcję?   │
│  3. Czy poprzedni krok ma status PASS?                 │
│                                                       │
│  Brak workflow → WARN (faza 1) / BLOCK (faza 2)      │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                 WARSTWA 2: STATE MACHINE              │
│              workflow_engine.py (nowy moduł)           │
│                                                       │
│  Workflow definition (YAML/DB) → dozwolone stany      │
│  Stan bieżący = last step PASS w step_log             │
│  Przejście = warunki spełnione → następny stan legal  │
│  Agent nie "pamięta" — po prostu NIE MA przejścia     │
│  dopóki warunki nie są spełnione                      │
│                                                       │
│  API:                                                  │
│  - can_transition(execution_id, target_step) → bool    │
│  - get_current_state(execution_id) → StepState         │
│  - get_allowed_actions(execution_id) → list[Action]    │
│  - validate_step_completion(exec_id, step_id) → bool   │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              WARSTWA 3: VERIFICATION                  │
│           Zewnętrzna walidacja artefaktów              │
│                                                       │
│  step-log PASS wymaga dowodu:                         │
│  - Plik istnieje? → Glob/stat check                   │
│  - Test przeszedł? → pytest exit code w output_json    │
│  - Commit zrobiony? → git log check                    │
│  - Wiadomość wysłana? → message ID w agent_bus         │
│                                                       │
│  Agent deklaruje PASS → verifier sprawdza artefakt    │
│  Brak artefaktu = PASS odrzucony, krok BLOCKED        │
└─────────────────────────────────────────────────────┘
```

### Kluczowe decyzje projektowe

**D1: Workflow definitions w DB, import z .md**

Workflow YAML header (CONVENTION_WORKFLOW 01R) + steps w formacie strict (04R)
już istnieją w konwencji. Zamiast runtime parsera .md → obiekt,
**definicje workflow trafiają do DB** (tabele poniżej).

PE autoruje workflow w .md (CONVENTION_WORKFLOW format) → `workflow-import` ładuje do DB.
User przegląda przez `render.py workflow` → .md na żądanie.
Runtime (state machine, hooks) czyta wyłącznie z DB.

**Dlaczego DB zamiast parser:**
- Parser = zależność runtime (przy każdym tool call), drift .md ↔ parser = bug
- DB = SELECT ~1ms, schema = kontrakt, walidacja na INSERT
- Spójność z projektem (agent_bus, backlog, suggestions — wszystko w mrowisko.db)
- Forward-compatible z composable steps (suggestion #498)

**Minimalne tabele (enforcement-focused):**

```sql
-- Definicja workflow (1 row per workflow version)
CREATE TABLE workflow_definitions (
    workflow_id   TEXT NOT NULL,
    version       TEXT NOT NULL,
    owner_role    TEXT NOT NULL,
    trigger_desc  TEXT,
    status        TEXT DEFAULT 'active' CHECK (status IN ('active','deprecated')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workflow_id, version)
);

-- Kroki workflow (building blocks)
CREATE TABLE workflow_steps (
    id              INTEGER PRIMARY KEY,
    workflow_id     TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    step_id         TEXT NOT NULL,
    phase           TEXT,
    sort_order      INTEGER NOT NULL,
    action          TEXT NOT NULL,
    tool            TEXT,
    command         TEXT,
    verification_type  TEXT,  -- file_exists|test_pass|message_sent|commit_exists|manual
    verification_value TEXT,
    on_failure_retry   INTEGER DEFAULT 0,
    on_failure_skip    INTEGER DEFAULT 0,
    on_failure_escalate INTEGER DEFAULT 1,
    on_failure_reason  TEXT,
    next_step_pass  TEXT,
    next_step_fail  TEXT,
    is_handoff      INTEGER DEFAULT 0,
    handoff_to      TEXT,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version),
    UNIQUE (workflow_id, workflow_version, step_id)
);

-- Decision points
CREATE TABLE workflow_decisions (
    id            INTEGER PRIMARY KEY,
    workflow_id   TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    decision_id   TEXT NOT NULL,
    condition     TEXT NOT NULL,
    path_true     TEXT NOT NULL,
    path_false    TEXT NOT NULL,
    default_action TEXT,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version)
);

-- Exit gates (checklist items per phase)
CREATE TABLE workflow_exit_gates (
    id            INTEGER PRIMARY KEY,
    workflow_id   TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    phase         TEXT NOT NULL,
    item_id       TEXT NOT NULL,
    condition     TEXT NOT NULL,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version)
);
```

**Czego NIE robimy teraz:**
- Composable step library (kroki współdzielone między workflow) — docelowo tak, teraz 1:1
- Dynamiczny assembly per rola/kontekst — docelowo tak, teraz statyczne definicje
- Wariantowość kroków (templating) — docelowo tak, teraz flat

Schema jest forward-compatible: `workflow_steps` to już "building blocks w DB".
Przejście do composable = dodanie tabeli `step_templates` + `workflow_compositions`
bez migracji istniejących danych.

**D2: Enforcement gradualny (soft → hard)**

| Faza | Zachowanie | Cel |
|------|-----------|-----|
| Faza A (soft) | Hook loguje WARNING gdy agent działa bez workflow | Zbieramy dane, nie blokujemy |
| Faza B (medium) | Hook blokuje tool calls poza workflow dla kroków wrażliwych | Enforcement na critical path |
| Faza C (hard) | Hook blokuje WSZYSTKIE tool calls poza workflow | Pełny enforcement |

Faza A pozwala zmierzyć skalę problemu i dostroić definicje workflow zanim zaczniemy blokować.

**D3: Enforcement point = PreToolUse hook (istniejący)**

Rozszerzamy obecny `pre_tool_use.py` o workflow awareness:
1. Na starcie: odczytaj `execution_id` z env/DB (ustawiony przez `workflow-start`)
2. Jeśli brak `execution_id`:
   - Faza A: log warning do `step_log` z `status=UNTRACKED`
   - Faza B/C: zwróć `deny` z repair message "Wywołaj workflow-start przed pracą"
3. Jeśli jest `execution_id`:
   - Odczytaj bieżący krok z state machine
   - Sprawdź czy tool call jest dozwolony w tym kroku
   - Jeśli nie → deny z "Najpierw zakończ krok X"

**D4: Verifier = osobna warstwa, nie self-check**

Agent wywołuje `step-log --step-id X --status PASS`.
Zamiast ufać agentowi, `step-log` sprawdza `verification` z workflow definition:
- `type: file_exists` → sprawdź czy plik istnieje
- `type: test_pass` → sprawdź exit code ostatniego pytest
- `type: message_sent` → sprawdź czy message ID istnieje w agent_bus
- `type: commit_exists` → sprawdź git log
- `type: manual` → PASS akceptowany (dla kroków bez automatycznej weryfikacji)

Jeśli weryfikacja fails → `step-log` zwraca error, krok pozostaje `IN_PROGRESS`.

**D5: Workflow registration at session start**

`session_init.py` rozszerzony o:
1. Sprawdź czy rola ma aktywny (interrupted) workflow → resume
2. Jeśli user podaje task → match do workflow definition
3. Ustaw `execution_id` w zmiennej środowiskowej sesji

**D7: Exploratory workflow (workflow-envelope)**

Nie każde zadanie ma zdefiniowany workflow. Niektóre są eksploracyjne (research, prototyp,
pierwsze wykonanie nowego typu zadania). Zamiast Wariantu 2 z CLAUDE.md ("brak workflow,
ale w scope roli") agent rejestruje **exploratory workflow** — pustą kopertę:

```
py tools/agent_bus_cli.py workflow-start --workflow-id exploratory --role <rola>
```

Exploratory workflow:
- Ma `execution_id` → audit trail istnieje, tool calls powiązane z sesją
- Nie ma zdefiniowanych kroków → state machine nie blokuje przejść
- Agent loguje kroki które wykonuje (`step-log` z dowolnym `step_id`)
- Hook widzi aktywny workflow → nie generuje WARNING/DENY
- Na zakończenie: agent wysyła opis kroków do PE → PE formalizuje workflow

Efekt: **tracking bez enforcement** — zachowujemy elastyczność dla nowych/eksploracyjnych
zadań, ale nie tracimy visibility. Każdy tool call ma execution_id, każdy krok jest
zalogowany, PE dostaje materiał do formalizacji.

Kiedy używać:
- Zadanie wykonywane pierwszy raz (nie ma jeszcze workflow)
- Zadanie eksploracyjne (research, spike, prototyp)
- Zadanie o nieznanej strukturze (debugging złożonego problemu)

Kiedy NIE używać:
- Istnieje workflow strict (04R) dla tego typu zadania → użyj go
- Agent "nie chce się trzymać" istniejącego workflow → to violation, nie eksploracja

**D6: HANDOFF_POINT = hard stop w state machine**

Krok oznaczony jako HANDOFF_POINT w workflow definition:
- State machine NIE pozwala na przejście do następnego stanu
- Agent dostaje komunikat: "HANDOFF do [rola]. Czekaj na odpowiedź."
- Przejście odblokowane dopiero gdy:
  - Odbiorca wyśle odpowiedź (message w agent_bus)
  - LUB human explicite odblokuje (CLI: `workflow-resume --execution-id X`)

---

## Alternatives Considered

### Alt 1: Prompt-only enforcement (wzmocnienie instrukcji)

**Odrzucone.** PE udokumentował 6 nieudanych prób. Agent zna reguły, ale optymalizuje
na output zamiast na proces. Prompt nie może wygrać z bezpośrednią instrukcją usera.

**Siła dowodów:** empiryczne (wewnętrzne: 6 prób) + empiryczne (research: sekcja 2).

### Alt 2: Git commit gate (walidacja na końcu)

**Odrzucone przez usera.** "Gate na końcu jest za późno. Agent zrobi 2h pracy bez workflow,
potem backfilluje step-logi byle jak."

Problem: zachęca do facade compliance — agent formalnie loguje kroki post-factum
bez rzeczywistego wykonania procesu.

### Alt 3: Pełny orchestrator (LangGraph-style)

**Odłożone.** Wymaga Fazy 3 (prompty w DB) + pełnej orkiestracji.
Zbyt duży scope dla obecnego stanu systemu.
State machine enforcement jest krokiem w stronę orchestratora,
ale działa standalone bez pełnej infrastruktury.

### Alt 4: Agent-bufor (backlog #60)

**Subsumowane.** Backlog #60 proponował "lekkiego agenta-weryfikatora" między fazami.
State machine enforcement realizuje ten sam cel bez dodatkowego agenta —
weryfikacja jest w kodzie (hook + verifier), nie w promptcie kolejnego LLM.

Zaleta: brak kosztu dodatkowego LLM call per krok.
Wada: weryfikacja ograniczona do warunków obserwowalnych (pliki, testy, commity).
Semantyczna jakość artefaktów wymaga review (Warstwa 3, typ `manual`).

---

## Consequences

### Pozytywne

1. **Agent nie może pominąć kroku** — state machine nie ma przejścia
2. **Audit trail wbudowany** — każda akcja powiązana z execution_id i step_id
3. **Incremental wdrożenie** — Faza A (soft) nie blokuje pracy, zbiera dane
4. **Reuse istniejącej infrastruktury** — `workflow_execution`, `step_log`, `pre_tool_use.py`
5. **Separation of concerns** — enforcement w kodzie, nie w prompcie
6. **HANDOFF enforcement** — hard stop eliminuje "zrobię sam zamiast czekać"
7. **Zewnętrzna weryfikacja** — PASS wymaga dowodu, nie deklaracji

### Negatywne

1. **Workflow definitions muszą być precyzyjne** — strict format (04R) wymagany
   dla każdego workflow objętego enforcement. Prose workflow nie importuje się do DB.
   *Mitygacja:* import tool + gradualny rollout (najpierw 2-3 critical workflows).

2. **Rigidity vs creativity trade-off** — agent w state machine nie może "improwizować".
   *Mitygacja:* Exploratory workflow (D7) — pusta koperta z tracking bez enforcement.
   Agent rejestruje `workflow-start --workflow-id exploratory`, ma audit trail i visibility,
   ale state machine nie blokuje przejść. Dla zadań eksploracyjnych / pierwszego wykonania.
   PE formalizuje workflow post-factum na podstawie zalogowanych kroków.

3. **Maintenance cost** — każda zmiana procesu wymaga aktualizacji workflow definition.
   *Mitygacja:* PE jest ownerem workflow definitions, ma dedykowany workflow do tworzenia/edycji.

4. **Verification gap** — weryfikacja automatyczna pokrywa artefakty (pliki, testy, commity),
   nie pokrywa jakości semantycznej. Agent może wyprodukować pusty plik i przejść dalej.
   *Mitygacja:* typ `manual` + review na exit gate. Długoterminowo: LLM-as-judge
   (research: sekcja 5, external verifier).

5. **Hook overhead** — każdy tool call przechodzi przez workflow check.
   *Mitygacja:* cache `execution_id` + `current_step` w pamięci procesu hooka.
   Koszt: 1 query SQLite per tool call (~1ms).

---

## Implementation Plan

Osobny dokument: `documents/human/plans/plan_workflow_enforcement.md`

---

## References

- Research: `documents/researcher/research/research_results_workflow_enforcement.md`
- Diagnosis: `documents/human/reports/workflow_violation_diagnosis_2026_03_25.md`
- CONVENTION_WORKFLOW: `documents/conventions/CONVENTION_WORKFLOW.md`
- Arch Uplift Plan Faza 7: `documents/dev/arch_uplift_plan.md`
- Backlog #60: Agent-bufor (subsumowany)
- Backlog #153: Workflow tracking (done — DB tables exist)
- ADR-001: `documents/architecture/ADR-001-domain-model-migration.md` (format reference)
- PE msg #405: 6 nieudanych prób prompt enforcement
- User quote: "Gate na końcu jest za późno" (2026-03-26)
- Suggestion #498: Wizja Composable Workflow Engine (potoki z promptów) — docelowa architektura
- User decision 2026-03-30: DB-first zamiast parser, forward-compatible z composable steps
