"""
planowanie_produkcji.py — Planowanie produkcji CZNI: zamówienia + gap analysis.

CLI:
    python tools/planowanie_produkcji.py --year 2025
    python tools/planowanie_produkcji.py --year 2025 --output output/planowanie/wynik.xlsx
"""

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_demand import fetch_demand
from tools.lib.pp_supply import fetch_supply
from tools.lib.excel_writer import ExcelWriter

_PROJECT_ROOT = Path(__file__).parent.parent
_OUTPUT_DIR = _PROJECT_ROOT / "output/planowanie"

# Faza 2: kolumny arkusza 1 (zamówienia)
_COLS_ORDERS = [
    "Nr_Zamowienia", "Data_Realizacji", "Kontrahent_Kod", "Kontrahent_Nazwa",
    "Towar_Kod", "Towar_Nazwa", "Ilosc", "Jednostka", "Opis",
]

# Re-eksport dla testów (filter_rows używane w test suite)
from tools.lib.pp_demand import _year_of


def filter_rows(rows: list[dict], year: int) -> list[dict]:
    """Filtruje po roku Data_Realizacji. Filtry CZNI/Opis już w SQL."""
    return [
        r for r in rows
        if r.get("Data_Realizacji") is not None
        and _year_of(r["Data_Realizacji"]) == year
    ]


def _export_orders(rows: list[dict], output_path: Path) -> None:
    data_rows = [[r.get(c) for c in _COLS_ORDERS] for r in rows]
    writer = ExcelWriter()
    writer.add_sheet("Zamówienia CZNI", _COLS_ORDERS, data_rows)
    try:
        writer.save(output_path)
    except PermissionError:
        raise RuntimeError(f"Nie można zapisać: {output_path}. Zamknij plik w Excelu.")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Planowanie produkcji CZNI — zamówienia + gap analysis."
    )
    parser.add_argument("--year", type=int, required=True,
                        help="Rok Data_Realizacji (np. 2025)")
    parser.add_argument("--output", default=None,
                        help="Ścieżka pliku xlsx (domyślnie: output/planowanie/)")
    args = parser.parse_args()

    today = datetime.date.today().isoformat()
    default_name = f"planowanie_CZNI_{args.year}_{today}.xlsx"
    output_path = Path(args.output) if args.output else _OUTPUT_DIR / default_name

    print("Pobieranie zamówień z ERP...")
    demand = fetch_demand(args.year)
    print(f"  Zamówienia CZNI rok {args.year}: {len(demand)} pozycji.")

    print("Pobieranie stanów OTOR_SUR...")
    supply = fetch_supply()
    print(f"  Surowce OTOR_SUR: {len(supply)} pozycji.")

    if not demand:
        print("Brak zamówień do eksportu.")
        sys.exit(0)

    _export_orders(demand, output_path)
    print(f"OK: {output_path.resolve()}")


if __name__ == "__main__":
    main()
