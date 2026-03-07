"""
excel_export.py — Narzędzie agenta: eksport wyników SQL do pliku Excel (.xlsx).

CLI:
    python tools/excel_export.py "SELECT TOP 100 ..." [--output SCIEZKA.xlsx] [--view-name "Nazwa"]

Jeśli --output nie podano, plik zapisywany jest w exports/ z nazwą opartą na znaczniku czasu.

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_writer import ExcelWriter
from tools.lib.sql_client import SqlClient

EXPORTS_DIR = Path(__file__).parent.parent / "exports"


def export_to_excel(
    sql: str,
    output_path: Path | None = None,
    view_name: str | None = None,
) -> dict:
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = view_name.replace(" ", "_").replace("/", "_") if view_name else "query"
        output_path = EXPORTS_DIR / f"{prefix}_{timestamp}.xlsx"

    output_path = Path(output_path)

    result = SqlClient().execute(sql, inject_top=1000)
    if not result["ok"]:
        return {
            "ok": False,
            "data": None,
            "error": result["error"],
            "meta": {"duration_ms": result["duration_ms"], "row_count": 0},
        }

    try:
        writer = ExcelWriter()
        writer.add_sheet("Dane", result["columns"], result["rows"])
        writer.save(output_path)
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "data": None,
            "error": {"type": "EXPORT_ERROR", "message": str(e)},
            "meta": {"duration_ms": result["duration_ms"], "row_count": 0},
        }

    return {
        "ok": True,
        "data": {
            "path": str(output_path.resolve()),
            "row_count": result["row_count"],
            "columns": result["columns"],
        },
        "error": None,
        "meta": {"duration_ms": result["duration_ms"], "row_count": result["row_count"]},
    }


def main():
    parser = argparse.ArgumentParser(description="Eksportuj wyniki SQL do pliku Excel.")
    parser.add_argument("sql", help='Zapytanie SELECT')
    parser.add_argument("--output", "-o", default=None, help="Ścieżka do pliku .xlsx")
    parser.add_argument("--view-name", default=None, help="Nazwa widoku w nazwie pliku")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    result = export_to_excel(args.sql, output_path, args.view_name)
    print(json.dumps(result, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
