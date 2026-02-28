# ERP SQL Syntax — Wytyczne dla agenta

Dokument opisuje składnię SQL akceptowaną przez system ERP przy konfiguracji kolumn i filtrów.
Agent musi generować kod ściśle zgodny z poniższymi wzorcami.

Jeśli w trakcie pracy odkryjesz nowe wzorce lub nieoczywiste zachowania — dopisz je tutaj
natychmiast, nie czekając na koniec sesji.

---

## 1. Struktura widoku — punkt wejścia

Każdy widok w ERP posiada plik `filtr.sql` określający główny kontekst — tabelę źródłową
i kotwicę łączącą widok z konkretnym obiektem w systemie.

```sql
-- Przykład: Towary według EAN
(Twr_GIDNumer=3282)

-- Przykład: Towary według grup
(TwG_GIDTyp=16 AND TwG_GIDNumer=3282 AND TwG_GrOTyp=-16 AND TwG_GrONumer=48)
```

`filtr.sql` definiuje główną tabelę i typ obiektu widoku. Agent musi go przeczytać przed
generowaniem kodu dla danego widoku — wyznacza tabelę startową i dostępne kolumny bez
dodatkowych JOIN-ów.

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

Filtr to wyłącznie warunek WHERE — bez SELECT, bez FROM. System ERP wstrzykuje go
w odpowiednie miejsce zapytania widoku.

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

### Limit znaków

ERP UI narzuca limit znaków na filtr SQL. Zweryfikowane empirycznie:
- **2043 znaków** — działa
- **2090 znaków** — nie zapisuje się
- Bezpieczny cel: **≤ 2000 znaków**
- Kolumna w bazie `CDN.Filtry.FIL_FiltrSQL` to varchar(4096) — NIE jest granicą,
  limit narzuca aplikacja kliencka (nie baza danych)

### Filtr z parametrami — składnia @PAR

Parametry deklarowane są przed warunkiem. Każdy parametr to jedna linia:

```
@PAR ?@TYP|NAZWA_ZMIENNEJ|&Etykieta dla użytkownika:REG=wartość_domyślna @? PAR@
```

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

Referencja w WHERE: `??NazwaParam` — ERP automatycznie otacza wartość cudzysłowami.

### D — Data

```sql
@PAR ?@D17|DataOd|&DataOd:REG=0 @? PAR@
@PAR ?@D17|DataDo|&DataDo:REG=0 @? PAR@

(??DataOd=0 OR Twr_DataUtworzenia/86400+69035>=??DataOd)
AND (??DataDo=0 OR Twr_DataUtworzenia/86400+69035<=??DataDo)
```

Format: `D[N]` — np. `D17`

Referencja w WHERE: `??NazwaParam` — ERP podstawia wartość numeryczną (Clarion date).
Domyślna wartość `REG=0` oznacza "pomiń filtr" gdy warunek to `??Param=0`.
Alternatywne wartości domyślne dat: `{DateClwFirstDay('m')}`, `{DateClwLastDay('m')}`.

### R — Lista rozwijana (dropdown)

#### Referencja w WHERE — krytyczna zasada `??_Q`

| Typ ID w dropdownie | Referencja w WHERE | Przykład |
|---|---|---|
| **varchar** (string) | `??_QNazwaParam` | `??_QStatus` |
| **numeric** (liczba) | `??NazwaParam` | `??Magazyn` |

Prefiks `_Q` instruuje ERP żeby otoczyć podstawianą wartość cudzysłowami (`'wartość'`).
Bez `_Q` ERP podstawia wartość dosłownie — dla stringów powoduje błąd składni SQL.

Typ `@S` zawsze używa `??NazwaParam` (ERP sam dodaje cudzysłowy dla stringów).

#### Stałe opcje (UNION)

```sql
@PAR ?@R(
    SELECT 'Tak' AS ID, 'Tak' AS Kod
    UNION ALL
    SELECT 'Nie' AS ID, 'Nie' AS Kod
)|UdostepnienieMS|&Udostępnione w mobilnej sprzedaży:REG=Tak @? PAR@

Twr_MobSpr = CASE WHEN ??_QUdostepnienieMS = 'Tak' THEN '1' ELSE '0' END
```

ID to varchar → używamy `??_Q`.

#### Dynamiczna lista z bazy danych

```sql
@PAR ?@R(
    SELECT DISTINCT
        CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) + ' (' + Twr_GrupaPodSpr + ')' AS "KOD",
        Twr_StawkaPodSpr AS "ID"
    FROM cdn.TwrKarty
    ORDER BY 1
)|StawkaVat|&Stawka Vat:REG= @? PAR@

Twr_StawkaPodSpr = ??StawkaVat
```

ID to numeric → używamy `??NazwaParam` (bez `_Q`).

#### Opcjonalny parametr (możliwość pominięcia)

Aby parametr był opcjonalny (puste = pokaż wszystko), dodaj pusty wiersz do dropdownu
i owiń warunek OR:

```sql
@PAR ?@R(
    SELECT '' AS ID, '(wszystkie)' AS KOD
    UNION ALL
    SELECT 'brak', 'Brak stanu'
    UNION ALL
    SELECT 'ma', 'Z dowolnym stanem'
)|StanMag|&Stan magazynowy:REG= @? PAR@

(??_QStanMag='' OR (??_QStanMag='brak' AND NOT EXISTS(...)) OR (??_QStanMag='ma' AND EXISTS(...)))
```

