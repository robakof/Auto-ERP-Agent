"""
export_ui.py — Eksportuje minimalne pliki UI do katalogu dist/ui/.

Uruchomienie:
    py tools/export_ui.py

Output: katalog dist/ui/ gotowy do skopiowania na inny komputer.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DIST = ROOT / "dist" / "ui"

# Pliki i katalogi do skopiowania (względem ROOT)
ITEMS = [
    # Aplikacja
    "tools/app.py",
    "tools/pages/oferta_katalogowa_3x3.py",
    "tools/pages/etykiety_wysylkowe.py",
    "tools/offer_data.py",
    "tools/offer_pdf_3x3.py",
    "tools/etykiety_export.py",
    "tools/lib/__init__.py",
    "tools/lib/sql_client.py",
    "tools/lib/output.py",
    # SQL
    "solutions/jas/etykiety_grupy.sql",
    "solutions/jas/etykiety_10_oferty.sql",
    "solutions/jas/etykiety_excel.sql",
    # Zasoby
    "documents/Wzory plików/OFerta katalogowa.xlsx",
    "documents/Wzory plików/logo CEiM krzywe.pdf",
    "documents/Wzory plików/logo_kerti.jpg",
    # Zależności
    "requirements.txt",
]


def export():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    missing = []
    for item in ITEMS:
        src = ROOT / item
        dst = DIST / item
        if not src.exists():
            missing.append(item)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  OK: {item}")

    # Pusty katalog output
    (DIST / "output").mkdir(exist_ok=True)
    print(f"  OK: output/ (pusty)")

    if missing:
        print("\nBrakujące pliki (pominięte):")
        for m in missing:
            print(f"  BRAK: {m}")

    print(f"\nGotowe: {DIST}")
    print("Skopiuj cały katalog 'ui' na docelowy komputer.")
    print("Uruchomienie: py -m streamlit run tools/app.py")


if __name__ == "__main__":
    export()
