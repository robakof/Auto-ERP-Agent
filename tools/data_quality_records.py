"""
data_quality_records.py — Zapisuje konkretne brudne rekordy do obszaru roboczego SQLite.

CLI:
    python tools/data_quality_records.py \
        --db "solutions/analyst/KntKarty/KntKarty_workdb.db" \
        --column "Telefon" \
        --sql "SELECT Kod_Kontrahenta, Nazwa_Kontrahenta, Telefon FROM dane WHERE Telefon LIKE '%@%'"

Agent dobiera kolumny identyfikujące rekord samodzielnie (kod, nazwa, nr dokumentu — zależnie od kontekstu).
Każdy wiersz wyniku zapisywany jako JSON do tabeli records.

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json


def save_records(db_path: Path, column: str, sql: str) -> dict:
    """Wykonuje query na tabeli dane i zapisuje wyniki do tabeli records."""
    if not db_path.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik bazy nie istnieje: {db_path}"},
            "meta": {},
        }

    normalized = sql.upper().lstrip()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        return {
            "ok": False,
            "data": None,
            "error": {"type": "VALIDATION_ERROR", "message": "Dozwolone tylko zapytania SELECT"},
            "meta": {},
        }

    created_at = date.today().isoformat()
    try:
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            for row in rows:
                record_dict = dict(zip(columns, row))
                conn.execute(
                    "INSERT INTO records (column, data, created_at) VALUES (?, ?, ?)",
                    (column, json.dumps(record_dict, ensure_ascii=False, default=str), created_at),
                )
            conn.commit()
        finally:
            conn.close()

        return {
            "ok": True,
            "data": {"column": column, "records_saved": len(rows)},
            "error": None,
            "meta": {},
        }
    except sqlite3.Error as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "SQL_ERROR", "message": str(e)},
            "meta": {},
        }


def main():
    parser = argparse.ArgumentParser(description="Zapisz brudne rekordy do obszaru roboczego SQLite.")
    parser.add_argument("--db", required=True, help="Ścieżka do pliku .db (SQLite)")
    parser.add_argument("--column", required=True, help="Nazwa kolumny której dotyczy problem")
    parser.add_argument("--sql", required=True, help="SELECT zwracający rekordy do poprawki z identyfikatorami")
    args = parser.parse_args()

    result = save_records(Path(args.db), args.column, args.sql)
    print_json(result)


if __name__ == "__main__":
    main()
