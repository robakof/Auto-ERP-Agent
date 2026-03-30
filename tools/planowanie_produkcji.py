"""
planowanie_produkcji.py — Planowanie produkcji CZNI: zamówienia + BOM + gap analysis.

CLI:
    python tools/planowanie_produkcji.py --year 2025 --bom-file "D:/pliki/Wycena PQ.xlsm"
    python tools/planowanie_produkcji.py --year 2025 --bom-file PATH --output wynik.xlsx
    python tools/planowanie_produkcji.py --year 2025 --mode orders-only
"""

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_demand import fetch_demand, _year_of
from tools.lib.pp_supply import fetch_supply
from tools.lib.pp_bom import load_bom
from tools.lib.pp_gap import compute_gap
from tools.lib.pp_export import export_plan
from tools.lib.excel_writer import ExcelWriter

_PROJECT_ROOT = Path(__file__).parent.parent
_OUTPUT_DIR = _PROJECT_ROOT / "output/planowanie"

_COLS_ORDERS = [
    "Nr_Zamowienia", "Data_Realizacji", "Kontrahent_Kod", "Kontrahent_Nazwa",
    "Towar_Kod", "Towar_Nazwa", "Ilosc", "Jednostka", "Opis",
]


# Re-eksport dla testów
def filter_rows(rows: list[dict], year: int) -> list[dict]:
    """Filtruje po roku Data_Realizacji. Filtry CZNI/Opis już w SQL."""
    return [
        r for r in rows
        if r.get("Data_Realizacji") is not None
        and _year_of(r["Data_Realizacji"]) == year
    ]


def _export_orders_only(rows: list[dict], output_path: Path) -> None:
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
        description="Planowanie produkcji CZNI — zamówienia + BOM + gap analysis."
    )
    parser.add_argument("--year", type=int, required=True,
                        help="Rok Data_Realizacji (np. 2025)")
    parser.add_argument("--bom-file", default=None,
                        help="Ścieżka do pliku Wycena PQ.xlsm")
    parser.add_argument("--output", default=None,
                        help="Ścieżka pliku xlsx wyjściowego")
    parser.add_argument("--mode", choices=["full", "orders-only"], default="full",
                        help="full=4 arkusze z gap analysis, orders-only=1 arkusz")
    args = parser.parse_args()

    today = datetime.date.today().isoformat()
    default_name = f"planowanie_CZNI_{args.year}_{today}.xlsx"
    output_path = Path(args.output) if args.output else _OUTPUT_DIR / default_name

    print("Pobieranie zamówień z ERP...")
    demand = fetch_demand(args.year)
    print(f"  Zamówienia CZNI rok {args.year}: {len(demand)} pozycji.")

    if not demand:
        print("Brak zamówień do eksportu.")
        sys.exit(0)

    if args.mode == "orders-only":
        _export_orders_only(demand, output_path)
        print(f"OK (orders-only): {output_path.resolve()}")
        return

    if not args.bom_file:
        parser.error("--bom-file wymagany dla trybu full (podaj ścieżkę do Wycena PQ.xlsm)")

    print(f"Wczytywanie BOM z {args.bom_file}...")
    bom = load_bom(Path(args.bom_file))
    print(f"  Produkty w BOM: {len(bom)}")

    print("Pobieranie stanów OTOR_SUR...")
    supply = fetch_supply()
    print(f"  Surowce OTOR_SUR: {len(supply)} pozycji.")

    print("Obliczanie gap analysis...")
    gaps, warns = compute_gap(demand, bom, supply)
    braki = sum(1 for g in gaps if g.brak > 0)
    print(f"  Surowce z brakiem: {braki}/{len(gaps)}")

    # supply_rows dla arkusza 3
    supply_rows = [
        {"Towar_Kod": k, "Towar_Nazwa": "", "Jednostka": "", "Stan": v}
        for k, v in supply.items()
    ]

    export_plan(demand, supply, gaps, supply_rows, output_path)
    print(f"OK: {output_path.resolve()}")


if __name__ == "__main__":
    main()
