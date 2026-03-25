"""
update_window_catalog.py — Narzędzie agenta: zarządzanie katalogiem okien ERP.

CLI:
    python tools/update_window_catalog.py \\
        --id okno_zamowien \\
        --name "Okno zamówień sprzedaży" \\
        --primary-table CDN.ZamNag \\
        --add-alias "lista ZO" \\
        --add-alias "zamówienia" \\
        --config-types columns filters

Tworzy nowy wpis lub aktualizuje istniejący (upsert po --id).
Aliasy dopisywane bez duplikatów (case-insensitive).

Output: JSON na stdout zgodny z kontraktem z ARCHITECTURE.md.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

from tools.lib.output import print_json

load_dotenv()

WINDOWS_FILE = "erp_windows.json"


def _load_windows(path: Path) -> list[dict]:
    """Wczytuje erp_windows.json. Zwraca pustą listę gdy plik nie istnieje."""
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_windows(windows: list[dict], path: Path) -> None:
    """Zapisuje erp_windows.json (indent=2, polskie znaki bez escape)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(windows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _find_window(windows: list[dict], window_id: str) -> int | None:
    """Zwraca indeks wpisu o danym id lub None."""
    for i, w in enumerate(windows):
        if w.get("id") == window_id:
            return i
    return None


def _merge_aliases(existing: list[str], new_aliases: list[str]) -> list[str]:
    """Dopisuje aliasy bez duplikatów (case-insensitive)."""
    lower_existing = {a.lower() for a in existing}
    result = list(existing)
    for alias in new_aliases:
        if alias.lower() not in lower_existing:
            result.append(alias)
            lower_existing.add(alias.lower())
    return result


def update_window(
    window_id: str,
    name: str | None = None,
    primary_table: str | None = None,
    add_aliases: list[str] | None = None,
    config_types: list[str] | None = None,
    solutions_path: str | None = None,
) -> dict:
    """Tworzy lub aktualizuje wpis okna ERP w erp_windows.json (upsert)."""
    start = time.monotonic()

    base = Path(solutions_path or os.getenv("SOLUTIONS_PATH", "./solutions"))
    windows_path = base / WINDOWS_FILE

    try:
        windows = _load_windows(windows_path)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "PARSE_ERROR", "message": str(e)},
            "meta": {"duration_ms": 0, "truncated": False},
        }

    idx = _find_window(windows, window_id)
    created = idx is None

    if created:
        entry: dict = {"id": window_id}
        windows.append(entry)
        idx = len(windows) - 1
    else:
        entry = windows[idx]

    if name is not None:
        entry["name"] = name
    if primary_table is not None:
        entry["primary_table"] = primary_table
    if add_aliases:
        entry["aliases"] = _merge_aliases(entry.get("aliases", []), add_aliases)
    if config_types is not None:
        entry["config_types"] = config_types

    try:
        _save_windows(windows, windows_path)
    except Exception as e:
        duration_ms = round((time.monotonic() - start) * 1000)
        return {
            "ok": False,
            "data": None,
            "error": {"type": "WRITE_ERROR", "message": str(e)},
            "meta": {"duration_ms": duration_ms, "truncated": False},
        }

    duration_ms = round((time.monotonic() - start) * 1000)
    return {
        "ok": True,
        "data": {"window": entry, "created": created},
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Zarządza katalogiem okien ERP.")
    parser.add_argument("--id", required=True, dest="window_id", help="Unikalny identyfikator okna")
    parser.add_argument("--name", default=None, help="Nazwa wyświetlana w ERP")
    parser.add_argument("--primary-table", default=None, help="Główna tabela SQL (CDN.XXX)")
    parser.add_argument("--add-alias", action="append", default=[], dest="add_aliases",
                        help="Alias do dopisania (można powtórzyć)")
    parser.add_argument("--config-types", nargs="+", default=None,
                        choices=["columns", "filters", "reports"],
                        help="Typy konfiguracji okna")
    args = parser.parse_args()

    result = update_window(
        window_id=args.window_id,
        name=args.name,
        primary_table=args.primary_table,
        add_aliases=args.add_aliases,
        config_types=args.config_types,
    )
    print_json(result)


if __name__ == "__main__":
    main()
