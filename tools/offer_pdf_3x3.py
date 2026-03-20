"""
offer_pdf_3x3.py — Generator PDF oferty katalogowej (wariant 3×3).

Layout: A4 pionowy, siatka 3×3 kart (9 produktów na stronę).
Zawartość karty: zdjęcie → nazwa (uppercase) → 3 parametry → cena.
Obsługa 3 języków: PL / EN / RO.
"""

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from tools.offer_data import ProductData


# ---------------------------------------------------------------------------
# Tłumaczenia
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "pl": {
        "header_wklady":      "Wkłady zniczowe CEiM",
        "label_wysokosc":     "Wysokość",
        "label_czas_palenia": "Czas palenia",
        "label_opakowanie":   "Opakowanie",
        "price_suffix":       "zł / szt.",
        "no_photo":           "brak zdjęcia",
    },
    "en": {
        "header_wklady":      "CEiM Candle Inserts",
        "label_wysokosc":     "Height",
        "label_czas_palenia": "Burning time",
        "label_opakowanie":   "Pack size",
        "price_suffix":       "EUR / pcs.",
        "no_photo":           "no photo",
    },
    "ro": {
        "header_wklady":      "Fitile znicze CEiM",
        "label_wysokosc":     "Înălțime",
        "label_czas_palenia": "Timp de ardere",
        "label_opakowanie":   "Ambalaj",
        "price_suffix":       "EUR / buc.",
        "no_photo":           "fără fotografie",
    },
}

# ---------------------------------------------------------------------------
# Wymiary
# ---------------------------------------------------------------------------

PAGE_W, PAGE_H = A4

MARGIN_H    = 12 * mm
MARGIN_V    = 14 * mm
HEADER_H    = 20 * mm
COLS        = 3
ROWS        = 3             # 3×3 = 9 produktów na stronę
GAP         = 4 * mm       # mniejszy odstęp dla 3 rzędów

GRID_W = PAGE_W - 2 * MARGIN_H
GRID_H = PAGE_H - MARGIN_V - HEADER_H - MARGIN_V
CELL_W = (GRID_W - (COLS - 1) * GAP) / COLS
CELL_H = (GRID_H - (ROWS - 1) * GAP) / ROWS

PAD         = 4 * mm       # mniejszy padding dla mniejszych kart
RADIUS      = 4 * mm
SHADOW_OFF  = 0.6 * mm
PHOTO_RATIO = 0.50         # zdjęcie ≈ 50% wysokości karty

PHOTO_H_MAX = CELL_H * PHOTO_RATIO

# ---------------------------------------------------------------------------
# Kolory
# ---------------------------------------------------------------------------

COLOR_ORANGE         = colors.HexColor("#c96a2b")
COLOR_BLACK          = colors.HexColor("#1A1A1A")
COLOR_GRAY           = colors.HexColor("#6B6B6B")
COLOR_SHADOW         = colors.HexColor("#DDDDDD")
COLOR_CARD_BORDER    = colors.HexColor("#E8E8E8")
COLOR_PLACEHOLDER_BG = colors.HexColor("#F2F2F2")
COLOR_PH_TEXT        = colors.HexColor("#AAAAAA")
COLOR_PARAM_LINE     = colors.HexColor("#F0F0F0")   # linia separatora parametrów


# ---------------------------------------------------------------------------
# Czcionki
# ---------------------------------------------------------------------------

def _register_fonts():
    registered = set(pdfmetrics.getRegisteredFontNames())

    def reg(name, paths):
        if name in registered:
            return name
        for p in paths:
            if Path(p).exists():
                pdfmetrics.registerFont(TTFont(name, p))
                return name
        return None

    # Garamond — nagłówek strony (materiały drukowane wg brandbook)
    reg("Garamond-Bold", [r"C:\Windows\Fonts\GARABD.TTF"])

    # Calibri — tekst kart (sans-serif wg promptu)
    regular = reg("Calibri",      [r"C:\Windows\Fonts\calibri.ttf",  r"C:\Windows\Fonts\CALIBRI_0.TTF"])  or "Helvetica"
    bold    = reg("Calibri-Bold", [r"C:\Windows\Fonts\calibrib.ttf", r"C:\Windows\Fonts\CALIBRIB_0.TTF"]) or "Helvetica-Bold"

    rn = set(pdfmetrics.getRegisteredFontNames())
    header_font = "Garamond-Bold" if "Garamond-Bold" in rn else bold
    return regular, bold, header_font


