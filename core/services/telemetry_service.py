"""Service for telemetry: tool calls, token usage, session traces."""

import sqlite3
from typing import Optional


class TelemetryService:
    """Track tool calls, token usage, and session traces."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add_tool_call(
        self,
        session_id: str,
        tool_name: str,
        input_summary: Optional[str] = None,
        is_error: int = 0,
        tokens_out: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """Log a tool call. Returns row id or 0 if duplicate."""
        cursor = self._conn.execute(
            """INSERT OR IGNORE INTO tool_calls (session_id, tool_name, input_summary, is_error, tokens_out, timestamp)
               VALUES (?, ?, ?, ?, ?, COALESCE(?, datetime('now', 'localtime')))""",
            (session_id, tool_name, input_summary, is_error, tokens_out, timestamp),
        )
        return cursor.lastrowid

    def add_token_usage(
        self,
        session_id: str,
        turn_index: int,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cache_read_tokens: Optional[int] = None,
        cache_create_tokens: Optional[int] = None,
        duration_ms: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        """Log token usage for one assistant turn. Returns row id."""
        cursor = self._conn.execute(
            """INSERT INTO token_usage
               (session_id, turn_index, input_tokens, output_tokens,
                cache_read_tokens, cache_create_tokens, duration_ms, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now', 'localtime')))""",
            (session_id, turn_index, input_tokens, output_tokens,
             cache_read_tokens, cache_create_tokens, duration_ms, timestamp),
        )
        return cursor.lastrowid

    def get_session_trace(self, session_id: str) -> Optional[dict]:
        """Return session metadata with tool_calls and token_usage."""
        session_row = self._conn.execute(
            "SELECT id, claude_session_id, role, transcript_path, started_at, ended_at FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not session_row:
            return None
        tool_rows = self._conn.execute(
            """SELECT id, tool_name, input_summary, is_error, tokens_out, timestamp
               FROM tool_calls WHERE session_id = ? ORDER BY id""",
            (session_id,),
        ).fetchall()
        token_rows = self._conn.execute(
            """SELECT turn_index, input_tokens, output_tokens,
                      cache_read_tokens, cache_create_tokens, duration_ms, timestamp
               FROM token_usage WHERE session_id = ? ORDER BY turn_index""",
            (session_id,),
        ).fetchall()
        return {
            "session": dict(session_row),
            "tool_calls": [dict(r) for r in tool_rows],
            "token_usage": [dict(r) for r in token_rows],
        }
