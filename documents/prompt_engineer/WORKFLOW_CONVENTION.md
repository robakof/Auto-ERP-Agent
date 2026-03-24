# Workflow Convention — składnia i struktura workflow

**Audience:** Prompt Engineer (tworzenie workflow), wszystkie role (wykonywanie workflow)

**Purpose:** Kanoniczny format workflow zapewniający spójność, wykonalność i łatwe ładowanie do kontekstu agenta.

---

## Kiedy tworzyć workflow

**TAK — utwórz workflow gdy:**
- Proces powtarza się (≥2 razy)
- Proces ma >3 kroki
- Proces wymaga gate'ów (verification, approval, safety checks)
- Proces ma pułapki (znane anti-patterns)
- Proces wymaga koordynacji między fazami/rolami

**NIE — nie twórz workflow gdy:**
- Jednorazowe zadanie
- Prosty proces (≤3 kroki, oczywiste)
- Proces wciąż eksperymentalny (stabilizuj go najpierw)

---

## Metadata Header (MUST HAVE)

**Purpose:** Machine-readable metadata dla DB-driven orchestration.

**Każdy workflow MUSI zaczynać od YAML header:**

```yaml
---
workflow_id: erp_columns_creation
version: 1.0
owner_role: erp_specialist
trigger: "User asks to create ERP column"
prerequisites:
  - schema_loaded
  - session_init_done
outputs:
  - type: file
    path: "solutions/bi/columns/{ColumnName}_draft.sql"
  - type: state
    field: column_created
---
```

**Pola wymagane:**
- `workflow_id` — unique identifier (snake_case, no spaces)
- `version` — semantic versioning (1.0, 1.1, 2.0)
- `owner_role` — rola wykonująca workflow (erp_specialist, developer, prompt_engineer, etc.)
- `trigger` — kiedy workflow jest uruchamiany (natural language description)

**Pola opcjonalne:**
- `prerequisites` — lista warunków które muszą być spełnione przed startem (schema_loaded, session_init_done, git_clean)
- `outputs` — lista artefaktów które workflow produkuje:
  - `type: file` + `path` — ścieżka pliku
  - `type: state` + `field` — zmiana stanu systemu (column_created, suggestions_closed)
  - `type: backlog_item` — utworzenie backlog item
  - `type: commit` — git commit

**Why critical:**
- **Machine-readable** — YAML parser → workflows table (DB)
- **Prerequisite checking** — orchestrator verifies przed startem
- **Output tracking** — orchestrator wie co workflow produkuje
- **Versioning** — multiple versions tego samego workflow

**Forbidden:**
- Workflow bez YAML header (nie parseable do DB)
- `workflow_id` z spacjami lub polskimi znakami (use snake_case)
- `version` bez semantic versioning (use X.Y format minimum)

---

## Struktura pliku

