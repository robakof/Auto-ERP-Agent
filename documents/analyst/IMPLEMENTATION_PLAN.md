# Analityk Danych — Plan implementacji

---

## Kamienie milowe

### KM1 — Fundament SQLite (data_quality_init + data_quality_query)

Cel: agent może zainicjalizować obszar roboczy i odpytywać dane lokalnie.

**`tools/data_quality_init.py`**
- Przyjmuje `--source` (widok BI lub tabela CDN) i `--output` (ścieżka .db)
- Eksportuje dane do tabeli `dane` w SQLite
- Tworzy puste tabele `findings` i `records` ze stałym schematem
- Jeśli plik istnieje — błąd z informacją (nie nadpisuje bez flagi `--force`)

Schema SQLite:
```sql
CREATE TABLE findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    column TEXT,
    observation TEXT,
    rows_affected INTEGER,
    created_at TEXT
);

CREATE TABLE records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    column TEXT,
    data TEXT,  -- JSON z identyfikatorami i wartością problematyczną
    created_at TEXT
);
```

**`tools/data_quality_query.py`**
- Przyjmuje `--db` i `--sql`
- Odpytuje lokalny SQLite (tabela `dane`)
- Obsługuje `--count-only` i `--quiet` (spójność z sql_query.py)
- Output: JSON przez print_json()

Testy: inicjalizacja z widokiem, inicjalizacja z tabelą CDN, query cross-column,
count-only, błąd gdy brak pliku.

---

### KM2 — Zapis znalezisk (data_quality_save + data_quality_records)

Cel: agent może zapisywać obserwacje i konkretne rekordy do pliku roboczego.

**`tools/data_quality_save.py`**
- Przyjmuje `--db`, `--column`, `--observation`, `--rows-affected`
- Dopisuje wiersz do tabeli `findings`
- Output: potwierdzenie zapisu (id wpisu)

**`tools/data_quality_records.py`**
- Przyjmuje `--db`, `--column`, `--sql`
- Wykonuje query na SQLite (tabela `dane`) i dopisuje wyniki do tabeli `records`
- Każdy wiersz wyniku serializowany jako JSON do kolumny `data`
- Output: liczba zapisanych rekordów

Testy: zapis obserwacji, zapis rekordów, wielokrotny append, query bez wyników.

---

### KM3 — Raport Excel (data_quality_report)

Cel: agent generuje gotowy raport dla użytkownika.

**`tools/data_quality_report.py`**
- Przyjmuje `--db` i `--output`
- Czyta `findings` → zakładka **Obserwacje**
- Czyta `records`, deserializuje JSON → zakładka **Rekordy**
- Kolumny w Rekordach: dynamiczne (z kluczy JSON) + stałe `Kolumna`, `created_at`
- Styl: Excel Table (zebra-stripes, Medium9) — spójnie z resztą projektu

Testy: raport z findings i records, raport tylko z findings, pusty raport (brak znalezisk).

---

### KM4 — Integracja z projektem (CLAUDE.md + ANALYST.md)

Cel: agent może być wywołany w roli Analityka Danych przez routing w CLAUDE.md.

**`documents/analyst/ANALYST.md`**
- Instrukcje operacyjne roli (workflow krok po kroku)
- Oparty na ARCHITECTURE.md — operacyjny, nie opisowy
- Wzorowany na strukturze AGENT.md

**`CLAUDE.md`** — dodanie wiersza do tabeli ról:
```
| Analityk | Analiza jakości danych, przegląd widoków BI | documents/analyst/ANALYST.md |
```

Testy: brak (dokumentacja) — weryfikacja przez sesję testową z agentem.

---

## Kolejność prac

```
KM1 → KM2 → KM3 → KM4
```

Każdy KM = osobny commit po przejściu testów.

---

## Pliki do stworzenia

```
tools/
├── data_quality_init.py
├── data_quality_query.py
├── data_quality_save.py
├── data_quality_records.py
└── data_quality_report.py

tests/
├── test_data_quality_init.py
├── test_data_quality_query.py
├── test_data_quality_save.py
├── test_data_quality_records.py
└── test_data_quality_report.py

documents/analyst/
└── ANALYST.md
```

`CLAUDE.md` — modyfikacja (chroniony plik — wymaga zatwierdzenia).
