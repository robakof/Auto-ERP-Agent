# Session Log

*5 pozycji*

---

## Status: Faza 1 — Plan zatwierdzony, gotowy do SQL

**Tabela główna:** CDN.Rozrachunki, 340 960 rekordów
**Filtr techniczny:** ROZ_GIDLp = 1 → 170 480 wierszy roboczych

**Baseline:** COUNT(*) z GIDLp=1 = 170 480 ✓

---

## Struktura tabeli

Każde rozliczenie = 2 wiersze (GIDLp=1 i GIDLp=2) — lustro z zamienionymi TRP/KAZ i różną walutą.
Widok bierze tylko GIDLp=1.

---

## Typy dokumentów (ROZ_TrpTyp / ROZ_KAZTyp)

```
435  = Różnica kursowa (RK)
784  = Zapis kasowy/bankowy (KB)
1489 = Przyjęcie zewnętrzne (PZ)
1521 = Faktura zakupu (FZ)
1529 = Korekta faktury zakupu (FZK)
2033 = Faktura sprzedaży (FS)
2034 = Paragon (PA)
2037 = Faktura eksportowa (FSE)
2041 = Korekta faktury sprzedaży (FSK)
2042 = Korekta paragonu (PAK)
2045 = Korekta faktury eksportowej (FKE)
2832 = Nota odsetkowa (NO)
4144 = Nota memoriałowa (NM)
```

Rozkład TRP: PA=135027, KB=23695, FS=9963, FSK=852, FZ=461, PAK=201, NM=180, FZK=86, FSE=11, NO=3, FKE=1

---

## JOINy — potwierdzone

| Typ (TrpTyp/KAZTyp) | Tabela | Klucz JOIN | Kolumna numeru |
|---|---|---|---|
| FS/PA/FSE/FSK/PAK/FKE/FZ/FZK/PZ/NO (TraNag typy) | CDN.TraNag | TrN_GIDTyp + TrN_GIDNumer | inline — patrz niżej |
| 784 (KB) | CDN.Zapisy | KAZ_GIDTyp + KAZ_GIDNumer | KAZ_NumerDokumentu (gotowy string) |
| 4144 (NM) | CDN.MemNag | MEN_GIDNumer (180/180 matched) | inline: MEN_Seria/YYYY/MM/MEN_Numer |
| 435 (RK) | CDN.RozniceKursowe | RKN_ID = ROZ_KAZNumer | inline: RK-RKN_Numer/YY |
| Operator | CDN.OpeKarty | Ope_GIDNumer = ROZ_OpeNumerRL | Ope_Ident, Ope_Nazwisko |

---

## Formaty numerów dokumentów — ZWERYFIKOWANE

### TraNag (FS, PA, FSE, FSK, PAK, FKE, FZ, FZK, PZ, NO)

```sql
CASE
    WHEN TrN_Stan & 2 = 2 AND TrN_GIDTyp IN (2041,1529,2042,2045) THEN '(Z)'
    WHEN TrN_GenDokMag = -1 AND TrN_GIDTyp IN (1521,1529,1489)    THEN '(A)'
    WHEN TrN_GenDokMag = -1                                        THEN '(s)'
    ELSE ''
END
+ OB_Skrot + '-'
+ CAST(TrN_TrNNumer AS VARCHAR(20))
+ '/' + RIGHT('0' + CAST(TrN_TrNMiesiac AS VARCHAR(2)), 2)
+ '/' + RIGHT(CAST(TrN_TrNRok AS VARCHAR(4)), 2)
+ CASE WHEN TrN_TrNSeria <> '' THEN '/' + TrN_TrNSeria ELSE '' END
```

Pokrycie: 99.999% (170 478 / 170 480). Znany wyjątek: 1 rekord FSK (GIDNumer=6394119,
FSK-8/01/26/SPKRK) dostaje (Z) z CDN.NazwaObiektu mimo Stan=5 (bit1=0). Nie udało się
ustalić przyczyny — wszystkie pola TraNag identyczne jak sąsiednie (s)FSK.
Prompt dla agenta researchującego: Rozrachunki_researcher_prompt.md

