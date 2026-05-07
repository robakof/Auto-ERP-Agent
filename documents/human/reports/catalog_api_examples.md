# Catalog API — przykłady danych wyjściowych

Base URL: `http://localhost:8502`
Auth: header `X-API-Key: ceim-katalog-2025` lub `?api_key=ceim-katalog-2025`

---

## 1. Pojedynczy produkt

**Request:** `GET /api/product/CZNI42027?api_key=ceim-katalog-2025`

**Response:**
```json
{
  "kod": "CZNI42027",
  "ean": "5907702542027",
  "nazwa": "P 109 serce SR",
  "grupa": "0CMENTARZ/ZNICZE/DUŻE",
  "sezon": "Sezon 2026",
  "kolor": "srebrny",
  "status_ofertowy": "",
  "czas_palenia_h": 27.0,
  "gramatura_g": 90.0,
  "wysokosc_netto_cm": 33.5,
  "szerokosc_netto_cm": 15.0,
  "srednica_cm": 15.0,
  "material": "Szkło",
  "zapach": "",
  "waga_g": 903.0,
  "srednica_otworu_cm": 8.3,
  "szerokosc_brutto_cm": 39.3,
  "wysokosc_brutto_cm": 25.0,
  "glebokosc_brutto_cm": 28.8,
  "szt_w_opakowaniu": 4,
  "szt_na_warstwie": 32,
  "szt_na_palecie": 192,
  "ma_zdjecie": true,
  "liczba_zdjec": 2,
  "zasilanie": "",
  "bateria_w_zestawie": "",
  "ceny": [
    {"cennik_id": 98,  "cennik_nazwa": "Wielkanoc 2025", "cennik_rodzaj": 1, "cena_netto": 14.85, "waluta": "PLN"},
    {"cennik_id": 2,   "cennik_nazwa": "CMENTARZ",       "cennik_rodzaj": 2, "cena_netto": 20.00, "waluta": "PLN"},
    {"cennik_id": 7,   "cennik_nazwa": "FRANOWO",         "cennik_rodzaj": 3, "cena_netto": 15.00, "waluta": "PLN"},
    {"cennik_id": 95,  "cennik_nazwa": "Wielkanoc 2025", "cennik_rodzaj": 4, "cena_netto": 11.77, "waluta": "PLN"},
    {"cennik_id": 96,  "cennik_nazwa": "Wielkanoc 2025", "cennik_rodzaj": 5, "cena_netto": 11.77, "waluta": "PLN"},
    {"cennik_id": 97,  "cennik_nazwa": "Wielkanoc 2025", "cennik_rodzaj": 6, "cena_netto": 12.00, "waluta": "PLN"},
    {"cennik_id": 11,  "cennik_nazwa": "CHATA POLSKA",   "cennik_rodzaj": 7, "cena_netto": 11.77, "waluta": "PLN"},
    {"cennik_id": 21,  "cennik_nazwa": "AT",              "cennik_rodzaj": 8, "cena_netto": 0.00,  "waluta": "PLN"},
    {"cennik_id": 22,  "cennik_nazwa": "PRYZMAT",         "cennik_rodzaj": 9, "cena_netto": 0.00,  "waluta": "PLN"}
  ]
}
```

### Mapowanie cennik_rodzaj:
| cennik_rodzaj | Klient |
|--------------|--------|
| 1 | CENA 100 (bazowa) |
| 2 | CMENTARZ |
| 3 | FRANOWO |
| 4 | BRICO |
| 5 | INTER |
| 6 | MRÓWKA / PSB |
| 7 | CHATA POLSKA |
| 8 | AT |
| 9 | PRYZMAT |

---

## 2. Skład pakietu

**Request:** `GET /api/package/PAKZM012025?api_key=ceim-katalog-2025`

