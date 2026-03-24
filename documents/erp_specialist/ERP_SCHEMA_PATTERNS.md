# ERP — Wzorce schematu bazy

Wzorce konwersji dat, tabel pomocniczych i nieoczywistych struktur CDN.
Ładuj gdy pracujesz z datami, atrybutami, dokumentami lub nieznanymi tabelami.

---

## Konwersja dat Clarion

### Dwa różne formaty — rozróżnij przed pisaniem kodu

| Format | Zakres wartości | Przykład kolumny | Konwersja |
|---|---|---|---|
| **Clarion DATE** | ~70000–100000 (dni od 1800-12-28) | Rez_DataRealizacji, Twr_DataUtworzenia, ZaN_DataRealizacji, **TrN_Data2, TrN_Data3** | `DATEADD(d, col, '18001228')` |
| **Clarion TIMESTAMP** | ~10^9 (sekundy od 1990-01-01) | Rez_DataRezerwacji | `DATEADD(ss, col, '1990-01-01')` |

**Jak zidentyfikować:** `SELECT MIN(col), MAX(col) FROM CDN.Tabela`
- ~70000–100000 → Clarion DATE
- ~10^9 → Clarion TIMESTAMP
- format daty → SQL DATE

### Bezpieczny zakres Clarion DATE

Standardowy zakres dat Clariona: **1–109211** (1801-01-01 do 2099-12-31).
Wartości spoza tego zakresu (>109211) mogą być **sentinelami aplikacyjnymi** ("bezterminowo").

Przykład z CDN.KntKarty (Knt_EFaVatDataDo):
- 117976 → 2123-12-31 (13 rek.) = sentinel "bezterminowo"
- 150483 → 2212-12-31 (1 rek.) = sentinel "bezterminowo"

**Wzorzec defensywny dla pól z potencjalnym sentinelem:**
```sql
CASE WHEN col BETWEEN 1 AND 109211 THEN DATEADD(d, col, '18001228') ELSE NULL END
```

**Wzorzec standardowy (gdy zakres potwierdzony):**
```sql
CASE WHEN col = 0 THEN NULL ELSE DATEADD(d, col, '18001228') END
```

### Wzorce konwersji (inline, bez CDN functions)

```sql
-- Clarion DATE → SQL DATE (obsługa 0 = brak daty):
CASE WHEN col = 0 THEN NULL
     ELSE CAST(DATEADD(d, col, '18001228') AS DATE)
END

-- Clarion TIMESTAMP → DATETIME:
CASE WHEN col = 0 THEN NULL
     ELSE CAST(DATEADD(ss, col, '1990-01-01') AS DATETIME)
END

-- Dzisiejsza data jako Clarion int (do WHERE):
DATEDIFF(d, '18001228', GETDATE())

-- Pierwszy/ostatni dzień bieżącego miesiąca jako Clarion:
DATEDIFF(d, '18001228', DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1))
DATEDIFF(d, '18001228', EOMONTH(GETDATE()))

-- N dni temu jako Clarion:
DATEDIFF(d, '18001228', DATEADD(d, -N, GETDATE()))

-- Różnica między dwiema datami Clarion w dniach:
(col2 - col1)    -- proste odejmowanie

-- Filtr w WHERE (rezerwacje aktywne i nieprzeterminowane):
Rez_DataRealizacji >= DATEDIFF(d, '18001228', GETDATE())
AND Rez_DataRealizacji > 0
```

### Filtr przez @PAR @D

```sql
-- ERP podstawia wartość Clarion, konwersja po stronie ERP:
Twr_DataUtworzenia/86400+69035 >= ??DataOd
```

---

## Wzorce tłumaczeń wartości (widoki BI)

### Konwencje nazewnictwa kolumn

- Kolumny: PascalCase z underscore, polskie, opisowe (`Data_Wystawienia`, `Kod_Towaru`)
- Klucz główny widoku: `ID_[encja]` (np. `ID_Rezerwacji`, `ID_Zamowienia`)
- Para lookup: zawsze `Kod_X` + `Nazwa_X`
- WHERE: tylko wykluczenie rekordów technicznych (np. `Rez_TwrNumer > 0`). Nigdy logika biznesowa.

