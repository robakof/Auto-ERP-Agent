"""
search_solutions.py — Narzędzie agenta: przeszukiwanie bazy rozwiązań SQL.

CLI:
    python tools/search_solutions.py "kontrahent" [--window "Okno towary"] [--type columns|filters]

Output: JSON na stdout zgodny z kontraktem z ARCHITECTURE.md.
"""

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.output import print_json

SOLUTIONS_ROOT = "solutions in ERP windows"


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _parse_path(sql_path: Path, solutions_base: Path) -> dict | None:
    """
    Wyciąga window/view/type/name z ścieżki pliku .sql.

    Oczekiwana struktura:
        {solutions_base}/solutions in ERP windows/{Okno}/{Widok}/{type}/{name}.sql
    """
    try:
        rel = sql_path.relative_to(solutions_base)
        parts = rel.parts  # ("solutions in ERP windows", "Okno", "Widok", "type", "name.sql")
        if len(parts) < 5:
            return None
        if parts[0] != SOLUTIONS_ROOT:
            return None
        sol_type = parts[3]
        if sol_type not in ("columns", "filters"):
            return None
        return {
            "window": parts[1],
            "view": parts[2],
            "type": sol_type,
            "name": sql_path.stem,
        }
    except ValueError:
        return None


def _matches(phrase: str, *, window: str, view: str, name: str, sql: str) -> bool:
    """Case-insensitive search w nazwie pliku, treści SQL, oknie i widoku."""
    phrase_lower = phrase.lower()
    return any(
        phrase_lower in text.lower()
        for text in (name, sql, window, view)
    )


def _get_filtr_sql(view_dir: Path, cache: dict) -> str | None:
    """Odczytuje filtr.sql z katalogu widoku. Wyniki cachowane w przekazanym słowniku."""
    if view_dir not in cache:
        filtr_path = view_dir / "filtr.sql"
        cache[view_dir] = _read_file(filtr_path) if filtr_path.exists() else None
    return cache[view_dir]


def search_solutions(
    phrase: str,
    window_filter: str | None = None,
    type_filter: str | None = None,
    limit: int = 20,
    solutions_path: str | None = None,
) -> dict:
    """Przeszukuje solutions/ i zwraca wyniki per kontrakt JSON."""
    start = time.monotonic()

    base = Path(solutions_path or os.getenv("SOLUTIONS_PATH", "./solutions"))
    erp_windows_dir = base / SOLUTIONS_ROOT

    if not erp_windows_dir.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "NOT_FOUND", "message": f"Katalog nie istnieje: {erp_windows_dir}"},
            "meta": {"duration_ms": 0, "truncated": False},
        }

    filtr_cache: dict[Path, str | None] = {}
    results = []

    for sql_path in sorted(erp_windows_dir.rglob("*.sql")):
        if sql_path.name == "filtr.sql":
            continue

        meta = _parse_path(sql_path, base)
        if meta is None:
            continue

        if type_filter and meta["type"] != type_filter:
            continue

        if window_filter and window_filter.lower() not in meta["window"].lower():
            continue

        sql_content = _read_file(sql_path)

        if phrase and not _matches(
            phrase,
            window=meta["window"],
            view=meta["view"],
            name=meta["name"],
            sql=sql_content,
        ):
            continue

        view_dir = sql_path.parent.parent  # {Widok}/
        filtr_sql = _get_filtr_sql(view_dir, filtr_cache)

        results.append({
            "path": str(sql_path.relative_to(base)).replace("\\", "/"),
            "window": meta["window"],
            "view": meta["view"],
            "type": meta["type"],
            "name": meta["name"],
            "sql": sql_content,
            "filtr_sql": filtr_sql,
        })

        if len(results) >= limit:
            break

    duration_ms = round((time.monotonic() - start) * 1000)
    return {
        "ok": True,
        "data": {"results": results},
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": len(results) == limit},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Przeszukuje bazę rozwiązań SQL.")
    parser.add_argument("phrase", nargs="?", default="", help="Fraza do wyszukania")
    parser.add_argument("--window", default=None, help="Filtr okna ERP")
    parser.add_argument("--type", choices=["columns", "filters"], default=None)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    result = search_solutions(
        phrase=args.phrase,
        window_filter=args.window,
        type_filter=args.type,
        limit=args.limit,
    )
    print_json(result)


if __name__ == "__main__":
    main()
