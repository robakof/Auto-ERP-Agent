"""KSeF Shadow DB init — tworzy lub sprawdza schema v1.

Uzycie:
    py tools/ksef_init_db.py                     # utworz/aktualizuj (default: data/ksef.db)
    py tools/ksef_init_db.py --db data/ksef.db
    py tools/ksef_init_db.py --check             # tylko weryfikacja

Exit: 0 = OK, 1 = niezgodnosc schemy, 2 = blad I/O.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ksef.adapters.repo import ShipmentRepository

_DEFAULT_DB = Path("data/ksef.db")
_EXPECTED_TABLES = {"ksef_wysylka", "ksef_transition", "schema_version"}
_EXPECTED_VERSION = 1


def main() -> int:
    parser = argparse.ArgumentParser(description="KSeF Shadow DB init/check")
    parser.add_argument("--db", type=Path, default=_DEFAULT_DB)
    parser.add_argument("--check", action="store_true", help="tylko weryfikacja, bez zmian")
    args = parser.parse_args()

    if args.check:
        return _check(args.db)

    try:
        ShipmentRepository(args.db).init_schema()
    except OSError as exc:
        print(f"I/O error: {exc}", file=sys.stderr)
        return 2
    print(f"OK: {args.db} — schema v{_EXPECTED_VERSION} gotowa")
    return _check(args.db)


def _check(db_path: Path) -> int:
    if not db_path.exists():
        print(f"FAIL: {db_path} nie istnieje", file=sys.stderr)
        return 1
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            tables = {r[0] for r in rows}
            missing = _EXPECTED_TABLES - tables
            if missing:
                print(f"FAIL: brakujace tabele {sorted(missing)}", file=sys.stderr)
                return 1
            version = conn.execute(
                "SELECT MAX(version) FROM schema_version"
            ).fetchone()[0]
    except sqlite3.DatabaseError as exc:
        print(f"FAIL: blad DB: {exc}", file=sys.stderr)
        return 1
    if version != _EXPECTED_VERSION:
        print(f"FAIL: schema v{version}, oczekiwano v{_EXPECTED_VERSION}", file=sys.stderr)
        return 1
    print(f"OK: {db_path} — tabele {sorted(_EXPECTED_TABLES)}, version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
