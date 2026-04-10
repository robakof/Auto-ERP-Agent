"""
offer_kerti_pdf.py — konwersja HTML → PDF przez WeasyPrint.
"""

from pathlib import Path


def html_to_pdf(html_string: str, output_path: str) -> str:
    """
    Konwertuje HTML string do PDF.

    Args:
        html_string: kompletny HTML z generate_html()
        output_path: ścieżka wynikowego PDF

    Returns:
        output_path
    """
    from weasyprint import HTML, CSS

    HTML(string=html_string).write_pdf(
        output_path,
        stylesheets=[CSS(string="@page { size: A4; margin: 0; }")],
    )
    return output_path
