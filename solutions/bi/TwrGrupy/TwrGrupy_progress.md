## Status: Faza 2 — draft gotowy, czeka na recenzję Analityka

**Tabela główna:** CDN.TwrGrupy, GIDTyp=16 (bridge towar→grupa ogólna)

**Baseline:** COUNT(*) = 13 817, COUNT(DISTINCT TwG_GIDNumer) = 10 123

**JOINy ustalone:**
- CDN.TwrKarty — LEFT JOIN na Twr_GIDNumer = TwG_GIDNumer — kod i nazwa towaru
- CDN.TwrGrupy (GIDTyp=-16) — LEFT JOIN na TwG_GIDNumer = br.TwG_GrONumer — kod i nazwa grupy

**Pominięte (uzasadnione):**
- TwG_GIDFirma, TwG_GIDLp, TwG_GrOTyp, TwG_GrOFirma, TwG_GrOLp — GID components
- TwG_SyncId — techniczne
- TwG_KategoriaBIId — COUNT DISTINCT = 1 (wartość 0)

**Data:** TwG_CzasModyfikacji — Clarion TIMESTAMP (~1e9), konwersja: DATEADD(ss, val, '1990-01-01')

**Pliki:**
- Brudnopis: solutions/bi/TwrGrupy/TwrGrupy_draft.sql
- Plan: solutions/bi/TwrGrupy/TwrGrupy_plan.xlsx
- Verify export: exports/TwrGrupy_verify_*.xlsx

**Następny krok:** czekam na recenzję Analityka (wiadomość agent_bus id=45)
