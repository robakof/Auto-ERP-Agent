"""
search_docs.py — Narzędzie agenta: przeszukiwanie indeksu dokumentacji ERP (FTS5).

CLI:
    python tools/docs_search.py "kontrahent zamowienie" [--table CDN.ZamNag] [--limit 1000]

Output: JSON na stdout zgodny z kontraktem narzędzi agenta.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.db import get_db
from tools.lib.output import print_json


def build_fts_query(phrase: str) -> str:
    """Zamienia frazę na zapytanie FTS5 z prefix matching (token* dla każdego słowa)."""
    tokens = phrase.strip().split()
    return " ".join(f"{t}*" if not t.endswith("*") else t for t in tokens if t)


def _build_where(fts_query: str, table_filter: str | None) -> tuple[str, list]:
    """Buduje klauzulę WHERE i listę parametrów dla zapytania FTS5."""
    conditions = ["columns_fts MATCH ?"]
    params: list = [fts_query]
    if table_filter:
        conditions.append("table_name = ?")
        params.append(table_filter)
    return " AND ".join(conditions), params


def _execute_table_scan(conn, table_filter: str, limit: int) -> list:
    """Zwraca wszystkie kolumny z danej tabeli bez FTS (gdy phrase='')."""
    conditions = ["table_name = ?"]
    params: list = [table_filter]
    where = " AND ".join(conditions)
    return conn.execute(
        f"""
        SELECT table_name, table_label, col_name, col_label,
               data_type, is_useful, description, value_dict, sample_values
        FROM columns
        WHERE {where}
        ORDER BY rowid
        LIMIT ?
        """,
        params + [limit],
    ).fetchall()


def _execute_fts(conn, where: str, params: list, limit: int) -> list:
    """Wykonuje zapytanie FTS5 i zwraca wiersze. Rzuca wyjątek przy błędzie."""
    return conn.execute(
        f"""
        SELECT table_name, table_label, col_name, col_label,
               data_type, is_useful, description, value_dict, sample_values
        FROM columns_fts
        WHERE {where}
        ORDER BY rank
        LIMIT ?
        """,
        params + [limit],
    ).fetchall()


def _row_to_dict(row, compact: bool = False) -> dict:
    """Konwertuje wiersz SQLite na słownik per kontrakt JSON."""
    if compact:
        return {
            "col_name": row[2],
            "col_label": row[3],
        }
    return {
        "table_name": row[0],
        "table_label": row[1],
        "col_name": row[2],
        "col_label": row[3],
        "data_type": row[4],
        "is_useful": row[5],
        "description": row[6],
        "value_dict": row[7],
        "sample_values": row[8],
    }


def _search_gid_types(conn, fts_query: str) -> list[dict]:
    """Przeszukuje gid_types_fts i zwraca listę typów GID."""
    try:
        rows = conn.execute(
            """
            SELECT g.gid_type, g.internal_name, g.symbol, g.description
            FROM gid_types_fts f
            JOIN gid_types g ON g.rowid = f.rowid
            WHERE gid_types_fts MATCH ?
            ORDER BY rank
            LIMIT 20
            """,
            [fts_query],
        ).fetchall()
    except Exception:
        return []
    return [
        {"gid_type": r[0], "internal_name": r[1], "symbol": r[2], "description": r[3]}
        for r in rows
    ]


def search_docs(
    phrase: str,
    table_filter: str | None = None,
    limit: int = 20,
    db_path: str | None = None,
    compact: bool = False,
) -> dict:
    """Przeszukuje docs.db i zwraca wyniki per kontrakt JSON."""
    start = time.monotonic()

    try:
        conn = get_db(db_path)
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "NOT_FOUND", "message": str(e)},
            "meta": {"duration_ms": 0, "truncated": False},
        }

    fts_query = build_fts_query(phrase)
    if not fts_query and not table_filter:
        conn.close()
        return {
            "ok": True,
            "data": {"results": [], "gid_types": []},
            "error": None,
            "meta": {"duration_ms": 0, "truncated": False},
        }

    try:
        if not fts_query and table_filter:
            rows = _execute_table_scan(conn, table_filter, limit)
        else:
            where, params = _build_where(fts_query, table_filter)
            rows = _execute_fts(conn, where, params, limit)
        gid_types = _search_gid_types(conn, fts_query) if fts_query else []
    except Exception as e:
        duration_ms = round((time.monotonic() - start) * 1000)
        return {
            "ok": False,
            "data": None,
            "error": {"type": "QUERY_ERROR", "message": str(e)},
            "meta": {"duration_ms": duration_ms, "truncated": False},
        }
    finally:
        conn.close()

    duration_ms = round((time.monotonic() - start) * 1000)
    results = [_row_to_dict(row, compact=compact) for row in rows]
    data = {"results": results}
    if not compact:
        data["gid_types"] = gid_types
    return {
        "ok": True,
        "data": data,
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": len(results) == limit},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Przeszukuje indeks dokumentacji ERP.")
    parser.add_argument("phrase", nargs="?", default="", help="Fraza do wyszukania (opcjonalna gdy podano --table)")
    parser.add_argument("--table", default=None, help="Ogranicz do tabeli (np. CDN.ZamNag)")
    parser.add_argument("--limit", type=int, default=20, help="Maks. liczba wyników (domyślnie 20)")
    parser.add_argument("--compact", action="store_true", help="Zwróć tylko col_name i col_label bez opisów — minimalny output")
    args = parser.parse_args()

    result = search_docs(
        phrase=args.phrase,
        table_filter=args.table,
        limit=args.limit,
        compact=args.compact,
    )
    print_json(result)


if __name__ == "__main__":
    main()
