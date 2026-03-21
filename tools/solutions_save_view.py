"""
solutions_save_view.py — Narzędzie agenta: zapisz draft SQL jako widok BI w solutions/.

CLI:
    python tools/solutions_save_view.py --draft SCIEZKA.sql [--view-name NAZWA] [--schema AIBI]

Tworzy solutions/bi/views/{NazwaWidoku}.sql z nagłówkiem USE + CREATE OR ALTER VIEW.
Gdy --view-name pominięty, nazwa pochodzi z nazwy pliku (strip _draft + .sql).

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json

BASE_DIR = Path(__file__).parent.parent
VIEWS_DIR = BASE_DIR / "solutions" / "bi" / "views"


def _view_name_from_path(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_draft"):
        stem = stem[: -len("_draft")]
    return stem


def save_view(
    draft_path: Path,
    view_name: str | None = None,
    schema: str = "AIBI",
) -> dict:
    draft_path = Path(draft_path)
    if not draft_path.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik draftu nie istnieje: {draft_path}"},
        }

    name = view_name or _view_name_from_path(draft_path)
    draft_sql = re.sub(r'\bTOP\s+\d+\s*', '', draft_path.read_text(encoding="utf-8"), flags=re.IGNORECASE)

    VIEWS_DIR.mkdir(parents=True, exist_ok=True)
    view_file = VIEWS_DIR / f"{name}.sql"
    view_file.write_text(
        f"USE [ERPXL_CEIM];\nGO\n\nCREATE OR ALTER VIEW {schema}.{name} AS\n\n{draft_sql}",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "data": {
            "path": str(view_file.resolve()),
            "view_name": name,
            "schema": schema,
        },
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Zapisz draft SQL jako widok BI w solutions/bi/views/.")
    parser.add_argument("--draft", required=True, help="Ścieżka do pliku draftu .sql")
    parser.add_argument("--view-name", default=None, help="Nazwa widoku (domyślnie: z nazwy pliku)")
    parser.add_argument("--schema", default="AIBI", help="Schemat SQL (domyślnie: AIBI)")
    args = parser.parse_args()

    result = save_view(
        draft_path=Path(args.draft),
        view_name=args.view_name,
        schema=args.schema,
    )
    print_json(result)


if __name__ == "__main__":
    main()
