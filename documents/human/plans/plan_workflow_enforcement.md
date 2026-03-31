# Plan implementacji: Workflow Enforcement (State Machine Pattern)

**ADR:** `documents/architecture/ADR-002-workflow-enforcement.md`
**Data:** 2026-03-27
**Owner:** Architect (design) → Developer (implementation)

---

## Przegląd faz

| Faza | Nazwa | Cel | Effort | Zależność |
|------|-------|-----|--------|-----------|
| 1 | DB Schema + Import Tool | Tabele workflow w DB + import z .md | srednia | brak |
| 2 | State Machine Engine | Logika stanów i przejść (czyta z DB) | srednia | Faza 1 |
| 3 | Hook Integration (soft) | PreToolUse awareness + WARNING mode | mala | Faza 2 |
| 4 | Step Verification | Zewnętrzna walidacja artefaktów przy step-log PASS | srednia | Faza 2 |
| 5 | Hook Enforcement (hard) | Blokowanie tool calls poza workflow | mala | Faza 3+4 |
| 6 | HANDOFF Enforcement | Hard stop na HANDOFF_POINT | mala | Faza 2 |

**Szacowany total:** 6 faz, każda niezależnie deployowalna i testowalna.

---

## Faza 1: DB Schema + Import Tool

**Owner:** Developer
**Input:** pliki `workflows/workflow_*.md` w formacie CONVENTION_WORKFLOW 04R (strict)
**Output:** migracja DB (tabele) + `tools/workflow_import.py` + `render.py workflow`

### Decyzja architektoniczna

DB jako runtime authority. .md jako format autorski.
Patrz ADR-002 D1 (zaktualizowany 2026-03-30) + suggestion #498 (wizja composable steps).

**Przepływ:** PE autoruje .md → `workflow_import.py` ładuje do DB → runtime czyta z DB.
User przegląda przez `render.py workflow` → .md na żądanie.

### Zadania

1.1. **Migracja DB** — utwórz tabele w mrowisko.db (schema z ADR-002 D1):
   - `workflow_definitions` (workflow_id, version, owner_role, trigger_desc, status)
   - `workflow_steps` (workflow_id, step_id, phase, action, tool, command, verification, on_failure, next_step, is_handoff, sort_order)
   - `workflow_decisions` (workflow_id, decision_id, condition, path_true, path_false, default)
   - `workflow_exit_gates` (workflow_id, phase, item_id, condition)

1.2. **Import tool** — `tools/workflow_import.py`:
   - Czyta .md w formacie CONVENTION_WORKFLOW 04R (strict)
   - Parsuje YAML header → `workflow_definitions`
   - Parsuje `## Step N:` → `workflow_steps`
   - Parsuje `## Decision Point N:` → `workflow_decisions`
   - Parsuje `### Exit Gate` → `workflow_exit_gates`
   - Wykrywa `→ HANDOFF:` → ustawia `is_handoff=1`, `handoff_to`
   - Upsert: reimport nadpisuje istniejącą wersję (nie duplikuje)

   ```
   py tools/workflow_import.py workflows/workflow_suggestions_processing.md
   py tools/workflow_import.py --all   # importuj wszystkie z workflows/
   ```

1.3. **Render** — `render.py workflow`:
   - Z DB → .md czytelny dla człowieka
   - Opcje: `--workflow-id X` (konkretny) lub `--list` (lista dostępnych)

1.4. **Walidacja przy import:**
   - Brak `step_id` → error (nie importuj)
   - Brak `workflow_id` w YAML header → error
   - Human-readable (05R) bez strict steps → warning, skip (nie blokuje)
   - Raport: imported N steps, M decisions, K exit gates

1.5. **Testy:**
   - Import istniejącego workflow (np. `workflow_suggestions_processing.md`)
   - Import workflow z HANDOFF_POINT → `is_handoff=1` w DB
   - Import workflow z decision points → `workflow_decisions` populated
   - Re-import (upsert) → nie duplikuje, nadpisuje
   - Edge case: workflow bez strict steps → warning, skip
   - Render → .md output czytelny, zawiera kroki i exit gates

### Exit gate

