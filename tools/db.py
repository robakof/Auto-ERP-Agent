"""
db.py — Wspólna logika połączenia z bazą SQLite (docs.db).

Używane przez build_index.py i search_docs.py.
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_db(path: str | None = None) -> sqlite3.Connection:
    """
    Zwraca połączenie z docs.db.

    Jeśli path=None, ścieżka konstruowana z ERP_DOCS_PATH z .env:
        {ERP_DOCS_PATH}/index/docs.db
    Tworzy katalog nadrzędny jeśli nie istnieje.
    """
    if path is None:
        erp_docs = os.getenv("ERP_DOCS_PATH", "./erp_docs")
        path = os.path.join(erp_docs, "index", "docs.db")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
