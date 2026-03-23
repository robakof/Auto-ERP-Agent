"""
jas_export.py — Wysyła WZ z ERP do JAS API jako zlecenia spedycyjne.

CLI:
    python tools/jas_export.py --all                    # wszystkie WZ z widoku
    python tools/jas_export.py --wz-id 12345            # jedna WZ po ID
    python tools/jas_export.py --numer WZ/2026/00123    # jedna WZ po numerze
    python tools/jas_export.py --all --dry-run          # tylko pokaż payloady
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json
from tools.lib.sql_client import SqlClient
from tools.jas_client import JasClient, JasApiError, JasAuthError
from tools.jas_mapper import rows_to_shipment

_PROJECT_ROOT = Path(__file__).parent.parent
SQL_PATH = _PROJECT_ROOT / "solutions/jas/wz_jas_pending.sql"


def _load_rows(wz_id: int | None, numer: str | None) -> list[dict]:
    """Pobiera wiersze z AILO.wz_jas_export z opcjonalnym filtrem."""
    sql_template = SQL_PATH.read_text(encoding="utf-8")

    if wz_id is not None:
        where = f"WHERE wz_id = {int(wz_id)}"
    elif numer:
        safe = numer.replace("'", "''")
        where = f"WHERE numer_wz = '{safe}'"
    else:
        where = ""

    sql = sql_template.replace("{where_clause}", where)
    result = SqlClient().execute(sql, inject_top=None)
    if not result["ok"]:
        raise RuntimeError(result["error"]["message"])

    cols = result["columns"]
    return [dict(zip(cols, row)) for row in result["rows"]]


def _group_by_wz(rows: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["wz_id"]].append(row)
    return dict(grouped)


def run(wz_id: int | None, numer: str | None, dry_run: bool) -> dict:
    rows = _load_rows(wz_id, numer)
    if not rows:
        return {"ok": True, "sent": 0, "skipped": 0, "errors": []}

    grouped = _group_by_wz(rows)
    client = JasClient() if not dry_run else None

    sent, skipped, errors = 0, 0, []

    for wid, wz_rows in grouped.items():
        payload = rows_to_shipment(wz_rows)
        numer_wz = wz_rows[0].get("numer_wz", str(wid))

        if payload is None:
            skipped += 1
            continue

        if dry_run:
            print(f"\n--- DRY RUN: {numer_wz} ---")
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
            sent += 1
            continue

        try:
            response = client.create_shipment(payload)
            print(f"OK: {numer_wz} → id={response.get('id', '?')}")
            sent += 1
        except (JasApiError, JasAuthError) as e:
            errors.append({"numer_wz": numer_wz, "error": str(e)})

    return {"ok": not errors, "sent": sent, "skipped": skipped, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description="Wyślij WZ do JAS API.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all",    action="store_true", help="Wszystkie WZ z widoku")
    group.add_argument("--wz-id",  type=int,            help="WZ po ID")
    group.add_argument("--numer",  type=str,            help="WZ po numerze")
    parser.add_argument("--dry-run", action="store_true",
                        help="Pokaż payload bez wysyłania do JAS")
    args = parser.parse_args()

    if not args.all and args.wz_id is None and args.numer is None:
        parser.error("Podaj --all, --wz-id lub --numer.")

    result = run(
        wz_id=args.wz_id,
        numer=args.numer,
        dry_run=args.dry_run,
    )
    print_json({"ok": result["ok"], "data": result, "error": None, "meta": {}})


if __name__ == "__main__":
    main()
