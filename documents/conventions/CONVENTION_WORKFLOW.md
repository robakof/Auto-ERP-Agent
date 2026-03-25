---
convention_id: workflow-convention
version: "1.4"
status: active
created: 2026-03-24
updated: 2026-03-24
author: prompt_engineer
owner: prompt_engineer
approver: dawid
audience: [prompt_engineer, architect, metodolog]
scope: "Definiuje strukturę i składnię dokumentów workflow dla agentów"
---

# CONVENTION_WORKFLOW — Składnia i struktura workflow

## TL;DR

- Workflow = YAML header (metadata) + outline (etapy z lotu ptaka) + markdown body (fazy/kroki)
- YAML header: `workflow_id`, `version`, `owner_role`, `trigger`, `participants`, `related_docs`
- Kroki numerowane: 1.1, 1.2, 1.1.1 (hierarchia dziesiętna)
- Strict format kroków: `step_id`, `action`, `tool`, `command`, `verification`, `on_failure`, `next_step`
- Exit gate = checklist z `item_id` i boolean checks
- Forbidden = opcjonalna sekcja dla znanych pułapek

---

## Zakres

**Pokrywa:**
- Struktura dokumentów workflow (YAML header, outline, sekcje)
- Format kroków (human-readable i DB-ready)
- Decision points i branching logic
- Exit gates i walidacja

**NIE pokrywa:**
- Treść konkretnych workflow (to ich ownerzy)
- Implementacja orchestratora (to Developer)
- Validation hooks implementation (future — czeka na research)
- Context loading/chunking (future — planowane, nie wdrożone)

**Kiedy tworzyć workflow:**
- Proces powtarza się (≥2 razy)
- Proces ma >3 kroki
- Proces wymaga gate'ów (verification, approval, safety checks)
- Proces ma pułapki (znane anti-patterns)
- Proces wymaga koordynacji między fazami/rolami

**Kiedy NIE tworzyć workflow:**
- Jednorazowe zadanie
- Prosty proces (≤3 kroki, oczywiste)
- Proces wciąż eksperymentalny (stabilizuj go najpierw)

---

## Kontekst

### Problem

Bez CONVENTION_WORKFLOW:
- Każdy workflow ma inną strukturę
- Nie można parsować workflow do DB (orchestrator)
- Brak walidowalnych exit gates
- Trudno się zapoznać z workflow (brak outline)

### Rozwiązanie

CONVENTION_WORKFLOW definiuje:
1. **Machine-readable header** — YAML parseable do DB
2. **Outline** — etapy z lotu ptaka na górze dokumentu
3. **Strict step format** — kroki z explicit tool, verification, error handling
4. **Exit gates** — walidowalne checklisty

---

## Reguły

### 01R: YAML Header wymagany

Każdy workflow MUSI zaczynać od YAML header:

```yaml
---
workflow_id: string           # unique identifier (snake_case)
version: string               # "1.0", "1.1", etc.
owner_role: string            # główna rola wykonująca
trigger: string               # kiedy uruchamiany (natural language)
participants: list            # [opcjonalne] wszystkie zaangażowane role
related_docs: list            # [opcjonalne] powiązane dokumenty
prerequisites: list           # [opcjonalne] warunki przed startem
outputs: list                 # [opcjonalne] artefakty które workflow produkuje
---
```

**Przykład:**
```yaml
---
workflow_id: erp_columns_creation
version: "1.0"
owner_role: erp_specialist
trigger: "Użytkownik prosi o utworzenie kolumny ERP"
participants:
  - erp_specialist
  - human (approval)
related_docs:
  - documents/erp_specialist/ERP_SQL_SYNTAX.md
  - documents/erp_specialist/ERP_SCHEMA_PATTERNS.md
prerequisites:
  - schema_loaded
  - session_init_done
outputs:
  - type: file
    path: "solutions/bi/columns/{NazwaKolumny}_draft.sql"
  - type: state
    field: column_created
---
```

**Output types:**
- `type: file` + `path` — plik
- `type: state` + `field` — zmiana stanu systemu
- `type: backlog_item` — utworzenie backlog item
- `type: commit` — git commit
- `type: message` — wiadomość przez agent_bus
- `type: suggestion` — sugestia
- `type: log` — wpis w session_log

---

### 02R: Outline na górze dokumentu

