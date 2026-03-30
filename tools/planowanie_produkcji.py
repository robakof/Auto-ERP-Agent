"""
planowanie_produkcji.py — Eksport zamówień niepotwierdzonych CZNI do Excel.

CLI:
    python tools/planowanie_produkcji.py --year 2026
    python tools/planowanie_produkcji.py --year 2026 --output output/planowanie/wynik.xlsx
"""

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient
from tools.lib.excel_writer import ExcelWriter

_PROJECT_ROOT = Path(__file__).parent.parent
_SQL_PATH = _PROJECT_ROOT / "solutions/erp_specialist/planowanie_produkcji_zamowienia_niepotwierdzone.sql"
_OUTPUT_DIR = _PROJECT_ROOT / "output/planowanie"

COLUMNS = [
    "ID_Zamowienia", "Nr_Zamowienia", "Data_Wystawienia", "Data_Realizacji",
    "Kontrahent_Kod", "Kontrahent_Nazwa",
    "Nr_Pozycji", "Towar_Kod", "Towar_Nazwa", "Ilosc", "Jednostka", "Opis",
]


def _fetch_all() -> list[dict]:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])
    cols = result["columns"]
    return [dict(zip(cols, row)) for row in result["rows"]]


def filter_rows(rows: list[dict], year: int) -> list[dict]:
    """Filtruje po: Towar_Kod CZNI*, Opis startswith 'Zamówienie', rok Data_Realizacji."""
    out = []
    for r in rows:
        if not (r.get("Towar_Kod") or "").startswith("CZNI"):
            continue
        opis = r.get("Opis") or ""
        if not opis.startswith("Zamówienie"):
            continue
        dr = r.get("Data_Realizacji")
        if dr is None or _year_of(dr) != year:
            continue
        out.append(r)
    return out


def _year_of(d) -> int:
    """Pobiera rok z datetime.date lub datetime.datetime."""
    if hasattr(d, "year"):
        return d.year
    raise TypeError(f"Nieoczekiwany typ daty: {type(d)}")


def _to_rows(rows: list[dict]) -> list[list]:
    return [[r.get(c) for c in COLUMNS] for r in rows]


def _export(rows: list[dict], output_path: Path) -> None:
    data_rows = _to_rows(rows)
    writer = ExcelWriter()
    writer.add_sheet("Zamówienia CZNI", COLUMNS, data_rows)
    try:
        writer.save(output_path)
    except PermissionError:
        raise RuntimeError(f"Nie można zapisać: {output_path}. Zamknij plik w Excelu.")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Eksport zamówień niepotwierdzonych CZNI do Excel."
    )
    parser.add_argument("--year", type=int, required=True,
                        help="Rok Data_Realizacji (np. 2026)")
    parser.add_argument("--output", default=None,
                        help="Ścieżka pliku xlsx (domyślnie: output/planowanie/)")
    args = parser.parse_args()

    today = datetime.date.today().isoformat()
    default_name = f"planowanie_CZNI_{args.year}_{today}.xlsx"
    output_path = Path(args.output) if args.output else _OUTPUT_DIR / default_name

    print(f"Pobieranie danych z ERP...")
    rows = _fetch_all()
    print(f"  Pobrano {len(rows)} pozycji łącznie.")

    filtered = filter_rows(rows, args.year)
    print(f"  Po filtrach (CZNI, Zamówienie*, rok {args.year}): {len(filtered)} pozycji.")

    if not filtered:
        print("Brak danych do eksportu.")
        sys.exit(0)

    _export(filtered, output_path)
    print(f"OK: {output_path.resolve()}")


if __name__ == "__main__":
    main()
