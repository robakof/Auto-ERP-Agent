# Plan podnoszenia architektury — Mrowisko 2.0

Cel: przejście od systemu agentów wyzwalanych ręcznie do autonomicznego roju z pełną
obserwowalnością. Każda faza jest niezależnie wartościowa i deployowalna.

Analiza koncepcyjna: `documents/dev/analiza_kierunki_2026-03-14.md`

---

## Faza 1 — Zapis sesji (w toku)

**Cel:** każda sesja jest identyfikowalna, każda wiadomość człowieka i agenta zapisana.

| id | Zadanie | Status |
|----|---------|--------|
| 47 | Zapis konwersacji do bazy — trace + conversation tables | w toku |
| 49 | on_stop zapisuje last_assistant_message + render sesji | planned |
| 50 | session_init — jeden tool call zamiast czytania 3-4 plików .md | planned |

**Wyniki E1-E3 (2026-03-14):**
- Hook UserPromptSubmit: działa, daje session_id + transcript_path + treść wiadomości
- Hook Stop: działa, daje last_assistant_message + transcript_path
- transcript_path → pełny .jsonl transkrypt sesji już istnieje — nie budujemy własnego trace
- Claude Code własne session_id zastępuje nasze UUID

**Następny krok:** on_stop.py zapisuje do conversation; zbadać strukturę .jsonl; skrócić CLAUDE.md

---

## Faza 2 — Wywoływanie agentów (✓ done)

**Cel:** agent może zlecić zadanie innemu agentowi bez człowieka w pętli.

| id | Zadanie | Status |
|----|---------|--------|
| 48 | Agent Launcher — wtyczka VS Code (M1: spawn+registry, M2: invocation, M3: auto-approve) | ✓ done |
| 51 | Approval gate (spawn-request → dialog → approve/reject) | ✓ done |
| 52 | Direct spawn + trusted pairs (auto-approve w config) | ✓ done |
|    | URI handler (agent z terminala steruje wtyczką) | ✓ done |
|    | sendText + read_transcript (agent pisze i czyta innego agenta) | ✓ done |

**PRD:** `documents/human/plans/PRD_agent_launcher.md`
**Architecture:** `documents/human/plans/ARCHITECTURE_agent_launcher.md`
**Commity:** `9ac9a48`..`bd09b76` (9 commitów)

---

## Faza 3 — Prompty z bazy (planned)

**Cel:** prompty ról w DB zamiast plików .md — dynamiczne, wersjonowane, edytowalne przez rolę.
Architektura warstw: `shared_base → role_block → phase_block → domain_pack → runtime_state`

| id | Zadanie | Status |
|----|---------|--------|
| 53 | Tabela `prompts` + migracja dokumentów ról | planned |
| 54 | Prompt Engineer — rola do edycji promptów w DB | planned |

**Efekt:** CLAUDE.md staje się minimalny (routing + "wywołaj session_init"). Pliki chronione znikają.

### Schemat tabeli `prompts` (zaktualizowany po research)

```sql
prompts (
  id, agent_id, kind, role, phase, task_type, domain,
  model_family, routing_description, content,
  version, status, tags, eval_suite_version,
  effective_from, replaced_by, created_at
)
```

Pole `kind`: `shared_base | role | phase | domain | example | routing`
Pole `routing_description`: oddzielone od `content` (execution body) — do użycia przez orchestrator/runner bez ładowania pełnego promptu.
Pole `status`: `draft | candidate | prod | deprecated`

### Nowe tabele wymagane przez Fazę 3 (z research)

**`prompt_assemblies`** — fingerprint promptu per sesja:
```sql
prompt_assemblies (
  assembly_id, session_id, role, phase, task_type,
  selected_prompt_ids, model_id, assembled_hash, created_at
)
```
Cel: korelacja regresji z konkretną wersją zestawu bloków. Każda sesja zapisuje co dostała.

**`phase_contracts`** — gate'y jako struktura danych (nie tylko prose w .md):
```sql
phase_contracts (
  id, workflow_id, phase_name,
  entry_requirements, required_artifacts,
  exit_requirements, escalation_conditions,
  output_schema
)
```
Cel: agent sprawdza kontrakt z DB zamiast parsować prose z .md. Gate = weryfikowalny stan.

**`known_failures`** — baza historycznych błędów agentów (retrieve per zadanie):
```sql
known_failures (
  id, agent_id, phase, task_type, failure_description,
  root_cause, fix_applied, tags, created_at
)
```
Cel: zamiast doklejać historię napraw do role_block — retrieve 1-3 najbardziej podobnych
przypadków do runtime_state. Prompt nie rośnie z każdą naprawą.

### session_init po Fazie 3

```
1. Pobierz shared_base
2. Dobierz role_block dla danej roli
3. Dobierz phase_block jeśli znana faza
4. Retrieve domain_pack po tagach zadania
5. Retrieve known_failures (1-3 przypadki podobne do bieżącego zadania)
6. Dokładaj runtime_state (backlog item, inbox, artefakty)
7. Zapisz assembly_id do session_log
```

### Zależność z Prompt Engineer

PE w Fazie PE-1 (przed Fazą 3) działa na plikach .md.
PE w Fazie PE-2 (po Fazie 3) używa `prompt_get/set/diff/publish/promote/rollback` + `eval_run`.
Plan roli: `documents/dev/prompt_engineer_plan.md`

---

## Faza 4 — Dyspozytor (in progress)

**Cel:** rola koordynująca przepływ pracy — office manager mrowiska.