- [x] Tabele DB istnieją (migracja done) — `ca57b4d`
- [x] Import poprawnie ładuje ≥2 workflow do DB — convention_creation (19 steps), suggestions_processing (17 steps)
- [x] Render produkuje czytelne .md z DB — `render.py workflow --list` / `--workflow-id`
- [x] Testy PASS — 27 testów w `test_workflow_import.py`

### Forward-compatibility

Schema `workflow_steps` to de facto step library — każdy krok to wiersz w DB.
Przejście do composable workflows (suggestion #498) = dodanie:
- `step_templates` (reużywalne klocki)
- `workflow_compositions` (które klocki, w jakiej kolejności, per rola)
Bez migracji istniejących danych — obecne tabele pozostają.

---

## Faza 2: State Machine Engine

**Owner:** Developer
**Input:** tabele `workflow_steps`, `workflow_decisions` (Faza 1) + istniejące `workflow_execution`, `step_log`
**Output:** moduł `tools/lib/workflow_engine.py`

### Zadania

2.1. **Klasa `WorkflowEngine`** z API:
```python
class WorkflowEngine:
    def __init__(self, db_path: str):
        """Łączy się z DB. Workflow definitions czytane z tabel, nie z plików."""

    def start(self, workflow_id: str, role: str, session_id: str) -> int:
        """Tworzy execution, zwraca execution_id.
        Waliduje: workflow_id istnieje w workflow_definitions."""

    def get_current_state(self, execution_id: int) -> StepState:
        """Zwraca bieżący krok (last PASS) + dozwolone przejścia."""

    def can_transition(self, execution_id: int, target_step: str) -> bool:
        """Czy przejście do target_step jest legalne z bieżącego stanu?"""

    def get_allowed_tools(self, execution_id: int) -> list[str]:
        """Jakie narzędzia są dozwolone w bieżącym kroku?"""

    def complete_step(self, execution_id: int, step_id: str,
                      evidence: dict | None = None) -> StepResult:
        """Próba zamknięcia kroku. Wywołuje verifier (Faza 4).
        Zwraca PASS/BLOCKED z uzasadnieniem."""

    def end(self, execution_id: int, status: str) -> None:
        """Zamyka execution."""
```

2.2. **State resolution** — bieżący stan obliczany z DB:
```sql
-- Bieżący krok
SELECT step_id, status FROM step_log
WHERE execution_id = ? ORDER BY timestamp DESC LIMIT 1

-- Dozwolone przejścia (z workflow_steps)
SELECT next_step_pass, next_step_fail FROM workflow_steps
WHERE workflow_id = ? AND workflow_version = ? AND step_id = ?
```
   - Jeśli brak wpisów → stan = pierwszy krok (sort_order=1)
   - Jeśli last = PASS → stan = `next_step_pass` tego kroku
   - Jeśli last = IN_PROGRESS/FAIL/BLOCKED → stan = ten sam krok

2.3. **Adjacency validation** — `can_transition` sprawdza czy `target_step`
     jest w dozwolonych przejściach z `workflow_steps` (next_step_pass/fail).

2.4. **HANDOFF detection** — jeśli bieżący krok ma `is_handoff=1` w `workflow_steps`:
   - `get_allowed_tools()` zwraca tylko `agent_bus_cli` (send/flag)
   - Przejście do następnego kroku zablokowane do odblokowania

2.5. **Exploratory workflow** — `workflow-start --workflow-id exploratory`:
   - Tworzy execution bez definicji w DB (brak wierszy w workflow_steps)
   - `can_transition()` → zawsze True (brak grafu = brak ograniczeń)
   - `get_allowed_tools()` → ALL (brak step-level restrictions)
   - `step-log` akceptuje dowolne `step_id` (agent loguje co robi, freeform)
   - Na `workflow-end`: zebrane step_ids → materiał do formalizacji przez PE
   - Cel: tracking + audit trail bez enforcement (research, spike, pierwsze wykonanie)

2.6. **Brak runtime parsowania** — engine czyta z DB. Żadnego .md w hot path.
     DB = source of truth. Import (Faza 1) jest jednorazowy per wersja workflow.

2.7. **Integracja z istniejącym CLI:**
   - `workflow-start` → deleguje do `WorkflowEngine.start()`
   - `step-log` → deleguje do `WorkflowEngine.complete_step()`
   - `workflow-end` → deleguje do `WorkflowEngine.end()`

2.8. **Testy:**
   - Happy path: start → step1 PASS → step2 PASS → end completed
   - Blocked: step1 FAIL → nie można przejść do step2
   - HANDOFF: krok handoff blokuje przejście
   - Resume: interrupted workflow → get_current_state zwraca ostatni PASS
   - Invalid transition: step1 → step3 (skip step2) → rejected
   - Exploratory: start exploratory → dowolne step-log → end → lista kroków

### Exit gate

- [x] WorkflowEngine poprawnie zarządza przejściami stanów — `tools/lib/workflow_engine.py`
- [x] can_transition blokuje nielegalne przejścia — 24 testów
- [x] HANDOFF blokuje automatyczne przejście — 5 testów handoff
- [x] Testy PASS (24 scenariuszy) — `tests/test_workflow_engine.py`
- [x] CLI integracja (soft mode) — workflow-start warning, step-log validation

---

## Faza 3: Hook Integration (soft mode)

**Owner:** Developer
**Input:** `WorkflowEngine` + istniejący `pre_tool_use.py`
**Output:** rozszerzony `pre_tool_use.py` z workflow awareness

### Zadania

3.1. **Detekcja aktywnego workflow** — hook sprawdza:
   - Env var `MROWISKO_EXECUTION_ID` (ustawiony przez workflow-start)
   - LUB query DB: `SELECT id FROM workflow_execution WHERE session_id=? AND status='running'`

3.2. **Soft mode (WARNING):**
   - Agent bez aktywnego workflow → hook loguje warning do stderr
     (widoczne dla agenta, nie blokuje)
   - Agent z workflow, ale tool call niezgodny z bieżącym krokiem → log warning
   - Metryka: ile razy warning się pojawia → dane do decyzji o przejściu do hard mode

3.3. **Exempt tools** — niektóre narzędzia nigdy nie są blokowane:
   - `Read`, `Glob`, `Grep` — odczyt jest zawsze dozwolony
   - `agent_bus_cli.py` — komunikacja zawsze dozwolona
   - `context_usage.py` — monitoring zawsze dozwolony

3.4. **Tracking untracked work:**
   - Nowy status w step_log: `UNTRACKED`
   - Hook loguje tool calls poza workflow jako `UNTRACKED` do osobnej tabeli
     lub z execution_id=NULL

3.5. **Testy:**
   - Hook z aktywnym workflow → no warning
   - Hook bez workflow → warning logged
   - Hook z workflow, wrong tool → warning logged
   - Exempt tools → no warning regardless

### Exit gate

- [x] Hook wykrywa obecność/brak workflow — query DB po session_id, throttled 30s
- [x] Warnings logowane (nie blokują) — stderr warning, soft mode
- [x] Dane o untracked work zbierane — step_log z execution_id=0, status=UNTRACKED
- [x] Testy PASS — 67 testów (5 nowych workflow awareness)
- [ ] Deploy na 1 tydzień → zebrać metryki

---

## Faza 4: Step Verification

**Owner:** Developer
**Input:** `WorkflowDefinition.verification` + `WorkflowEngine.complete_step()`
**Output:** moduł `tools/lib/step_verifier.py`

### Zadania

4.1. **Klasa `StepVerifier`** z dispatched verification:
```python
class StepVerifier:
    def verify(self, step_def: StepDef, evidence: dict) -> VerifyResult:
        """Sprawdza czy artefakt istnieje / warunek spełniony."""

    # Dispatch per verification type:
    def _verify_file_exists(self, path: str) -> bool
    def _verify_test_pass(self, test_path: str) -> bool
    def _verify_commit_exists(self, pattern: str) -> bool
    def _verify_message_sent(self, message_id: int) -> bool
    def _verify_manual(self) -> bool  # always True
```

4.2. **Verification types** (mapowane z `verification` field w step definition):
   | Type | Jak sprawdza | Auto? |
   |------|-------------|-------|
   | `file_exists` | `os.path.exists(path)` | tak |
   | `file_not_empty` | `os.path.getsize(path) > 0` | tak |
   | `test_pass` | `subprocess pytest --tb=no -q` exit code | tak |
   | `commit_exists` | `git log --oneline -1 --grep=pattern` | tak |
   | `message_sent` | query `messages` table by ID | tak |
   | `git_clean` | `git status --porcelain` empty | tak |
   | `manual` | zawsze PASS (human/semantic review) | nie |

4.3. **Integracja z `complete_step()`:**
   - `step-log --step-id X --status PASS` → engine wywołuje verifier
   - Verifier PASS → krok zamknięty
   - Verifier FAIL → krok pozostaje IN_PROGRESS, error message do agenta

4.4. **Graceful degradation:**
   - Workflow bez `verification` field → typ `manual` (domyślny)
   - Verifier nie blokuje retroaktywnie — dotyczy tylko nowych step-log calls

4.5. **Testy:**
   - file_exists: plik jest / nie ma → PASS/FAIL
   - test_pass: testy przechodzą / failują
   - commit_exists: commit z wzorcem / brak
   - manual: zawsze PASS

### Exit gate

- [ ] Verifier poprawnie sprawdza ≥4 typy artefaktów
- [ ] complete_step odmawia PASS gdy verifier fails
- [ ] Testy PASS

---

## Faza 5: Hook Enforcement (hard mode)

**Owner:** Developer
**Input:** metryki z Fazy 3 (ile untracked tool calls)
**Output:** rozszerzony `pre_tool_use.py` z enforcement mode

### Zadania

5.1. **Configuration** — tryb enforcement w config/env:
   ```
   MROWISKO_WORKFLOW_ENFORCEMENT=soft|medium|hard
   ```
   - `soft` = warnings only (Faza 3)
   - `medium` = blokuj Write/Edit/Bash bez workflow, pozwól Read/Grep/Glob
   - `hard` = blokuj ALL non-exempt tools bez workflow

5.2. **Deny z repair message:**
   ```
   "Brak aktywnego workflow. Wywołaj: py tools/agent_bus_cli.py workflow-start
    --workflow-id <ID> --role <rola> przed kontynuacją."
   ```

5.3. **Step-level enforcement (medium+):**
   - Agent w workflow, ale tool call niezgodny z bieżącym krokiem:
   ```
   "Bieżący krok: verify_git (tool: Bash, command: git status).
    Nie możesz użyć Write dopóki ten krok nie ma status PASS."
   ```

5.4. **Override mechanism:**
   - Env var `MROWISKO_WORKFLOW_OVERRIDE=1` wyłącza enforcement (emergency)
   - Logowane jako `OVERRIDE` w step_log

5.5. **Testy:**
   - soft: tool call bez workflow → warning, allowed
   - medium: Write bez workflow → denied
   - medium: Read bez workflow → allowed
   - hard: any tool bez workflow → denied (except exempt)
   - override: tool call z override → allowed + logged

### Exit gate

- [ ] Enforcement modes działają zgodnie z konfiguracją
- [ ] Deny messages zawierają actionable repair instructions
- [ ] Override mechanism działa i loguje
- [ ] Testy PASS

---

## Faza 6: HANDOFF Enforcement

**Owner:** Developer
**Input:** HANDOFF_POINT z WorkflowDefinition + WorkflowEngine
**Output:** rozszerzony engine + CLI

### Zadania

6.1. **HANDOFF state w engine:**
   - Krok z `is_handoff=True` → stan = `AWAITING_HANDOFF`
   - W tym stanie: tylko `agent_bus_cli` dozwolone (send, flag, handoff)
   - Przejście do następnego kroku zablokowane

6.2. **Odblokowanie HANDOFF:**
   - Automatyczne: message od `handoff_to` roli w agent_bus → engine sprawdza
   - Manualne: `py tools/agent_bus_cli.py workflow-resume --execution-id X`
   - Human override: user mówi "kontynuuj" → session_init / hook odblokuje

6.3. **Timeout warning:**
   - HANDOFF state >30 min → log warning (informacyjnie, nie blokuje)

6.4. **Testy:**
   - Krok handoff → tylko agent_bus dozwolone
   - Próba Write w stanie AWAITING_HANDOFF → denied
   - workflow-resume → odblokowanie → kontynuacja
   - Auto-resume po message od target roli

### Exit gate

- [ ] HANDOFF_POINT blokuje przejście
- [ ] Odblokowanie działa (manual + auto)
- [ ] Testy PASS

---

## Faza 0-prep: Konwersja workflow do strict format

**Owner:** Prompt Engineer
**Kiedy:** równolegle z Fazą 1-2 (nie blokuje, ale potrzebne przed Fazą 3)

### Zadania

0.1. **Audit istniejących workflow** — które są strict (04R), które human-readable (05R):
   - `workflows/workflow_suggestions_processing.md` — sprawdź format
   - `workflows/workflow_developer.md` — multi-scenario, wymaga rozbicia (msg #426)
   - Pozostałe 8 workflow → audit

0.2. **Konwersja top 3 workflow do strict format:**
   - Priority 1: `workflow_suggestions_processing` (najczęściej używany)
   - Priority 2: `workflow_convention_creation` (tu był violation)
   - Priority 3: `workflow_code_review` (gate quality)

0.3. **Rozbicie workflow_developer.md** na osobne workflow per scenariusz (msg #426):
   - `workflow_developer_new_tool.md`
   - `workflow_developer_bug_fix.md`
   - `workflow_developer_patch.md`
   - Każdy z własnym `workflow_id`

### Exit gate

- [ ] ≥3 workflow w formacie strict (04R) z step_id, verification, next_step
- [ ] workflow_developer.md rozbity na ≥2 osobne pliki

---

## Kolejność wdrożenia i zależności

```
Faza 0-prep (PE) ─────────────────────────────────────────┐
     │ (równolegle)                                        │
     ▼                                                     ▼
Faza 1 (DB+Import) ──→ Faza 2 (Engine) ──┬──→ Faza 3 (Hook soft)
                                       │          │
                                       │          ▼
                                       │   [1 tydzień metryki]
                                       │          │
                                       ├──→ Faza 4 (Verifier)
                                       │          │
                                       ▼          ▼
                                  Faza 6 (HANDOFF) │
                                                   ▼
                                            Faza 5 (Hook hard)
```

**Critical path:** Faza 1 (DB+Import) → Faza 2 (Engine) → Faza 3 (soft mode deploy).
Pozostałe fazy mogą być wdrażane równolegle po Fazie 2.

**Nowy element Fazy 0-prep:** PE po konwersji do strict .md uruchamia `workflow_import.py`
żeby załadować definicje do DB. Import = warunek wejścia do Fazy 2 testów.

---

## Backlog items do aktualizacji

| Backlog ID | Akcja | Uzasadnienie |
|-----------|-------|-------------|
| #60 | Status → `superseded` | Subsumowany przez ADR-002 |
| arch_uplift Faza 7 | Powiązać z ADR-002 | To jest realizacja Fazy 7 |

---

## Kryteria sukcesu (mierzalne)

1. **Faza 3 deployed:** ≥80% tool calls w workflow ma execution_id (vs baseline ~0%)
2. **Faza 4 deployed:** ≥90% step-log PASS ma automatyczną weryfikację artefaktu
3. **Faza 5 deployed:** 0 naruszeń workflow w ciągu 2 tygodni od włączenia hard mode
4. **Faza 6 deployed:** 0 HANDOFF_POINT pominiętych (agent czeka na odpowiedź)

---

## Ryzyka

| Ryzyko | Prawdopodobieństwo | Impact | Mitygacja |
|--------|-------------------|--------|-----------|
| Workflow definitions niekompletne → false blocks | wysokie (start) | wysoki | Faza A (soft) zbiera dane przed blokowaniem |
| Agent obchodzi enforcement (np. pisze do pliku przez Bash zamiast Write) | niskie | sredni | Bash hook już istnieje, rozszerzamy |
| Overhead per tool call spowalnia pracę | niskie | niski | SQLite query ~1ms, cache definition |
| Zbyt wiele workflow do konwersji na strict + import | srednie | sredni | Priorytetyzacja top 3, reszta gradualnie |
| User override ("zrób mimo braku workflow") | srednie | sredni | Override logowany, metryki, review |
