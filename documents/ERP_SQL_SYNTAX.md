# ERP SQL Syntax — Wytyczne dla agenta

Dokument opisuje składnię SQL akceptowaną przez system ERP przy konfiguracji kolumn i filtrów. Agent musi generować kod ściśle zgodny z poniższymi wzorcami.

---

## 1. Struktura widoku — punkt wejścia

Każdy widok w ERP posiada plik `filtr.sql` określający główny kontekst — tabelę źródłową i kotwicę łączącą widok z konkretnym obiektem w systemie.

```sql
-- Przykład: Towary według EAN
(Twr_GIDNumer=3282)

-- Przykład: Towary według grup
(TwG_GIDTyp=16 AND TwG_GIDNumer=3282 AND TwG_GrOTyp=-16 AND TwG_GrONumer=48)
```

`filtr.sql` definiuje główną tabelę i typ obiektu widoku. Agent musi go przeczytać przed generowaniem kodu dla danego widoku — wyznacza tabelę startową i dostępne kolumny bez dodatkowych JOIN-ów.

---

## 2. Kolumny

Kolumna to pełne zapytanie SELECT zwracające dodatkowe dane dla każdego wiersza widoku.

### Struktura obowiązkowa

```sql
SELECT
    kolumna [ALIAS WYSWIETLANY]
FROM cdn.TabelaGlowna
[LEFT JOIN ...]
WHERE
{filtrsql}
```

### Zasady

- Alias kolumny w nawiasach kwadratowych: `kolumna [MOJA NAZWA]`
- Placeholder `{filtrsql}` na końcu klauzuli WHERE — system wstrzykuje tu aktywne filtry widoku
- Pisownia `{filtrsql}` jest case-insensitive — dopuszczalne `{filtrsql}` i `{filtrSQL}`
- Tabela główna musi odpowiadać tabeli z `filtr.sql` widoku
- Preferowane LEFT JOIN dla atrybutów (rekord może nie mieć wartości)

### Przykład — pojedyncza kolumna

```sql
SELECT Twr_Ean [EAN]
FROM cdn.TwrKarty
JOIN cdn.TwrGrupy ON Twr_GIDNumer = TwG_GIDNumer AND Twr_GIDTyp = TwG_GIDTyp
WHERE {filtrSQL}
```

### Przykład — wiele kolumn z atrybutów (LEFT JOIN na tę samą tabelę)

```sql
SELECT
    k3.Atr_Wartosc [SEZON],
    k4.Atr_Wartosc [KOLOR]
FROM cdn.TwrKarty
LEFT JOIN cdn.Atrybuty k3 ON Twr_GIDNumer = k3.Atr_ObiNumer
    AND Twr_GIDTyp = k3.Atr_ObiTyp AND k3.Atr_AtKId = 3
LEFT JOIN cdn.Atrybuty k4 ON Twr_GIDNumer = k4.Atr_ObiNumer
    AND Twr_GIDTyp = k4.Atr_ObiTyp AND k4.Atr_AtKId = 4
WHERE {filtrsql}
```

---

## 3. Filtry

Filtr to wyłącznie warunek WHERE — bez SELECT, bez FROM. System ERP wstrzykuje go w odpowiednie miejsce zapytania widoku.

### Filtr prosty (bez parametrów)

```sql
Twr_Archiwalny = 1
```

```sql
Twr_Ean IN (
    SELECT Twr_Ean FROM cdn.TwrKarty
    WHERE Twr_Ean <> ''
    GROUP BY Twr_Ean
    HAVING COUNT(Twr_Ean) > 1
)
```

### Filtr z parametrami — składnia @PAR

Parametry deklarowane są przed warunkiem. Każdy parametr to jedna linia:

```
@PAR ?@TYP|NAZWA_ZMIENNEJ|&Etykieta dla użytkownika:REG=wartość_domyślna @? PAR@
```

Odwołanie do parametru w warunku: `??NAZWA_ZMIENNEJ`

---

## 4. Typy parametrów @PAR

### S — String (tekst)

