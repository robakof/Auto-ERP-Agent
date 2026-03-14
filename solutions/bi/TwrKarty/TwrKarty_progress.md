## Status: Faza 1 — Plan do zatwierdzenia

**Tabela główna:** CDN.TwrKarty (Karty Towarów), 10 123 rekordów total
**Filtr:** WHERE Twr_GIDNumer > 0 (pomija 1 rekord techniczny GIDNumer=0)
**Baseline:** COUNT(*) = 10 122, COUNT(DISTINCT Twr_GIDNumer) = 10 122 ✓

**Struktura tabeli:** 195 kolumn CDN + 5 kolumn z JOINów = 200 wierszy w planie
**Stałe (distinct=1, SKIP):** ~140 kolumn
**Uwzględnić w widoku:** ~40 kolumn

**Kluczowe obserwacje z discovery:**
- Twr_Aktywna = zawsze 0 — ANOMALIA. Faktyczny status: Twr_Archiwalny (0=aktywny, 1=archiwalny)
- Twr_Zakup, Twr_Sprzedaz = zawsze 0 — nieużywane
- Twr_Typ enum: 1=Towar, 2=Produkt, 3=Koszt, 4=Usługa, 6=? (nieznana wartość)
- Twr_LastModL/O/C, Twr_DataUtworzenia = Clarion TIMESTAMP (DATEADD ss od 1990-01-01)

**JOINy zaplanowane:**
- CDN.OpeKarty (Ope_GIDNumer) × 2 — operator tworzący (OpeNumer) + modyfikujący (OpeNumerM)
- CDN.Magazyny (Mag_GIDNumer) — magazyn domyślny (MagNumer, 5 wartości: 1,4,5,9,10)
- CDN.KntKarty (Knt_GIDNumer) — producent (PrdNumer, FK do Kontrahenta GIDTyp=32)
- CDN.TwrGrupyDom — grupy domowe (TGD_GIDTyp=16 przypisania, TGD_GIDTyp=-16 definicje)

**Enumeracje do zbadania (brak pełnego CASE):**
- Twr_Typ wartość 6 — nieznana (docs mówi 1-4, w bazie jest też 6)
- Twr_JmFormat (0,2,3,4) — znaczenie nieznane
- Twr_CenaSpr (1,3,6) — typ ceny sprzedaży
- Twr_DstDomyslny (0,1,2,3,4) — typ domyślnego dostawcy
- Twr_KosztUTyp (0,1) — typ kosztu
- Twr_PIADostepnoscFlaga (0,8) — flaga PIA
- Twr_DodEleZez (0,1,2) — elementy zezwolenia

**Pliki:**
- Plan: solutions/bi/TwrKarty/TwrKarty_plan.xlsx
- Plan src: solutions/bi/TwrKarty/TwrKarty_plan_src.sql
- Brudnopis: solutions/bi/TwrKarty/TwrKarty_draft.sql (NIE ISTNIEJE — po zatwierdzeniu planu)

**Następny krok:**
1. User zatwierdza plan (Komentarz_Usera w xlsx)
2. Zbadać Twr_Typ=6 w bazie (ile rekordów, jakie towary)
3. Sprawdzić schemat CDN.Magazyny (kolumna Mag_GIDNumer i Mag_Nazwa)
4. Napisać draft.sql po zatwierdzeniu planu
