"""
planowanie_produkcji.py — Planowanie produkcji CZNI: zamówienia + BOM + gap analysis + harmonogram.

CLI:
    py tools/planowanie_produkcji.py --year 2025 --bom-file PATH
    py tools/planowanie_produkcji.py --year 2025 --bom-file PATH --mode gap
    py tools/planowanie_produkcji.py --year 2025 --bom-file PATH --capacity-file PATH --mode schedule
    py tools/planowanie_produkcji.py --year 2025 --bom-file PATH --capacity-file PATH --priority-file PATH --start-date 2026-05-04 --mode all
"""

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.pp_demand import fetch_demand, _year_of
from tools.lib.pp_supply import fetch_supply
from tools.lib.pp_bom import load_bom, load_efficiency
from tools.lib.pp_capacity import load_capacity
from tools.lib.pp_gap import compute_gap
from tools.lib.pp_export import export_plan
from tools.lib.pp_schedule import build_schedule
from tools.lib.pp_produced import fetch_produced
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
    parser.add_argument("--capacity-file", default=None,
                        help="Ścieżka do pliku moce produkcyjne.xlsx")
    parser.add_argument("--priority-file", default=None,
                        help="Excel z kolumną Priorytet (Run 2, opcjonalny)")
    parser.add_argument("--start-date", default=None,
                        help="Data startowa harmonogramu YYYY-MM-DD (domyślnie: dziś)")
    parser.add_argument("--output", default=None,
                        help="Ścieżka pliku xlsx wyjściowego")
    parser.add_argument("--mode",
                        choices=["full", "orders-only", "gap", "schedule", "all"],
                        default="full",
                        help="full/gap=4 ark., orders-only=1 ark., schedule/all=7 ark.")
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
        parser.error("--bom-file wymagany dla trybów gap/full/schedule/all")

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

    supply_rows = [
        {"Towar_Kod": k, "Towar_Nazwa": "", "Jednostka": "", "Stan": v}
        for k, v in supply.items()
    ]

    # Tryb schedule / all — buduj harmonogram
    schedule = None
    priorities: set[str] = set()
    start_date = datetime.date.today()

    if args.mode in ("schedule", "all"):
        if not args.capacity_file:
            parser.error("--capacity-file wymagany dla trybu schedule/all")

        if args.start_date:
            start_date = datetime.date.fromisoformat(args.start_date)

        print(f"Wczytywanie mocy produkcyjnych z {args.capacity_file}...")
        capacity = load_capacity(Path(args.capacity_file))
        print(f"  Dni z mocami: {len(capacity)}")

        print("Wczytywanie wydajności z BOM...")
        efficiency = load_efficiency(Path(args.bom_file))
        print(f"  Produkty z wydajnością: {len(efficiency)}")

        if args.priority_file:
            priorities = _load_priorities(Path(args.priority_file))
            print(f"  Zamówienia z priorytetem: {len(priorities)}")

        print("Pobieranie przyjętej produkcji PW Otorowo...")
        try:
            produced = fetch_produced(args.year)
            print(f"  Wyprodukowane kody CZNI: {len(produced)}")
        except RuntimeError as e:
            print(f"  [WARN] Brak danych PW: {e} — harmonogram bez odjęcia produkcji.")
            produced = {}

        print("Budowanie harmonogramu (EDF + priorytet)...")
        schedule = build_schedule(demand, efficiency, produced, capacity, priorities, start_date)
        print(f"  Sloty harmonogramu: {len(schedule)}")

    export_plan(demand, supply, gaps, supply_rows, output_path,
                schedule=schedule, priorities=priorities, start_date=start_date)
    print(f"OK: {output_path.resolve()}")


def _load_priorities(priority_file: Path) -> set[str]:
    """Wczytuje Nr_Zamowienia z Priorytet=1 z pliku xlsx (Arkusz 5 z poprzedniego runu)."""
    import warnings
    import openpyxl
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(priority_file, read_only=True, data_only=True)
    ws = wb.active
    priorities: set[str] = set()
    header = None
    for row in ws.iter_rows(values_only=True):
        if header is None:
            header = [str(c).strip() if c else "" for c in row]
            continue
        try:
            nr_idx = header.index("Nr_Zamowienia")
            prio_idx = header.index("Priorytet")
        except ValueError:
            break
        nr = row[nr_idx]
        prio = row[prio_idx]
        if nr and str(prio).strip() == "1":
            priorities.add(str(nr))
    wb.close()
    return priorities


if __name__ == "__main__":
    main()
