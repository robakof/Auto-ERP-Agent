# Plan przebudowy plików wytycznych

## Problem

`CLAUDE.md` jest ładowany przy każdej sesji niezależnie od roli. Zawiera ~230 linii
instrukcji operacyjnych agenta ERP. Developer i Metodolog ładują to wszystko mimo że
90% jest im niepotrzebne. Kontekst window marnowany.

Dodatkowe problemy zidentyfikowane w sesji:
- Brak routingu wewnętrznego agenta — agent nie wie od razu jakie pliki załadować
- Eskalacja nie obejmuje walidacji infrastruktury (pusta baza, zły endpoint)
- Zasada prawdy zbyt słaba — "nie zmyślaj" to minimum, nie standard
- Workflowy inicjalizacji projektu (Phase 1-2) ładowane przy każdej sesji dev

## Cel

CLAUDE.md jako czysty routing. Każdy dokument roli ładuje tylko to co potrzebne
do swojego zadania. Agent eskaluje zamiast zgadywać.

---

## Docelowa struktura plików

```
CLAUDE.md                               ← routing + zasady wspólne (~50 linii)
documents/
├── agent/
│   ├── AGENT.md                        ← nowy; routing zadań + narzędzia + eskalacja + zasada prawdy
│   ├── agent_suggestions.md
│   ├── ERP_COLUMNS_WORKFLOW.md         ← bez zmian
│   ├── ERP_FILTERS_WORKFLOW.md         ← bez zmian
│   ├── ERP_VIEW_WORKFLOW.md            ← bez zmian
│   ├── ERP_SCHEMA_PATTERNS.md          ← bez zmian
│   └── ERP_SQL_SYNTAX.md              ← bez zmian
├── dev/
│   ├── DEVELOPER.md                    ← rename z AI_GUIDELINES.md + routing header
│   ├── PROJECT_START.md                ← nowy; wyodrębniony workflow Phase 1-2
│   ├── developer_suggestions.md
│   ├── backlog.md
│   └── progress_log.md
└── methodology/
    ├── METHODOLOGY.md                  ← dodać routing header
    ├── methodology_suggestions.md
    ├── methodology_backlog.md
    ├── methodology_progress.md
    └── przebudowa_wytycznych/          ← usunąć po wdrożeniu
```

## Co trafia gdzie

### CLAUDE.md — zostaje, skraca się

Zostaje:
- Opis projektu (2 zdania)
- Tabela ról → routing do właściwego pliku
- Lista plików chronionych
- Zasady eskalacji między poziomami
- Styl komunikacji

Przenosi się do AGENT.md: cała obecna zawartość operacyjna

### AGENT.md — nowy plik

Zawiera:
- Routing wewnętrzny: typ zadania → które pliki załadować
- Sygnatury narzędzi (potrzebne w każdym trybie)
- Walidacja środowiska na starcie (docs.db, połączenie SQL)
- Zasada prawdy (mocna wersja)
- Eskalacja — rozszerzona o infrastrukturę
- Refleksja po etapie pracy
- Workflowy: NIE (tylko wskazanie plików; treść w ERP_*_WORKFLOW.md)

Tryby agenta:
- ERP konfiguracja (kolumny, filtry) → ERP_COLUMNS/FILTERS_WORKFLOW.md
- Widoki BI → ERP_VIEW_WORKFLOW.md
- Analiza spójności danych → [przyszły tryb, pliki TBD]

### AI_GUIDELINES.md → DEVELOPER.md

Rename + routing header na starcie sesji.

Dodać:
- Reguła skali zadania: małe → ARCHITECTURE.md z sekcjami; duże → osobne PRD+TECHSTACK+ARCHITECTURE
- Przy zadaniu projektowym: zaproponuj nową gałąź → przejdź z użytkownikiem przez PROJECT_START.md
- Phase 1-2 wyodrębnione do PROJECT_START.md (zostaje referencja w DEVELOPER.md)

### PROJECT_START.md — nowy plik

Zawartość Phase 1-2 z obecnego AI_GUIDELINES.md:
- Phase 1: dokumentacja projektowa (PRD, TECHSTACK, ARCHITECTURE)
- Phase 2: eksperymenty i plan implementacji
- Reguła skali: kiedy osobne pliki, kiedy jeden ARCHITECTURE.md

### METHODOLOGY.md

Bez zmian merytorycznych. Dodać routing header: "Na starcie sesji przeczytaj methodology_progress.md."

---

## Kroki implementacji

1. Napisać AGENT.md
2. Napisać PROJECT_START.md (wyodrębnić Phase 1-2 z AI_GUIDELINES)
3. Skrócić CLAUDE.md do routingu
4. Rename AI_GUIDELINES.md → DEVELOPER.md + routing header + aktualizacje
5. Dodać routing header do METHODOLOGY.md
6. Zaktualizować cross-referencje w plikach agenta (wskazują na AGENT.md, nie CLAUDE.md)
7. Usunąć katalog przebudowa_wytycznych/
8. Commit

## Propozycje do przeglądu

- `CLAUDE_proposal.md`
- `AGENT_proposal.md`
- `DEVELOPER_proposal.md`
