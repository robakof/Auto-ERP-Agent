"""
offer_generator_3x3.py — CLI generatora ofert katalogowych PDF (wariant 3×3, 9 produktów/stronę).

Użycie:
    python tools/offer_generator_3x3.py \\
        --input "documents/Wzory plików/OFerta katalogowa.xlsx" \\
        --output output/oferta_wklady_3x3.pdf \\
        --lang pl
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.offer_data import load_products
from tools.offer_pdf_3x3 import generate_pdf


def main():
    parser = argparse.ArgumentParser(description="Generator PDF oferty katalogowej (3×3)")
    parser.add_argument("--input",  required=True, help="Plik Excel z listą produktów")
    parser.add_argument("--output", required=True, help="Ścieżka wyjściowa PDF")
    parser.add_argument("--lang",   default="pl", choices=["pl", "en", "ro"])
    parser.add_argument("--model",  default="wklady", choices=["wklady"])
    args = parser.parse_args()

    print(f"Ładowanie danych z: {args.input}")
    products = load_products(args.input, lang=args.lang)
    print(f"Załadowano {len(products)} produktów.")

    print(f"Generowanie PDF 3×3 ({args.lang.upper()})...")
    output = generate_pdf(products, args.output, lang=args.lang, model=args.model)
    print(f"PDF zapisany: {output}")


if __name__ == "__main__":
    main()
