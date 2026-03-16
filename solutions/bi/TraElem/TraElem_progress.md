## Status: Faza 0 ZAKOŃCZONA — plan w trakcie generowania (plan_src.sql gotowy)

**Tabela główna:** CDN.TraElem
**Baseline:** COUNT(*) = 1 147 150 (baza produkcyjna, rośnie)
**PK:** (TrE_GIDNumer, TrE_GIDLp) — COUNT DISTINCT = 1 147 150 = Total ✓
**JOIN TraNag:** INNER zwraca 1 147 149 (1 sierota) → używamy LEFT JOIN

---

## Discovery — kluczowe ustalenia

### Typy dokumentów
TrE_GIDTyp: 23 distinct — identyczne jak TrN_GIDTyp w TraNag.
CASE wzorzec — użyć identycznego jak AIBI.TraNag.

### TrE_TypTwr (typ towaru):
- 1 = Towar (739 884 wierszy)
- 2 = Produkt (399 441)
- 3 = Koszt (47)
- 4 = Usługa (639)
- 6 = A-Vista (7 139) — pozycja bez stałej karty towaru
  Weryfikacja: jedyny TwrKarty z Typ=6 ma Kod="A-VISTA"; wszystkie TraElem TypTwr=6 mają TrE_TwrKod="A-VISTA"
  Interpretacja potwierdzona przez dane — nie wymaga eskalacji.

### TrE_TrnTStamp:
Range: 1 054 292 805 do 2 147 385 600 → ~10^9 = Clarion TIMESTAMP (sekundy od 1990-01-01)
2 147 385 600 = sentinel (~2058) — używać CASE WHEN 0 THEN NULL.

### TrE_GIDLp vs TrE_Pozycja:
- GIDLp = techniczna część PK (nie ulega przenumerowaniu, może mieć "dziury")
- Pozycja = wyświetlana na dokumencie (ciągła)
- Plan: uwzględnić GIDLp jako Nr_Pozycji; pominąć Pozycja (redundantna)

### Kolumny inline:
TrE_TwrNazwa i TrE_TwrKod są przepisywane z kartoteki i podlegają edycji —
odzwierciedlają stan w chwili transakcji. Używamy inline, bez JOIN TwrKarty.

### Akwizytor:
TrE_AkwTyp: 0, 32 (KntKarty), 944 (PrcKarty) — identyczny wzorzec jak TrN_AkwTyp w TraNag.
Wzorzec: COALESCE(akw_knt.Knt_Akronim, akw_prc.Prc_Akronim).

### TrE_ZlcNumer: tylko 6 distinct wartości — FK do zlecenia praktycznie puste → pominąć.

### TrE_CenaSpr: wartości -32000 (nieokreślony), 0 (brak), 1-9 (numery cenników) → NULL gdy 0/-32000.

### TrE_Cecha: partia/seria towaru, 32 distinct wartości (np. "138.P4/2J").

---

## JOINy ustalone

| Alias | Tabela | Warunek | Po co |
|---|---|---|---|
| n | CDN.TraNag | LEFT JOIN n.TrN_GIDNumer=e.TrE_GIDNumer AND n.TrN_GIDTyp=e.TrE_GIDTyp | Numer_Dokumentu, Data_Wystawienia |
| knt_pos | CDN.KntKarty | LEFT JOIN knt_pos.Knt_GIDNumer=e.TrE_KntNumer AND e.TrE_KntNumer>0 | Akronim_Kontrahenta_Pozycji |
| akw_knt | CDN.KntKarty | LEFT JOIN akw_knt.Knt_GIDNumer=e.TrE_AkwNumer AND e.TrE_AkwTyp=32 | Akwizytor_Akronim |
| akw_prc | CDN.PrcKarty | LEFT JOIN akw_prc.Prc_GIDNumer=e.TrE_AkwNumer AND e.TrE_AkwTyp=944 | Akwizytor_Akronim |

---

## Plan kolumn — status

Plan_src.sql: `solutions/bi/TraElem/TraElem_plan_src.sql` — GOTOWY (131 wierszy)
Plan Excel: NIE WYGENEROWANY — błąd bi_plan_generate.py

### PROBLEM z bi_plan_generate.py
Użyłem składni `FROM (VALUES ...) AS t(...)` zamiast `SELECT ... UNION ALL SELECT ...`.
Narzędzie używa SQLite — wymaga formatu UNION ALL (jak TwrKarty_plan_src.sql).

### CO ZROBIĆ NASTĘPNYM RAZEM
1. Przepisać TraElem_plan_src.sql na format UNION ALL:
   ```
   SELECT 1 AS Kolejnosc, 'TrE_GIDTyp' AS CDN_Pole, ... AS Opis_w_dokumentacji, ...
   UNION ALL SELECT 2, 'TrE_GIDFirma', ...
   ...
   ```
   Wzorzec: patrz `solutions/bi/TwrKarty/TwrKarty_plan_src.sql`

2. Uruchomić: `python tools/bi_plan_generate.py --src solutions/bi/TraElem/TraElem_plan_src.sql`

3. Wysłać plan do Analityka przez agent_bus.

### Kolumny do uwzględnienia (Tak) — 48 kolumn:
Typ_Dokumentu, ID_Dokumentu, Nr_Pozycji,
[JOIN TraNag] Numer_Dokumentu, Data_Wystawienia,
ID_Towaru, Nazwa_Towaru, Kod_Towaru, Typ_Towaru,
ID_Kontrahenta_Pozycji, Akronim_Kontrahenta_Pozycji,
ID_Akwizytora, Akwizytor_Akronim,
DataCzas_Utworzenia,
Ilosc, Jednostka_Miary, Przelicznik_JM,
Grupa_VAT, Stawka_VAT, Flaga_VAT,
Waluta, Kurs_Mianownik, Kurs_Licznik,
Cena_Poczatkowa_Waluta, Rabat_Procent, Wartosc_Po_Rabacie_Waluta,
Wartosc_Netto_PLN, Wartosc_Brutto_PLN, Wartosc_Rzeczywista_Netto_PLN,
Koszt_Ksiegowy_PLN, Koszt_Rzeczywisty_PLN,
Cena_Jednostkowa, Cena_Po_Rabacie,
ID_Cennika,
Kraj_Pochodzenia, Rabat_Promocyjny, Rabat_Korekta, Rabat_Operator,
Cecha_Towaru,
Ilosc_Przed_Korekta, Cena_Przed_Korekta, Wartosc_Przed_Korekta_PLN,
Grupa_VAT_Przed_Korekta, Stawka_VAT_Przed_Korekta, Flaga_VAT_Przed_Korekta,
Przyczyna_Korekty

---

## Pliki

- Brudnopis: solutions/bi/TraElem/TraElem_draft.sql (stub, do wypełnienia w Fazie 2)
- Plan src: solutions/bi/TraElem/TraElem_plan_src.sql (do przepisania na UNION ALL)
- Plan Excel: NIE ISTNIEJE — do wygenerowania
- Eksport: NIE ISTNIEJE

## Następny krok

1. Przepisać plan_src.sql na UNION ALL
2. Wygenerować plan Excel
3. Wysłać do Analityka
