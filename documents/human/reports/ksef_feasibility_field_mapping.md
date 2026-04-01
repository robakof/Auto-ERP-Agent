# KSeF FA(2) — mapa pól SQL → XML

Data: 2026-03-31
Autor: ERP Specialist
Wniosek: **TAK — widok SQL pokrywa wszystkie pola wymagane przez KSeF FA(2)**

---

## Sekcja 1: Nagłówek XML (Naglowek)

| Pole KSeF | Źródło | Wartość / Kolumna | Uwaga |
|---|---|---|---|
| KodFormularza | stała | `FA` | — |
| WariantFormularza | stała | `2` | FA(2) |
| DataWytworzeniaFa | generowane | czas generowania XML | w kodzie Python |
| SystemInfo | opcjonalne | `Comarch ERP XL` | — |

---

## Sekcja 2: Podmiot1 — Sprzedawca (CDN.Firma)

| Pole KSeF | Kolumna SQL | Przykład |
|---|---|---|
| NIP | `Frm_NIP` | 7871003063 |
| PelnaNazwa | `Frm_Nazwa1` + `' '` + `Frm_Nazwa2` | Produkcja Zniczy I Lampionów CEIM MAREK CYPROWSKI |
| KodKraju | `Frm_Kraj` | PL |
| AdresL1 | `Frm_Ulica` | Leśna 14 |
| AdresL2 | `Frm_KodP` + `' '` + `Frm_Miasto` | 64-551 Otorowo |

---

## Sekcja 3: Podmiot2 — Nabywca (CDN.KntKarty)

JOIN: `CDN.TraNag.TrN_KntNumer = CDN.KntKarty.Knt_GIDNumer`

| Pole KSeF | Kolumna SQL | Uwaga |
|---|---|---|
| NIP | `Knt_Nip` | — |
| PrefiksNIP | `Knt_NipPrefiks` | dla UE; puste = PL |
| PelnaNazwa | `Knt_Nazwa1` | — |
| KodKraju | `Knt_Kraj` | — |
| AdresL1 | `Knt_Ulica` | zawiera "ul. " + numer — do oczyszczenia |
| AdresL2 | `Knt_KodP` + `' '` + `Knt_Miasto` | — |

**Uwaga:** `Knt_Ulica` = `"ul. Sienkiewicza 1"` — prefiks "ul." może wymagać usunięcia w XML.

---

## Sekcja 4: Faktura (Fa) — nagłówek (CDN.TraNag)

Filtr FS: `TrN_GIDTyp = 2033`

| Pole KSeF | Kolumna SQL | Formuła / Uwaga |
|---|---|---|
| KodWaluty | `TrN_Waluta` | PLN |
| P_1 (data wystawienia) | `TrN_Data2` | `DATEADD(day, TrN_Data2, '1800-12-28')` |
| P_1M (miesiąc) | — | wyciągany z P_1 |
| P_2A (numer faktury) | `TrN_TrNSeria` + `'/'` + `TrN_TrNNumer` | np. SPKR/268 |
| P_6 (rodzaj faktury) | stała | `VAT` dla FS |
| P_15 (kwota należności) | `TrN_NettoR` + `TrN_VatR` | — |
| RodzajFaktury | `TrN_NrKorekty` | puste = VAT; niepuste = KOR |

### Konwersja daty — zweryfikowana ✓
```sql
DATEADD(day, TrN_Data2, '1800-12-28')
-- TrN_Data2 = 82273  →  2026-03-31
-- TrN_Termin = 82287 →  2026-04-14
```

---

## Sekcja 5: VAT per stawka (CDN.TraVat)

JOIN: `TrV_GIDTyp = TrN_GIDTyp AND TrV_GIDNumer = TrN_GIDNumer`

| Pole KSeF | Kolumna SQL | Stawki w danych |
|---|---|---|
| P_13_1 (podstawa 23%) | `TrV_NettoR` WHERE `TrV_StawkaPod = '23.00'` | ✓ 19 492 wierszy |
| P_14_1 (VAT 23%) | `TrV_VatR` WHERE `TrV_StawkaPod = '23.00'` | ✓ |
| P_13_2 (podstawa 8%) | `TrV_NettoR` WHERE `TrV_StawkaPod = '8.00'` | ✓ 9 wierszy |
| P_14_2 (VAT 8%) | `TrV_VatR` WHERE `TrV_StawkaPod = '8.00'` | ✓ |

