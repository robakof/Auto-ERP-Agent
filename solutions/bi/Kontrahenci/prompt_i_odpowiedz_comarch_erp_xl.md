# Research: formaty dat w bazie Comarch ERP XL (Clarion)

## Prompt użytkownika

## Kontekst

Pracuję z bazą SQL Server systemu Comarch ERP XL (wersja polska, baza ERPXL_CEIM).
System ERP XL jest oparty na środowisku Clarion — przechowuje daty jako liczby całkowite
w co najmniej dwóch formatach:

**Potwierdzony FORMAT A — Clarion DATE:**
- Liczba dni od 1800-12-28
- Zakres dla dat bieżących: ~70 000–100 000
- Konwersja SQL: `DATEADD(d, col, '18001228')`
- Przykłady z bazy: 70316, 81239, 82156, 82184

**Potwierdzony FORMAT B — Clarion TIMESTAMP:**
- Liczba sekund od 1990-01-01
- Zakres: ~10^9
- Konwersja SQL: `DATEADD(ss, col, '1990-01-01')`
- Przykłady z bazy: 1047823554, 1141724389

## Problem

W tabeli `CDN.KntKarty` pole `Knt_EFaVatDataDo` (Data ważności dla elektronicznego
przesyłania faktur VAT) ma wartości w zakresie **81169–150483**.

- Wartość 81169 → Format A → `1800-12-28 + 81169 dni` = ok. 2022-05-xx ✓ (sensowna)
- Wartość **150483** → Format A → `1800-12-28 + 150483 dni` = ok. **rok 2213** ✗ (podejrzane)

Pytania do wyjaśnienia:

1. **Czy w Comarch ERP XL / Clarion istnieje konwencja sentinel value** dla "data bez ograniczenia"
   (bezterminowo)? Jeśli tak — jaka to wartość i jak ją interpretować w SQL?

2. **Czy istnieje trzeci format daty** używany przez Comarch ERP XL — inne niż Clarion DATE
   i Clarion TIMESTAMP? Np. format oparty na innej epoce lub innej jednostce?

3. **Jak w dokumentacji Comarch ERP XL opisany jest format pola datowego** dla tabel takich
   jak KntKarty, ZamNag, TraNag — czy wszystkie pola INT/SMALLINT zawierające daty
   używają tych samych dwóch formatów?

4. **Czy wartość 150483 w kontekście daty ważności e-Faktury VAT** ma znane znaczenie?
   (Np. czy jest to standardowy sentinel w implementacji Comarch dla "ważne bezterminowo"?)

## Czego szukać

- Dokumentacja Clarion (TopSpeed/SoftVelocity): formaty przechowywania dat, sentinel values
- Forum Comarch: wątki o konwersji dat z bazy ERP XL do SQL
- Baza wiedzy Comarch / dokumentacja techniczna CDN.KntKarty lub podobnych tabel
- Artykuły o integracji Comarch ERP XL z SQL Server / Power BI / raportami

## Oczekiwany wynik

Odpowiedź powinna zawierać:
1. Wzorzec SQL do konwersji dla każdego zidentyfikowanego formatu
2. Sposób obsługi sentinel value (jeśli istnieje) — np. `CASE WHEN col > 130000 THEN NULL ELSE DATEADD(...)`
3. Źródło (link lub nazwa dokumentu)

Jeśli nie znajdziesz pewnej odpowiedzi — podaj najlepszą hipotezę z uzasadnieniem,
żebym mógł ją zweryfikować przez SELECT na realnych danych.

---

## Odpowiedź

Najbardziej prawdopodobny obraz jest taki:

