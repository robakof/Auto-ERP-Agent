# PRD: Mrowisko Agent Launcher

*Data: 2026-03-26*
*Autor: Architect*
*Status: Draft — do review*

---

## 1. Wprowadzenie i cel

**Nazwa projektu:** Mrowisko Agent Launcher (wtyczka VS Code + warstwa invocation)

**Cel:** Umożliwić człowiekowi i agentom uruchamianie pełnych, interaktywnych sesji Claude Code w osobnych terminalach VS Code — z pełną widocznością, możliwością dołączenia do rozmowy i skalowalnością do 100+ równoległych agentów.

**Problem:**
Obecnie agenci komunikują się przez agent_bus (mrowisko.db), ale każdą sesję Claude Code uruchamia ręcznie człowiek. Nie ma mechanizmu który pozwala:
- Agentowi wywołać innego agenta
- Orkiestratorowi zarządzać wieloma sesjami
- Człowiekowi widzieć i wchodzić w sesje agentów

**Wizja docelowa:** Ściana monitorów, 100+ agentów, wielu orkiestratorów, orkiestrator orkiestratorów. Jedyne ograniczenie = kasa na tokeny.

---

## 2. Użytkownicy i persony

| Persona | Kim jest | Jak korzysta z systemu |
|---|---|---|
| **Człowiek (Dawid)** | Założyciel, nadzorca, współpracownik agentów | Uruchamia agentów ręcznie lub przez wtyczkę. Wchodzi w terminale agentów, pisze wiadomości, nadzoruje pracę. Widzi stan wszystkich żywych agentów. |
| **Agent (rola)** | Sesja Claude Code z przypisaną rolą (Developer, ERP Specialist, Architect...) | Wykonuje zadania. W kontekście workflow może wywołać innego agenta. Poza workflow — eskaluje do orkiestratora. Ma dostęp do rejestru żywych agentów i ich terminali. |
| **Orkiestrator** | Agent ze specjalną rolą — decyduje o rozpoczęciu workflow i spawnie agentów | Czyta backlog/inbox. Decyduje kogo uruchomić z jakim zadaniem. Monitoruje stan żywych agentów. Może być wielu orkiestratorów + meta-orkiestrator. |

**Kluczowa zasada:** Człowiek i agent mają **symetryczny dostęp** do terminali — obaj mogą uruchomić, obaj mogą dołączyć.

---

## 3. Wymagania funkcjonalne

| ID | Wymaganie | Priorytet | Faza |
|---|---|---|---|
| **F-01** | **Spawn interaktywnej sesji Claude Code** — uruchomienie pełnego CLI Claude Code w nowym terminalu VS Code (identycznie jak ręczne `claude`). Żadne skróty, pełny interfejs. | Must | 1 |
| **F-02** | **Wstrzyknięcie kontekstu** — rola, task, dodatkowe instrukcje przekazane do spawned sesji (przez `--append-system-prompt`, CLAUDE.md routing lub inny mechanizm) | Must | 1 |
| **F-03** | **Ręczny spawn z UI** — człowiek wybiera rolę + task z interfejsu wtyczki (quick pick / command palette) | Must | 1 |
| **F-04** | **Rejestr żywych agentów** — centralny stan w mrowisko.db: kto żyje, w jakim terminalu, jaki task, kto uruchomił | Must | 1 |
| **F-05** | **Interaktywność** — człowiek może wejść w terminal spawned agenta i pisać (VS Code Terminal API to daje natywnie) | Must | 1 |
| **F-06** | **Approval gate** — przed auto-spawnem wtyczka pyta człowieka o zatwierdzenie | Must | 2 |
| **F-07** | **Workflow invocation** — agent w kontekście workflow może wywołać innego agenta (przez agent_bus + wtyczkę) | Must | 2 |
| **F-08** | **Lifecycle detection** — wykrywanie że sesja się zakończyła / agent czeka / agent pracuje (hooki Claude Code) | Should | 2 |
| **F-09** | **Multi-window** — wtyczka działa w wielu oknach VS Code, wszystkie czytają ten sam rejestr (mrowisko.db) | Must | 2 |
| **F-10** | **Orkiestrator** — rola decydująca o spawnie agentów poza workflow. Czyta backlog, decyduje kogo uruchomić. | Should | 3 |
| **F-11** | **Skalowalność 100+** — architektura nie blokuje na N agentów (ograniczenie = zasoby OS + tokeny) | Must | 3 |
| **F-12** | **Status dashboard** — widok stanu wszystkich żywych agentów (terminal title, ikona, status bar) | Nice | 3 |
| **F-13** | **Agent widzi terminale człowieka** — agent ma dostęp do rejestru terminali uruchomionych przez człowieka (i vice versa) | Should | 2 |
| **F-14** | **Resume** — możliwość wznowienia sesji agenta w nowym terminalu (`--resume`) | Nice | 3 |

---

## 4. Wymagania niefunkcjonalne