**Dane CEIM:** w praktyce tylko stawki 23% i 8%. Brak ZW/NP/0% w bieżących FS.

---

## Sekcja 6: Pozycje faktury FaWiersz (CDN.TraElem)

JOIN: `TrE_GIDTyp = TrN_GIDTyp AND TrE_GIDNumer = TrN_GIDNumer`

| Pole KSeF | Kolumna SQL | Uwaga |
|---|---|---|
| NrWierszaFa | `TrE_GIDLp` | numer pozycji |
| P_7 (nazwa towaru) | `TrE_TwrNazwa` | — |
| P_8A (jednostka miary) | `TrE_JmZ` | szt., kg, itp. |
| P_8B (ilość) | `TrE_Ilosc` | — |
| P_9A (cena jedn. netto) | `TrE_Cena` | — |
| P_10 (wartość netto) | `TrE_KsiegowaNetto` | — |
| P_11 (stawka VAT) | `TrE_StawkaPod` | 23.00 → "23", 8.00 → "8" |
| P_12 (kwota VAT) | obliczana | `TrE_KsiegowaBrutto - TrE_KsiegowaNetto` |

---

## Sekcja 7: Płatność (CDN.TraPlat + CDN.RachunkiBankowe)

JOIN TraPlat: `TrP_GIDTyp = TrN_GIDTyp AND TrP_GIDNumer = TrN_GIDNumer`
JOIN Rachunek: `RachunkiBankowe.RkB_Id = TrP_RachBank`

| Pole KSeF | Kolumna SQL | Mapowanie |
|---|---|---|
| TerminPlatnosci | `TrP_Termin` | `DATEADD(day, TrP_Termin, '1800-12-28')` |
| FormaPlatnosci | `TrP_FormaNr` | 10→1(gotówka), 20→6(przelew), 50→3(karta) |
| NrRachunku | `RkB_NrRachunku` | tylko dla FormaNr=20 (przelew) |

**Formy płatności w danych CEIM:**
- 20 = Przelew — 10 841 rekordów
- 10 = Gotówka — 6 051 rekordów
- 50 = Karta — 2 603 rekordów

---

## Sekcja 8: Adnotacje (CDN.TraNag)

| Pole KSeF | Kolumna SQL | Stan |
|---|---|---|
| P_16 (MPP — split payment) | `TrN_MPP` | ✓ dostępne (0 = nie) |
| P_18 (self-billing) | stała `0` | CEIM nie stosuje |
| P_19 (TP — podmiot powiązany) | do weryfikacji | brak w bieżącym zakresie |

---

## Podsumowanie — co wymaga transformacji (nie brakuje, ale trzeba przetworzyć)

| Pole | Problem | Rozwiązanie |
|---|---|---|
| Daty | format Comarch (liczba dni) | `DATEADD(day, col, '1800-12-28')` |
| Adres nabywcy | prefiks "ul." w Knt_Ulica | REPLACE lub TRIM w SQL/Python |
| P_11 (stawka VAT) | decimal "23.00" | CAST + mapowanie na string "23" |
| P_12 (kwota VAT) | brak kolumny wprost | obliczana: Brutto - Netto |
| FormaPlatnosci | kody Comarch ≠ kody KSeF | mapowanie: 10→1, 20→6, 50→3 |
| Numer faktury P_2A | dwa pola | konkatenacja: Seria + '/' + Numer |

---

## Tabele SQL używane w widoku

```
CDN.TraNag        — nagłówek faktury (główna tabela)
CDN.TraElem       — pozycje faktury
CDN.TraVat        — VAT per stawka
CDN.TraPlat       — płatności
CDN.KntKarty      — dane nabywcy
CDN.RachunkiBankowe — numery rachunków bankowych
CDN.Firma         — dane sprzedawcy (1 rekord)
```
