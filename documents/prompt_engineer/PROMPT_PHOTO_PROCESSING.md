# Prompt: Obróbka zdjęć produktowych (ChatGPT / GPT-4o)

Prompty do wysłania do GPT-4o wraz ze zdjęciem produktu.
Cel: przygotowanie zdjęć do oferty katalogowej PDF.

---

## Uwaga architektoniczna (dla Developera)

**Prompt A** (usunięcie tła, kadrowanie) — odpowiedni dla GPT-4o. Działa reliably.

**Skalowanie proporcjonalne** — NIE zlecaj GPT-4o. GPT-4o nie jest pixel-precise.
Matematyka jest deterministyczna: `height_px = (height_cm / max_height_cm) * 800`.
Rekomendacja: zaimplementować w `offer_pdf.py` lub osobnym skrypcie przez Pillow.
Wzór: po usunięciu tła przez GPT-4o → Python skaluje zdjęcie do docelowej wysokości px.

ESCALATE_ARCHITECTURE → Developer: dodać etap skalowania Pillow do pipeline oferty.

---

## Prompt A — Usunięcie tła i kadrowanie katalogowe

Prześlij ten prompt do GPT-4o razem ze zdjęciem produktu.

```
You are editing a product photo for a print catalog.

Edit the attached photo:
1. Background: replace with solid white (#FFFFFF). No shadows, no gradients, no reflections.
2. Cutout: clean, sharp edges. No artifacts, no halo, no fringing.
3. Framing: product centered horizontally and vertically. Equal margins on all sides (approx. 8% of canvas).
4. Lighting: keep the product's natural appearance. Do not alter colors, do not add artificial highlights.
5. Output: PNG, 1000×1000 px, white background (#FFFFFF).
6. Do not add any text, watermarks, labels, captions, or signatures to the image.

Return only the edited image. No text in the response, no explanation.
```

### Wariant: tło przezroczyste

Użyj gdy pipeline generowania PDF obsługuje PNG z kanałem alpha:

```
You are editing a product photo for a print catalog.

Edit the attached photo:
1. Background: remove completely. Output must have a transparent background (PNG alpha channel).
2. Cutout: clean, sharp edges. No artifacts, no halo, no fringing.
3. Framing: product centered horizontally and vertically. Equal margins on all sides (approx. 8% of canvas).
4. Lighting: keep the product's natural appearance. Do not alter colors.
5. Output: PNG, 1000×1000 px, transparent background.

Return only the edited image. No text, no explanation.
```

---

## Prompt B — Weryfikacja jakości (opcjonalny krok kontrolny)

Użyj gdy chcesz GPT-4o ocenił jakość przed wstawieniem do PDF. Prześlij przetworzone zdjęcie.

```
You are a quality checker for catalog product photos.

Evaluate the attached image against these criteria:
1. Background: is it solid white or fully transparent? (pass / fail)
2. Cutout: are product edges clean without artifacts or halo? (pass / fail)
3. Centering: is the product centered with balanced margins? (pass / fail)
4. Color: does the product look natural, not color-shifted? (pass / fail)

For each failed criterion, describe the specific defect in one sentence.
Output format:
Background: [pass/fail] — [note if fail]
Cutout: [pass/fail] — [note if fail]
Centering: [pass/fail] — [note if fail]
Color: [pass/fail] — [note if fail]
Overall: [ACCEPT / REJECT]
```

---

## Skalowanie proporcjonalne — wzór dla Pythona (Pillow)

Implementacja do `offer_pdf.py` lub osobnego skryptu preprocessing.

Dane wejściowe z ERP (CDN.Atrybuty, Atr_AtkId=12):

| Kod | Nazwa | Wysokość (cm) |
|---|---|---|
| CWKZ0031 | Wk CEiM zniczowy 2 | 11 |
| CWKZ0033 | Wk CEiM zniczowy 3 | 14 |
| CWKZ0034 | Wk CEiM zniczowy 4 | 17 |
| CWKZ0035 | Wk CEiM zniczowy 5 | 24 |
| CWKZ0041 | Wk CEiM zniczowy 5 szeroki | 18 |
| CWKZ0036 | Wk CEiM zniczowy 5,5 | 21 |
| CWKZ0037 | Wk CEiM zniczowy 6 | 24 |
| CWKZ0038 | Wk CEiM zniczowy 6,5 | 21 |
| CWKZ0092 | Wk Płomień 2 | 11 |
| CWKZ0093 | WK Płomień 3 | 14 |
| CWKZ0094 | WK Płomień 4 | 17 |

Wzór skalowania (canvas 1000×1000 px):

```
CANVAS_H = 1000
PRODUCT_AREA_H = 800   # strefa produktu: y=100..900 (margines 10% góra i dół)
BASE_Y = 900           # wspólna podstawa (dół produktu)
MAX_HEIGHT_CM = 24     # najwyższy produkt w katalogu

target_height_px = round((height_cm / MAX_HEIGHT_CM) * PRODUCT_AREA_H)
# Szerokość: zachować proporcje oryginalnego zdjęcia po przycięciu tła
aspect_ratio = original_w / original_h
target_width_px = round(target_height_px * aspect_ratio)

# Pozycja: wyrównanie do podstawy, wycentrowanie poziome
x = (CANVAS_H - target_width_px) // 2
y = BASE_Y - target_height_px
```

Wynikowe wysokości (px) przy powyższym wzorze:

| Kod | Wys. cm | Wys. px (z 800px max) |
|---|---|---|
| CWKZ0031 | 11 | 367 |
| CWKZ0033 | 14 | 467 |
| CWKZ0034 | 17 | 567 |
| CWKZ0035 | 24 | 800 |
| CWKZ0041 | 18 | 600 |
| CWKZ0036 | 21 | 700 |
| CWKZ0037 | 24 | 800 |
| CWKZ0038 | 21 | 700 |
| CWKZ0092 | 11 | 367 |
| CWKZ0093 | 14 | 467 |
| CWKZ0094 | 17 | 567 |

---

## Integracja z pipeline oferty

Proponowany przepływ (do zaimplementowania przez Developera):

```
1. [ręcznie] GPT-4o: Prompt A → zdjęcie z białym tłem (PNG 1000×1000)
   → zapisać do: D:\UdzialySieciowe\ZDJĘCIA\...\processed\{Twr_Kod}_processed.png

2. [skrypt Python] Pillow: proporcjonalne skalowanie wg wzoru powyżej
   → zapisać do: D:\UdzialySieciowe\ZDJĘCIA\...\catalog\{Twr_Kod}_catalog.png

3. [offer_pdf.py] Wczytaj _catalog.png zamiast oryginału
```

Ścieżki do potwierdzenia z Developerem — zależą od struktury katalogów przyjętej w `offer_data.py`.

---

## Format wynikowy — rekomendacja

Rekomendacja: **białe tło PNG** (wariant 1 Promptu A).

Uzasadnienie: `offer_pdf.py` używa ReportLab który obsługuje PNG z białym tłem bez dodatkowej
konfiguracji. Tło przezroczyste wymaga weryfikacji czy ReportLab poprawnie kompozytuje alpha
na białym tle PDF — ryzyko artefaktów w zależności od wersji biblioteki.

---

*Wersja: 1.0 | 2026-03-23 | Autor: prompt_engineer*
