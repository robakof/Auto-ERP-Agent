"""
excel_read_rows.py — Narzędzie agenta: odczyt wierszy z pliku Excel.

CLI:
    python tools/excel_read_rows.py --file PATH.xlsx [--sheet NAZWA] [--columns col1,col2]

Typowe użycie: odczyt planu widoku BI po edycji przez usera (kolumna Komentarz_Usera).
Bez --columns zwraca wszystkie kolumny.

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_reader import ExcelReader
from tools.lib.output import print_json


def read_rows(
    file_path: Path,
    sheet_name: str | None = None,
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
            return reader.read_rows(sheet_name, columns)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "data": None, "error": {"type": "OPEN_ERROR", "message": str(e)}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Odczytaj wiersze z pliku Excel.")
    parser.add_argument("--file", required=True, help="Ścieżka do pliku .xlsx")
    parser.add_argument("--sheet", default=None, help="Nazwa arkusza (domyślnie: pierwszy)")
    parser.add_argument("--columns", default=None, help="Kolumny oddzielone przecinkami (domyślnie: wszystkie)")
    args = parser.parse_args()

    cols = [c.strip() for c in args.columns.split(",")] if args.columns else None
    result = read_rows(Path(args.file), args.sheet, cols)
    print_json(result)


if __name__ == "__main__":
    main()