**Prefiksy — znaczenie:**
- (s) = serwisowy / bez dokumentu magazynowego (GenDokMag=-1 dla typów sprzedażowych)
- (A) = anulowany (GenDokMag=-1 dla FZ/FZK/PZ — typy zakupowe)
- (Z) = zwrot (korekty z TrN_Stan & 2 = 2)
- brak = standard (GenDokMag=2)

**PA specyfika:** GenDokMag przyjmuje wartości 0, 1, 2 (nie tylko -1/2) — brak prefiksu dla PA.

### Zapisy (KB, typ 784)

```sql
KAZ_NumerDokumentu  -- gotowy string, np. "PA-1/06/23/FRA"
```

### MemNag (NM, typ 4144)

Format z systemu: `NM-INN/2026/02/2` → schemat: Skrot-Seria/YYYY/MM/Numer

```sql
'NM-' + MEN_Seria
+ '/' + LEFT(CAST(MEN_RokMiesiac AS VARCHAR(6)), 4)
+ '/' + RIGHT('0' + CAST(MEN_RokMiesiac % 100 AS VARCHAR(2)), 2)
+ '/' + CAST(MEN_Numer AS VARCHAR(10))
```
UWAGA: format NM nie był weryfikowany przez CDN.NazwaObiektu — do potwierdzenia.

### RozniceKursowe (RK, typ 435)

Format z systemu: `RK-10/25` → schemat: RK-Numer/YY

```sql
'RK-' + CAST(RKN_Numer AS VARCHAR(10))
+ '/' + RIGHT(CAST(RKN_Rok AS VARCHAR(4)), 2)
```

---

## Stałe (pominięte w widoku)

ROZ_GIDTyp=433, ROZ_GIDLp (filtr=1), ROZ_DtTyp/Firma/Numer/Lp=0,
ROZ_CtTyp/Firma/Numer/Lp=0, ROZ_DataOddzialu=0, ROZ_DataCentrali=0,
ROZ_DTDC=0, ROZ_CTDC=0, ROZ_OpeTypRL=128, ROZ_OpeLpRL=0,
ROZ_OpeTypRZ/FirmaRZ/NumerRZ/LpRZ=0, ROZ_DataRozrachunku=0, ROZ_Wycena=0

---

## ROZ_DataRozliczenia

Typ: Clarion DATE → `DATEADD(d, ROZ_DataRozliczenia, '18001228')`
Min: 81238 = 2023-05-31, Max: 1908212 = 7025 (błąd w danych ERP)
Liczba rekordów z datą > ok. 2030: 4 rekordy
User chce: zachować datę + flaga `Data_Podejrzana = CASE WHEN > 84000 THEN 'Tak' ELSE 'Nie' END`
Próg 84000 ≈ rok 2030 (bezpieczny margines).

---

## Enumeracje

ROZ_RKStrona: 0=Brak RK (170439 rek.), 1=Winien (30 rek.), 2=Ma (11 rek.)
ROZ_GIDFirma / ROZ_TrpFirma / ROZ_KAZFirma: distinct=2 → {1464833, 11528}

---

## Pliki

- Brudnopis:    solutions/bi/Rozrachunki/Rozrachunki_draft.sql
- Plan Excel:   solutions/bi/Rozrachunki/Rozrachunki_plan.xlsx  ← ZATWIERDZONE przez usera
- Plan src:     solutions/bi/Rozrachunki/Rozrachunki_plan_src.sql
- Obiekty:      solutions/bi/Rozrachunki/Rozrachunki_objects.sql
- Verify:       solutions/bi/Rozrachunki/Rozrachunki_objects_verify.sql
- Researcher:   solutions/bi/Rozrachunki/Rozrachunki_researcher_prompt.md

---

## Status: Faza 4 — ZAKOŃCZONE ✓

**Baseline aktualny:** 170 484–170 487 (baza produkcyjna rośnie między zapytaniami)
**Brak mnożenia wierszy:** COUNT(*) = COUNT(DISTINCT ROZ_GIDNumer) ✓
**Nr_Dok1 NULL:** 0 strukturalnych (artefakty wyścigu czasowego w eksporcie) ✓
**Nr_Dok2 NULL:** 0 strukturalnych ✓

### Odkrycie: Nota odsetkowa w CDN.UpoNag

