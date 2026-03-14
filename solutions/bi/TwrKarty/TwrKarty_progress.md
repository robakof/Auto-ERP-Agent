## Status: Faza 2 — Draft SQL gotowy, zweryfikowany

**Tabela główna:** CDN.TwrKarty (Karty Towarów)
**Filtr:** WHERE Twr_GIDNumer > 0
**Baseline:** COUNT(*) = 10 122, COUNT(DISTINCT) = 10 122 ✓

**Kolumny w widoku:** 64
**Status:** SQL poprawny, eksport zweryfikowany, brak błędów

---

### Enumeracje rozkodowane

- `Twr_Typ`: 1=Towar, 2=Produkt, 3=Koszt, 4=Usługa (wartość 6 — 0 rekordów, ELSE fallback)
- `Twr_JmFormat`: liczba miejsc po przecinku (numeric, bez CASE)
- `Twr_CenaSpr`: kanał sprzedaży przez CASE z TwrCenyNag (1=CENA 100, 2=CMENTARZ, 3=FRANOWO, 4=BRICO, 5=INTER, 6=MRÓWKA, 7=CHATA POLSKA, 8=AT, 9=PRYZMAT)
- `Twr_PIADostepnoscFlaga`: bitmask (0=Brak, 8=Mobilny Sprzedawca, ELSE Kombinacja)
- `Twr_DodEleZez`: 0=Nie, wartości 1 i 2 nieznane (ELSE fallback)
- `Twr_Archiwalny`: 0=Aktywny, 1=Archiwalny (nie: Tak/Nie)
- `Twr_CCKNumer`: 0=Brak, 1=Partia (JOIN CDN.CechyKlasy GIDTyp=192)
- `TGD_GIDTyp=-16`: potwierdzone w CDN.Obiekty — "Grupa towarów"

### JOINy wdrożone

- `CDN.OpeKarty` ×2 — operator tworzący (OpeNumer) + modyfikujący (OpeNumerM)
- `CDN.Magazyny` — magazyn domyślny (MAG_GIDNumer, 0 NULLs)
- `CDN.KntKarty knt_prd` — producent (PrdNumer, GIDTyp=Twr_PrdTyp, 8254 NULLs)
- `CDN.TwrGrupyDom` ×2 — przypisanie (GIDTyp=16) + definicja grupy (GIDTyp=-16)
- `CDN.TwrJm` — domyślna JM dodatkowa (JmDomyslna jako Lp; 0=fallback Twr_Jm)
- `CDN.TwrDost` + `CDN.KntKarty knt_dst` — domyślny dostawca (DstDomyslny jako Lp, 9896 NULLs)
- `CDN.CechyKlasy` — klasa cechy (CCKNumer, GIDTyp=192)

### Pliki

- Brudnopis: `solutions/bi/TwrKarty/TwrKarty_draft.sql`
- Plan: `solutions/bi/TwrKarty/TwrKarty_plan.xlsx`
- Eksport: `solutions/bi/TwrKarty/TwrKarty_export.xlsx`

### Następny krok

Akceptacja usera → Faza 4: CREATE OR ALTER VIEW BI.TwrKarty + commit
