# Specyfikacja projektu: Generowanie ofert katalogowych — moduł Wkłady

## Cel

Generator PDF oferty katalogowej dla wkładów zniczowych.
Układ wzorowany na plikach: `documents/Wzory plików/wzor oferta 1.jpg`, `wzor oferta 2.jpg`

---

## Źródła danych

### 1. Plik wejściowy (lista produktów na ofercie)
`documents/Wzory plików/OFerta katalogowa.xlsx`

Kolumny:
- `Akronim produktu` — klucz łączący z ERP (`Twr_Kod`)
- `EAN`
- `Nazwa`
- `Cena sprzedaży` — cena widoczna na ofercie

### 2. ERP — CDN.TwrKarty
Połączenie: `Twr_Kod = Akronim produktu`

Kolumny:
- `Twr_GIDNumer` — do JOINów
- `Twr_Nazwa` — nazwa produktu
- `Twr_Jm` — jednostka miary podstawowa
- `Twr_Ean` — EAN

### 3. ERP — CDN.TwrJm (jednostki pomocnicze)
Połączenie: `TwJ_TwrNumer = Twr_GIDNumer`

Filtr: `TwJ_JmZ = 'opak.'`
Kolumna: `TwJ_PrzeliczL` — ilość szt. w opakowaniu

### 4. ERP — CDN.Atrybuty (wysokość netto produktu)
Połączenie: `Atr_ObiNumer = Twr_GIDNumer`

Filtr: `Atr_AtkId = 12`
Kolumna: `Atr_Wartosc` — wysokość netto produktu w cm

### 5. Zdjęcia produktów
Katalog: `D:\UdzialySieciowe\ZDJĘCIA\ZDJĘCIA PRODUKTÓW\jpg do systemu\`
Konwencja nazwy pliku: `{Twr_Kod}.jpg`

---

## Pola na karcie produktu (model: Wkłady)

| Pole | Źródło | Format wyświetlania |
|---|---|---|
| Nazwa produktu | ERP `Twr_Nazwa` | np. "Wk CEiM zniczowy 5" |
| Wysokość | ERP atrybut AtK_ID=12 | np. "24 cm" |
| Czas palenia | wyekstrahować z nazwy (liczba po "zniczowy" lub "Płomień") | np. "5 dni 120h" |
| Ilość w opakowaniu | ERP TwrJm, jednostka "opak." | np. "20 szt." |
| Cena sprzedaży | Excel kolumna "Cena sprzedaży" | np. "2,27 zł" |
| Zdjęcie | plik jpg wg Twr_Kod | — |

### Przelicznik: Czas palenia → godziny
| Dni | Godziny | Format na ofercie |
|---|---|---|
| 2 | 48 | 2 dni 48h |
| 3 | 72 | 3 dni 72h |
| 4 | 96 | 4 dni 96h |
| 5 | 120 | 5 dni 120h |
| 5,5 | 132 | 5,5 dnia 132h |
| 6 | 144 | 6 dni 144h |
| 6,5 | 156 | 6,5 dnia 156h |

---

## Layout PDF (wzorowany na wzorach)

- Format: A4 pionowy, białe tło
- Nagłówek strony: "Wkłady zniczowe CEiM" (pogrubiony, duże litery, lewa strona)
- Siatka produktów: 2 kolumny × 3 wiersze = 6 produktów na stronę (lub 2×2 jeśli zdjęcia duże)
- Każda karta produktu:
  - Zdjęcie (wycentrowane, proporcjonalne)
  - Nazwa produktu (pogrubiona)
  - 4 parametry z ikonkami lub etykietami (Wysokość / Czas palenia / Ilość w opak. / Cena)

---

## Opcje językowe

- Polski (domyślny)
- Angielski
- Rumuński

Etykiety pól do tłumaczenia:
- "Wysokość" / "Height" / "Înălțime"
- "Czas palenia" / "Burning time" / "Timp de ardere"
- "Ilość w opakowaniu" / "Pieces per pack" / "Bucăți per pachet"
- "Cena" / "Price" / "Preț"
- Nagłówek: "Wkłady zniczowe CEiM" / "CEiM Candle Inserts" / "Fitile znicze CEiM"

---

## Dane weryfikacyjne (11 produktów z pliku)

| Kod | Nazwa | Wys. | Czas palenia | Opak. | Cena |
|---|---|---|---|---|---|
| CWKZ0031 | Wk CEiM zniczowy 2 | 11 cm | 2 dni 48h | 20 szt. | 1,16 zł |
| CWKZ0033 | Wk CEiM zniczowy 3 | 14 cm | 3 dni 72h | 20 szt. | 1,36 zł |
| CWKZ0034 | Wk CEiM zniczowy 4 | 17 cm | 4 dni 96h | 20 szt. | 1,77 zł |
| CWKZ0035 | Wk CEiM zniczowy 5 | 24 cm | 5 dni 120h | 20 szt. | 2,27 zł |
| CWKZ0041 | Wk CEiM zniczowy 5 szeroki | 18 cm | 5 dni 120h | 16 szt. | 2,28 zł |
| CWKZ0036 | Wk CEiM zniczowy 5,5 | 21 cm | 5,5 dnia 132h | 12 szt. | 2,68 zł |
| CWKZ0037 | Wk CEiM zniczowy 6 | 24 cm | 6 dni 144h | 16 szt. | 3,03 zł |
| CWKZ0038 | Wk CEiM zniczowy 6,5 | 21 cm | 6,5 dnia 156h | 12 szt. | 3,36 zł |
| CWKZ0092 | Wk Płomień 2 | 11 cm | 2 dni 48h | 20 szt. | 1,01 zł |
| CWKZ0093 | WK Płomień 3 | 14 cm | 3 dni 72h | 20 szt. | 1,19 zł |
| CWKZ0094 | WK Płomień 4 | 17 cm | 4 dni 96h | 20 szt. | 1,30 zł |

---

## Uwagi

- CWKZ0041: brak zdjęcia w katalogu (eskalacja #3 w agent_bus). Generator musi obsłużyć brak pliku (placeholder lub pominięcie).
- Zdjęcia: 10/11 dostępnych — wszystkie poza CWKZ0041
- Cena w Excelu jest float — zaokrąglić do 2 miejsc, wyświetlać z separatorem dziesiętnym przecinek
- Model "Płomień" (CWKZ0092-0094): osobna seria ale ten sam szablon karty

---

## Drugi model (do realizacji w kolejnej sesji)

Znicze (szkła) — parametry i pola do ustalenia osobno.
