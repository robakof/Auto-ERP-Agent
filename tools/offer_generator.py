"""
offer_generator.py — CLI generatora ofert katalogowych PDF.

Użycie:
    python tools/offer_generator.py \\
        --input "documents/Wzory plików/OFerta katalogowa.xlsx" \\
        --output output/oferta_wklady.pdf \\
        --lang pl \\
        --model wklady
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.offer_data import load_products
from tools.offer_pdf import generate_pdf


def main():
    parser = argparse.ArgumentParser(description="Generator PDF oferty katalogowej")
    parser.add_argument(
        "--input", required=True,
        help="Ścieżka do pliku Excel z listą produktów (OFerta katalogowa.xlsx)"
    )
    parser.add_argument(
        "--output", required=True,
        help="Ścieżka wyjściowa pliku PDF"
    )
    parser.add_argument(
        "--lang", default="pl", choices=["pl", "en", "ro"],
        help="Język oferty: pl (domyślnie), en, ro"
    )
    parser.add_argument(
        "--model", default="wklady", choices=["wklady"],
        help="Model karty produktu (domyślnie: wklady)"
    )
    args = parser.parse_args()

    print(f"Ładowanie danych z: {args.input}")
    products = load_products(args.input, lang=args.lang)
    print(f"Załadowano {len(products)} produktów.")

    print(f"Generowanie PDF ({args.lang.upper()})...")
    output = generate_pdf(products, args.output, lang=args.lang, model=args.model)
    print(f"PDF zapisany: {output}")


if __name__ == "__main__":
    main()
