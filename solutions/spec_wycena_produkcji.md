# Specyfikacja: Generator Wyceny Produkcji

## Cel

Skrypt Python generujący plik Excel z wyceną dla wybranej oferty klienta.
Dane produktów pobierane z ERP (CDN). Wynik oparty na szablonie `Wycena 2026 Otorowo Szablon.xlsm`.

---

## Wejście

- `offer_group_id` — ID grupy oferty z CDN.TwrGrupy (np. 10729 = AUCHAN 2026)
- `client_name` — nazwa klienta do wpisania w kolumnę A (np. "AUCHAN")

## Wyjście

Plik `.xlsx` z arkuszem `Wycena Zniczy`, gdzie dla każdego produktu z oferty
generowanych jest 16 wierszy BOM.

---

## Struktura ofert w ERP

```
CDN.TwrGrupy
  10_OFERTY (GIDNumer: 9139)
    └── 2026 (GIDNumer: 10719)
          ├── AUCHAN        (GIDNumer: 10729)  ← 91 produktów CZNI*
          ├── DINO          (GIDNumer: 10877)
          ├── BABCIA DZIADEK(GIDNumer: 10720)
          ├── BRICO CENTRALA(GIDNumer: 10974)
          ├── SOLAR+MIRAGE  (GIDNumer: 10852)
          └── WIELKANOC_2026(GIDNumer: 10934)
```

## SQL — lista produktów z oferty

```sql
SELECT TwG_Kod AS produkt_kod, TwG_Nazwa AS produkt_nazwa
FROM CDN.TwrGrupy
WHERE TwG_GrONumer = :offer_group_id
  AND TwG_GIDTyp = 16          -- tylko kartoteki, nie grupy
  AND TwG_Kod LIKE 'CZNI%'
ORDER BY TwG_Kod
```

## SQL — jednostki opakowań produktu (Paletka i Paleta)

```sql
SELECT j.TwJ_JmZ, j.TwJ_PrzeliczL
FROM CDN.TwrKarty tw
JOIN CDN.TwrJm j ON j.TwJ_TwrNumer = tw.Twr_GIDNumer
                 AND j.TwJ_TwrTyp = tw.Twr_GIDTyp
WHERE tw.Twr_Kod = :produkt_kod
  AND j.TwJ_JmZ IN ('opak.', 'paleta')
```

Kolumna `TwJ_PrzeliczL` (VARCHAR) → rzutować na FLOAT.

---

## Struktura wierszy BOM (16 wierszy na produkt)

| # | Właściwość | Grupa        | Nazwa Właściwości        | Akronim surowca | Mianownik przeliczenia       |
|---|-----------|--------------|--------------------------|-----------------|------------------------------|
| 1 | Surowiec  | Podstawowa   | Dekiel                   | ręcznie         | 1                            |
| 2 | Surowiec  | Zdobienie    | Brokat                   | ręcznie         | **ręcznie** (puste)          |
| 3 | Surowiec  | Podstawowa   | Etykieta                 | ET0077          | 1                            |
| 4 | Surowiec  | Pakowanie    | Folia pakowa             | FO0003          | CEILING((1000/45) × Paletka) |
| 5 | Surowiec  | Pakowanie    | Folia Stretch            | FO0004          | Paleta × 2                   |
| 6 | Surowiec  | Pakowanie    | Paletka                  | ręcznie         | z ERP: TwJ_PrzeliczL 'opak.' |
| 7 | Surowiec  | Zdobienie    | Farba lakier do szkła    | ręcznie         | **ręcznie** (puste)          |
| 8 | Surowiec  | Podstawowa   | Spód                     | ręcznie         | 1                            |
| 9 | Surowiec  | Podstawowa   | Szkło                    | patrz algorytm  | 0.99 (klient określony) / 0.98 (pozostałe) |
|10 | Surowiec  | Podstawowa   | Wkład                    | ręcznie         | 1                            |
|11 | Koszt     | Inne koszty  | Energia Otorowo          | —               | 1                            |
|12 | Koszt     | Zdobienie    | Godzina pracy malarni    | —               | **ręcznie** (puste)          |
|13 | Koszt     | Inne koszty  | Dodatkowe koszty Otorowo | —               | 1                            |
|14 | Koszt     | Robocizna    | Roboczogodzina Otorowo   | —               | **ręcznie** (puste)          |
|15 | Koszt     | Robocizna    | Premia                   | —               | 1                            |
|16 | Koszt     | (null)       | BDO                      | —               | 1                            |

