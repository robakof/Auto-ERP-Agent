# Plan przebudowy dispatchera i kontroli agentow v2

**Data:** 2026-03-30
**Autor:** Architect
**Trigger:** Diagnoza #530 + feedback czlowieka
**Status:** v2 — po review czlowieka, uwzglednia zmiane priorytetow
**Poprzednia wersja:** `plan_dispatcher_rebuild_v1.md`

---

## TL;DR

Workflow enforcement to problem #1 — od tego zaczynamy. Centralna mechanika:
**Policy Engine** — konfigurowalny, atomowy enforcement narzedzi per workflow/step/agent.
Budujemy interfejsy na skale (100 agentow), nawet jesli v0 pokrywa 20% przypadkow.

5 z 8 problemow ma istniejace mechanizmy — brakuje enforcement.
git_commit.py dostaje session-scoped `--all` (nie blokada, inteligentny staging).

---

## Zmiany wzgledem v1 (feedback czlowieka)

| Punkt | v1 | v2 |
|-------|----|----|
| Priorytet #1 | Quick wins (spawn, commits) | Workflow Enforcement |
| git_commit --all | Blokada przy multi-agent | Session-scoped staging (tylko pliki agenta) |
| Spawn hook | Blokada spawn + stop + kill | Tylko spawn (stop/kill = szybkosc wazniejsza) |
| D1 Enforcement | Warning vs hard block | Policy Engine — atomowa kontrola, konfigurowalny, dispatcher jako approver |
| Event monitoring | Plan gotowy | Wymaga researchu |
| D2 Izolacja | Convention vs worktree | Worktree = docelowo (100 agentow), merge automation kluczowa |

---

## Mapa problemow — stan obecny (bez zmian)

| # | Problem | Istniejacy mechanizm | Luka | Severity |
|---|---------|---------------------|------|----------|
| P1 | Agenci pomijaja workflow gate | workflow-start/end/step-log CLI | Brak mechanicznego enforcement | Critical |
| P2 | live-agents = martwe ciala | on_user_prompt heartbeat + GC (>10 min) | Crash bez on_session_end | Medium |
| P3 | Dispatcher slepy (polling) | ADR-003, plan v1 | Niezaimplementowany | High |
| P4 | Spawn bez bezpiecznika | spawn-request CLI istnieje | Dispatcher uzywa spawn zamiast spawn-request | Critical |
| P5 | Race condition commity | git_commit.py --files | Agenci uzywaja --all | High |
| P6 | Zablokowany agent = cisza | flag + send istnieja | Prompt nie mowi SOS | Medium |
| P7 | Brak budzetu backlogu | backlog-add/update | Brak needs_estimate | Low |
| P8 | Prymitywne narzedzia | inbox-summary, live-agents osobno | Brak dashboard JSON | High |

---

## PLAN 80/20 — 3 zmiany natychmiastowe

### Zmiana 1: Session-scoped git staging

**Problem:** P5 — `--all` staguje pliki innych agentow
**Obecny stan:** git_commit.py wspiera `--files` (reczne), `--all` (niebezpieczne).

**Rozwiazanie:**
- Hook on Write/Edit dopisuje sciezke do `.claude/session_files_{session_id}.txt`
- `--all` w git_commit.py czyta ten plik i staguje TYLKO pliki z biezacej sesji
- Agent nie musi recznie listowac plikow, a nie wciaga cudzych zmian
- Fallback: jesli plik sesji nie istnieje → zachowanie jak teraz (warning)

**Effort:** mala-srednia (hook ~15 linii, git_commit.py modyfikacja ~30 linii)
**Owner:** Developer
**Backlog:** #217

---

### Zmiana 2: Hook spawn/kill-request enforcement

**Problem:** P4 — Dispatcher spawnowal i killoval nie tych agentow
**Obecny stan:** spawn-request istnieje, dispatcher uzywa spawn. Kill bez zatwierdzenia.

