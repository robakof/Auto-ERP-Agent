# Plan: Photo Preprocess — skalowanie proporcjonalne zdjęć katalogowych

## Zakres

Skrypt Python + UI do wsadowego przetwarzania zdjęć produktów po GPT-4o.
Skaluje proporcjonalnie wg wysokości z ERP, zapisuje indywidualne pliki do katalogu wyjściowego.

---

## Pliki do stworzenia

### 1. `tools/photo_preprocess.py` — logika (CLI + biblioteka)

Odpowiedzialność:
- `load_heights_from_erp(kody) -> dict[str, float]` — zapytanie ERP (CDN.Atrybuty, AtkId=12)
- `process_image(input_path, output_path, height_cm)` — Pillow: skalowanie wg wzoru PE
- `batch_process(input_dir, output_dir, progress_cb=None)` — iteracja po PNG w input_dir

Wzór skalowania (z PROMPT_PHOTO_PROCESSING.md):
```
CANVAS = 1000
PRODUCT_AREA_H = 800   # y=100..900
BASE_Y = 900
MAX_HEIGHT_CM = 24

target_h = round((height_cm / MAX_HEIGHT_CM) * PRODUCT_AREA_H)
target_w = round(target_h * (orig_w / orig_h))
x = (CANVAS - target_w) // 2
y = BASE_Y - target_h
# Canvas 1000x1000 białe tło, produkt wklejony w wyliczonej pozycji
```

Mapowanie nazwy pliku → Twr_Kod:
- `CWKZ0034.png` → `CWKZ0034` (stem = Twr_Kod, bez sufiksu)

Output: `{output_dir}/{Twr_Kod}.png` (ta sama nazwa pliku, inny katalog)

MAX_HEIGHT_CM — dynamiczny:
- Przed skalowaniem: pobierz wysokości ERP dla wszystkich produktów w wsadzie
- `MAX_HEIGHT_CM = max(heights.values())` — najwyższy produkt w danym wsadzie wyznacza skalę

CLI:
```
python tools/photo_preprocess.py --input-dir PATH --output-dir PATH
```

### 2. `tools/photo_preprocess_ui.py` — interfejs tkinter

Elementy UI:
- Pole "Katalog wejściowy" + przycisk `…` (picker)
- Pole "Katalog wyjściowy" + przycisk `…` (picker)
- Lista plików PNG znalezionych w katalogu wejściowym (podgląd)
- Przycisk "Przetwórz"
- Pasek postępu + status (N/M plików, nazwa bieżącego)
- Wynik: liczba przetworzonych / błędów

### 3. `documents/human/ar/skrypty/Obróbka zdjęć katalogowych.bat`

```bat
@echo off
cd /d "%~dp0\..\..\..\..\"
start "" pythonw tools\photo_preprocess_ui.py
```

---

## Pliki do aktualizacji

### `tools/offer_data.py` — priorytet katalogu catalog/

`_find_photo(kod)` będzie szukać w kolejności:
1. `{PHOTOS_DIR}\catalog\{kod}_catalog.png`
2. `{PHOTOS_DIR}\{kod}.jpg`
3. `{PHOTOS_DIR}\{kod}.png`

---

## Poza zakresem tego planu

- Integracja z GPT-4o (Prompt A) — osobny temat
- Zmiana pipeline offer_pdf.py poza aktualizacją _find_photo

---

## Pytania otwarte

— brak (plan potwierdzony)
