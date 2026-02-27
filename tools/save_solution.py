"""
save_solution.py — Narzędzie agenta: zapis nowego rozwiązania SQL do solutions/.

CLI:
    python tools/save_solution.py \\
        --window "Okno towary" \\
        --view "Towary według EAN" \\
        --type filters \\
        --name "brak jpg" \\
        --sql "Twr_GIDNumer NOT IN (...)"

    Długi SQL: przekaż przez --sql-file PATH zamiast --sql.

Output: JSON na stdout zgodny z kontraktem z ARCHITECTURE.md.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SOLUTIONS_ROOT = "solutions in ERP windows"


def _read_sql_content(args) -> tuple[str | None, dict | None]:
    """Czyta treść SQL z argumentów CLI. Zwraca (sql, None) lub (None, error_dict)."""
    if args.sql:
        return args.sql, None
    if args.sql_file:
        try:
            return Path(args.sql_file).read_text(encoding="utf-8"), None
        except Exception as e:
            return None, {
                "ok": False, "data": None,
                "error": {"type": "READ_ERROR", "message": str(e)},
                "meta": {"duration_ms": 0, "truncated": False},
            }
    return None, {
        "ok": False, "data": None,
        "error": {"type": "MISSING_ARGUMENT", "message": "Wymagane --sql lub --sql-file"},
        "meta": {"duration_ms": 0, "truncated": False},
    }


def save_solution(
    window: str,
    view: str,
    sol_type: str,
    name: str,
    sql: str,
    force: bool = False,
    solutions_path: str | None = None,
) -> dict:
    """Zapisuje plik .sql do właściwego miejsca w hierarchii solutions/."""
    start = time.monotonic()

    base = Path(solutions_path or os.getenv("SOLUTIONS_PATH", "./solutions"))
    target = base / SOLUTIONS_ROOT / window / view / sol_type / f"{name}.sql"

    if target.exists() and not force:
        return {
            "ok": False,
            "data": None,
            "error": {
                "type": "FILE_EXISTS",
                "message": f"Plik już istnieje: {target}. Użyj --force aby nadpisać.",
            },
            "meta": {"duration_ms": 0, "truncated": False},
        }

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(sql, encoding="utf-8")
    except Exception as e:
        duration_ms = round((time.monotonic() - start) * 1000)
        return {
            "ok": False,
            "data": None,
            "error": {"type": "WRITE_ERROR", "message": str(e)},
            "meta": {"duration_ms": duration_ms, "truncated": False},
        }

    duration_ms = round((time.monotonic() - start) * 1000)
    rel_path = str(target.relative_to(base)).replace("\\", "/")
    return {
        "ok": True,
        "data": {"path": rel_path},
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Zapisuje rozwiązanie SQL do solutions/.")
    parser.add_argument("--window", required=True, help="Nazwa okna ERP")
    parser.add_argument("--view", required=True, help="Nazwa widoku")
    parser.add_argument("--type", required=True, choices=["columns", "filters"],
                        dest="sol_type", help="Typ rozwiązania")
    parser.add_argument("--name", required=True, help="Nazwa pliku (bez .sql)")
    parser.add_argument("--sql", default=None, help="Treść SQL (inline)")
    parser.add_argument("--sql-file", default=None, help="Ścieżka do pliku z treścią SQL")
    parser.add_argument("--force", action="store_true", help="Nadpisz istniejący plik")
    args = parser.parse_args()

    sql, error = _read_sql_content(args)
    if error:
        print(json.dumps(error))
        return

    result = save_solution(
        window=args.window,
        view=args.view,
        sol_type=args.sol_type,
        name=args.name,
        sql=sql,
        force=args.force,
    )
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