**Rozwiazanie:**
- pre_tool_use hook: komenda zawiera `agent_bus_cli.py spawn` (bez `-request`) → deny
- pre_tool_use hook: komenda zawiera `agent_bus_cli.py kill` → deny
- Message: "Uzyj spawn-request / kill-request. Wymaga zatwierdzenia czlowieka."
- **Stop NIE blokowany** — szybkosc reakcji wazniejsza (stop = graceful, odwracalne).
- **Konfigurowalnosc:** ktore akcje wymagaja zatwierdzenia jest parametrem Policy Engine,
  nie hardcode. v0: spawn+kill w hookach. v1: policy YAML definiuje per-role.

**Effort:** mala (hook ~25 linii + kill-request command ~20 linii)
**Owner:** Developer
**Backlog:** #219

---

### Zmiana 3: Workflow gate — mechaniczny warning

**Problem:** P1 — agenci pracuja poza workflow, prompt ignorowany
**Obecny stan:** Regula w CLAUDE.md, zero mechanicznego enforcement.

**Rozwiazanie (v0 — natychmiastowe):**
- Kolumna `workflow_active` w live_agents (boolean, ustawiana przez workflow-start/end)
- Hook on Write/Edit: sprawdza workflow_active dla biezacego agenta
  - workflow_active = false → **warning** (nie block): loguje naruszenie + wysyla alert do dispatchera
  - Prog: 3 naruszenia → wiadomosc do agenta "Wejdz w workflow lub przerwij prace"
- To jest **v0 Policy Engine** — fundamenty pod pelna atomowa kontrole

**Effort:** srednia (DB migration, hook, alert logic)
**Owner:** Developer + Architect (design interfejsu)
**Backlog:** NOWY (priorytet 1)

---

### Bonus (zero kodu): Regula SOS

**Problem:** P6 — zablokowany agent milczy
**Rozwiazanie prompt:** "Gdy utknales → SOS do dispatchera. Dispatcher nie zyje → flag do czlowieka."
**Owner:** PE

---

## PELNY ROADMAP

```
F0: Quick Wins + Workflow Gate v0
 │
 ├──→ F1: Observability (dashboard, session_init 2.0)
 │     │
 │     └──→ F3: Event System v1 (research-backed)
 │           │
 │           └──→ F4: Policy Engine v1 (atomic control)
 │
 ├──→ F2: Policy Engine Design (ADR + research)
 │     │
 │     └──→ F4: Policy Engine v1 (implementacja)
 │
 ├──→ F5: Backlog Maturity
 │
 └──→ F6: Agent Isolation (worktree + merge pipeline)
```

---

### Faza 0: Quick Wins + Workflow Gate v0 (2-3 sesje)

**Cel:** Natychmiastowe enforcement istniejacych mechanizmow + fundament Policy Engine.

| Zadanie | Owner | Effort | Backlog |
|---------|-------|--------|---------|
| Session-scoped git staging | Dev | mala-srednia | #217 |
| Hook: spawn+kill → request enforcement | Dev | mala | #219 |
| workflow_active flag + warning hook | Dev | srednia | NOWY |
| Prompt: SOS rule | PE | zero | NOWY |
| Prompt: session-scoped commit convention | PE | zero | #217 |

**Exit gate:** Hook testy PASS, workflow warning dziala, session-scoped staging dziala.
**Czas:** 2 sesje Dev + 1 sesja PE

---

### Faza 1: Observability (2-3 sesje)

**Cel:** Dispatcher widzi mrowisko jednym wywolaniem.

| Zadanie | Owner | Effort | Backlog |
|---------|-------|--------|---------|
| Dashboard CLI (jeden JSON) | Dev | srednia | NOWY |
| Fix search_conversation duplikaty | Dev | mala | NOWY |
| Fix read_transcript session resolution | Dev | mala | NOWY |
| session_init 2.0: kompresja startowa | Dev + PE | srednia | #211 |

3-warstwowy model observability (D3):
1. session_init = snapshot na starcie (pelny stan)
2. Event stream = nasluch zmian (delty, F3)
3. Dashboard CLI = refresh na zadanie (pelny stan kiedy chce)