Po YAML header, każdy workflow MUSI mieć outline — etapy z lotu ptaka:

```markdown
## Outline

1. **Inicjalizacja** — weryfikacja kontekstu i wymagań
2. **Discovery** — analiza schematu i wzorców
3. **Implementacja** — tworzenie SQL
4. **Weryfikacja** — testy i review
5. **Deployment** — commit i dokumentacja
```

**Dlaczego:**
- Szybkie zapoznanie się z workflow
- Kontekst dla agenta przed szczegółami
- Nawigacja w długich dokumentach

---

### 03R: Struktura dokumentu

Każdy workflow MUSI mieć strukturę:

```markdown
---
[YAML header]
---

# Workflow: [Nazwa]

[Opis — 1-2 zdania. Dla kogo, kiedy używać.]

## Outline

[Etapy z lotu ptaka — numerowana lista]

---

## [Opcjonalnie: Routing]

[Tabela routing jeśli workflow obsługuje multiple scenarios]

---

## [Nazwa fazy/sekcji]

**Owner:** [rola wykonująca]

### Inputs required (opcjonalne)
[Co musi istnieć PRZED fazą — patrz 12R]

### Steps
[Kroki wykonania]

### Required artifacts (opcjonalne)
[Co faza MUSI wyprodukować — patrz 12R]

### Forbidden (opcjonalne)
[Anti-patterns dla tej fazy — tylko jeśli są znane pułapki]

### Exit gate
[Warunki przejścia]

### Self-check (opcjonalne)
[Checklist przed zakończeniem — patrz 12R]

### Output format (opcjonalne, DB-ready)
[JSON schema outputu — patrz 12R]

### Handoff rule (opcjonalne)
[Kiedy i do kogo przekazać — patrz 12R]

---

[Powtórz dla każdej fazy]
```

---

### 04R: Format kroków — Strict (DB-Ready)

Dla workflow które będą DB-driven, każdy krok MUSI mieć format:

```markdown
## Step [numer]: [Nazwa]

**step_id:** [unique_identifier]
**action:** [Co robisz — 1 zdanie imperatyw]
**tool:** [Bash|Read|Write|Edit|Grep|Glob|agent_bus_cli|custom]
**command:** `[dokładna komenda]`
**verification:** [Jak sprawdzić success?]
**on_failure:**
  - retry: [yes|no]
  - skip: [yes|no]
  - escalate: [yes|no]
  - reason: "[Dlaczego fail? Co zrobić?]"
**next_step:** [step_id] (if PASS), [action] (if FAIL)
```

**Przykład:**
```markdown
## Step 1: Weryfikacja Git Status

**step_id:** verify_git_clean
**action:** Sprawdź czy working tree czysty
**tool:** Bash
**command:** `git status`
**verification:** Output zawiera "nothing to commit, working tree clean"
**on_failure:**
  - retry: no
  - skip: no
  - escalate: yes
  - reason: "Niezcommitowane zmiany blokują workflow. Użytkownik musi commitować lub stash."
**next_step:** group_suggestions (if PASS), escalate (if FAIL)
```

**Zagnieżdżenia:** Dla sub-kroków użyj step_id z hierarchią:
- `step_1`
- `step_1_1` (sub-krok)
- `step_1_1_1` (sub-sub-krok)

---

### 05R: Format kroków — Human-readable (Simple)

Dla prostych workflow można użyć formatu human-readable:

```markdown
### Steps

1. [Krok główny]
   1.1. [Sub-krok]
   1.2. [Sub-krok]
      1.2.1. [Sub-sub-krok]

2. [Kolejny krok główny]
   2.1. [Sub-krok]
```

**Zasady:**
- Hierarchia dziesiętna: 1, 1.1, 1.1.1 (nie 1a, 1b)
- Imperatyw: "Sprawdź", "Utwórz", "Wyślij"
- Konkretność: podaj ścieżki, komendy, wzorce
- Warunki: "Jeśli X → Tak. Jeśli Y → Nie."

**Uwaga:** Jeśli workflow będzie DB-driven → wszystkie kroki MUSZĄ być w formacie strict (04R).

---

### 06R: Decision Points

Workflow z conditional paths MUSI mieć explicit decision points:

```markdown
## Decision Point [numer]: [Nazwa]

**decision_id:** [unique_identifier]
**condition:** [Boolean expression lub check]
**path_true:** [step_id lub action]
**path_false:** [step_id lub action]
**default:** [action jeśli indeterminate]
```

