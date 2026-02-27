"""
sql_query.py — Narzędzie agenta: wykonywanie zapytań SELECT na SQL Server ERP.

CLI:
    python tools/sql_query.py "SELECT TOP 5 ZaN_GIDNumer FROM CDN.ZamNag"

Output: JSON na stdout zgodny z kontraktem z ARCHITECTURE.md.
"""

import json
import os
import sys
import time

import pyodbc
from dotenv import load_dotenv

load_dotenv()

DRIVER = "ODBC Driver 17 for SQL Server"
DEFAULT_TOP = 100
TIMEOUT_SECONDS = 30

BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TRUNCATE", "EXEC", "EXECUTE", "SP_", "XP_",
    "OPENROWSET", "OPENQUERY", "SELECT INTO",
]


def get_connection() -> pyodbc.Connection:
    """Tworzy połączenie z SQL Server na podstawie zmiennych środowiskowych."""
    conn_str = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={os.getenv('SQL_SERVER')};"
        f"DATABASE={os.getenv('SQL_DATABASE')};"
        f"UID={os.getenv('SQL_USERNAME')};"
        f"PWD={os.getenv('SQL_PASSWORD')};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=TIMEOUT_SECONDS)


def validate_query(sql: str) -> str | None:
    """Zwraca komunikat błędu lub None gdy zapytanie jest bezpieczne do wykonania."""
    upper = sql.upper()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in upper:
            return f"BLOCKED_KEYWORD: '{keyword}' nie jest dozwolone"
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    if len(statements) > 1:
        return "MULTIPLE_STATEMENTS: dozwolone tylko jedno zapytanie"
    if not upper.lstrip().startswith("SELECT"):
        return "NOT_SELECT: dozwolone tylko zapytania SELECT"
    return None


def run_query(sql: str) -> dict:
    """Wykonuje zapytanie SQL i zwraca wynik jako słownik per kontrakt JSON."""
    error = validate_query(sql)
    if error:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "VALIDATION_ERROR", "message": error},
            "meta": {"duration_ms": 0, "truncated": False},
        }

    if "TOP " not in sql.upper():
        sql = sql.replace("SELECT ", f"SELECT TOP {DEFAULT_TOP} ", 1)

    start = time.monotonic()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]
        duration_ms = round((time.monotonic() - start) * 1000)
        truncated = len(rows) == DEFAULT_TOP
        return {
            "ok": True,
            "data": {"columns": columns, "rows": rows, "row_count": len(rows)},
            "error": None,
            "meta": {"duration_ms": duration_ms, "truncated": truncated},
        }
    except pyodbc.Error as e:
        duration_ms = round((time.monotonic() - start) * 1000)
        message = e.args[1] if len(e.args) > 1 else str(e)
        return {
            "ok": False,
            "data": None,
            "error": {"type": "SQL_ERROR", "message": message},
            "meta": {"duration_ms": duration_ms, "truncated": False},
        }


def main():
    """Entry point CLI."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "ok": False,
            "data": None,
            "error": {"type": "MISSING_ARGUMENT", "message": 'Usage: sql_query.py "SELECT ..."'},
            "meta": {"duration_ms": 0, "truncated": False},
        }))
        return
    sql = sys.argv[1]
    result = run_query(sql)
    print(json.dumps(result, default=str))


if __name__ == "__main__":
    main()