**Zaleznosci:** F0 (konwencje najpierw)
**Exit gate:** `dashboard` zwraca poprawny JSON, search bez duplikatow.

---

### Faza 2: Policy Engine Design — ADR + Research (1-2 sesje Arch)

**Cel:** Zaprojektowac Policy Engine jako fundamentalna mechanike orkiestracji.
Interfejsy na skale 100 agentow, nawet jesli v1 pokrywa 20%.

**Scope researchu:**
- Jak inne systemy orkiestracji (K8s RBAC, OPA, AWS IAM) robia policy enforcement?
- Jakie granularity jest optymalne? (per-agent vs per-workflow vs per-step)
- Jak dispatcher moze modyfikowac policy w runtime?
- Jak zrealizowac approval loop (hook catch → dispatcher approval → relay do agenta)?

**Deliverable:** ADR-004 Policy Engine + plan implementacji v1

**Scope ADR-004 (draft):**

```
Policy Engine — konfigurowalny enforcement narzedzi

Poziomy kontroli (od grubego do atomowego):
1. Global defaults — co wolno bez workflow (whitelist: Read, Grep, Glob, suggest)
2. Per-role defaults — np. dispatcher nie moze spawn, PE moze edytowac prompty
3. Per-workflow — w workflow X dozwolone narzedzia Y
4. Per-step — w kroku K workflow W, agent moze tylko Z

Policy schema (YAML):
  policies:
    global:
      outside_workflow:
        Read: allow
        Grep: allow
        Write: warn_after(3)    # 3 writes → alert dispatcher
        Edit: warn_after(3)
        Bash: warn_after(5)

    role.dispatcher:
      always:
        spawn: deny             # must use spawn-request
        stop: allow             # graceful, odwracalne — nie blokuj
        kill: deny              # zabijal nie tych agentow — wymaga zatwierdzenia

    role.erp_specialist:
      workflow.erp_columns:
        step.validate_sql:
          Bash: allow_only("py tools/erp_*.py")
          Write: deny
          Edit: allow_only("solutions/**")

Enforcement actions:
  - allow: tool call proceeds
  - deny: tool call blocked, message to agent
  - warn: tool call proceeds, alert logged
  - warn_after(N): allow first N calls, then warn
  - escalate: tool call paused, dispatcher gets approval request
    → dispatcher approves → tool call proceeds
    → dispatcher denies → tool call blocked + guidance message

Runtime modification:
  - Dispatcher moze aktualizowac policy per-agent w runtime
  - CLI: policy-update --agent <session_id> --rule "Write: deny"
  - Policy changes persisted in DB, hooks reloaduja na nastepnym tool call
```

**Zaleznosci:** F0 (v0 workflow gate daje dane na temat typowych naruszen)
**Backlog:** NOWY (Arch area)

---

### Faza 3: Event System v1 — ADR-003 (3-5 sesji, research-backed)

**Cel:** Event-driven monitoring zamiast pollingu.

**Wymagany research PRZED implementacja:**
- Jakie event-driven patterns dzialaja w embedded/SQLite kontekstach?
- Polling vs filesystem watches vs SQLite triggers — co pasuje do naszego stacku?
- Latencja dostarczenia eventu — ile jest akceptowalne?
- Jak skaluje sie przy 100 agentach generujacych eventy?

**Deliverable researchu:** `documents/architect/research_results_event_patterns.md`

Plan po researchu — aktualizacja `plan_event_listener_v1.md` jesli research zmienia zalozenia.
ADR-003 juz istnieje (Option B). Research moze potwierdzic lub zaproponowac zmiane.

**v1 — Orchestrator-mediated:**
Agent konczy → event → budzi orkiestratora → walidacja (workflow, step-logi) →
orkiestrator poke'uje dalej. Na poczatku TYLKO dla orkiestratora — kazdy event
przechodzi przez niego. Daje pelna kontrole + zbiera metryki naruszen.

