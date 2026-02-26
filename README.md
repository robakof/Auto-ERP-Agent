# Automatyczny Konfigurator Systemu ERP

Środowisko agentowe w VS Code umożliwiające autonomiczną konfigurację systemu ERP (kolumny, filtry, raporty) przez agenta LLM — bez ręcznego przeklejania kodu między narzędziami.

## Problem

Konfiguracja ERP wymaga wielu cykli: człowiek dostarcza dokumentację i przykłady do LLM, LLM generuje SQL, człowiek testuje w SSMS, przekazuje wyniki z powrotem, powtarza. Ten projekt automatyzuje ten cykl.

## Jak to działa

Agent LLM operuje wewnątrz VS Code i samodzielnie:
1. Eksploruje schemat bazy danych ERP (read-only)
2. Przeszukuje bazę gotowych rozwiązań SQL
3. Przeszukuje dokumentację ERP
4. Generuje i iteracyjnie testuje kod SQL
5. Zgłasza człowiekowi wyłącznie akcje wymagające ręcznej interwencji

## Struktura projektu

```
/
├── README.md                  # Ten plik
├── .env.example               # Szablon konfiguracji (connection string, ścieżki)
│
├── documents/                 # Dokumentacja projektowa
│   ├── AI_GUIDELINES.md       # Wytyczne dla agenta AI
│   ├── PRD.md                 # Wymagania produktowe
│   ├── TECHSTACK.md           # Wybór technologii
│   ├── ARCHITECTURE.md        # Architektura systemu
│   ├── IMPLEMENTATION_PLAN.md # Plan implementacji
│   └── progress_log.md        # Log postępów prac
│
├── solutions/                 # Baza rozwiązań SQL
│   ├── columns/               # Fragmenty kodu: konfiguracja kolumn
│   ├── filters/               # Fragmenty kodu: konfiguracja filtrów
│   ├── reports/               # Fragmenty kodu: konfiguracja raportów
│   └── index.json             # Indeks metadanych rozwiązań
│
├── erp_docs/                  # Dokumentacja systemu ERP
│   ├── raw/                   # Pliki źródłowe (Excel, PDF, Markdown)
│   └── index/                 # Sparsowane i zindeksowane dane
│
├── tools/                     # Skrypty Python (narzędzia agenta)
│   ├── sql_query.py           # Wykonywanie zapytań SQL (read-only)
│   ├── search_solutions.py    # Przeszukiwanie bazy rozwiązań
│   └── search_docs.py         # Przeszukiwanie dokumentacji ERP
│
└── logs/
    └── sessions/              # Logi sesji agenta (Markdown/JSON)
```

## Dokumentacja

| Dokument | Opis |
|----------|------|
| [PRD.md](documents/PRD.md) | Wymagania funkcjonalne i niefunkcjonalne |
| [AI_GUIDELINES.md](documents/AI_GUIDELINES.md) | Zasady pracy agenta AI w tym projekcie |
| [TECHSTACK.md](documents/TECHSTACK.md) | Wybrane technologie i uzasadnienia |
| [ARCHITECTURE.md](documents/ARCHITECTURE.md) | Architektura, data flow, diagramy |
| [progress_log.md](documents/progress_log.md) | Bieżące postępy prac |

## Szybki start

1. Skopiuj `.env.example` do `.env` i uzupełnij connection string do SQL Server
2. Zainstaluj zależności: `pip install -r requirements.txt`
3. Uruchom agenta w VS Code i podaj wymaganie w języku naturalnym

## Technologia

- **Agent:** Claude Code (MCP)
- **Baza danych:** SQL Server (połączenie przez `pyodbc`, wyłącznie read-only)
- **Skrypty:** Python 3.11+
- **Dokumentacja ERP:** pliki Excel/PDF parsowane lokalnie
