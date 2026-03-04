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
WHERE <filtr techniczny>    -- np. Rez_TwrNumer > 0
```

Ten count powinien zgadzać się z wynikiem końcowego SELECT — jeśli jest więcej, JOIN mnoży wiersze.

### c) Zbadaj pola "typowe" (enumeracje)

Dla każdego pola reprezentującego typ/status/kierunek — zanim wpiszesz CASE, sprawdź:

```sql
SELECT pole, COUNT(*) cnt FROM CDN.MainTable GROUP BY pole ORDER BY cnt DESC
```

Dla pól GIDTyp — skrzyżuj z CDN.Obiekty:

```sql
SELECT OB_GIDTyp, OB_Nazwa FROM CDN.Obiekty WHERE OB_GIDTyp IN (...)
```

### d) Zidentyfikuj typ pól datowych

```sql
SELECT MIN(col_data), MAX(col_data) FROM CDN.MainTable WHERE col_data > 0
```

- ~70000–100000 → Clarion DATE (`DATEADD(d, col, '18001228')`)
- ~10^9 → Clarion TIMESTAMP (`DATEADD(ss, col, '1990-01-01')`)
- format daty → SQL DATE (bez konwersji)

Patrz `ERP_SCHEMA_PATTERNS.md` — wzorce inline.

### e) Weryfikacja numerów dokumentów

Jeśli tabela zawiera numery dokumentów — **poproś usera** o uruchomienie w ERP:

```sql
SELECT TOP 5 cdn.NazwaObiektu(GIDTyp, GIDNumer, 0, 2), [pola do ręcznej konstrukcji]
FROM CDN.MainTable
```

Porównaj wynik z ręczną konstrukcją przed wdrożeniem.
CEiM_Reader nie ma EXECUTE na CDN functions — nie możesz tego zweryfikować sam.

### f) Sprawdź JOINy przez COUNT

Dodawaj JOINy stopniowo i sprawdzaj COUNT po każdym:

```sql
-- Po dodaniu LEFT JOIN CDN.ZamNag:
SELECT COUNT(*), COUNT(DISTINCT r.Rez_GIDNumer) FROM ... LEFT JOIN CDN.ZamNag z ON ...
WHERE ...
-- Jeśli COUNT(*) > COUNT(DISTINCT) → JOIN mnoży wiersze → dodaj warunek zawężający
```

---

## Faza 1 — Plan mapowania (plik MD, zatwierdzenie przez usera)

Utwórz plik `solutions/bi/plans/[NazwaWidoku]_plan.md` z tabelą mapowania.
**Nie pisz SQL dopóki user nie zatwierdzi planu.**

### Szablon planu

```markdown
# Plan widoku BI.[NazwaWidoku]

## Tabela główna
CDN.XXX — opis

## Filtry techniczne
- `Rez_TwrNumer > 0` — wyklucza rekordy techniczne bez towaru (N rekordów)

## JOINy
| Tabela | Typ | Klucz | Uzasadnienie |
|---|---|---|---|
| CDN.TwrKarty | INNER | Twr_GIDNumer = Rez_TwrNumer | Kod i nazwa towaru |
| CDN.KntKarty | LEFT | Knt_GIDNumer+Knt_GIDTyp = Rez_KntNumer+Rez_KntTyp | Kontrahent opcjonalny |

## Mapowanie pól
| CDN_Pole | Alias_w_raporcie | Transformacja | Uzasadnienie |
|---|---|---|---|
| Rez_GIDNumer | ID_Rezerwacji | bez zmian | klucz główny |
| Rez_DataRealizacji | Data_Realizacji | Clarion DATE | format BI |
| Rez_ZrdTyp | Opis_Typu_Dokumentu | CASE via CDN.Obiekty | czytelna etykieta |

## Metryki obliczeniowe
- `Ilosc_Do_Pokrycia = Ilosc - Zrealizowano - IloscMag`

## Baseline
- N rekordów z filtrem technicznym
```

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

Odwzorowuj kolejność kolumn z tabeli źródłowej:
GID → klucze obce (towar, kontrahent) → typ dokumentu źródłowego → magazyn → ilości → daty → flagi → metryki obliczeniowe

### Ograniczenia CEiM_BI

- Brak EXECUTE na funkcje CDN (error 229)
- Wszystkie konwersje i numery dokumentów muszą być inline
- SELECT tylko na `BI.*` — CDN przez widok

---

## Faza 3 — Export i weryfikacja

```bash
python tools/export_bi_view.py \
  --sql "SELECT TOP 5000 ..." \
  --view-name "Rezerwacje" \
  --source-table "CDN.Rezerwacje" \
  --plan "solutions/bi/plans/Rezerwacje_plan.md"
```

Następnie zweryfikuj kolumny przez statystyki:

```bash
python tools/read_excel_stats.py \
  --file "exports/Rezerwacje_TIMESTAMP.xlsx" \
  --sheet "Wynik" \
  --max-unique 15
```

Na co patrzeć:
- Pola datowe: czy wartości wyglądają jak daty (nie liczby), czy NULL tam gdzie spodziewany
- Pola typów (enumeracje): czy distinct ≤ oczekiwana liczba wartości, czy etykiety sensowne
- Metryki obliczeniowe: czy wartości w rozsądnym zakresie (nie ujemne tam gdzie nie powinny)
- Row count: czy COUNT z baseline zgadza się z wynikiem SELECT

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

- Numery dokumentów — zawsze weryfikuj przez CDN.NazwaObiektu (user musi uruchomić)
- Pole z enumeracją nieznaną (nie ma w CDN.Obiekty, brak dokumentacji) — poproś o wyjaśnienie
- Wynik pusty lub row count znacząco inny od baseline — nie zgaduj, zapytaj
- Odkryjesz nowy wzorzec konwersji lub nieoczywiste pole — dopisz do `ERP_SCHEMA_PATTERNS.md`
