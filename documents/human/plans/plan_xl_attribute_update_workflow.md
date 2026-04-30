# Plan: xl-attribute update workflow

## Cel
Umożliwić selektywną aktualizację atrybutów kartoteki — użytkownik podaje listę akronimów,
dostaje plik Excel z aktualnymi wartościami, edytuje, zatwierdza.

## Zmiany

### 1. `xl_attribute_template.py` — nowy tryb `--akronimy`
- Nowe zapytanie: `_QUERY_PRODUCTS_BY_AKRONIMY` — filtr WHERE Twr_Kod IN (...)
- Nowe zapytanie: `_QUERY_VALUES_BY_AKRONIMY` — istniejące wartości dla wybranych produktów
- Nowa funkcja: `generate_for_akronimy(akronimy, output)` — reużywa logiki Excel z `generate_template()`
- CLI: `--akronimy "KOD1,KOD2,KOD3"` lub `--akronimy-file lista.txt`

### 2. `xl_attribute_set.py` — przywrócenie `delete_attributes`
- Przywrócona funkcja `delete_attributes(akronim)` — DELETE FROM CDN.Atrybuty
- Używana tylko w trybie `--update` przez bulk

### 3. `xl_attribute_bulk.py` — nowy tryb `--update`
- Bez `--update` (domyślnie): insert-only, bez delete (obecne zachowanie)
- Z `--update`: delete+insert dla każdego produktu z pliku — świadoma podmiana

## Nowe CLI

```
# Krok 1: wygeneruj plik z aktualnymi wartościami dla wybranych kartoteki
python tools/xl_attribute_template.py --akronimy "PROD1,PROD2,PROD3"

# Krok 2: (edytujesz plik w Excelu)

# Krok 3: zatwierdź aktualizację
python tools/xl_attribute_bulk.py --file plik.xlsx --update
```

## Testy
- `test_xl_attribute_template.py` — testy dla `generate_for_akronimy`
- `test_xl_attribute_bulk.py` — testy dla trybu `--update`
