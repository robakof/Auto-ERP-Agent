# ERP — Workflow tworzenia widoków BI

Widoki BI tworzone są w schemacie `BI` przez konto DBA i udostępniane kontu `CEiM_BI`.
Tworzenie widoku to operacja złożona — wymaga fazy discovery i zatwierdzonego planu.

---

## Faza 0 — Discovery (PRZED pisaniem SQL)

Wykonaj przed napisaniem jakiegokolwiek kodu. Cel: zrozumieć dane, nie zgadywać.

### a) Poznaj strukturę tabeli

```sql
SELECT TOP 1 * FROM CDN.MainTable
```

### b) Ustal baseline row count

```sql
SELECT COUNT(*), COUNT(DISTINCT GIDNumer) FROM CDN.MainTable
WHERE <filtr techniczny>
```

Ten count musi zgadzać się z wynikiem końcowego SELECT. Jeśli po dodaniu JOINów jest więcej — JOIN mnoży wiersze.

### c) Zbadaj pola "typowe" (enumeracje)

Najpierw pobierz WSZYSTKIE unikalne wartości pola:

```sql
SELECT pole, COUNT(*) cnt FROM CDN.MainTable GROUP BY pole ORDER BY cnt DESC
```

Następnie jednym zapytaniem skrzyżuj **wszystkie znalezione wartości** z CDN.Obiekty:

```sql
SELECT OB_GIDTyp, OB_Nazwa, OB_Skrot
FROM CDN.Obiekty
WHERE OB_GIDTyp IN (<wszystkie DISTINCT wartości z poprzedniego zapytania>)
```

Jeśli jakaś wartość nie ma odpowiednika w CDN.Obiekty — **eskaluj do usera** z surówką
(ile rekordów, jakie charakterystyczne pola) zanim wpiszesz ją do CASE. Nie zgaduj etykiety.

### d) Zidentyfikuj typ pól datowych

```sql
SELECT MIN(col_data), MAX(col_data) FROM CDN.MainTable WHERE col_data > 0
```

- ~70000–100000 → Clarion DATE (`DATEADD(d, col, '18001228')`)
- ~10^9 → Clarion TIMESTAMP (`DATEADD(ss, col, '1990-01-01')`)
- format daty → SQL DATE (bez konwersji)

Patrz `ERP_SCHEMA_PATTERNS.md` — wzorce inline.

### e) Weryfikacja numerów dokumentów

Jeśli tabela zawiera numery dokumentów — **poproś usera** o uruchomienie w SSMS.
Zapytanie musi zwrócić **po jednym przykładzie na każdy typ dokumentu** (nie TOP 5 losowo):

```sql
USE [ERPXL_CEIM];
GO

SELECT NumerERP, TypDok, [pola do ręcznej konstrukcji]
FROM (
    SELECT
        [CDN].[NazwaObiektu](TypPole, NumerPole, 0, 2) AS NumerERP,
        TypPole AS TypDok,
        [pola],
        ROW_NUMBER() OVER (PARTITION BY TypPole ORDER BY NumerPole DESC) AS rn
    FROM [CDN].[MainTable]
) x
WHERE rn = 1
ORDER BY TypDok;
```

Porównaj każdy typ z ręczną konstrukcją. CEiM_Reader nie ma EXECUTE na CDN functions.

### f) Sprawdź JOINy przez COUNT

Dodawaj JOINy jeden po drugim i sprawdzaj COUNT po każdym:

```sql
SELECT COUNT(*), COUNT(DISTINCT r.GIDNumer) FROM ... LEFT JOIN CDN.XXX ON ...
WHERE ...
-- Jeśli COUNT(*) > COUNT(DISTINCT) → JOIN mnoży wiersze → dodaj warunek zawężający
```

---

## Faza 1 — Plan mapowania (plik MD, zatwierdzenie przez usera)

**Zapisz plik PRZED pokazaniem go userowi.** Plan nie istnieje dopóki nie ma pliku.

```
solutions/bi/plans/[NazwaWidoku]_plan.md
```

Następnie pokaż treść pliku userowi i czekaj na zatwierdzenie. **Nie pisz SQL dopóki user nie zatwierdzi planu.**

### Szablon planu

```markdown
# Plan widoku BI.[NazwaWidoku]

## Tabela główna
CDN.XXX — opis, N rekordów z filtrem technicznym

## Filtry techniczne
- [warunek] — wyklucza N rekordów, uzasadnienie

## JOINy
| Tabela | Typ | Klucz | Uzasadnienie |
|---|---|---|---|
| CDN.XXX | INNER/LEFT | klucz | po co ten JOIN |

## Mapowanie pól
| CDN_Pole | Transformacja | Alias_w_raporcie | Uzasadnienie |
|---|---|---|---|
| XXX_GIDNumer | bez zmian | ID_[Encja] | klucz główny |
| XXX_DataXXX | Clarion DATE / TIMESTAMP / SQL DATE | Data_XXX | format BI |
| XXX_TypXXX | CASE via CDN.Obiekty | Opis_XXX | czytelna etykieta |

## Metryki obliczeniowe
- [Alias = formuła CDN]

## Baseline
- N rekordów (COUNT = COUNT DISTINCT ✓)
```

