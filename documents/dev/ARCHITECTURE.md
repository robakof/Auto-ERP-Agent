# ARCHITECTURE: Automatyczny Konfigurator Systemu ERP

## 1. Diagram wysokiego poziomu

```
Użytkownik (VS Code)
        │
        ▼
  Claude Code (agent)
        │
        ├──► python tools/sql_query.py "SELECT ..."
        │           │
        │           └──► SQL Server (read-only)
        │
        ├──► python tools/search_docs.py "zamówienie kontrahent"
        │           │
        │           └──► erp_docs/index/docs.db (SQLite FTS5)
        │
        ├──► python tools/search_solutions.py "kolumna KntKarty"
        │           │
        │           └──► solutions/**/*.sql + solutions/**/*.json
        │
        └──► python tools/save_solution.py ...
                    │
                    └──► solutions/ (zapis po akceptacji człowieka)
```

---

## 2. Komponenty systemu

### 2.1 Agent — Claude Code

Rdzeń systemu. Operuje wewnątrz VS Code, wywołuje narzędzia jako komendy CLI, iteruje do uzyskania poprawnego wyniku. Nie ma własnego kodu — to konfiguracja środowiska (`.env`, `CLAUDE.md`).

### 2.2 Narzędzia MCP (tools/)

Cztery skrypty Python wywoływane przez agenta. Każde narzędzie to niezależny proces — przyjmuje argumenty z CLI, zwraca wynik na stdout (JSON), kończy działanie.

| Skrypt | Wejście | Wyjście |
|--------|---------|---------|
| `sql_query.py` | zapytanie SQL (string) | wyniki SELECT jako JSON |
| `search_docs.py` | fraza / nazwa tabeli | pasujące kolumny, opisy, słowniki wartości |
| `search_solutions.py` | słowa kluczowe / typ | lista pasujących rozwiązań z kodem SQL |
| `save_solution.py` | kod SQL + metadane | zapis do `solutions/` (plik `.sql` + plik `.json`) |
| `search_windows.py` | fraza (nazwa okna) | pasujące okna ERP z tabelami i typami konfiguracji |

### 2.3 Indeks dokumentacji (erp_docs/index/docs.db)

Baza SQLite budowana jednorazowo ze źródeł w `erp_docs/raw/`. Agent odpytuje ją przez `search_docs.py`. Nie jest modyfikowana podczas sesji.

**Tabele:**
- `tables` — numer, nazwa (CDN.XXX), prefiks, opis
- `columns` — nr tabeli, nazwa kolumny, typ, opis, przykładowe wartości, słownik wartości
- `relations` — tabela źródłowa, tabela docelowa, kolumny łączące
- `columns_fts` — wirtualna tabela FTS5 (indeksuje: nazwa tabeli, nazwa kolumny, opis, słownik wartości)

### 2.4 Baza rozwiązań (solutions/)

Kolekcja zatwierdzonych fragmentów SQL zorganizowana hierarchicznie wg okna ERP i widoku. Struktura folderów sama w sobie koduje metadane (okno, widok, typ).

```
solutions/
└── solutions in ERP windows/
    └── [Okno ERP]/
        └── [Widok]/
            ├── filtr.sql          ← główny filtr widoku (kotwica)
            ├── columns/
            │   └── [nazwa].sql    ← definicja kolumny
            └── filters/
                └── [nazwa].sql    ← definicja filtru
```

`search_solutions.py` odkrywa pliki przez przeszukiwanie drzewa katalogów — okno i widok odczytuje ze ścieżki. Brak centralnego indeksu eliminuje ryzyko konfliktu przy równoległym zapisie.

**Format plików SQL (potwierdzony eksperymentem E-05):**

Kolumny — pełny `SELECT` z aliasami `[NAZWA]`, JOINami i placeholderem `{filtrsql}` na końcu:
```
SELECT kolumna [ALIAS] FROM cdn.Tabela JOIN ... WHERE {filtrsql}
```

Filtry — wyłącznie warunek WHERE (bez SELECT), opcjonalnie z deklaracjami parametrów:
```
@PAR ?@S20|zmienna|&Etykieta:REG=domyslna @? PAR@
warunek WHERE używający ??zmienna
```

Typy parametrów filtrów: `S[N]` (string), `D[N]` (data), `R(SELECT ...)` (dropdown z bazy).

`filtr.sql` w katalogu widoku — kotwica definiująca główny kontekst widoku (np. `TwG_GIDNumer=3282`).

### 2.5 Źródła dokumentacji (erp_docs/raw/)

Dane wejściowe do budowy indeksu — nie czytane bezpośrednio przez agenta.