Typ 2832 (NO) NIE jest w CDN.TraNag — rekordy są w CDN.UpoNag.
JOIN: `upo.UPN_GIDNumer = r.ROZ_TrpNumer/KAZNumer` przy danym typie.
Kolumny numeru: UPN_Numer, UPN_Rok, UPN_Seria.
3 rekordów TRP=NO, 7 rekordów KAZ=NO — wszystkie matchują.

Format numeru NO (ZWERYFIKOWANY przez CDN.NazwaObiektu):
`NO-{RIGHT(Rok,2)}/{Numer}` np. NO-25/3

```sql
'NO-' + RIGHT(CAST(UPN_Rok AS VARCHAR(4)), 2)
+ '/' + CAST(UPN_Numer AS VARCHAR(10))
+ CASE WHEN UPN_Seria <> '' THEN '/' + UPN_Seria ELSE '' END
```

### Pliki

- Brudnopis: solutions/bi/Rozrachunki/Rozrachunki_draft.sql (iteracja 3)
- Eksport:   solutions/bi/Rozrachunki/Rozrachunki_export.xlsx

### bi_verify (Faza 3) — wyniki

- 170 490 wierszy, 26 kolumn ✓
- ID_Rozliczenia distinct = row_count — klucz unikalny ✓
- Brak "Nieznane" w Typ_Dok1 / Typ_Dok2 ✓
- Nr_Dok1 null=2, Nr_Dok2 null=4 — artefakty wyścigu czasowego, 0 strukturalnych ✓
- Operator 18 distinct, 0 null ✓
- Waluta PLN/EUR, Strona_RK Brak/Winien/Ma ✓

### Faza 4 — ZAKOŃCZONA

- `solutions/bi/views/Rozrachunki.sql` — CREATE OR ALTER VIEW AIBI.Rozrachunki
- `solutions/bi/catalog.json` — wpis dodany (nazwa AIBI.Rozrachunki)
- Schema zmieniona z BI → AIBI (user zmienił catalog.json ręcznie)
- Widok NIE jest jeszcze wdrożony na bazie — plik SQL gotowy, wymaga uruchomienia w SSMS
- AIBI.KntKarty działa na bazie ✓, AIBI.Rozrachunki i AIBI.Rezerwacje jeszcze nie

### Reguła GID (potwierdzona przez usera, zapisana w ERP_VIEW_WORKFLOW.md)

- GIDFirma → pomijamy
- GIDTyp → tłumaczymy przez CASE
- GIDNumer → zostawiamy
- GIDLp → pomijamy


---

## Status: Faza 1 — Plan wygenerowany, czeka na zatwierdzenie

**Tabela główna:** CDN.ZamNag
**Baseline:** COUNT(*) = 12022, COUNT(DISTINCT ZaN_GIDNumer) = 12022 ✓
**Filtr techniczny:** brak (pełny zbiór)

---

## Enumeracje rozkodowane

| Pole | Wartości | Źródło |
|---|---|---|
| ZaN_GIDTyp | 960 dla wszystkich (stała) | CDN.Obiekty |
| ZaN_ZamTyp | 640=Oferta zakupu, 768=Oferta sprzedaży (6 rek.), 1152=ZZ (519), 1280=ZS (11497) | dokumentacja |
| ZaN_Stan | 1=Oferta, 2=Zamówienie, 3=Potwierdzone, 4=Zaakceptowane, 5=W realizacji, 21=Zrealizowane (16+5), 35=Anulowane potw. (32+3), 51=Anulowane arch.+potw. (32+16+3), 53=Anulowane arch.+w real. (32+16+5) | dokumentacja |
| ZaN_Rodzaj | 4=Zewnętrzne (10953), 8=Wewnętrzne (1069) | dokumentacja |
| ZaN_StatusRealizacji | 0=brak, 1182=Anulowane, 1179=Wysłane | CDN.Slowniki |
| ZaN_RealWCalosci | 0=Nie (12018), 1=Tak (4) | baza |

---

## Typy dat — potwierdzone

