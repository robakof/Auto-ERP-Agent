# Architectural Review: Runner v2 (VS Code Extension)

**Date:** 2026-03-22
**Reviewer:** Architect
**Requester:** Developer
**Context:** Handoff #194 — wyniki eksperymentów E1-E4

---

## Executive Summary

**Decision:** **APPROVED WITH CONDITIONS** ✓

**Recommendation:** Wtyczka VS Code jako **mrowisko_runner v2 dla dev use case** (Horyzont 1-2).

**Warunki:**
1. CLI fallback dla headless environments **musi być na roadmap** (Faza 4)
2. Równoległe ścieżki z ADR-001 M3 (nie blokować się nawzajem)
3. Hybryda długoterminowa: wtyczka (dev) + CLI (production/headless)

**Uzasadnienie:**
- ✓ Zgodność z STRATEGIC_PLAN (równoległe ścieżki: Eksperymenty + Porządki)
- ✓ Trade-offs akceptowalne dla interim solution
- ✓ Integracja z agent_bus zachowana (kluczowe dla projektu)
- ✓ Interaktywność bez custom impl (pragmatyzm > perfekcjonizm)
- ⚠ IDE lock-in (VS Code only) — mitygowane przez CLI fallback w Fazie 4

---

## Analiza eksperymentów

### E1: Agent Teams — ODRZUCONE ✓

**Decyzja Developer:** Odrzucone z powodu braku integracji z mrowisko.db

**Architect assessment:** **AGREE** ✓

**Uzasadnienie:**
- Agent_bus (mrowisko.db) to **rdzeń architektury** — messages, backlog, suggestions, session logs
- Agent Teams używa local files (nie shared DB) → agenci w Agent Teams **nie mogą komunikować się** z agentami w agent_bus
- Strukturalny bloker — nie da się naprawić "mostem" bez duplikacji logiki
- Alternative (wtyczka VS Code) zachowuje integrację z agent_bus ✓

**Trade-off analysis:**
| Kryterium | Agent Teams | Wtyczka VS Code |
|-----------|-------------|-----------------|
| Integracja z agent_bus | ✗ | ✓ |
| Koszt wdrożenia | Niski | Średni |
| Kontrola architektury | ✗ Black box | ✓ Pełna |

**Verdict:** Agent Teams nie pasuje do projektu. Odrzucenie uzasadnione.

---

### E4: Wtyczka VS Code — SUKCES ✓✓✓

**Rezultaty:**
- ✓ Terminal API daje pełną kontrolę nad terminalami
- ✓ `claude.cmd -p <rola> --append-system-prompt` działa przez wtyczkę
- ✓ **Terminal automatycznie interaktywny** — human może dołączyć bez custom impl
- ✓ Multi-agent view (split terminals natywnie)
- ✓ Shared mrowisko.db — agent spawned = agent ręczny (pełna kompatybilność)

**Architect assessment:** **Solid engineering** ✓

Developer przeprowadził 4 testy (echo, spawn agent, interaktywność, złożony task) — wszystkie pass.
PoC wtyczki działa (`extensions/mrowisko-terminal-control/`).

---

## Zgodność z long-term vision

### SPIRIT.md — 4 zasady ducha

#### 1. "Buduj dom, nie szałas"

> Każde narzędzie, każdy widok, każda reguła powinna być użyteczna poza aktualnym kontekstem.

**Wtyczka VS Code:**
- ✓ Użyteczna dla dev use case (human-in-the-loop, multi-agent view)
- ✗ **Nie działa poza IDE** (headless, CI/CD, cron)

**Verdict:** **Częściowo zgodne** — jest użyteczna, ale nie uniwersalna.

**Mitigation:** CLI fallback w Fazie 4 (hybryda: wtyczka dla dev, CLI dla production).

---

#### 2. "Automatyzuj siebie"

> Jeśli coś wymaga czyjejś stałej obecności w pętli — to jest stan przejściowy.

**Wtyczka VS Code:**
- ✓ Inbox watcher (polling co 60s) → auto-spawn przy nowej wiadomości
- ✓ Spawn from Backlog → auto-realizacja zadań
- ✓ Human **może** dołączyć, ale **nie musi**

**Verdict:** **Zgodne** ✓

Human-in-the-loop jest **opcjonalne**, nie **obowiązkowe**. Eskalacja wyjątek, nie reguła.

