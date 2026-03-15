"""
sql_query.py — Narzędzie agenta: wykonywanie zapytań SELECT na SQL Server ERP.

CLI:
    python tools/sql_query.py "SELECT TOP 5 ZaN_GIDNumer FROM CDN.ZamNag"
    python tools/sql_query.py --file SCIEZKA.sql [--export SCIEZKA.xlsx]
                              [--export-limit N] [--count-only] [--quiet]

Flagi:
    --count-only      Pomiń kolumnę rows w odpowiedzi (tylko row_count + columns)
    --quiet           Wypisz OK {n} lub ERROR: komunikat zamiast JSON
    --export-limit N  Ogranicz eksport do N wierszy (dla dużych tabel, np. TraNag 224k)

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_writer import ExcelWriter
from tools.lib.output import print_json
from tools.lib.sql_client import SqlClient


def run_query(sql: str, inject_top: int = 100) -> dict:
    result = SqlClient().execute(sql, inject_top=inject_top)
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
    try:
        writer.save(export_path)
    except PermissionError:
        result["ok"] = False
        result["data"] = None
        result["error"] = {
            "type": "EXPORT_PERMISSION_ERROR",
            "message": f"Nie można zapisać pliku: {export_path}. Zamknij go w Excelu i spróbuj ponownie.",
        }
        return
    result["data"]["export_path"] = str(export_path.resolve())


def main():
    parser = argparse.ArgumentParser(description="Wykonaj zapytanie SELECT na SQL Server ERP.")
    parser.add_argument("sql", nargs="?", default=None, help="Zapytanie SELECT (inline)")
    parser.add_argument("--file", "-f", default=None, help="Ścieżka do pliku .sql z zapytaniem")
    parser.add_argument("--export", "-e", default=None, help="Eksportuj wynik do pliku .xlsx")
    parser.add_argument("--export-limit", type=int, default=None, dest="export_limit",
                        help="Ogranicz eksport do N wierszy (np. 100000 dla dużych tabel)")
    parser.add_argument("--count-only", action="store_true", help="Pomiń rows w odpowiedzi")
    parser.add_argument("--quiet", action="store_true", help="Wypisz OK {n} lub ERROR: komunikat")
    args = parser.parse_args()

    if args.file:
        sql_path = Path(args.file)
        if not sql_path.exists():
            print_json({
                "ok": False, "data": None,
                "error": {"type": "FILE_NOT_FOUND", "message": f"Plik SQL nie istnieje: {args.file}"},
                "meta": {"duration_ms": 0, "truncated": False},
            })
            return
        sql = sql_path.read_text(encoding="utf-8")
    elif args.sql:
        sql = args.sql
    else:
        print_json({
            "ok": False, "data": None,
            "error": {"type": "MISSING_ARGUMENT", "message": "Podaj zapytanie SQL jako argument lub przez --file"},
            "meta": {"duration_ms": 0, "truncated": False},
        })
        return

    if args.export:
        inject_top = args.export_limit  # None = bez limitu; N = TOP N
    else:
        inject_top = 100
    result = run_query(sql, inject_top=inject_top)

    if result["ok"] and args.export:
        _export_to_excel(result, Path(args.export))

    if args.quiet:
        if result["ok"]:
            print(f"OK {result['data']['row_count']}")
        else:
            print(f"ERROR: {result['error']['message']}")
        return

    if args.count_only and result["ok"]:
        result["data"].pop("rows", None)

    print_json(result)


if __name__ == "__main__":
    main()
