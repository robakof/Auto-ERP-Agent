# Plan: Widoki SQL do systemu katalogów CEiM

Data: 2026-05-07
Specyfikacja: `documents/Wzory plików/adr024_sql_view_fields (1).md`

---

## Research — wyniki

### 1. Identyfikacja produktu
- `CDN.TwrKarty`: `Twr_Kod`, `Twr_Nazwa`, `Twr_Ean` — OK, dane poprawne

### 2. Klasyfikacja (foldery)
- Drzewo folderów: `CDN.TwrGrupy` (parent-child przez `TwG_GrONumer`)
- Przynależność towaru: `CDN.TwrGrupyDom` (join: `TGD_GIDNumer = Twr_GIDNumer`, `TGD_GrONumer = TwG_GIDNumer`)
- Folder root ofertowy: `10_OFERTY` (GID=9139)
  - Dzieci: `2025` (GID=9235), `2026` (GID=10719), `ROM-POL`, `WYPRZEDAŻ`
  - Pod `2025`: BRICO (GID=9645), AUCHAN, DINO, INTER, HURT, BRICO DDD, HANDEL
  - Pod `2026`: BRICO CENTRALA, AUCHAN, DINO, SOLAR+MIRAGE, itd.
- Folder root rodziny: `01_CMENTARZ` → `1_ZNICZE` → `4_DUŻE` (przykład CZNI42027)
- **Towar może być w wielu folderach** — potwierdzone w TwrGrupyDom

### 3. Parametry produktu (ZBADANE — Faza 2)
Tabele: `CDN.Atrybuty` + `CDN.AtrybutyKlasy`
Join: `Atr_ObiTyp = 16` (towar), `Atr_ObiNumer = Twr_GIDNumer`, `Atr_AtkId = AtK_ID`

**22 klasy atrybutów na towarach — mapowanie do specyfikacji:**

| AtK_ID | AtK_Nazwa | AtK_Format | Pole spec | Pokrycie |
|--------|-----------|------------|-----------|----------|
| 3 | SEZON | @s100 | #9 Sezon | 6282 towarów |
| 5 | KOLOR | @s100 | #10 Kolor/wariant | 1264 |
| 6 | MATERIAŁ | @s100 | #33 Materiał | 1435 |
| 9 | CZAS PALENIA / DZIAŁANIA | @n7.2 | #11 Czas palenia | 1258 |
| 10 | GRAMATURA WKŁADU  | @n4.0 | #12 Gramatura | 947 |
| 11 | SZEROKOŚĆ NETTO PRODUKTU | @n7.2 | #14 Szer. netto | 1318 |
| 12 | WYSOKOŚĆ NETTO PRODUKTU  | @n7.2 | #13 Wys. netto | 1488 |
| 13 | SZEROKOŚĆ BRUTTO OPAKOWANIA | @n7.2 | #15 Szer. brutto | 1187 |
| 14 | WYSOKOŚĆ BRUTTO OPAKOWANIA  | @n7.2 | #16 Wys. brutto | 1194 |
| 15 | GŁĘBOKOŚĆ BRUTTO OPAKOWANIA  | @n7.2 | #17 Głęb. brutto | 1186 |
| 16 | ŚREDNICA PRODUKTU | @n7.2 | #30 Średnica | 1162 |
| 55 | WAGA PRODUKTU | @n7.2 | (dodatkowe) | 1024 |
| 56 | ŚREDNICA OTWORU | @n7.2 | (dodatkowe) | 1013 |
| 4 | ZAPACH | @s100 | #31 Zapach | 50 |
| 44 | GRUPA | @s200 | (ścieżka folderowa) | 10252 |
| 8 | CZY BATERIA W ZESTAWIE | @s100 | (dodatkowe) | 252 |
| 7 | ZASILANIE | @s100 | (dodatkowe) | 516 |
| 57 | OFERTA AUTOMATYCZNA | @s100 | (dodatkowe) | 113 |
| 59 | STATUS OFERTOWY PRODUKTU | @s100 | (dodatkowe) | 1628 |
| 18 | TREND NOWOŚCI | @n7.2 | (dodatkowe) | 26 |
| 48 | Ilość zestawów | @s100 | (dodatkowe) | 4 |
| 25 | % ODPADU | @n9.4 | (dodatkowe) | 1 |

**Weryfikacja CZNI42027:** SEZON=Sezon 2026, KOLOR=srebrny, MATERIAŁ=Szkło,
CZAS PALENIA=27, GRAMATURA=90, WYS. NETTO=33.5, SZER. NETTO=15, ŚREDNICA=15 — zgadza się ze spec.

**Brak w ERP:** pole #32 "Efekt" — nie istnieje jako klasa atrybutów.

### 4. Jednostki logistyczne (ZBADANE — Faza 2)
Tabela: `CDN.TwrJm`
Join: `TwJ_TwrNumer = Twr_GIDNumer`
Kolumny: `TwJ_JmZ` (nazwa jm.), `TwJ_PrzeliczL` (ilość), `TwJ_PrzeliczM` (mnożnik, zwykle 1)

**Weryfikacja CZNI42027:**
| TwJ_JmZ | TwJ_PrzeliczL | Pole spec |
|---------|---------------|-----------|
| opak. | 4 | #18 Szt. w opakowaniu |
| warstwa | 32 | #19 Szt. na warstwie |
| paleta | 192 | #20 Szt. na palecie |

