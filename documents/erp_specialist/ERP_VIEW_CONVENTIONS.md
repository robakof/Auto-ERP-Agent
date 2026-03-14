# Konwencje widoków BI — karta referencyjna

Dokument uzupełniający do ERP_VIEW_WORKFLOW.md.
Zawiera skondensowane reguły do szybkiej weryfikacji gotowego widoku.
Nie zastępuje workflow — jest jego checklistą operacyjną.

Przed każdym widokiem idącym do DBA: przejdź przez ten dokument od góry do dołu.

---

## Schemat i nazewnictwo

- Schemat: `AIBI` (nie BI, nie CDN)
- Plik views/: zawsze zaczyna się od `USE [ERPXL_CEIM]; GO` — plik musi być self-contained
- Format pliku views/:
  ```sql
  USE [ERPXL_CEIM];
  GO
  CREATE OR ALTER VIEW AIBI.NazwaWidoku AS
  ...
  ```
- Brudnopis: sam SELECT, bez CREATE i bez USE/GO — testowany przez sql_query.py
- Nazwy kolumn: PascalCase z underscore, polskie, opisowe (`Data_Wystawienia`, `Kod_Towaru`)
- Klucz główny widoku: `ID_[encja]` (`ID_Rezerwacji`, `ID_Zamowienia`)
- Para lookup: zawsze `Kod_X` + `Nazwa_X`

---

## Dane wrażliwe — NIGDY w widoku AIBI

Poniższe kategorie danych nie mogą trafić do żadnego widoku AIBI:

| Kategoria | Przykłady kolumn CDN |
|---|---|
| Numery PESEL | kolumny zawierające PESEL w nazwie lub opisie |
| Numery rachunków bankowych | Knt_Nrb*, Bnk_Nrb*, numery IBAN |
| Numery dokumentów tożsamości | dowód osobisty, paszport, prawo jazdy |

NIP, REGON, GLN — **dopuszczalne** (dane operacyjne firmy, nie osobowe).
Telefon, email — **dopuszczalne** (dane kontaktowe biznesowe).

W razie wątpliwości: pomiń i odnotuj w progress logu z pytaniem do Dawida.

---

## Komponenty GID

| Komponent | Reguła |
|---|---|
| `GIDFirma` | Pomijamy zawsze |
| `GIDTyp` | Tłumaczymy przez CASE gdy rozróżnia typy (np. ZaN_ZamTyp). Pomijamy gdy stały dla całej tabeli. |
| `GIDNumer` | Zachowujemy jako `ID_[encja]` |
| `GIDLp` | Pomijamy. Wyjątek: CDN.Rozrachunki — używamy wyłącznie w WHERE (= 1), nie w SELECT. |

---

## Tłumaczenia wartości

### Flagi 0/1
```sql
CASE pole WHEN 1 THEN 'Tak' WHEN 0 THEN 'Nie'
ELSE 'Nieznane (' + CAST(pole AS VARCHAR) + ')' END
```
Dobieraj etykiety kontekstowo: 'Aktywna'/'Nieaktywna', 'Zatwierdzone'/'Niezatwierdzone' itp.

### Enumeracje i typy dokumentów
```sql
CASE pole
    WHEN 960  THEN 'Zamówienie'
    WHEN 1280 THEN 'Zamówienie sprzedaży'
    -- wartości z dokumentacji, nawet jeśli nie ma ich w bazie:
    WHEN 2592 THEN 'Rezerwacja u dostawcy'
    ELSE 'Nieznane (' + CAST(pole AS VARCHAR) + ')'  -- OBOWIĄZKOWY
END
```
ELSE z surową wartością jest **obowiązkowy**. Nigdy samo ELSE NULL.

### Typy dokumentów: pełne nazwy PL
'Faktura sprzedaży' — nie 'FS'. 'Zamówienie sprzedaży' — nie 'ZS'.
Wyjątek: skróty jako część składowa numeru dokumentu (Nr_Dok) — dopuszczalne.