### Flagi 0/1

```sql
CASE pole
    WHEN 1 THEN 'Tak'
    WHEN 0 THEN 'Nie'
    ELSE 'Nieznane (' + CAST(pole AS VARCHAR) + ')'
END AS Flaga_Nazwa
```

### Enumeracje — ELSE obowiązkowy

```sql
CASE pole
    WHEN 960 THEN 'Zamówienie sprzedaży'
    WHEN 1152 THEN 'Zamówienie zakupu'
    ELSE 'Nieznane (' + CAST(pole AS VARCHAR) + ')'
END AS Typ_Dokumentu
```

**UWAGA:** ELSE z surową wartością jest obowiązkowy — nowe wartości mogą pojawić się w przyszłości.

### Pole numeryczne = brak (0 → NULL)

```sql
CASE WHEN col = 0 THEN NULL ELSE col END AS ID_Powiazania
```

Stosuj gdy 0 oznacza "brak powiązania" (np. klucze obce, numery dokumentów).

---

## Odkrywanie nazw nieznanych tabel

Nazwy tabel CDN są nieintuicyjne — **nigdy nie zgaduj**. Zawsze weryfikuj przez:

```
docs_search "[prefiks]GIDNumer"   ← znajdzie tabelę po prefiksie kolumny klucza
```

Przykład: szukasz tabeli operatorów → `docs_search "Ope_GIDNumer"` → `CDN.OpeKarty` (nie `CDN.Operatorzy`).

---

## CDN.Obiekty — słownik typów dokumentów

Przy polach GIDTyp w nieznanej tabeli — najpierw `docs_search "symbol_lub_numer"` (szybciej, offline):
```
docs_search "14346"   → internal_name=Typ_ProdZasoby → hint na CDN.ProdZasoby
docs_search "BkRez"   → gid_type=2592, tabela=CDN.Rezerwacje
```
Jeśli brak wyniku — zapytaj CDN.Obiekty:

```sql
SELECT OB_GIDTyp, OB_Nazwa, OB_Skrot
FROM CDN.Obiekty
WHERE OB_GIDTyp IN (960, 2592, 14346)
```

Znane wartości:
| GIDTyp | Nazwa | Skrót |
|---|---|---|
| 960 | Zamówienie | Zam |
| 2592 | Rezerwacja u dostawcy | BkRez |
| 14346 | Zasób procesu produkcyjnego | ZPZ |

---

## ZaN_ZamTyp vs ZaN_GIDTyp (CDN.ZamNag)

**UWAGA — częsty błąd:**

- `ZaN_GIDTyp` = 960 dla **wszystkich** rekordów ZamNag (typ obiektu/tabeli — nie używaj do rozróżniania ZS/ZZ)
- `ZaN_ZamTyp` = faktyczny kierunek dokumentu: **1280 = ZS** (sprzedaż), **1152 = ZZ** (zakup)
  - UWAGA: w bazie ERPXL_CEIM ZS ma typ **1280**, nie 960 (zweryfikowano CDN.NazwaObiektu 2026-03-04)
  - Wartość 960 nie pojawia się w aktywnych rezerwacjach tej bazy

```sql
-- Poprawnie — kierunek zamówienia (baza ERPXL_CEIM):
CASE z.ZaN_ZamTyp WHEN 1280 THEN 'ZS' WHEN 1152 THEN 'ZZ' ELSE '???' END

-- Błędnie — ZaN_GIDTyp zawsze 960:
CASE z.ZaN_GIDTyp ...  ← NIGDY nie używaj do rozróżniania ZS/ZZ
```

Jeśli w danych pojawią się inne wartości ZaN_ZamTyp (np. wykryjesz przez `SELECT DISTINCT ZaN_ZamTyp FROM CDN.ZamNag`) — **eskaluj do usera** z surówką (ile rekordów, jakie serie/numery). Nie nazywaj nieznanego typu dopóki user nie wyjaśni co to jest.