# ---------------------------------------------------------------------------
# Nagłówek strony
# ---------------------------------------------------------------------------

def _draw_header(c: canvas.Canvas, lang: str, font_header: str):
    tr   = TRANSLATIONS[lang]
    text = tr["header_wklady"]
    y    = PAGE_H - MARGIN_V - HEADER_H

    # Pomarańczowa linia akcentująca (wg brandbook)
    c.setStrokeColor(COLOR_ORANGE)
    c.setLineWidth(2.5)
    c.line(MARGIN_H, y + 2 * mm, PAGE_W - MARGIN_H, y + 2 * mm)

    # Tekst wycentrowany — Garamond Bold
    c.setFillColor(COLOR_BLACK)
    c.setFont(font_header, 22)
    tw = c.stringWidth(text, font_header, 22)
    c.drawString((PAGE_W - tw) / 2, y + HEADER_H * 0.5 - 4, text)


# ---------------------------------------------------------------------------
# Karta produktu
# ---------------------------------------------------------------------------

def _draw_shadow(c: canvas.Canvas, x, y, w, h, r):
    """Rysuje cień pod kartą (offset szary prostokąt z zaokrągleniem)."""
    c.setFillColor(COLOR_SHADOW)
    c.setStrokeColor(COLOR_SHADOW)
    c.roundRect(x + SHADOW_OFF, y - SHADOW_OFF, w, h, r, fill=1, stroke=0)


def _draw_card_bg(c: canvas.Canvas, x, y, w, h, r):
    """Rysuje białą kartę z delikatną ramką."""
    c.setFillColor(colors.white)
    c.setStrokeColor(COLOR_CARD_BORDER)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def _draw_product_card(
    c: canvas.Canvas,
    product: ProductData,
    cx: float, cy: float,
    lang: str,
    font_regular: str, font_bold: str,
    photo_h: float,
):
    tr = TRANSLATIONS[lang]

    # Cień + karta
    _draw_shadow(c, cx, cy, CELL_W, CELL_H, RADIUS)
    _draw_card_bg(c, cx, cy, CELL_W, CELL_H, RADIUS)

    inner_x = cx + PAD
    inner_w  = CELL_W - 2 * PAD

    # ---- ZDJĘCIE ----
    # Obszar foto: górna część karty, wycentrowany w poziomie
    photo_area_y = cy + CELL_H - PAD - PHOTO_H_MAX
    photo_x = cx + (CELL_W - inner_w) / 2

    # Białe tło zdjęcia
    c.setFillColor(colors.white)
    c.rect(photo_x, photo_area_y, inner_w, PHOTO_H_MAX, fill=1, stroke=0)

    if product.zdjecie_path:
        try:
            c.drawImage(
                product.zdjecie_path,
                photo_x,
                photo_area_y,                        # kotwica do dołu obszaru
                width=inner_w, height=photo_h,
                preserveAspectRatio=True,
                anchor="s",
                mask="auto",
            )
        except Exception:
            _placeholder(c, photo_x, photo_area_y, inner_w, PHOTO_H_MAX, tr["no_photo"], font_regular)
    else:
        _placeholder(c, photo_x, photo_area_y, inner_w, PHOTO_H_MAX, tr["no_photo"], font_regular)

    # ---- NAZWA (18px → 13.5pt, uppercase, bold, wycentrowana) ----
    name_sz = 11
    name_y  = photo_area_y - 6 * mm
    c.setFillColor(COLOR_BLACK)
    c.setFont(font_bold, name_sz)
    name_text = product.nazwa.upper()
    nw = c.stringWidth(name_text, font_bold, name_sz)
    c.drawString(cx + (CELL_W - nw) / 2, name_y, name_text)

    # ---- CENA (24px → 18pt, pomarańczowa, wycentrowana — hierarchia: nazwa > cena) ----
    parts        = product.cena.split()
    price_number = parts[0] if parts else product.cena
    price_suffix = tr["price_suffix"]

    num_sz = 11
    suf_sz = 8.5
    price_y = name_y - 7 * mm

    c.setFont(font_bold, num_sz)
    nw2 = c.stringWidth(price_number + " ", font_bold, num_sz)
    c.setFont(font_regular, suf_sz)
    sw  = c.stringWidth(price_suffix, font_regular, suf_sz)
    px  = cx + (CELL_W - nw2 - sw) / 2

    c.setFillColor(COLOR_BLACK)
    c.setFont(font_bold, num_sz)
    c.drawString(px, price_y, price_number + " ")

    c.setFillColor(COLOR_GRAY)
    c.setFont(font_regular, suf_sz)
    c.drawString(px + nw2, price_y + 1, price_suffix)

    # ---- PARAMETRY (14px → 10.5pt, wycentrowane, line-height 1.6) ----
    params = [
        (tr["label_wysokosc"],     product.wysokosc),
        (tr["label_czas_palenia"], product.czas_palenia),
        (tr["label_opakowanie"],   product.ilosc_opak),
    ]

    label_sz = 8.5
    value_sz = 8.5
    row_h    = 5.5 * mm   # line-height 1.6
    param_y  = price_y - 6 * mm

    for i, (label, value) in enumerate(params):
        ry = param_y - i * row_h

        # Linia separatora
        c.setStrokeColor(COLOR_PARAM_LINE)
        c.setLineWidth(0.4)
        c.line(inner_x, ry + row_h - 0.8 * mm, inner_x + inner_w, ry + row_h - 0.8 * mm)

        # Etykieta — do lewej
        c.setFillColor(COLOR_GRAY)
        c.setFont(font_regular, label_sz)
        c.drawString(inner_x, ry, label + ":")

        # Wartość — do prawej
        c.setFillColor(COLOR_BLACK)
        c.setFont(font_bold, value_sz)
        c.drawRightString(cx + CELL_W - PAD, ry, value)