**Przykład:**
```markdown
## Decision Point 1: Sprawdzenie Extraction Ratio

**decision_id:** check_extraction_ratio
**condition:** extracted_count / total_count >= 0.10
**path_true:** close_suggestions (kontynuuj workflow)
**path_false:** escalate_to_user (review needed — ratio za niski)
**default:** escalate_to_user (jeśli counts niedostępne)
```

---

### 07R: Exit Gate — Checklist

Każda faza MUSI kończyć się exit gate:

**Format DB-ready:**
```markdown
### Exit Gate

**Checklist:**
- [ ] `item_id_1`: [Konkretny warunek]
- [ ] `item_id_2`: [Konkretny warunek]

**Status:**
- PASS if: wszystkie checklist items == true
- BLOCKED if: [item_id] == false → [action]
- RETRY if: [item_id] == false → agent może naprawić
```

**Format human-readable:**
```markdown
### Exit gate

PASS jeśli [warunek].
BLOCKED jeśli [warunek — co blokuje?].
ESCALATE jeśli [warunek — kiedy eskalować?].
```

---

### 08R: Owner i Participants

Każda faza/sekcja MUSI mieć `**Owner:** [rola]`.

W YAML header użyj `participants` gdy workflow wymaga wielu ról (w tym human):
```yaml
participants:
  - erp_specialist
  - human (approval)
  - developer (review)
```

Jeśli workflow przechodzi między rolami — wyraźnie oznacz handoff.

---

### 09R: Konkretność kroków

Każdy krok MUSI być wykonalny bez zgadywania:
- Podaj dokładne ścieżki plików
- Podaj dokładne komendy
- Podaj decision tree (jeśli X → Y)

---

### 10R: Forbidden = pułapki z praktyki (opcjonalne)

Sekcja Forbidden jest **opcjonalna** — dodawaj tylko gdy są znane pułapki.

Jeśli dodajesz, pisz konkretne pułapki, nie teoretyczne błędy:
- ✓ "Nie używaj `git mv` per plik — hook blokuje; używaj `mv` potem `git add -A`"
- ✗ "Nie rób literówek" (zbyt ogólne)

---

### 11R: Lokalizacja workflow

Wszystkie workflow żyją w: `workflows/workflow_[nazwa].md`

**Wzorzec nazewnictwa:** `workflow_` jako prefix (od ogółu do szczegółu).

Convention żyje w: `documents/conventions/CONVENTION_WORKFLOW.md`

---

### 12R: Extended phase template — opcjonalne sekcje per faza

Fazy mogą zawierać dodatkowe sekcje zwiększające precision i automatyzowalność.
Wszystkie sekcje w 12R są **opcjonalne** — dodawaj gdy faza tego wymaga.
Dla workflow DB-ready zalecane jest użycie wszystkich.

**Guidance:** Dla prostych workflow max 4 sekcje per faza (Owner, Steps, Exit gate + 1 opcjonalna).
Dodawaj więcej sekcji tylko gdy faza jest złożona lub multi-role.

**Sekcje:**

#### Inputs required
Co MUSI istnieć PRZED rozpoczęciem fazy:
- Artefakty z poprzedniej fazy (pliki, stany)
- Warunki zewnętrzne (git clean, schema loaded)
- Dane wejściowe (format, schema)

```markdown
### Inputs required
- [ ] `artifact_id`: [opis — co musi istnieć]
- [ ] `state_condition`: [warunek stanu systemu]
```

**Reguła:** Jeśli inputs required nie są spełnione → faza nie startuje (status: BLOCKED).

#### Required artifacts
Co faza MUSI wyprodukować — lista artefaktów z identyfikatorami:

```markdown
### Required artifacts
- [ ] `artifact_id`: [opis — co faza produkuje, typ, ścieżka]
```

**Mapowanie na output types z 01R:** file, state, backlog_item, commit, message, suggestion, log.

#### Self-check
Checklist dla agenta PRZED oznaczeniem fazy jako PASS:

```markdown
### Self-check
- [ ] Czy wszystkie kroki zostały wykonane?
- [ ] Czy wszystkie required artifacts istnieją?
- [ ] Czy exit gate jest spełniony?
- [ ] Jeśli nie → BLOCKED, nie PASS.
```