---

#### 3. "Wiedza musi przetrwać sesję, model i firmę"

> Każde odkrycie trafia do trwałego nośnika.

**Wtyczka VS Code:**
- ✓ Agent_bus (mrowisko.db) zachowany
- ✓ Shared DB — wszystkie terminale (ręczne + spawned) używają tej samej bazy
- ✓ Messages, backlog, suggestions, session logs — trwałe

**Verdict:** **Zgodne** ✓

Wiedza przetrwa — agent spawned zapisuje do tej samej bazy co agent ręczny.

---

#### 4. "Wybieraj to co skaluje"

> Jeden wyjątek: jawny deadline lub zatwierdzenie człowieka.

**Wtyczka VS Code:**
- ✓ Skaluje się w ramach IDE (multi-agent, split terminals)
- ⚠ Nie skaluje się poza IDE (headless environments)

**Verdict:** **Częściowo zgodne** — skaluje się dla dev use case, nie dla wszystkich use case.

**Mitigation:** CLI fallback = uniwersalność długoterminowa.

---

### STRATEGIC_PLAN_2026-03.md — Wariant C (równoległe ścieżki)

**Plan:**
```
Ścieżka 1: Eksperymenty (E1-E4) → Decyzja → Runner v2
Ścieżka 2: Porządki (ADR-001 Faza 0-2) → M3 AgentBus adapter
```

**Stan faktyczny:**
- Ścieżka 1: ✓ E1-E4 zakończone, decyzja podjęta (wtyczka VS Code)
- Ścieżka 2: ✓ ADR-001 M2 zakończone (61/61 tests pass), M3 w kolejce

**Verdict:** **Zgodne z planem** ✓

Równoległe ścieżki działają. Wtyczka nie blokuje ADR-001, ADR-001 nie blokuje wtyczki.

---

## Trade-offs architektoniczne

### Wtyczka VS Code vs Agent Teams vs CLI subprocess

| Kryterium | Wtyczka VS Code | Agent Teams | CLI subprocess |
|-----------|-----------------|-------------|----------------|
| **Integracja z agent_bus** | ✓ Natywna | ✗ Brak | ✓ Natywna |
| **Interaktywność** | ✓ Terminal API | ✓ Wbudowana | ✗ Wymaga custom impl |
| **Multi-agent view** | ✓ Split terminals | ✓ Split panes | ✗ Single stream |
| **Widoczność w IDE** | ✓ Natywna | ✓ Natywna | ✗ Poza IDE |
| **Kontrola architektury** | ✓ Pełna | ✗ Black box | ✓ Pełna |
| **Deployment** | ⚠ Extension install | ✓ Flag | ✓ Standalone |
| **Headless support** | ✗ VS Code only | ✗ VS Code only | ✓ CLI |
| **Multi-machine sync** | ✓ Shared DB | ✗ Local files | ✓ Shared DB |
| **Koszt wdrożenia** | Średni (~500 LOC TS) | Niski (flag) | Niski (~200 LOC Py) |

---

### Dlaczego wtyczka wygrywa (short-term)

1. **Interaktywność "za darmo"** — Terminal API obsługuje input automatycznie
2. **Multi-agent view natywnie** — split terminals bez dodatkowej pracy
3. **Integracja z agent_bus** — kluczowy requirement, tylko wtyczka + CLI to spełniają
4. **Human widzi wszystko** — developer experience > everything else dla dev use case

---

### Dlaczego wtyczka NIE wygrywa (long-term)

1. **IDE lock-in** — wymaga VS Code (nie działa w Vim, Emacs, CLI-only environments)
2. **Headless blocker** — CI/CD, cron jobs, remote servers bez GUI
3. **Deployment complexity** — TypeScript, extension packaging, Marketplace (opcjonalnie)

---

### Hybryda (rekomendacja)

**Short-term (Horyzont 1-2):**
- Wtyczka VS Code dla dev use case (human-in-the-loop, multi-agent view, debugging)

**Long-term (Horyzont 3):**
- CLI fallback dla production/headless
- Shared core logic (wtyczka + CLI delegują do tego samego agent_bus)
- Deployment: wtyczka (opcjonalna), CLI (core)

---

## Zgodność z ADR-001 (Domain Model)