```markdown
---
workflow_id: [workflow_name]
version: 1.0
owner_role: [rola]
trigger: "[opis kiedy uruchamiany]"
prerequisites:
  - [warunek_1]
  - [warunek_2]
outputs:
  - type: [file|state|backlog_item|commit]
    path: "[ścieżka]"  # dla type: file
    field: "[nazwa]"   # dla type: state
---

# Workflow: [Nazwa procesu]

[Krótki opis — 1-2 zdania. Dla kogo, kiedy używać.]

---

## [Opcjonalnie: Routing]

[Jeśli workflow obsługuje multiple scenarios — tabela routing:]

| Typ zadania | Sekcja |
|---|---|
| Scenario A | Sekcja A |
| Scenario B | Sekcja B |

---

## [Nazwa fazy/sekcji]

**Owner:** [rola wykonująca — np. developer, erp_specialist, PE]

### [Opcjonalnie: Purpose]

[Dla czego ta faza istnieje? Jaki problem rozwiązuje?]

### [Opcjonalnie: Zakres]

[Kiedy ta sekcja się stosuje? Boundary conditions.]

### Steps

[Numerowane kroki wykonania. Używaj hierarchii a/b/c dla sub-kroków:]

1a. [Krok główny]
1b. [Sub-krok]
1c. [Sub-krok]

2a. [Kolejny krok główny]
2b. [Sub-krok]

[Formatting kroków:]
- **Imperatyw:** "Sprawdź", "Utwórz", "Wyślij" (nie "Powinieneś sprawdzić")
- **Konkretny:** Podaj ścieżki, komendy, wzorce (nie "Przygotuj plik")
- **Warunkowy:** "Jeśli X → Tak. Jeśli Y → Nie."

[Przykłady dobrych kroków:]
✓ "Utwórz plik: `solutions/bi/{NazwaWidoku}/{NazwaWidoku}_draft.sql`"
✓ "Sprawdź `git status`. Jeśli brudny → zapytaj czy commitować."
✓ "Wyślij: `python tools/agent_bus_cli.py send --from PE --to developer`"

[Przykłady złych kroków:]
✗ "Przygotuj dane" (co to znaczy?)
✗ "Zastanów się nad rozwiązaniem" (nie wykonalne)
✗ "Upewnij się że wszystko działa" (jak sprawdzić?)

### Strict Step Format (DB-Ready) — MUST HAVE

**Purpose:** Format parseable do DB (workflow_steps table). Explicit tool, verification, error handling.

**Kiedy używać:**
- **Zawsze** gdy workflow ma być DB-driven (migrated to orchestrator)
- Workflow z >5 kroków (explicit structure helps)
- Workflow z error handling (retry/skip/escalate)

**Format:**

```markdown
## Step [numer]: [Nazwa kroku]

**step_id:** [unique_identifier]
**action:** [Opis co robisz — 1 zdanie imperatyw]
**tool:** [Bash|Read|Write|Edit|Grep|Glob|agent_bus_cli|custom]
**command:** `[dokładna komenda lub ścieżka pliku]`
**verification:** [Jak sprawdzić success? Output/file/state check]
**on_failure:**
  - retry: [yes|no]
  - skip: [yes|no]
  - escalate: [yes|no]
  - reason: "[Dlaczego fail? Co zrobić?]"
**next_step:** [step_id lub numer] (if PASS), [step_id] (if FAIL)
```

**Pola wymagane:**
- `step_id` — unique identifier (snake_case, używany w next_step transitions)
- `action` — co krok robi (imperatyw, 1 zdanie)
- `tool` — jakie narzędzie uruchamiasz (Bash, Read, agent_bus_cli, etc.)
- `command` — dokładna komenda lub ścieżka (parseable przez orchestrator)
- `verification` — jak sprawdzić czy sukces (output check, file existence, state change)
- `on_failure` — co zrobić przy fail (retry/skip/escalate + reason)
- `next_step` — transition (state machine: A → B)

**Przykład:**

```markdown
## Step 1: Verify Git Status

