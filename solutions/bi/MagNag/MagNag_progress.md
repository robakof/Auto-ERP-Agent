## Status: Faza 3 zatwierdzona — czeka na Fazę 4 (DBA)

**Tabela główna:** CDN.MagNag
**Baseline:** COUNT(*) = 199 862, COUNT(DISTINCT GIDNumer) = 199 862 — brak duplikatów
**Filtr techniczny:** brak

**Typy dokumentów (GIDTyp):**
- 1089: PM — Przyjęcie magazynowe (13 rek.)
- 1093: AWD — Awizo dostawy (31 608 rek.)
- 1601: WM — Wydanie magazynowe (54 rek.)
- 1605: ZWM — Zlecenie wydania z magazynu (168 187 rek.)

**Daty:**
- MaN_Data3: Clarion DATE → DATEADD(d, col, '18001228') → Data_Wystawienia
- MaN_DataZatwierdzenia: Clarion DATE → Data_Zatwierdzenia (0=NULL)
- MaN_DataOd, MaN_DataDo, MaN_LastMod: Clarion TIMESTAMP → DATEADD(ss, col, '1990-01-01')

**Enumeracje rozkodowane:**
- MaN_GIDTyp: 1089=PM, 1093=AWD, 1601=WM, 1605=ZWM (obiekty.tsv)
- MaN_Stan: 0=W edycji, 1=W buforze, 2=Po edycji, 5=Zatwierdzona, 6=Anulowana (docs)
- MaN_Status: 0=Niezatwierdzony, 1=Zatwierdzony, 2=W realizacji, 3=Zrealizowany, 4=Zamknięty, 5=Zamknięty bez realizacji, 6=Zamknięty do edycji (docs)
- MaN_TrNTyp: 8=Wydanie (WM+ZWM), 9=Przyjęcie (PM+AWD) — korelacja, nie dokumentacja
- MaN_WMS: 0=Nie, 177=Tak — jedyna niezerowa wartość
- MaN_Zrodlo: 0=Niepowiązany, 1=Powiązany, 2=Powiązany wielokrotnie (docs)
- MaN_ZrdTyp: 21 typów z TraNag/ZamNag (obiekty.tsv) — wszystkie zidentyfikowane
- MaN_Priorytet: 0/20/30 — brak opisu w dokumentacji, zachowane raw

**Numeracja:** SKRÓT-Nr/MM/YY[/Seria] — skróty z obiekty.tsv (PM/AWD/WM/ZWM) ✓

**JOINy zweryfikowane (COUNT 100%):**
- CDN.Magazyny mag_trm ON MAG_GIDNumer = MaN_TrMNumer ✓
- CDN.Magazyny mag_d ON MAG_GIDNumer = MaN_MagDNumer ✓
- CDN.KntKarty knt ON Knt_GIDNumer = MaN_KntNumer AND Knt_GIDTyp = MaN_KntTyp (warunek KntNumer>0) ✓
- CDN.OpeKarty ope ON Ope_GIDNumer = MaN_OpeNumer ✓
- CDN.OpeKarty ope_r ON Ope_GIDNumer = MaN_OpeNumerR (warunek >0) ✓
- CDN.OpeKarty ope_m ON Ope_GIDNumer = MaN_OpeNumerM (warunek >0) ✓
- CDN.FrmStruktura frs ON FRS_ID = MaN_FrsID ✓
- CDN.KntAdresy kna ON KnA_GIDNumer = MaN_KnANumer AND KnA_GIDTyp = MaN_KnATyp (warunek >0) — 167232=167232 ✓
- CDN.ZamNag zan ON ZaN_GIDNumer = MaN_ZaNNumer (warunek >0) — 10315=10315 ✓
- CDN.TraNag zrd + CDN.ZamNag zrd_zan per MaN_ZrdTyp (do Nr_Dokumentu_Zrodlowego) — planowany

**Kluczowe nazwy kolumn:**
- CDN.Magazyny: MAG_Kod, MAG_Nazwa
- CDN.KntKarty: Knt_Akronim, Knt_Nazwa1
- CDN.OpeKarty: Ope_Ident (nie Ope_Kod — nie istnieje)
- CDN.FrmStruktura: FRS_ID, FRS_Nazwa
- CDN.KntAdresy: KnA_GIDNumer, KnA_GIDTyp, KnA_Akronim
- CDN.ZamNag numeracja: ZaN_ZamNumer, ZaN_ZamMiesiac, ZaN_ZamRok, ZaN_ZamSeria

**Pominięcia COUNT DISTINCT=1:** MaN_TrMTyp, MaN_MagDTyp, MaN_OpeLpR, MaN_OpeLpM, MaN_TypZrd, MaN_SpeNumer, MaN_TrasaId

**Historia recenzji:**
- Iteracja 1 (msg 126): BLOCKED — 10 punktów (brak kolumn opisowych dla ID_XXX, KntAdresy nie zbadana)
- Iteracja 2 (msg 128): wysłana — wszystkie 10 BLOCKING zaadresowane
- Iteracja 3 (msg 130): wysłana — BLOCKING Nr_Zamowienia (hardkodowany 'ZS-' → CASE ZaN_ZamTyp)

**Uwaga techniczna:** MagNag_plan_src.sql używa formatu VALUES (SQL Server). bi_plan_generate.py (SQLite) go nie obsługuje — używaj excel_export.py do generowania planu Excel.

**Pliki:**
- Brudnopis: solutions/bi/MagNag/MagNag_draft.sql
- Plan src: solutions/bi/MagNag/MagNag_plan_src.sql
- Plan Excel: solutions/bi/MagNag/MagNag_plan.xlsx (91 wierszy)
- Progress: solutions/bi/MagNag/MagNag_progress.md

- Iteracja 3 zatwierdzona (msg 131) ✓

**Faza 2 zakończona:**
- Draft: solutions/bi/MagNag/MagNag_draft.sql (44 kolumny)
- Eksport próbkowy: solutions/bi/MagNag/MagNag_export.xlsx (TOP 100 000)
- Row count: 199 893 = 199 893 DISTINCT (brak mnożenia); baseline 199 862 (+31 = wyścig czasowy)
- Self-check: brak "Nieznane" w enumeracjach ✓
- Wysłany do Analityka (msg 132)

- Faza 3 zatwierdzona (msg 136) ✓

**Następny krok: Faza 4**
1. python tools/solutions_save_view.py --draft solutions/bi/MagNag/MagNag_draft.sql
2. agent_bus flag → DBA do wdrożenia (solutions/bi/views/MagNag.sql)
3. Po wdrożeniu: bi_catalog_add.py --view AIBI.MagNag --add
4. git_commit.py --message "feat: widok BI AIBI.MagNag" --all --push
