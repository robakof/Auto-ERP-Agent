"""
search_windows.py — Narzędzie agenta: wyszukiwanie okien ERP po nazwie lub aliasie.

CLI:
    python tools/search_windows.py "towary ean" [--type columns|filters]

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

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.output import print_json

WINDOWS_FILE = "erp_windows.json"


def _matches_phrase(phrase: str, window: dict) -> bool:
    """Sprawdza czy fraza pasuje do nazwy lub aliasów okna (case-insensitive)."""
    phrase_lower = phrase.lower()
    if phrase_lower in window.get("name", "").lower():
        return True
    return any(phrase_lower in alias.lower() for alias in window.get("aliases", []))


def search_windows(
    phrase: str,
    type_filter: str | None = None,
    solutions_path: str | None = None,
) -> dict:
    """Przeszukuje erp_windows.json i zwraca pasujące okna per kontrakt JSON."""
    start = time.monotonic()

    base = Path(solutions_path or os.getenv("SOLUTIONS_PATH", "./solutions"))
    windows_path = base / WINDOWS_FILE

    if not windows_path.exists():
        # Plik nie istnieje jeszcze (wypełniany w KM2) — zwracamy puste wyniki zamiast błędu
        return {
            "ok": True,
            "data": {"results": []},
            "error": None,
            "meta": {"duration_ms": 0, "truncated": False},
        }

    try:
        windows = json.loads(windows_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "PARSE_ERROR", "message": str(e)},
            "meta": {"duration_ms": 0, "truncated": False},
        }

    results = []
    for window in windows:
        if phrase and not _matches_phrase(phrase, window):
            continue
        if type_filter and type_filter not in window.get("config_types", []):
            continue
        results.append({
            "id": window.get("id"),
            "name": window.get("name"),
            "aliases": window.get("aliases", []),
            "primary_table": window.get("primary_table"),
            "config_types": window.get("config_types", []),
        })

    duration_ms = round((time.monotonic() - start) * 1000)
    return {
        "ok": True,
        "data": {"results": results},
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Wyszukuje okna ERP po nazwie lub aliasie.")
    parser.add_argument("phrase", nargs="?", default="", help="Fraza do wyszukania")
    parser.add_argument("--type", choices=["columns", "filters", "reports"], default=None)
    args = parser.parse_args()

    result = search_windows(phrase=args.phrase, type_filter=args.type)
    print_json(result)


if __name__ == "__main__":
    main()