**step_id:** verify_git_clean
**action:** Sprawdź czy working tree czysty
**tool:** Bash
**command:** `git status`
**verification:** Output contains "nothing to commit, working tree clean"
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Uncommitted changes block workflow. User must commit or stash."
**next_step:** group_suggestions (if PASS), escalate (if FAIL)
```

**Why critical:**
- **DB migration** — każde pole → column w workflow_steps table
- **State machine** — next_step defines transitions (orchestrator wie co dalej)
- **Error handling** — retry/skip/escalate explicit (no guessing)
- **Tool execution** — orchestrator wie które narzędzie uruchomić

**Forbidden:**
- Step bez step_id (nie można zidentyfikować w DB)
- Command z placeholders niewyjaśnionymi ("`python {script}`" — który script?)
- Verification vague ("sprawdź czy działa" — jak sprawdzić?)
- on_failure bez reason (dlaczego fail? co zrobić?)

**Human-readable vs DB-ready:**

Możesz używać **obu formatów w jednym workflow:**
- **Human-readable** (1a, 1b, 2a) — dla prostych kroków bez error handling
- **DB-ready** (step_id, tool, verification) — dla complex kroków z error handling

**Ale:** Jeśli workflow będzie DB-driven (orchestrator execution) → **wszystkie steps MUSZĄ być DB-ready format**.

---

### Forbidden

[Anti-patterns — czego NIE robić. Bullet list.]

- [Forbidden pattern 1 — konkretny, z uzasadnieniem jeśli nieoczywiste]
- [Forbidden pattern 2]
- [...]

[Przykłady:]
✓ "Nie zaczynaj pisać SQL przed zakończeniem Inicjalizacji."
✓ "Pliki robocze w root projektu (`tmp_*.py`) — narzędzie od razu w `tools/`."
✗ "Nie rób błędów" (zbyt ogólne)

### Decision Points (DB-Ready) — MUST HAVE

**Purpose:** Explicit branching logic — state machine routing parseable do DB.

**Kiedy używać:**
- Workflow z conditional paths (if X → A, else → B)
- Workflow z quality gates (extraction ratio check, test coverage check)
- Workflow z user approval points (continue vs escalate)

**Format:**

```markdown
## Decision Point [numer]: [Nazwa decision]

**decision_id:** [unique_identifier]
**condition:** [Boolean expression lub check]
**path_true:** [step_id lub action] — co zrobić jeśli TRUE
**path_false:** [step_id lub action] — co zrobić jeśli FALSE
**default:** [action] — co zrobić jeśli condition indeterminate
```

**Pola wymagane:**
- `decision_id` — unique identifier (snake_case)
- `condition` — boolean expression (parseable lub human-readable z klarownym checkable statement)
- `path_true` — gdzie iść jeśli TRUE (step_id, escalate, retry, next_phase)
- `path_false` — gdzie iść jeśli FALSE
- `default` — fallback jeśli condition nie da się obliczyć (usually escalate)

**Przykład 1: Quality Gate**

```markdown
## Decision Point 1: Extraction Ratio Check

**decision_id:** check_extraction_ratio
**condition:** extracted_count / total_count >= 0.10
**path_true:** close_suggestions (continue workflow)
**path_false:** escalate_to_user (review needed — ratio too low)
**default:** escalate_to_user (if counts unavailable)
```

**Przykład 2: User Approval**

```markdown
## Decision Point 2: User Approves Plan

**decision_id:** user_approval_plan
**condition:** User responded "yes" to plan approval prompt
**path_true:** implement_plan (Step 3)
**path_false:** revise_plan (Step 2)
**default:** escalate (if no response after timeout)
```

**Why critical:**
- **State machine** — decision points są nodes w state machine (orchestrator routing)
- **DB migration** — workflow_decision_points table
- **Explicit branching** — no hidden logic (condition visible, paths clear)
- **Quality gates** — enforcement (extraction ratio, test coverage) built into workflow

**Forbidden:**
- Decision embedded w step text ("Jeśli X zrób Y") — extract to decision point
- Condition vague ("sprawdź czy OK") — konkretny boolean check
- Missing default path (co jeśli condition indeterminate?)

**Human-readable vs DB-ready:**

**Embedded decision (human-readable):**
```
1b. Jeśli git brudny → zapytaj użytkownika
```

**Explicit decision point (DB-ready):**
```markdown
## Decision Point 1: Git Status Check
**decision_id:** check_git_clean
**condition:** git status == "nothing to commit, working tree clean"
**path_true:** Step 2 (continue)
**path_false:** escalate_to_user (ask to commit/stash)
```

**Ale:** Jeśli workflow będzie DB-driven → **wszystkie decisions MUSZĄ być explicit decision points**.

---

### Exit gate

[Warunki przejścia do następnej fazy/zamknięcia workflow.]

**Human-readable format (statusy):**
```
PASS jeśli [warunek].
BLOCKED jeśli [warunek — co blokuje?].
ESCALATE jeśli [warunek — kiedy eskalować do użytkownika/innej roli?].
```

**DB-ready format (STRICT CHECKLIST) — MUST HAVE dla DB-driven workflows:**

```markdown
### Exit Gate

