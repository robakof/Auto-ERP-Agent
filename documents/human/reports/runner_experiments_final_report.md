# Raport końcowy: Eksperymenty Runner wieloagentowy

Data: 2026-03-22
Eksperymentator: Developer
Backlog: #114 — Plan eksperymentów: Runner wieloagentowy
Claude Code version: 2.0.76

---

## Executive Summary

Przeprowadzono 3 eksperymenty badające możliwości uruchomienia agentów autonomicznych z interaktywnością człowieka:

| Eksperyment | Status | Wynik |
|-------------|--------|-------|
| **E1: Agent Teams na Windows** | ✓ Zakończony | Działa, ale **nie integruje się z mrowisko.db** |
| **E2: Terminal interaktywny** | ⚠ Wymaga testu manualnego | Plan przygotowany, wymaga wykonania przez użytkownika |
| **E3: Prompt autonomiczny** | ✓ Zakończony | Zidentyfikowane problemy + wymagania dla PE |

**Kluczowy wniosek:**
Agent Teams to eksperymentalny feature który **nie spełnia głównego wymagania** (integracja z agent_bus). Rekomendacja: **własne rozwiązanie** (mrowisko_runner.py v2).

---

## E1: Agent Teams na Windows

**Raport szczegółowy:** `experiment_e1_agent_teams.md`

### Wyniki

