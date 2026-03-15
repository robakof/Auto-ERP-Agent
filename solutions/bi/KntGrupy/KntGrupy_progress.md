## Status: Faza 2 — draft gotowy, czeka na recenzję Analityka

**Tabela główna:** CDN.KntGrupy, GIDTyp=32 (bridge kontrahent→grupa ogólna)

**Baseline:** COUNT(*) = 5 669, COUNT(DISTINCT KnG_GIDNumer) = 4 545

**JOINy ustalone:**
- CDN.KntKarty — LEFT JOIN na Knt_GIDNumer = KnG_GIDNumer — akronim i nazwa kontrahenta
- CDN.KntGrupy (GIDTyp=-32) — LEFT JOIN na KnG_GIDNumer = br.KnG_GrONumer — kod grupy

**Pominięte (uzasadnione):**
- KnG_GIDFirma, KnG_GIDLp, KnG_GrOTyp, KnG_GrOFirma, KnG_GrOLp — GID components
- KnG_SyncId — techniczne
- KnG_OpeNumer — techniczne (bez JOIN OpeKarty)

**Daty:** Clarion TIMESTAMP (~1e9)
- KnG_CzasModyfikacji → Data_Modyfikacji (0 NULLi)
- KnG_CzasZalozenia → Data_Zalozenia (3 121 NULLi — CzasZalozenia=0 dla starych rekordów)

**Uwaga:** KntGrupy ma tylko KnG_Akronim dla grupy (brak Nazwa). Kod_Grupy = akronim grupy.

**Pliki:**
- Brudnopis: solutions/bi/KntGrupy/KntGrupy_draft.sql
- Plan: solutions/bi/KntGrupy/KntGrupy_plan.xlsx
- Verify export: exports/KntGrupy_verify_*.xlsx

**Następny krok:** czekam na recenzję Analityka (wiadomość agent_bus id=45)
