# Bugfix: Kerti generator — Playwright NotImplementedError w Streamlicie

## Problem

Generator oferty Kerti w Streamlicie (`tools/pages/oferta_handlowa.py`) zwraca:

```
NotImplementedError
File "asyncio/base_events.py", line 528, in _make_subprocess_transport
```

Z CLI działa — w Streamlit UI nie.

## Przyczyna

Streamlit uruchamia tornado, które na Windows ustawia `SelectorEventLoop`
w głównym wątku. Playwright sync API wymaga `ProactorEventLoop` do odpalenia
Chromium przez `subprocess_exec`. Mimo że Playwright tworzy własny loop, kolizja
z event loopem tornado w tym samym wątku powoduje że subprocess transport nie działa.

Lokalna reprodukcja z CLI: PASS (tam jest domyślny ProactorEventLoop, brak tornado).

## Fix

Odpalić Playwright w osobnym procesie Pythona (subprocess) — izolacja event loopu.

**Plik:** `tools/offer_kerti_pdf.py`

**Zmiana:**

1. Wydzielić renderowanie PDF do funkcji `_render(html_path, output_path)`
   która zawiera istniejącą logikę sync_playwright.
2. `html_to_pdf(html_string, output_path)` zapisuje HTML do tempfile
   i uruchamia subprocess:
   `[sys.executable, __file__, "--html", tmp, "--output", output]`.
3. Dodać `if __name__ == "__main__"` z argparse → wywołanie `_render`.
4. Backward compat: sygnatura `html_to_pdf(html_string, output_path) -> str` bez zmian.

Nie dotykam Streamlit UI (traceback display został już wdrożony w poprzednim kroku).

## Test

1. **Unit/CLI:** `py tmp/repro_kerti.py` — dalej PASS (subprocess wywoła ten sam kod).
2. **Streamlit:** upload Excel z `SZ0371`, klik "Generuj PDF" → PDF wygenerowany, brak traceback.

## Zakres

- 1 plik: `tools/offer_kerti_pdf.py`
- ~25 linii zmian
- Brak nowych zależności (`subprocess` stdlib, Playwright już jest)