**Checklist:**
- [ ] `item_id_1`: [Konkretny warunek — file exists, test passed, state changed]
- [ ] `item_id_2`: [Konkretny warunek]
- [ ] `item_id_3`: [Konkretny warunek]

**Status:**
- PASS if: all checklist items == true
- BLOCKED if: [item_id] == false → [action] (escalate/retry/skip)
- RETRY if: [item_id] == false → agent can fix (rerun step)
```

**Pola wymagane (DB-ready):**
- **Checklist items** — każdy item ma:
  - `item_id` — unique identifier (snake_case, boolean flag name)
  - Konkretny check (file exists, output contains X, state field == Y)
- **Status logic** — explicit rules:
  - PASS if: all true
  - BLOCKED if: który item blokuje? → co zrobić?
  - RETRY if: który item można naprawić? → agent rerun step

**Przykład:**

```markdown
### Exit Gate

**Checklist:**
- [ ] `suggestions_grouped`: Grouped list created in `documents/human/suggestions/grouped.md`
- [ ] `backlog_items_created`: ≥1 backlog items created (extraction ratio ≥10%)
- [ ] `suggestions_status_updated`: All processed suggestions status changed (realized/noted/in_backlog)

**Status:**
- PASS if: all checklist items == true
- BLOCKED if: backlog_items_created == false → escalate to PE (review extraction — ratio too low)
- RETRY if: suggestions_grouped == false → agent can rerun grouping step
```

**Why critical:**
- **DB migration** — checklist items → boolean flags w workflow_state table
- **Status logic parseable** — orchestrator wie kiedy PASS/BLOCKED/RETRY
- **Actionable** — agent/orchestrator wie co brakuje (który item false?)
- **Quality gates** — enforcement (extraction ratio ≥10%) built into exit gate

**Forbidden:**
- Vague checklist ("wszystko zrobione" — co to znaczy?)
- Checklist item bez item_id (nie parseable do DB)
- Status logic bez action (BLOCKED → co zrobić?)

**Human-readable vs DB-ready:**

Możesz używać **obu formatów:**
- **Human-readable** (PASS/BLOCKED/ESCALATE text) — dla prostych workflow
- **DB-ready** (strict checklist) — dla DB-driven workflow

**Ale:** Jeśli workflow będzie DB-driven → **exit gate MUSI być strict checklist format**.

---

[Powtórz strukturę dla każdej fazy/sekcji]

---

## [Opcjonalnie: Dodatkowe sekcje]

### Dependencies

[Co musi być gotowe przed rozpoczęciem workflow?]

### Success criteria

[Jak wygląda sukces całego workflow? (różne od exit gate — to kryteria końcowe.)]

### Mockup outputu / Przykład

[Jeśli workflow produkuje artefakt — pokaż przykład.]

### References

[Linki do dokumentów wspierających, narzędzi, schematów.]
```

---

## Zasady pisania

### 1. Konkretność > Ogólność

**Dobry krok:**
> 1a. Sprawdź czysty working tree: `git status`. Jeśli brudny → zapytaj czy commitować.

**Zły krok:**
> 1a. Upewnij się że repozytorium jest w dobrym stanie.

### 2. Wykonalność

Agent musi móc wykonać krok bez zgadywania:
- ✓ Podaj dokładne ścieżki plików
- ✓ Podaj dokładne komendy
- ✓ Podaj decision tree (jeśli X → Y)

### 3. Hierarchia kroków

**a/b/c dla sub-kroków:**
```
1a. Główny krok
1b. Sub-krok (część głównego)
1c. Sub-krok (część głównego)

2a. Kolejny główny krok
2b. Sub-krok
```

**NIE mieszaj numeracji:**
✗ 1, 1.1, 1.2, 2, 2a (niespójne)

### 4. Forbidden = anti-patterns

