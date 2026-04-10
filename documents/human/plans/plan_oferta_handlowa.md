# Plan: Generator PDF oferty handlowej — Szkło Kerti

**Data:** 2026-04-10
**Autor:** Architect
**Status:** Do zatwierdzenia przez usera

---

## Cel

Nowy moduł Streamlit generujący PDF oferty handlowej szkła Kerti.
Wygląd: jak `documents/Wzory plików/oferta_kerti_FINAL28.html`.
Dane: ERP (wzorzec z `offer_data.py`) + Excel (Akronim + Cena).

---

## Decyzja architektoniczna: rendering

**Wybór: WeasyPrint (HTML → PDF)**

Design FINAL28.html używa CSS Grid, SVG ikon, CSS variables i Montserrat.
reportlab wymagałby ręcznego odtworzenia każdego elementu (brak SVG, brak CSS Grid).

WeasyPrint renderuje HTML/CSS do PDF bez przeglądarki — instalacja `pip install weasyprint`,
brak Chromium (~300MB). Obsługuje CSS Grid, inline SVG, CSS variables.

Font Montserrat: WeasyPrint może pobrać przez Google Fonts URL lub użyć lokalnego TTF.
Rekomendacja: podaj URL Google Fonts w HTML — WeasyPrint fetchuje przy generowaniu.
Fallback: `C:\Windows\Fonts\Montserrat*.ttf` jeśli dostępny.

---

## Nowe moduły

```
tools/
  offer_kerti_data.py      ← warstwa danych (ERP + Excel) → KertiGlassData
  offer_kerti_html.py      ← generator HTML (design FINAL28)
  offer_kerti_pdf.py       ← WeasyPrint: HTML → PDF
  pages/
    oferta_handlowa.py     ← Streamlit UI page
```

Zmiany istniejących plików:
- `tools/app.py` — dodaj wpis "Oferta Handlowa Kerti" do APPS
- `requirements.txt` — dodaj `weasyprint`

---

## Warstwa danych — offer_kerti_data.py

### Dataclass

```python
@dataclass
class KertiGlassData:
    kod: str
    nazwa: str
    seria: str               # z CDN.TwrGrupy (jak istn. offer_data.py)
    wysokosc_cm: float       # Atr_AtkId=12 (już znane)
    sr_otworu_cm: float      # Atr_AtkId=??? — Developer do ustalenia
    sr_spodu_cm: float       # Atr_AtkId=??? — Developer do ustalenia (opcjonalne)
    ilosc_paleta: int        # TwrJm JM='paleta' lub Atr_AtkId=??? — Developer do ustalenia
    nowosc: bool             # z Excel (kolumna 'Nowość', TRUE/FALSE) lub Atr
    cena: str                # z Excel 'Cena sprzedaży'
    zdjecie_path: str | None # z C:\CEIM\Zdjecia (istn. _find_photo)
```

### Excel format (wejście)

Taki sam jak oferta katalogowa + opcjonalna kolumna `Nowość`:

| Kolumna | Opis |
|---|---|
| `Akronim produktu` | kod ERP |
| `Cena sprzedaży` | cena (float) |
| `Nowość` | TRUE/FALSE (opcjonalna — jeśli brak: False dla wszystkich) |

### Zapytania ERP

Wzorzec identyczny z `offer_data.py`:

1. **TwrKarty** — nazwa, GIDNumer (bez zmian)
2. **TwrGrupy** — seria produktu (bez zmian)
3. **Atrybuty AtK_ID=12** — wysokość (bez zmian)
4. **Atrybuty AtK_ID=???** — śr.otworu — **Developer do ustalenia**
5. **Atrybuty AtK_ID=???** — śr.spodu — **Developer do ustalenia**
6. **TwrJm JM='paleta'** — ilość na palecie — **Developer do weryfikacji** (czy kolumna TwJ_PrzeliczL zawiera tę wartość, tak jak opak.)

Jeśli atrybuty szklane niedostępne w ERP → kolumny te mogą trafić do Excel jako opcjonalne.

### Grupowanie na strony

Auto-grupowanie wg `seria` (jak istn. `_get_line` w offer_pdf_3x3).
Każda seria → nowa sekcja. Jeśli seria nie mieści się na stronie → nowa strona.
Layout domyślny: g3 (3 kolumny), możliwy g2 i g4 per seria (UI radio).

---

## Generator HTML — offer_kerti_html.py

Generuje string HTML odwzorowujący design FINAL28.html.

### Struktura strony produktowej (wg FINAL28)

```
┌─────────────────────────────────┐
│  .ph — nagłówek                 │  ~22mm
│  logo Kerti | tytuł | logo SOLAG│
├─────────────────────────────────┤
│  .legend — legenda ikon         │  ~11mm
│  SVG śr.otworu | śr.spodu | pal.│
├─────────────────────────────────┤
│  .pb — treść (CSS Grid .g3)     │  flex:1
│  .mc karta:                     │
│    [.piw zdjęcie]               │
│    .pn nazwa                    │
│    .dg złota linia              │
│    .sr SVG + wartość            │  × 3 parametry
├─────────────────────────────────┤
│  .pf — stopka                   │  ~8mm
└─────────────────────────────────┘
```

### SVG ikony parametrów (z FINAL28)

