# Backlog — 2026-03-22

*10 pozycji*

---

## Wysoka wartość, średnia praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 114 | Plan eksperymentow: Runner wieloagentowy | Arch | wysoka | srednia |

## Wysoka wartość, duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 115 | Refaktor na Domain Model (ADR-001) | Arch | wysoka | duza |
| 90 | Architektura synchronizacji bazy danych między maszynami | Arch | wysoka | duza |

## Średnia wartość, mała praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 83 | Środowisko pracy — szukanie lepszego edytora/IDE | Dev | srednia | mala |

## Średnia wartość, średnia/duża praca

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 113 | Folder documents/exports/ — ujednolicenie lokalizacji eksportów | Dev | srednia | srednia |

## Pozostałe

| id | tytuł | obszar | wartość | effort |
|----|-------|--------|---------|--------|
| 112 | Rename solutions in ERP windows → erp_windows | ERP | niska | srednia |
| 104 | Transakcje atomowe w agent_bus | Dev | niska | srednia |
| 17 | Model wirtualnej firmy AI — zasady do METHODOLOGY.md | Metodolog | None | None |
| 16 | Przycinanie ramy teoretycznej | Metodolog | None | None |
| 1 | LOOM — publikacja na GitHub | Dev | średnia | mała |

---

## Szczegóły

### [115] Refaktor na Domain Model (ADR-001)
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** planned  **created_at:** 2026-03-22

# Refaktor na Domain Model (ADR-001)

## Cel
Przejście z architektury dict-based na Domain Model oparty o klasy.

## Zakres
- Faza 0: `core/entities/` — Entity, Status, wyjątki, Suggestion, BacklogItem, Message
- Faza 1: `core/repositories/` — SuggestionRepository, BacklogRepository, MessageRepository
- Faza 2: `core/services/agent_bus.py` — adapter zachowujący kompatybilność wsteczną
- Faza 3: `core/entities/agents.py` — Role, Session, Agent, LiveAgent (dla runnera)

## Zyski
- Walidacja przy tworzeniu obiektu (nie runtime SQL errors)
- Enkapsulacja logiki biznesowej (`suggestion.implement()` zamiast `bus.update_status()`)
- Testowalność (mockowanie repozytoriów)
- Gotowość na `LiveAgent.spawn_child()` dla samowywołania

## Dokumentacja
- ADR: `documents/architect/ADR-001-domain-model.md`
- Plan strategiczny: `documents/architect/STRATEGIC_PLAN_2026-03.md`

### [114] Plan eksperymentow: Runner wieloagentowy
**area:** Arch  **value:** wysoka  **effort:** srednia  **status:** planned  **created_at:** 2026-03-22

# Plan eksperymentów: Runner wieloagentowy

## Cel
Odkryć jak uruchomić agenta w normalnym terminalu z wstrzykniętym taskiem, który działa autonomicznie i pozwala human dołączyć.

## Eksperymenty

### E1: Agent Teams na Windows
- Czy `claude team create` działa na Windows?
- Czy split panes / in-process działa w VS Code terminal?
- Czy można zintegrować z istniejącym agent_bus?

### E2: Terminal interaktywny z wstrzykniętym taskiem
- `claude --append-system-prompt "[TRYB AUTONOMICZNY] Task: ..." -p "Rozpocznij"`
- Czy sesja jest interaktywna (można pisać)?
- Czy --continue / --resume działają?

### E3: Prompt autonomiczny
- Ustalenie dlaczego agent czekał na human input (problem promptu, nie runnera)
- Wymagania dla promptu autonomicznego → handoff do PE

## Output
Raport z wynikami + decyzja architektoniczna: Agent Teams / własne / hybryda

## Kontekst
- Research: `documents/architect/research_results_agent_runner_patterns (1).md`
- Plan strategiczny: `documents/architect/STRATEGIC_PLAN_2026-03.md`

### [113] Folder documents/exports/ — ujednolicenie lokalizacji eksportów
**area:** Dev  **value:** srednia  **effort:** srednia  **status:** planned  **created_at:** 2026-03-22

# Folder documents/human/ — przestrzeń robocza człowieka

**Koncepcja:** Dedykowana przestrzeń robocza dla człowieka — wszystkie pliki generowane przez agentów dla użytkownika (backlog, sugestie, logi, plany, raporty, notatki, eksporty danych).

## Problem

Eksporty/notatki generowane przez agentów lądują chaotycznie:
- Folder główny projektu
- `tmp/` (mieszane z plikami tymczasowymi)
- Brak spójnej konwencji

Użytkownik musi ręcznie kopiować pliki do Obsidian vault.

## Rozwiązanie

Dedykowany folder `documents/human/` z podkatalogami per typ:
```
documents/human/
  ├── backlog/      # render.py backlog
  ├── suggestions/  # render.py suggestions
  ├── inbox/        # wiadomości do człowieka (flagi, eskalacje)
  ├── logs/         # session-log
  ├── plans/        # plany architektoniczne, notatki
  ├── reports/      # raporty, analizy
  └── data/         # excel exports, offers, pricing
```

**Tracked w git** — pełna historia zmian.

## Zakres zmian

### Developer (ta sesja):
1. Utworzenie struktury `documents/human/`
2. Aktualizacja `render.py` (domyślne ścieżki)
3. Mapowanie narzędzi i promptów → przekazanie do PE
4. Testy

### Prompt Engineer (osobna sesja):
1. Aktualizacja CLAUDE.md i promptów ról
2. Aktualizacja workflow files
3. Aktualizacja pozostałych narzędzi

## Szczegóły

Pełny plan: `documents/dev/exports_folder_implementation_plan.md`

