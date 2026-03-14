## Status: Faza 3 — Draft finalny, gotowy do Fazy 4 (CREATE VIEW)

**Tabela główna:** CDN.TwrKarty (Karty Towarów)
**Filtr:** WHERE Twr_GIDNumer > 0
**Baseline:** COUNT(*) = 10 122, COUNT(DISTINCT) = 10 122 ✓
**Kolumny w widoku:** 65
**Brudnopis:** `solutions/bi/TwrKarty/TwrKarty_draft.sql`
**Kolumny w widoku:** 66
**Eksport:** `solutions/bi/TwrKarty/TwrKarty_export.xlsx` (zamknij przed nowym eksportem)

---

### Stan draftu (finalny)

Wszystkie enumeracje, JOINy i ścieżki grup wdrożone i zweryfikowane.
Decyzje usera podjęte i wdrożone:
- `Techniczna_Dec1` — zostawiona as-is z komentarzem SQL ("anomalia — docs mówią że puste")
- `MRP_Id` — JOIN do CDN.ProdOkresy (POK_Id), dodana kolumna `MRP_Okres_Data` (POK_DataOd → Clarion DATE)

---

### Enumeracje rozkodowane

- `Twr_Typ`: 1=Towar, 2=Produkt, 3=Koszt, 4=Usługa (wartość 6 — ELSE fallback, 0 rekordów)
- `Twr_CenaSpr`: kanał sprzedaży — CASE z TwrCenyNag (1=CENA 100, 2=CMENTARZ, 3=FRANOWO, 4=BRICO, 5=INTER, 6=MRÓWKA, 7=CHATA POLSKA, 8=AT, 9=PRYZMAT)
- `Twr_PIADostepnoscFlaga`: bitmask (0=Brak, 8=Mobilny Sprzedawca, ELSE Kombinacja)
- `Twr_DodEleZez`: 0=Nie, wartości 1 i 2 — ELSE fallback (79 rekordów z wartością 2)
- `Twr_Archiwalny`: 0=Aktywny, 1=Archiwalny
- `Twr_CCKNumer`: 0=Brak, 1=Partia (JOIN CDN.CechyKlasy GIDTyp=192; kolumna ID_Klasy_Cechy USUNIĘTA)

### JOINy wdrożone

- `CDN.OpeKarty` ×2 — operator tworzący + modyfikujący
- `CDN.Magazyny` — magazyn domyślny (5 distinct, 0 NULLs)
- `CDN.KntKarty knt_prd` — producent (GIDTyp=Twr_PrdTyp, 8254 NULLs)
- `CDN.TwrGrupyDom` + CTE rekurencyjne `Sciezka_Grup_Twr` — pełna ścieżka grupy domowej (3 poziomy, separator \, np. `01_CMENTARZ\1_ZNICZE\3_ŚREDNIE`)
- `CDN.TwrJm` ×4 — JM_Domyslna_Symbol, JM_Domyslna_Zakup_Symbol, JM_Mobile_Sprzedaz_Symbol, JM_Dopelniania_Mobile_Symbol
- `CDN.TwrDost` + `CDN.KntKarty knt_dst` — domyślny dostawca (9896 NULLs)
- `CDN.CechyKlasy` — klasa cechy (GIDTyp=192)
- `CDN.TwrCenyNag` — NIE użyty (CASE zamiast JOIN — wiele wersji cennika per kanał)

### Poprawki analityka z recenzji (wdrożone)

- `Autonumeracja_Kod` — USUNIĘTA (99% NULLs)
- `Data_Modyfikacji_O` — USUNIĘTA (≈ duplikat DataUtworzenia, 1 rekord różny)
- JM symbole dla JM_Domyslna_Zakup, JM_Mobile_Sprzedaz, JM_Dopelniania_Mobile — DODANE

### Następny krok

Faza 4: `CREATE OR ALTER VIEW BI.TwrKarty` + commit
