# Plan strategiczny: Mrowisko → wieloagentowość

Data: 2026-03-22
Autor: Architect
Status: **ZATWIERDZONY** (2026-03-22)

---

## 1. Stan obecny

### Co mamy
| Element | Stan | Gotowość |
|---------|------|----------|
| agent_bus (DB) | Działa | ✓ messages, backlog, suggestions, instances |
| mrowisko_runner.py | PoC | ✗ subprocess, brak interaktywności |
| ADR-001 Domain Model | Proposed | Plan gotowy, kod nie istnieje |
| Faza 3 (prompty w DB) | Deferred | Schema zaprojektowany, niezaimplementowany |
| Prompty ról | Działa | Zakładają human-in-the-loop |
| Research runner patterns | Done | Agent Teams, tmux, hooks udokumentowane |

### Problem do rozwiązania
Runner który:
- Uruchamia agenta w normalnym terminalu (VS Code, tmux, cokolwiek)
- Może być wywołany przez człowieka LUB innego agenta (PM)
- Pokazuje co się dzieje (pełna widoczność)
- Pozwala człowiekowi dołączyć do konwersacji (opcjonalnie)
- Działa autonomicznie bez human-in-the-loop

---

## 2. Pytania architektoniczne do rozstrzygnięcia

### P1: Agent Teams vs własne rozwiązanie

| Kryterium | Agent Teams | Własne |
|-----------|-------------|--------|
| Dojrzałość | Eksperymentalne | Do zbudowania |
| Kontrola | Ograniczona (Anthropic API) | Pełna |
| Integracja z agent_bus | Wymaga mostu | Natywna |
| Windows support | **Nieznany** | Zależny od implementacji |
| Human-in-the-loop | Wbudowany (split panes) | Do zaprojektowania |
| Koszt wdrożenia | Niski jeśli działa | Średni/wysoki |

**Rekomendacja:** Faza eksperymentalna — sprawdzić czy Agent Teams działa na Windows i spełnia wymagania. Jeśli nie → własne rozwiązanie oparte o tmux/terminal.

### P2: Czy refaktor ADR-001 blokuje runner?

**Nie blokuje bezpośrednio.**

ADR-001 (Domain Model) to refaktor wewnętrzny — zmienia jak kod jest zorganizowany, nie co robi. Runner może działać na obecnym agent_bus (dicty) lub przyszłym (klasy).

**Ale:** ADR-001 wprowadza `LiveAgent.spawn_child()` — abstrakcję samowywołania. Jeśli zrobimy runner przed ADR-001, będziemy mieli dwie implementacje do zsynchronizowania.

**Trade-off:**
- Runner najpierw → szybszy feedback, ale tech debt
- ADR-001 najpierw → czystszy kod, ale opóźnienie runnera

### P3: Czy prompty w DB (Faza 3) blokują runner?

**Nie blokują**, ale są silnie powiązane.

Runner potrzebuje promptu autonomicznego. Prompt autonomiczny to wariant promptu roli.
Faza 3 daje mechanizm wariantów (`kind: phase | mode`).

**Bez Fazy 3:** prompt autonomiczny jako osobny plik `.md` — działa, ale duplikacja.
**Z Fazą 3:** prompt autonomiczny jako blok w DB — czyste, skalowalne.

### P4: Co jest prawdziwym blokerem?

**Brak wiedzy** o tym jak uruchomić sesję Claude Code tak, żeby:
1. Działała w normalnym terminalu
2. Miała wstrzyknięty task
3. Działała autonomicznie (nie czekała na human)

Obecny runner używa `claude -p "prompt" --output-format stream-json` — to zabija interaktywność.

Potrzebujemy eksperymentu: **czy `claude --append-system-prompt "..." -p "task"` w normalnym terminalu (bez stream-json) da interaktywną sesję która działa autonomicznie?**

---

## 3. Propozycja kolejności działań

### Wariant A: Eksperymenty → Runner → Refaktor

```
[Teraz]
    │
    ▼
Faza E: Eksperymenty (1-2 sesje)
    ├── E1: Agent Teams na Windows — czy działa?
    ├── E2: claude --append-system-prompt w normalnym terminalu
    └── E3: Prompt autonomiczny — czy agent działa bez human?
    │
    ▼
Decyzja: Agent Teams / własne / hybryda
    │
    ▼
Runner v2 (na podstawie wyników)
    │
    ▼
ADR-001 + Faza 3 (równolegle, refaktor bez blokowania)
```

**Zalety:** Szybki feedback, nie inwestujemy w ślepą uliczkę.
**Wady:** Może opóźnić porządki (ADR-001).