`Knt_EFaVatDataDo` wygląda na **zwykły Clarion DATE w kolumnie INT**, ale z **aplikacyjnym sentinelem Comarcha** dla „bezterminowo”, a `150483` jest bardzo mocnym kandydatem na właśnie taki sentinel. Nie znalazłem publicznej dokumentacji Comarch, która mówi to wprost dla tego konkretnego pola, więc tę część traktowałbym jako **najlepszą hipotezę roboczą**, nie jako potwierdzony fakt. Fakty, które ją wspierają, są jednak dość mocne: Clarionowy „standard date” to liczba dni od `1800-12-28`, natomiast dokumentacja Clariona podaje standardowy zakres lat mniej więcej `1801..2099`; wartość `150483` daje `2212-12-31`, więc wychodzi **poza standardowy zakres Clariona** i słabo pasuje do realnej daty biznesowej. Jednocześnie dokumentacja Comarch dla tej funkcji mówi tylko, że przy wysyłce sprawdzany jest warunek „data wysyłki > termin ważności”, bez opisu osobnego trybu „bezterminowo”, co dobrze pasuje do implementacji przez specjalną dużą wartość. ([clarion.help](https://clarion.help/doku.php?id=date_pictures.htm))

## 1) Wzorce SQL

**Format A — Clarion DATE**  
To jest potwierdzone: liczba dni od `1800-12-28`. Clarion opisuje „standard date” właśnie tak, a w materiałach ERP XL `TrN_Data2` jest konwertowane przez `DATEADD(day, ..., '18001228')`. ([clarion.help](https://clarion.help/doku.php?id=date_pictures.htm))

```sql
DATEADD(day, col, CONVERT(date, '18001228'))
```

Bezpieczniejsza wersja do raportów:

```sql
CASE
    WHEN col IS NULL OR col = 0 THEN NULL
    WHEN col BETWEEN 1 AND 109211 THEN DATEADD(day, col, CONVERT(date, '18001228')) -- do 2099-12-31
    ELSE NULL
END
```

Ta wersja jest zgodna z dokumentowanym „cleared date = 0” po stronie Clariona i odcina wartości wykraczające poza standardowy zakres dat Clariona. ([clarion.help](https://clarion.help/doku.php?id=zerodate.htm))

**Format B — ERP XL „timestamp” (sekundy od 1990-01-01)**  
W społeczności ERP XL i w materiałach o pracy z bazą XL to jest opisywane jako liczba sekund od `1990-01-01`; Comarch dodał też funkcję `CDN.DateToTS`, która właśnie taką konwersję robi. To wygląda na **konwencję ERP XL/Comarch**, a nie na natywny „standard time” Clariona. ([cdn.3lance.pl](https://cdn.3lance.pl/viewtopic.php?t=1778&utm_source=chatgpt.com))

```sql
DATEADD(second, col, CONVERT(datetime, '19900101'))
```

Ostrożna wersja:

```sql
CASE
    WHEN col IS NULL THEN NULL
    ELSE DATEADD(second, col, CONVERT(datetime, '19900101'))
END
```

Tu nie wprowadzałbym automatycznie `col = 0 => NULL`, bo dla tego formatu `0` arytmetycznie oznacza po prostu `1990-01-01 00:00:00`, a nie znalazłem dokumentu Comarcha mówiącego, że w każdej kolumnie XL taki `0` ma znaczyć „pusto”. ([swiatxl.pl](https://www.swiatxl.pl/sxj045-najczesciej-uzywane-funkcje-sql-w-xl-u-narzedzie-erp-xl?utm_source=chatgpt.com))

**„Trzeci format” w ERP XL**  
Znalazłem **trzeci sposób reprezentacji daty w ERP XL**, ale nie jako trzeci pojedynczy epoch-int. Chodzi o datę rozbitą na osobne pola `rok/miesiąc/dzień`, składane funkcją `CDN.YMD(rok, miesiac, dzien)`. Materiały o ERP XL wskazują, że tak bywa m.in. w księgowości i rejestrach VAT. Dodatkowo w dokumentacji migratora Comarch są też pola opisane literalnie jako integer w formacie `RRRR MM DD`, ale to dotyczy struktur importowo-migracyjnych, nie dowodzi istnienia trzeciej ogólnej konwencji w głównych tabelach typu `KntKarty`/`TraNag`/`ZamNag`. ([swiatxl.pl](https://www.swiatxl.pl/sxj045-najczesciej-uzywane-funkcje-sql-w-xl-u-narzedzie-erp-xl?utm_source=chatgpt.com))

```sql
CDN.YMD(Rok, Miesiac, Dzien)
```

## 2) Sentinel value w Clarion / SQL

W dokumentacji Clariona jest dość jasny trop: dla SQL driverów `ZEROISNULL=TRUE` jest domyślne, a opis mówi wprost, że **DATE/TIME o wartości 0** są domyślnie traktowane jako `NULL` w backendzie. Nowszy opis `ZERODATE` mówi o „cleared DATE and TIME fields”, a dla MSSQL podaje nawet, że **cleared Date** będzie zawsze zapisywany jako `NULL`. To jest bardzo mocny dowód, że **ogólny Clarionowy sentinel pustej daty to `0`**. ([clarion.help](https://clarion.help/doku.php?id=zerodate.htm))

Ale ważny niuans: to dotyczy **prawdziwych pól DATE/TIME widzianych przez driver Clariona**. W ERP XL wiele dat siedzi w **surowych INT-ach**, więc ta zamiana na `NULL` nie musi działać automatycznie. W takich kolumnach aplikacja może używać własnych sentinelów. ([clarion.help](https://clarion.help/doku.php?id=zerodate.htm))

Dlatego dla ERP XL proponowałbym dwa poziomy obsługi:

**Ogólna reguła Clarion DATE w INT:**
```sql
CASE
    WHEN col IS NULL OR col = 0 THEN NULL
    ELSE DATEADD(day, col, '18001228')
END
```

**Reguła praktyczna dla `Knt_EFaVatDataDo`:**
```sql
CASE
    WHEN Knt_EFaVatDataDo IS NULL OR Knt_EFaVatDataDo = 0 THEN NULL
    WHEN Knt_EFaVatDataDo = 150483 THEN NULL  -- hipoteza: "bezterminowo"
    WHEN Knt_EFaVatDataDo BETWEEN 1 AND 109211 THEN DATEADD(day, Knt_EFaVatDataDo, '18001228')
    ELSE NULL
END
```

Ta druga reguła nie jest „oficjalną dokumentacją”, tylko roboczym modelem opartym na tym, że `150483` wypada poza standardowy zakres Clariona, a biznesowo pole oznacza termin ważności zgody na e‑fakturę. ([pomoc.comarch.pl](https://pomoc.comarch.pl/xl/index.php/dokumentacja/kontrahenci/))

## 3) Odpowiedzi na Twoje pytania

**1. Czy istnieje konwencja sentinel value dla „bez ograniczenia” / pustej daty?**  
Dla samego Clariona: **tak, najbardziej udokumentowanym sentinelem pustej daty jest `0`**. Potwierdzają to opisy `ZEROISNULL` i `ZERODATE` dla cleared DATE/TIME fields. Dla **konkretnego pola ERP XL `Knt_EFaVatDataDo`** nie znalazłem publicznego dokumentu Comarcha mówiącego wprost „150483 = bezterminowo”, ale to jest obecnie moja **najmocniejsza hipoteza**. ([clarion.help](https://clarion.help/doku.php?id=zerodate.htm))

**2. Czy istnieje trzeci format daty w ERP XL?**  
Jeśli pytasz o **trzeci pojedynczy liczbowy epoch-format** podobny do `18001228` i `19900101`, to **nie znalazłem wiarygodnego potwierdzenia** dla głównych tabel XL. Znalazłem natomiast trzeci sposób reprezentacji daty w ERP XL: **osobne pola rok/miesiąc/dzień** składane przez `CDN.YMD(...)`. Znalazłem też przykłady struktur migracyjnych z integerem w formacie `RRRRMMDD`, ale to już nie jest ogólna konwencja fizycznego zapisu w głównych tabelach operacyjnych. ([swiatxl.pl](https://www.swiatxl.pl/sxj045-najczesciej-uzywane-funkcje-sql-w-xl-u-narzedzie-erp-xl?utm_source=chatgpt.com))

**3. Czy wszystkie pola INT/SMALLINT z datami używają tych samych dwóch formatów?**  
**Nie wygląda na to.** W ERP XL spotkasz co najmniej:
- Clarion DATE w liczbie dni od `1800-12-28`,
- XL-owy timestamp w sekundach od `1990-01-01`,
- daty rozbite na `rok/miesiąc/dzień` składane funkcją `CDN.YMD(...)`.  
Dla `TraNag` masz publiczne przykłady `TrN_Data2` jako Clarion DATE, ale nie znalazłem jednej oficjalnej publicznej „mapy wszystkich pól datowych” dla `KntKarty`, `ZamNag`, `TraNag`, która gwarantowałaby pełną jednolitość wszystkich `INT/SMALLINT`. ([cdn.3lance.pl](https://cdn.3lance.pl/viewtopic.php?t=1778&utm_source=chatgpt.com))

**4. Czy `150483` ma znane znaczenie dla ważności e‑Faktury VAT?**  
Nie znalazłem publicznego źródła, które to jednoznacznie dokumentuje. Najlepsza hipoteza jest taka, że to **Comarchowy sentinel „bezterminowo”** dla `Knt_EFaVatDataDo`. Uzasadnienie:
- pole dotyczy terminu ważności zgody na e‑fakturę i system porównuje tylko „czy data wysyłki przekroczyła termin”; ([pomoc.comarch.pl](https://pomoc.comarch.pl/xl/index.php/dokumentacja/kontrahenci/))
- `150483` jako Clarion DATE daje `2212-12-31`, czyli datę nierealną biznesowo;
- `2212-12-31` leży poza standardowym zakresem dat Clariona dokumentowanym w helpie. ([clarion.help](https://clarion.help/doku.php?id=accessing_clarion_s_runtime_library_from_c_c_or_modula_2_code.htm&utm_source=chatgpt.com))

## 4) Co bym sprawdził SELECT-em

Najprostszy test:

```sql
SELECT
    Knt_EFaVatDataDo,
    COUNT(*) AS Cnt,
    MIN(DATEADD(day, Knt_EFaVatDataDo, '18001228')) AS AsDateMin,
    MAX(DATEADD(day, Knt_EFaVatDataDo, '18001228')) AS AsDateMax
FROM CDN.KntKarty
WHERE Knt_EFaVatDataDo IS NOT NULL
GROUP BY Knt_EFaVatDataDo
ORDER BY Knt_EFaVatDataDo;
```

Jeśli `150483` występuje masowo, a zwykłe wartości są w pobliżu bieżących lat, to bardzo wzmacnia hipotezę sentinela.

Drugi test: rozdzielenie „sensownych” i „podejrzanych”:

```sql
SELECT
    SUM(CASE WHEN Knt_EFaVatDataDo BETWEEN 1 AND 109211 THEN 1 ELSE 0 END) AS InClarionRange,
    SUM(CASE WHEN Knt_EFaVatDataDo > 109211 THEN 1 ELSE 0 END) AS AboveClarionRange,
    SUM(CASE WHEN Knt_EFaVatDataDo = 150483 THEN 1 ELSE 0 END) AS Exact150483
FROM CDN.KntKarty;
```

Trzeci test: czy `150483` koreluje z włączoną zgodą i adresem e‑mail, czyli z logicznym „bezterminowo”:

```sql
SELECT TOP (200)
    Knt_Akronim,
    Knt_EFaVatDataDo,
    CASE
        WHEN Knt_EFaVatDataDo = 150483 THEN 'SUSPECT_SENTINEL'
        WHEN Knt_EFaVatDataDo BETWEEN 1 AND 109211 THEN CONVERT(varchar(10), DATEADD(day, Knt_EFaVatDataDo, '18001228'), 120)
        ELSE 'OTHER'
    END AS InterpretedDate
FROM CDN.KntKarty
WHERE Knt_EFaVatDataDo IS NOT NULL
ORDER BY Knt_EFaVatDataDo DESC;
```

## 5) Moja praktyczna rekomendacja

Dla raportów/ETL zrobiłbym to tak:

```sql
CASE
    WHEN col IS NULL OR col = 0 THEN NULL
    WHEN col = 150483 THEN NULL   -- tylko dla Knt_EFaVatDataDo, jako hipoteza biznesowa
    WHEN col BETWEEN 1 AND 109211 THEN DATEADD(day, col, '18001228')
    ELSE NULL
END
```

I obok dodałbym kolumnę diagnostyczną:

```sql
CASE
    WHEN col IS NULL OR col = 0 THEN 'EMPTY'
    WHEN col = 150483 THEN 'SENTINEL_150483?'
    WHEN col BETWEEN 1 AND 109211 THEN 'CLARION_DATE'
    ELSE 'OUT_OF_RANGE'
END
```

Źródła, na których bym się opierał przy dalszej weryfikacji, to:
- **Clarion Community Help**: `Date Pictures`, `DATE (return standard date)`, `ZERODATE`, `ZEROISNULL`, `Standard Time`. ([clarion.help](https://clarion.help/doku.php?id=date_pictures.htm))
- **Comarch ERP XL – Kontrahenci**: opis pola „Faktura VAT przesyłane elektronicznie” i komunikatu o przekroczonej dacie ważności. ([pomoc.comarch.pl](https://pomoc.comarch.pl/xl/index.php/dokumentacja/kontrahenci/))
- **Materiały społeczności ERP XL / praktyka SQL dla XL**: przykłady `TrN_Data2`, `Twr_LastModL`, `CDN.DateToTS`, `CDN.YMD`. ([cdn.3lance.pl](https://cdn.3lance.pl/viewtopic.php?t=1778&utm_source=chatgpt.com))

Jeżeli chcesz, mogę z tego od razu złożyć gotowy `SELECT` pod `CDN.KntKarty`, który zwróci jednocześnie surową wartość, zinterpretowaną datę i flagę jakości danych.