| id | Zadanie | Status |
|----|---------|--------|
| 55 | Dyspozytor v1 — prompt roli, narzędzia CLI | ✓ done |
|    | Prompt DISPATCHER.md (PE) | ✓ done (review minor) |
|    | Narzędzia: inbox-summary, live-agents, handoffs-pending (Dev) | ✓ done |
|    | Test: pierwszy spawn Dyspozytora | planned |

**Zależność:** Faza 2 (Agent Launcher) — ✓ done (M1-M3).
**Uwaga:** Dawna nazwa "PM" zmieniona na "Dyspozytor" (`dispatcher`) — koordynuje przepływ, nie zarządza projektem.

---

## Faza 5 — Dokumentacja w bazie + rendery (planned)

**Cel:** jedna baza danych jako źródło wiedzy; człowiek i agent widzą to samo przez rendery.

| id | Zadanie | Status |
|----|---------|--------|
| 56 | Tabela docs + migracja documents/ do DB | planned |
| 57 | render.py --session → XLSX: Conversation / ToolCalls / Summary | planned |

**Efekt:** człowiek w 30s rozumie co agent dostał i co zrobił w sesji.

---

## Faza 6 — Odblokowanie agentów w wierszu poleceń (planned)

**Cel:** agent w trybie autonomicznym nie staje na blokadzie hooka — człowiek nie musi być obecny.

| id | Zadanie | Status |
|----|---------|--------|
| 58 | Hook smart fallback + tryb autonomiczny (whitelist + auto-approve) | planned |

**Problem:** hook bezpieczeństwa blokuje komendy wymagające ręcznego zatwierdzenia.
Runner (Faza 2) jest bezużyteczny jeśli każda sesja może utknąć bez człowieka w pętli.

**Zakres:**
- Analiza jakie komendy są najczęściej blokowane
- Hook "smart fallback": zamiast blokady zwraca bezpieczny odpowiednik
- Tryb autonomiczny: session-type (human/autonomous) → różne poziomy auto-approve
- Whitelist bezpiecznych wzorców

**Zależność:** sensowny po Fazie 2 (runner musi istnieć żeby problem był realny).

---

## Mapa zależności

```
Faza 1 (zapis sesji)
    │
    ▼
Faza 2 (agent invocation)  →  PE Faza 1 (.md editor, bez DB)
    │                               │
    ▼                               ▼
Faza 4 (PM)              Faza 3 (prompty w DB)  →  PE Faza 2 (prompt registry)
    │                               │
    ▼                               ▼
Faza 5 (docs w DB + rendery)   phase_contracts + known_failures
    │
    ▼
Faza 6 (odblokowanie agentów — hook smart fallback)
```

PE Faza 1 nie blokuje na Fazę 3 — można wdrożyć wcześniej jako .md editor.

---

## Faza 7 — Strict workflow enforcement (planned)

**Cel:** agent poza workflow jest podejrzany. Każdy krok logowany, każdy workflow zgodny z konwencją.

| id | Zadanie | Status |
|----|---------|--------|
|    | Audit trail — każdy krok workflow logowany do DB | planned |
|    | Workflow compliance gate — agent musi być w workflow żeby działać | planned |
|    | DB-driven workflows (parsowalne, nie prose) | planned |

**Zależność:** Faza 4 (Dyspozytor — enforcement through orchestration).
**Backlog:** powiązane z konwencją CONVENTION_WORKFLOW (DB-ready format).

---

## Faza 8 — Security multi-agent (planned)

**Cel:** ochrona przed przejęciem/zatruciem agentów, prompt injection, nieautoryzowanym spawnem.

| id | Zadanie | Status |
|----|---------|--------|
|    | Research: Cyber Security systemów wieloagentowych | planned (backlog #193) |
|    | Agent identity verification (kto spawnowal, kto pisze) | planned |
|    | Allowlist akcji per rola (nie tylko narzędzia — scope operacji) | planned |

**Zależność:** Faza 7 (strict enforcement jako fundament bezpieczeństwa).

---

## Faza 9 — Architektura skali (planned)

**Cel:** wieloinstancyjność ról, ochrona kontekstu, routing per workflow.

| id | Zadanie | Status |
|----|---------|--------|
|    | Wieloinstancyjność roli (Developer-1 w workflow, Developer-2 wolny) | planned (backlog #194) |
|    | Ochrona kontekstu (agent w workflow nie dostaje niezwiązanych tasków) | planned |
|    | Kolejka Dyspozytora (globalna) + kolejka per rola (lokalna) | planned |
|    | live_agents.workflow_id — Dyspozytor widzi kto jest w jakim kontekście | planned |
|    | Token budget scheduling | planned |

**Zależność:** Faza 7+8 (enforcement + security jako fundament skali).

---

## Zaktualizowana mapa zależności

```
Faza 1 (zapis sesji)
    │
    ▼
Faza 2 (agent invocation) ✓ DONE
    │
    ├──────────────────────────────────┐
    ▼                                 ▼
Faza 4 (Dyspozytor) ← in progress   Faza 3 (prompty w DB) ← planned
    │                                 │
    ▼                                 ▼
Faza 5 (docs w DB)               PE Faza 2 (prompt registry)
    │
    ▼
Faza 6 (odblokowanie agentów)
    │
    ▼
Faza 7 (strict workflow enforcement)
    │
    ▼
Faza 8 (security multi-agent)
    │
    ▼
Faza 9 (architektura skali — wieloinstancyjność, kontekst, budget)
```

---

*Ostatnia aktualizacja: 2026-03-26 (Faza 2 DONE, Faza 4 Dyspozytor in progress, Fazy 7-9 dodane)*
