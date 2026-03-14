## Status: Faza 2 — SQL gotowy, czeka na zatwierdzenie usera

**Tabela główna:** CDN.Rezerwacje (label: Rezerwacje_Towarów)
**Filtr techniczny:** Rez_TwrNumer > 0

**Baseline:** COUNT(*) = 1090, COUNT(DISTINCT Rez_GIDNumer) = 1090 ✓

---

## Enumeracje rozkodowane

### Rez_GIDTyp (typ własnej encji)
- 2592 = 'Rezerwacja u dostawcy' (CDN.Obiekty)
- 2576 = 'Rezerwacja' (CDN.Obiekty)

### Rez_TwrTyp (typ towaru)
- 0 = brak towaru (pominięte przez filtr)
- 16 = 'Towar' (CDN.Obiekty)

### Rez_ZrdTyp (typ dokumentu źródłowego) — WYMAGA WERYFIKACJI NUMERACJI
- 960   = 'Zamówienie' (CDN.Obiekty)
- 14346 = 'Zasób procesu produkcyjnego' / ZPZ (CDN.Obiekty)
- 2592  = 'Rezerwacja u dostawcy' (CDN.Obiekty)

### Rez_KntTyp (typ kontrahenta)
- 0  = brak kontrahenta
- 32 = 'Kontrahent' (CDN.Obiekty)

### Rez_DstTyp (typ dostawy)
- 0   = brak dostawy
- 160 = 'Dostawa' (CDN.Obiekty)

### Rez_OpeTyp — zawsze 128 = 'Operator'
### Rez_MagTyp — zawsze 208 = 'Magazyn'

### Rez_Zrodlo (źródło rezerwacji)
- 5  = 'Z zamówienia wewnętrznego' (dokumentacja)
- 6  = 'Ręczna wewnętrzna' (dokumentacja, nie ma w bazie)
- 9  = 'Z zamówienia zewnętrznego' (dokumentacja)
- 10 = 'Ręczna zewnętrzna' (dokumentacja)
- 16 = 'Dok. magazynowy' (dokumentacja, nie ma w bazie)

### Rez_Aktywna
- Zawsze 1 = 'Tak' (w zbiorze po filtrze)

### Rez_Typ
- Zawsze 1 = 'Rezerwacja' (dokumentacja: 1-rezerwacja, 0-nierezerwacja)

### Rez_Priorytet
- 0  = bez priorytetu
- 20 = priorytet 20 (dokumentacja nie podaje etykiet — zachować surową wartość)

---

## Typy dat (Clarion)

| Pole              | Zakres wartości   | Typ              | Konwersja                              |
|-------------------|-------------------|------------------|----------------------------------------|
| Rez_DataRealizacji | 81258–82253      | Clarion DATE     | DATEADD(d, col, '18001228')            |
| Rez_DataWaznosci  | 81258–93890       | Clarion DATE     | DATEADD(d, col, '18001228')            |
| Rez_DataAktywacji | 81253–82249       | Clarion DATE     | DATEADD(d, col, '18001228')            |
| Rez_DataPotwDst   | 81258–82253       | Clarion DATE     | DATEADD(d, col, '18001228')            |
| Rez_DataRezerwacji| 1054812919–1141727805 | Clarion TIMESTAMP | DATEADD(ss, col, '1990-01-01')     |
| Rez_TStamp        | ~10^9             | Clarion TIMESTAMP | DATEADD(ss, col, '1990-01-01')        |

---

## JOINy ustalone (brak mnożenia wierszy — każdy 1090/1090)

| JOIN                   | Klucz                             | Dane do sprowadzenia        |
|------------------------|-----------------------------------|-----------------------------|
| CDN.TwrKarty t         | t.Twr_GIDNumer = r.Rez_TwrNumer   | Twr_Kod, Twr_Nazwa          |
| CDN.KntKarty k         | k.Knt_GIDNumer = r.Rez_KntNumer   | Knt_Kod, Knt_Nazwa (LEFT)   |
| CDN.OpeKarty o         | o.Ope_GIDNumer = r.Rez_OpeNumer   | Ope_Ident, Ope_Nazwisko     |
| CDN.Magazyny m         | m.Mag_GIDNumer = r.Rez_MagNumer   | Mag_Kod, Mag_Nazwa          |

Tabela CDN.OpeKarty (nie CDN.Operatorzy — ta nie istnieje).

---

## Numery dokumentów — CZEKA NA ODPOWIEDŹ USERA

Query przekazany userowi — ZrdTyp: 960 (Zamówienie), 14346 (ZPZ), 2592 (Rezerwacja u dostawcy).