### Czy wtyczka blokuje ADR-001?

**NIE** ✓

Wtyczka działa na poziomie **wywołania procesu** (`claude.cmd -p <rola>`), nie na poziomie logiki agent_bus.

ADR-001 refaktoruje **wewnętrzną** strukturę agent_bus (dicty → klasy), ale **interfejs CLI** pozostaje ten sam:
- `agent_bus_cli.py send` → działa przed i po ADR-001
- `agent_bus_cli.py backlog` → działa przed i po ADR-001

Wtyczka może działać na:
- **Obecnym agent_bus** (dicty, procedures) — działa teraz
- **Przyszłym agent_bus** (repositories, domain model) — będzie działać po M3

---

### Czy ADR-001 blokuje wtyczkę?

**NIE** ✓

ADR-001 M3 (AgentBus adapter) wprowadzi `AgentBus.send()` → deleguje do `MessageRepository.save()`.

Wtyczka może używać tego samego interfejsu — żadnych zmian w kodzie wtyczki.

**Przykład:**
```typescript
// Wtyczka (teraz i po M3)
terminal.sendText(`agent_bus send --from developer --to analyst`);
```

Niezależnie czy agent_bus używa dictów czy repositories — CLI command jest ten sam.

---

### Integracja: wtyczka + LiveAgent.spawn_child()

ADR-001 wprowadza `LiveAgent.spawn_child()` — abstrakcję samowywołania agent→agent.

**Potencjalna integracja (Faza 4):**
```python
# Agent w sesji
live_agent = LiveAgent(role="developer", session_id="abc123")
child = live_agent.spawn_child(role="erp_specialist", task="Utworzyć widok TraNag")

# Pod maską: wtyczka VS Code
# - Tworzy terminal "Agent: ERP Specialist"
# - Uruchamia claude.cmd -p erp_specialist --append-system-prompt "Task: ..."
```

**Nie blokujące:**
- Wtyczka może działać **bez** `LiveAgent.spawn_child()` (Faza 2-3)
- `LiveAgent.spawn_child()` może działać **bez** wtyczki (CLI subprocess fallback)
- Integracja **opcjonalna**, nie **obowiązkowa**

---

## Roadmap — assessment

### Faza 2: Refaktor promptów (Prompt Engineer)

**Tasks:**
- PE: Refaktor runner_autonomous.md
- PE: Aktualizacja session_start (wszystkie role)
- PE: Test plan autonomii

**Architect assessment:**
- ✓ Nie blokuje ADR-001 M3
- ✓ Niezależna ścieżka (PE vs Developer)
- ✓ Wymagane dla autonomii agenta

**Verdict:** **Approved** — proceed równolegle z ADR-001 M3.

---

### Faza 3: Rozbudowa wtyczki (Developer)

**Tasks:**
- Spawn from Backlog
- Inbox watcher (polling co 60s)
- Status bar (liczba aktywnych agentów)
- Fix output buffering (stream-json + custom renderer OR cmd.exe)
- Terminal title update (status running/done)

**Architect assessment:**
- ✓ Nie blokuje ADR-001 M3
- ✓ Incrementalne (można robić per feature)
- ⚠ Output buffering — minor issue, nie krytyczne

**Verdict:** **Approved** — proceed równolegle z ADR-001 M3.

**Priorytet features:**
1. **High:** Spawn from Backlog (core functionality)
2. **High:** Inbox watcher (autonomia)
3. **Medium:** Status bar (UX improvement)
4. **Low:** Output buffering (nice to have)
5. **Low:** Terminal title update (polish)

---

### Faza 4: Production (Developer + równolegle ADR-001)

**Tasks:**
- Multi-agent orchestration (agent spawns agent)
- Monitoring dashboard (panel w VS Code)
- Heartbeat visualization
- Invocation log analytics
- **CLI fallback dla headless environments**

**Architect assessment:**
- ✓ Zgodne z STRATEGIC_PLAN (długoterminowo)
- ✓ CLI fallback = krytyczny dla Horyzont 3 (produktyzacja, replikacja mrowiska)
- ⚠ `LiveAgent.spawn_child()` integracja — wymaga ADR-001 M3+ zakończonego