```
erp_docs/raw/
├── Przetwarzanie bazy XL pod zapytania LLM - testowanie makro.xlsm
│       ← główne źródło: tabele, kolumny, relacje, słowniki
└── Dokumnetacja bazy/
        ← HTML per tabela (backup/uzupełnienie)
```

### 2.6 Logi sesji

Nie zaimplementowane w MVP. Rolę historii sesji pełni historia commitów Git (`git log solutions/`) oraz pliki w `solutions/` jako artefakty zakończonych zadań.

---

## 3. Data Flow — typowa sesja

```
1. WYMAGANIE
   Użytkownik podaje wymaganie w języku naturalnym, np.:
   "Dodaj kolumnę z nazwą kontrahenta do listy zamówień"

2. EKSPLORACJA SCHEMATU
   Agent → sql_query.py
   "SELECT kolumny z INFORMATION_SCHEMA dla ZamNag i KntKarty"
   ← JSON z listą kolumn i typów

3. WYSZUKIWANIE DOKUMENTACJI
   Agent → search_docs.py "ZamNag kontrahent nazwa"
   ← Pasujące kolumny z opisami i przykładowymi wartościami

4. WYSZUKIWANIE WZORCÓW
   Agent → search_solutions.py "kolumna kontrahent zamówienie"
   ← Pasujące rozwiązania SQL z poprzednich sesji

5. GENEROWANIE KODU
   Agent generuje kod SQL na podstawie zebranych danych

6. TESTOWANIE
   Agent → sql_query.py [wygenerowane zapytanie testujące]
   ← Wynik: dane lub błąd SQL

   Jeśli błąd → analiza → korekta → powrót do kroku 6
   (maks. 5 iteracji, potem eskalacja do człowieka)

7. PREZENTACJA WYNIKU
   Agent wyświetla gotowy kod SQL + instrukcję wklejenia do ERP

8. ZAPIS (po akceptacji)
   Agent → save_solution.py [kod + metadane]
   ← Nowe rozwiązanie dodane do solutions/
```

---

## 4. Przepływ danych — inicjalizacja indeksu

```
erp_docs/raw/*.xlsm
        │
        ▼
  tools/build_index.py
  (uruchamiany raz lub na żądanie --reindex)
        │
        ├── parsuje arkusze: Tabele, Kolumny, Relacje,
        │   Słownik wartości kolumn, Przykładowe wartości kolumn
        │
        └──► erp_docs/index/docs.db (SQLite FTS5)
```

---

## 5. Struktura plików projektu

```
/
├── .env                        ← connection string SQL Server (nie w repo)
├── .env.example                ← szablon
├── CLAUDE.md                   ← instrukcje operacyjne agenta ERP
├── INSTALL.md                  ← instrukcja instalacji na nowej maszynie
├── verify.py                   ← skrypt weryfikacji instalacji
│
├── documents/
│   ├── agent/
│   │   └── ERP_SQL_SYNTAX.md  ← składnia SQL specyficzna dla Comarch XL
│   └── dev/
│       ├── AI_GUIDELINES.md   ← wytyczne dla agenta deweloperskiego
│       ├── ARCHITECTURE.md    ← ten dokument
│       └── progress_log.md    ← log postępów prac
│
├── tools/
│   ├── sql_query.py            ← narzędzie: zapytania SQL Server
│   ├── search_docs.py          ← narzędzie: przeszukiwanie indeksu
│   ├── search_solutions.py     ← narzędzie: przeszukiwanie bazy rozwiązań
│   ├── search_windows.py       ← narzędzie: identyfikacja okna ERP
│   ├── save_solution.py        ← narzędzie: zapis nowego rozwiązania
│   ├── update_window_catalog.py ← narzędzie: zarządzanie erp_windows.json
│   ├── build_index.py          ← inicjalizacja indeksu SQLite z Excel
│   └── db.py                   ← wspólna logika połączenia SQLite
│
├── solutions/
│   ├── erp_windows.json        ← katalog okien ERP
│   └── solutions in ERP windows/
│       └── [Okno ERP]/
│           └── [Widok]/
│               ├── filtr.sql   ← kotwica widoku
│               ├── columns/
│               └── filters/
│
├── erp_docs/
│   ├── raw/                    ← pliki źródłowe (Excel, HTML)
│   └── index/
│       └── docs.db             ← SQLite FTS5 (w repo, ~7 MB)
│
└── tests/                      ← testy jednostkowe (pytest)
```

---

## 6. Kluczowe wzorce projektowe

