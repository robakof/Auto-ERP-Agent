# Plan: Generator PDF oferty katalogowej

## Zakres

Moduł Python generujący PDF oferty katalogowej dla wkładów zniczowych.
Dane: ERP + Excel. Output: A4 PDF, siatka produktów, 3 języki.
Interface (UI) — osobne zadanie, poza zakresem tej sesji.

---

## Tech stack

- **reportlab** — generowanie PDF (czyste Python, precyzyjna kontrola layoutu, dobre wsparcie obrazów)
- **openpyxl** — odczyt Excel (już w projekcie)
- **pyodbc** — zapytania ERP (już w projekcie)

---

## Struktura modułów

```
tools/
  offer_data.py        # warstwa danych — ERP + Excel → lista ProductData
  offer_pdf.py         # generator PDF — ProductData → plik .pdf
  offer_generator.py   # CLI entry point
```

### offer_data.py

Odpowiedzialność:
- Odczyt Excel (lista produktów + ceny)
- Zapytania ERP (TwrKarty + TwrJm + Atrybuty AtK_ID=12)
- Parsowanie czasu palenia z nazwy (regex: liczba po "zniczowy" / "Płomień")
- Przeliczenie dni → godziny (dni × 24)
- Rozwiązanie ścieżki zdjęcia (.jpg → fallback .png → None)
- Zwraca: `list[ProductData]`

```python
@dataclass
class ProductData:
    kod: str
    nazwa: str
    wysokosc: str        # "24 cm"
    czas_palenia: str    # "5 dni 120h"
    ilosc_opak: str      # "20 szt."
    cena: str            # "2,27 zł"
    zdjecie_path: str | None
```

### offer_pdf.py

Odpowiedzialność:
- Layout A4, białe tło
- Nagłówek kategorii (lewa strona, pogrubiony)
- Siatka 2×3 kart produktów
- Karta produktu: zdjęcie + nazwa + 4 parametry z etykietami
- Obsługa placeholder gdy brak zdjęcia
- Tłumaczenia etykiet (PL/EN/RO)

### offer_generator.py (CLI)

```
python tools/offer_generator.py \
  --input "documents/Wzory plików/OFerta katalogowa.xlsx" \
  --output output/oferta_wklady.pdf \
  --lang pl \
  --model wklady
```

Argumenty:
- `--input` — ścieżka do Excel z listą produktów
- `--output` — ścieżka wyjściowa PDF
- `--lang` — język: pl (domyślnie) / en / ro
- `--model` — model karty: wklady (domyślnie) / znicze (przyszłość)

---

## Tłumaczenia etykiet

| Klucz | PL | EN | RO |
|---|---|---|---|
| header_wklady | Wkłady zniczowe CEiM | CEiM Candle Inserts | Fitile znicze CEiM |
| label_wysokosc | Wysokość | Height | Înălțime |
| label_czas_palenia | Czas palenia | Burning time | Timp de ardere |
| label_ilosc_opak | Ilość w opakowaniu | Pieces per pack | Bucăți per pachet |
| label_cena | Cena | Price | Preț |

---

## Kolejność implementacji

1. `offer_data.py` + test na 11 produktach (weryfikacja danych)
2. `offer_pdf.py` — generowanie PDF z danymi testowymi
3. `offer_generator.py` — CLI łączący oba moduły
4. Commit + push

---

## Otwarte kwestie (do ustalenia z użytkownikiem)

- Czy cena ma mieć jednostkę "zł" na stałe, czy walutę z ERP?
- Placeholder gdy brak zdjęcia: szare pole z napisem "brak zdjęcia" czy pominąć kartę?
- Folder wyjściowy dla PDF: `output/` w projekcie?
