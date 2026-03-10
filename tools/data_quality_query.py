"""
data_quality_query.py — Odpytuje lokalny obszar roboczy SQLite Analityka Danych.

CLI:
    python tools/data_quality_query.py --db "path/to/workdb.db" --sql "SELECT col FROM dane WHERE ..."
    python tools/data_quality_query.py --db "..." --sql "..." [--count-only] [--quiet]

Flagi:
    --count-only  Pomiń kolumnę rows w odpowiedzi (tylko row_count + columns)
    --quiet       Wypisz OK {n} lub ERROR: komunikat zamiast JSON

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json


def run_query(db_path: Path, sql: str) -> dict:
    """Wykonuje zapytanie SELECT na lokalnym SQLite obszaru roboczego."""
    start = time.monotonic()

    if not db_path.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik bazy nie istnieje: {db_path}"},
            "meta": {"duration_ms": 0},
        }

    normalized = sql.upper().lstrip()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return {
            "ok": False,
            "data": None,
            "error": {"type": "VALIDATION_ERROR", "message": "Dozwolone tylko zapytania SELECT"},
            "meta": {"duration_ms": 0},
        }

    try:
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [list(row) for row in cursor.fetchall()]
        finally:
            conn.close()

        duration_ms = round((time.monotonic() - start) * 1000)
        return {
            "ok": True,
            "data": {
                "row_count": len(rows),
                "columns": columns,
                "rows": rows,
            },
            "error": None,
            "meta": {"duration_ms": duration_ms},
        }
    except sqlite3.Error as e:
        duration_ms = round((time.monotonic() - start) * 1000)
        return {
            "ok": False,
            "data": None,
            "error": {"type": "SQL_ERROR", "message": str(e)},
            "meta": {"duration_ms": duration_ms},
        }


def main():
    parser = argparse.ArgumentParser(description="Odpytuj lokalny SQLite obszaru roboczego Analityka Danych.")
    parser.add_argument("--db", required=True, help="Ścieżka do pliku .db (SQLite)")
    parser.add_argument("--sql", required=True, help="Zapytanie SELECT")
    parser.add_argument("--count-only", action="store_true", help="Pomiń rows w odpowiedzi")
    parser.add_argument("--quiet", action="store_true", help="Wypisz OK {n} lub ERROR: komunikat")
    args = parser.parse_args()

    result = run_query(Path(args.db), args.sql)

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