| Pole | Format | Wzorzec |
|---|---|---|
| ZaN_DataWystawienia | Clarion DATE (81226–82251) | CAST(DATEADD(d,val,'18001228') AS DATE) |
| ZaN_DataRealizacji | Clarion DATE (81226–93890) | jw. |
| ZaN_DataWaznosci | Clarion DATE (81239–93890) | jw. |
| ZaN_DataPotwierdz | Clarion DATE, 11984/12022 | jw. |
| ZaN_LastMod | Clarion TIMESTAMP (10^9) | CAST(DATEADD(ss,val,'1990-01-01') AS DATETIME) |
| ZaN_GodzinaWystawienia | centisekundy (val/100 → s) | CAST(DATEADD(ss,val/100,'19000101') AS TIME) |
| ZaN_GodzinaPotwierdzenia | centisekundy (val/100 → s) | jw. |

---

## JOINy ustalone (12022/12022 ✓)

| JOIN | Klucz | Dane | Wypełnienie |
|---|---|---|---|
| CDN.KntKarty k | Knt_GIDNumer = ZaN_KntNumer AND > 0 | Knt_Akronim, Knt_Nazwa1 | 10742/12022 |
| CDN.Magazyny m | MAG_GIDNumer = ZaN_MagNumer AND > 0 | MAG_Kod, MAG_Nazwa | 12021/12022 |
| CDN.OpeKarty ow | Ope_GIDNumer = ZaN_OpeNumerW AND > 0 | Ope_Ident | 12022/12022 |
| CDN.FrmStruktura frs | FRS_ID = ZaN_FrSID AND > 0 | FRS_Nazwa | 12022/12022 |
| CDN.KntKarty akw | Knt_GIDNumer = ZaN_AkwNumer AND > 0 | Knt_Akronim | 10649/12022 |

---

## Numeracja dokumentów (inline — bez CDN funkcji)

```sql
CASE n.ZaN_ZamTyp WHEN 1280 THEN 'ZS' WHEN 1152 THEN 'ZZ'
    WHEN 768 THEN 'OFS' WHEN 640 THEN 'OFZ' ELSE 'ZAM' END
+ '-' + CAST(n.ZaN_ZamNumer AS VARCHAR(10))
+ '/' + RIGHT('0' + CAST(n.ZaN_ZamMiesiac AS VARCHAR(2)), 2)
+ '/' + CAST(n.ZaN_ZamRok AS VARCHAR(4))
+ '/' + RTRIM(n.ZaN_ZamSeria)
-- Przykład: ZS-2/05/2023/PH_4
```

UWAGA: ERP_SCHEMA_PATTERNS.md ma błąd w tym wzorcu — podaje WHEN 960 zamiast WHEN 1280.
Zgłosić do usera po zakończeniu widoku.

---

## Pola wykluczone (potwierdzone)

- ZaN_GIDTyp, ZaN_GIDFirma, ZaN_GIDLp — stałe techniczne
- ZaN_DataAkceptacji, ZaN_PrjId — zawsze 0/puste
- ZaN_IncotermsSymbol — EXW dla 12021/12022 (prawie stała)
- ZaN_DokumentObcy — 1/12022 wypełnione
- ZaN_Aktywny, ZaN_DokZwiazane — is_useful=Nie
- ZaN_EAN — brak danych

---

## Pola do potwierdzenia przez usera (Faza 1)

- ZaN_CenaSpr — wartości 4, nieznane zastosowanie
- ZaN_ExpoNorm — wartości 1, nieznane zastosowanie
- ZaN_ZrdNumer — czy użyteczny (zawsze = GIDNumer?)
- Numer inline do weryfikacji wizualnej w SSMS

---

## Pliki

- Brudnopis: solutions/bi/Zamowienia/Zamowienia_draft.sql
- Plan: solutions/bi/Zamowienia/Zamowienia_plan.xlsx (135 wierszy)
- Plan SQL: solutions/bi/Zamowienia/Zamowienia_plan_src.sql

---

## Faza 2 — SQL (2026-03-09)

**Status:** Faza 2 ZAKOŃCZONA → czeka na akceptację usera

**Plik:** `solutions/bi/Zamowienia/Zamowienia_draft.sql`
**Eksport:** `solutions/bi/Zamowienia/Zamowienia_export.xlsx`
**Wynik:** 12034 wierszy ✓, 102 kolumny ✓

