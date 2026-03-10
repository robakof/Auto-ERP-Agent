# LOOM

**Layered Observation and Orchestration Methodology**

Metodologia pracy nad projektami informatycznymi z udziałem agenta LLM (Claude Code).

---

## Koncepcja

LOOM organizuje pracę na trzech poziomach:

| Poziom | Rola | Zakres |
|---|---|---|
| Agent | Executor | Realizuje zadania domenowe (kod, testy, integracje) |
| Developer | Architekt | Kształtuje narzędzia, architekturę, wytyczne |
| Metodolog | Obserwator | Ocenia i poprawia metodę pracy |

Każdy poziom ma własny dokument wytycznych, plik refleksji i backlog.
Eskalacja idzie wyłącznie w górę. Agenci nie działają poza zakresem swojej roli.

---

## Jak zacząć nowy projekt

1. Utwórz nowe repo i sklonuj je lokalnie
2. Skopiuj `seed.md` do katalogu projektu jako `CLAUDE.md`
3. Uruchom Claude Code w tym katalogu
4. Agent przeprowadzi Cię przez inicjalizację i przekaże Developerowi

---

## Struktura repo

```
seed.md                              ← bootstrap nowego projektu
CLAUDE_template.md                   ← szablon CLAUDE.md z placeholderami
documents/
├── dev/
│   ├── DEVELOPER.md                 ← wytyczne developerskie
│   ├── PROJECT_START.md             ← workflow inicjalizacji projektu
│   └── templates/                   ← puste pliki startowe (kopiowane przez seed)
│       ├── backlog.md
│       ├── developer_suggestions.md
│       └── progress_log.md
└── methodology/
    ├── METHODOLOGY.md               ← pełna metodologia LOOM
    └── templates/
        ├── methodology_suggestions.md
        ├── methodology_backlog.md
        └── methodology_progress.md
```

---

## Co projekt dostaje z LOOM

- Routing ról w `CLAUDE.md`
- Wytyczne Developera z workflow inicjalizacji i implementacji
- System refleksji trójpoziomowej (agent → developer → metodolog)
- Progress log jako zewnętrzna pamięć agenta
- Backlog jako priorytetyzowana lista zadań

## Czego LOOM nie dostarcza

- Dokumentu roli agenta domenowego (`AGENT.md`) — tworzysz per projekt
- Workflow pliki specyficzne dla domeny — tworzysz per projekt
- Treści backlogu i progress logu — startują puste
