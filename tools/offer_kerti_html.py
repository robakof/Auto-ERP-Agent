"""
offer_kerti_html.py — generator HTML oferty szkła Kerti.

Design: odwzorowanie FINAL28.html (klasy .cp/.pc/.mc/.ph/.legend/.pb/.pf).
Dane: list[KertiGlassData] z offer_kerti_data.py.
"""

import base64
import io
import os
from itertools import groupby
from pathlib import Path
from typing import Optional

from offer_kerti_data import KertiGlassData

ASSETS_DIR = Path(__file__).parent / "kerti_assets"

# Max products per page per layout
PAGE_LIMITS = {"g2": 6, "g3": 9, "g4": 12}

# SVG icons — dokładne kopie z FINAL28
SVG_WYSOKOSC = (
    '<svg class="si" viewBox="0 0 10 10">'
    '<line x1="5" y1="0" x2="5" y2="10" stroke="#BD7E4D" stroke-width="1.6"/>'
    '<line x1="1.5" y1="1" x2="8.5" y2="1" stroke="#BD7E4D" stroke-width="1.3"/>'
    '<line x1="1.5" y1="9" x2="8.5" y2="9" stroke="#BD7E4D" stroke-width="1.3"/>'
    '</svg>'
)
SVG_SR_OTWORU = (
    '<svg class="si" viewBox="0 0 10 10">'
    '<circle cx="5" cy="5" r="4" stroke="#BD7E4D" stroke-width="1.2" fill="none"/>'
    '<line x1="1" y1="5" x2="9" y2="5" stroke="#BD7E4D" stroke-width="0.9"/>'
    '</svg>'
)
SVG_SR_SPODU = (
    '<svg class="si" viewBox="0 0 10 10">'
    '<ellipse cx="5" cy="7.5" rx="3.5" ry="2" stroke="#BD7E4D" stroke-width="1.2" fill="none"/>'
    '</svg>'
)
SVG_PALETA = (
    '<svg class="si" viewBox="0 0 10 10">'
    '<rect x="0.5" y="3" width="9" height="6.5" rx="1" stroke="#BD7E4D" stroke-width="1.2" fill="none"/>'
    '<rect x="2" y="1" width="6" height="3" rx="0.8" stroke="#BD7E4D" stroke-width="1" fill="none"/>'
    '</svg>'
)

LEGEND_SVG_WYSOKOSC = SVG_WYSOKOSC.replace('#BD7E4D', '#8B5E38')
LEGEND_SVG_SR_OTWORU = SVG_SR_OTWORU.replace('#BD7E4D', '#8B5E38')
LEGEND_SVG_SR_SPODU = SVG_SR_SPODU.replace('#BD7E4D', '#8B5E38')
LEGEND_SVG_PALETA = SVG_PALETA.replace('#BD7E4D', '#8B5E38')


def _asset_b64(filename: str) -> str:
    """Zwraca data URI base64 dla pliku z katalogu assets."""
    path = ASSETS_DIR / filename
    with open(path, "rb") as f:
        raw = f.read()
    ext = path.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    b64 = base64.b64encode(raw).decode()
    return f"data:{mime};base64,{b64}"


def _img_to_b64(photo_path: str) -> str:
    """Konwertuje zdjęcie produktu do base64 JPEG (opcjonalnie upscale 2x)."""
    try:
        from PIL import Image
        img = Image.open(photo_path)
        if img.width < 512:
            img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=92, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""


def _fmt_cm(val: Optional[float]) -> str:
    if val is None:
        return "—"
    s = f"{val:.1f}".replace(".", ",")
    return f"{s} cm"


def _fmt_paleta(val: Optional[int]) -> str:
    if val is None:
        return "—"
    return f"{val:,}".replace(",", "\u00a0") + "\u00a0szt."


def _render_card(product: KertiGlassData, max_h: float) -> str:
    """Renderuje kartę produktu (.pc div).

    Gdy produkt nie ma wysokości w ERP — zdjęcie widoczne w pełnym rozmiarze
    (scale=1.0), a w polach wymiarów pokazuje się "—".
    """
    if product.wysokosc_cm and max_h > 0:
        scale = round(product.wysokosc_cm / max_h, 3)
    else:
        scale = 1.0
    transform = f"transform:scale({scale});transform-origin:bottom center;"

    img_src = _img_to_b64(product.zdjecie_path) if product.zdjecie_path else ""
    img_tag = (
        f'<img src="{img_src}" alt="{product.nazwa}" '
        f'style="width:100%;height:100%;object-fit:contain;{transform}">'
        if img_src else ""
    )

    badge = '<div class="nb">Nowo\u015b\u0107</div>' if product.nowosc else ""

    sr_spodu = (
        f'<div class="sr">{SVG_SR_SPODU}<span class="sv">{_fmt_cm(product.sr_spodu_cm)}</span></div>'
        if product.sr_spodu_cm is not None else ""
    )
    paleta = (
        f'<div class="sr">{SVG_PALETA}<span class="sv">{_fmt_paleta(product.ilosc_paleta)}</span></div>'
        if product.ilosc_paleta is not None else ""
    )

    return (
        f'<div class="pc">'
        f'{badge}'
        f'<div class="piw" style="background:#fff;">{img_tag}</div>'
        f'<div class="pn">{product.nazwa}</div>'
        f'<div class="dg"></div>'
        f'<div class="sr">{SVG_WYSOKOSC}<span class="sv">{_fmt_cm(product.wysokosc_cm)}</span></div>'
        f'<div class="sr">{SVG_SR_OTWORU}<span class="sv">{_fmt_cm(product.sr_otworu_cm)}</span></div>'
        f'{sr_spodu}'
        f'{paleta}'
        f'</div>'
    )


