"""
data_quality_init.py — Inicjalizuje lokalny obszar roboczy SQLite dla Analityka Danych.

CLI:
    python tools/data_quality_init.py --source "BI.KntKarty" --output "solutions/analyst/KntKarty/KntKarty_workdb.db"
    python tools/data_quality_init.py --source "CDN.ZamNag" --output "..." --force

Flagi:
    --force   Nadpisz istniejący plik .db

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json
from tools.lib.sql_client import SqlClient

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS findings (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    column    TEXT,
    observation TEXT,
    rows_affected INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    column     TEXT,
    data       TEXT,
    created_at TEXT
);
"""


def _to_sqlite_value(v):
    """Konwertuje wartość Python do typu akceptowanego przez SQLite."""
    if v is None or isinstance(v, (int, float, str)):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def init_workdb(source: str, output_path: Path, force: bool = False) -> dict:
    """Eksportuje widok/tabelę do SQLite i inicjalizuje obszar roboczy analityka."""
    start = time.monotonic()

    if output_path.exists() and not force:
        return {
            "ok": False,
            "data": None,
            "error": {
                "type": "FILE_EXISTS",
                "message": f"Plik już istnieje: {output_path}. Użyj --force aby nadpisać.",
            },
            "meta": {"duration_ms": 0},
        }

    sql = f"SELECT * FROM {source}"
    result = SqlClient().execute(sql, inject_top=None)

    if not result["ok"]:
        return {
            "ok": False,
            "data": None,
            "error": result["error"],
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    columns = result["columns"]
    col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
    placeholders = ", ".join("?" * len(columns))
    rows = [[_to_sqlite_value(v) for v in row] for row in result["rows"]]

    conn = sqlite3.connect(output_path)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.execute("DROP TABLE IF EXISTS dane")
        conn.execute(f"CREATE TABLE dane ({col_defs})")
        conn.executemany(f"INSERT INTO dane VALUES ({placeholders})", rows)
        conn.commit()
    finally:
        conn.close()

    return {
        "ok": True,
        "data": {
            "source": source,
            "db_path": str(output_path.resolve()),
            "row_count": result["row_count"],
            "columns": columns,
        },
        "error": None,
        "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
    }


def main():
    parser = argparse.ArgumentParser(description="Inicjalizuj obszar roboczy SQLite dla Analityka Danych.")
    parser.add_argument("--source", required=True, help="Widok BI lub tabela CDN (np. BI.KntKarty)")
    parser.add_argument("--output", required=True, help="Ścieżka do pliku .db (SQLite)")
    parser.add_argument("--force", action="store_true", help="Nadpisz istniejący plik")
    args = parser.parse_args()

    result = init_workdb(args.source, Path(args.output), args.force)
    print_json(result)


if __name__ == "__main__":
    main()