**JOINy w brudnopisie:**
- CDN.ZamNag zrd — self-join źródłowy (ZrdNumer != GIDNumer → aktualnie all NULL)
- CDN.KntKarty k/odb/plat/akw — kontrahent, odbiorca, płatnik, akwizytor
- CDN.KntAdresy kna/adw — adres kontrahenta, adres wysyłki
- CDN.Magazyny m/magd — magazyn, magazyn docelowy
- CDN.OpeKarty opew/opem/opez/opep/opemod/opepos — operatorzy (6 aliasów)
- CDN.FrmStruktura frs — firma handlowa
- CDN.PrcKarty prc — opiekun (GIDTyp=944)
- CDN.Rejestry rej — rejestr kasowy
- CDN.TwrCenyNag tcn — cennik (subquery MIN)
- CDN.Slowniki slw_fiask / slw_stat — fiasco + status realizacji

**Naprawione:**
- Cecha_Opis: NULLIF '<Nieokreślona>' (z polskim ś) — poprawiono

**Otwarte kwestie:**
- ZaN_PromocjePar=3 (3731 rek.) — oznaczone 'Nieznane (3)', czeka na weryfikację usera (przykłady: ZS-390/09/2024/SPKR)
- ZaN_DokZwiazane — bitmask surowy, prompt do researchera w toku

**Poprawki (2026-03-09 sesja 2):**
- Rok w numerze: RIGHT(CAST(ZamRok AS VARCHAR(4)),2) → format YY zgodny z ERP
- Stan 53: 'Anulowane (arch.+w real.)' → 'Zamknięte w realizacji'
- DokZwiazane: zostawiony jako surowy bitmask (brak możliwości empirycznego dekodowania)

**Status: Faza 4 — widok zapisany** `solutions/bi/views/Zamowienia.sql`
**Następny krok:** CREATE VIEW na DBA + otwarty temat ZaN_PromocjePar=3

---

## Status: Faza 4 — ZAKOŃCZONY. Widok zapisany, commit d2030d3, czeka na CREATE VIEW na DBA.

**Tabela główna:** CDN.KntKarty
**Filtr techniczny:** brak (pełny zbiór)
**Baseline:** COUNT(*) = 4530, COUNT(DISTINCT Knt_GIDNumer) = 4530 ✓

---

## Enumeracje rozkodowane

| Pole | Wartości | Źródło |
|---|---|---|
| Knt_GIDTyp | 32=Kontrahent (stała — pominięte) | CDN.Obiekty |
| Knt_Typ | 8=Dostawca, 16=Odbiorca, 24=Dostawco-Odbiorca, 0=Nieokreślono | dokumentacja |
| Knt_Status | 0=Nieokreślono, 1=Podmiot gospodarczy, 2=Odbiorca finalny | dokumentacja |
| Knt_Archiwalny | 0=Nie (2064), 1=Tak (2466) | baza |
| Knt_Dewizowe | 0=Nie (4527), 1=Tak (3) | baza |
| Knt_PlatnikVat | 0=Nie (2512), 1=Tak (2018) | baza |
| Knt_Akwizytor | 0=Nie, 1=Tak | dokumentacja |
| Knt_ExpoKraj | 1=krajowy, 2=z UE, 3=spoza UE | dokumentacja |
| Knt_LimitTerminowy | 0=nieograniczony, 1=ograniczony | dokumentacja |
| Knt_StanPostep | 0=brak, 1=w trakcie postępowania | dokumentacja |
| Knt_EFaVatAktywne | 0=Nie, 1=Tak | dokumentacja |
| Knt_Nieaktywny | zawsze 0 → pominięte | baza |
| Knt_Zrodlo | zawsze 0 → pominięte | baza |
| Knt_LimitWart | "Nie wykorzystane" wg dok. → pominięte | dokumentacja |
| Knt_KrajSiedziby | "Pole nie jest obsługiwane" → pominięte | dokumentacja |

---

## Typy dat — CZĘŚCIOWO NIEZNANE

### Potwierdzone — Clarion DATE (DATEADD(d, col, '18001228'))

| Pole | Min–Max | Wynik konwersji |
|---|---|---|
| Knt_LastModL | 1047823554–1141724389 | Clarion TIMESTAMP (DATEADD(ss, col, '1990-01-01')) |
| Knt_VatDataRejestracji | 70316–82184 | Clarion DATE ✓ |
| Knt_DataOdLoj | 81239–81239 | Clarion DATE ✓ |
| Knt_DataWydania | 81112–82156 | Clarion DATE ✓ |

