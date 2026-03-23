# Podsumowanie eksperymentów: Runner wieloagentowy

Data: 2026-03-22
Backlog: #114 — Plan eksperymentów: Runner wieloagentowy
Status: ✓ ZAKOŃCZONE

---

## Executive Summary

Przeprowadzono 4 eksperymenty badające możliwości uruchomienia agentów autonomicznych z interaktywnością człowieka.

| Eksperyment | Status | Wynik kluczowy |
|-------------|--------|----------------|
| **E1: Agent Teams** | ✓ Zakończony | Działa, ale nie integruje się z mrowisko.db |
| **E2: Terminal interaktywny** | — Pominięty | Pokryty przez E4 |
| **E3: Prompt autonomiczny** | ✓ Zakończony | Zidentyfikowane problemy + handoff do PE |
| **E4: Wtyczka VS Code** | ✓✓✓ SUKCES | **Pełna kontrola terminali + interaktywność** |

**Decyzja architektoniczna:** **Wtyczka VS Code jako mrowisko_runner v2**

---

## E1: Agent Teams na Windows

**Raport:** `experiment_e1_agent_teams.md`

### Wyniki
- ✓ Agent Teams istnieje (feature eksperymentalny)
- ✓ Działa na Windows (tryb in-process)
- ✗ **NIE integruje się z mrowisko.db** — oddzielny system

### Decyzja
**✗ Odrzucone** — brak integracji z agent_bus to strukturalny bloker dla projektu.

---

## E2: Terminal interaktywny

**Status:** Pominięty — funkcjonalność przetestowana w ramach E4.

E4 (wtyczka VS Code) pokrył wszystkie pytania E2:
- Czy terminal interaktywny? ✓ TAK
- Czy można uruchomić Claude? ✓ TAK
- Czy human może dołączyć? ✓ TAK

---

## E3: Prompt autonomiczny

**Raport:** `experiment_e3_autonomous_prompt.md`

### Zdiagnozowane problemy

1. **Kolejność wstrzykiwania:** `--append-system-prompt` może dodawać `[TRYB AUTONOMICZNY]` za późno
2. **Workflow gate:** Agent może czekać na potwierdzenie wyboru workflow
3. **Brak instrukcji zakończenia:** "Zakończ sesję" niejednoznaczne
4. **Max turns za niski:** 8 tur może nie wystarczyć

### Handoff
**Do Prompt Engineer** (message id=188):
- Refaktor `runner_autonomous.md`
- Aktualizacja `session_start` we wszystkich rolach
- Reguła `[TRYB AUTONOMICZNY]` **przed** "czekaj na instrukcję"

---

## E4: Wtyczka VS Code - kontrola terminali

**Raport:** `experiment_e4_vscode_extension.md`

### Implementacja
- Lokalizacja: `extensions/mrowisko-terminal-control/`
- TypeScript (~200 LOC)
- 2 komendy: Test Terminal Control, Spawn Agent

### Testy

**Test 1: Prosty terminal (echo)**
- ✓ Terminal utworzony
- ✓ Komendy wykonane
- ✓ Output widoczny

**Test 2: Spawn Agent (Claude Code)**
- ✓ Terminal "Agent: developer" utworzony
- ✓ Claude uruchomiony (`claude.cmd` działa)
- ✓ Agent wykonał task autonomicznie
- ✓ Sesja zakończyła się poprawnie

**Test 3: Interaktywność**
- ✓ **Human może pisać w terminalu spawned agenta**
- ✓ Input jest przetwarzany
- ✓ Terminal pozostaje interaktywny

**Test 4: Złożony task (backlog)**
- ✓ Agent wykonał `agent_bus backlog --area Dev`
- ✓ Zwrócił 3 zadania z backlogu
- ⚠ Output opóźniony (PowerShell buffering)

### Wynik
**✓✓✓ PEŁNY SUKCES** — wtyczka ma pełną kontrolę nad terminalami + interaktywność działa.

---

## Decyzja architektoniczna

### Rekomendacja: Wtyczka VS Code jako mrowisko_runner v2

**Uzasadnienie:**

| Kryterium | Wtyczka VS Code | Agent Teams | CLI subprocess |
|-----------|-----------------|-------------|----------------|
| Integracja z agent_bus | ✓ | ✗ | ✓ |
| Interaktywność (human dołącza) | ✓ | ✓ | ✗ |
| Multi-agent view | ✓ Split terminals | ✓ Split panes | ✗ |
| Widoczność w IDE | ✓ | ✓ | ✗ |
| Kontrola architektury | ✓ Pełna | ✗ Black box | ✓ Pełna |
| Koszt wdrożenia | Średni | Niski | Niski |
| Multi-machine sync | ✓ Shared DB | ✗ Local files | ✓ Shared DB |

**Dlaczego wtyczka wygrywa:**
1. ✓ Interaktywność "za darmo" (Terminal API)
2. ✓ Multi-agent view natywnie (split terminals)
3. ✓ Integracja z agent_bus zachowana
4. ✓ Human widzi wszystko w IDE

**Dlaczego nie Agent Teams:**
- ✗ Brak integracji z mrowisko.db (kluczowy bloker)

**Dlaczego nie CLI subprocess:**
- ✗ Brak interaktywności bez dużej dodatkowej pracy
- ✗ Human nie widzi co robi agent (trzeba parsować stdout)

---

## Architektura docelowa

### mrowisko_runner v2 = Wtyczka VS Code

