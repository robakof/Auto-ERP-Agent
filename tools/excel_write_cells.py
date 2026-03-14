"""
excel_write_cells.py — Narzędzie agenta: zapis wartości do komórek istniejącego pliku Excel.

CLI:
    python tools/excel_write_cells.py --file PATH.xlsx --sheet ARKUSZ
        --key-column COL_KLUCZ --target-column COL_CEL --data-file dane.json

data-file: JSON z mapowaniem {wartość_klucza: wartość_do_zapisu}
    Przykład: {"Twr_GIDNumer": "klucz techniczny", "Twr_Nazwa": "ok"}

Plik jest modyfikowany in-place (nadpisywany).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_editor import ExcelEditor
from tools.lib.output import print_json


def main():
    parser = argparse.ArgumentParser(description="Zapisz wartości do komórek istniejącego xlsx.")
    parser.add_argument("--file", required=True, help="Ścieżka do pliku xlsx")
    parser.add_argument("--sheet", required=True, help="Nazwa arkusza")
    parser.add_argument("--key-column", dest="key_column", required=True,
                        help="Kolumna identyfikująca wiersz")
    parser.add_argument("--target-column", dest="target_column", required=True,
                        help="Kolumna do zapisu")
    parser.add_argument("--data-file", dest="data_file", required=True,
                        help="Plik JSON: {klucz: wartość}")
    args = parser.parse_args()

    data_path = Path(args.data_file)
    if not data_path.exists():
        print_json({"ok": False, "data": None,
                    "error": {"type": "FILE_NOT_FOUND", "message": f"Plik danych nie istnieje: {data_path}"}})
        sys.exit(1)

    data = json.loads(data_path.read_text(encoding="utf-8"))

    try:
        editor = ExcelEditor(args.file)
    except FileNotFoundError as e:
        print_json({"ok": False, "data": None,
                    "error": {"type": "FILE_NOT_FOUND", "message": str(e)}})
        sys.exit(1)

    result = editor.write_cells(
        sheet=args.sheet,
        key_column=args.key_column,
        target_column=args.target_column,
        data=data,
    )

    if result["ok"]:
        editor.save(args.file)

    editor.close()
    print_json(result)


if __name__ == "__main__":
    main()
