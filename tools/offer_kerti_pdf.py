"""
offer_kerti_pdf.py — konwersja HTML → PDF przez Playwright (Chromium).

Playwright jest odpalany w osobnym procesie Pythona, bo Streamlit + tornado
ustawiają SelectorEventLoop w głównym wątku, co łamie subprocess transport
Playwrighta (NotImplementedError na Windows). Subprocess izoluje event loop.
"""

import subprocess
import sys
import tempfile
from pathlib import Path


def _render(html_path: str, output_path: str) -> None:
    """Renderuje PDF z HTML file (odpalane w osobnym procesie)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(f"file:///{html_path.replace(chr(92), '/')}", wait_until="networkidle")
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


def html_to_pdf(html_string: str, output_path: str) -> str:
    """
    Konwertuje HTML string do PDF A4 bez marginesów.

    Uruchamia renderowanie w osobnym procesie Pythona (izolacja event loopu —
    fix dla NotImplementedError w kontekście Streamlit/tornado na Windows).

    Args:
        html_string: kompletny HTML z generate_html()
        output_path: ścieżka wynikowego PDF

    Returns:
        output_path
    """
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp.write(html_string)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, __file__, "--html", tmp_path, "--output", output_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Playwright subprocess failed (rc={result.returncode}):\n"
                f"STDERR: {result.stderr}\nSTDOUT: {result.stdout}"
            )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render HTML file to PDF via Playwright.")
    parser.add_argument("--html", required=True, help="Input HTML file path")
    parser.add_argument("--output", required=True, help="Output PDF path")
    args = parser.parse_args()
    _render(args.html, args.output)