Kolumny E, F, G zawsze pre-wypełnione zgodnie z tabelą. Kolumna H — stałe
akronimy dla Etykiety, Folii; reszta pusta (ręcznie). Kolumna I (Nazwa surowca)
— pusta (do ręcznego uzupełnienia lub przyszłej automatyzacji).

---

## Kolumna A — Klient

- Pierwszy wiersz produktu: wartość `client_name` (np. "AUCHAN")
- Kolejne wiersze tego produktu: puste (null)

---

## Kolumna B — Akronim produktu

- We wszystkich 16 wierszach produktu: kod produktu (np. "CZNI39355")

---

## Kolumny C, D — EAN i Nazwa

Do ustalenia z użytkownikiem: czy generator ma wpisywać formuły
(=WYSZUKAJ.PIONOWO z arkusza Baza_towarów_i_stanów) czy puste?

---

## Kolumny K–V — formuły

Do ustalenia z użytkownikiem: czy przepisywać formuły z szablonu?
Jeśli tak — wymagany arkusz Baza_towarów_i_stanów w pliku wynikowym.

---

## Algorytm wyszukiwania Szkła (kolumna H, wiersz Szkło)

Propozycja automatyczna — wymaga weryfikacji człowieka.

### Krok 1: produkty z 3+ cyfr w nazwie
```sql
SELECT TOP 1 Twr_Kod
FROM CDN.TwrKarty
WHERE Twr_Kod LIKE 'SZ%'
  AND Twr_Nazwa LIKE '%' + SUBSTRING(:produkt_nazwa, PATINDEX('%[0-9][0-9][0-9]%', :produkt_nazwa), 3) + '%'
```
Przykłady: "Z 536 mix" → szuka "536" → SZ0236 ✓, "Z 1325 serce mix" → szuka "132" → SZ0324 ✓

### Krok 2: produkty z 1–2 cyfr w nazwie
```sql
SELECT TOP 1 Twr_Kod
FROM CDN.TwrKarty
WHERE Twr_Kod LIKE 'SZ%'
  AND Twr_Nazwa LIKE '%' + LEFT(:produkt_nazwa, CHARINDEX(' ', :produkt_nazwa + ' ', CHARINDEX(' ', :produkt_nazwa + ' ') + 1) - 1) + '%'
```
Przykłady: "D 9 diament mix" → szuka "D 9" → SZ0294 ✓, "WR 9 kolor mix" → "WR 9" → SZ0300 ✓

### Mianownik Szkła
- Oferta z klientem określonym (offer_group_id != null): **0.99**
- Pozostałe: **0.98**

---

## Mianownik Paletki i Palety

```python
paletka = float(row['TwJ_PrzeliczL'])  # gdzie TwJ_JmZ = 'opak.'
paleta  = float(row['TwJ_PrzeliczL'])  # gdzie TwJ_JmZ = 'paleta'
folia_pakowa   = math.ceil((1000 / 45) * paletka)
folia_stretch  = paleta * 2
```

---

## Plik szablonu

`Wycena 2026 Otorowo Szablon.xlsm` — arkusz `Wycena Zniczy`
- Wiersz 1: wiersz nagłówkowy (pomijamy przy generowaniu)
- Wiersz 2: nagłówki kolumn (kopiujemy)
- Wiersze 3+: dane (generujemy)

Szablon ma 45642 wierszy pre-alokowanych (puste). Generator nadpisuje od wiersza 3.

---

## Kolumny generowane przez skrypt

Generator wypełnia TYLKO kolumny: **A, B, E, F, G, H, J**

Pozostałe kolumny:
- C (EAN), D (Nazwa) — formuły z arkusza `Baza_towarów_i_stanów`, generator pomija
- K (Cena jednostkowa) — formuła automatyczna, generator pomija
- L–V — formuły lub ignorowane, generator pomija

## Otwarte pytania do ustalenia z użytkownikiem

1. Akronim surowca (kolumna H) dla wierszy: Dekiel, Spód, Wkład, Paletka, Paleta — stały czy z ERP?