### [112] Rename solutions in ERP windows → erp_windows
**area:** ERP  **value:** niska  **effort:** srednia  **status:** planned  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 5.3 (Low)

Katalog ma spacje w nazwie: `solutions/solutions in ERP windows/`

Problemy:
- Utrudnia automatyzację (wymaga escape'owania)
- Niespójne z resztą struktury

Akcja: mv 'solutions/solutions in ERP windows' solutions/erp_windows + update odwołań.

### [104] Transakcje atomowe w agent_bus
**area:** Dev  **value:** niska  **effort:** srednia  **status:** planned  **created_at:** 2026-03-22

**Źródło:** Audyt Faza 2.3 (Low)

Brak jawnych transakcji (BEGIN/COMMIT). Każda operacja commitowana osobno.

Ryzyko: race conditions przy wielu agentach równolegle.

Akcja: dodać context manager dla transakcji przy złożonych operacjach. Priorytet wzrośnie gdy mrowisko_runner wejdzie do produkcji.

### [90] Architektura synchronizacji bazy danych między maszynami
**area:** Arch  **value:** wysoka  **effort:** duza  **status:** planned  **created_at:** 2026-03-21

# Architektura synchronizacji bazy danych między maszynami

## Problem

`mrowisko.db` zawiera komunikację między agentami (agent_bus), backlog zadań, logi sesji.
Praca na dwóch maszynach równolegle powoduje konflikty merge niemożliwe do automatycznego rozwiązania.

## Zakres

Zaprojektować i wdrożyć architekturę synchronizacji bazy danych między maszynami, która umożliwi:
- Wymianę wiadomości między agentami na różnych maszynach
- Współdzielony backlog zadań
- Brak konfliktów git
- Minimalne opóźnienie synchronizacji

## Opcje rozwiązań

Szczegółowa analiza opcji w: `documents/dev/machine_sync_architecture.md`

Opcje:
- **A:** Git LFS + manual merge (prowizorka)
- **B:** Baza zewnętrzna PostgreSQL/cloud (profesjonalne, wymaga hostingu)
- **C:** Podział lokalnej i shared DB (kompromis, offline-first)
- **D:** Event sourcing append-only (eleganckie, wymaga refactoru agent_bus)

## Następne kroki

1. User decyduje którą opcję wybrać (na podstawie priorytetów: koszt vs realtime vs elegancja)
2. Szczegółowy plan implementacji dla wybranej opcji
3. Implementacja etapami

## Tymczasowe rozwiązanie

Baza danych wyłączona z synchronizacji git (dodana do .gitignore) do czasu wdrożenia docelowej architektury.

### [83] Środowisko pracy — szukanie lepszego edytora/IDE
**area:** Dev  **value:** srednia  **effort:** mala  **status:** planned  **created_at:** 2026-03-20

Szukanie lepszego środowiska do pracy z agentem (edytor / IDE).

Obecne środowisko (VS Code + Claude Code) ma ograniczenia przy intensywnej pracy z botem
i wieloma sesjami agentów równolegle.

Zakres:
- Przegląd alternatyw: Cursor, Windsurf, JetBrains + plugin, inne
- Kryteria: wsparcie dla MCP, hooks, multi-session, podgląd logów, wygoda pracy z .env i plikami konfiguracyjnymi
- Rekomendacja z trade-offami

### [17] Model wirtualnej firmy AI — zasady do METHODOLOGY.md
**area:** Metodolog  **status:** planned  **created_at:** 2026-03-13

### Model wirtualnej firmy AI — zasady do METHODOLOGY.md

**Źródło:** methodology_suggestions (sesja 2026-03-11)
**Sesja:** 2026-03-11
**Dokument do zmiany:** METHODOLOGY.md (nowa sekcja lub rozszerzenie "Trzy poziomy działania")

Wypracowane zasady czekające na wdrożenie:

1. Podział ról człowiek/AI — rola trafia do tego kto lepiej ją wypełnia w danym momencie.
   Warunek przydziału do AI: decyzje przewidywalne i weryfikowalne.

2. Jednostka pracy — zdefiniuj zanim zaczniesz zbierać refleksje. Definicja należy
   do dokumentu roli w projekcie, nie do metodologii.

3. Struktura organizacyjna przy skali — przepływ refleksji odzwierciedla org chart.
   PM jako warstwa agregująca między developerami a metodologiem.

Ref. methodology_suggestions.md: [2026-03-11] Wirtualna firma AI.

---

### [16] Przycinanie ramy teoretycznej
**area:** Metodolog  **status:** planned  **created_at:** 2026-03-13

### Przycinanie ramy teoretycznej

**Źródło:** methodology_suggestions
**Sesja:** 2026-03-08
**Dokument do zmiany:** METHODOLOGY.md (sekcja "Wprowadzenie")

Test operacyjny dla każdego pojęcia: czy zmienia jakąkolwiek decyzję?
Fraktalność — tak (ta sama struktura per poziom złożoności).
Genomiczność, cybernetyka drugiego rzędu — legitymizacja, nie instrukcja.
Zostawić jedną ramę orientacyjną, resztę zastąpić konkretnymi warunkami.

---

### [1] LOOM — publikacja na GitHub
**area:** Dev  **value:** średnia  **effort:** mała  **status:** planned  **created_at:** 2026-03-13

### [Dev] LOOM — publikacja na GitHub

**Źródło:** methodology_progress
**Sesja:** 2026-03-11
**Wartość:** średnia
**Pracochłonność:** mała

Folder `_loom/` zawiera komplet plików gotowych do wypchnięcia jako osobne repo.

Kroki:
1. Utwórz repo GitHub (np. `CyperCyper/loom`)
2. Wypchnij zawartość `_loom/` jako root repo
3. Zaktualizuj placeholder URL w `_loom/seed.md`

---
