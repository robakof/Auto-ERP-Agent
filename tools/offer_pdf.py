"""
offer_pdf.py — Generator PDF oferty katalogowej.

Layout: A4 pionowy, siatka 2×3 kart produktów.
Każda karta: zdjęcie + nazwa + 4 parametry z etykietami.
Obsługa 3 języków: PL / EN / RO.
"""

from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from tools.offer_data import ProductData


# ---------------------------------------------------------------------------
# Tłumaczenia
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "pl": {
        "header_wklady": "Wkłady zniczowe CEiM",
        "label_wysokosc": "Wysokość",
        "label_czas_palenia": "Czas palenia",
        "label_ilosc_opak": "Ilość w opakowaniu",
        "label_cena": "Cena netto",
        "no_photo": "brak zdjęcia",
    },
    "en": {
        "header_wklady": "CEiM Candle Inserts",
        "label_wysokosc": "Height",
        "label_czas_palenia": "Burning time",
        "label_ilosc_opak": "Pieces per pack",
        "label_cena": "Net price",
        "no_photo": "no photo",
    },
    "ro": {
        "header_wklady": "Fitile znicze CEiM",
        "label_wysokosc": "Înălțime",
        "label_czas_palenia": "Timp de ardere",
        "label_ilosc_opak": "Bucăți per pachet",
        "label_cena": "Preț net",
        "no_photo": "fără fotografie",
    },
}

# ---------------------------------------------------------------------------
# Wymiary layoutu
# ---------------------------------------------------------------------------

PAGE_W, PAGE_H = A4                 # 595.3 x 841.9 pt

MARGIN_LEFT = 15 * mm
MARGIN_RIGHT = 15 * mm
MARGIN_TOP = 20 * mm
MARGIN_BOTTOM = 15 * mm

HEADER_HEIGHT = 20 * mm
COLS = 2
ROWS = 3

GRID_W = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT
GRID_H = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM - HEADER_HEIGHT
CELL_W = GRID_W / COLS
CELL_H = GRID_H / ROWS

CELL_PAD = 4 * mm
PHOTO_H = CELL_H * 0.52
PARAM_LABEL_W = 38 * mm

# ---------------------------------------------------------------------------
# Kolory brandbook CEiM
# ---------------------------------------------------------------------------

COLOR_ORANGE = colors.HexColor("#FAA400")   # pomarańcz główny
COLOR_BLACK = colors.HexColor("#1A1A1A")    # czerń — teksty
COLOR_GRAY = colors.HexColor("#6B6B6B")     # szary — etykiety
COLOR_CREAM = colors.HexColor("#FFF8EE")    # krem — tło uzupełniające
COLOR_PLACEHOLDER_BG = colors.HexColor("#F2F2F2")
COLOR_PLACEHOLDER_TEXT = colors.HexColor("#AAAAAA")


def _register_fonts():
    """Rejestruje czcionki brandbook CEiM: Garamond (nagłówki druk) + Calibri (tekst)."""
    registered = set(pdfmetrics.getRegisteredFontNames())

    def try_register(name, paths):
        if name in registered:
            return name
        for path in paths:
            if Path(path).exists():
                pdfmetrics.registerFont(TTFont(name, path))
                return name
        return None

    # Garamond — nagłówki (materiały drukowane wg brandbook)
    try_register("Garamond", [r"C:\Windows\Fonts\GARA.TTF"])
    try_register("Garamond-Bold", [r"C:\Windows\Fonts\GARABD.TTF"])

    # Calibri — tekst podstawowy (wg brandbook)
    regular = try_register("Calibri", [r"C:\Windows\Fonts\calibri.ttf", r"C:\Windows\Fonts\CALIBRI_0.TTF"]) or "Helvetica"
    bold = try_register("Calibri-Bold", [r"C:\Windows\Fonts\calibrib.ttf", r"C:\Windows\Fonts\CALIBRIB_0.TTF"]) or "Helvetica-Bold"

    reg_names = set(pdfmetrics.getRegisteredFontNames())
    font_header = "Garamond-Bold" if "Garamond-Bold" in reg_names else bold
    return regular, bold, font_header


# ---------------------------------------------------------------------------
# Rysowanie elementów
# ---------------------------------------------------------------------------

def _draw_header(c: canvas.Canvas, lang: str, font_regular: str, font_bold: str, font_header: str):
    """Rysuje nagłówek wg brandbook CEiM: Garamond, pomarańczowa linia akcentująca."""
    tr = TRANSLATIONS[lang]
    x = MARGIN_LEFT
    y = PAGE_H - MARGIN_TOP - HEADER_HEIGHT

    # Gruba linia akcentująca w kolorze firmowym (#FAA400) — wg brandbook
    line_y = y + 2 * mm
    c.setStrokeColor(COLOR_ORANGE)
    c.setLineWidth(2.0)
    c.line(x, line_y, x + GRID_W, line_y)

    # Tekst nagłówka — Garamond Bold, kolor #1A1A1A
    c.setFillColor(COLOR_BLACK)
    c.setFont(font_header, 22)
    text_y = y + HEADER_HEIGHT / 2 - 4
    c.drawString(x, text_y, tr["header_wklady"])