**v2 — Direct agent-to-agent:**
Gdy pipeline jest stabilny (N sesji bez naruszen) → auto-walidacja → direct poke
do nastepnego agenta + powiadomienie orkiestratora. Orkiestrator w trybie obserwatora.

Robimy v1. v2 jako automatyczna ewolucja po stabilizacji pipeline.

**Zaleznosci:** F1 (dashboard — events wzbogacaja dashboard output)
**Backlog:** #212

---

### Faza 4: Policy Engine v1 — Implementacja (3-5 sesji)

**Cel:** Pelna atomowa kontrola narzedzi per workflow/step/agent.

Na bazie ADR-004 (Faza 2). Scope v1:
- Policy YAML loader + validator
- Hook integracja (pre_tool_use czyta policy)
- Dispatcher approval loop (escalate action → event/message → approval → relay)
- Dashboard: sekcja "policy violations" + "pending approvals"
- CLI: policy-update, policy-show, approval-respond

**Zaleznosci:** F2 (ADR-004 design) + F3 (event system dla approval relay)
**Backlog:** NOWY

**Trade-off v1:**
- Pelna granularity (per-step) vs uproszczona (per-workflow) — decyzja po ADR-004
- Real-time approval vs async — decyzja po event system v1 benchmarku
- YAML config vs DB-driven — YAML latwiejszy do review, DB latwiejszy do runtime update
  Rekomendacja: YAML jako source of truth, cachowane w DB, runtime overrides w DB

---

### Faza 5: Backlog Maturity (1-2 sesje)

**Cel:** Budzet i estymacja zanim task trafi do realizacji.

| Zadanie | Owner | Effort |
|---------|-------|--------|
| Status `needs_estimate` w DB | Dev | mala |
| backlog-add default → needs_estimate | Dev | mala |
| Dashboard: sekcja "do oceny" | Dev | mala |
| Workflow: idea → estimate → planned | PE + Arch | mala |

**Zaleznosci:** Brak (nizszy priorytet, rownolegle z F1+)
**Backlog:** #220

---

### Faza 6: Agent Isolation — Worktree + Merge Pipeline (3-5 sesji, research-first)

**Cel:** Pelna izolacja plikow miedzy rownoleglymi agentami.

**Docelowy model (dla 100 agentow):**
- Kazdy agent dostaje osobny git worktree na osobnym branchu
- Praca agenta = seria commitow na swoim branchu
- Po zakonczeniu → merge request do main
- Dispatcher/CI zatwierdza merge

**Merge automation — kluczowy problem:**
- 100 agentow = potencjalnie 100 branchow do merge
- Merge queue (kolejka): branche mergowane sekwencyjnie, kazdy rebasowany na HEAD
- Conflict detection: pre-merge check "czy moj branch konflikuje z czyims?"
- File ownership: dispatcher przypisuje katalogi/pliki agentom → minimalizuje konflikty
- Fast-forward only: jesli branch dotyka tylko "swoich" plikow → auto-merge bez review

**Jak to typowo dziala w duzych teamach:**
- Short-lived branches (zyja minuty-godziny, nie dni)
- Trunk-based development: merge czesto, male zmiany
- Merge bot (np. bors, mergify) kolejkuje i rebasuje automatycznie
- Monorepo + CODEOWNERS → automatyczne przypisanie reviewera per katalog

**Roznica vs ludzie:** agenci sa szybsi i bardziej przewidywalni.
Mozemy narzucic "agent X dotyka tylko `documents/erp_specialist/**`" →
zero conflictow z agentem Y ktory dotyka `tools/**`.

**Interim (F0):** Session-scoped staging (--all staguje tylko swoje pliki).
**Docelowo (F6):** Worktree per agent + merge pipeline + file ownership w policy.

**Zaleznosci:** F0 (interim), F4 (policy engine — file ownership enforcement)
**Backlog:** #217 (rozszerzenie scope)

---

## Priorytetyzacja backlog items (zaktualizowana)