**Response:**
```json
{
  "pakiet_kod": "PAKZM012025",
  "pakiet_nazwa": "PAKIET ZNICZE MAŁE 1",
  "skladniki": [
    {"kod": "CZNI37153", "nazwa": "Z 574 Krzyż ZŁ",          "ilosc_szt": 80},
    {"kod": "CZNI37191", "nazwa": "Z 574 SR",                  "ilosc_szt": 80},
    {"kod": "CZNI37160", "nazwa": "Z 574 wianek B.",           "ilosc_szt": 80},
    {"kod": "CZNI41587", "nazwa": "Z 574 aniołek b.ZŁ",       "ilosc_szt": 80},
    {"kod": "BUBE41099", "nazwa": "Z 272 kolumna zalewany",    "ilosc_szt": 253},
    {"kod": "BUBE37238", "nazwa": "Z 217 ZŁ",                  "ilosc_szt": 144},
    {"kod": "BUBE42737", "nazwa": "Z 272 aplikacja",           "ilosc_szt": 132},
    {"kod": "BUBE37139", "nazwa": "Z 574 zalewany mix",        "ilosc_szt": 121}
  ]
}
```

---

## 3. Lista produktów (z filtrami)

**Request:** `GET /api/products?sezon=2025&cennik_rodzaj=4&limit=3&api_key=ceim-katalog-2025`

**Response:**
```json
{
  "count": 3,
  "products": [
    {"KodXL": "BUBE37139", "KodEAN": "...", "NazwaHandlowa": "Z 574 zalewany mix", "CenaNetto": 2.42, ...},
    {"KodXL": "BUBE37238", "KodEAN": "...", "NazwaHandlowa": "Z 217 ZŁ", "CenaNetto": 3.06, ...},
    {"KodXL": "BUBE42737", "KodEAN": "...", "NazwaHandlowa": "Z 272 aplikacja", "CenaNetto": 3.49, ...}
  ]
}
```

Parametry filtrowania:
- `sezon` — np. "2025", "2026" (LIKE match)
- `grupa` — np. "CMENTARZ", "OFERTY" (LIKE match)
- `cennik_rodzaj` — 1-9 (patrz tabela powyżej). Bez tego parametru = produkty bez ceny
- `limit` — max wierszy (domyślnie 500, max 10000)

---

## 4. Zdjęcie produktu

**Request:** `GET /api/photo/CZNI42027?api_key=ceim-katalog-2025`

**Response:** Binary image (JPG lub PNG), Content-Type: `image/jpeg` lub `image/png`

Wielu zdjęć: `?index=0` (pierwsze), `?index=1` (drugie)

Można osadzić bezpośrednio w HTML:
```html
<img src="http://localhost:8502/api/photo/CZNI42027?api_key=ceim-katalog-2025" />
```

---

## 5. Lista pakietów

**Request:** `GET /api/packages?sezon=2025&api_key=ceim-katalog-2025`

**Response:**
```json
{
  "count": 29,
  "packages": [
    {"PakietKod": "PAKK0012025", "PakietNazwa": "PAKIET ZNICZE 1 KERTI"},
    {"PakietKod": "PAKK0022025", "PakietNazwa": "PAKIET ZNICZE 2 KERTI"},
    {"PakietKod": "PAKLA012025", "PakietNazwa": "PAKIET LAMPIONY"},
    {"PakietKod": "PAKZD012025", "PakietNazwa": "PAKIET ZNICZE DUŻE 1"},
    {"PakietKod": "PAKZM012025", "PakietNazwa": "PAKIET ZNICZE MAŁE 1"},
    "..."
  ]
}
```

---

## 6. Lista cenników

**Request:** `GET /api/price-lists?api_key=ceim-katalog-2025`

**Response:**
```json
{
  "count": 65,
  "price_lists": [
    {"TCN_Id": 1, "Nazwa": "CENA 100", "Rodzaj": 1},
    {"TCN_Id": 2, "Nazwa": "CMENTARZ", "Rodzaj": 2},
    {"TCN_Id": 7, "Nazwa": "FRANOWO", "Rodzaj": 3},
    {"TCN_Id": 8, "Nazwa": "BRICO", "Rodzaj": 4},
    "..."
  ]
}
```

---

## 7. Health check (bez autoryzacji)

**Request:** `GET /api/health`

**Response:**
```json
{"status": "ok", "database": "ERPXL_CEIM"}
```

---

## Swagger UI

Interaktywna dokumentacja: `http://localhost:8502/docs`
Można testować endpointy bezpośrednio w przeglądarce.

---

## Uruchomienie serwera

```
start_catalog_api.bat
```
Port: 8502 (konfigurowalne w .env: CATALOG_API_PORT)
