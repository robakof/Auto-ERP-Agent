"""
bi_plan_generate.py — Narzędzie agenta: generowanie planu Excel z pliku SQL metadanych.

CLI:
    python tools/bi_plan_generate.py --src SCIEZKA_plan_src.sql [--output SCIEZKA.xlsx]

Format pliku src: SELECT z stałymi wartościami + UNION ALL (bez połączenia z DB).
Wykonywany lokalnie w SQLite in-memory — obsługuje polskie znaki i myślniki.

Domyślna ścieżka output: *_plan_src.sql → *_plan.xlsx w tym samym katalogu.

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_writer import ExcelWriter
from tools.lib.output import print_json


def _default_output(src: Path) -> Path:
    """Zwraca domyślną ścieżkę output obok pliku src."""
    if src.name.endswith("_plan_src.sql"):
        return src.parent / (src.name[: -len("_plan_src.sql")] + "_plan.xlsx")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return src.parent / f"{src.stem}_{timestamp}.xlsx"


def generate_plan(src: Path, output_path: Path | None = None) -> dict:
    """Generuje plan Excel z pliku SQL metadanych (SQLite in-memory)."""
    start = time.monotonic()

    if not src.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik nie istnieje: {src}"},
            "meta": {"duration_ms": 0},
        }

    sql = src.read_text(encoding="utf-8")

    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "SQL_ERROR", "message": str(e)},
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
        }

    if output_path is None:
        output_path = _default_output(src)

    try:
        writer = ExcelWriter()
        writer.add_sheet("Plan", columns, rows)
        writer.save(output_path)
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "EXPORT_ERROR", "message": str(e)},
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
        }

    return {
        "ok": True,
        "data": {
            "path": str(output_path.resolve()),
            "row_count": len(rows),
            "columns": columns,
        },
        "error": None,
        "meta": {"duration_ms": round((time.monotonic() - start) * 1000)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generuj plan Excel z pliku SQL metadanych.")
    parser.add_argument("--src", required=True, help="Ścieżka do pliku *_plan_src.sql")
    parser.add_argument("--output", "-o", default=None, help="Ścieżka do pliku .xlsx (opcjonalnie)")
    args = parser.parse_args()

    result = generate_plan(
        src=Path(args.src),
        output_path=Path(args.output) if args.output else None,
    )
    print_json(result)


if __name__ == "__main__":
    main()