---

## Numeracja dokumentów (inline, bez CDN.NumerDokumentu)

Funkcja `CDN.NumerDokumentu` i `CDN.NazwaObiektu` wymagają EXECUTE — CEiM_Reader nie ma dostępu.
Buduj numer ręcznie. **Przed wdrożeniem zweryfikuj z userem** — poproś o SELECT z CDN.NazwaObiektu
i porównaj z ręczną konstrukcją na realnych danych. Patrz `ERP_VIEW_WORKFLOW.md` sekcja "e) Weryfikacja numerów dokumentów".

**Format roku:** nie zakładaj czy to YY czy YYYY — zawsze weryfikuj przez NazwaObiektu zanim wpiszesz do SQL.

### ZamNag (ZS/ZZ)

```sql
CASE z.ZaN_ZamTyp WHEN 1280 THEN 'ZS' WHEN 1152 THEN 'ZZ' ELSE 'ZAM' END
+ '-' + CAST(z.ZaN_ZamNumer AS VARCHAR(10))
+ '/' + RIGHT('0' + CAST(z.ZaN_ZamMiesiac AS VARCHAR(2)), 2)  -- zero-padded miesiąc
+ '/' + RIGHT(CAST(z.ZaN_ZamRok AS VARCHAR(4)), 2)
+ '/' + RTRIM(z.ZaN_ZamSeria)
-- Wynik: ZS-9/09/25/ZTHK (format roku zweryfikowany przez NazwaObiektu)
```

### ProdZlecenia (ZP) — przez CDN.ProdZasoby

Rezerwacja ZPZ (`Rez_ZrdTyp=14346`) łączy się przez:
`Rez_ZrdNumer → CDN.ProdZasoby.PZA_Id → CDN.ProdZlecenia.PZL_Id` (via `PZA_PZLId`)

```sql
LEFT JOIN CDN.ProdZasoby pza ON pza.PZA_Id = r.Rez_ZrdNumer AND r.Rez_ZrdTyp = 14346
LEFT JOIN CDN.ProdZlecenia pzl ON pzl.PZL_Id = pza.PZA_PZLId

-- Numer (zweryfikowany CDN.NazwaObiektu): ZP-1/08/23/OTO
'ZP-' + CAST(pzl.PZL_Numer AS VARCHAR(10))
+ '/' + RIGHT('0' + CAST(pzl.PZL_Miesiac AS VARCHAR(2)), 2)
+ '/' + RIGHT(CAST(pzl.PZL_Rok AS VARCHAR(4)), 2)
+ '/' + RTRIM(pzl.PZL_Seria)
```

### TraNag (FS/FZ/WZ/PZ)

