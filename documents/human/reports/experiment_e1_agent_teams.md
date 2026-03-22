# Eksperyment E1: Agent Teams na Windows

Data: 2026-03-22
Eksperymentator: Developer
Backlog: #114 — Plan eksperymentów: Runner wieloagentowy
Claude Code version: 2.0.76

---

## Cel

Sprawdzić czy Agent Teams działa na Windows i spełnia wymagania projektu:
- Uruchomienie agenta w normalnym terminalu
- Wywołanie przez człowieka LUB innego agenta (PM)
- Pełna widoczność co się dzieje
- Możliwość dołączenia człowieka do konwersacji
- Praca autonomiczna bez human-in-the-loop
- **Integracja z istniejącym agent_bus (mrowisko.db)**

---

## Wynik researchu

### Czy Agent Teams istnieje?

**✓ TAK** — feature eksperymentalny w Claude Code.

**Aktywacja:**
```json
// ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "in-process"
}
```

Lub przez flagę:
```bash
claude --teammate-mode in-process
```

**Użycie:** Nie ma dedykowanej komendy CLI. Prosisz Claude'a w naturalnym języku:
```
"Stwórz zespół agentów do recenzji PR #142. Spawnuj 3 recenzentów..."
```

Claude automatycznie:
- Tworzy zespół
- Spawnuje team memberów
- Koordynuje zadania
- Synchronizuje komunikację

---

### Czy działa na Windows?

**✓ TAK, z ograniczeniami**

| Tryb | Windows | Opis |
|------|---------|------|
| **In-process** (domyślny) | ✓ Tak | Wszystko w jednym terminalu, `Shift+Down` przełącza między agentami |
| **Split panes** | ✗ Nie | Wymaga `tmux` lub iTerm2 — niedostępne natywnie na Windows |

**Windows = tylko tryb in-process.**

---

### Jak agenci się komunikują?

**Bezpośrednia komunikacja między teammates:**

- Teammate A → message → Teammate B (bezpośrednio)
- Broadcast (wszystkim naraz)
- Shared task list (koordynacja pracy)
- Shared mailbox (automatyczne dostarczanie wiadomości)

Każdy agent ma własne okno kontekstu — nie dzielą się historią czatu.

**Przechowywanie stanu:**
- `~/.claude/teams/{team-name}/config.json`
- `~/.claude/tasks/{team-name}/`
- **Lokalne pliki, NIE baza danych**

---

### Integracja z mrowisko.db/agent_bus_cli.py?

**✗ NIE — to oddzielny system.**

Agent Teams:
- Używa lokalnych plików do koordynacji
- Nie ma API do integracji z zewnętrzną bazą danych
- Nie może czytać/pisać do `mrowisko.db`
- Nie zna `agent_bus_cli.py` (messages, backlog, suggestions)

**Projekt Mrowisko a Agent Teams = dwie alternatywne architektury.**

---

## Ocena względem wymagań projektu

| Wymaganie | Agent Teams | Status |
|-----------|-------------|--------|
| Uruchomienie w normalnym terminalu | ✓ In-process | ✓ |
| Wywołanie przez człowieka | ✓ Naturalny język | ✓ |
| Wywołanie przez innego agenta (PM) | ✗ Brak integracji z agent_bus | ✗ |
| Pełna widoczność | ✓ Shift+Down przełączanie | ✓ |
| Dołączenie człowieka | ✓ Shared terminal | ✓ |
| Autonomiczność | ? Zależy od promptu | ? |
| **Integracja z mrowisko.db** | ✗ Oddzielny system | ✗ |

---

## Ograniczenia (eksperymentalny feature)

1. **Brak resumienia:** `/resume` nie przywraca in-process teammates
2. **Status opóźniony:** Aktualizacje tasków mogą mieć lag
3. **Jedna sesja = jeden zespół:** Nie można zarządzać wieloma równolegle
4. **Tylko lead spawnuje:** Agenci nie mogą spawnować swoich team members
5. **Brak wsparcia dla VS Code terminal, Windows Terminal**
6. **Brak integracji z zewnętrznym message bus** (SQLite, Redis, itp.)

---

## Trade-offs: Agent Teams vs własne rozwiązanie (mrowisko_runner.py)

| Aspekt | Agent Teams | Własne (mrowisko_runner.py) |
|--------|-------------|------------------------------|
| **Dojrzałość** | Eksperymentalne | PoC (do rozbudowy) |
| **Kontrola** | Ograniczona (Anthropic) | Pełna |
| **Integracja z agent_bus** | ✗ Niemożliwa | ✓ Natywna |
| **Windows support** | ✓ In-process | ✓ Subprocess |
| **Human-in-the-loop** | ✓ Wbudowany (Shift+Down) | ✗ Wymaga implementacji |
| **Koszt wdrożenia** | Niski (feature flag) | Średni (development) |
| **Multi-machine sync** | ✗ Lokalne pliki | ✓ Shared DB (mrowisko.db) |
| **Backlog/suggestions** | ✗ Nie zna | ✓ Natywne |
| **Eskalacja do człowieka** | ✓ Naturalnie (shared session) | ✗ Wymaga implementacji |
| **Resumienie sesji** | ✗ Brak wsparcia | ? Wymaga testu (E2) |