Dla dat opcjonalnych: `REG=0` + warunek `(??DataOd=0 OR ...)`.

#### Bezpieczeństwo typów w UNION

Gdy używasz UNION z pustym wierszem (`'' AS ID`), wszystkie kolejne wiersze muszą mieć
ID tego samego typu (varchar). Jeśli ID pochodzi z kolumny numerycznej — rzutuj ją:

```sql
-- Zamiast Twr_StawkaPodSpr AS ID (numeric — powoduje błąd konwersji):
CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) AS ID
```

Warunek WHERE dostosuj analogicznie:
```sql
CAST(CAST(Twr_StawkaPodSpr AS INT) AS VARCHAR(2)) = ??_QStawkaVat
```

---

## 5. Konwersja dat

Daty w bazie ERP przechowywane są w formacie Clarion (liczba całkowita). Konwersja:

```sql
kolumna_daty/86400+69035
```

Przykład:
```sql
Twr_DataUtworzenia/86400+69035 >= ??DataOd
```

---

## 6. Tabele pomocnicze — nieoczywiste struktury

### Załączniki (CDN.DaneBinarne + CDN.DaneObiekty)

Załączniki w ERP przechowywane są w dwóch tabelach:

- `CDN.DaneBinarne` — dane pliku (`DAB_ID`, `DAB_Rozszerzenie` — rozszerzenie bez kropki)
- `CDN.DaneObiekty` — powiązanie pliku z obiektem ERP (`DAO_DABId`, `DAO_ObiNumer`, `DAO_ObiTyp`)

Wzorzec filtra "brak załącznika .jpg":

```sql
NOT EXISTS (
    SELECT 1
    FROM CDN.DaneObiekty dao
    JOIN CDN.DaneBinarne dab ON dao.DAO_DABId = dab.DAB_ID
    WHERE dao.DAO_ObiNumer = Twr_GIDNumer
      AND dao.DAO_ObiTyp = Twr_GIDTyp
      AND LOWER(dab.DAB_Rozszerzenie) = 'jpg'
)
```

### Stan magazynowy (CDN.TwrZasoby)

Tabela `CDN.TwrZasoby` zawiera dwie kolumny ilości — różnią się semantycznie:

| Kolumna | Znaczenie | Kiedy używać |
|---|---|---|
| `TwZ_Ilosc` | Ilość dostępna (widoczna w ERP jako "stan") | Filtr "brak stanu mag." |
| `TwZ_IlMag` | Ilość fizyczna w magazynie | Porównanie handlowe/magazynowe |

Filtr "brak stanu na wszystkich magazynach" — użyj `TwZ_Ilosc`:

```sql
NOT EXISTS (
    SELECT 1 FROM CDN.TwrZasoby
    WHERE TwZ_TwrNumer = Twr_GIDNumer
      AND TwZ_Ilosc > 0
)
```

### Atrybuty obiektów (CDN.Atrybuty)

```sql
EXISTS (
    SELECT 1 FROM CDN.Atrybuty
    WHERE Atr_ObiNumer = Twr_GIDNumer
      AND Atr_ObiTyp = Twr_GIDTyp
      AND Atr_AtkId = 59          -- ID atrybutu (sprawdź w CDN.AtrybutyKlasy)
      AND Atr_Wartosc = 'Wartość'
)
```

Identyfikatory atrybutów dla okna Towary:
- `Atr_AtkId = 3` — Sezon
- `Atr_AtkId = 59` — Status ofertowy produktu

---

## 7. Wskazówki dla agenta

**Przed generowaniem kodu dla widoku:**
1. Przeczytaj `filtr.sql` widoku — wyznacza tabelę główną i typ obiektu
2. Sprawdź istniejące kolumny/filtry w tym samym widoku — naśladuj ich styl i JOINy
3. Użyj `search_docs.py` z nazwą tabeli z `filtr.sql` jako punktem startowym

**Generowanie kolumny:**
- Zawsze kończ `WHERE {filtrsql}`
- Alias kolumny w `[NAWIASACH KWADRATOWYCH]`
- LEFT JOIN dla kolumn opcjonalnych (atrybuty, powiązane tabele)

**Generowanie filtru z @PAR:**
- Nie dodawaj SELECT ani FROM — tylko warunek WHERE
- `@R` z varchar ID → `??_QNazwa` w WHERE
- `@R` z numeric ID → `??Nazwa` w WHERE
- `@S` → `??Nazwa` w WHERE
- `@D` → `??Nazwa` w WHERE, `REG=0` + warunek `??=0` dla parametrów opcjonalnych
- Dla dat: konwersja `/86400+69035`
- Limit: ≤ 2000 znaków całego filtra

**Weryfikacja przed oddaniem:**
- Uruchom testowe zapytanie przez `sql_query.py` — sprawdź czy wynik jest sensowny
- Sprawdź czy kolumny w JOINach istnieją (`INFORMATION_SCHEMA`)
- Przy filtrach z @PAR: przetestuj logikę warunku z podstawionymi wartościami testowymi

---

*Dokument aktualizowany na bieżąco w trakcie pracy z systemem.*
