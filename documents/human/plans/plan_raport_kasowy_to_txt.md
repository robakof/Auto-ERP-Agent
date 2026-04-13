# Narzędzie: raport kasowy XLSX → TXT (format CDN POSS)

## Cel

Konwersja `Raport kasowy.xlsx` (eksport z ERP) do formatu TXT zgodnego ze
wzorcem `documents/Wzory plików/kasaFranowoprzykład.txt` — strict 1:1
schemat 15 pól, encoding CP1250.

## Narzędzie

`tools/raport_kasowy_to_txt.py`

CLI:
```
py tools/raport_kasowy_to_txt.py --input "raport.xlsx" --output "raport.txt"
```

## Mapowanie pól

| # | Pole TXT | Źródło XLSX | Transformacja |
|---|---|---|---|
| 0 | flaga | — | zawsze `0` |
| 1 | data | `Data` | `yy/MM/dd` |
| 2 | godzina | `Czas zapisu` | `H:MM:SS` (pad spacją gdy H<10) |
| 3 | typ | parsowane z `Dokument` | PA/FS → 1, KW → 2 |
| 4 | akronim | `Akronim` | 1:1 |
| 5 | prefix | `Dokument` | część przed pierwszą cyfrą (`PA-`, `KW/`, `FS-`) |
| 6 | numer | `Dokument` | pierwsza grupa cyfr po prefixie |
| 7 | sufix | `Dokument` | reszta po numerze (`/03/26/CME`, `/26`) |
| 8 | full ID | `Treść` | 1:1 |
| 9 | nazwa kontrahenta | — | puste `""` (xlsx nie ma) |
| 10 | punkt | — | zawsze `"POSS"` |
| 11 | kwota | `Przychód`/`Rozchód` | `Przychód` jeśli >0, inaczej `Rozchód` |
| 12-14 | rezerwa | — | `0,0,0` |

## Format wyjściowy

- Encoding: **CP1250** (Windows-1250)
- Każdy wiersz: 15 pól oddzielonych przecinkami
- Pola tekstowe w `"..."`, pola numeryczne bez
- Liczby: kropka jako separator dziesiętny, bez tysięcznych
- Newline: `\r\n` (Windows)

## Test

1. Konwersja `Raport kasowy.xlsx` (803 wiersze, 801 transakcji)
2. Weryfikacja: liczba wierszy w TXT = liczba transakcji w XLSX
3. Walidacja per-typ: PA=788, KW=13
4. Wybrane wiersze ręcznie porównane do oczekiwanego formatu
5. Encoding test: plik otwiera się jako CP1250 bez "mojibake"
