"""
search_docs.py — Narzędzie agenta: przeszukiwanie indeksu dokumentacji ERP (FTS5).

CLI:
    python tools/search_docs.py "kontrahent zamowienie" [--table CDN.ZamNag] [--useful-only] [--limit 10]

Output: JSON na stdout zgodny z kontraktem z ARCHITECTURE.md.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.db import get_db


def build_fts_query(phrase: str) -> str:
    """Zamienia frazę na zapytanie FTS5 z prefix matching (token* dla każdego słowa)."""
    tokens = phrase.strip().split()
    return " ".join(f"{t}*" if not t.endswith("*") else t for t in tokens if t)


def search_docs(
    phrase: str,
    table_filter: str | None = None,
    useful_only: bool = False,
    limit: int = 20,
    db_path: str | None = None,
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
    if not fts_query:
        return {
            "ok": True,
            "data": {"results": []},
            "error": None,
            "meta": {"duration_ms": 0, "truncated": False},
        }

    conditions = ["columns_fts MATCH ?"]
    params: list = [fts_query]

    if table_filter:
        conditions.append("table_name = ?")
        params.append(table_filter)

    if useful_only:
        conditions.append("is_useful NOT IN ('', 'Nie', 'Relacja')")

    where = " AND ".join(conditions)

    try:
        rows = conn.execute(
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
    results = [
        {
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
        for row in rows
    ]

    return {
        "ok": True,
        "data": {"results": results},
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": len(results) == limit},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Przeszukuje indeks dokumentacji ERP.")
    parser.add_argument("phrase", help="Fraza do wyszukania")
    parser.add_argument("--table", default=None, help="Ogranicz do tabeli (np. CDN.ZamNag)")
    parser.add_argument("--useful-only", action="store_true", help="Tylko kolumny użyteczne")
    parser.add_argument("--limit", type=int, default=20, help="Maks. liczba wyników (domyślnie 20)")
    args = parser.parse_args()

    result = search_docs(
        phrase=args.phrase,
        table_filter=args.table,
        useful_only=args.useful_only,
        limit=args.limit,
    )
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
