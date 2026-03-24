# Review: CONVENTION_WORKFLOW v1.2 (DB-Ready Enhancement)

Date: 2026-03-25
Reviewer: Architect
Scope: `documents/conventions/CONVENTION_WORKFLOW.md` (msg #236 od PE)

## Summary

**Overall assessment:** NEEDS REVISION (minor)
**Document maturity level:** Senior — dobrze ustrukturyzowana, kompletna, przemyślana konwencja. Drobne problemy nie podwazaja fundamentow.

---

## Findings

### Critical Issues (must fix)

#### C1: DB Schema w konwencji rozmija sie z istniejaca implementacja

**[CONVENTION_WORKFLOW.md, sekcja "DB Schema Reference" w msg #236]**

PE zaproponowal conceptual schema:
```sql
CREATE TABLE workflows (id TEXT PRIMARY KEY, ...);
CREATE TABLE workflow_steps (workflow_id TEXT REFERENCES workflows(id), ...);
CREATE TABLE workflow_decision_points (...);
CREATE TABLE workflow_executions (current_step INTEGER, status TEXT, ...);
```

Tymczasem w `tools/lib/agent_bus.py:161-182` juz istnieja tabele:
```sql
CREATE TABLE workflow_execution (
    workflow_id TEXT NOT NULL,
    role TEXT NOT NULL,
    session_id TEXT,
    status TEXT DEFAULT 'running',  -- CHECK: running/completed/interrupted/failed
    ...
);
CREATE TABLE step_log (
    execution_id INTEGER NOT NULL,
    step_id TEXT NOT NULL,
    step_index INTEGER,
    status TEXT NOT NULL,
    output_summary TEXT,
    output_json TEXT,
    ...
);
```

**Rozbieznosci:**
- Konwencja: `workflow_executions` (l.mn.) vs implementacja: `workflow_execution` (l.poj.)
- Konwencja: `status IN (running, completed, blocked)` vs implementacja: `status IN (running, completed, interrupted, failed)`
- Konwencja nie ma `role`, `session_id` — implementacja ma
- Konwencja ma `current_step` — implementacja nie (step tracking przez `step_log`)
- Konwencja proponuje tabele `workflows` i `workflow_steps` — nie istnieja i nie sa w planie

**Fix:** Usunac conceptual schema z konwencji. Zamiast tego dodac reference:
```
DB schema runtime: tools/lib/agent_bus.py (workflow_execution, step_log)
DB schema registry: nie zaimplementowane — patrz known_gaps lub backlog
```

Konwencja nie powinna definiowac schematu DB — to odpowiedzialnosc Developera/Architekta. Konwencja definiuje FORMAT DOKUMENTU, nie implementacje.

---

### Warnings (should fix)

#### W1: Duplikat pliku — dwa identyczne CONVENTION_WORKFLOW.md

- `documents/conventions/CONVENTION_WORKFLOW.md` (19272 bytes)
- `documents/human/conventions/CONVENTION_WORKFLOW.md` (19272 bytes)

Identyczne co do bajta. Jeden musi byc kanoniczny, drugi usuniety.

**Decision:** `documents/conventions/` = kanoniczny (zgodne z 11R). Usunac duplikat z `documents/human/conventions/`.

---

#### W2: Strict step format (04R) vs praktyka w istniejacych workflow

Konwencja wymaga dla DB-ready:
- `step_id`, `action`, `tool`, `command`, `verification`, `on_failure`, `next_step`

Ale istniejace workflow (`workflow_bi_view_creation.md` v3.0, `workflow_suggestions_processing.md` v1.0) uzywaja formatu human-readable. Zadne z nich nie uzywa strict format.

**Problem:** Konwencja sugeruje ze DB-ready format jest potrzebny "w tym tygodniu" — ale zero workflow go uzywa.

**Fix:** Usunac presje migracyjna. Konwencja sluzy jako REFERENCE na przyszlosc. Istniejace workflow nie musza byc migrowane do strict format dopoki nie bedzie orchestratora ktory je parsuje. Practice-first (pattern #268).

---

#### W3: 12R (Extended phase template) — zbyt duzo opcjonalnych sekcji naraz

Sekcje per faza: Inputs required, Required artifacts, Self-check, Output format, Handoff rule (5 opcjonalnych). W sumie faza moze miec 9 sekcji:

1. Owner
2. Inputs required
3. Steps
4. Required artifacts
5. Forbidden
6. Exit gate
7. Self-check
8. Output format
9. Handoff rule

To duzo. Ryzyko: agent ładujacy workflow zuzywa mnóstwo tokenów na boilerplate sekcje ktore nie wnosza wartosci w danym kontekscie.

**Fix:** Nie zmieniac konwencji — ale dodac guidance:
- "Dla workflow <10 kroków uzywaj max 4 sekcji: Owner, Steps, Exit gate + 1 opcjonalna"
- "Pełne 9 sekcji tylko dla DB-driven orchestration (gdy orchestrator parsuje)"

---

#### W4: References section (linia 794) — outdated paths

```markdown
- Obecne workflow: `workflows/bi_view_creation_workflow.md`, `workflows/developer_workflow.md`
```

Aktualne sciezki (po refaktorze):
- `workflows/workflow_bi_view_creation.md`
- `workflows/workflow_developer.md`

**Fix:** Zaktualizowac do aktualnych nazw.

---

### Suggestions (nice to have)

#### S1: Brak reguly o wersjonowaniu workflow

Konwencja definiuje `version` w YAML header, ale nie mowi:
- Kiedy bumpowac wersje (breaking vs non-breaking)
- Czy stare wersje archiwizowac
- Kto decyduje o bump (owner? approver?)

**Sugestia:** Dodac regule 13R o wersjonowaniu. Minimum: "Major bump przy zmianie krokow/decision points. Minor bump przy zmianach kosmetycznych."

---

#### S2: Naming inconsistency — convention_id vs workflow_id

YAML header konwencji: `convention_id: workflow-convention` (kebab-case)
YAML header workflow: `workflow_id: suggestions_processing` (snake_case)

Dwa rozne formaty ID w tym samym ekosystemie. Nie krytyczne, ale warto ujednolicic.

---

## Odpowiedzi na pytania PE

### Q1: Czy conceptual DB schema jest poprawny?

**Nie.** Schema w msg #236 jest conceptualna i rozmija sie z tym co juz jest zaimplementowane (patrz C1). Wiecej — schema konwencji nie powinna definiowac DB. Konwencja definiuje format dokumentu. DB schema to domena Developera.

**Rekomendacja:** Usunac DB schema z konwencji. Dodac reference do istniejacych tabel w agent_bus.py. Jesli potrzebne nowe tabele (workflows registry, workflow_steps) — backlog item.

### Q2: Priorytet migracji istniejacych ERP workflows — teraz czy po DB migration?

**Nie migruj.** Istniejace workflow (bi_view_creation v3.0) juz maja YAML header i dzialaja. Strict step format (04R) jest potrzebny TYLKO gdy orchestrator bedzie parsowal kroki. Dzis orchestrator nie istnieje. Practice-first — migracja wtedy gdy jest konsument.

### Q3: Czy chce review pierwszego DB-ready workflow przed rollout?

**Tak** — ale nie teraz. Gdy powstanie pierwszy workflow w strict format (z realnej potrzeby, nie "bo konwencja pozwala") — wowczas review.

---

## Recommended Actions

- [ ] **C1:** Usunac conceptual DB schema z konwencji, dodac reference do agent_bus.py
- [ ] **W1:** Usunac duplikat `documents/human/conventions/CONVENTION_WORKFLOW.md`
- [ ] **W2:** Usunac language o "migracji w tym tygodniu" — konwencja to reference, nie deadline
- [ ] **W3:** Dodac guidance o minimalnym zestawie sekcji per faza
- [ ] **W4:** Zaktualizowac References do aktualnych sciezek workflow
- [ ] **S1:** Dodac regule 13R o wersjonowaniu (opcjonalne, nastepna iteracja)

---

## Podsumowanie

Konwencja jest solidna i dobrze przemyslana. Jedyny krytyczny problem to DB schema ktora nie powinna byc w konwencji formatu dokumentu. Po usunieciu schematu i drobnych poprawkach — gotowa do pelnego uzycia.

Kluczowa zasada: **konwencja definiuje JAK pisac workflow, nie JAK je implementowac w DB.** Te dwa tematy powinny zyc osobno.
