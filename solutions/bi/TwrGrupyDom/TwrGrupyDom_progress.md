## Status: Faza 1 — Plan mapowania (czeka na zatwierdzenie)

**Tabela główna:** CDN.TwrGrupyDom (GIDTyp=16 — przypisania towar-grupa)

**Baseline:** COUNT(*) = 10122 (po wykluczeniu TGD_GIDNumer=0 — 1 rekord techniczny), COUNT(DISTINCT TGD_GIDNumer) = 10122 ✓

**Struktura tabeli:**
- TGD_GIDTyp: -16 = definicje grup (hierarchia, 202 węzłów), 16 = przypisania towar-grupa (10123 rek.)
- TGD_GIDNumer (type=16) = Twr_GIDNumer (ID towaru) — klucz JOIN z AIBI.TwrKarty
- TGD_GrONumer (type=16) = ID grupy bezpośredniej w hierarchii (type=-16)
- TGD_Kod (type=16) = duplikat Twr_Kod — redundant, pominięty

**Kolumny techniczne (pominięte):**
- TGD_GIDTyp, TGD_GIDFirma, TGD_GIDLp — stałe
- TGD_GrOTyp, TGD_GrOFirma, TGD_GrOLp — stałe
- TGD_Kod — redundant z Twr_Kod

**JOINy ustalone:**
- CDN.TwrGrupyDom grp (GIDTyp=-16) — Kod_Grupy bezpośredniej
- Recursive CTE Sciezka_Grup (wzorzec z TwrKarty) — Sciezka_Grupy, Poziom_Grupy

**Kolumny widoku (propozycja, 4 kolumny):**
1. ID_Towaru (TGD_GIDNumer)
2. ID_Grupy (TGD_GrONumer)
3. Kod_Grupy (via JOIN type=-16)
4. Sciezka_Grupy (via CTE)
5. Poziom_Grupy (via CTE)

**Pliki:**
- Plan: solutions/bi/TwrGrupyDom/TwrGrupyDom_plan.xlsx
- Brudnopis: (do utworzenia po zatwierdzeniu planu)

**Następny krok:** Zatwierdzenie planu przez usera → Faza 2 (draft SQL)