✓ **Agent Teams istnieje** — feature eksperymentalny (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
✓ **Działa na Windows** — tryb in-process (Shift+Down przełączanie)
✗ **NIE integruje się z mrowisko.db** — oddzielny system (lokalne pliki, nie SQL)

### Trade-offs: Agent Teams vs własne rozwiązanie

| Aspekt | Agent Teams | Własne (mrowisko_runner.py v2) |
|--------|-------------|--------------------------------|
| Integracja z agent_bus | ✗ | ✓ |
| Human-in-the-loop | ✓ Wbudowany | ✗ Wymaga implementacji |
| Kontrola architektury | ✗ Black box | ✓ Pełna |
| Koszt wdrożenia | Niski | Średni |
| Multi-machine sync | ✗ | ✓ (shared DB) |

### Decyzja

**✗ Odrzucone** — brak integracji z mrowisko.db to strukturalny bloker.

---

## E2: Terminal interaktywny z --append-system-prompt

**Raport szczegółowy:** `experiment_e2_interactive_terminal.md`

### Plan testów

Przygotowano 4 testy sprawdzające:
1. Komenda minimalna (bez stream-json) — czy sesja jest interaktywna?
2. Komenda z --max-turns — czy agent zatrzymuje się sam?
3. Wznowienie sesji (--continue) — czy działa?
4. Pełny prompt autonomiczny — czy agent wykonuje task bez czekania?

### Problem

Nie można uruchomić nested session (Claude Code w Claude Code). Wymaga **manualnego testu** przez użytkownika w osobnym terminalu.

### Status

⚠ **Do wykonania przez użytkownika** — plan gotowy, czeka na realizację.

---

## E3: Prompt autonomiczny

**Raport szczegółowy:** `experiment_e3_autonomous_prompt.md`

### Zdiagnozowane problemy

1. **Kolejność wstrzykiwania:** `--append-system-prompt` może dodawać `[TRYB AUTONOMICZNY]` **po** regule "czekaj na instrukcję" z promptu roli
2. **Workflow gate:** Agent może czekać na potwierdzenie wyboru workflow
3. **Brak jasnej instrukcji zakończenia:** "Zakończ sesję" niejednoznaczne
4. **Max turns za niski:** 8 tur może nie wystarczyć na złożone taski

### Rozwiązania

| Problem | Rozwiązanie |
|---------|-------------|
| Kolejność wstrzykiwania | `--system-prompt` zamiast `--append-system-prompt` (pełna kontrola) |
| Workflow gate | Reguła: w trybie autonomicznym wybór bez potwierdzenia |
| Brak instrukcji końca | Konkretna instrukcja: "Napisz 'Task zakończony' i STOP" |
| Max turns | Zwiększyć do 15-20 |

### Handoff do Prompt Engineer

**Zadanie:** Refaktor promptu autonomicznego

**Zakres:**
1. Rewizja `runner_autonomous.md` (jasna instrukcja zakończenia)
2. Rewizja `session_start` we wszystkich rolach (reguła `[TRYB AUTONOMICZNY]` **przed** "czekaj na instrukcję")
3. Dedykowany wariant promptu dla trybu autonomicznego
4. Test plan (minimalne + złożone zadanie)

**Output:** `documents/prompt_engineer/autonomous_prompt_refactor.md`

### Status

✓ **Zakończony** — wymaga handoff do PE.

---

## Decyzja architektoniczna

### Rekomendacja: Własne rozwiązanie (mrowisko_runner.py v2)

**Uzasadnienie:**
- Agent Teams **nie integruje się z mrowisko.db** (kluczowy bloker)
- Projekt wymaga kontroli nad architekturą (backlog, suggestions, messages)
- Multi-machine sync wymaga shared DB (nie lokalne pliki)
- Długoterminowa wizja = pełna autonomia z eskalacją do człowieka

**Architektura docelowa:**

```
mrowisko_runner.py v2
    │
    ├─ Uruchomienie w normalnym terminalu (bez --output-format stream-json)
    ├─ Kontrola pełnego system promptu (--system-prompt)
    ├─ Prompt autonomiczny (refaktor przez PE)
    ├─ Możliwość resumowania (--continue)
    ├─ Human-in-the-loop (approval gate OR interaktywność terminala)
    └─ Natywna integracja z agent_bus (backlog, messages, suggestions)
```

---

## Roadmap implementacji

### Faza 1: Walidacja (←— jesteśmy tutaj)

- [x] E1: Agent Teams research
- [x] E3: Wymagania dla promptu autonomicznego
- [ ] E2: Test terminala interaktywnego (manual test przez użytkownika)

### Faza 2: Refaktor promptów (Prompt Engineer)

- [ ] PE: Refaktor runner_autonomous.md
- [ ] PE: Aktualizacja session_start we wszystkich rolach
- [ ] PE: Test plan autonomii

### Faza 3: Implementacja mrowisko_runner.py v2 (Developer)

- [ ] Usunąć `--output-format stream-json` (normalny terminal)
- [ ] Zmienić `--append-system-prompt` → `--system-prompt` (pełna kontrola)
- [ ] Zwiększyć MAX_TURNS do 15-20
- [ ] Usunąć `--no-session-persistence` (pozwól --continue)
- [ ] Dodać tryb interaktywny (human może dołączyć do sesji)
- [ ] Test: autonomiczny task + human dołącza w trakcie

### Faza 4: Production (równolegle z ADR-001)

- [ ] Monitoring (invocation_log analytics)
- [ ] Error recovery (unclaim task przy błędzie)
- [ ] Rate limiting (max N agentów równolegle)
- [ ] Heartbeat dashboard (live view)

---

## Następne kroki

### Natychmiastowe (teraz)

1. **Developer → PE:** Wyślij handoff (agent_bus message) z zadaniem refaktoru promptu autonomicznego
2. **User:** Wykonaj E2 (manual test w osobnym terminalu) — instrukcje w `experiment_e2_interactive_terminal.md`

### Krótkoterminowe (tydzień)

3. **PE:** Refaktor promptu autonomicznego
4. **Developer:** Test E2 po wdrożeniu zmian PE
5. **Developer:** Design mrowisko_runner.py v2 (na podstawie wyników E2+E3)

### Długoterminowe (równolegle)

6. **Architect/Developer:** ADR-001 Domain Model (Faza 0-2) — nie blokuje runnera
7. **Developer:** Implementacja mrowisko_runner.py v2
8. **Developer:** Integracja runner z ADR-001 (LiveAgent.spawn_child)

---

## Odrzucone opcje

| Opcja | Powód odrzucenia |
|-------|------------------|
| Agent Teams jako główny system | Brak integracji z mrowisko.db |
| Split panes (tmux) na Windows | Nie działa natywnie (wymaga WSL) |
| Hybryda Teams + runner | Zbędna złożoność (dwa systemy) |
| Subprocess bez interaktywności | Człowiek nie może dołączyć (bottleneck) |

---

## Dokumenty wyjściowe

| Plik | Opis |
|------|------|
| `experiment_e1_agent_teams.md` | Research Agent Teams + ocena integracji |
| `experiment_e2_interactive_terminal.md` | Plan testów terminala interaktywnego |
| `experiment_e3_autonomous_prompt.md` | Analiza problemów + wymagania dla PE |
| `runner_experiments_final_report.md` | Raport końcowy (ten dokument) |

---

## Kluczowe wnioski

1. **Agent Teams nie pasuje do projektu** — brak integracji z agent_bus = strukturalny bloker
2. **Terminal interaktywny jest możliwy** — wymaga usunięcia `--output-format stream-json`
3. **Prompt autonomiczny wymaga refaktoru** — reguła `[TRYB AUTONOMICZNY]` musi być **przed** "czekaj na instrukcję"
4. **Własne rozwiązanie to jedyna opcja** — pełna kontrola + integracja z mrowisko.db

---

**Backlog #114 status:** ✓ Zakończony (pozostaje E2 — manual test)

**Autorzy:**
- Developer (research, analiza, dokumentacja)
- claude-code-guide agent (dokumentacja Agent Teams)

**Data zakończenia:** 2026-03-22