---

## Czy eksperyment udany?

**✓ Częściowo — Agent Teams działa na Windows, ale NIE spełnia głównego wymagania.**

**Kluczowy bloker:**
> Agent Teams to oddzielny system koordynacji. **Nie integruje się z mrowisko.db**, więc nie może:
> - Czytać backlog z agent_bus
> - Wysyłać suggestions
> - Komunikować się z ERP Specialist/Analyst przez messages
> - Być wywoływany przez PM agent

---

## Wnioski i rekomendacja

### 1. Agent Teams jako monolit (all-in)

**Scenario:** Porzucamy `mrowisko.db` i całkowicie przenosimy się na Agent Teams.

**Konsekwencje:**
- ✗ Utrata istniejącej infrastruktury (agent_bus_cli.py, backlog, suggestions, session_log)
- ✗ Brak kontroli nad koordynacją (black box Anthropic)
- ✗ Brak multi-machine sync (lokalne pliki)
- ✗ Feature eksperymentalny = ryzyko zmian API

**Rekomendacja:** ✗ NIE — zbyt duża strata, brak korzyści długoterminowych.

---

### 2. Hybryda (Agent Teams + mrowisko_runner.py)

**Scenario:** Używamy Agent Teams do zadań ad-hoc, a `mrowisko_runner.py` do powtarzalnych workflow.

**Use case:**
- **Ad-hoc (Agent Teams):** "Zrecenzuj PR #142 zespołem 3 agentów" — ręczny trigger przez człowieka
- **Powtarzalne (mrowisko_runner):** ERP Specialist → Analyst (dane z backlog) — autonomiczny poller

**Konsekwencje:**
- ✓ Best of both worlds: interaktywność (Teams) + automatyzacja (runner)
- ✗ Dwa systemy do utrzymania
- ✗ Agenci w różnych systemach nie mogą się komunikować

**Rekomendacja:** ⚠ Możliwe, ale niszowe — Agent Teams dla człowieka, runner dla autonomii.

---

### 3. Własne rozwiązanie (rozbudowa mrowisko_runner.py)

**Scenario:** Budujemy własny runner z interaktywnością człowieka.

**Korzyści:**
- ✓ Pełna kontrola nad architekturą
- ✓ Integracja z mrowisko.db (backlog, suggestions, messages)
- ✓ Multi-machine sync (shared DB)
- ✓ Możliwość stopniowej rozbudowy (approval gate → autonomia)

**Wyzwania:**
- ✗ Wymaga development (interaktywność, terminal sharing, resumienie)
- ✗ Większy koszt wdrożenia niż Agent Teams
- ✗ Wyższa złożoność techniczna

**Rekomendacja:** ✓ TAK — to jest zgodne z długoterminową wizją projektu.

---

## Decyzja architektoniczna (do zatwierdzenia)

**Propozycja:** Własne rozwiązanie (mrowisko_runner.py v2) z dodaniem:

1. **Interaktywność:**
   - Uruchomienie w normalnym terminalu (bez `--output-format stream-json`)
   - Możliwość dołączenia człowieka (shared session przez tmux/screen lub VS Code terminal API)

2. **Resumienie:**
   - Obsługa `--continue` / `--resume` (eksperyment E2)

3. **Autonomia:**
   - Prompt autonomiczny (eksperyment E3 → handoff do PE)

**Następne kroki:**
- E2: Sprawdzić czy terminal interaktywny z --append-system-prompt działa
- E3: Ustalić wymagania dla promptu autonomicznego (handoff do PE)
- Design mrowisko_runner.py v2 na podstawie wyników E2+E3

---

## Odrzucone opcje

| Opcja | Powód odrzucenia |
|-------|------------------|
| Agent Teams jako główny system | Brak integracji z mrowisko.db |
| Split panes (tmux) na Windows | Nie działa natywnie, wymaga WSL |
| Hybryda Teams + runner | Dwa systemy = zbędna złożoność dla obecnego scope |

---

**Status eksperymentu E1:** ✓ Zakończony

**Kontekst powiązany:**
- Research: `documents/architect/research_results_agent_runner_patterns (1).md` (jeśli istnieje)
- Plan strategiczny: `documents/architect/STRATEGIC_PLAN_2026-03.md`