**Verdict:** **Approved z warunkami:**
1. **CLI fallback musi być zaimplementowany** — nie optional, obowiązkowy
2. **Priorytet CLI fallback: HIGH** (równy z multi-agent orchestration)
3. Monitoring dashboard, heartbeat, invocation log — **nice to have**, nie krytyczne

---

## Ryzyko i mitigation

### Ryzyko 1: IDE lock-in (VS Code only)

**Probability:** HIGH (wtyczka działa tylko w VS Code)
**Impact:** MEDIUM (blokuje headless use cases)

**Mitigation:**
- CLI fallback w Fazie 4 (obowiązkowy, nie optional)
- Shared core logic (wtyczka + CLI delegują do agent_bus)

**Status:** MITIGATED (jeśli CLI fallback na roadmap)

---

### Ryzyko 2: Output buffering (PowerShell)

**Probability:** MEDIUM (występuje, ale nie zawsze)
**Impact:** LOW (UX issue, nie functional blocker)

**Mitigation:**
- `--output-format stream-json` + custom renderer
- OR `shellPath: 'cmd.exe'` zamiast PowerShell
- OR akceptuj opóźnienie (not critical for autonomy)

**Status:** ACCEPTED (minor issue, nie blokuje Fazę 3)

---

### Ryzyko 3: Wtyczka vs ADR-001 conflict

**Probability:** LOW (interfejs CLI stable)
**Impact:** LOW (wtyczka działa na CLI, nie bezpośrednio na agent_bus)

**Mitigation:**
- Równoległe ścieżki (wtyczka Faza 2-3, ADR-001 M3)
- Interface stability (agent_bus_cli.py nie zmienia się)

**Status:** MITIGATED (design rozdziela concerns)

---

### Ryzyko 4: Over-engineering wtyczki

**Probability:** MEDIUM (Faza 4 ma dużo features)
**Impact:** MEDIUM (koszt wdrożenia, maintenance burden)

**Mitigation:**
- Incremental delivery (Faza 3 przed Fazą 4)
- Priorytetyzacja features (core functionality first)
- CLI fallback = escape hatch (jeśli wtyczka za złożona, fallback do CLI)

**Status:** WATCH (monitor complexity w Fazie 3-4)

---

## Odpowiedzi na pytania Developer

### 1. Czy decyzja architektoniczna (wtyczka VS Code) jest zgodna z długoterminową wizją?

**Odpowiedź:** **TAK, z warunkiem CLI fallback** ✓

**Uzasadnienie:**
- Wtyczka to **interim solution** dla dev use case (Horyzont 1-2)
- Horyzont 3 (produktyzacja, replikacja) wymaga CLI fallback (headless)
- Hybryda (wtyczka + CLI) jest zgodna z long-term vision

**Warunek:** CLI fallback musi być na roadmap Fazy 4 (obowiązkowy, nie optional).

---

### 2. Czy roadmap (Faza 2-4) jest spójny z ADR-001 Domain Model?

**Odpowiedź:** **TAK** ✓

**Uzasadnienie:**
- Faza 2-3 (wtyczka) nie blokuje ADR-001 M3 (równoległe ścieżki)
- Faza 4 (`LiveAgent.spawn_child()` integracja) wymaga ADR-001 M3+, ale nie blokuje wcześniejszych faz
- Interface stability (agent_bus_cli.py) gwarantuje kompatybilność

**Rekomendacja:** Proceed równolegle — Developer na wtyczkę (Faza 2-3), Developer na ADR-001 M3 when ready.

---

### 3. Priorytet: wtyczka (Faza 3) vs ADR-001 (Faza 0-2)?

**Odpowiedź:** **Równoległe ścieżki** (zgodnie z STRATEGIC_PLAN Wariant C)

**Uzasadnienie:**
- ADR-001 M2 zakończone (61/61 tests pass) → M3 ready to start
- Wtyczka Faza 2 (PE) niezależna od ADR-001 → proceed równolegle
- Wtyczka Faza 3 (Developer) niezależna od ADR-001 M3 → proceed równolegle

**Timeline propozycja:**
```
[Teraz]
    ├─── ADR-001 M3 (AgentBus adapter) ───────► ~1 tydzień
    ├─── Wtyczka Faza 2 (PE: prompty) ────────► ~1-2 sesje
    └─── Wtyczka Faza 3 (Dev: features) ──────► ~1 tydzień
        │
        ▼
    [Za 2 tygodnie]
    ├─── ADR-001 zakończone ✓
    ├─── Wtyczka Faza 3 zakończona ✓
    └─── Faza 4 (production) = ADR-001 + wtyczka integration
```

