"""
SqlClient — współdzielona logika SQL Server: połączenie, guardrails, wykonanie zapytania.

Używana przez: sql_query.py, excel_export.py, excel_export_bi.py, bot/sql_executor.py
"""

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()


@dataclass(frozen=True)
class SqlCredentials:
    server: str
    database: str
    username: str
    password: str

    @classmethod
    def from_env(cls, prefix: str = "SQL_") -> "SqlCredentials":
        return cls(
            server=os.getenv(f"{prefix}SERVER", ""),
            database=os.getenv(f"{prefix}DATABASE", ""),
            username=os.getenv(f"{prefix}USERNAME", ""),
            password=os.getenv(f"{prefix}PASSWORD", ""),
        )


def create_erp_sql_client() -> "SqlClient":
    return SqlClient(SqlCredentials.from_env("SQL_"))


def create_bot_sql_client() -> "SqlClient":
    return SqlClient(SqlCredentials.from_env("BOT_SQL_"))


class SqlClient:
    DRIVER = "ODBC Driver 17 for SQL Server"
    TIMEOUT_SECONDS = 30
    BLOCKED_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "EXEC", "EXECUTE", "SP_", "XP_",
        "OPENROWSET", "OPENQUERY", "SELECT INTO",
    ]

    def __init__(self, credentials: SqlCredentials | None = None):
        self.credentials = credentials or SqlCredentials.from_env("SQL_")

    @staticmethod
    def _strip_comments(sql: str) -> str:
        """Usuwa linie zaczynające się od -- (komentarze SQL)."""
        lines = [line for line in sql.splitlines() if not line.lstrip().startswith("--")]
        return "\n".join(lines)

    @staticmethod
    def _split_statements(sql: str) -> list[str]:
        """Dzieli SQL po średniku z pominięciem średników wewnątrz string literals."""
        statements = []
        current: list[str] = []
        in_string = False
        i = 0
        while i < len(sql):
            ch = sql[i]
            if in_string:
                current.append(ch)
                if ch == "'":
                    # '' = escaped quote — pozostajemy w stringu
                    if i + 1 < len(sql) and sql[i + 1] == "'":
                        current.append("'")
                        i += 2
                        continue
                    in_string = False
            else:
                if ch == "'":
                    in_string = True
                    current.append(ch)
                elif ch == ";":
                    fragment = "".join(current).strip()
                    if fragment:
                        statements.append(fragment)
                    current = []
                    i += 1
                    continue
                else:
                    current.append(ch)
            i += 1
        fragment = "".join(current).strip()
        if fragment:
            statements.append(fragment)
        return statements

    def validate(self, sql: str) -> str | None:
        """Zwraca komunikat błędu lub None gdy zapytanie jest bezpieczne."""
        sql = self._strip_comments(sql)
        upper = sql.upper()
        for keyword in self.BLOCKED_KEYWORDS:
            if keyword in upper:
                return f"BLOCKED_KEYWORD: '{keyword}' nie jest dozwolone"
        statements = self._split_statements(sql)
        if len(statements) > 1:
            return "MULTIPLE_STATEMENTS: dozwolone tylko jedno zapytanie"
        normalized = upper.lstrip()
        if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
            return "NOT_SELECT: dozwolone tylko zapytania SELECT"
        return None

    def get_connection(self) -> pyodbc.Connection:
        conn_str = (
            f"DRIVER={{{self.DRIVER}}};"
            f"SERVER={self.credentials.server};"
            f"DATABASE={self.credentials.database};"
            f"UID={self.credentials.username};"
            f"PWD={self.credentials.password};"
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

        if inject_top is not None and "TOP " not in sql.upper() and not sql.upper().lstrip().startswith("WITH"):
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