```
VS Code Extension
    │
    ├─ Command: Spawn Agent (manual trigger)
    │   └─ Quick pick: rola + task
    │
    ├─ Command: Spawn from Backlog (auto z backlogu)
    │   └─ Czyta backlog → spawn z taskiem
    │
    ├─ Watcher: agent_bus inbox (polling)
    │   └─ Co 60s → auto-spawn przy nowej wiadomości
    │
    └─ Status Bar: Agent monitor
        └─ Heartbeat + liczba aktywnych agentów
```

### Workflow (przykład)

1. **Developer (ręczny terminal):**
   ```bash
   claude -p developer
   ```
   - Czyta backlog
   - Wysyła task do ERP Specialist przez `agent_bus send`

2. **Wtyczka (auto-spawn):**
   - Wykrywa wiadomość w inbox ERP Specialist
   - Tworzy terminal "Agent: ERP Specialist"
   - Uruchamia Claude z taskiem z inbox

3. **ERP Specialist (spawned):**
   - Wykonuje workflow
   - Wysyła wynik przez `agent_bus send --to developer`

4. **Developer:**
   - Czyta inbox — widzi wynik
   - **Opcjonalnie:** Klika w terminal ERP Specialist, pisze dalsze instrukcje (interaktywność!)

---

## Roadmap implementacji

### Faza 1: Walidacja ✓ (zakończona)

- [x] E1: Agent Teams research
- [x] E3: Wymagania dla promptu autonomicznego
- [x] E4: Wtyczka VS Code PoC

### Faza 2: Refaktor promptów (Prompt Engineer)

- [ ] PE: Refaktor runner_autonomous.md
- [ ] PE: Aktualizacja session_start (wszystkie role)
- [ ] PE: Test plan autonomii

### Faza 3: Rozbudowa wtyczki (Developer)

- [ ] Spawn from Backlog
- [ ] Inbox watcher (polling co 60s)
- [ ] Status bar (liczba aktywnych agentów)
- [ ] Fix output buffering (stream-json + custom renderer OR cmd.exe)
- [ ] Terminal title update (status running/done)

### Faza 4: Production (Developer + równolegle ADR-001)

- [ ] Multi-agent orchestration (agent spawns agent)
- [ ] Monitoring dashboard (panel w VS Code)
- [ ] Heartbeat visualization
- [ ] Invocation log analytics
- [ ] CLI fallback dla headless environments

---

## Minor issues (do adresowania)

### 1. Output buffering
**Problem:** PowerShell bufferuje output — thinking/tool calls nie real-time
**Fix:** `--output-format stream-json` + custom renderer OR `shellPath: 'cmd.exe'`

### 2. Brak statusu agenta
**Problem:** Human nie wie czy agent pracuje czy zakończył
**Fix:** Status bar + terminal title update

### 3. Sesja kończy się za szybko
**Problem:** Task "zakończ" → agent kończy od razu
**Fix:** Prompt autonomiczny: "Czekaj na kolejną wiadomość" zamiast kończyć

---

## Kluczowe wnioski

1. **VS Code Terminal API = game changer** — interaktywność bez custom impl
2. **Agent Teams nie pasuje** — brak integracji z agent_bus
3. **Wtyczka prostsze niż subprocess** — Terminal API robi większość pracy
4. **Agent_bus kompatybilny** — wtyczka + ręczne sesje współdzielą DB
5. **Human może dołączyć** — terminal interaktywny potwierdzony ✓✓✓

---

## Odpowiedź na główne pytanie

> "Czy będę mógł uruchomić ja wiersz polecenia z claude code i będzie on interaktywny z innymi agentami?"

**TAK ✓✓✓**

**Jak to działa:**
1. Ty (ręczny terminal): `claude -p developer`
2. Wtyczka (spawned terminale): Agent: ERP Specialist, Agent: Analyst, ...
3. **Wszyscy** używają tej samej bazy `mrowisko.db` (agent_bus)
4. **Komunikacja:** `agent_bus send` → inbox → drugi agent czyta
5. **Interaktywność:** Kliknij w terminal spawned agenta → pisz wiadomości

**Pełna interaktywność agent-human-agent przez agent_bus** ✓

---

## Dokumenty wyjściowe

| Plik | Opis |
|------|------|
| `experiment_e1_agent_teams.md` | E1 szczegóły + ocena integracji |
| `experiment_e2_interactive_terminal.md` | E2 plan (pokryty przez E4) |
| `experiment_e3_autonomous_prompt.md` | E3 analiza + wymagania dla PE |
| `experiment_e4_vscode_extension.md` | E4 szczegóły + testy |
| `runner_experiments_summary.md` | **Raport końcowy** (ten dokument) |
| `extensions/mrowisko-terminal-control/` | Kod wtyczki (TypeScript) |

---

## Eksperymenty do wykonania?

**NIE** — wszystkie zaplanowane eksperymenty zakończone ✓

**E1-E4 pokrywają wszystkie pytania:**
- ✓ Agent Teams (oceniony, odrzucony)
- ✓ Terminal interaktywny (potwierdzony przez E4)
- ✓ Prompt autonomiczny (wymagania dla PE)
- ✓ Kontrola terminali (wtyczka VS Code działa)

**Następny krok:** Implementacja (Faza 2-4 z roadmapy).

---

**Status backlog #114:** ✓ Done

**Autorzy:**
- Developer (research, implementacja, testy, dokumentacja)
- User (testy manualne, feedback)
- claude-code-guide agent (dokumentacja Agent Teams)

**Data zakończenia:** 2026-03-22

