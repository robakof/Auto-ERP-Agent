# Plan implementacji: Generator Wyceny Zniczy

## Zakres

Skrypt `tools/wycena_generate.py` — generuje plik Excel z wyceną dla wybranej oferty.

## CLI

```
python tools/wycena_generate.py --offer-group-id 10729 --client-name "AUCHAN" [--output PATH]
```

Domyślny output: `Wycena_{client_name}_{YYYY-MM-DD}.xlsm` w katalogu bieżącym.

## Kroki działania

1. Kopia szablonu `Wycena 2026 Otorowo Szablon.xlsm` → plik wynikowy
2. Zapytanie ERP — lista produktów CZNI z offer_group_id
3. Dla każdego produktu:
   a. Zapytanie ERP — jednostki (opak. → paletka, paleta → paleta)
   b. Algorytm Szkła — 2 próby SQL, jeśli brak → H puste
   c. Oblicz mianowniki (Folia pakowa, Folia Stretch)
4. Zapis 16 wierszy BOM na produkt do arkusza `Wycena Zniczy`, od wiersza 3
5. Zapis tylko kolumn: A, B, E, G, H, J — reszta nienaruszona

## Mapowanie kolumn

| Kolumna | Zawartość |
|---------|-----------|
| A | client_name (tylko 1. wiersz produktu) |
| B | produkt_kod (wszystkie 16 wierszy) |
| E | Właściwość: "Surowiec" lub "Koszt" |
| G | Nazwa właściwości (Dekiel, Brokat, Etykieta…) |
| H | Akronim surowca (ET0077, FO0003, FO0004, szkło z ERP lub puste) |
| J | Mianownik (liczba lub puste) |

## Mianowniki J

| Wiersz | J |
|--------|---|
| Dekiel | 1 |
| Brokat | puste |
| Etykieta | 1 |
| Folia pakowa | CEIL((1000/45) × paletka) |
| Folia Stretch | paleta × 2 |
| Paletka | paletka (z ERP TwJ_PrzeliczL 'opak.') |
| Farba lakier | puste |
| Spód | 1 |
| Szkło | 0.99 (offer_group_id podany) |
| Wkład | 1 |
| Energia Otorowo | 1 |
| Godzina pracy malarni | puste |
| Dodatkowe koszty | 1 |
| Roboczogodzina | puste |
| Premia | 1 |
| BDO | 1 |

## Biblioteki

- `openpyxl` z `keep_vba=True` — modyfikacja .xlsm bez niszczenia makr/formuł
- `tools.lib.sql_client.SqlClient` — zapytania ERP (już w projekcie)
- `shutil.copy2` — kopia szablonu

## Struktura kodu

```
tools/wycena_generate.py   — główny skrypt (CLI + orkiestracja)
tools/lib/wycena_bom.py    — logika BOM (definicja 16 wierszy, obliczenia mianowników)
```

## Obsługa błędów

- Produkt bez jednostki 'opak.' → Paletka i wyliczenia = puste, log warning
- Produkt bez jednostki 'paleta' → Paleta i wyliczenia = puste, log warning
- Szkło nieznalezione → H puste (algorytm oba kroki nie dały wyniku)
- Szablon nie istnieje → błąd z komunikatem

## Nie wchodzi w zakres

- Kolumny C, D, F, I, K–V — nie dotykamy
- Testy automatyczne — v1 bez (poproś jeśli potrzebne)