| ID | Wymaganie | Miara |
|---|---|---|
| NF-01 | Spawned terminal musi być nieodróżnialny od ręcznie uruchomionego Claude Code | Parity test: te same funkcje CLI dostępne |
| NF-02 | Rejestr żywych agentów współdzielony między instancjami VS Code | Jedno źródło prawdy: mrowisko.db |
| NF-03 | Spawn agenta < 5 sekund od decyzji | Czas od kliknięcia do widocznego terminala |
| NF-04 | Wtyczka nie blokuje IDE | Async operations, brak freeze UI |
| NF-05 | Brak single point of failure | Każdy agent = niezależna sesja Claude Code. Crash jednego nie zabija reszty |
| NF-06 | Środowisko: Windows 11 + VS Code | Inne platformy nice-to-have, nie bloker |

---

## 5. Scope i ograniczenia

### W scope

- Wtyczka VS Code (TypeScript)
- Rozszerzenie mrowisko.db o tabelę żywych agentów / invocations
- Integracja z Claude Code CLI (nie Agent SDK — CLI daje pełną interaktywność)
- Hooki Claude Code do lifecycle detection

### Poza scope

- Prompt autonomiczny (odłożony — mechanika first)
- Agent SDK jako alternatywa CLI (dopiero jeśli CLI się nie sprawdzi)
- Headless / CLI-only fallback (dopiero jeśli VS Code się nie sprawdzi)
- Orkiestrator orkiestratorów (Faza 3+, po walidacji podstawowej mechaniki)

### Ograniczenia znane

- VS Code Terminal API nie pozwala **odczytać** outputu terminala (można pisać, nie można czytać) — lifecycle detection musi iść przez hooki, nie przez parsowanie terminala
- Brak oficjalnego `--parent-session` w Claude Code CLI — parent/child tracking we własnej bazie
- `--permission-mode acceptEdits` nie daje pełnej autonomii (nadal pyta o Bash) — do rozwiązania później (Faza 6 arch_uplift_plan)

---

## 6. Aspekty techniczne

### Domain model

```
Session         — konwersacja Claude Code, przywołalna przez resume
Terminal        — terminal VS Code (efemeryczny)
LiveAgent       — Session + Terminal (runtime composite)
Registry        — centralny rejestr w mrowisko.db
Invocation      — fakt wywołania (kto, kogo, kiedy, z jakim taskiem)
```

### Technologia

- VS Code Extension API (Terminal API, commands, status bar)
- Claude Code CLI (spawn, hooki, --append-system-prompt)
- SQLite / mrowisko.db (rejestr, invocations)
- TypeScript (wtyczka)
- Python (hooki, agent_bus integracja)

### Otwarte pytania techniczne

| # | Pytanie | Wpływ | Status |
|---|---------|-------|--------|
| T-01 | Czy `claude --append-system-prompt "..."` (bez `-p`) daje pełną interaktywną sesję? | Architektura spawnu | Otwarte — wymaga spike |
| T-02 | Czy wtyczka w oknie A może sterować terminalem w oknie B? | Multi-window | Otwarte — wymaga spike |
| T-03 | Jak przekazać task agentowi w interaktywnej sesji — przez system prompt, przez pierwszą wiadomość, przez plik? | Wstrzyknięcie kontekstu | Otwarte |
| T-04 | Jaki hook Claude Code najlepiej sygnalizuje "sesja zakończona"? | Lifecycle detection | Otwarte — zbadany częściowo (SessionEnd, Stop) |

---

## 7. Etapy realizacji (wstępne)

### Faza 1: Dopracowanie wtyczki (spawn + rejestr)

- F-01, F-02, F-03, F-04, F-05
- Spike: odpowiedzi na T-01..T-04
- Cel: człowiek może spawnem uruchomić pełną sesję Claude Code

### Faza 2: Invocation (agent wywołuje agenta)

- F-06, F-07, F-08, F-09, F-13
- Mechanika: agent_bus → wtyczka → spawn
- Approval gate w fazie testów

### Faza 3: Skala i orkiestracja

- F-10, F-11, F-12, F-14
- Orkiestrator, dashboard, 100+ agentów
- Meta-orkiestrator

---

## 8. Kontekst projektu

### Istniejące zasoby

| Zasób | Stan | Lokalizacja |
|---|---|---|
| PoC wtyczki (E4) | Działa — 2 komendy, ~70 LOC | `extensions/mrowisko-terminal-control/` |
| Agent Bus v2 | Production — 8 serwisów, reply_to_id | `tools/lib/agent_bus.py`, `core/services/` |
| Research: multiagent workspace | Done | `documents/researcher/research/multiagent_workspace.md` |
| Research: mrowisko runner | Done | `documents/researcher/research/mrowisko_runner.md` |
| Research: workflow orchestration | Done | `documents/researcher/research/workflow_orchestration.md` |
| Research: swarm communication | Done | `documents/researcher/research/swarm_communication.md` |
| Eksperymenty E1-E4 | Done | `documents/human/reports/runner_experiments_summary.md` |
| Strategic plan | Zatwierdzony | `documents/architect/STRATEGIC_PLAN_2026-03.md` |
| Arch uplift plan | Faza 2 planned | `documents/dev/arch_uplift_plan.md` |

### Powiązanie z arch_uplift_plan

Ten PRD pokrywa **Fazę 2 (Wywoływanie agentów)** z `arch_uplift_plan.md`.
Fazy 1 (zapis sesji), 3 (prompty DB), 4 (PM), 5 (docs DB), 6 (odblokowanie agentów) — osobne, ale powiązane.
