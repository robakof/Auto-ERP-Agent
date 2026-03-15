## Status: Faza 3 — eksport v2 wysłany do Analityka, czeka na zatwierdzenie

**Tabela główna:** CDN.TraNag
**Baseline:** COUNT(*) = 224 002 (rośnie w czasie sesji — baza produkcyjna)

---

## Co zostało zrobione

1. Draft v1 (68 kolumn) — zatwierdzony przez Analityka (msg id=64, 2026-03-15 11:51)
2. User zażądał 5 uzupełnień:
   - Numer_Dok_Korygowanego (self-join CDN.TraNag jako `zwrot`)
   - Adres_Kontrahenta (CDN.KntAdresy kna_k)
   - Adres_Wysylki (CDN.KntAdresy kna_w)
   - Numer_Zamowienia (CDN.ZamNag zam, format ZS-N/MM/YY/Seria)
   - Nazwa_Cennika (CDN.TwrCenyNag CTE CenBase — MIN(TCN_Id) per TCN_RodzajCeny)
3. Draft v2 zapisany: solutions/bi/TraNag/TraNag_draft.sql (73 kolumny)
4. COUNT(*) draftu v2 = 224 002 = baseline (JOINy nie mnożą) ✓
5. Eksport v2 wykonany: solutions/bi/TraNag/TraNag_export_v2.xlsx (TOP 100k)
6. Wysłano do Analityka (msg id=70, 2026-03-15) — czeka na zatwierdzenie Fazy 3

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

## Otwarta kwestia (czeka na decyzję Analityka)

Rekordy z KodP = "00-000" (placeholder ERP) i pustą ulicą/miastem dają:
- Adres_Kontrahenta = ", 00-000"
- Adres_Wysylki = ", 00-000"
NULLIF nie usuwa bo string nie jest pusty. Opcje:
(a) zostawić — odzwierciedla dane ERP
(b) dodać CASE filtrujący "00-000" jako placeholder

---

## Uwaga o eksporcie (ważne dla następnego agenta)

Przy 224k wierszach Excel się zacina. Zamiast pelnego eksportu uzyj:
```
python tools/sql_query.py --file solutions/bi/TraNag/TraNag_export_sample.sql --export solutions/bi/TraNag/TraNag_export_v2.xlsx
```
Plik TraNag_export_sample.sql = TOP 100000 ORDER BY ID_Dokumentu DESC z pełnym draftem.
Fix 2026-03-15: CTE musi być na zewnątrz subquery — naprawiony.

---

## Następny krok dla kolejnego agenta

1. Sprawdź inbox — Analityk powinien odpowiedzieć na msg id=70
2. Jeśli zatwierdzenie: solutions_save_view.py + agent_bus flag dla DBA
3. Jeśli uwagi: wprowadź zmiany w drafcie, eksport, ponowna recenzja

---

## Wiadomości agent_bus z tej i poprzednich sesji

- id=62: erp_specialist → developer — Komentarz_Usera mylaaca nazwa kolumny
- id=63: erp_specialist → analyst — eksport v1 gotowy (ZDEZAKTUALIZOWANY)
- id=64: analyst → erp_specialist — zatwierdzam eksport v1 (odczytana)
- id=65: flag — DBA do wdrozenia (PRZEDWCZESNY — anulowany)
- id=66: erp_specialist → analyst — uzupelnienia v2 + pytanie o wytyczne
- id=67: analyst → erp_specialist — wytyczne FK zaktualizowane (odczytana)
- id=70: erp_specialist → analyst — eksport v2 gotowy, proszę o recenzję Fazy 3

---

## Pliki

- Brudnopis v2: solutions/bi/TraNag/TraNag_draft.sql (CTE + 73 kolumny)
- Eksport sample: solutions/bi/TraNag/TraNag_export_sample.sql (TOP 100k, naprawiony)
- Eksport v2: solutions/bi/TraNag/TraNag_export_v2.xlsx (100k wierszy)
- Plan: solutions/bi/TraNag/TraNag_plan.xlsx
- Eksport v1 (stary, 68 kolumn): solutions/bi/TraNag/TraNag_export.xlsx
