"""
data_quality_save.py — Zapisuje obserwację analityka do obszaru roboczego SQLite.

CLI:
    python tools/data_quality_save.py \
        --db "solutions/analyst/KntKarty/KntKarty_workdb.db" \
        --column "Telefon" \
        --observation "47 rekordów zawiera znak '@' — prawdopodobne adresy email." \
        --rows-affected 47

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json


def save_finding(db_path: Path, column: str, observation: str, rows_affected: int) -> dict:
    """Dopisuje obserwację do tabeli findings w pliku SQLite obszaru roboczego."""
    if not db_path.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik bazy nie istnieje: {db_path}"},
            "meta": {},
        }

    created_at = date.today().isoformat()
    try:
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(
                "INSERT INTO findings (column, observation, rows_affected, created_at) VALUES (?, ?, ?, ?)",
                (column, observation, rows_affected, created_at),
            )
            finding_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        return {
            "ok": True,
            "data": {"id": finding_id, "column": column, "rows_affected": rows_affected},
            "error": None,
            "meta": {},
        }
    except sqlite3.Error as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "DB_ERROR", "message": str(e)},
            "meta": {},
        }


def main():
    parser = argparse.ArgumentParser(description="Zapisz obserwację analityka do obszaru roboczego SQLite.")
    parser.add_argument("--db", required=True, help="Ścieżka do pliku .db (SQLite)")
    parser.add_argument("--column", required=True, help="Nazwa kolumny której dotyczy obserwacja")
    parser.add_argument("--observation", required=True, help="Opis obserwacji w naturalnym języku")
    parser.add_argument("--rows-affected", required=True, type=int, help="Liczba rekordów których dotyczy problem")
    args = parser.parse_args()

    result = save_finding(Path(args.db), args.column, args.observation, args.rows_affected)
    print_json(result)


if __name__ == "__main__":
    main()
