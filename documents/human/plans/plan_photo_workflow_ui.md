# Plan: Photo Workflow UI — pełny interfejs obróbki zdjęć katalogowych

## Przepływ użytkownika

```
1. Otwórz aplikację
2. [KROK 1] Prompt A wyświetlony w oknie → przycisk "Kopiuj prompt"
   → user kopiuje do ChatGPT, przetwarza zdjęcia jedno po jednym, zapisuje wyniki do folderu
3. [KROK 2] User wskazuje 3 foldery:
   - Źródłowy (oryginalne zdjęcia .jpg/.png)
   - Przetworzone (wyniki z GPT-4o)
   - Katalogowe (output skalowania — finalny)
4. [KROK 3] Kliknięcie "Skaluj" → batch_process z photo_preprocess.py
   - Pasek postępu, status per plik
   - Wynik: N przetworzonych, lista pominiętych/błędów
```

## Plik

`tools/photo_workflow_ui.py` — nowe narzędzie (zastępuje/rozszerza photo_preprocess_ui.py)

## Sekcje UI

### Sekcja 1 — Prompt GPT-4o
- Label: "Krok 1: Skopiuj prompt do ChatGPT i przetwórz zdjęcia"
- Pole tekstowe (readonly, ~5 linii) z treścią Prompt A
- Przycisk "Kopiuj do schowka"

### Sekcja 2 — Foldery
- Katalog źródłowy (oryginały): pole + przycisk `…`
- Katalog przetworzonych (GPT output): pole + przycisk `…`
- Katalog katalogowy (output): pole + przycisk `…`
- Lista plików PNG w katalogu przetworzonych (podgląd)

### Sekcja 3 — Skalowanie
- Przycisk "Skaluj"
- Pasek postępu (determinate)
- Status: [N/M] nazwa_pliku → Gotowe: X przetworzone, Y pominięte

## Prompt A

Wczytywany z: `documents/prompt_engineer/PROMPT_PHOTO_PROCESSING.md`
Sekcja: "Prompt A — Usunięcie tła i kadrowanie katalogowe" (wariant białe tło)

## .bat launcher

`documents/human/ar/skrypty/Obróbka zdjęć katalogowych.bat` — aktualizacja
(zastąpienie photo_preprocess_ui.py → photo_workflow_ui.py)