---

## Pola do pominięcia (COUNT DISTINCT = 1 dla całej tabeli)

- Rez_GIDFirma, Rez_TwrFirma, Rez_ZrdFirma, Ope_Firma, Mag_Firma — stała firma
- Rez_GIDLp — zawsze 0
- Rez_Opis — zawsze pusty

---

## Pliki

- Brudnopis: solutions/bi/drafts/Rezerwacje.sql
- Plan: solutions/bi/plans/Rezerwacje_plan.xlsx
- Progress: solutions/bi/drafts/Rezerwacje_progress.md

## Zmiany po przeglądzie planu przez usera

**Usunięte (decyzja usera):**
- Rez_BsSTwrNumer i Rez_BsNID (zawsze 0 — bezwartościowe)
- GUID_Rezerwacji (zawsze pusty)

**Dodane:**
- Numer_Dok_Zrodlowego — inline z CDN.ZamNag dla ZrdTyp=960 (ZW). ZPZ i Rez.u.dostawcy = NULL (ograniczenie)
- Numer_Dok_Dostawy — inline z CDN.Dostawy + CDN.TraNag (FZ/PW/PZ)
- Nazwa_Centrum — CDN.FrmStruktura JOIN na FRS_ID
- Nazwa_Zasobu_Technologii — CDN.ProdTechnologiaZasoby JOIN na PTZ_Id
- Imie_Nazwisko_Operatora — Ope_Nazwisko (pełna nazwa, brak Ope_Imie w tabeli)
- Typ (Rez_Typ) — CASE 1=Rezerwacja 0=Nierezerwacja (włączony na żądanie usera)

**Bugfix JOINów:**
- Magazyny: INNER → LEFT JOIN (277 rekordów ma Rez_MagNumer=0 = rezerwacja globalna)
- KntKarty: Knt_Kod→Knt_Akronim, Knt_Nazwa→Knt_Nazwa1

**Inline ZPZ — ROZWIĄZANE:**
ZrdTyp=14346, ZrdNumer=CDN.ProdZasoby.PZA_Id → PZA_PZLId → CDN.ProdZlecenia (PZL_Numer/Miesiac/Rok/Seria).
Format: 'ZP-' + PZL_Numer + '/' + MM + '/' + RR + '/' + Seria. Zweryfikowane: ZP-1/08/23/OTO ✓.
COUNT po dodaniu JOINów: 1090/1090 ✓.

**Weryfikacja ostateczna:** 1090/1090 ✓ (3 eksporty, wszystkie zgodne z baseline)

## Ograniczenie — Numer_Dok_Zrodlowego (NIEROZWIĄZANE, wymaga DBA)

Rez_ZrdTyp=960 → CDN.ZamNag (ZaN_GIDNumer=ZrdNumer, ZaN_GIDTyp=960).
Prefix dokumentu zależy od ZaN_ZamTyp:

| ZaN_ZamTyp | Prefix | Rekordów | Inline |
|---|---|---|---|
| 1152 | ZZ- | 10 | ✓ można dodać do CASE |
| 1280 | ZW- LUB ZS- | 27 | ✗ prefix zależy od logiki wewnętrznej CDN.NazwaObiektu |
| 14346 (ZPZ) | ZP- | 516 | ✗ tabela z ZrdNumer (zakres 10k+) nieznana |
| 2592 | brak | 32 | — |

Dla ZaN_ZamTyp=1280: OTO/BUS/FRA serie → "ZW-", PH_x/SPKR serie → "ZS-".
Wzorzec oparty na serii jest kruchy — nie wszystkie serie znane.
CDN.NazwaObiektu rozwiązuje problem jednoznacznie — DBA powinien rozważyć
embedding funkcji w CREATE VIEW (ownership chaining może działać dla CEiM_BI).

ZWERYFIKOWANE (CDN.NazwaObiektu w SSMS, wszystkie serie):
- ZaN_ZamTyp=1152 → ZZ- (seria ZTHK)
- ZaN_ZamTyp=1280, LIKE 'PH[_]%' lub 'SPKR' → ZS- (PH_2/3/5/6, SPKR)
- ZaN_ZamTyp=1280, IN('OTO','BUS','FRA') → ZW-
- ELSE → '??(...)-...' — jawny fallback dla nowych serii
- ZrdTyp=2592 → '<do uzupelnienia>' (zwraca funkcja CDN.NazwaObiektu)

**Następny krok:** Zatwierdzenie SQL przez usera → CREATE OR ALTER VIEW BI.Rezerwacje → commit
