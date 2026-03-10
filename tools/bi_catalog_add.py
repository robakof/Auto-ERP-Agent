"""
bi_catalog_add.py — aktualizuje kolumny w catalog.json na podstawie rzeczywistej struktury widoków AIBI.

Użycie:
    python tools/bi_catalog_add.py --view AIBI.Rezerwacje
    python tools/bi_catalog_add.py --all
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import create_erp_sql_client
from tools.lib.output import print_json

CATALOG_PATH = Path(__file__).parent.parent / "solutions" / "bi" / "catalog.json"


def fetch_columns(view_name: str) -> list[str] | None:
    client = create_erp_sql_client()
    result = client.execute(f"SELECT TOP 1 * FROM {view_name}", inject_top=None)
    if not result["ok"]:
        return None
    return result["columns"]


def update_catalog(view_name: str, catalog: dict) -> tuple[bool, str]:
    columns = fetch_columns(view_name)
    if columns is None:
        return False, f"Nie można pobrać kolumn dla {view_name}"

    for view in catalog["views"]:
        if view["name"].upper() == view_name.upper():
            view["columns"] = columns
            return True, f"{view_name}: zaktualizowano {len(columns)} kolumn"

    return False, f"{view_name}: nie znaleziono w catalog.json"


def main():
    parser = argparse.ArgumentParser(description="Aktualizuj kolumny w catalog.json z bazy danych")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--view", help="Nazwa widoku (np. AIBI.Rezerwacje)")
    group.add_argument("--all", action="store_true", help="Aktualizuj wszystkie widoki z katalogu")
    args = parser.parse_args()

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    results = []

    if args.all:
        views = [v["name"] for v in catalog["views"]]
    else:
        views = [args.view]

    for view_name in views:
        ok, message = update_catalog(view_name, catalog)
        results.append({"view": view_name, "ok": ok, "message": message})

    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print_json({"ok": True, "data": {"results": results}})


if __name__ == "__main__":
    main()
