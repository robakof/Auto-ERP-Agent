# Plan przebudowy dispatchera i kontroli agentow

**Data:** 2026-03-30
**Autor:** Architect
**Trigger:** Diagnoza #530 (dispatcher) — 8 problemow krytycznych z sesji orkiestracji 2026-03-29
**Status:** Proposed — do zatwierdzenia przez czlowieka

---

## TL;DR

5 z 8 problemow ma juz istniejace mechanizmy w kodzie — brakuje enforcement.
Plan 80/20 skupia sie na wymuszeniu uzycia tego co mamy (3 zmiany, ~2 sesje Dev + 1 PE).
Pelny roadmap: 6 faz, od quick wins po izolacje agentow.

---

## Mapa problemow — stan obecny

| # | Problem | Istniejacy mechanizm | Luka | Severity |
|---|---------|---------------------|------|----------|
| P1 | Agenci pomijaja workflow gate | workflow-start/end/step-log CLI | Brak mechanicznego enforcement — prompt ignorowany | Critical |
| P2 | live-agents = martwe ciala | on_user_prompt heartbeat + GC (>10 min auto-stop), on_session_end sets stopped | GC dzialajacy — PE "zniknela" = crash/kill bez on_session_end | Medium |
| P3 | Dispatcher slepy (polling) | ADR-003 zaprojektowany, plan v1 istnieje | Niezaimplementowany — czeka na Dev | High |
| P4 | Spawn/stop bez bezpiecznika | `spawn-request` CLI istnieje (pending + approval) | Dispatcher uzywa `spawn` zamiast `spawn-request` | Critical |
| P5 | Race condition commity | git_commit.py wspiera `--files`, warning przy --all | Agenci uzywaja --all z nawyku, brak blokady | High |
| P6 | Zablokowany agent = cisza | `flag` (eskalacja) + `send` (do dispatchera) istnieja | Prompt nie mowi "gdy utknales — SOS do dispatchera" | Medium |
| P7 | Brak budzetu backlogu | backlog-add/update istnieja | Brak statusu needs_estimate, brak workflow oceny | Low |
| P8 | Prymitywne narzedzia | inbox-summary, live-agents, handoffs-pending osobno | Brak jednego dashboard JSON, buggy search_conversation | High |

**Wniosek:** Wiekszosc problemow to nie brak narzedzi — to brak enforcement i integracji.

---

## PLAN 80/20 — 3 zmiany natychmiastowe

### Zmiana 1: Wymuszenie spawn-request (blokada spawn dla dispatchera)

**Problem:** P4 — Dispatcher spawnowal/stopowal autonomicznie
**Obecny stan:** `spawn-request` istnieje w agent_bus_cli.py (linia 740), tworzy pending record.
Dispatcher uzywa `spawn` (direct) zamiast `spawn-request` (approval gate).

**Rozwiazanie (dwupoziomowe):**
1. **Prompt (juz zrobione):** DISPATCHER.md critical_rules pkt 1 — "NIE spawaj autonomicznie"
2. **Hook (do zrobienia):** pre_tool_use hook — gdy agent to dispatcher i komenda zawiera
   `agent_bus_cli.py spawn` (bez `-request`) → deny z message:
   "Uzyj spawn-request zamiast spawn. Spawn wymaga zatwierdzenia czlowieka."
   Analogicznie dla `stop` i `kill`.