**Źródło wzorca:** Anthropic zaleca self-check relative to criteria przed zakończeniem fazy.
**Cel:** Redukcja "zatwierdzenia z rozpędu" — agent sprawdza siebie zanim zadeklaruje PASS.

#### Output format (DB-ready)
JSON schema outputu fazy — dla orchestratora:

```markdown
### Output format
```json
{
  "phase": "<PHASE_NAME>",
  "status": "PASS|BLOCKED|ESCALATE",
  "artifacts": ["artifact_id_1", "artifact_id_2"],
  "missing_items": [],
  "verification_summary": ""
}
```
```

**Kiedy dodawać:** Tylko dla workflow DB-driven. Dla human-readable workflow — pomiń.

#### Handoff rule
Kiedy i do kogo można przekazać wynik fazy:

```markdown
### Handoff rule
Przekazanie do [rola] tylko przy status=PASS.
Handoff payload: [co musi zawierać].
```

**Reguła:** Bez handoff rule orchestrator nie wie kiedy i do kogo przekazać.
Jeśli workflow jest jednoosobowy (jedna rola, wszystkie fazy) — handoff rule zbędne.

---

### 13R: HANDOFF_POINT — jawne przekazanie kontroli

Każde miejsce w workflow gdzie kontrola przechodzi do innej roli lub człowieka MUSI być oznaczone jako HANDOFF_POINT. Agent widząc HANDOFF_POINT **zatrzymuje się** i czeka na odpowiedź — nie przechodzi dalej samodzielnie.

**Format:**
```markdown
→ HANDOFF: [rola | human]. STOP.
  Mechanizm: [agent_bus send <rola> | agent_bus flag | czekaj na user input]
  Czekaj na: [co musi wrócić — opis artefaktu lub odpowiedzi]
  Nie przechodź do [następny krok] bez otrzymania odpowiedzi.
```

**Przykład:**
```markdown
3. Wyślij pytania badawcze do PE.
   ```
   py tools/agent_bus_cli.py send --from architect --to prompt_engineer --content-file tmp/research_questions.md
   ```
   → HANDOFF: prompt_engineer. STOP.
     Mechanizm: agent_bus send
     Czekaj na: research prompt od PE w inbox.
     Nie przechodź do kroku 4 bez otrzymania promptu.
```

**Kiedy stosować:**
- Agent zleca task innej roli i potrzebuje wyniku przed kontynuacją
- Agent czeka na decyzję / zatwierdzenie człowieka
- Workflow przechodzi między fazami obsługiwanymi przez różne role

**Czego NIE robić:**
- Nie wykonuj kroku należącego do innej roli (scope leak)
- Nie zakładaj że skoro wysłałeś wiadomość, to możesz kontynuować
- Nie interpretuj braku odpowiedzi jako zgody

---

**Pełna kolejność sekcji per faza:**
1. Owner
2. Inputs required (opcjonalne)
3. Steps
4. Required artifacts (opcjonalne)
5. Forbidden (opcjonalne)
6. Exit gate
7. Self-check (opcjonalne)
8. Output format (opcjonalne, DB-ready)
9. Handoff rule (opcjonalne)

---

## Przykłady

### Przykład 1: Dwa style workflow

**Styl A: Liniowy (fazy sekwencyjne)**

Użyj gdy:
- Proces ma jasne fazy (discovery → implementation → verification)
- Każda faza ma purpose i exit gate
- Proces techniczny (SQL, data pipeline, deployment)

```
Inicjalizacja
Faza 0 — Discovery
Faza 1 — Implementacja
Faza 2 — Weryfikacja
Faza 3 — Deployment
```

**Styl B: Multi-scenario (routing)**

Użyj gdy:
- Workflow obsługuje różne typy zadań (tool/bug/patch)
- Każdy typ ma inny flow
- Proces operacyjny (developer daily work)

```
Routing table (typ zadania → sekcja)
Sekcja A: Narzędzie (Tool)
Sekcja B: Bug fix
Sekcja C: Patch
```

---

### Przykład 2: Template DB-ready (pełny)