**Thin tools, smart agent** — narzędzia są proste i deterministyczne (wejście → wyjście), cała logika decyzji po stronie agenta. Narzędzie nie "wie" po co jest wywoływane.

**Read-only by default** — `sql_query.py` wymaga trzech warstw ochrony:
1. Użytkownik bazy danych z uprawnieniami wyłącznie SELECT (konfiguracja DB — główna bariera)
2. Odrzucanie zapytań zawierających DML/DDL, EXEC, wielokrotne instrukcje (`;` poza końcem) przed wysłaniem
3. Automatyczne dopisywanie `TOP 100` do zapytań testowych + timeout na poziomie sterownika pyodbc

**Eskalacja przez output** — agent sygnalizuje potrzebę interwencji człowieka przez wyraźny komunikat w terminalu; brak osobnego mechanizmu powiadomień.

**Idempotentna inicjalizacja** — `build_index.py` można uruchomić wielokrotnie; zawsze buduje indeks od zera na podstawie aktualnych plików źródłowych.

---

## 7. Katalog okien ERP

### Problem

Komendy użytkownika odnoszą się do okien aplikacji ERP, nie do tabel SQL. Jedno okno = jeden lub kilka widoków SQL. Agent musi wiedzieć, które okno użytkownik ma na myśli, zanim dobierze właściwe tabele.

Przykład: "dodaj kolumnę z nazwą kontrahenta" — niejednoznaczne:
- Okno przeglądania kartotek kontrahentów → tabela `CDN.KntKarty`
- Lista kontrahentów w oknie zamówień → tabela `CDN.ZamNag` + JOIN `CDN.KntKarty`
- Kartoteka towaru w dokumencie → inna tabela

### Rozwiązanie: `erp_windows.json`

Plik katalogu okien przechowywany w `solutions/erp_windows.json`. Tworzony i rozszerzany ręcznie przez developera.

**Struktura wpisu:**
- `id` — unikalny identyfikator okna
- `name` — nazwa wyświetlana w ERP (jak widzi ją użytkownik)
- `aliases` — popularne nazwy nieformalne ("okno zamówień", "lista ZO")
- `primary_table` — główna tabela SQL okna
- `related_tables` — tabele joinowane typowo w tym oknie
- `config_types` — co można konfigurować: kolumny / filtry / raporty

**Workflow agenta przy niejednoznacznym wymaganiu:**
```
Użytkownik: "dodaj kolumnę do okna zamówień"
        │
        ▼
Agent → search_windows.py "zamówienia"
        │
        ▼
Znaleziono 3 okna:
  [1] Lista zamówień sprzedaży (ZamNag)
  [2] Lista zamówień zakupu (ZamNag, typ=2)
  [3] Pozycje zamówienia (ZamElem)
        │
        ▼
Agent pyta użytkownika o doprecyzowanie
        │
        ▼
Kontynuuje z właściwą tabelą
```

**Piąte narzędzie:** `tools/search_windows.py` — przeszukuje `erp_windows.json` po nazwie, aliasach i typie konfiguracji.

---

## 8. Strategia nawigacji po 1000 tabelach

### Problem

Agent nie może przeglądać 1647 tabel sekwencyjnie. Nazwy kolumn SQL są nieczyttelne (`ZaN_KntGIDNumer`). Opisy i przykładowe wartości są kluczowe dla zrozumienia — ale jest ich ~18 650.

### Podejście: warstwy filtrowania

```
Warstwa 1 — Okno ERP
  Agent zna już primary_table z katalogu okien
  → zawęża przestrzeń do 1-5 tabel

Warstwa 2 — Własne nazwy i flagi użyteczności
  Kolumny oznaczone "Czy użyteczna = TAK" i "Preferowana do raportów"
  Własne opisy tabel (Nazwa własna tabeli) i kolumn (Nazwa własna kolumny)
  → FTS po opisowych nazwach, nie po kodach SQL

Warstwa 3 — Słowniki wartości
  Dla kolumn enum (np. typ dokumentu, status) — agent rozumie znaczenie wartości
  → precyzyjne warunki WHERE w generowanym SQL

Warstwa 4 — Przykładowe wartości
  Weryfikacja przez sql_query.py: czy kolumna zawiera to czego szukam?
  → ostateczna weryfikacja przez zapytanie do żywej bazy
```

### Jak własne nazwy użytkownika trafiają do agenta

Arkusze Excel (`Tabele.Nazwa własna tabeli`, `Kolumny.Nazwa własna kolumny`, `Kolumny.Czy użyteczna`, `Kolumny.Preferowana do raportów`) są importowane do SQLite przez `build_index.py`. Agent przeszukuje te pola w pierwszej kolejności — zanim sięgnie po oryginalne nazwy SQL.