### Nieznane / do wyjaśnienia — BLOKUJE BUDOWĘ SQL

| Pole | Min–Max | Uwaga |
|---|---|---|
| Knt_EFaVatDataDo | 81169–**150483** | 150483 wykracza poza typowy Clarion DATE (~70k–100k) |
| Knt_DataKarty | brak danych (0 rek. > 0) | nie można określić |
| Knt_FAVATData | brak danych (0 rek. > 0) | nie można określić |
| Knt_DataDoLoj | nie sprawdzono | — |
| Knt_DataPromocji | nie sprawdzono | opis: "wg daty: 1=Wystawienia, 2=Realizacji" (może flaga, nie data) |
| Knt_VatDataPrzywrocenia | nie sprawdzono | — |
| Knt_VatDataOdmowy | nie sprawdzono | — |
| Knt_VatDataUsuniecia | nie sprawdzono | — |

**Kluczowe pytanie:** wartość 150483 w Knt_EFaVatDataDo — czy to:
- Clarion DATE dalekiej przyszłości (np. sentinel "bez daty wygaśnięcia")?
- Inny format daty używany przez Comarch XL?
- Błąd w danych?

Odpowiedź z web research oczekiwana — patrz plik `Kontrahenci_date_research_prompt.md`.

---

## JOINy ustalone (każdy 4530/4530 ✓)

| JOIN | Klucz | Dane |
|---|---|---|
| CDN.OpeKarty o | o.Ope_GIDNumer = k.Knt_OpeNumer AND k.Knt_OpeNumer > 0 | Ope_Ident, Ope_Nazwisko (LEFT) |
| CDN.FrmStruktura frs | frs.FRS_ID = k.Knt_FrsID AND k.Knt_FrsID > 0 | FRS_Nazwa (LEFT) |

**Ważne rozróżnienia:**
- Knt_OpeNumer = operator zakładający kartę (NIE opiekun — opiekun jest w CDN.KntOpiekun)
- Knt_KnGNumer = GIDNumer kontrahenta-rodzica (self-join CDN.KntKarty, NIE ID grupy z KntGrupy)
- CDN.KntGrupy = bridge table przynależności do grup (KnG_GIDTyp=32 → membership, KnG_GIDTyp=-32 → definicja grupy)

---

## Pola wykluczone (potwierdzone)

- Knt_GIDTyp, Knt_GIDFirma, Knt_GIDLp — stałe techniczne
- Knt_Nieaktywny, Knt_Zrodlo — zawsze 0
- Knt_LimitWart — nieużywane wg dokumentacji
- Knt_DataW, Knt_DataUtworzenia — wszystkie NULL/0 w bazie
- Knt_KrajSiedziby — nieobsługiwane wg dokumentacji
- Knt_PrcTyp/Firma/Numer/Lp — nieobsługiwane (opiekun w CDN.KntOpiekun)
- Knt_Aktywna — nieużywane wg dokumentacji
- Knt_HasloChk, Knt_HasloKontrahent, Knt_PIN — dane wrażliwe
- Knt_Soundex, Knt_AkronimFormat, Knt_Wsk, Knt_OutlookUrl — techniczne/przestarzałe
- Knt_GUIDdane — duplikat GUID

---

## Odkrycia infrastrukturalne (sesja 2026-03-08)

**Bug docs_search naprawiony:** `docs_search "" --table CDN.X` zwracał [] bo pusta fraza
powodowała early return przed wykonaniem zapytania do bazy.
Naprawiono w `tools/docs_search.py` — dodano `_execute_table_scan` dla trybu phrase="" + table_filter.
Commit: `04344ce`. Testy: 19/19 ✓.

`docs.db` w katalogu głównym = pusty plik (0 bajtów, artefakt).
Właściwa baza: `erp_docs/index/docs.db` (7 MB, 214 kolumn CDN.KntKarty z opisami i sample_values).

---

## Pliki

- Brudnopis: `solutions/bi/Kontrahenci/Kontrahenci_draft.sql`
- Plan: `solutions/bi/Kontrahenci/Kontrahenci_plan.xlsx` (211 wierszy, opisy + sample_values z docs.db, komentarze usera)
- Prompt do researchu: `solutions/bi/Kontrahenci/Kontrahenci_date_research_prompt.md`
- Progress: `solutions/bi/Kontrahenci/Kontrahenci_progress.md`

