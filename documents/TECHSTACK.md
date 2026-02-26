# TECHSTACK: Automatyczny Konfigurator Systemu ERP

## 1. Przegląd decyzji technicznych

| Komponent | Wybrana technologia | Alternatywa odrzucona |
|-----------|--------------------|-----------------------|
| Agent | Claude Code + MCP | LangChain / AutoGen |
| Połączenie SQL Server | `pyodbc` | `sqlalchemy` + `pyodbc` |
| Parsowanie dokumentacji Excel | `openpyxl` | `pandas` |
| Indeks dokumentacji | SQLite + FTS5 | `sentence-transformers` |
| Baza rozwiązań | pliki `.sql` + `index.json` | SQLite |
| Środowisko Python | Python 3.12 | — |
| Logowanie | `logging` (stdlib) → JSON | zewnętrzne frameworki |

---

## 2. Agent — Claude Code + MCP

**Decyzja:** Claude Code jako środowisko agenta, narzędzia agenta jako MCP tools zaimplementowane w Pythonie.

**Uzasadnienie:**
- Zero kodu frameworku agenta — Claude Code zarządza pętlą myślenia i wywoływaniem narzędzi
- Narzędzia MCP to zwykłe skrypty Python wywoływane przez Claude Code z terminala VS Code
- Krótki czas do MVP w porównaniu do budowania własnego agenta od zera

**Odrzucone:** LangChain / AutoGen — nadmiarowa złożoność dla projektu jednoużytkownikowego; wymagają budowania pętli agenta od zera.

---

## 3. Połączenie z SQL Server — `pyodbc`

**Decyzja:** Bezpośrednie połączenie przez `pyodbc` bez warstwy ORM.

**Uzasadnienie:**
- Agent wykonuje wyłącznie operacje SELECT — ORM (SQLAlchemy) jest zbędny
- Jedna zależność zamiast dwóch
- Pełna kontrola nad treścią zapytania SQL

**Konfiguracja:** connection string przechowywany w `.env`, wczytywany przez `python-dotenv`.

---

## 4. Parsowanie dokumentacji Excel — `openpyxl`

**Decyzja:** `openpyxl` do jednorazowego parsowania pliku `.xlsm` i importu do SQLite.

**Uzasadnienie:**
- `openpyxl` jest już zainstalowany w środowisku
- Plik dokumentacji (`Przetwarzanie bazy XL pod zapytania LLM`) zawiera 12 arkuszy z ustrukturyzowanymi danymi (tabele, kolumny, relacje, słowniki wartości)
- Import odbywa się raz przy inicjalizacji lub na żądanie (`search_docs --reindex`)

**Odrzucone:** `pandas` — zbędna zależność przy prostym imporcie wierszy do SQLite.

**Struktura źródłowa Excel:**

| Arkusz | Wiersze | Zawartość |
|--------|---------|-----------|
| Tabele | ~1 650 | Nazwy tabel, prefiksy, opisy, liczba kolumn |
| Kolumny | ~18 650 | Kolumny z typami, rolami, flagami użyteczności |
| Relacje | ~10 420 | Powiązania między tabelami |
| Słownik wartości kolumn | ~100 | Znaczenie wartości enum (np. Knt_Typ: 8=Dostawca) |
| Przykładowe wartości kolumn | ~41 270 | Przykładowe wartości per kolumna |
| Opcje kolumn | ~18 430 | Opcje SQL (IDENTITY, klucze) |
| Kolumny_do_LLM | ~87 | Ręcznie kurowany kontekst do bieżącego zadania |
| Relacje_dla_LLM | — | Ręcznie kurowane relacje do bieżącego zadania |

---

## 5. Indeks dokumentacji — SQLite + FTS5

**Decyzja:** SQLite z rozszerzeniem FTS5 jako indeks przeszukiwalnej dokumentacji.

**Uzasadnienie:**
- FTS5 wbudowany w Python (stdlib `sqlite3`) — zero dodatkowych zależności
- Obsługuje wyszukiwanie pełnotekstowe po nazwach kolumn, opisach, wartościach słownikowych
- Dane persystują między sesjami (w przeciwieństwie do in-memory DataFrame)
- Wystarczający przy skali ~18 650 kolumn i ~1 650 tabel
- Rozszerzalny na embeddingi semantyczne w Fazie 4 (można dodać kolumnę `embedding BLOB`)

**Odrzucone:** `sentence-transformers` — zależność ~500 MB, model ML, overhead inicjalizacji; nieuzasadniony przy danych dobrze opisanych strukturalnie.

**Schemat indeksu (koncepcja):**
- Tabela `tables`: numer, nazwa, prefiks, opis
- Tabela `columns`: nr tabeli, nazwa kolumny, typ, opis, przykładowe wartości, słownik wartości
- Tabela `relations`: tabela źródłowa, tabela docelowa, kolumny łączące
- Wirtualna tabela FTS5 indeksująca: nazwy tabel, nazwy kolumn, opisy, słowniki wartości

---

## 6. Baza rozwiązań — pliki `.sql` + `index.json`

**Decyzja:** Katalog plików `.sql` z plikiem metadanych `index.json`.

**Uzasadnienie:**
- Czytelna dla człowieka — pliki `.sql` można przeglądać i edytować bez narzędzi
- Prosta do rozszerzania — dodanie nowego rozwiązania to dodanie pliku i wpisu w JSON
- Kontrola wersji (Git) działa naturalnie z plikami tekstowymi
- Przy spodziewanej skali (docelowo ~50–200 rozwiązań) SQLite nie przynosi korzyści

**Struktura metadanych `index.json`:** typ konfiguracji (kolumna/filtr/raport), tabele źródłowe, słowa kluczowe, data dodania, autor.

---

## 7. Środowisko — Python 3.12

**Decyzja:** Python 3.12 (wersja zainstalowana w środowisku).

**Zależności projektu:**

| Pakiet | Wersja | Zastosowanie |
|--------|--------|--------------|
| `pyodbc` | najnowsza | Połączenie z SQL Server |
| `openpyxl` | najnowsza | Parsowanie pliku `.xlsm` |
| `python-dotenv` | najnowsza | Wczytywanie `.env` |

Wszystkie zależności stdlib (sqlite3, logging, json, pathlib) — bez dodatkowych pakietów.

---

## 8. Logowanie — `logging` (stdlib)

**Decyzja:** Moduł `logging` z Pythona stdlib, zapis do pliku JSON per sesja.

**Uzasadnienie:**
- Zero dodatkowych zależności
- Structured logging (JSON) umożliwia późniejszą analizę sesji
- Pliki sesji w `logs/sessions/` zgodnie z wymaganiem F-08 z PRD

---

*Dokument przygotowany: 2026-02-26*
