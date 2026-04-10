"""
offer_kerti_pdf.py — konwersja HTML → PDF przez Playwright (Chromium).
"""

import tempfile
from pathlib import Path


def html_to_pdf(html_string: str, output_path: str) -> str:
    """
    Konwertuje HTML string do PDF A4 bez marginesów.

    Args:
        html_string: kompletny HTML z generate_html()
        output_path: ścieżka wynikowego PDF

    Returns:
        output_path
    """
    from playwright.sync_api import sync_playwright

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html_string)
        tmp_path = tmp.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(f"file:///{tmp_path.replace(chr(92), '/')}", wait_until="networkidle")
            page.wait_for_timeout(1500)
            page.pdf(
                path=output_path,
                width="210mm",
                height="297mm",
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                print_background=True,
                prefer_css_page_size=True,
            )
            browser.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return output_path
