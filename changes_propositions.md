# KM5 — Deployment (Git-based)

Data: 2026-03-01

---

## Cel

Każda maszyna = `git clone`. Agent commituje zmiany (SQL, składnia) lokalnie.
Developer pushuje nowe funkcjonalności, inni `git pull`ują.
docs.db (6.7 MB) trafia do git — buildujesz gdy XLSM się zmienia, pozostali `git pull`.

---

## Zakres zmian

### 1. `.gitignore` — odblokowanie docs.db

Aktualnie: `erp_docs/index/` jest w .gitignore → docs.db jest wykluczone.
Zmiana: usunąć `erp_docs/index/` z .gitignore (cały katalog index/ wchodzi do git).
Pliki WAL (*.db-wal, *.db-shm) dodać do .gitignore — tymczasowe pliki SQLite.

### 2. `erp_docs/index/docs.db` — dodanie do git

Po zmianie .gitignore: `git add erp_docs/index/docs.db` i commit.

### 3. `README.md` — pełne przepisanie

Aktualny README opisuje starą architekturę (płaska struktura, index.json).
Nowy README będzie zawierał:

- Krótki opis (2-3 zdania)
- Wymagania: Python 3.12+, VS Code + Claude Code, dostęp do SQL Servera
- Instalacja krok po kroku:
  1. `git clone`
  2. `pip install -r requirements.txt`
  3. Skopiować `.env.example` → `.env`, uzupełnić SQL credentials
  4. Gotowe — docs.db i solutions/ już w repo
- Aktualna struktura projektu (odzwierciedlająca stan po KM1–KM4)
- Synchronizacja: `git pull` po zmianach developera, agent robi `git commit` po zmianach
- Rebuild docs.db (opcjonalnie): `python tools/build_index.py` gdy XLSM się zmieni

### 4. `.env.example` — uproszczenie

Usunąć zmienne które nigdy nie wymagają zmiany (tools używają ścieżek relatywnych):
- `SOLUTIONS_PATH`, `ERP_DOCS_PATH`, `LOGS_PATH` — usunąć
- `MAX_ITERATIONS` — usunąć (nieużywane przez tools)

Zostawić tylko to co każdy musi uzupełnić:
- `SQL_SERVER`, `SQL_DATABASE`, `SQL_USERNAME`, `SQL_PASSWORD`
- `XLSM_PATH` z komentarzem: opcjonalne, wymagane tylko przy rebuild docs.db

### 5. `documents/dev/progress_log.md` — wpis KM5

---

## Co NIE wchodzi w zakres

- Żadnych zmian w tools/ (działają na ścieżkach relatywnych — działają out-of-the-box)
- Żadnej konfiguracji branchy / git workflow (main, proste)
- Żadnych skryptów instalacyjnych (README wystarczy)

---

## Kolejność implementacji

1. Zmień .gitignore
2. Dodaj docs.db do git (commit)
3. Przepisz README.md (commit)
4. Zaktualizuj .env.example (commit)
5. Zaktualizuj progress_log.md (commit)

---

*Plan przygotowany: 2026-03-01*