def _get_line(nazwa: str) -> str:
    """Wyciąga identyfikator linii z nazwy — usuwa końcowy numer i wszystko po nim."""
    return re.sub(r'\s+\d.*$', '', nazwa).strip().lower()


def _placeholder(c, x, y, w, h, text, font):
    c.setFillColor(COLOR_PLACEHOLDER_BG)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setFillColor(COLOR_PH_TEXT)
    c.setFont(font, 9)
    c.drawString(x + w / 2 - c.stringWidth(text, font, 9) / 2, y + h / 2 - 4, text)


# ---------------------------------------------------------------------------
# Generowanie PDF
# ---------------------------------------------------------------------------

def generate_pdf(
    products: list[ProductData],
    output_path: str,
    lang: str = "pl",
    model: str = "wklady",
):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    font_regular, font_bold, font_header = _register_fonts()

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(TRANSLATIONS[lang].get(f"header_{model}", "Oferta"))

    # Skalowanie zdjęć wg wysokości produktu
    PHOTO_H_MIN = PHOTO_H_MAX * 0.45
    heights = [p.wysokosc_val for p in products if p.wysokosc_val > 0]
    h_min   = min(heights) if heights else 1.0
    h_max   = max(heights) if heights else 1.0
    h_range = (h_max - h_min) or 1.0

    def photo_h(p: ProductData) -> float:
        if p.wysokosc_val <= 0:
            return PHOTO_H_MAX
        return PHOTO_H_MIN + ((p.wysokosc_val - h_min) / h_range) * (PHOTO_H_MAX - PHOTO_H_MIN)

    # Wstaw None-padding przy zmianie linii produktów (nowa linia → nowy wiersz)
    padded: list = []
    current_line = None
    for p in products:
        line = _get_line(p.nazwa)
        if current_line is not None and line != current_line:
            while len(padded) % COLS != 0:
                padded.append(None)
        padded.append(p)
        current_line = line

    per_page   = COLS * ROWS
    total_pages = (len(padded) + per_page - 1) // per_page
    grid_top_y = PAGE_H - MARGIN_V - HEADER_H

    for page_idx in range(total_pages):
        if page_idx > 0:
            c.showPage()

        _draw_header(c, lang, font_header)

        for i, product in enumerate(padded[page_idx * per_page: (page_idx + 1) * per_page]):
            if product is None:
                continue
            col    = i % COLS
            row    = i // COLS
            cell_x = MARGIN_H + col * (CELL_W + GAP)
            cell_y = grid_top_y - (row + 1) * CELL_H - row * GAP

            _draw_product_card(
                c, product,
                cell_x, cell_y,
                lang, font_regular, font_bold,
                photo_h=photo_h(product),
            )

    c.save()
    return output_path
