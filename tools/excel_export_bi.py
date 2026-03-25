"""
excel_export_bi.py — Narzędzie agenta: eksport widoku BI do wieloarkuszowego pliku Excel.

CLI:
    python tools/excel_export_bi.py --sql "SELECT ..." --view-name "NazwaWidoku"
    python tools/excel_export_bi.py --file SCIEZKA.sql  --view-name "NazwaWidoku"
                                    [--source-table CDN.XXX] [--plan SCIEZKA.xlsx]
                                    [--output SCIEZKA.xlsx]

Arkusze:
  Plan    — tabela mapowania z pliku --plan (.xlsx lub .md); pusty szablon gdy brak
  Wynik   — wynik SQL (do 5000 wierszy)
  Surówka — SELECT TOP 200 * FROM source-table (jeśli podano --source-table)

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.excel_reader import ExcelReader
from tools.lib.excel_writer import ExcelWriter
from tools.lib.output import print_json
from tools.lib.sql_client import SqlClient

EXPORTS_DIR = Path(__file__).parent.parent / "exports"
RAW_TOP = 200


def _plan_sheet_data(plan_path: Path | None) -> tuple[list[str], list[list]]:
    """Zwraca (columns, rows) dla arkusza Plan."""
    if plan_path and plan_path.exists():
        if plan_path.suffix == ".xlsx":
            try:
                with ExcelReader(plan_path) as reader:
                    result = reader.read_rows()
                if result["ok"]:
                    return result["data"]["columns"], result["data"]["rows"]
            except Exception:  # noqa: BLE001
                pass
        else:
            # legacy .md — wstaw jako tekst w jednej kolumnie
            lines = plan_path.read_text(encoding="utf-8").splitlines()
            return ["Plan_MD"], [[line] for line in lines]

    # fallback — pusty szablon
    cols = ["CDN_Pole", "Alias_w_widoku", "Transformacja", "Uwzglednic", "Uzasadnienie"]
    return cols, [["-- brak pliku --plan; uzupełnij ręcznie --"] + [""] * (len(cols) - 1)]


def export_bi_view(
    sql: str,
    view_name: str,
    source_table: str | None = None,
    plan_path: Path | None = None,
    output_path: Path | None = None,
) -> dict:
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = view_name.replace(" ", "_").replace("/", "_")
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = EXPORTS_DIR / f"{safe_name}_{timestamp}.xlsx"

    output_path = Path(output_path)
    client = SqlClient()

    result = client.execute(sql, inject_top=5000)
    if not result["ok"]:
        return {
            "ok": False,
            "data": None,
            "error": result["error"],
            "meta": {"duration_ms": result["duration_ms"]},
        }

    raw_result = None
    if source_table:
        raw_result = client.execute(f"SELECT TOP {RAW_TOP} * FROM {source_table}", inject_top=None)

    try:
        writer = ExcelWriter()

        plan_cols, plan_rows = _plan_sheet_data(plan_path)
        writer.add_sheet("Plan", plan_cols, plan_rows)
        writer.add_sheet("Wynik", result["columns"], result["rows"])

        sheets = ["Plan", "Wynik"]
        if raw_result and raw_result["ok"]:
            writer.add_sheet("Surówka", raw_result["columns"], raw_result["rows"])
            sheets.append("Surówka")

        writer.save(output_path)
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "data": None,
            "error": {"type": "EXPORT_ERROR", "message": str(e)},
            "meta": {"duration_ms": result["duration_ms"]},
        }

    return {
        "ok": True,
        "data": {
            "path": str(output_path.resolve()),
            "view_name": view_name,
            "row_count": result["row_count"],
            "columns": result["columns"],
            "sheets": sheets,
        },
        "error": None,
        "meta": {"duration_ms": result["duration_ms"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Eksportuj widok BI do wieloarkuszowego Excel.")
    parser.add_argument("--sql", default=None, help="Zapytanie SELECT (inline)")
    parser.add_argument("--file", "-f", default=None, help="Ścieżka do pliku .sql z zapytaniem")
    parser.add_argument("--view-name", required=True, help="Nazwa widoku")
    parser.add_argument("--source-table", default=None, help="Tabela źródłowa (arkusz Surówka)")
    parser.add_argument("--plan", default=None, help="Ścieżka do pliku planu (.xlsx lub .md)")
    parser.add_argument("--output", "-o", default=None, help="Ścieżka do pliku .xlsx")
    args = parser.parse_args()

    _error_meta = {"duration_ms": 0}

    if args.file:
        sql_path = Path(args.file)
        if not sql_path.exists():
            print_json({
                "ok": False, "data": None,
                "error": {"type": "FILE_NOT_FOUND", "message": f"Plik SQL nie istnieje: {args.file}"},
                "meta": _error_meta,
            })
            return
        sql = sql_path.read_text(encoding="utf-8")
    elif args.sql:
        sql = args.sql
    else:
        print_json({
            "ok": False, "data": None,
            "error": {"type": "MISSING_ARGUMENT", "message": "Podaj zapytanie SQL przez --sql lub --file"},
            "meta": _error_meta,
        })
        return

    result = export_bi_view(
        sql=sql,
        view_name=args.view_name,
        source_table=args.source_table,
        plan_path=Path(args.plan) if args.plan else None,
        output_path=Path(args.output) if args.output else None,
    )
    print_json(result)


if __name__ == "__main__":
    main()
