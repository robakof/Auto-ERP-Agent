"""
E-04: Weryfikacja działania narzędzia jako skrypt CLI wywoływany przez agenta
Cel: sprawdzić czy sql_query.py wywołany z bash zwraca poprawny JSON,
     jaki jest efekt dużego outputu i czy błędy są czytelne dla agenta.
"""

import json
import os
import sys
import textwrap
import pyodbc
from dotenv import load_dotenv

load_dotenv()

DRIVER = "ODBC Driver 17 for SQL Server"
SERVER = os.getenv("SQL_SERVER")
DATABASE = os.getenv("SQL_DATABASE")
USERNAME = os.getenv("SQL_USERNAME")
PASSWORD = os.getenv("SQL_PASSWORD")
DEFAULT_TOP = 100

BLOCKED_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
                    "TRUNCATE", "EXEC", "EXECUTE", "sp_", "xp_", "OPENROWSET",
                    "OPENQUERY", "SELECT INTO"]


def get_connection():
    conn_str = (
        f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};"
        f"UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=10)


def validate_query(sql: str) -> str | None:
    """Zwraca komunikat błędu lub None gdy zapytanie jest OK."""
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


def run_query(sql: str, inject_top: bool = True) -> dict:
    error = validate_query(sql)
    if error:
        return {"ok": False, "data": None,
                "error": {"type": "VALIDATION_ERROR", "message": error},
                "meta": {"duration_ms": 0, "truncated": False}}

    # Wstrzyknięcie TOP 100 jeśli brak
    if inject_top and "TOP " not in sql.upper():
        sql = sql.replace("SELECT ", f"SELECT TOP {DEFAULT_TOP} ", 1)

    import time
    start = time.monotonic()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]
        duration = round((time.monotonic() - start) * 1000)
        truncated = len(rows) == DEFAULT_TOP
        return {
            "ok": True,
            "data": {"columns": columns, "rows": rows, "row_count": len(rows)},
            "error": None,
            "meta": {"duration_ms": duration, "truncated": truncated}
        }
    except pyodbc.Error as e:
        duration = round((time.monotonic() - start) * 1000)
        return {
            "ok": False, "data": None,
            "error": {"type": "SQL_ERROR", "message": str(e.args[1])},
            "meta": {"duration_ms": duration, "truncated": False}
        }


# ── Testy ──────────────────────────────────────────────────────────────────


def test_basic_select():
    print("[1] Podstawowy SELECT — czy JSON jest poprawny:")
    result = run_query("SELECT ZaN_GIDNumer, ZaN_GIDTyp FROM CDN.ZamNag")
    ok = result["ok"] and len(result["data"]["rows"]) > 0
    print(f"    {'OK' if ok else 'FAIL'} — {result['data']['row_count']} wierszy, "
          f"{result['meta']['duration_ms']} ms, truncated={result['meta']['truncated']}")
    return ok


def test_top_injection():
    print("[2] Auto-wstrzykiwanie TOP 100:")
    result = run_query("SELECT ZaN_GIDNumer FROM CDN.ZamNag")
    ok = result["ok"] and result["data"]["row_count"] <= DEFAULT_TOP
    print(f"    {'OK' if ok else 'FAIL'} — zwrócono {result['data']['row_count']} wierszy (max {DEFAULT_TOP})")
    return ok


def test_blocked_dml():
    print("[3] Blokada DML na poziomie walidacji (przed wysłaniem do DB):")
    for sql in ["INSERT INTO CDN.ZamNag VALUES (1)", "DELETE FROM CDN.ZamNag", "EXEC sp_who"]:
        result = run_query(sql)
        status = "OK" if not result["ok"] and result["error"]["type"] == "VALIDATION_ERROR" else "FAIL"
        print(f"    [{status}] '{sql[:40]}' -> {result['error']['message']}")


def test_sql_error_format():
    print("[4] Format błędu SQL — czy agent dostaje czytelny komunikat:")
    result = run_query("SELECT nieistniejaca_kolumna FROM CDN.ZamNag")
    ok = not result["ok"] and result["error"]["type"] == "SQL_ERROR"
    print(f"    {'OK' if ok else 'FAIL'} — {result['error']['message'][:80]}")
    return ok


def test_output_size():
    print("[5] Rozmiar outputu JSON przy 100 wierszach x wiele kolumn:")
    result = run_query("SELECT * FROM CDN.ZamNag")
    output = json.dumps(result, default=str)
    size_kb = round(len(output.encode()) / 1024, 1)
    print(f"    Rozmiar: {size_kb} KB, kolumn: {len(result['data']['columns'])}, "
          f"wierszy: {result['data']['row_count']}")
    if size_kb > 500:
        print("    UWAGA — output duży, rozważ ograniczenie kolumn w zapytaniach agenta")
    else:
        print("    OK — rozmiar akceptowalny")


def test_information_schema():
    print("[6] Zapytanie INFORMATION_SCHEMA — kluczowe dla eksploracji schematu:")
    result = run_query(
        "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = 'ZamNag'"
    )
    ok = result["ok"] and result["data"]["row_count"] > 0
    print(f"    {'OK' if ok else 'FAIL'} — {result['data']['row_count']} kolumn w ZamNag")
    return ok


if __name__ == "__main__":
    print("=== E-04: Weryfikacja narzędzia sql_query jako CLI ===\n")
    test_basic_select()
    test_top_injection()
    test_blocked_dml()
    test_sql_error_format()
    test_output_size()
    test_information_schema()

    print("\n[E-04] Zakończono")
    print("\nDodatkowy test — wywołanie jak agent (przez bash, JSON na stdout):")
    result = run_query("SELECT TOP 3 ZaN_GIDNumer FROM CDN.ZamNag")
    print(json.dumps(result, indent=2, default=str))
