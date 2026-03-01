# IMPLEMENTATION_PLAN

Plan modułowej implementacji systemu. Każdy kamień milowy kończy się działającym, testowalnym komponentem. Szczegółowe plany per moduł tworzone osobno przed implementacją.

---

## Kamień milowy 1 — Narzędzia agenta (tools/)

Implementacja pięciu skryptów CLI zwracających JSON zgodny z kontraktami z ARCHITECTURE.md.

**Moduły w kolejności implementacji:**

| # | Skrypt | Zależności | Opis |
|---|--------|------------|------|
| 1 | `sql_query.py` | pyodbc, .env | SELECT na SQL Server, blokada DML, TOP 100, timeout |
| 2 | `build_index.py` + `db.py` | openpyxl, sqlite3 | Import Excel → SQLite FTS5 (Tabele, Kolumny, Relacje, Słowniki) |
| 3 | `search_docs.py` | docs.db | FTS5 z unicode61 remove_diacritics=2, filtrowanie po is_useful |
| 4 | `search_solutions.py` | solutions/ | Traversal katalogów, FTS po treści plików .sql i ścieżce |
| 5 | `search_windows.py` | erp_windows.json | Dopasowanie okna ERP do zapytania użytkownika |
| 6 | `save_solution.py` | solutions/ | Zapis nowego .sql we właściwym miejscu struktury |

Każdy skrypt testowalny z CLI: `python tools/sql_query.py "SELECT TOP 1 ..."` → JSON na stdout.

---

## Kamień milowy 2 — Katalog okien ERP (erp_windows.json)

Ręczne wypełnienie katalogu okien przez developera na podstawie istniejących `filtr.sql`.

**Zawartość per wpis:** id, name, aliases, primary_table, related_tables, config_types, ścieżka w solutions/.

Minimalny zakres MVP: okna pokryte istniejącymi rozwiązaniami w `solutions/` (aktualnie: Okno towary → Towary według EAN, Towary według grup).

---

## Kamień milowy 3 — CLAUDE.md (instrukcje agenta)

Rozbudowanie `CLAUDE.md` o kompletne instrukcje operacyjne dla agenta.

**Zawartość:**
- Lista narzędzi z sygnaturami CLI i formatem wyjścia
- Domyślny workflow: okno → dokumentacja → wzorce → generowanie → test → zapis
- Reguły eskalacji: po ilu iteracjach, przy jakich błędach
- Instrukcje formułowania zapytań FTS5 (rdzeń + `*`, prefiks)
- Odwołanie do `ERP_SQL_SYNTAX.md` jako źródła prawdy o składni
- Protokół weryfikacji: porównanie wyniku zapytania z przykładowymi wartościami z search_docs

---

## Kamień milowy 4 — MVP end-to-end

Test pełnego cyklu na rzeczywistym wymaganiu w oknie Towary.

**Kryterium sukcesu:** Agent samodzielnie (bez interwencji człowieka) przechodzi przez kroki 1–7 z PRD TO-BE i generuje poprawny kod SQL gotowy do wklejenia w ERP.

**Przypadek testowy:**
> "Dodaj filtr do Okna Towary/Towary według EAN który wskaże kartoteki towarowe nie posiadające załączników w formacie .jpg"

Oczekiwany wynik: plik `.sql` pasujący stylem do istniejących rozwiązań w tym widoku.

---

## Kamień milowy 5 — Deployment (współdzielony folder)

Konfiguracja środowiska dla kolejnych użytkowników na pulpitach zdalnych.

- Przeniesienie `solutions/` i `erp_docs/` na współdzielony folder sieciowy
- Aktualizacja `.env.example` o zmienną `SHARED_PATH`
- Weryfikacja działania na drugiej maszynie
- Dokumentacja procesu instalacji (README.md)

---

## Poza zakresem MVP

Odkładamy na późniejsze fazy (zgodnie z PRD):
- Semantyczne wyszukiwanie embeddingami (Faza 4)
- Dashboard historii sesji (Faza 4)
- Automatyczny generator podzapytań testujących (Faza 3)
- Obsługa raportów (Faza 2+)

---

*Dokument przygotowany: 2026-02-27*