def _render_legend() -> str:
    return (
        '<div class="legend">'
        f'<div class="li">{LEGEND_SVG_WYSOKOSC}Wysoko\u015b\u0107</div>'
        f'<div class="li">{LEGEND_SVG_SR_OTWORU}\u015ar. otworu</div>'
        f'<div class="li">{LEGEND_SVG_SR_SPODU}\u015ar. spodu</div>'
        f'<div class="li">{LEGEND_SVG_PALETA}Ilo\u015b\u0107/paleta</div>'
        '</div>'
    )


def _render_section(seria: str, products: list[KertiGlassData], layout: str) -> str:
    """Renderuje sekcję z nagłówkiem serii i gridiem kart."""
    heights = [p.wysokosc_cm for p in products if p.wysokosc_cm]
    max_h = max(heights) if heights else 1.0
    cards = "".join(_render_card(p, max_h) for p in products)
    seria_upper = seria.upper() if seria else "SZKŁO KERTI"
    return (
        f'<div class="sl">{seria_upper}</div>'
        f'<div class="{layout}" style="align-items:start;">{cards}</div>'
    )


def _render_product_page(
    sections_html: str,
    logo_kerti_b64: str,
) -> str:
    """Renderuje stronę produktową (.page.cp) z podaną zawartością sekcji."""
    ph = (
        '<div class="ph">'
        '<div><div class="ph-title">Szk\u0142o Zniczowe</div></div>'
        f'<img src="{logo_kerti_b64}" alt="Kerti" class="ph-logo">'
        '</div>'
    )
    footer_text = "Kerti &middot; SOLAG &middot; Szk\u0142o Zniczowe 2026"
    return (
        '<div class="page cp">'
        f'{ph}'
        f'{_render_legend()}'
        f'<div class="pb">{sections_html}</div>'
        f'<div class="pf"><div class="ft">{footer_text}</div><div class="fl"></div></div>'
        '</div>'
    )


def _render_cover(cover_bg_b64: str) -> str:
    return (
        '<div class="page" style="background:#000;overflow:hidden;position:relative;">'
        f'<img src="{cover_bg_b64}" alt="Ok\u0142adka" '
        f'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;">'
        '</div>'
    )


def _render_contact(header_bg_b64: str, logo_kerti_b64: str, logo_solag_b64: str) -> str:
    """Generuje stronę kontaktową na podstawie szablonu z assets."""
    template_path = ASSETS_DIR / "contact_page.html"
    template = template_path.read_text(encoding="utf-8")
    return template.format(
        header_bg_b64=header_bg_b64,
        logo_kerti_b64=logo_kerti_b64,
        logo_solag_b64=logo_solag_b64,
    )


def _load_css(header_bg_b64: str) -> str:
    css = (ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    return css.replace("{header_bg_url}", header_bg_b64)


def _paginate(products: list[KertiGlassData], layout: str) -> list[list[KertiGlassData]]:
    """Dzieli listę produktów na strony wg limitu PAGE_LIMITS."""
    limit = PAGE_LIMITS.get(layout, 9)
    return [products[i:i + limit] for i in range(0, len(products), limit)]


def generate_html(
    products: list[KertiGlassData],
    layout: str = "g3",
) -> str:
    """
    Generuje kompletny HTML oferty Kerti.

    Args:
        products: lista produktów z load_kerti_products()
        layout: 'g2' | 'g3' | 'g4'

    Returns:
        string HTML gotowy do WeasyPrint
    """
    logo_kerti_b64  = _asset_b64("logo_kerti.png")
    logo_solag_b64  = _asset_b64("logo_solag.png")
    header_bg_b64   = _asset_b64("header_bg.jpg")
    cover_bg_b64    = _asset_b64("cover_bg.jpg")

    css = _load_css(header_bg_b64)

    google_font = (
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
    )

    head = f"<head><meta charset='UTF-8'>{google_font}<style>{css}</style></head>"

    # Cover
    pages_html = _render_cover(cover_bg_b64)

    # Product pages — grupuj wg serii, paginuj
    grouped = groupby(products, key=lambda p: p.seria)
    for seria, group_iter in grouped:
        group = list(group_iter)
        pages = _paginate(group, layout)
        for page_products in pages:
            section = _render_section(seria, page_products, layout)
            pages_html += _render_product_page(section, logo_kerti_b64)

    # Contact page
    pages_html += _render_contact(header_bg_b64, logo_kerti_b64, logo_solag_b64)

    return f"<!DOCTYPE html><html lang='pl'>{head}<body>{pages_html}</body></html>"
