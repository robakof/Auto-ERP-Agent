# Plan eksperymentów: Agent Launcher

*Data: 2026-03-26*
*Autor: Architect*
*Status: Draft*
*PRD: `documents/human/plans/PRD_agent_launcher.md`*

---

## Cel

Odpowiedzieć na otwarte pytania techniczne T-01..T-04 z PRD zanim zaczniemy implementację.
Każdy eksperyment to 1 konkretne pytanie → 1 test → 1 odpowiedź (TAK/NIE/WARUNKOWO).

---

## E-01: Interaktywna sesja z wstrzykniętym kontekstem

**Pytanie (T-01 + T-03):** Jak uruchomić pełną interaktywną sesję Claude Code z wstrzykniętym kontekstem (rola, task)?

**Warianty do przetestowania:**

| # | Komenda | Co testujemy |
|---|---------|-------------|
| A | `claude --append-system-prompt "[TRYB AUTONOMICZNY] Rola: developer. Task: sprawdź backlog"` | Czy bez `-p` daje interaktywną sesję z kontekstem? |
| B | `claude -p "Developer, sprawdź backlog Dev"` | Czy `-p` z promptem daje interaktywność (czy kończy po odpowiedzi)? |
| C | `claude` → ręczne wpisanie "Developer, sprawdź backlog" | Baseline — jak zachowuje się normalna sesja |
| D | `claude --system-prompt "Jesteś Developer. Task: sprawdź backlog"` | Czy `--system-prompt` (nie append) nadpisuje CLAUDE.md? |
| E | `claude --resume <session_id>` | Czy można wznowić sesję w nowym terminalu? |

**Kryteria sukcesu:**
- Sesja jest w pełni interaktywna (mogę pisać kolejne wiadomości)
- CLAUDE.md jest załadowany (agent zna swoje instrukcje)
- Hooki działają (session_init się odpala)
- Wstrzyknięty kontekst jest widoczny dla agenta
- Interfejs CLI identyczny z ręcznym uruchomieniem (slash commands, status line, /help)

**Output:** Tabela wyników per wariant + rekomendacja najlepszego sposobu spawn.

---

## E-02: Multi-window terminal control

**Pytanie (T-02):** Czy wtyczka VS Code w oknie A może widzieć/sterować terminale w oknie B?

**Testy:**

| # | Test | Co sprawdzamy |
|---|------|--------------|
| A | Otworzyć 2 okna VS Code na tym samym workspace. Wtyczka w oknie A — czy widzi terminale okna B? | `vscode.window.terminals` scope |
| B | Wtyczka w oknie A tworzy terminal — czy pojawia się w oknie A czy B? | Gdzie ląduje spawned terminal |
| C | Dwa okna VS Code, oba mają wtyczkę załadowaną. Obie czytają mrowisko.db — czy widzą te same dane? | Shared state przez DB |

**Hipoteza:** VS Code Extension API jest per-window (każde okno to osobny Extension Host). Terminale jednego okna nie są widoczne z drugiego. Współdzielony stan = mrowisko.db (nie Extension API).

**Jeśli hipoteza potwierdzona:** Każde okno VS Code jest niezależnym „pilotem" — widzi tylko swoje terminale, ale współdzieli rejestr przez DB. To wystarcza dla wizji wielookiennej.

**Output:** Potwierdzenie/obalenie hipotezy + implikacje architektoniczne.

---

## E-03: Lifecycle detection przez hooki

**Pytanie (T-04):** Jak wykryć że sesja Claude Code się zakończyła / agent czeka / pracuje?

**Testy:**

| # | Test | Co sprawdzamy |
|---|------|--------------|
| A | Dodać hook `Stop` — co dostaje w payload? | Czy mamy session_id, exit reason, transcript_path? |
| B | Dodać hook `SessionEnd` — kiedy się odpala vs `Stop`? | Różnica między Stop a SessionEnd |
| C | Agent kończy pracę (`/exit` lub wyczerpanie turns) — czy hook się odpala? | Reliability |
| D | Agent czeka na input — czy jest jakiś sygnał? | Idle detection |
| E | Hook zapisuje event do mrowisko.db — round-trip test | Czy wtyczka może pollować DB i wykryć zmianę? |

**Hipoteza z researchu:** Hooki (Stop, SessionEnd) to jedyny wiarygodny sygnał. Nie ma "heartbeat" API. Idle detection prawdopodobnie niemożliwy bez custom rozwiązania.

**Output:** Mapa zdarzeń lifecycle + rekomendacja jakie hooki podpiąć + schemat zapisu do mrowisko.db.

---

## E-04: Terminal API capabilities

**Pytanie:** Co dokładnie daje VS Code Terminal API dla naszych potrzeb?

**Testy:**

| # | Test | Co sprawdzamy |
|---|------|--------------|
| A | `terminal.sendText()` — czy można wysłać tekst do działającej sesji Claude? | Symulacja "człowiek pisze w terminalu agenta" |
| B | Nazewnictwo: `createTerminal({name: "Agent: developer"})` — czy nazwa jest widoczna i przydatna? | UX identyfikacji |
| C | Terminal w editor area (nie w panelu dolnym) — czy `createTerminal` pozwala na to? | Layout per wizja usera (terminale obok siebie pionowo) |
| D | `terminal.exitStatus` — czy daje exit code po zakończeniu? | Alternatywa/uzupełnienie dla hooków |
| E | `vscode.window.onDidCloseTerminal` — event kiedy terminal zamknięty | Cleanup registry |
| F | Ile terminali można otworzyć zanim VS Code zwalnia? | Limit skalowalności per okno |

**Output:** Capability matrix VS Code Terminal API + znane limity.

---

## Kolejność i zależności

```
E-01 (spawn interactive)     — PIERWSZY, fundamentalny
    │
    ├── E-04 (Terminal API)  — równolegle, niezależny
    │
    ▼
E-03 (lifecycle hooks)       — po E-01 (potrzebuje działającej sesji do testowania hooków)
    │
    ▼
E-02 (multi-window)          — ostatni (wymaga działającego spawnu + hooków)
```

**Szacowany zakres:** 1-2 sesje Developera.

---

## Kto realizuje

| Eksperyment | Rola | Uwagi |
|---|---|---|
| E-01 | Developer + Człowiek | Wymaga manualnego testowania interaktywności |
| E-02 | Developer | Czysty test API |
| E-03 | Developer | Hook setup + test |
| E-04 | Developer | Czysty test API |

**HANDOFF_POINT:** Architect → Developer (po zatwierdzeniu planu przez człowieka).
Wyniki wracają do Architekta → decyzja architektoniczna → Tech Stack + Architecture docs.