Uwaga: w tabeli mapowania **CDN_Pole jest główną kolumną** — plan dokumentuje które oryginalne
pola bazy są przetwarzane i w jaki sposób.

---

## Faza 2 — Generowanie SQL (po zatwierdzeniu planu)

### Zasady nazewnictwa

- Widok: `BI.Rezerwacje`, `BI.Zamowienia` (rzeczownik mnogi, PascalCase)
- Kolumny: `Kod_Towaru`, `Data_Realizacji`, `ID_Rezerwacji` (underscore, opisowe)
- Klucz główny: `ID_[encja]` (np. `ID_Rezerwacji` — nie samo `ID`)
- Dla każdego lookup: kod + nazwa (np. `Kod_Magazynu` + `Nazwa_Magazynu`)

### Brak WHERE z logiką biznesową

Widoki BI zwracają pełne zbiory — filtrowanie wykonuje bot/Power BI:

```sql
-- Poprawnie — tylko wykluczenie rekordów technicznych:
WHERE r.Rez_TwrNumer > 0

-- Błędnie — ogranicza Power BI:
WHERE r.Rez_Aktywna = 1
```

### Kolejność kolumn

Odwzorowuj kolejność kolumn z tabeli źródłowej — sprawdź przez `SELECT TOP 1 * FROM CDN.Tabela`
i trzymaj się jej. Metryki obliczeniowe dopisuj na końcu.

### Ograniczenia CEiM_BI

- Brak EXECUTE na funkcje CDN (error 229)
- Wszystkie konwersje i numery dokumentów muszą być inline
- SELECT tylko na `BI.*` — CDN przez widok

---

## Faza 3 — Export i weryfikacja (po zatwierdzeniu SQL, bez pytania usera)

Po akceptacji SQL przez usera uruchom export i weryfikację **bez dodatkowego pytania**:

```bash
python tools/export_bi_view.py \
  --sql "SELECT ..." \
  --view-name "[NazwaWidoku]" \
  --source-table "CDN.MainTable" \
  --plan "solutions/bi/plans/[NazwaWidoku]_plan.md"
```

Następnie **obowiązkowo** uruchom statystyki:

```bash
python tools/read_excel_stats.py \
  --file "exports/[NazwaWidoku]_TIMESTAMP.xlsx" \
  --sheet "Wynik" \
  --max-unique 15
```

### Weryfikacja wyników

Sprawdź przed pokazaniem userowi:

- **Row count**: `row_count` z exportu musi równać się `COUNT(*)` z bazy z tego samego SQL.
  Jeśli różnią się — zbadaj dlaczego (nie zakładaj "dane się zmieniły"). Różnica może oznaczać
  błąd w JOINach lub pominięte wiersze.
- Pola datowe: czy wartości wyglądają jak daty (nie surowe liczby Clarion)
- Enumeracje: czy `distinct` ≤ oczekiwana liczba typów, czy etykiety sensowne
- Metryki: czy wartości w rozsądnym zakresie

---

## Faza 4 — Zapis i commit (po akceptacji usera)

```sql
CREATE OR ALTER VIEW BI.NazwaWidoku AS
<SELECT>
```

Zapisz do `solutions/bi/views/NazwaWidoku.sql`, zaktualizuj `solutions/bi/catalog.json`:

```json
{
  "name": "BI.NazwaWidoku",
  "file": "views/NazwaWidoku.sql",
  "description": "...",
  "primary_table": "CDN.XXX",
  "joins": ["CDN.YYY"],
  "columns": ["ID_Encji", "Kolumna1"],
  "notes": "Wskazówki: wartości kodowane, warunki filtrowania dla bota"
}
```

Następnie commit:

```bash
git add solutions/bi/
git commit -m "feat: widok BI.[NazwaWidoku] — opis"
git push
```

---

## Kiedy eskalować do usera

- Wartość enumeracji nieznana (brak w CDN.Obiekty) — podaj surówkę: ile rekordów, jakie charakterystyczne pola
- Numery dokumentów — zawsze weryfikuj przez CDN.NazwaObiektu (user musi uruchomić w SSMS)
- Row count z exportu ≠ COUNT z bazy — zbadaj i wyjaśnij różnicę zanim pokażesz wyniki
- Wynik zapytania pusty lub dane wyglądają na błędne — nie zgaduj kontekstu biznesowego
- Odkryjesz nowy wzorzec — dopisz do `ERP_SCHEMA_PATTERNS.md` natychmiast