Nie lista "oczywistych" błędów — lista **znanych pułapek z praktyki**:
- ✓ "Nie używaj `git mv` per plik — hook blokuje; używaj `mv` potem `git add -A`"
- ✗ "Nie rób literówek" (zbyt ogólne)

### 5. Exit gate = warunki przejścia

**Nie:** "Zrobiłem wszystko."
**Tak:** "PASS jeśli oba pliki robocze istnieją."

**Nie:** "Zakończ fazę."
**Tak:**
```
PASS jeśli:
- [ ] Testy przechodzą
- [ ] Commit + push
```

### 6. Owner = accountability

Każda faza/sekcja ma **Owner** — rola która wykonuje.
Jeśli workflow przechodzi między rolami — wyraźnie oznacz handoff.

---

## Dwa style workflow

### Styl A: Liniowy (fazy sekwencyjne)

**Użyj gdy:**
- Proces ma jasne fazy (discovery → implementation → verification)
- Każda faza ma purpose i exit gate
- Proces techniczny (SQL, data pipeline, deployment)

**Struktura:**
```
Inicjalizacja
Faza 0 — Discovery
Faza 1 — Implementation
Faza 2 — Verification
Faza 3 — Deployment
```

**Przykład:** `workflows/bi_view_creation_workflow.md`

---

### Styl B: Multi-scenario (routing)

**Użyj gdy:**
- Workflow obsługuje różne typy zadań (tool/bug/patch)
- Każdy typ ma inny flow
- Proces operacyjny (developer daily work, PE suggestions processing)

**Struktura:**
```
Routing table (typ zadania → sekcja)
Sekcja A: Narzędzie (Tool)
Sekcja B: Bug fix
Sekcja C: Patch
Sekcja D: Zamknięcie
```

**Przykład:** `workflows/developer_workflow.md`

---

## Ładowanie workflow do kontekstu agenta

**Zasada:** Agent dostaje **tylko sekcję bieżącej fazy**, nie cały workflow.

**Dlaczego:**
- Redukcja context usage
- Focus — agent nie widzi kroków które nie dotyczą obecnej fazy
- Safety — agent nie może "przeskoczyć" fazy

**Implementacja (dla orchestratora):**
```python
# Zamiast:
prompt = read_file("workflows/bi_view_creation_workflow.md")  # cały workflow

# Użyj:
section = extract_section("workflows/bi_view_creation_workflow.md", phase="Faza 0")
prompt = section  # tylko Faza 0
```

**W workflow zaznacz:**
> W runtime agent dostaje tylko sekcję swojej bieżącej fazy + [inne wymagane pliki].
> Nie wczytuj całego dokumentu do promptu sesji.

---

## Template: Nowy workflow (quickstart)

**Human-readable format (szybki start):**

```markdown
# Workflow: [Nazwa]

[Opis — 1-2 zdania]

---

## [Nazwa fazy]

**Owner:** [rola]

### Steps

1a. [Krok]
1b. [Sub-krok]

2a. [Krok]

### Forbidden

- [Anti-pattern 1]
- [Anti-pattern 2]

### Exit gate

PASS jeśli [warunek].

---
```

**DB-ready format (dla DB-driven workflows):**