def _draw_product_card(
    c: canvas.Canvas,
    product: ProductData,
    cell_x: float,
    cell_y: float,
    lang: str,
    font_regular: str,
    font_bold: str,
    photo_h: float = None,
):
    """Rysuje kartę jednego produktu w komórce siatki."""
    tr = TRANSLATIONS[lang]

    # Bez obramowania między kartami

    inner_x = cell_x + CELL_PAD
    inner_w = CELL_W - 2 * CELL_PAD

    # --- Zdjęcie lub placeholder ---
    if photo_h is None:
        photo_h = PHOTO_H
    # Zdjęcia kotwiczone do wspólnej linii bazowej na dole obszaru foto
    photo_area_bottom = cell_y + CELL_H - CELL_PAD - PHOTO_H
    photo_y = photo_area_bottom  # wszystkie zdjęcia zaczynają się z tej samej linii
    photo_x = cell_x + CELL_PAD
    photo_w = inner_w

    # Białe tło pod zdjęciem — neutralizuje kremowe tło strony
    c.setFillColor(colors.white)
    c.rect(photo_x, photo_y, photo_w, photo_h, fill=1, stroke=0)

    if product.zdjecie_path:
        try:
            c.drawImage(
                product.zdjecie_path,
                photo_x, photo_y,
                width=photo_w, height=photo_h,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
        except Exception:
            _draw_placeholder(c, photo_x, photo_y, photo_w, photo_h, tr["no_photo"], font_regular)
    else:
        _draw_placeholder(c, photo_x, photo_y, photo_w, photo_h, tr["no_photo"], font_regular)

    # --- Nazwa produktu ---
    name_y = photo_y - 6 * mm
    c.setFillColor(COLOR_BLACK)
    c.setFont(font_bold, 8)
    name_text = product.nazwa
    c.drawString(inner_x, name_y, name_text)

    # --- Parametry ---
    params = [
        (tr["label_wysokosc"], product.wysokosc),
        (tr["label_czas_palenia"], product.czas_palenia),
        (tr["label_ilosc_opak"], product.ilosc_opak),
        (tr["label_cena"], product.cena),
    ]

    param_start_y = name_y - 5 * mm
    row_h = 4.0 * mm

    for i, (label, value) in enumerate(params):
        row_y = param_start_y - i * row_h

        # Etykieta (szary #6B6B6B wg brandbook)
        c.setFillColor(COLOR_GRAY)
        c.setFont(font_regular, 6.5)
        c.drawString(inner_x, row_y, label + ":")

        # Wartość (czerń #1A1A1A wg brandbook)
        c.setFillColor(COLOR_BLACK)
        c.setFont(font_bold, 7.5)
        c.drawString(inner_x + PARAM_LABEL_W, row_y, value)


def _draw_placeholder(
    c: canvas.Canvas,
    x: float, y: float, w: float, h: float,
    text: str,
    font: str,
):
    """Rysuje szare pole zastępcze z napisem."""
    c.setFillColor(COLOR_PLACEHOLDER_BG)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.setFillColor(COLOR_PLACEHOLDER_TEXT)
    c.setFont(font, 9)
    text_x = x + w / 2 - c.stringWidth(text, font, 9) / 2
    text_y = y + h / 2 - 4
    c.drawString(text_x, text_y, text)


# ---------------------------------------------------------------------------
# Główna funkcja generowania PDF
# ---------------------------------------------------------------------------

def generate_pdf(
    products: list[ProductData],
    output_path: str,
    lang: str = "pl",
    model: str = "wklady",
):
    """
    Generuje PDF oferty katalogowej.

    Args:
        products: lista produktów (z offer_data.load_products)
        output_path: ścieżka wyjściowa pliku PDF
        lang: język (pl/en/ro)
        model: model karty — obecnie tylko 'wklady'
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    font_regular, font_bold, font_header = _register_fonts()

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(TRANSLATIONS[lang].get(f"header_{model}", "Oferta"))

    # Skalowanie zdjęć proporcjonalnie do wysokości produktu
    PHOTO_H_MIN = PHOTO_H * 0.45
    PHOTO_H_MAX = PHOTO_H * 1.0
    heights = [p.wysokosc_val for p in products if p.wysokosc_val > 0]
    h_min = min(heights) if heights else 1.0
    h_max = max(heights) if heights else 1.0
    h_range = h_max - h_min if h_max != h_min else 1.0

    def photo_height_for(product: ProductData) -> float:
        if product.wysokosc_val <= 0:
            return PHOTO_H
        ratio = (product.wysokosc_val - h_min) / h_range
        return PHOTO_H_MIN + ratio * (PHOTO_H_MAX - PHOTO_H_MIN)

    per_page = COLS * ROWS
    total_pages = (len(products) + per_page - 1) // per_page

    for page_idx in range(total_pages):
        if page_idx > 0:
            c.showPage()

        _draw_header(c, lang, font_regular, font_bold, font_header)

        page_products = products[page_idx * per_page: (page_idx + 1) * per_page]

        for i, product in enumerate(page_products):
            col = i % COLS
            row = i // COLS

            cell_x = MARGIN_LEFT + col * CELL_W
            # Komórki od góry w dół (rząd 0 = najwyższy)
            grid_top_y = PAGE_H - MARGIN_TOP - HEADER_HEIGHT
            cell_y = grid_top_y - (row + 1) * CELL_H

            _draw_product_card(
                c, product,
                cell_x, cell_y,
                lang, font_regular, font_bold,
                photo_h=photo_height_for(product),
            )

    c.save()
    return output_path
