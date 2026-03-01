# Automatyczny Konfigurator Systemu ERP

Agent LLM w VS Code autonomicznie konfiguruje system ERP Comarch XL — generuje i testuje
kod SQL dla kolumn i filtrów w oknach ERP, bez ręcznego przeklejania kodu między narzędziami.

---

## Instalacja

Pełna instrukcja krok po kroku: [INSTALL.md](INSTALL.md)

Skrót dla maszyny z zainstalowanymi narzędziami:

```
git clone https://github.com/CyperCyper/Auto-ERP-Agent.git
cd Auto-ERP-Agent
pip install -r requirements.txt
copy .env.example .env   # uzupełnij SQL credentials
```

---

## Wymagania

- Python 3.12+
- Node.js LTS + Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Microsoft ODBC Driver 17 for SQL Server
- Dostęp sieciowy do SQL Servera (konto read-only)
- VS Code (opcjonalnie, ale zalecane)

---

## Struktura projektu

```
/
├── CLAUDE.md                          # Instrukcje operacyjne agenta ERP
├── INSTALL.md                         # Instrukcja instalacji na nowej maszynie
├── .env.example                       # Szablon konfiguracji
├── requirements.txt                   # Zależności Python
│
├── tools/                             # Narzędzia CLI agenta (Python)
│   ├── sql_query.py                   # Wykonywanie zapytań SELECT na SQL Server
│   ├── db.py                          # Połączenie SQLite (moduł pomocniczy)
│   ├── build_index.py                 # Import XLSM → SQLite FTS5
│   ├── search_docs.py                 # Przeszukiwanie dokumentacji ERP (FTS5)
│   ├── search_solutions.py            # Przeszukiwanie bazy rozwiązań SQL
│   ├── search_windows.py              # Identyfikacja okna ERP
│   ├── save_solution.py               # Zapis rozwiązania SQL do solutions/
│   └── update_window_catalog.py       # Zarządzanie katalogiem okien ERP
│
├── solutions/                         # Baza rozwiązań SQL
│   ├── erp_windows.json               # Katalog okien ERP (id, aliasy, tabela główna)
│   └── solutions in ERP windows/
│       └── [Okno ERP]/
│           └── [Widok]/
│               ├── filtr.sql          # Kotwica widoku (kontekst tabeli głównej)
│               ├── columns/           # Fragmenty SQL: konfiguracja kolumn
│               └── filters/           # Fragmenty SQL: konfiguracja filtrów
│
├── erp_docs/
│   └── index/
│       └── docs.db                    # Indeks dokumentacji ERP (SQLite FTS5, ~7 MB)
│
├── documents/
│   ├── agent/
│   │   └── ERP_SQL_SYNTAX.md          # Składnia SQL specyficzna dla Comarch XL
│   └── dev/
│       ├── AI_GUIDELINES.md           # Wytyczne dla agenta deweloperskiego
│       ├── PRD.md                     # Wymagania produktowe
│       ├── ARCHITECTURE.md            # Architektura systemu
│       ├── MVP_IMPLEMENTATION_PLAN.md # Plan implementacji
│       └── progress_log.md            # Log postępów prac
│
└── tests/                             # Testy jednostkowe (pytest)
```

---

## Synchronizacja

Projekt jest repozytorium Git. Zmiany wprowadzane przez agenta (nowe rozwiązania SQL,
aktualizacje składni) są commitowane lokalnie i synchronizowane przez Git.

**Pobierz najnowsze zmiany** (nowe funkcjonalności, rozwiązania, dokumentacja):
```
git pull
```

**Wypchnij zmiany agenta** (nowe .sql, aktualizacje erp_windows.json):
```
git push
```

---

## Dokumentacja ERP (docs.db)

Indeks dokumentacji jest zbudowany i zawarty w repozytorium (`erp_docs/index/docs.db`).
Nie wymaga żadnej akcji przy instalacji.

Rebuild jest potrzebny tylko gdy zmieni się plik źródłowy XLSM:
```
python tools/build_index.py
```
Następnie: `git add erp_docs/index/docs.db` + commit + push.

---

## Weryfikacja instalacji

```
python tools/search_windows.py "towary"
python tools/search_docs.py "towar*" --useful-only --limit 3
python tools/sql_query.py "SELECT TOP 1 Twr_GIDNumer FROM CDN.TwrKarty"
```

Każde polecenie powinno zwrócić JSON z `"ok": true`.