---

## Faza 2 — Brudnopis SQL (2026-03-08)

**Plik:** `solutions/bi/Kontrahenci/Kontrahenci_draft.sql`
**Eksport:** `solutions/bi/Kontrahenci/Kontrahenci_export.xlsx`
**Wynik:** 4530 wierszy ✓, 151 kolumn ✓

**JOINy w brudnopisie:**
- CDN.KntAdresy a — adres powiązany (KnA_GIDNumer = Knt_KnANumer)
- CDN.Banki bnk — bank (Bnk_GIDNumer = Knt_BnkNumer)
- CDN.OpeKarty o — operator zakładający (Ope_GIDNumer = Knt_OpeNumer)
- CDN.OpeKarty om — operator modyfikujący (Ope_GIDNumer = Knt_OpeNumerM)
- CDN.FrmStruktura frs — firma handlowa (FRS_ID = Knt_FrsID)
- CDN.KntKarty akw — akwizytor self-join (Knt_GIDNumer = Knt_AkwNumer)
- CDN.KntKarty plat — płatnik self-join (Knt_GIDNumer = Knt_KnPNumer)
- CDN.Rejestry rej — rejestr kasowy (KAR_GIDNumer = Knt_KarNumer)
- CDN.KntGrupy kg — grupa (KnG_GIDNumer = Knt_KnGNumer WHERE KnG_GIDTyp=-32)

**Formy płatności:** CASE z kodami 0/10/20/50/100 (brak tabeli słownikowej w DB)
**Daty potwierdzone Clarion DATE:** VatDataRejestracji/Przywrocenia/Usuniecia, DataOdLoj, DataDoLoj, DataWydania
**Daty potwierdzone Clarion TIMESTAMP:** LastModL/O/C
**TODO:** Knt_EFaVatDataDo — wartość 150483 → CASE WHEN > 100000 THEN NULL (sentinel do weryfikacji)

**Pola puste (0 rek.) → pominięte:** FaVATOsw, MSTwrGrupaNumer, PodzialPlat, VatWalSys, ZTrNumer, OpZNumer, LastTransLockDate, FAVATData, DataKarty
**Knt_DataPromocji:** to flaga (1=Wystawienia, 2=Realizacji), nie data

---

## Faza 2 — Rewizja draftu (2026-03-08, sesja 2)

**BLOKADA: sql_client.py odrzuca WITH CTE** — walidator sprawdza `startswith("SELECT")` (sql_client.py:81). Rozwiązanie: poprawić walidator aby akceptował `WITH ... SELECT` lub przepisać CTE jako podzapytanie.

**Zmiany w tej sesji:**
- Pełny rewrite draftu: czytelne nazwy kolumn (usunięto skróty _Loj, _Spr, _Zak, _Ka, _Mod, _Zal, EFaVat_, FK)
- Dodano WITH CTE `Sciezka_Grup` — rekurencja po CDN.KntGrupy (KnG_GIDTyp=-32), ścieżka bez korzenia "Grupa Główna"
- Nowy JOIN: CDN.TwrCenyNag (tcn) → Nazwa_Cennika_Sprzedazy (MIN(TCN_Nazwa) GROUP BY TCN_RodzajCeny)
- Nowy JOIN: CDN.Slowniki (slw) → Rodzaj_Kontrahenta (SLW_WartoscS gdzie SLW_ID=Knt_Rodzaj)
- Knt_TypDok: CASE 0=Brak, 2033=Faktura sprzedaży, 2034=Paragon
- Knt_Dzialalnosc: pełny CASE (0–9) z dokumentacji
- Knt_ExpoKraj: CASE 1=Krajowy, 2=Z UE, 3=Spoza UE
- Knt_LimitTerminowy: CASE 0=Nieograniczony, 1=Ograniczony
- Knt_Rodzaj 800=Kontrahent (z Slowniki), 0=NULL
- Usunięto duplikat Knt_Dewizowe (zostaje CASE)
- Błąd w drafcie: `k.Knt_KnGNumer AS ID_Rodzaju_Kontrahenta` — POWINNO BYĆ `k.Knt_Rodzaj AS ID_Rodzaju_Kontrahenta` — DO POPRAWY