| Priorytet | Backlog | Tytul | Faza | Effort |
|-----------|---------|-------|------|--------|
| 1 | NOWY | Policy Engine v0 — workflow gate + warning hook | F0 | srednia |
| 2 | #219 | Spawn hook (tylko spawn, nie stop) | F0 | mala |
| 3 | #217 | Session-scoped git staging | F0 | mala-srednia |
| 4 | NOWY | SOS rule (prompt) | F0 | zero |
| 5 | NOWY | Dashboard CLI tool | F1 | srednia |
| 6 | #211 | Session init 2.0 | F1 | duza |
| 7 | NOWY | ADR-004 Policy Engine Design | F2 | srednia (Arch) |
| 8 | NOWY | Research event-driven patterns | F3-prep | srednia (Arch) |
| 9 | #212 | Event Listener v1 | F3 | srednia-duza |
| 10 | NOWY | Policy Engine v1 | F4 | duza |
| 11 | #220 | Backlog budzet | F5 | mala |
| 12 | #217+ | Agent Isolation (worktree) | F6 | duza |
| -- | #218 | Hook memory redirect | -- | DONE |

---

## Decyzje architektoniczne (zaktualizowane)

### D1: Policy Engine — konfigurowalny atomowy enforcement

**Wizja:** Kazde wywolanie narzedzia przechodzi przez policy layer.
Policy okresla: allow / warn / deny / escalate-to-dispatcher.

**Granularity (od grubej do atomowej):**
1. Global defaults (co wolno bez workflow)
2. Per-role (dispatcher nie moze spawn)
3. Per-workflow (w ERP columns wolno tylko Read + Bash z erp_*.py)
4. Per-step (w kroku validate_sql: tylko Bash z erp_validate.py)

**Dispatcher jako approver:**
Hook lapie naruszenie → tworzy approval_request w DB →
dispatcher dostaje event/message → zatwierdza lub odmawia + nakierowuje →
decyzja wraca do agenta (przez poke lub event).

**Konfigurowalnosc (nie hardcode — policy definiuje wszystko):**
- `allow` — dozwolone bez warunkow
- `warn_after(N)` — N operacji poza regula → warning
- `deny` — natychmiastowa blokada z redirect message
- `escalate` — pauza + pytanie do dispatchera
- Ktore akcje wymagaja zatwierdzenia = parametr policy, nie hardcode w hookach
- Dispatcher moze modyfikowac policy w runtime per-agent

**V0 (F0):** workflow_active flag + warning hook (3 writes poza workflow → alert)
**V1 (F4):** Pelny YAML-driven policy engine + dispatcher approval loop

Budujemy interfejsy v1 od poczatku, nawet jesli v0 implementuje 20%.

### D2: Agent Isolation — worktree + merge pipeline

**Docelowy model:** Worktree per agent. Kazde dzialanie = osobny branch.
Przy 100 agentach merge automation jest kluczowa.

**Merge pipeline:**
- Merge queue (sekwencyjne, rebasowane na HEAD)
- File ownership (policy engine przypisuje katalogi → minimalizuje konflikty)
- Auto-merge: jesli agent dotyka tylko swoich plikow → fast-forward bez review

**Interim (F0):** Session-scoped staging chroni przed cudzymi plikami.
**Docelowo (F6):** Worktree + merge bot + file ownership w policy.

### D3: Observability — 3-warstwowy model

**Warstwa 1 — Snapshot (session_init):**
Na starcie sesji dispatcher dostaje pelny stan mrowiska: kto zyje, co czeka, jakie handoffy.
Jednorazowy, kompletny obraz — punkt odniesienia.

**Warstwa 2 — Nasluch (event-driven delta):**
Po starcie dispatcher slucha zmian wzgledem snapshot. Nie polling — eventy przychodzace:
agent skonczyl, handoff wyslany, flag podniesiony. Tylko DELTY, nie pelny stan.
Implementacja: event system (F3) + listenery dispatchera.