Numer dokumentu z prefiksem (zweryfikowana formuła, baza ERPXL_CEIM):
```sql
CASE
    -- (Z) = korekta zbiorcza rabatowa: do dokumentu spięte są WZK/WKE/PZK przez spinacz
    WHEN n.TrN_GIDTyp IN (2041, 2045, 1529)
         AND EXISTS (
             SELECT 1 FROM CDN.TraNag s
             WHERE s.TrN_SpiTyp   = n.TrN_GIDTyp
               AND s.TrN_SpiNumer = n.TrN_GIDNumer
               AND (
                    (n.TrN_GIDTyp = 2041 AND s.TrN_GIDTyp = 2009) OR  -- (Z)FSK <- WZK
                    (n.TrN_GIDTyp = 2045 AND s.TrN_GIDTyp = 2013) OR  -- (Z)FKE <- WKE
                    (n.TrN_GIDTyp = 1529 AND s.TrN_GIDTyp = 1497)     -- (Z)FZK <- PZK
               )
         )                                                   THEN '(Z)'
    -- (A) PRZED fallback Stan&2: FZK (1529) z GenDokMag=-1 i Stan=3 ma Stan&2=2,
    -- więc bez tej kolejności dostałby błędnie (Z) zamiast (A)
    WHEN n.TrN_GenDokMag = -1
         AND n.TrN_GIDTyp IN (1521, 1529, 1489)             THEN '(A)'
    WHEN n.TrN_Stan & 2 = 2
         AND n.TrN_GIDTyp IN (2041, 2045, 1529)             THEN '(Z)'  -- fallback heurystyczny
    WHEN n.TrN_GenDokMag = -1                               THEN '(s)'
    ELSE ''
END
-- Format pełny (zweryfikowany CDN.NazwaObiektu, 2026-03-15): (PREFIKS)SKRÓT-Numer/MM/YY[/Seria]
+ CASE n.TrN_GIDTyp
    WHEN 2034 THEN 'PA'   WHEN 2033 THEN 'FS'   WHEN 1617 THEN 'PW'
    WHEN 2001 THEN 'WZ'   WHEN 1521 THEN 'FZ'   WHEN 2009 THEN 'WZK'
    WHEN 1603 THEN 'MMW'  WHEN 1604 THEN 'MMP'  WHEN 1616 THEN 'RW'
    WHEN 2041 THEN 'FSK'  WHEN 2003 THEN 'KK'   WHEN 1489 THEN 'PZ'
    WHEN 1497 THEN 'PZK'  WHEN 1625 THEN 'PWK'  WHEN 1529 THEN 'FZK'
    WHEN 2042 THEN 'PAK'  WHEN 2037 THEN 'FSE'  WHEN 2013 THEN 'WKE'
    WHEN 2005 THEN 'WZE'  WHEN 1624 THEN 'RWK'  WHEN 2039 THEN 'RS'
    WHEN 2045 THEN 'FKE'  WHEN 2035 THEN 'RA'   WHEN 2004 THEN 'DP'
    WHEN 1232 THEN 'KDZ'
    ELSE CAST(n.TrN_GIDTyp AS VARCHAR(10))
  END
+ '-' + CAST(n.TrN_TrNNumer AS VARCHAR(10))
+ '/' + RIGHT('0' + CAST(n.TrN_TrNMiesiac AS VARCHAR(2)), 2)
+ '/' + RIGHT(CAST(n.TrN_TrNRok AS VARCHAR(4)), 2)
+ CASE WHEN RTRIM(n.TrN_TrNSeria) = '' THEN '' ELSE '/' + RTRIM(n.TrN_TrNSeria) END
```

Uwagi:
- `TrN_TypNumeracji` nie istnieje — używaj `TrN_GIDTyp IN (lista numeryczna)`
- `(Z)` = korekta zbiorcza rabatowa, nie "zwrot/anulowanie" (źródło: dok. Comarch 2018.1)
- Rozrachunki.sql używa starej heurystyki Stan & 2 — wymaga aktualizacji przez ERP Specialist

### KB (784) → CDN.Zapisy

Nie buduj numeru inline — `KAZ_NumerDokumentu` zawiera gotowy string:

```sql
LEFT JOIN CDN.Zapisy kaz ON kaz.KAZ_GIDNumer = r.ROZ_KAZNumer
-- numer: kaz.KAZ_NumerDokumentu  (gotowy string, bez transformacji)
```

### CDN.UpoNag (typ 2832) — Nota odsetkowa

Typ 2832 (NO) **nie jest w CDN.TraNag** — jest w CDN.UpoNag (tabela upomnień/not odsetkowych).

```sql
LEFT JOIN CDN.UpoNag upo ON upo.UPN_GIDNumer = r.ROZ_TrpNumer  -- lub KAZNumer
WHERE r.ROZ_TrpTyp = 2832  -- lub ROZ_KAZTyp = 2832
```

Format numeru (zweryfikowany CDN.NazwaObiektu):
```sql
'NO-' + RIGHT(CAST(upo.UPN_Rok AS VARCHAR(4)), 2) + '/' + CAST(upo.UPN_Numer AS VARCHAR(10))
-- Wynik: NO-25/3  (YY/Numer — rok przed numerem, odwrotnie niż w większości typów)
```