**Effort:** mala (hook ~20 linii, wzorowany na istniejacym memory hook #218)
**Owner:** Developer
**Impact:** Eliminuje najniebezpieczniejsza autonomiczna akcje
**Backlog:** #219 (update scope)

---

### Zmiana 2: Konwencja per-file commits (blokada --all przy multi-agent)

**Problem:** P5 — PE git add --all wciagnela zmiany Deva
**Obecny stan:** git_commit.py wspiera `--files`, wyswietla warning przy --all.

**Rozwiazanie (dwupoziomowe):**
1. **Konwencja (prompt):** CLAUDE.md sekcja Git — dodac regule:
   "Przy rownolegych sesjach (live_agents > 1) uzywaj `--files` zamiast `--all`.
   `--all` dozwolone tylko gdy jestes jedynym aktywnym agentem."
2. **Tool guard:** git_commit.py z `--all` sprawdza live_agents count:
   - count > 1 → refuse z message "Wielu aktywnych agentow. Uzyj --files [lista plikow]."
   - count <= 1 → dozwolone (warning jak teraz)

**Effort:** mala (konwencja = prompt edit, tool guard = ~15 linii w git_commit.py)
**Owner:** Developer (tool) + PE (prompt)
**Impact:** Eliminuje race condition przy commitach
**Backlog:** #217 (update scope — quick fix zamiast pelnej izolacji)

---

### Zmiana 3: Dispatcher dashboard tool (jeden JSON)

**Problem:** P8 — 5+ CLI calls na orientacje + P2 (stale detection)
**Obecny stan:** inbox-summary, live-agents, handoffs-pending — trzy osobne komendy.

**Rozwiazanie:**
Nowa komenda CLI: `py tools/agent_bus_cli.py dashboard`
Zwraca jeden JSON:
```json
{
  "timestamp": "2026-03-30T08:00:00",
  "agents": {
    "active": [{"role": "developer", "session_id": "abc", "heartbeat_ago": "2m"}],
    "stale": [{"role": "prompt_engineer", "session_id": "def", "heartbeat_ago": "25m"}],
    "stopped": 3
  },
  "inbox": {
    "unread_by_role": {"developer": 2, "architect": 0, "dispatcher": 1}
  },
  "handoffs": {
    "pending": [{"from": "developer", "to": "architect", "phase": "code review"}]
  },
  "backlog": {
    "planned_by_area": {"Dev": 5, "Arch": 3, "Prompt": 2},
    "in_progress": 1
  },
  "alerts": [
    "Agent prompt_engineer stale (25m bez heartbeat)",
    "Handoff developer→architect czeka na odbiorcę"
  ]
}
```

**Effort:** srednia (laczy istniejace queries + alerts logic, ~100 linii)
**Owner:** Developer
**Impact:** Orientacja dispatchera: 1 call zamiast 5+, mniej tokenow, szybszy start
**Backlog:** NOWY ITEM do dodania

---

### Szybki win (bonus, zero kodu): Regula SOS

**Problem:** P6 — Dev utknał i pytal usera zamiast dispatchera
**Rozwiazanie:** Dodac do CLAUDE.md sekcja wspolna:
"Gdy jestes zablokowany (hook error, tool failure, brak dostepu) i nie mozesz kontynuowac:
1. Wyslij SOS do dispatchera: `agent_bus_cli.py send --from <rola> --to dispatcher --content-file tmp/sos.md`
2. Jesli dispatcher nie zyje — `flag` do czlowieka.
Nie czekaj w ciszy. Nie pytaj usera o problemy techniczne — eskaluj."

**Effort:** zero kodu (prompt change)
**Owner:** PE
**Backlog:** NOWY ITEM do dodania

---

## PELNY ROADMAP

```
Faza 0 ──→ Faza 1 ──→ Faza 2 ──→ Faza 3
  │           │                      │
  │           └──→ Faza 4            │
  │                                  │
  └──────────────────────────────→ Faza 5
```

### Faza 0: Quick Wins — Enforcement (1-2 sesje)

**Cel:** Wymuszenie uzycia istniejacych mechanizmow.

| Zadanie | Owner | Effort | Backlog |
|---------|-------|--------|---------|
| Hook: spawn → spawn-request redirect | Dev | mala | #219 |
| git_commit.py: multi-agent guard | Dev | mala | #217 |
| Prompt: SOS rule (CLAUDE.md) | PE | zero | NOWY |
| Prompt: per-file commit convention | PE | zero | #217 |

**Exit gate:** Hook testy PASS, git_commit guard testy PASS, prompty zaktualizowane.
**Czas:** 1 sesja Dev + 1 sesja PE

---

### Faza 1: Observability (2-3 sesje)

**Cel:** Dispatcher widzi mrowisko jednym wywolaniem. Narzedzia niezawodne.

| Zadanie | Owner | Effort | Backlog |
|---------|-------|--------|---------|
| Dashboard CLI command | Dev | srednia | NOWY |
| Fix search_conversation duplikaty | Dev | mala | NOWY |
| Fix read_transcript session_id resolution | Dev | mala | NOWY |
| session_init 2.0: kompresja startowa | Dev + PE | srednia | #211 |

**Zaleznosci:** Faza 0 (konwencje musza byc wdrozone zanim optymalizujemy tooling)
**Exit gate:** `dashboard` zwraca poprawny JSON, search_conversation bez duplikatow.
**Czas:** 2-3 sesje Dev

---

### Faza 2: Event System v1 — ADR-003 (3-5 sesji)

**Cel:** Event-driven monitoring zamiast pollingu.

Plan istniejacy: `documents/human/plans/plan_event_listener_v1.md`
ADR: `documents/architecture/ADR-003-event-listener-system.md`

5 podfaz (jak w planie):
1. DB Schema + Migration
2. Core Library (event_emitter.py)
3. CLI Integration (listen/events/unlisten)
4. Hook Integration (agent_started/stopped)
5. Session Init Integration (events w context)

**Zaleznosci:** Faza 1 (dashboard tool — events wzbogacaja dashboard output)
**Exit gate:** E2E test: register listener → emit event → check events → event delivered
**Backlog:** #212

**Rozszerzenie ADR-003 — Dispatcher Keyboard:**
Po wdrozeniu event system, dashboard tool zyskuje sekcje `events`:
```json
{
  "events": {
    "pending": [
      {"type": "workflow_end", "source": "prompt_engineer", "data": {...}}
    ],
    "count": 3
  }
}
```
Events naturlanie integruja sie z dashboard — nie potrzeba osobnego "keyboard" UI.
Dashboard = dispatcher keyboard.

---

### Faza 3: Workflow Enforcement (2-3 sesje)

**Cel:** Mechaniczne wymuszenie workflow gate — agent nie moze pracowac poza workflow.

| Zadanie | Owner | Effort | Opis |
|---------|-------|--------|------|
| workflow_active flag w live_agents | Dev | mala | Kolumna: czy agent ma otwarty workflow |
| Hook: block write/edit poza workflow | Dev | srednia | pre_tool_use sprawdza workflow_active |
| Alert: brak step-log > N min | Dev | mala | Event emitter → poke dispatcher |
| Whitelist operacji bez workflow | PE + Arch | mala | Zdefiniowac co wolno bez workflow |

**Zaleznosci:** Faza 2 (event system potrzebny do alertowania dispatchera)
**Exit gate:** Agent bez aktywnego workflow nie moze uzyc Write/Edit (poza whitelistem).
**Czas:** 2-3 sesje Dev + 1 PE

**Trade-off:** Mechaniczny enforcement vs elastycznosc.
- Zbyt agresywny → agenci zablokowany na kazdym kroku
- Zbyt luzny → agenci ignoruja (status quo)
- Propozycja: warning (log + alert), nie hard block, w Fazie 3a. Hard block w 3b po walidacji.

---

### Faza 4: Backlog Maturity (1-2 sesje)

**Cel:** Budzet i estymacja zanim task trafi do realizacji.

| Zadanie | Owner | Effort |
|---------|-------|--------|
| Status `needs_estimate` w DB schema | Dev | mala |
| backlog-add default → needs_estimate | Dev | mala |
| Dashboard: sekcja "do oceny" | Dev | mala |
| Workflow: idea → estimate → planned | PE + Arch | mala |

**Zaleznosci:** Brak (moze isc rownolegle z Faza 1-2, ale priorytet nizszy)
**Backlog:** #220
**Exit gate:** backlog-add tworzy z needs_estimate, dashboard pokazuje osobna sekcje.

---

### Faza 5: Agent Isolation (3-5 sesji, research-first)

**Cel:** Pelna izolacja plikow miedzy rownoleglymi agentami.

**Opcje do zbadania:**
| Opcja | Pro | Con |
|-------|-----|-----|
| git worktree per agent | Pelna izolacja, standard git | Zlozonosc merge, sync |
| Per-file locking (pessimistic) | Prosty, granularny | Deadlocki, overhead |
| Claimed files w DB | Lekki, pasuje do istniejacego modelu | Enforcement tylko w naszych narzediach |
| Branch per agent + auto-merge | Znany pattern | Merge conflicts |

**Zaleznosci:** Faza 0 (konwencja per-file jako interim rozwiazanie)
**Backlog:** #217 (rozszerzenie scope po quick fix)
**Decyzja:** Research → ADR → implementacja. Nie buduj bez analizy trade-offow.

---

## Priorytetyzacja backlog items

### Kolejnosc realizacji (mapowanie na fazy)

| Priorytet | Backlog | Tytul | Faza | Effort | Status |
|-----------|---------|-------|------|--------|--------|
| 1 | #219 | Spawn bezpiecznik | F0 | mala | planned → in_progress |
| 2 | #217 | Race condition commity (quick fix) | F0 | mala | planned |
| 3 | NOWY | Dashboard tool | F1 | srednia | do dodania |
| 4 | #211 | Session init 2.0 | F1 | duza | planned |
| 5 | #212 | Event Listener v1 | F2 | srednia | planned |
| 6 | NOWY | Workflow enforcement hooks | F3 | srednia | do dodania |
| 7 | #220 | Backlog budzet | F4 | mala | planned |
| 8 | NOWY | SOS rule (prompt) | F0 | zero | do dodania PE |
| 9 | NOWY | Fix search_conversation | F1 | mala | do dodania |
| -- | #218 | Hook memory redirect | -- | -- | DONE |

### Items poza tym planem (osobny track)

| Backlog | Tytul | Komentarz |
|---------|-------|-----------|
| #210 | Obsidian URI | Niezalezny, moze isc rownolegle |
| #196 | Est. context usage per area | Czeka na dashboard (F1) |
| #194 | Architektura skali | Czeka na #193 (research security) |
| #193 | Research Cyber Security | Niezalezny research |
| #192 | CONVENTION_TYPESCRIPT | Po Agent Launcher |
| #168 | Tryb nasluchu | Komplementarny z ADR-003 (F2) |
| #139 | Config-driven architecture audit | Niezalezny |
| #169-183 | Konwencje (EPIC) | Niezalezny track |

---

## Szacowany effort calosciowy

| Faza | Sesje Dev | Sesje PE | Sesje Arch | Suma |
|------|-----------|----------|------------|------|
| F0: Quick Wins | 1 | 1 | 0 | 2 |
| F1: Observability | 2-3 | 0.5 | 0 | 2.5-3.5 |
| F2: Event System | 3-5 | 0 | 0.5 (review) | 3.5-5.5 |
| F3: Workflow Enforce | 2-3 | 1 | 0.5 | 3.5-4.5 |
| F4: Backlog Maturity | 1-2 | 0.5 | 0.5 | 2-3 |
| F5: Agent Isolation | 3-5 | 0 | 1 (ADR) | 4-6 |
| **Total** | **12-19** | **3** | **2.5** | **17.5-24.5** |

**Realistyczny horyzont:** 2-3 tygodnie przy 2-3 sesjach dziennie.
**80/20 (Faza 0):** 2 sesje — mozna zrealizowac dzisiaj.

---

## Decyzje architektoniczne (trade-offy)

### D1: Warning vs Hard Block (workflow enforcement)
- **Warning:** agent loguje naruszenie, dispatcher dostaje alert, praca kontynuuje
- **Hard block:** agent nie moze uzyc Write/Edit poza workflow
- **Rekomendacja:** Warning w F3a, hard block w F3b po walidacji na 2-3 sesjach

### D2: git worktree vs per-file convention (izolacja)
- **Worktree:** pelna izolacja, ale merge complexity
- **Convention:** prostsze, ale wymaga dyscypliny
- **Rekomendacja:** Convention teraz (F0), worktree research w F5

### D3: Dashboard tool vs session_init enrichment (observability)
- **Dashboard CLI:** osobne narzedzie, dispatcher wola kiedy chce
- **Session init 2.0:** wszystko na starcie, ale ciezszy init
- **Rekomendacja:** Oba — dashboard dla mid-session, session_init 2.0 dla startu

### D4: Event system scope (ADR-003)
- **Minimal (v1):** CLI emit + pull-on-init, bez extension changes
- **Full (v2):** Extension push, budzi idle agentow
- **Rekomendacja:** v1 (juz zdecydowane w ADR-003), v2 gdy poke latency staje sie blokerem

---

## Nastepne kroki

1. **Czlowiek zatwierdza plan** (lub modyfikuje priorytety/scope)
2. **Faza 0 start:** Dev + PE spawned z konkretnymi taskami
3. **Architect review** po kazdej fazie (plan_review workflow)
4. **Workflow exploration #70** zamykamy dopiero po F2 (event system = pelna aktualizacja dispatchera)

---

## Referencje

- Diagnoza #530: wiadomosc od dispatchera
- ADR-003: `documents/architecture/ADR-003-event-listener-system.md`
- Plan event listener: `documents/human/plans/plan_event_listener_v1.md`
- Diagnoza startu: `documents/human/reports/dispatcher_startup_diagnosis_2026_03_29.md`
- DISPATCHER.md: `documents/dispatcher/DISPATCHER.md`
- PATTERNS.md: `documents/architecture/PATTERNS.md`