```
śr.otworu: <circle cx="5" cy="5" r="4" stroke="#BD7E4D"/>
            + <line x1="1" y1="5" x2="9" y2="5" stroke="#BD7E4D"/>

śr.spodu:   <ellipse cx="5" cy="7.5" rx="3.5" ry="2" stroke="#BD7E4D"/>

paleta:     <rect x="0.5" y="3" width="9" height="6.5" rx="1" stroke="#BD7E4D"/>
            + <rect x="2" y="1" width="6" height="3" rx="0.8" stroke="#BD7E4D"/>
```

### CSS kolory

```css
--gold: #BD7E4D
--dark: #071019
--off:  #F6F3EE
--red:  #C0392B   /* badge Nowość */
```

### Skalowanie zdjęć

Proporcjonalne do wysokości cm — wzorzec z FINAL28:
```python
scale = produkt.wysokosc_cm / max_wysokosc_na_stronie
# transform: scale({scale}); transform-origin: bottom center
```

### Struktura HTML wyjściowego

```
HTML
├── <head> CSS (wszystkie klasy jak FINAL28)
├── strona 1: okładka (ciemne tło, logo Kerti, rok)
├── strony produktowe (wg grup/serii)
└── strona ostatnia: kontakt (dane z CONFIG)
```

### Dane firmy (strona kontakt)

Hardcoded w CONFIG w kodzie (nie z arkusza Excel):
```python
FIRMA_CONFIG = {
    "nazwa": "CEiM Sp. z o.o.",   # ← user potwierdzi dane
    "adres": "...",
    "tel": "...",
    "email": "...",
    "www": "...",
    "kontakt_imie": "...",
    "kontakt_tel": "...",
}
```
**Developer do ustalenia z userem: dane firmy na stronie kontaktowej.**

---

## Konwerter PDF — offer_kerti_pdf.py

```python
from weasyprint import HTML, CSS

def html_to_pdf(html_string: str, output_path: str) -> str:
    HTML(string=html_string).write_pdf(output_path)
    return output_path
```

Rozmiar strony kontrolowany przez CSS `@page { size: A4; margin: 0; }` w HTML.

---

## UI — pages/oferta_handlowa.py

Wzorzec identyczny z `oferta_katalogowa_3x3.py`:

```
Nagłówek: "Generator Oferty Handlowej Kerti"
─────────────────────────────────────────────
Plik wejściowy: st.file_uploader (.xlsx)
─────────────────────────────────────────────
Logo: radio [CEiM | KERTI]
Layout: radio [g2 | g3 | g4]   ← domyślnie g3
─────────────────────────────────────────────
[Generuj PDF]  →  st.download_button
```

---

## app.py — nowy wpis

```python
{
    "name": "Oferta Handlowa Kerti",
    "desc": "Generator PDF oferty szkła Kerti (design katalogowy)",
    "icon": "🪟",
    "page": "pages/oferta_handlowa.py",
    "active": True,
},
```

---

## requirements.txt

Dodaj:
```
weasyprint>=60.0
```

---

## Otwarte pytania — Developer do ustalenia

1. **AtK_ID dla śr.otworu** — sprawdź w ERP: `SELECT DISTINCT Atr_AtkId, Atr_Wartosc FROM CDN.Atrybuty WHERE Atr_ObiNumer IN (<GID szkła>)` i zidentyfikuj atrybut średnicy otworu.

2. **AtK_ID dla śr.spodu** — jak wyżej.

3. **Ilość na palecie** — czy dostępna przez TwrJm (JM='paleta') czy przez Atrybut?
   Query: `SELECT TwJ_JmZ, TwJ_PrzeliczL FROM CDN.TwrJm WHERE TwJ_TwrNumer = <GID> ORDER BY TwJ_PrzeliczL DESC`

4. **Kolumna Nowość w Excel** — czy user chce ją w Excelu czy z ERP atrybutu? Rekomendacja: Excel (łatwa kontrola).

5. **Dane firmy na stronie kontakt** — user podaje: nazwa, adres, tel, email, www, osoba kontaktowa.

6. **Logo SOLAG** — czy strona ma zawierać logo SOLAG obok Kerti? (FINAL28 ma oba.) Ścieżka: `documents/Wzory plików/logo_solag.png` — Developer do weryfikacji czy plik istnieje.

7. **Okładka** — FINAL28 ma okładkę z tłem `cover.jpg`. Czy generujemy okładkę? Jeśli tak — jaki plik tła?

---

## Kolejność implementacji

1. `offer_kerti_data.py` — data layer + test na 5 produktach (potwierdzić AtK_IDs)
2. `offer_kerti_html.py` — generator HTML, weryfikacja wizualna w przeglądarce
3. `offer_kerti_pdf.py` — WeasyPrint, test PDF
4. `pages/oferta_handlowa.py` — UI
5. `app.py` + `requirements.txt` — wpis + zależność
6. Commit

---

## Reuse z istniejącego kodu

| Komponent | Skąd | Jak |
|---|---|---|
| `_find_photo(kod)` | offer_data.py | skopiuj / zaimportuj |
| `_format_price(price, lang)` | offer_data.py | skopiuj / zaimportuj |
| `run_query(sql)` | sql_query.py | import bez zmian |
| `_get_logo_png(logo)` | offer_pdf_3x3.py | skopiuj / zaimportuj |
| ERP query pattern | offer_data.py | adaptuj AtK_IDs |
| UI pattern | oferta_katalogowa_3x3.py | adaptuj nagłówek i parametry |

**Nie modyfikuj** `offer_data.py` ani `offer_pdf_3x3.py` — nowe moduły są niezależne.