W klauzuli NOT IN dla TraNag wyklucz typ 2832:
```sql
r.ROZ_TrpTyp NOT IN (784, 4144, 435, 2832)
```

---

## CDN.TraNag ↔ CDN.ZamNag (TrN_ZaNNumer)

Dokumenty WZ/FS/PZ łączą się z zamówieniem przez:

```sql
TrN_ZaNNumer = ZaN_GIDNumer  AND  TrN_ZaNTyp = 960
```

Przydatne dla widoków łączących zamówienia z dokumentami realizacji.

---

## Dokumenty źródłowe — ZrdTyp/ZrdNumer (multi-type reference)

Gdy tabela ma ZrdTyp/ZrdNumer wskazujące na wiele typów dokumentów (np. MagNag: 21 typów):

1. **Zidentyfikuj główne typy:**
   - TraNag (GIDTyp różne od 960) — pokrywa większość typów
   - ZamNag (GIDTyp = 960)

2. **Buduj LEFT JOIN dla każdego głównego typu:**
   ```sql
   LEFT JOIN CDN.TraNag zrd_tra
     ON TrN_GIDNumer = ZrdNumer
     AND TrN_GIDTyp = ZrdTyp
     AND ZrdNumer > 0
     AND ZrdTyp <> 960

   LEFT JOIN CDN.ZamNag zrd_zan
     ON ZaN_GIDNumer = ZrdNumer
     AND ZrdTyp = 960
     AND ZrdNumer > 0
   ```

3. **CASE dla Nr_Dokumentu_Zrodlowego:**
   ```sql
   CASE
     WHEN ZrdNumer = 0 THEN NULL
     WHEN ZrdTyp = 960 THEN [format ZS z ZamNag]
     ELSE [format TraNag ze skrótem z obiekty.tsv]
   END
   ```

Nie buduj osobnego JOIN per typ — wystarczą 2-3 główne kategorie.

---

## JOIN kontrahenta (dwuczęściowy klucz)

```sql
LEFT JOIN CDN.KntKarty k ON k.Knt_GIDNumer = r.Rez_KntNumer
                         AND k.Knt_GIDTyp   = r.Rez_KntTyp
```

Zawsze LEFT JOIN — rezerwacje wewnętrzne mogą nie mieć KntNumer.

---

## Magazyn globalny (ID = 0)

```sql
CASE WHEN r.Rez_MagNumer = 0 THEN 'Globalnie' ELSE m.Mag_Nazwa END AS Magazyn,
CASE WHEN r.Rez_MagNumer = 0 THEN NULL ELSE m.Mag_Kod END AS Kod_Magazynu,
CASE WHEN r.Rez_MagNumer = 0 THEN 'Tak' ELSE 'Nie' END AS Rezerwacja_Globalna
-- i zawsze LEFT JOIN CDN.Magazyny m ON m.Mag_GIDNumer = r.Rez_MagNumer
```

---

## Tabele pomocnicze

### Załączniki (CDN.DaneBinarne + CDN.DaneObiekty)

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

| Kolumna | Znaczenie |
|---|---|
| `TwZ_Ilosc` | Ilość dostępna (widoczna w ERP jako "stan") |
| `TwZ_IlMag` | Ilość fizyczna w magazynie |

```sql
NOT EXISTS (
    SELECT 1 FROM CDN.TwrZasoby
    WHERE TwZ_TwrNumer = Twr_GIDNumer AND TwZ_Ilosc > 0
)
```

### Atrybuty (CDN.Atrybuty)

```sql
EXISTS (
    SELECT 1 FROM CDN.Atrybuty
    WHERE Atr_ObiNumer = Twr_GIDNumer AND Atr_ObiTyp = Twr_GIDTyp
      AND Atr_AtkId = 59 AND Atr_Wartosc = 'Wartość'
)
```

### Opisy dokumentów