```markdown
---
workflow_id: workflow_nazwa
version: "1.0"
owner_role: erp_specialist
trigger: "Użytkownik prosi o X"
participants:
  - erp_specialist
  - human (approval)
related_docs:
  - documents/erp_specialist/ERP_SQL_SYNTAX.md
prerequisites:
  - session_init_done
outputs:
  - type: file
    path: "solutions/output.sql"
---

# Workflow: Nazwa Procesu

Krótki opis — 1-2 zdania. Dla kogo, kiedy używać.

## Outline

1. **Inicjalizacja** — weryfikacja kontekstu
2. **Discovery** — analiza wymagań
3. **Implementacja** — tworzenie artefaktu
4. **Weryfikacja** — testy i review
5. **Zamknięcie** — commit i dokumentacja

---

## Faza 1: Inicjalizacja

**Owner:** erp_specialist

### Inputs required
- [ ] `session_init_done`: session_init wykonany z rolą erp_specialist
- [ ] `user_request`: Użytkownik podał wymagania (okno, kolumna, cel)

### Steps

## Step 1: Weryfikacja Git Status

**step_id:** verify_git_clean
**action:** Sprawdź czy working tree czysty
**tool:** Bash
**command:** `git status`
**verification:** Output zawiera "nothing to commit"
**on_failure:**
  - retry: no
  - escalate: yes
  - reason: "Niezcommitowane zmiany. Commit lub stash."
**next_step:** load_schema (if PASS), escalate (if FAIL)

---

## Decision Point 1: Schema Check

**decision_id:** check_schema_loaded
**condition:** Plik schema.json istnieje i ma >0 bytes
**path_true:** Faza 2 (kontynuuj)
**path_false:** load_schema (załaduj schema)
**default:** escalate (jeśli błąd odczytu)

### Required artifacts
- [ ] `git_status_clean`: Working tree czysty (type: state)
- [ ] `schema_available`: Schema załadowana do kontekstu (type: state)

### Exit Gate

**Checklist:**
- [ ] `git_clean`: Working tree czysty
- [ ] `schema_loaded`: Schema dostępna

**Status:**
- PASS if: wszystkie == true
- BLOCKED if: git_clean == false → escalate

### Self-check
- [ ] Czy git status sprawdzony?
- [ ] Czy schema załadowana i dostępna?
- [ ] Czy user request jest zrozumiały (nie wymaga dopytania)?
- [ ] Jeśli nie → BLOCKED, nie PASS.

### Output format
```json
{
  "phase": "initialization",
  "status": "PASS|BLOCKED",
  "artifacts": ["git_status_clean", "schema_available"],
  "missing_items": [],
  "verification_summary": "Git clean, schema loaded, requirements clear"
}
```

### Handoff rule
Przekazanie do Fazy 2 (Discovery) tylko przy status=PASS.
Wewnętrzne — ta sama rola (erp_specialist).

---

## Faza 2: Discovery
...
```

---

### Przykład 3: Template Human-readable (prosty)

```markdown
---
workflow_id: workflow_prosta_nazwa
version: "1.0"
owner_role: developer
trigger: "Prosty task do wykonania"
---

# Workflow: Prosta Nazwa

Opis — 1-2 zdania.

## Outline

1. **Przygotowanie** — sprawdź kontekst
2. **Wykonanie** — zrób task
3. **Zamknięcie** — commit

---

## Faza 1: Przygotowanie

**Owner:** developer

### Steps

1. Sprawdź `git status`. Jeśli brudny → zapytaj czy commitować.
2. Wczytaj wymagania z `docs/requirements.md`.
   2.1. Zweryfikuj że plik istnieje.
   2.2. Przeczytaj sekcję "Scope".

### Exit gate

PASS jeśli git czysty i requirements wczytane.

---
```

---

## Antywzorce

### 01AP: Workflow bez YAML header

**Źle:**
```markdown
# Workflow: Coś tam

Jakieś kroki...
```

**Dlaczego:** Nie parseable do DB, orchestrator nie wie co to za workflow.

**Dobrze:**
```yaml
---
workflow_id: workflow_cos_tam
version: "1.0"
owner_role: developer
trigger: "..."
---
```

---

### 02AP: Krok bez verification

**Źle:**
```markdown
## Step 1: Utwórz plik

**action:** Utwórz plik
**tool:** Write
**command:** `Write solutions/output.sql`
```

**Dlaczego:** Orchestrator nie wie jak sprawdzić czy krok się powiódł.

**Dobrze:**
```markdown
**verification:** Plik istnieje w solutions/output.sql AND rozmiar > 0
```

