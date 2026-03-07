"""
SqlClient — współdzielona logika SQL Server: połączenie, guardrails, wykonanie zapytania.

Używana przez: sql_query.py, excel_export.py, excel_export_bi.py
"""

import os
import sys
import time
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()


class SqlClient:
    DRIVER = "ODBC Driver 17 for SQL Server"
    TIMEOUT_SECONDS = 30
    BLOCKED_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "EXEC", "EXECUTE", "SP_", "XP_",
        "OPENROWSET", "OPENQUERY", "SELECT INTO",
    ]

    def validate(self, sql: str) -> str | None:
        """Zwraca komunikat błędu lub None gdy zapytanie jest bezpieczne."""
        upper = sql.upper()
        for keyword in self.BLOCKED_KEYWORDS:
            if keyword in upper:
                return f"BLOCKED_KEYWORD: '{keyword}' nie jest dozwolone"
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        if len(statements) > 1:
            return "MULTIPLE_STATEMENTS: dozwolone tylko jedno zapytanie"
        if not upper.lstrip().startswith("SELECT"):
            return "NOT_SELECT: dozwolone tylko zapytania SELECT"
        return None

    def get_connection(self) -> pyodbc.Connection:
        conn_str = (
            f"DRIVER={{{self.DRIVER}}};"
            f"SERVER={os.getenv('SQL_SERVER')};"
            f"DATABASE={os.getenv('SQL_DATABASE')};"
            f"UID={os.getenv('SQL_USERNAME')};"
            f"PWD={os.getenv('SQL_PASSWORD')};"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str, timeout=self.TIMEOUT_SECONDS)

    def execute(self, sql: str, inject_top: int | None = 100) -> dict:
        """
        Wykonuje zapytanie SELECT. Zwraca słownik wewnętrzny (nie kontrakt CLI).

        inject_top: gdy podane i brak TOP w SQL — wstawia TOP N. None = bez wstrzyknięcia.
        """
        error = self.validate(sql)
        if error:
            return {
                "ok": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "duration_ms": 0,
                "error": {"type": "VALIDATION_ERROR", "message": error},
            }

        if inject_top is not None and "TOP " not in sql.upper():
            sql = sql.replace("SELECT ", f"SELECT TOP {inject_top} ", 1)

        start = time.monotonic()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = [list(row) for row in cursor.fetchall()]
            duration_ms = round((time.monotonic() - start) * 1000)
            truncated = inject_top is not None and len(rows) == inject_top
            return {
                "ok": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "truncated": truncated,
                "duration_ms": duration_ms,
                "error": None,
            }
        except pyodbc.Error as e:
            duration_ms = round((time.monotonic() - start) * 1000)
            message = e.args[1] if len(e.args) > 1 else str(e)
            return {
                "ok": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "duration_ms": duration_ms,
                "error": {"type": "SQL_ERROR", "message": message},
            }
