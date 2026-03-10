"""
SqlExecutor — wykonanie SQL na schemacie AIBI.* przez konto CEIM_AIBI.

Używa create_bot_sql_client() — konto BOT_SQL_* z .env.
Max 200 wierszy na zapytanie.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.sql_client import SqlClient, create_bot_sql_client

MAX_ROWS = 200


@dataclass
class ExecutionResult:
    ok: bool
    columns: list[str]
    rows: list[list]
    row_count: int
    error: str | None
    duration_ms: int


class SqlExecutor:
    def __init__(self, client: SqlClient | None = None):
        self.client = client or create_bot_sql_client()

    def execute(self, sql: str) -> ExecutionResult:
        result = self.client.execute(sql, inject_top=MAX_ROWS)
        if not result["ok"]:
            return ExecutionResult(
                ok=False,
                columns=[],
                rows=[],
                row_count=0,
                error=result["error"]["message"],
                duration_ms=result["duration_ms"],
            )
        return ExecutionResult(
            ok=True,
            columns=result["columns"],
            rows=result["rows"],
            row_count=result["row_count"],
            error=None,
            duration_ms=result["duration_ms"],
        )