```sql
-- Handlowe (CDN.TrNOpisy):
TrN_GIDNumer IN (SELECT TnO_TrnNumer FROM cdn.TrNOpisy WHERE UPPER(Tno_Opis) LIKE '%SEZON%')

-- Zamówienia (CDN.ZaNOpisy):
ZaN_GIDNumer IN (SELECT ZnO_ZamNumer FROM cdn.ZaNOpisy WHERE ZnO_Opis LIKE '%SEZON%')

-- Magazynowe — brak osobnej tabeli opisów; opis bezpośrednio w MaN_CechaOpis:
UPPER(MaN_CechaOpis) LIKE '%SEZON%'
```

**UWAGA:** CDN.MagNag nie ma odpowiednika TrNOpisy. Filtr
`Okno dokumenty/Magazynowe/filters/Sezon w opisie dokumentu.sql` używa błędnie
`TrN_GIDNumer` i `cdn.TrNOpisy` — należy go zastąpić `MaN_CechaOpis`.

### Operatorzy (CDN.OpeKarty)

**UWAGA:** Kolumna `Ope_Kod` NIE ISTNIEJE — zwraca SQL_ERROR. Używaj `Ope_Ident` (login operatora).

```sql
LEFT JOIN CDN.OpeKarty ope ON ope.Ope_GIDNumer = [pole]OpeNumer
-- Kolumna opisowa: Ope_Ident (login, np. "ADMIN", "JAN.KOWALSKI")

-- W filtrze:
WHERE Ope_Ident LIKE '%' + ??Wystawiajacy + '%'
```

### Adresy kontrahentów (CDN.KntAdresy)

Tabela `CDN.KntAdresy` — adresy dostawy kontrahentów.

| GIDTyp | Nazwa | Opis |
|--------|-------|------|
| 864 | Adr | Adres podstawowy |
| 896 | AdrAl | Adres inny |

```sql
LEFT JOIN CDN.KntAdresy kna
    ON kna.KnA_GIDNumer = [pole]KnANumer
   AND kna.KnA_GIDTyp   = [pole]KnATyp
   AND [pole]KnANumer > 0
```

Kolumny opisowe:
- `KnA_Akronim` — alias adresu (główna kolumna identyfikująca)
- `KnA_Nazwa1` — nazwa firmy/odbiorcy
- `KnA_Miasto`, `KnA_Ulica` — adres fizyczny

Weryfikacja JOIN na `CDN.MagNag`: 167 232 = 167 232 (100%).

### Płatności (CDN.TraPlat)

| Kolumna | Znaczenie |
|---|---|
| `TrP_FormaNazwa` | Nazwa formy płatności |
| `TrP_Kwota` | Kwota |
| `TrP_Rozliczona` | 0 = nierozliczona |
| `TrP_FormaNr` | 10=gotówka, 50=karta |

### Prefiks widoku Kontrahenci/Grupy

Widok "Grupy" używa prefiksu `KnG_` (nie `Knt_`). Filtr musi odnosić się do `KnG_GIDNumer`.

### Grupy kontrahentów — dwie tabele, różne zastosowania

| Tabela | Typ rekordów | Zastosowanie |
|---|---|---|
| `CDN.KntGrupy` type=-32 | ~30 rek. — definicje grup (hierarchia) | budowanie ścieżki CTE |
| `CDN.KntGrupy` type=32 | ~5651 rek. — WSZYSTKIE grupy kontrahenta | bridge table — mnoży wiersze |
| `CDN.KntGrupyDom` type=-32 | ~29 rek. — definicje grup (hierarchia) | budowanie ścieżki CTE |
| `CDN.KntGrupyDom` type=32 | dokładnie 1 rek. per kontrahent | **GRUPA GŁÓWNA** — użyj tej |