```sql
@PAR ?@S100|Szukaj|&Szukaj:REG= @? PAR@

Twr_Kod LIKE '%' + ??Szukaj + '%'
OR Twr_Ean LIKE '%' + ??Szukaj + '%'
OR Twr_Nazwa LIKE '%' + ??Szukaj + '%'
```

Format: `S[max_dlugosc]` — np. `S20`, `S100`

### D — Data

```sql
@PAR ?@D17|DataOd|&DataOd:REG={DateClwFirstDay('m')} @? PAR@
@PAR ?@D17|DataDo|&DataDo:REG={DateClwLastDay('m')} @? PAR@

Twr_DataUtworzenia/86400+69035 > ??DataOd
AND Twr_DataUtworzenia/86400+69035 < ??DataDo
```

Format: `D[N]` — np. `D17`

Wartości domyślne dat: `{DateClwFirstDay('m')}` (pierwszy dzień miesiąca), `{DateClwLastDay('m')}` (ostatni dzień miesiąca)

### R — Lista rozwijana (dropdown)

**Z zapytaniem SQL (dynamiczna lista):**

```sql
@PAR ?@R(
    SELECT DISTINCT
        CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) + ' (' + Twr_GrupaPodSpr + ')' AS "KOD",
        Twr_StawkaPodSpr AS "ID"
    FROM cdn.TwrKarty
    ORDER BY 1
)|StawkaVat|&Stawka Vat:REG= @? PAR@

Twg_GIDNumer IN (
    SELECT Twr_GIDNumer FROM cdn.TwrKarty WHERE Twr_StawkaPodSpr = ??StawkaVat
)
```

Kolumny SELECT parametru R: `"KOD"` (wyświetlana użytkownikowi), `"ID"` (wartość przekazywana do warunku)

**Ze stałymi opcjami (UNION):**

```sql
@PAR ?@R(
    SELECT 'Tak' AS ID, 'Tak' AS Kod
    UNION ALL
    SELECT 'Nie' AS ID, 'Nie' AS Kod
)|UdostepnienieMS|&Udostępnione w mobilnej sprzedaży:REG=Tak @? PAR@

Twr_MobSpr = CASE WHEN ??UdostepnienieMS = 'Tak' THEN '1' ELSE '0' END
```

---

## 5. Konwersja dat

Daty w bazie ERP przechowywane są w formacie Clarion (liczba całkowita). Konwersja do daty SQL:

```sql
-- Wartość kolumny daty -> data porównywalna z parametrem D
kolumna_daty/86400+69035
```

Przykład:
```sql
Twr_DataUtworzenia/86400+69035 > ??DataOd
```

---

## 6. Wskazówki dla agenta

**Przed generowaniem kodu dla widoku:**
1. Przeczytaj `filtr.sql` widoku — wyznacza tabelę główną i typ obiektu
2. Sprawdź istniejące kolumny/filtry w tym samym widoku — naśladuj ich styl i JOINy
3. Użyj `search_docs.py` z nazwą tabeli z `filtr.sql` jako punktem startowym

**Generowanie kolumny:**
- Zawsze kończ `WHERE {filtrsql}`
- Alias kolumny w `[NAWIASACH KWADRATOWYCH]`
- LEFT JOIN dla kolumn opcjonalnych (atrybuty, powiązane tabele)

**Generowanie filtru:**
- Nie dodawaj SELECT ani FROM — tylko warunek WHERE
- Dla parametrów od użytkownika: zawsze używaj `@PAR`
- Dla dat: pamiętaj o konwersji `/86400+69035`
- Dla list: typ `R` z SELECT generującym kolumny `"KOD"` i `"ID"`

**Weryfikacja przed oddaniem:**
- Uruchom testowe zapytanie przez `sql_query.py` z `WHERE` zamiast `{filtrsql}` — sprawdź czy wynik jest sensowny
- Sprawdź czy kolumny w JOINach istnieją (`INFORMATION_SCHEMA`)
- Porównaj aliasy i nazwy kolumn z przykładowymi wartościami z `search_docs.py`

---

*Dokument przygotowany: 2026-02-27*
