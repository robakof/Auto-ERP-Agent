"""
search_bi.py — Narzędzie agenta: wyszukiwanie widoków AIBI po frazie.

CLI:
    python tools/search_bi.py "zamówienia kontrahenta"
    python tools/search_bi.py "NIP"
    python tools/search_bi.py ""   # zwraca wszystkie widoki

Output: JSON na stdout.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.output import print_json

DEFAULT_CATALOG = os.path.join(
    os.path.dirname(__file__), "..", "solutions", "bi", "catalog.json"
)

SEARCH_FIELDS = ["name", "description", "example_questions", "columns", "notes"]


def _load_catalog(catalog_path: str) -> tuple[dict | None, dict | None]:
    path = Path(catalog_path)
    if not path.exists():
        return None, {"type": "CATALOG_NOT_FOUND", "message": f"Brak pliku: {catalog_path}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data, None
    except json.JSONDecodeError as e:
        return None, {"type": "CATALOG_INVALID", "message": str(e)}


def _matches(view: dict, query: str) -> bool:
    query_lower = query.lower()
    for field in SEARCH_FIELDS:
        value = view.get(field, "")
        if isinstance(value, list):
            text = " ".join(value)
        else:
            text = str(value)
        if query_lower in text.lower():
            return True
    return False


def search_bi(
    query: str,
    catalog: dict | None = None,
    catalog_path: str | None = None,
) -> dict:
    """Przeszukuje katalog widoków AIBI po frazie.

    Args:
        query: Fraza do wyszukania. Pusty string zwraca wszystkie widoki.
        catalog: Słownik katalogu (do testów). Jeśli podany, catalog_path ignorowany.
        catalog_path: Ścieżka do catalog.json. Domyślnie solutions/bi/catalog.json.

    Returns:
        Dict z kluczami: ok, data, error, meta.
    """
    start = time.monotonic()

    if catalog is None:
        path = catalog_path or DEFAULT_CATALOG
        catalog, error = _load_catalog(path)
        if error:
            return {
                "ok": False, "data": None, "error": error,
                "meta": {"duration_ms": 0, "truncated": False},
            }

    views = catalog.get("views", [])

    if query == "":
        results = views
    else:
        results = [v for v in views if _matches(v, query)]

    duration_ms = round((time.monotonic() - start) * 1000)
    return {
        "ok": True,
        "data": {"results": results, "count": len(results)},
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Wyszukuje widoki AIBI po frazie.")
    parser.add_argument("query", nargs="?", default="", help="Fraza (puste = wszystkie)")
    parser.add_argument("--catalog", default=None, help="Ścieżka do catalog.json")
    args = parser.parse_args()

    result = search_bi(query=args.query, catalog_path=args.catalog)
    print_json(result)


if __name__ == "__main__":
    main()