Zgadza się ze specyfikacją (4, 32, 192). Brak "karton" (pole #21) — nie wypełnione w danych.
Pivot po TwJ_JmZ potrzebny: opak. → kolumna, warstwa → kolumna, paleta → kolumna.

### 5. Ceny (ZBADANE — Faza 2)
Tabele: `CDN.TwrCeny` + `CDN.TwrCenyNag`
Join: `TwC_TcnId = TCN_Id`, `TwC_TwrNumer = Twr_GIDNumer`
Filtr ogólny: `TwC_KntNumer = 0` (ceny nie przypisane do kontrahenta)

**65 cenników** w systemie. Kluczowe RodzajCeny:
- 1 = CENA 100 (bazowa)
- 4 = BRICO
- 5 = INTER
- 6 = MRÓWKA / PSB
- 7 = CHATA POLSKA
- 8 = AT
- 9 = PRYZMAT

**Weryfikacja CZNI42027:** cena 11.77 PLN (spec) = cenniki Wielkanoc 2025 / CHATA POLSKA.
Wiele cenników per RodzajCeny (np. 10 cenników BRICO). Najnowszy cennik dominuje (najwyższy TCN_Id).

**PYTANIE DO USERA:** Który cennik/RodzajCeny dla widoku katalogowego? Spec mówi "cena netto jednostkowa"
ale nie precyzuje cennika. Prawdopodobnie potrzebny parametr — np. oferta BRICO = RodzajCeny=4.

### 6. Pakiety (ZBADANE — Faza 2) — BRAK STRUKTURY W ERP

**Kluczowe odkrycie:** Struktura parent→child pakietów NIE ISTNIEJE w bazie Comarch XL.

Co zbadano:
- `CDN.TwrReceptury` — tabela nie istnieje
- `CDN.TwrZamienniki` — tabela nie istnieje
- `CDN.KompNag/KompElem` — kompensaty finansowe, nie produktowe
- `CDN.ProdTechnologia` — PAKZM012025 nie ma technologii
- `CDN.TwrLinki` — linki do grup (folder), nie do produktów
- `CDN.TwrGrupyDom` — PAKZM012025 jako folder jest PUSTY
- `CDN.FrsZamienniki` — schemat tabeli nie pasuje (FRZ_ prefix)
- `CDN.BstSkladniki` — bilans, nie produkty
- Atrybuty PAKZM012025: tylko GRUPA="OFERTY/2025/KATALOG CEIM/PAKIETY"

**29 pakietów 2025** (PAK*2025): PAKZM01-03, PAKZS01-05, PAKZD01-04, PAKLA01-01A,
PAKK001-007, PAKKPRO/PROA/WK, PAKZW1-3.
Wszystkie to zwykłe kartoteki (Twr_Typ=1), cena 0.00 PLN.

**Wniosek:** Skład pakietu (parent→child + ilości) jest WYŁĄCZNIE w Excelu katalogowym (kol. Z, AB, AC).
Do zrealizowania Widoku 3 potrzebna jest jedna z opcji:
  a) Import mapowania Excel → custom tabela SQL (`CEiM.PakietyElem`)
  b) Join po atrybucie GRUPA (ale CZNI41099 ma GRUPA=CMENTARZ, nie PAKIETY — nie zadziała)
  c) Widok 3 generowany z Excela, nie z SQL

**Rekomendacja:** Opcja (a) — jednorazowy import per sezon. Tabela:
```sql
CREATE TABLE CEiM.PakietyElem (
    Pakiet_Kod VARCHAR(20),    -- np. PAKZM012025
    Towar_Kod  VARCHAR(20),    -- np. CZNI41099
    Ilosc_Szt  INT,            -- 253
    Ilosc_Opak INT,            -- 11
    Cena_Jedn  DECIMAL(10,2),  -- 2.42
    Sezon      VARCHAR(10)     -- 2025
);
```

### 7. Zdjęcia
- Ścieżka: `D:\UdzialySieciowe\ZDJĘCIA\ZDJĘCIA PRODUKTÓW\{Kod_XL}.png`
- Do ustalenia dostępność z serwera

---

## Plan implementacji (zaktualizowany)

### Faza 1 — Widok folderów (WIDOK 2) ✓ gotowy do budowy
CTE rekursywne po `TwrGrupy` → pełna ścieżka.
Join z `TwrGrupyDom` → `Twr_Kod`.
Typ folderu: root=`10_OFERTY` → oferta, inne → rodzina.

### Faza 2 — Research ✓ ZAKOŃCZONY
Wszystkie pola zmapowane. Brakuje: decyzja o cenniku, decyzja o pakietach.

### Faza 3 — Widok produktów (WIDOK 1)
Join: TwrKarty + atrybuty (PIVOT po AtK_Nazwa) + ceny (parametryzowane cennik) + jednostki (PIVOT po TwJ_JmZ) + foldery (z Widoku 2).
Jeden wiersz per produkt.

### Faza 4 — Widok pakietów (WIDOK 3) — WYMAGA DECYZJI
Opcje: (a) custom tabela z importem, (b) generowanie z Excela.
**Blokowane** do czasu decyzji użytkownika.

### Faza 5 — Zdjęcia
Sprawdzenie dostępności ścieżki sieciowej.

---

## Pytania do użytkownika (blokujące)

1. **Cennik:** Który cennik/RodzajCeny dla widoku katalogowego?
   Np. BRICO=4, CENA 100=1, a może parametr w widoku?
2. **Pakiety:** Opcja (a) import Excela do custom tabeli, opcja (b) bez SQL, opcja (c) inna?
3. **Zdjęcia:** Czy ścieżka `D:\UdzialySieciowe\...` jest dostępna z SQL Servera?

---

## Następny krok
Budowa Widoku 2 (foldery) — niezależny od pytań blokujących.
Po decyzji o cenniku → Widok 1 (produkty).
