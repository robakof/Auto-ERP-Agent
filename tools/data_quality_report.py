"""
data_quality_report.py — Generuje raport Excel z obszaru roboczego SQLite Analityka Danych.

CLI:
    python tools/data_quality_report.py \
        --db "solutions/analyst/KntKarty/KntKarty_workdb.db" \
        --output "solutions/analyst/KntKarty/KntKarty_report.xlsx"

Raport zawiera dwie zakładki:
    Obserwacje — lista znalezisk (jedna obserwacja = jeden wiersz)
    Rekordy    — konkretne wiersze do poprawki z identyfikatorami

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_writer import ExcelWriter
from tools.lib.output import print_json


def _load_findings(conn: sqlite3.Connection) -> tuple[list[str], list[list]]:
    cursor = conn.execute(
        "SELECT column, observation, rows_affected, created_at FROM findings ORDER BY id"
    )
    columns = ["Kolumna", "Obserwacja", "Liczba_rekordow", "Data_analizy"]
    rows = [list(row) for row in cursor.fetchall()]
    return columns, rows


def _load_records(conn: sqlite3.Connection) -> tuple[list[str], list[list]]:
    cursor = conn.execute("SELECT column, data, created_at FROM records ORDER BY id")
    raw = cursor.fetchall()

    if not raw:
        return ["Kolumna", "Data_analizy"], []

    # Zbierz wszystkie klucze JSON zachowując kolejność pierwszego wystąpienia
    all_keys: list[str] = []
    seen: set[str] = set()
    for _, data_json, _ in raw:
        for key in json.loads(data_json).keys():
            if key not in seen:
                all_keys.append(key)
                seen.add(key)

    columns = all_keys + ["Kolumna", "Data_analizy"]
    rows = []
    for col, data_json, created_at in raw:
        record = json.loads(data_json)
        row = [record.get(k) for k in all_keys] + [col, created_at]
        rows.append(row)

    return columns, rows


def generate_report(db_path: Path, output_path: Path) -> dict:
    """Generuje raport Excel z tabel findings i records w pliku SQLite."""
    if not db_path.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik bazy nie istnieje: {db_path}"},
            "meta": {},
        }

    conn = sqlite3.connect(db_path)
    try:
        findings_cols, findings_rows = _load_findings(conn)
        records_cols, records_rows = _load_records(conn)
    finally:
        conn.close()

    writer = ExcelWriter()
    writer.add_sheet("Obserwacje", findings_cols, findings_rows)
    writer.add_sheet("Rekordy", records_cols, records_rows)
    writer.save(output_path)

    return {
        "ok": True,
        "data": {
            "output_path": str(output_path.resolve()),
            "findings_count": len(findings_rows),
            "records_count": len(records_rows),
        },
        "error": None,
        "meta": {},
    }


def main():
    parser = argparse.ArgumentParser(description="Generuj raport Excel z obszaru roboczego Analityka Danych.")
    parser.add_argument("--db", required=True, help="Ścieżka do pliku .db (SQLite)")
    parser.add_argument("--output", required=True, help="Ścieżka do pliku wynikowego .xlsx")
    args = parser.parse_args()

    result = generate_report(Path(args.db), Path(args.output))
    print_json(result)


if __name__ == "__main__":
    main()