### Wariant B: Refaktor → Runner

```
[Teraz]
    │
    ▼
ADR-001 Faza 0-2 (Entity + Repo + AgentBus adapter)
    │
    ▼
Faza 3 (prompty w DB) — równolegle z ADR-001 Faza 3
    │
    ▼
Eksperymenty Runner
    │
    ▼
Runner v2 (na czystej architekturze)
```

**Zalety:** Czysta architektura od początku, `LiveAgent` gotowy do użycia.
**Wady:** Długi czas do działającego runnera, ryzyko over-engineering.

### Wariant C: Równoległe ścieżki (rekomendowany)

```
[Teraz]
    │
    ├─────────────────────────────────┐
    ▼                                 ▼
Ścieżka 1: Eksperymenty         Ścieżka 2: Porządki
    │                                 │
    ├── E1: Agent Teams               ├── ADR-001 Faza 0-1
    ├── E2: Terminal + append-sys     │   (Entity + Repo)
    └── E3: Prompt autonomiczny       │
    │                                 ├── Faza 3 (prompty DB)
    ▼                                 │   równolegle
Decyzja architektoniczna              │
    │                                 │
    └─────────────────────────────────┘
                    │
                    ▼
            Runner v2 (na czystej architekturze,
                       z wynikami eksperymentów)
```

**Zalety:**
- Eksperymenty dają feedback bez blokowania porządków
- Porządki (ADR-001) idą swoim tempem
- Runner budowany na podstawie wiedzy + czystej architektury

**Wady:**
- Wymaga koordynacji dwóch ścieżek
- Więcej pracy równolegle

---

## 4. Plan eksperymentów (Faza E)

### E1: Agent Teams na Windows
**Cel:** Sprawdzić czy Agent Teams działa na Windows i spełnia wymagania.
**Kroki:**
1. Uruchomić `claude team create` lub equivalent
2. Sprawdzić czy split panes / in-process działa
3. Ocenić integrację z VS Code terminal
4. Ocenić czy można zintegrować z istniejącym agent_bus

**Output:** Raport: działa/nie działa + trade-offy.

### E2: Terminal interaktywny z wstrzykniętym taskiem
**Cel:** Sprawdzić czy można uruchomić normalną sesję Claude Code z taskiem.
**Kroki:**
1. `claude --append-system-prompt "[TRYB AUTONOMICZNY] Task: ..." -p "Rozpocznij pracę"`
2. Obserwować czy sesja jest interaktywna (można pisać)
3. Sprawdzić czy --continue / --resume działają
4. Ocenić czy agent wykonuje task czy czeka na human

**Output:** Raport + working command line.

### E3: Prompt autonomiczny
**Cel:** Sprawdzić czy agent może działać bez human-in-the-loop.
**Kroki:**
1. Stworzyć minimalny prompt autonomiczny (do Prompt Engineera)
2. Uruchomić agenta z tym promptem
3. Obserwować czy wykonuje task bez pytań
4. Zidentyfikować co powoduje czekanie na human

**Output:** Wymagania dla promptu autonomicznego → handoff do PE.

---

## 5. Rekomendacja

**Wariant C (równoległe ścieżki)** z następującą sekwencją:

| Tydzień | Ścieżka 1 (Eksperymenty) | Ścieżka 2 (Porządki) |
|---------|--------------------------|----------------------|
| 1 | E1: Agent Teams | ADR-001 Faza 0 (Entity, exceptions) |
| 1 | E2: Terminal + append-sys | — |
| 2 | E3: Prompt autonomiczny | ADR-001 Faza 1 (Repo) |
| 2 | Decyzja architektoniczna | — |
| 3 | — | ADR-001 Faza 2 (AgentBus adapter) |
| 3 | — | Faza 3 (prompty DB) — start |
| 4 | Runner v2 design | Faza 3 kontynuacja |
| 5+ | Runner v2 implementacja | Faza 3 + PE Faza 2 |

**Priorytet na teraz:**
1. **Eksperymenty E1-E2** — Developer (1-2 sesje)
2. **ADR-001 Faza 0** — Developer (równolegle)

---

## 6. Decyzje wymagające zatwierdzenia

1. [ ] Akceptuję Wariant C (równoległe ścieżki)?
2. [ ] Priorytet: eksperymenty E1-E2 jako pierwsze?
3. [ ] ADR-001 startuje równolegle (nie czeka na wyniki eksperymentów)?

---

*Dokument do dyskusji — Architect czeka na feedback.*
