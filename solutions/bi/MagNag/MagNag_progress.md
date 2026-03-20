## Status: Faza 1b — czeka na recenzję Analityka

**Tabela główna:** CDN.MagNag
**Baseline:** COUNT(*) = 199 862, COUNT(DISTINCT) = 199 862 — brak duplikatów
**Filtr techniczny:** brak (wszystkie rekordy)

**Typy dokumentów (GIDTyp):**
- 1089: PM — Przyjęcie magazynowe (13 rek.)
- 1093: AWD — Awizo dostawy (31 608 rek.)
- 1601: WM — Wydanie magazynowe (54 rek.)
- 1605: ZWM — Zlecenie wydania z magazynu (168 187 rek.)

**Daty:**
- MaN_Data3: Clarion DATE → DATEADD(d, col, '18001228') → Data_Wystawienia
- MaN_DataZatwierdzenia: Clarion DATE → Data_Zatwierdzenia
- MaN_DataOd, MaN_DataDo, MaN_LastMod: Clarion TIMESTAMP → DATEADD(ss, col, '1990-01-01')

**Enumeracje rozkodowane:**
- MaN_GIDTyp: 1089=PM, 1093=AWD, 1601=WM, 1605=ZWM (obiekty.tsv)
- MaN_Stan: 0=W edycji, 1=W buforze, 2=Po edycji, 5=Zatwierdzona, 6=Anulowana (docs)
- MaN_Status: 0-6 per dokumentacja
- MaN_TrNTyp: 8=Wydanie, 9=Przyjęcie (korelacja z GIDTyp; @S3 — do potwierdzenia przez Analityka)
- MaN_WMS: 0=Nie, 177=Tak (do potwierdzenia przez Analityka)
- MaN_Zrodlo: 0=Niepowiązany, 1=Powiązany, 2=Wielokrotnie (docs)
- MaN_ZrdTyp: 21 typów z TraNag/ZamNag (obiekty.tsv)
- MaN_Priorytet: 0/20/30 — brak opisu w dokumentacji

**Numeracja:** SKRÓT-Nr/MM/YY[/Seria] — skróty z obiekty.tsv ✓

**JOINy zweryfikowane:**
- CDN.Magazyny (TrMNumer + MagDNumer) — 100%
- CDN.KntKarty (KntNumer+KntTyp) — 100%
- CDN.OpeKarty (OpeNumer, OpeNumerR, OpeNumerM) — 100%
- CDN.FrmStruktura (FrsID) — 100%

**Pominięcia COUNT DISTINCT=1:** MaN_TrMTyp, MaN_MagDTyp, MaN_OpeLpR, MaN_OpeLpM, MaN_TypZrd, MaN_SpeNumer, MaN_TrasaId

**Otwarte pytania (dla Analityka):**
1. MaN_TrNTyp etykiety (8/9) — potwierdzenie korelacyjnych label
2. MaN_WMS=177 — potwierdzenie jako Tak
3. MaN_Priorytet 0/20/30 — czy znane znaczenie?
4. MaN_KnANumer — czy CDN.KntAdresy ma kolumnę opisową?

**Pliki:**
- Brudnopis: solutions/bi/MagNag/MagNag_draft.sql
- Plan src: solutions/bi/MagNag/MagNag_plan_src.sql
- Plan Excel: solutions/bi/MagNag/MagNag_plan.xlsx
- Progress: solutions/bi/MagNag/MagNag_progress.md

**Następny krok:** Czekam na recenzję Analityka (agent_bus msg id=126)
