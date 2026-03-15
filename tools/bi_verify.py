"""
bi_verify.py — Narzędzie agenta: test + eksport + statystyki widoku BI w 1 kroku.

CLI:
    python tools/bi_verify.py --draft SCIEZKA.sql --view-name NAZWA
                              [--plan SCIEZKA.xlsx] [--source-table CDN.XXX]
                              [--export SCIEZKA.xlsx] [--max-unique N]

Wykonuje 3 kroki: validate + execute SQL → export do Excel → statystyki arkusza Wynik.
Zwraca kompaktowy raport zamiast pełnych danych.

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.excel_export_bi import export_bi_view
from tools.excel_read_stats import read_stats
from tools.lib.output import print_json

EXPORTS_DIR = Path(__file__).parent.parent / "exports"
SOLUTIONS_BI_DIR = Path(__file__).parent.parent / "solutions" / "bi"


def _stable_export_path(view_name: str) -> Path | None:
    """Return stable export path in solutions/bi/{view_name}/ if directory exists."""
    safe_name = view_name.replace(" ", "_").replace("/", "_")
    solutions_dir = SOLUTIONS_BI_DIR / safe_name
    if solutions_dir.exists():
        return solutions_dir / f"{safe_name}_export.xlsx"
    return None


def verify(
    draft_path: Path,
    view_name: str,
    plan_path: Path | None = None,
    source_table: str | None = None,
    export_path: Path | None = None,
    max_unique: int = 20,
) -> dict:
    draft_path = Path(draft_path)
    if not draft_path.exists():
        return {
            "ok": False,
            "data": None,
            "error": {"type": "FILE_NOT_FOUND", "message": f"Plik draftu nie istnieje: {draft_path}"},
            "meta": {"duration_ms": 0},
        }

    if export_path is None:
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = view_name.replace(" ", "_").replace("/", "_")
        export_path = EXPORTS_DIR / f"{safe_name}_verify_{timestamp}.xlsx"

    export_path = Path(export_path)
    sql = draft_path.read_text(encoding="utf-8")

    export_result = export_bi_view(
        sql=sql,
        view_name=view_name,
        source_table=source_table,
        plan_path=plan_path,
        output_path=export_path,
    )

    if not export_result["ok"]:
        return {
            "ok": False,
            "data": None,
            "error": export_result["error"],
            "meta": export_result["meta"],
        }

    # Copy to stable path in solutions/bi/{view_name}/ if directory exists
    stable_path = _stable_export_path(view_name)
    if stable_path:
        shutil.copy2(export_path, stable_path)

    stats_result = read_stats(export_path, sheet_name="Wynik", max_unique=max_unique)

    col_stats = stats_result["data"]["columns"] if stats_result["ok"] else []

    return {
        "ok": True,
        "data": {
            "row_count": export_result["data"]["row_count"],
            "column_count": len(export_result["data"]["columns"]),
            "export_path": str(export_path.resolve()),
            **({"stable_export_path": str(stable_path.resolve())} if stable_path else {}),
            "stats": [
                {
                    "name": c["name"],
                    "distinct": c["distinct"],
                    "null_count": c["null_count"],
                    **({"values": c["values"]} if "values" in c else {"sample": c.get("sample", [])}),
                }
                for c in col_stats
            ],
        },
        "error": None,
        "meta": export_result["meta"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test + eksport + statystyki widoku BI w 1 kroku.")
    parser.add_argument("--draft", required=True, help="Ścieżka do pliku draftu .sql")
    parser.add_argument("--view-name", required=True, help="Nazwa widoku")
    parser.add_argument("--plan", default=None, help="Ścieżka do pliku planu (.xlsx)")
    parser.add_argument("--source-table", default=None, help="Tabela źródłowa (arkusz Surówka)")
    parser.add_argument("--export", "-e", default=None, help="Ścieżka do pliku .xlsx (domyślnie: auto)")
    parser.add_argument("--max-unique", type=int, default=20, help="Próg unikalnych wartości w stats")
    args = parser.parse_args()

    result = verify(
        draft_path=Path(args.draft),
        view_name=args.view_name,
        plan_path=Path(args.plan) if args.plan else None,
        source_table=args.source_table,
        export_path=Path(args.export) if args.export else None,
        max_unique=args.max_unique,
    )
    print_json(result)


if __name__ == "__main__":
    main()