**Nie blokują się nawzajem** — Developer może pracować na obu równolegle lub delegować PE (Faza 2) podczas ADR-001 M3.

---

### 4. Minor issues (buffering, status bar) — czy priorytet przed Fazą 4?

**Odpowiedź:** **Nie** — incremental delivery

**Uzasadnienie:**
- Output buffering: **LOW priority** (UX issue, nie functional blocker)
- Status bar: **MEDIUM priority** (nice to have, nie krytyczne)

**Rekomendacja:**
- Faza 3: core functionality (Spawn from Backlog, inbox watcher) → HIGH priority
- Minor issues: implement jeśli trivial fix, otherwise defer do Fazy 4

**Trade-off:**
- Szybsza delivery (Faza 3 bez polish) → feedback loop szybszy
- vs Perfect UX (wszystkie minor issues fixed) → dłuższy czas do działającego runnera

**Wybór:** Pragmatyzm > perfekcjonizm. Ship Faza 3 z minor issues, fix incrementalnie.

---

## Decision

**APPROVED WITH CONDITIONS** ✓

### Warunki akceptacji:

1. **CLI fallback musi być na roadmap Fazy 4** (obowiązkowy, HIGH priority)
   - Headless support krytyczny dla Horyzont 3
   - Hybryda (wtyczka + CLI) zgodna z long-term vision

2. **Równoległe ścieżki z ADR-001 M3** (nie blokować się nawzajem)
   - Developer może pracować na wtyczkę Faza 2-3 podczas ADR-001 M3
   - PE realizuje Fazę 2 (prompty) niezależnie

3. **Incremental delivery** (core functionality first, polish later)
   - Faza 3: Spawn from Backlog + inbox watcher = HIGH priority
   - Minor issues (buffering, status bar) = MEDIUM/LOW priority

---

## Recommended Actions

### Immediate (Developer):
- [ ] Zaakceptuj warunki (CLI fallback na roadmap Fazy 4)
- [ ] Rozpocznij Fazę 2 (handoff do PE — refaktor promptów)
- [ ] Równolegle: ADR-001 M3 (AgentBus adapter) when ready

### Short-term (PE):
- [ ] Faza 2: Refaktor runner_autonomous.md
- [ ] Aktualizacja session_start (wszystkie role)
- [ ] Test plan autonomii

### Short-term (Developer):
- [ ] Faza 3: Spawn from Backlog (HIGH priority)
- [ ] Faza 3: Inbox watcher (HIGH priority)
- [ ] Faza 3: Status bar (MEDIUM priority, jeśli czas)
- [ ] Minor issues: defer do Fazy 4 unless trivial fix

### Long-term (Developer + Architect):
- [ ] Faza 4: **CLI fallback** (OBOWIĄZKOWY, HIGH priority)
- [ ] Faza 4: Multi-agent orchestration
- [ ] Faza 4: `LiveAgent.spawn_child()` integracja (wymaga ADR-001 M3+)

---

## Summary

**Wtyczka VS Code jako runner v2 = solid engineering decision dla dev use case.**

**Strengths:**
- Interaktywność "za darmo" (Terminal API)
- Multi-agent view natywnie
- Integracja z agent_bus zachowana
- Zgodność z STRATEGIC_PLAN (równoległe ścieżki)

**Weaknesses (mitigated):**
- IDE lock-in → CLI fallback w Fazie 4
- Output buffering → minor issue, fixable

**Zgodność z long-term vision:**
- ✓ Automatyzuj siebie (inbox watcher, auto-spawn)
- ✓ Wiedza przetrwa (shared mrowisko.db)
- ⚠ Buduj dom (interim solution, nie final) → CLI fallback = uniwersalność
- ⚠ Wybieraj to co skaluje (skaluje się w IDE, nie poza) → CLI fallback

**Verdict:** **GREEN LIGHT** ✓ — proceed to Faza 2-3 with conditions.

---

**Next:** Developer potwierdza akceptację warunków → rozpoczyna Fazę 2 (handoff do PE) + Fazę 3 (równolegle z ADR-001 M3).