```markdown
---
workflow_id: [nazwa_workflow]
version: 1.0
owner_role: [rola]
trigger: "[opis kiedy uruchamiany]"
prerequisites:
  - [warunek_1]
outputs:
  - type: [file|state|backlog_item|commit]
    path: "[ścieżka]"
---

# Workflow: [Nazwa]

[Opis — 1-2 zdania. Dla kogo, kiedy używać.]

---

## [Nazwa fazy]

**Owner:** [rola]

### Purpose

[Dlaczego ta faza istnieje?]

### Steps

## Step 1: [Nazwa kroku]

**step_id:** [unique_id]
**action:** [Opis — 1 zdanie imperatyw]
**tool:** [Bash|Read|Write|agent_bus_cli|etc]
**command:** `[dokładna komenda]`
**verification:** [Jak sprawdzić success?]
**on_failure:**
  - retry: [yes|no]
  - escalate: [yes|no]
  - reason: "[Dlaczego fail? Co zrobić?]"
**next_step:** [step_id] (if PASS), [action] (if FAIL)

---

## Decision Point 1: [Nazwa decision]

**decision_id:** [unique_id]
**condition:** [Boolean check]
**path_true:** [step_id lub action]
**path_false:** [step_id lub action]
**default:** [action jeśli indeterminate]

---

### Forbidden

- [Anti-pattern 1 — konkretny]
- [Anti-pattern 2]

### Exit Gate

**Checklist:**
- [ ] `item_id_1`: [Konkretny check]
- [ ] `item_id_2`: [Konkretny check]

**Status:**
- PASS if: all checklist items == true
- BLOCKED if: [item_id] == false → [action]

---
```

**Którą wersję wybrać:**
- **Human-readable** — dla prostych workflow, internal use, agent context loading
- **DB-ready** — dla DB-driven orchestration (migracja do DB w tym tygodniu!)

Zapisz w `workflows/[nazwa_workflow].md`.

---

## Checklist PE: Workflow review

Przed zatwierdzeniem nowego workflow, sprawdź:

**Wszystkie workflow (minimum):**
- [ ] **Konkretność:** Każdy krok wykonalny bez zgadywania?
- [ ] **Steps numeracja:** Hierarchia a/b/c spójna (lub strict format)?
- [ ] **Forbidden:** Lista pułapek z praktyki (nie teoretycznych)?
- [ ] **Exit gate:** Warunki jasne i testowalne?
- [ ] **Owner:** Każda faza ma przypisaną rolę?
- [ ] **Loadable:** Można wyekstrahować sekcję do kontekstu agenta?
- [ ] **Examples:** Są przykłady/mockupy jeśli output nieoczywisty?

**DB-ready workflow (dodatkowo — jeśli workflow będzie migrowany do DB):**
- [ ] **YAML header:** workflow_id, version, owner_role, trigger present?
- [ ] **step_id:** Każdy step ma unique step_id (snake_case)?
- [ ] **tool:** Każdy step ma explicit tool (Bash, Read, agent_bus_cli)?
- [ ] **verification:** Każdy step ma konkretny verification check?
- [ ] **on_failure:** Każdy step ma on_failure (retry/escalate/skip + reason)?
- [ ] **next_step:** Każdy step ma next_step transition (state machine)?
- [ ] **decision_id:** Decision points mają decision_id + condition + paths?
- [ ] **exit_gate checklist:** Checklist items z item_id (boolean flags)?
- [ ] **Parseable:** Workflow może być parsed do DB schema (no vague text)?

**Critical dla DB migration (migracja w tym tygodniu!):**
- [ ] **Wszystkie steps** strict format (step_id, tool, verification, on_failure, next_step)
- [ ] **Wszystkie decisions** explicit decision points (decision_id, condition, paths)
- [ ] **Exit gate** strict checklist (item_id, status logic parseable)

---

## Meta: Ten dokument

**Audience:** Prompt Engineer (pisanie workflow), wszystkie role (czytanie convention)
**Status:** Canonical — każdy nowy workflow musi przestrzegać tej konwencji
**Owner:** Prompt Engineer (aktualizuje gdy pattern się zmienia)

**Lokalizacja:**
- Convention: `documents/prompt_engineer/WORKFLOW_CONVENTION.md` (ten plik)
- Workflow files: `workflows/[nazwa].md`

**Przy tworzeniu workflow:**
1. Przeczytaj tę konwencję
2. Wybierz styl (Liniowy vs Multi-scenario)
3. Użyj template
4. Review checklist
5. Zapisz w `workflows/`

---

**Version:** 1.0 (2026-03-24)
**Source:** Ekstrakcja z `bi_view_creation_workflow.md` + `developer_workflow.md`