### Klucze obce
Dla każdego ID klucza obcego:
1. Dodaj JOIN do docelowej tabeli
2. Sprowadź przynajmniej kod + nazwa
3. Zachowaj ID (dla debugowania i przyszłych JOINów)

Gdy tabela referencyjna nie jest oczywista — nie kończ na jednej próbie.
Obowiązkowe kroki eskalacji:
1. `docs_search` po nazwie kolumny
2. `INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME LIKE '%prefiks%'`
3. `CDN.Obiekty` po zakresie wartości klucza
4. Szukaj tabeli po prefiksie kolumny (np. `POK_Id` → tabela z kolumnami `POK_*`)

JOIN 100% dopasowań to dowód że tabela istnieje — nie deklaruj "brak tabeli" bez przejścia przez wszystkie kroki.

### Grupy hierarchiczne

Gdy FK wskazuje na tabelę z hierarchią grup (np. `CDN.TwrGrupyDom`):
- Nie eksponuj płaskiego kodu — buduj pełną ścieżkę rekurencyjną przez CTE
- Format ścieżki: `Poziom1\Poziom2\Poziom3` (separator `\`)
- Kolumny w widoku: `ID_Grupy` + `Sciezka_Grupy`

```sql
WITH Sciezka_Grup AS (
    SELECT TGD_GIDNumer, TGD_GrONumer,
           CAST(TGD_Kod AS NVARCHAR(500)) AS Sciezka
    FROM CDN.TwrGrupyDom
    WHERE TGD_GIDTyp = -16 AND TGD_GrONumer = 0  -- root
    UNION ALL
    SELECT d.TGD_GIDNumer, d.TGD_GrONumer,
           CAST(sg.Sciezka + '\' + d.TGD_Kod AS NVARCHAR(500))
    FROM CDN.TwrGrupyDom d
    JOIN Sciezka_Grup sg ON sg.TGD_GIDNumer = d.TGD_GrONumer
    WHERE d.TGD_GIDTyp = -16
)
```

Wzorzec stosuj wszędzie gdzie tabela grup ma kolumnę klucza rodzica (np. `TGD_GrONumer`, `KGR_GrNumer`).

### Pole numeryczne = brak
```sql
CASE WHEN col = 0 THEN NULL ELSE col END AS ID_X
-- lub warunek > 0 w JOIN (NULL propaguje przez LEFT JOIN)
```

---

## Daty

### Clarion DATE (~70 000–109 211)
```sql
-- Standardowy (gdy brak sentineli):
CASE WHEN col = 0 THEN NULL
     ELSE CAST(DATEADD(d, col, '18001228') AS DATE) END

-- Defensywny (gdy możliwe wartości >109211 jako sentinel "bezterminowo"):
CASE WHEN col BETWEEN 1 AND 109211
     THEN CAST(DATEADD(d, col, '18001228') AS DATE)
     ELSE NULL END
```

### Clarion TIMESTAMP (~10^9)
```sql
CASE WHEN col = 0 THEN NULL
     ELSE CAST(DATEADD(ss, col, '1990-01-01') AS DATETIME) END
```

### Jak rozróżnić
`SELECT MIN(col), MAX(col) FROM CDN.Tabela WHERE col > 0`
- 70 000–109 211 → Clarion DATE
- ~10^9 → Clarion TIMESTAMP
- format daty → SQL DATE (bez konwersji)

---

## Numery dokumentów

Buduj inline — bez `CDN.NazwaObiektu` i `CDN.NumerDokumentu` (brak EXECUTE dla CEiM_BI).

Format roku (YY vs YYYY) weryfikuj przez NazwaObiektu **przed** wdrożeniem — nie zakładaj.

### TraNag — prefiks dokumentu (obowiązkowa kolejność CASE)
```sql
CASE
    WHEN n.TrN_GIDTyp IN (2041, 2045, 1529)
         AND EXISTS (
             SELECT 1 FROM CDN.TraNag s
             WHERE s.TrN_SpiTyp   = n.TrN_GIDTyp
               AND s.TrN_SpiNumer = n.TrN_GIDNumer
               AND (
                    (n.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009) OR
                    (n.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013) OR
                    (n.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497)
               )
         )                                              THEN '(Z)'
    WHEN n.TrN_Stan & 2 = 2
         AND n.TrN_GIDTyp IN (2041, 2045, 1529)        THEN '(Z)'  -- fallback
    WHEN n.TrN_GenDokMag = -1
         AND n.TrN_GIDTyp IN (1521, 1529, 1489)        THEN '(A)'
    WHEN n.TrN_GenDokMag = -1                          THEN '(s)'
    ELSE ''
END + RTRIM(n.TrN_Seria) + '/' + CAST(n.TrN_NumerTrN AS VARCHAR(10))
    + '/' + RIGHT(CAST(n.TrN_Rok AS VARCHAR(4)), 2)
```

`TrN_TypNumeracji` nie istnieje — używaj `TrN_GIDTyp IN (lista numeryczna)`.

---

## JOIN kontrahenta

```sql
-- Zawsze dwuczęściowy klucz gdy tabela źródłowa ma osobny GIDTyp:
LEFT JOIN CDN.KntKarty k ON k.Knt_GIDNumer = r.Rez_KntNumer
                         AND k.Knt_GIDTyp   = r.Rez_KntTyp
                         AND r.Rez_KntNumer > 0

-- Self-join KntKarty (akwizytor, płatnik) — GIDTyp stały, wystarczy jeden klucz:
LEFT JOIN CDN.KntKarty akw ON akw.Knt_GIDNumer = k.Knt_AkwNumer
                           AND k.Knt_AkwNumer > 0
```

---

## WHERE

Widoki BI zwracają pełne zbiory. WHERE tylko dla filtrów technicznych:

```sql
-- Poprawnie (wykluczenie rekordów bez klucza):
WHERE r.Rez_TwrNumer > 0
WHERE r.ROZ_GIDLp = 1   -- CDN.Rozrachunki: zawsze!

-- Błędnie (logika biznesowa):
WHERE r.Rez_Aktywna = 1
WHERE ZaN_Stan != 19
```

---

## Pominięcie pola

Pole można pominąć WYŁĄCZNIE gdy spełniony jeden z warunków:

1. `COUNT(DISTINCT col) = 1` dla całej tabeli — udowodnione zapytaniem
2. Dokumentacja wprost: "pole nie jest obsługiwane" / "nieużywane"
3. Dane wrażliwe (patrz sekcja wyżej)
4. Czyste komponenty GID: GIDFirma, GIDLp

Rzadko wypełnione, mała wartość analityczna, nieznane zastosowanie — **NIE są powodem** do pominięcia.

---

## Przed oddaniem do Analityka

- [ ] Dane wrażliwe: żadna kolumna z listy wrażliwych nie jest w SELECT
- [ ] GID: Firma pominięta, Lp pominięty, Numer zachowany, Typ przetłumaczony lub pominięty (gdy stały)
- [ ] Flagi: wszystkie 0/1 mają CASE z etykietami
- [ ] Enumeracje: wszystkie CASE mają ELSE z surową wartością
- [ ] Daty: konwersja Clarion zastosowana, 0 → NULL, sentinel → NULL
- [ ] Numery dokumentów: prefiks TraNag w prawidłowej kolejności (EXISTS → Stan&2 → GenDokMag)
- [ ] JOINy: COUNT(*) = COUNT(DISTINCT klucz) przed i po każdym JOIN
- [ ] WHERE: tylko warunki techniczne
- [ ] Pominięcia: każde uzasadnione jednym z 4 powodów
