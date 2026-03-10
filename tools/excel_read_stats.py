"""
excel_read_stats.py — Narzędzie agenta: statystyki kolumn z pliku Excel.

CLI:
    python tools/excel_read_stats.py --file PATH.xlsx [--sheet NAZWA]
                                     [--max-unique N] [--columns col1,col2]

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_reader import ExcelReader
from tools.lib.output import print_json


def read_stats(
    file_path: Path,
    sheet_name: str | None = None,
    max_unique: int = 20,
    columns: list[str] | None = None,
) -> dict:
    if not Path(file_path).exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik nie istnieje: {file_path}"},
        }
    try:
        with ExcelReader(file_path) as reader:
            return reader.read_stats(sheet_name, max_unique, columns)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "data": None, "error": {"type": "OPEN_ERROR", "message": str(e)}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Odczytaj statystyki kolumn z pliku Excel.")
    parser.add_argument("--file", required=True, help="Ścieżka do pliku .xlsx")
    parser.add_argument("--sheet", default=None, help="Nazwa arkusza (domyślnie: pierwszy)")
    parser.add_argument("--max-unique", type=int, default=20, help="Próg unikalnych wartości")
    parser.add_argument("--columns", default=None, help="Kolumny oddzielone przecinkami")
    args = parser.parse_args()

    cols = [c.strip() for c in args.columns.split(",")] if args.columns else None
    result = read_stats(Path(args.file), args.sheet, args.max_unique, cols)
    print_json(result)


if __name__ == "__main__":
    main()
