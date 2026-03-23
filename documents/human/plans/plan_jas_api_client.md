# Plan: JAS API Client — integracja WZ → zlecenie spedycyjne

## Pliki do stworzenia

### 1. `tools/jas_client.py`
OAuth2 + wywołania API:
- `JasClient.authenticate()` → POST token endpoint → Bearer token (cache do wygaśnięcia)
- `JasClient.create_shipment(payload: dict) → dict`
- `JasClient.get_shipment(id) → dict` (do weryfikacji po wysłaniu)

### 2. `solutions/jas/wz_jas_pending.sql`
Zapytanie do `AILO.wz_jas_export` — zwraca WZ do wysłania (filtr po wz_id lub numer_wz).

### 3. `tools/jas_mapper.py`
Mapowanie listy wierszy ERP → `CreateShipmentRequest`:
- Grupuje wiersze po `wz_id` → jeden shipment, wiele cargo[]
- Mapuje pola wg tabeli poniżej

### 4. `tools/jas_export.py` — CLI
```
python tools/jas_export.py --wz-id 12345          # jedna WZ
python tools/jas_export.py --all                   # wszystkie z widoku
python tools/jas_export.py --dry-run               # tylko pokaż payload, nie wysyłaj
```

## Mapowanie pól

| JAS pole | Źródło ERP | Uwagi |
|---|---|---|
| shipment.customerRefNo | numer_wz | |
| shipment.deliveryDate | data_realizacji_zs | format ISO 8601 |
| shipment.remarks | opis | nullable |
| shipment.goodsName | JAS_GOODS_NAME (.env) | np. "Znicze" |
| shipment.loadingPlace.address | JAS_LOADING_* (.env) | adres stały nadawcy |
| shipment.deliveryPlace.address.name | odbiorca_nazwa | |
| shipment.deliveryPlace.address.street | odbiorca_ulica | |
| shipment.deliveryPlace.address.houseNo | odbiorca_nr_domu | |
| shipment.deliveryPlace.address.city | odbiorca_miasto | |
| shipment.deliveryPlace.address.zipCode | odbiorca_kod_pocztowy | |
| shipment.deliveryPlace.address.country | odbiorca_kraj | |
| shipment.recipient | = deliveryPlace | ten sam adres |
| cargo[].package.type | typ_opakowania | "Paleta"/"Paleta-EPAL"/"Paleta-INNA" |
| cargo[].package.quantity | ilosc | |
| cargo[].dimensions.length | dlugosc_cm | |
| cargo[].dimensions.width | szerokosc_cm | |
| cargo[].dimensions.height | wysokosc_cm | |
| cargo[].dimensions.weight | waga_kg_max | |
| additionalServices | [] | puste na start |

## Nowe zmienne .env

```
JAS_GOODS_NAME=Znicze
JAS_LOADING_NAME=PRODUKCJA ZNICZY I LAMPIONÓW CEIM MAREK CYPROWSKI
JAS_LOADING_STREET=
JAS_LOADING_HOUSE_NO=
JAS_LOADING_CITY=
JAS_LOADING_ZIP=
JAS_LOADING_COUNTRY=PL
```

## Test

`tmp/test_jas_client.py`:
- Test autentykacji (rzeczywiste wywołanie, sprawdź token)
- Test `--dry-run` dla przykładowej WZ (sprawdź poprawność payloadu bez wysyłania)
- Test `create_shipment` na instancji testowej

## Poza zakresem MVP

- Śledzenie wysłanych WZ (deduplikacja)
- UI
- Obsługa błędów biznesowych (zwroty, korekty)