**Warstwa 3 — Refresh na zadanie (dashboard CLI):**
W dowolnym momencie dispatcher moze poprosic o pelny stan: `dashboard`.
Uzyteczne po dluzszej przerwie lub przy watpliwosciach co do aktualnosci.

```
session_init (snapshot) → event stream (delty) → dashboard (refresh na zadanie)
```

### D4: Event system — orchestrator-mediated vs direct

**v1 — Orchestrator-mediated loop:**
Agent konczy prace → event → budzi orkiestratora →
orkiestrator sprawdza: czy agent byl w workflow? step-logi kompletne? wynik OK? →
jesli TAK → orkiestrator poke'uje agenta dalej (lub nastepnego agenta w pipeline) →
jesli NIE → orkiestrator eskaluje / koryguje

```
Agent A (done) → event → Orkiestrator → walidacja → poke Agent A/B
```

To daje pelna kontrole: orkiestrator jest zawsze w petli, kazdy krok zwalidowany.
Na poczatku to jedyny tryb — orkiestrator uczy sie wzorcow naruszen.

**v2 — Direct agent-to-agent z powiadomieniem:**
Gdy workflow jest przetrenowany (zero naruszen przez N sesji) i kontrola zaciesniciona:
Agent konczy → automatyczna walidacja (policy engine) →
jesli PASS → bezposredni poke do nastepnego agenta + powiadomienie orkiestratora →
jesli FAIL → eskalacja do orkiestratora (jak w v1)

```
Agent A (done) → auto-validation → poke Agent B + notify Orkiestrator
                                  → fail? → Orkiestrator (fallback)
```

**Warunek przejscia v1→v2:** Metryki — N sesji bez naruszen workflow w danym pipeline.
Nie przelaczamy recznie — system sam "awansuje" pipeline do v2 gdy jest wystarczajaco stabilny.

**Decyzja:** v1 na poczatek (orkiestrator zawsze w petli). v2 jako ewolucja po stabilizacji.

---

## Szacowany effort (zaktualizowany)

| Faza | Sesje Dev | Sesje PE | Sesje Arch | Suma |
|------|-----------|----------|------------|------|
| F0: Quick Wins + WF Gate v0 | 2-3 | 1 | 0 | 3-4 |
| F1: Observability | 2-3 | 0.5 | 0 | 2.5-3.5 |
| F2: Policy Engine Design | 0 | 0 | 1-2 | 1-2 |
| F3: Event System v1 | 3-5 | 0 | 0.5 (research) | 3.5-5.5 |
| F4: Policy Engine v1 | 3-5 | 0.5 | 1 (review) | 4.5-6.5 |
| F5: Backlog Maturity | 1-2 | 0.5 | 0.5 | 2-3 |
| F6: Agent Isolation | 3-5 | 0 | 1 (ADR) | 4-6 |
| **Total** | **14-23** | **2.5** | **4-5** | **20.5-30.5** |

**Realistyczny horyzont:** 3-4 tygodnie przy 2-3 sesjach dziennie.
**F0 (natychmiastowe):** 3-4 sesje — start dzisiaj.

---

## Nastepne kroki

1. **Czlowiek zatwierdza plan v2**
2. **F0 start:** Dev (spawn hook + session staging + workflow gate v0) + PE (SOS rule)
3. **F2 rownolegle:** Architect rozpoczyna research + ADR-004 Policy Engine
4. **Review** po kazdej fazie (Architect)

---

## Referencje

- Diagnoza #530: wiadomosc od dispatchera
- ADR-003: `documents/architecture/ADR-003-event-listener-system.md`
- Plan event listener: `documents/human/plans/plan_event_listener_v1.md`
- Diagnoza startu: `documents/human/reports/dispatcher_startup_diagnosis_2026_03_29.md`
- DISPATCHER.md: `documents/dispatcher/DISPATCHER.md`
- PATTERNS.md: `documents/architecture/PATTERNS.md`
- Plan v1: `documents/human/plans/plan_dispatcher_rebuild_v1.md`