### Strategia formułowania zapytań FTS5

FTS5 nie wykonuje stemmingu — `zamowienie` nie pasuje do `zamówień`. Rozwiązanie potwierdzone eksperymentem E-03:

- Tokenizer: `unicode61 remove_diacritics=2` — usuwa ogonki z indeksu i zapytań
- Zapytania agenta: **prefix matching** z rdzeniem słowa, np. `kontrah* zamow*` zamiast `kontrahent zamówienie`
- Domyślnie filtruj do kolumn z flagą `Czy użyteczna` — eliminuje 95% szumu
- Kolumny i tabele bez własnych nazw zwracają słabe wyniki — adnotacja Excel jest krytyczna dla jakości wyszukiwania

---

## 9. Model synchronizacji przez Git

### Problem

Każda maszyna z osobną bazą rozwiązań i dokumentacją → brak wymiany wiedzy między użytkownikami.

### Rozwiązanie

```
GitHub (CyperCyper/Auto-ERP-Agent)
│
├── [Maszyna A] git clone → praca → git add solutions/ → git commit → git push
├── [Maszyna B] git clone → git pull (pobiera nowe rozwiązania od A)
└── [Maszyna C] git clone → git pull
```

**Jak to działa:**
- Agent po każdym zatwierdzonym rozwiązaniu commituje i pushuje (`solutions/`, `erp_windows.json`)
- Pozostałe maszyny pobierają zmiany przez `git pull`
- `docs.db` (~7 MB) jest w repo — nie wymaga rebuild przy instalacji
- Brak ryzyka konfliktu zapisu — każde rozwiązanie to osobny plik `.sql` w unikatowej ścieżce

**Konfiguracja per maszyna (`.env`):**
- `SQL_SERVER`, `SQL_DATABASE`, `SQL_USERNAME`, `SQL_PASSWORD` — dostęp do SQL Server

---

## 10. Deployment na kolejnych maszynach

```
1. git clone https://github.com/CyperCyper/Auto-ERP-Agent.git
2. cd Auto-ERP-Agent
3. pip install -r requirements.txt
4. copy .env.example .env  # uzupełnij SQL credentials
5. python verify.py        # weryfikacja: docs.db, solutions/, SQL Server
6. Otwórz VS Code, uruchom Claude Code
```

`docs.db` i cała baza rozwiązań są w repo — żadna dodatkowa inicjalizacja nie jest potrzebna.

---

## 11. Kontrakty JSON narzędzi

Każde narzędzie zwraca na stdout JSON zgodny z poniższym schematem. Agent może zawsze oczekiwać tych samych pól.

**Schemat bazowy (wszystkie narzędzia):**
```
{
  "ok": true | false,
  "data": { ... },        ← wynik (null gdy ok=false)
  "error": {              ← null gdy ok=true
    "type": "SQL_ERROR | NOT_FOUND | NETWORK_UNAVAILABLE | PERMISSION_DENIED | ...",
    "message": "..."
  },
  "meta": {
    "duration_ms": 142,
    "truncated": false     ← true gdy wynik obcięty do TOP 100
  }
}
```

**`sql_query.py` — pole `data`:**
```
{
  "columns": ["col1", "col2"],
  "rows": [["val1", "val2"], ...],
  "row_count": 42
}
```

**`search_docs.py` — pole `data`:**
```
{
  "results": [
    {
      "table_name": "CDN.ZamNag",
      "table_label": "Nagłówki zamówień",
      "column_name": "ZaN_KntGIDNumer",
      "column_label": "ID Kontrahenta",
      "type": "INTEGER",
      "is_useful": true,
      "description": "...",
      "value_dict": "...",
      "sample_values": "..."
    }
  ]
}
```

**`search_solutions.py` — pole `data`:**
```
{
  "results": [
    {
      "window": "Okno lista zamówień sprzedaży",
      "view": "Zamówienia",
      "type": "columns",
      "name": "knt_nazwa_w_zamowieniach",
      "sql": "...",
      "filtr_sql": "..."    ← zawartość filtr.sql z katalogu widoku
    }
  ]
}
```

**`search_windows.py` — pole `data`:**
```
{
  "results": [
    {
      "id": "lista_zamowien_sprzedazy",
      "name": "Lista zamówień sprzedaży",
      "aliases": ["okno zamówień", "lista ZO"],
      "primary_table": "CDN.ZamNag",
      "config_types": ["columns", "filters"]
    }
  ]
}
```

---

*Dokument przygotowany: 2026-02-26 | Zaktualizowany: 2026-03-03*
