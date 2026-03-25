# Plan: Edytowalny nagłówek + wybór logo — offer_ui_3x3.py

Data: 2026-03-24
Rola: Developer
Status: gotowy do implementacji (jutro)

---

## Zakres

1. Pole tekstowe w UI — nagłówek wpisywany przez użytkownika
2. Wybór logo — CEIM lub KERTI (radio buttons)

---

## Zmiany w kodzie

### offer_ui_3x3.py

Dodać między "Język" a separatorem:

```
Nagłówek:   [ Wkłady zniczowe CEiM          ]   (pole tekstowe, edytowalne)
Logo:       (•) CEiM   ( ) KERTI
```

Przekazać do `generate_pdf()`:
```python
generate_pdf(products, output_path, lang=lang,
             header_text=self._header_var.get(),
             logo=self._logo_var.get())
```

### offer_pdf_3x3.py

1. `generate_pdf()` — dodać parametry `header_text: str | None` i `logo: str = "ceim"`
2. `_draw_header()` — przyjmuje `header_text` zamiast czytać z `tr["header_wklady"]`
3. `_get_logo_png()` → `_get_logo_png(logo: str)` — wybiera plik na podstawie argumentu:
   - `"ceim"` → `documents/Wzory plików/logo CEiM krzywe.pdf`
   - `"kerti"` → `documents/Wzory plików/logo Kerti.pdf` (plik do dostarczenia)

---

## Wymagania wstępne

- [ ] **Plik logo KERTI** — dodać do `documents/Wzory plików/logo Kerti.pdf` przed implementacją
  (format: PDF lub PNG, najlepiej wektorowy jak CEIM)

---

## Kolejność pracy

1. Użytkownik dostarcza logo KERTI → zapisać do `documents/Wzory plików/`
2. Developer: modyfikacja `offer_pdf_3x3.py` — parametryzacja header + logo
3. Developer: modyfikacja `offer_ui_3x3.py` — dodanie pól UI
4. Test: generuj PDF z nagłówkiem "Wkłady zniczowe KERTI" + logo KERTI