---

### 03AP: Decision embedded w step text

**Źle:**
```markdown
1.2. Jeśli git brudny → zapytaj użytkownika, jeśli czysty → kontynuuj
```

**Dlaczego:** Nie parseable, orchestrator nie widzi branching logic.

**Dobrze:**
```markdown
## Decision Point 1: Git Status

**decision_id:** check_git_clean
**condition:** git status == "nothing to commit"
**path_true:** Step 2
**path_false:** escalate_to_user
```

---

### 04AP: Exit gate vague

**Źle:**
```markdown
### Exit gate

PASS jeśli wszystko zrobione.
```

**Dlaczego:** "Wszystko" nie jest sprawdzalne.

**Dobrze:**
```markdown
**Checklist:**
- [ ] `file_created`: Plik istnieje w ścieżce X
- [ ] `tests_passed`: Wszystkie testy zielone
```

---

### 05AP: Krok niekonkretny

**Źle:**
```markdown
1. Przygotuj dane do analizy.
```

**Dlaczego:** Agent nie wie co to znaczy "przygotuj".

**Dobrze:**
```markdown
1. Wczytaj dane z `data/input.csv` używając `Read`. Zwaliduj że ma ≥100 wierszy.
```

---

## Checklist PE: Workflow review

Przed zatwierdzeniem workflow, sprawdź:

**Wszystkie workflow:**
- [ ] YAML header kompletny (workflow_id, version, owner_role, trigger)?
- [ ] Outline na górze (etapy z lotu ptaka)?
- [ ] Każdy krok wykonalny bez zgadywania?
- [ ] Numeracja kroków spójna (1, 1.1, 1.1.1)?
- [ ] Exit gate warunki jasne i testowalne?
- [ ] Owner per faza?
- [ ] Nazewnictwo: `workflow_[nazwa].md`?

**DB-ready workflow (dodatkowo):**
- [ ] Każde przekazanie kontroli oznaczone jako HANDOFF_POINT (13R)?
- [ ] Każdy step ma step_id?
- [ ] Każdy step ma tool + command?
- [ ] Każdy step ma verification?
- [ ] Każdy step ma on_failure (retry/escalate + reason)?
- [ ] Każdy step ma next_step?
- [ ] Decision points explicit (decision_id, condition, paths)?
- [ ] Exit gate strict checklist (item_id per check)?

**Extended phase sections (12R — opcjonalne, zalecane dla DB-ready):**
- [ ] Inputs required: prerequisites z item_id per faza?
- [ ] Required artifacts: lista artefaktów z item_id per faza?
- [ ] Self-check: checklist przed PASS per faza?
- [ ] Output format: JSON schema per faza?
- [ ] Handoff rule: kto, kiedy, z czym per faza (jeśli multi-role)?

---

## References

- Obecne workflow: `workflows/workflow_developer.md`, `workflows/workflow_plan_review.md`, `workflows/workflow_code_review.md`, `workflows/workflow_suggestions_processing.md`
- CONVENTION_META: `documents/conventions/CONVENTION_META.md`
- Research (compliance): `documents/researcher/research/workflow_compliance.md`
- Research (orchestration): `documents/researcher/research/workflow_orchestration.md`

---

## Changelog

| Wersja | Data | Zmiany |
|---|---|---|
| 1.4 | 2026-03-25 | Poprawki po review Architekta (msg #288): usunięto duplikat pliku, zaktualizowano References (nowe workflow), dodano guidance max 4 sekcji per faza dla prostych workflow. DB schema i język migracyjny — brak (usunięte wcześniej). |
| 1.3 | 2026-03-25 | 13R: HANDOFF_POINT — jawne przekazanie kontroli między rolami. Checklist PE rozszerzony o weryfikację HANDOFF_POINT. |
| 1.2 | 2026-03-24 | 12R: Extended phase template — inputs required, required artifacts, self-check, output format, handoff rule. Rozszerzony template 03R i przykład DB-ready. PE checklist rozszerzony. Research references zaktualizowane. |
| 1.1 | 2026-03-24 | Dodano: outline, related_docs, participants, 7 output types, numeracja 1.1.1, Forbidden opcjonalny, nazewnictwo workflow_*, język polski |
| 1.0 | 2026-03-24 | Migracja do struktury CONVENTION_META |
