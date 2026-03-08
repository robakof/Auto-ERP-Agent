"""
sql_query.py — Narzędzie agenta: wykonywanie zapytań SELECT na SQL Server ERP.

CLI:
    python tools/sql_query.py "SELECT TOP 5 ZaN_GIDNumer FROM CDN.ZamNag"
    python tools/sql_query.py --file SCIEZKA.sql [--export SCIEZKA.xlsx]

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_writer import ExcelWriter
from tools.lib.sql_client import SqlClient


def run_query(sql: str) -> dict:
    result = SqlClient().execute(sql, inject_top=100)
    if not result["ok"]:
        return {
            "ok": False,
            "data": None,
            "error": result["error"],
            "meta": {"duration_ms": result["duration_ms"], "truncated": False},
        }
    return {
        "ok": True,
        "data": {
            "row_count": result["row_count"],
            "columns": result["columns"],
            "rows": result["rows"],
        },
        "error": None,
        "meta": {"duration_ms": result["duration_ms"], "truncated": result["truncated"]},
    }


def _export_to_excel(result: dict, export_path: Path) -> None:
    writer = ExcelWriter()
    writer.add_sheet("Dane", result["data"]["columns"], result["data"]["rows"])
    writer.save(export_path)
    result["data"]["export_path"] = str(export_path.resolve())


def main():
    parser = argparse.ArgumentParser(description="Wykonaj zapytanie SELECT na SQL Server ERP.")
    parser.add_argument("sql", nargs="?", default=None, help="Zapytanie SELECT (inline)")
    parser.add_argument("--file", "-f", default=None, help="Ścieżka do pliku .sql z zapytaniem")
    parser.add_argument("--export", "-e", default=None, help="Eksportuj wynik do pliku .xlsx")
    args = parser.parse_args()

    if args.file:
        sql_path = Path(args.file)
        if not sql_path.exists():
            print(json.dumps({
                "ok": False, "data": None,
                "error": {"type": "FILE_NOT_FOUND", "message": f"Plik SQL nie istnieje: {args.file}"},
                "meta": {"duration_ms": 0, "truncated": False},
            }, ensure_ascii=False))
            return
        sql = sql_path.read_text(encoding="utf-8")
    elif args.sql:
        sql = args.sql
    else:
        print(json.dumps({
            "ok": False, "data": None,
            "error": {"type": "MISSING_ARGUMENT", "message": "Podaj zapytanie SQL jako argument lub przez --file"},
            "meta": {"duration_ms": 0, "truncated": False},
        }))
        return

    result = run_query(sql)

    if result["ok"] and args.export:
        _export_to_excel(result, Path(args.export))

    print(json.dumps(result, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
