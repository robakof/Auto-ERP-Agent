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