**Wzorzec dla grupy głównej (ścieżka rekurencyjna):**
```sql
WITH Sciezka_Grup AS (
    SELECT KGD_GIDNumer, CAST(KGD_Kod AS NVARCHAR(2000)) AS Sciezka
    FROM CDN.KntGrupyDom WHERE KGD_GIDTyp = -32 AND KGD_GrONumer = 0
    UNION ALL
    SELECT g.KGD_GIDNumer, CAST(p.Sciezka + '\' + RTRIM(g.KGD_Kod) AS NVARCHAR(2000))
    FROM CDN.KntGrupyDom g
    INNER JOIN Sciezka_Grup p ON p.KGD_GIDNumer = g.KGD_GrONumer
    WHERE g.KGD_GIDTyp = -32 AND g.KGD_GrONumer > 0
)
-- W zapytaniu głównym:
LEFT JOIN CDN.KntGrupyDom kgd
    ON kgd.KGD_GIDNumer = k.Knt_GIDNumer AND kgd.KGD_GIDTyp = 32
LEFT JOIN Sciezka_Grup sg ON sg.KGD_GIDNumer = kgd.KGD_GrONumer
```

`KGD_GIDNumer` (type=32) = `Knt_GIDNumer` kontrahenta (nie `Knt_KnGNumer`!).
`KGD_GrONumer` = GIDNumer grupy nadrzędnej w hierarchii type=-32.

### Grupy towarów — CDN.TwrGrupyDom

Analogiczny wzorzec dla hierarchii grup towarowych.

| Tabela | Typ rekordów | Zastosowanie |
|---|---|---|
| `CDN.TwrGrupyDom` type=-16 | definicje grup (hierarchia) | budowanie ścieżki CTE |
| `CDN.TwrGrupyDom` type=16 | przynależność towaru do grupy | link towar → grupa |

**Wzorzec dla grupy towarowej (ścieżka rekurencyjna):**
```sql
WITH Sciezka_Grup AS (
    SELECT GIDNumer, GrONumer, CAST(Kod AS NVARCHAR(500)) AS Sciezka
    FROM CDN.TwrGrupyDom WHERE GIDTyp = -16 AND GrONumer = 0
    UNION ALL
    SELECT d.GIDNumer, d.GrONumer, CAST(sg.Sciezka + '\' + d.Kod AS NVARCHAR(500))
    FROM CDN.TwrGrupyDom d JOIN Sciezka_Grup sg ON sg.GIDNumer = d.GrONumer
    WHERE d.GIDTyp = -16
)
-- W zapytaniu głównym:
LEFT JOIN CDN.TwrGrupyDom tgd
    ON tgd.GIDNumer = t.Twr_GIDNumer AND tgd.GIDTyp = 16
LEFT JOIN Sciezka_Grup sg ON sg.GIDNumer = tgd.GrONumer
```

Format ścieżki: `Poziom1\Poziom2\Poziom3`. Kolumny: `ID_Grupy` + `Sciezka_Grupy`.

---

## CDN.Rozrachunki — struktura GIDLp

Każde rozliczenie = **2 lustrzane wiersze** (GIDLp=1 i GIDLp=2) z zamienionymi stronami TRP/KAZ.
Widok bierze wyłącznie `GIDLp=1`.

```sql
WHERE r.ROZ_GIDLp = 1
```

- TRP = strona 1 (najczęściej faktura/paragon — typy TraNag, UpoNag)
- KAZ = strona 2 (najczęściej płatność KB — typ 784 → CDN.Zapisy)
- Dominujący wzorzec w ERPXL_CEIM: PA(2034) → KB(784) — ~135k wierszy

Przy dodawaniu JOIN sprawdź czy `COUNT(*) = COUNT(DISTINCT ROZ_GIDNumer)` —
CDN.Zapisy może mieć wiele wierszy na jeden KAZ_GIDNumer (raporty kasowe).

---

## Znane problematyczne filtry

| Plik | Problem |
|---|---|
| `Okno lista zamówień sprzedaży/Zamówienia/filters/Wystawiający.sql` | Brak `??Wystawiający` w WHERE |
| `Okno dokumenty/Magazynowe/filters/Sezon w opisie dokumentu.sql` | Używa `TrN_GIDNumer` zamiast `MaN_GIDNumer` |
| `Okno zapisy bankowe/Zapisy bankowe/filters/Wartość i numer dokumentu.sql` | Stary format inline bez `@PAR` |
| `Okno dokumenty/Elementy/columns/Marża.sql` | Brak `WHERE {filtrsql}` |
