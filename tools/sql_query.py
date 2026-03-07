"""
sql_query.py — Narzędzie agenta: wykonywanie zapytań SELECT na SQL Server ERP.

CLI:
    python tools/sql_query.py "SELECT TOP 5 ZaN_GIDNumer FROM CDN.ZamNag"

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

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


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "ok": False,
            "data": None,
            "error": {"type": "MISSING_ARGUMENT", "message": "Podaj zapytanie SQL jako argument"},
            "meta": {"duration_ms": 0, "truncated": False},
        }))
        return
    result = run_query(sys.argv[1])
    print(json.dumps(result, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
