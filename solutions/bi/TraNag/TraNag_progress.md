## Status: Faza 2 — uzupelnienia v2 w toku, eksport NIE wykonany

**Tabela główna:** CDN.TraNag
**Baseline:** COUNT(*) = 224 000 (rośnie w czasie sesji — baza produkcyjna)

---

## Co zostało zrobione w tej sesji

1. Draft v1 (68 kolumn) — zatwierdzony przez Analityka (msg id=64, 2026-03-15 11:51)
2. User zażądał 5 uzupełnień:
   - Numer_Dok_Korygowanego (self-join CDN.TraNag jako `zwrot`)
   - Adres_Kontrahenta (CDN.KntAdresy kna_k)
   - Adres_Wysylki (CDN.KntAdresy kna_w)
   - Numer_Zamowienia (CDN.ZamNag zam, format ZS-N/MM/YY/Seria)
   - Nazwa_Cennika (CDN.TwrCenyNag CTE CenBase — MIN(TCN_Id) per TCN_RodzajCeny)
3. Draft v2 zapisany: solutions/bi/TraNag/TraNag_draft.sql
4. COUNT(*) draftu v2 = 224 000 = baseline (JOINy nie mnożą) ✓
5. Eksport v2 NIE wykonany — sesja przerwana z powodu limitu kontekstu

---

## Odchylenia od planu (zatwierdzone przez usera)

- Akwizytor_Login → Akwizytor_Akronim
  Plan: OpeKarty/typ128 — typ 128 nie wystepuje w danych
  Dane: TrN_AkwTyp=32 (48461, KntKarty), TrN_AkwTyp=944 (2, PrcKarty)
  Impl: COALESCE(akw_knt.Knt_Akronim, akw_prc.Prc_Akronim)

---

## Nowe JOINy w v2

| Alias | Tabela | Warunek |
|-------|--------|---------|
| zwrot | CDN.TraNag | zwrot.TrN_GIDNumer = n.TrN_ZwrNumer AND n.TrN_ZwrNumer > 0 |
| kna_k | CDN.KntAdresy | kna_k.KnA_GIDNumer = n.TrN_KnANumer AND n.TrN_KnANumer > 0 |
| kna_w | CDN.KntAdresy | kna_w.KnA_GIDNumer = n.TrN_AdWNumer AND n.TrN_AdWNumer > 0 |
| zam   | CDN.ZamNag    | zam.ZaN_GIDNumer = n.TrN_ZaNNumer AND n.TrN_ZaNNumer > 0 |
| CenBase (CTE) | CDN.TwrCenyNag | TCN_RodzajCeny = n.TrN_CenaSpr AND n.TrN_CenaSpr > 0 |

Numer_Dok_Korygowanego: bez prefiksu (Z) — wymagalby kolejnego EXISTS subquery.
Obejmuje tylko (A)/(s) z GenDokMag.

---

## Uwaga o eksporcie (ważne dla następnego agenta)

Przy 224k wierszach Excel się zacina. Zamiast pelnego eksportu uzyj:
```
python tools/sql_query.py --file solutions/bi/TraNag/TraNag_export_sample.sql --export solutions/bi/TraNag/TraNag_export.xlsx
```
Plik TraNag_export_sample.sql = TOP 100000 ORDER BY ID_Dokumentu DESC z pelnym draftem.
Suggest do busa id=32 — Developer ma dodac --limit N do sql_query.py --export.

---

## Następny krok dla kolejnego agenta

1. Wykonaj eksport przez TraNag_export_sample.sql (nie draft bezposrednio)
2. Zweryfikuj nowe kolumny: Numer_Dok_Korygowanego, Adres_Kontrahenta, Adres_Wysylki, Numer_Zamowienia, Nazwa_Cennika
3. Wyslij eksport do Analityka (Faza 3 ponowna — zmiana zakresu)
4. Po zatwierdzeniu: solutions_save_view.py + agent_bus flag dla DBA

---

## Wiadomosci agent_bus z tej sesji

- id=62: erp_specialist → developer — Komentarz_Usera mylaaca nazwa kolumny
- id=63: erp_specialist → analyst — eksport v1 gotowy (ZDEZAKTUALIZOWANY — v2 w toku)
- id=64: analyst → erp_specialist — zatwierdzam eksport v1 (odczytana)
- id=65: flag — DBA do wdrozenia (PRZEDWCZESNY — widok v2 jeszcze nie gotowy)
- id=66: erp_specialist → analyst — uzupelnienia v2 + pytanie o wytyczne

---

## Pliki

- Brudnopis v2: solutions/bi/TraNag/TraNag_draft.sql (CTE + 5 nowych kolumn)
- Eksport sample: solutions/bi/TraNag/TraNag_export_sample.sql (TOP 100k)
- Plan: solutions/bi/TraNag/TraNag_plan.xlsx
- Eksport: solutions/bi/TraNag/TraNag_export.xlsx (STARY — v1, 68 kolumn)
