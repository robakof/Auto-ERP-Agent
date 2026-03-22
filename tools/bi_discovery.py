"""
bi_discovery.py — Narzędzie agenta: automatyczny raport discovery tabeli CDN.

CLI:
    python tools/bi_discovery.py CDN.ZamNag [--pk ZaN_GIDNumer] [--filter "warunek WHERE"]
                                             [--max-enum N]

Wykonuje jedno zbiorcze zapytanie COUNT DISTINCT per kolumna, następnie:
- enum/constant: GROUP BY z listą wartości
- kolumny z "Data" w nazwie lub typ SQL DATE: MIN/MAX + klasyfikacja daty

Role kolumn: empty | constant | enum | id | Clarion_DATE | Clarion_TIMESTAMP | SQL_DATE | text | numeric

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.output import print_json
from tools.lib.sql_client import SqlClient

_DATE_SQL_TYPES = frozenset({"date", "datetime", "datetime2", "smalldatetime", "datetimeoffset"})
_NUMERIC_TYPES = frozenset({
    "int", "bigint", "smallint", "tinyint",
    "numeric", "decimal", "float", "real", "money", "smallmoney",
})
_TEXT_TYPES = frozenset({"varchar", "nvarchar", "char", "nchar", "text", "ntext"})

_CLARION_DATE_MAX = 200_000
_CLARION_TIMESTAMP_MIN = 1_000_000_000


def _looks_like_date(name: str) -> bool:
    return "data" in name.lower()


def _classify_clarion(mn, mx) -> str:
    try:
        mn, mx = int(mn), int(mx)
    except (TypeError, ValueError):
        return "numeric"
    if mx >= _CLARION_TIMESTAMP_MIN:
        return "Clarion_TIMESTAMP"
    if 1 <= mn and mx <= _CLARION_DATE_MAX:
        return "Clarion_DATE"
    return "numeric"


def _error_result(error: dict, duration_ms: int = 0) -> dict:
    return {"ok": False, "data": None, "error": error, "meta": {"duration_ms": duration_ms}}


def discover(
    table: str,
    pk: str | None = None,
    filter_expr: str | None = None,
    max_enum: int = 20,
    no_enum: bool = False,
    skip_text_columns: bool = False,
    columns_only: bool = False,
) -> dict:
    client = SqlClient()
    where = f" WHERE {filter_expr}" if filter_expr else ""
    parts = table.split(".", 1)
    schema, tname = (parts[0], parts[1]) if len(parts) == 2 else ("dbo", parts[0])
    total_ms = 0

    # 1. Metadane kolumn
    meta = client.execute(
        f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{tname}' ORDER BY ORDINAL_POSITION",
        inject_top=None,
    )
    if not meta["ok"]:
        return _error_result(meta["error"], meta["duration_ms"])
    total_ms += meta["duration_ms"]

    col_meta = [{"name": r[0], "sql_type": r[1]} for r in meta["rows"]]
    col_names = [c["name"] for c in col_meta]

    # Tryb --columns-only: zwróć tylko metadane kolumn bez analizy
    if columns_only:
        columns = [{"name": cm["name"], "sql_type": cm["sql_type"]} for cm in col_meta]
        return {
            "ok": True,
            "data": {"table": table, "columns": columns, "mode": "columns_only"},
            "error": None,
            "meta": {"duration_ms": total_ms},
        }

    # 2. Baseline COUNT (+ opcjonalny COUNT DISTINCT pk)
    pk_part = f", COUNT(DISTINCT [{pk}])" if pk else ""
    baseline = client.execute(
        f"SELECT COUNT(*){pk_part} FROM {table}{where}",
        inject_top=None,
    )
    if not baseline["ok"]:
        return _error_result(baseline["error"], total_ms + baseline["duration_ms"])
    total_ms += baseline["duration_ms"]

    brow = baseline["rows"][0]
    row_count = int(brow[0])
    pk_distinct = int(brow[1]) if pk else None

    # 3. COUNT DISTINCT per kolumna (batch po 50)
    distinct_map: dict[str, int] = {}
    for i in range(0, len(col_names), 50):
        batch = col_names[i : i + 50]
        parts_sql = ", ".join(f"COUNT(DISTINCT [{c}])" for c in batch)
        cd = client.execute(f"SELECT {parts_sql} FROM {table}{where}", inject_top=None)
        if not cd["ok"]:
            return _error_result(cd["error"], total_ms + cd["duration_ms"])
        total_ms += cd["duration_ms"]
        for j, col in enumerate(batch):
            val = cd["rows"][0][j]
            distinct_map[col] = int(val) if val is not None else 0

    # 4. Klasyfikacja każdej kolumny
    columns = []
    for cm in col_meta:
        name, sql_type = cm["name"], cm["sql_type"]
        distinct = distinct_map.get(name, 0)
        col: dict = {"name": name, "sql_type": sql_type, "distinct": distinct}

        if distinct == 0:
            col["role"] = "empty"

        elif distinct <= max_enum:
            if no_enum:
                col["role"] = "constant" if distinct == 1 else "enum"
            else:
                group = client.execute(
                    f"SELECT TOP {max_enum + 1} [{name}], COUNT(*) FROM {table}{where} "
                    f"GROUP BY [{name}] ORDER BY COUNT(*) DESC",
                    inject_top=None,
                )
                if group["ok"]:
                    total_ms += group["duration_ms"]
                    vals = [r[0] for r in group["rows"]]
                    if distinct == 1:
                        col["role"] = "constant"
                        col["value"] = vals[0] if vals else None
                    else:
                        col["role"] = "enum"
                        col["values"] = vals
                else:
                    col["role"] = "constant" if distinct == 1 else "enum"

        elif distinct == row_count:
            col["role"] = "id"

        elif sql_type in _DATE_SQL_TYPES:
            mn_mx = client.execute(
                f"SELECT MIN([{name}]), MAX([{name}]) FROM {table}{where}",
                inject_top=None,
            )
            col["role"] = "SQL_DATE"
            if mn_mx["ok"]:
                total_ms += mn_mx["duration_ms"]
                col["min"] = mn_mx["rows"][0][0]
                col["max"] = mn_mx["rows"][0][1]

        elif sql_type in _NUMERIC_TYPES and _looks_like_date(name):
            mn_mx = client.execute(
                f"SELECT MIN([{name}]), MAX([{name}]) FROM {table}{where}",
                inject_top=None,
            )
            if mn_mx["ok"]:
                total_ms += mn_mx["duration_ms"]
                mn, mx = mn_mx["rows"][0]
                col["role"] = _classify_clarion(mn, mx)
                col["min"] = mn
                col["max"] = mx
            else:
                col["role"] = "numeric"

        elif sql_type in _TEXT_TYPES:
            col["role"] = "text"

        else:
            col["role"] = "numeric"

        # --skip-text-columns: pomiń kolumny role=text z outputu
        if skip_text_columns and col["role"] == "text":
            continue

        columns.append(col)

    data: dict = {"table": table, "row_count": row_count, "columns": columns}
    if pk:
        data["pk_distinct"] = pk_distinct
    if filter_expr:
        data["filter"] = filter_expr

    return {
        "ok": True,
        "data": data,
        "error": None,
        "meta": {"duration_ms": total_ms},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Raport discovery tabeli CDN dla widoku BI.")
    parser.add_argument("table", help="Nazwa tabeli, np. CDN.ZamNag")
    parser.add_argument("--pk", default=None, help="Kolumna klucza głównego (COUNT DISTINCT)")
    parser.add_argument("--filter", dest="filter_expr", default=None, help="Warunek WHERE")
    parser.add_argument("--max-enum", type=int, default=20, help="Próg enumeracji i limit wartości (domyślnie: 20)")
    parser.add_argument("--no-enum", action="store_true",
                        help="Pomiń GROUP BY dla kolumn enum — tylko role/distinct, bez listy wartości. "
                             "Zalecane dla dużych tabel (>50 kolumn) — redukuje output i czas zapytań.")
    parser.add_argument("--skip-text-columns", action="store_true",
                        help="Pomiń kolumny role=text z outputu — zmniejsza rozmiar wyniku dla tabel z długimi tekstami.")
    parser.add_argument("--columns-only", action="store_true",
                        help="Tylko nazwy i typy kolumn, bez analizy distinct values — najszybszy tryb.")
    args = parser.parse_args()

    result = discover(
        table=args.table,
        pk=args.pk,
        filter_expr=args.filter_expr,
        max_enum=args.max_enum,
        no_enum=args.no_enum,
        skip_text_columns=args.skip_text_columns,
        columns_only=args.columns_only,
    )
    print_json(result)


if __name__ == "__main__":
    main()