**Odkrycia o cennikach (CDN.TwrCenyNag):**
- Knt_Cena = TCN_RodzajCeny (nie TCN_Id)
- Wartości: 1=CENA 100, 2=CMENTARZ, 3=FRANOWO, 4=BRICO, 5=INTER, 6=mrówka, 7=CHATA POLSKA, 8=AT, 9=PRYZMAT
- Wiele rekordów per TCN_RodzajCeny → używamy MIN(TCN_Nazwa) GROUP BY

**Struktura grup KntGrupy (KnG_GIDTyp=-32):**
- Korzeń: GIDNumer=0, GrONumer=-1, Akronim="Grupa Główna"
- Poziom 1 (GrONumer=0): 01.KLIENCI(5), 02.DOSTAWCY(11), 03.HANDLOWCY(2319), 04.AKWIZYTORZY(18)
- 01.KLIENCI ma dzieci: 01.DETAL(9), 02.DETAL+(2), 03.HURT(3), 04.CENTRALA(6), 05.BRICO(4), etc.
- CTE startuje od GrONumer=0 (pomija "Grupa Główna")
- 13 rekordów Knt_KnGNumer=0 → brak przypisania do grupy → NULL w Sciezka_Grupy

---

## Faza 3 — Weryfikacja exportu (2026-03-08, sesja 3)

**Export:** `solutions/bi/Kontrahenci/Kontrahenci_export.xlsx`
**Wynik:** 4530 wierszy ✓, 151 kolumn ✓, arkusze: Plan / Wynik / Surówka

**Naprawione w tej sesji:**
- `sql_client.py` — walidator akceptuje WITH...SELECT (CTE); inject_top pomijany dla WITH
- Bug: `k.Knt_KnGNumer AS ID_Rodzaju_Kontrahenta` → `k.Knt_Rodzaj AS ID_Rodzaju_Kontrahenta`

**Weryfikacja statystyk:**
- Typ: 4 wartości (Odbiorca/Dostawca/Dostawca-Odbiorca/Nieokreślono) ✓
- Status: 3 wartości ✓ | Platnik_VAT: Tak/Nie ✓ | Archiwalny: Tak/Nie ✓
- Eksport_Rodzaj: 4 wartości (Krajowy/Z UE/Spoza UE/Nieokreślono) ✓
- Sciezka_Grupy: 16 distinct, 4514 NULL (brak przypisania do grupy) ✓
- Data_Ostatniej_Modyfikacji: format datetime 2024–2025 ✓
- EFaktura_VAT_Data_Waznosci: sentinel >109211 → NULL, 6 realnych dat ✓
- Rodzaj_Kontrahenta: "Kontrahent" (słownik CDN.Slowniki) ✓
- Brak "Nieznane" w żadnej enumeracji ✓

---

## Faza 3 — Rewizja grup (2026-03-08, sesja 4)

**Problem:** `CDN.KntGrupy` (type=32) zawiera WSZYSTKIE grupy kontrahenta (bridge table) — 5651 rekordów dla 4530 kontrahentów → JOIN mnożył wiersze.

**Rozwiązanie:** `CDN.KntGrupyDom` — osobna tabela z grupą główną (JEDENA per kontrahent):
- `KntGrupyDom` type=32: 4530 rekordów, `KGD_GIDNumer = Knt_GIDNumer`
- `KGD_GrONumer` → wskazuje na grupę w type=-32 (definicje hierarchii)
- CTE zbudowany z `CDN.KntGrupyDom` (type=-32), separator `\`
- JOIN: `kgd ON KGD_GIDNumer = k.Knt_GIDNumer AND KGD_GIDTyp = 32` → `sg ON KGD_GIDNumer = kgd.KGD_GrONumer`

**Wynik:** 4530 wierszy ✓, 26 distinct ścieżek, 656 NULL (brak grupy głównej), separator `\`

**Usunięto:** `ID_Rodzaju_Kontrahenta` (niepotrzebne — mamy `Rodzaj_Kontrahenta`)

**Następny krok:** CREATE OR ALTER VIEW BI.Kontrahenci wykonać na DBA (plik: solutions/bi/views/Kontrahenci.sql)


---

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


---

Sesja 2026-03-12: widok Rozrachunki.sql — otwarte: Stan&2 wymaga korekty, priorytet GenDokMag wyzszy.
