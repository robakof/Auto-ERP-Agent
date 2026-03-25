"""Service for session logs, session records, and conversation entries."""

import sqlite3
from typing import Optional


class SessionService:
    """Manage session logs, upsert sessions, conversation entries."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add_log(
        self,
        role: str,
        content: str,
        title: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """Add a session log entry. Returns log id."""
        cursor = self._conn.execute(
            """INSERT INTO session_log (role, content, title, session_id)
               VALUES (?, ?, ?, ?)""",
            (role, content, title, session_id),
        )
        return cursor.lastrowid

    def get_log(self, role: str, limit: int = 20) -> list[dict]:
        """Get session log entries for a role. Newest first."""
        rows = self._conn.execute(
            """SELECT id, role, content, title, session_id, created_at
               FROM session_log WHERE role = ?
               ORDER BY created_at DESC, id DESC
               LIMIT ?""",
            (role, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_logs(
        self,
        role: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        metadata_only: bool = False,
    ) -> list[dict]:
        """Get session log entries. Optionally filter by role. Newest first."""
        if metadata_only:
            fields = "id, role, title, created_at"
        else:
            fields = "id, role, content, title, session_id, created_at"

        if role:
            query = f"""SELECT {fields}
                        FROM session_log WHERE role = ?
                        ORDER BY created_at DESC, id DESC
                        LIMIT ? OFFSET ?"""
            rows = self._conn.execute(query, (role, limit, offset)).fetchall()
        else:
            query = f"""SELECT {fields}
                        FROM session_log
                        ORDER BY created_at DESC, id DESC
                        LIMIT ? OFFSET ?"""
            rows = self._conn.execute(query, (limit, offset)).fetchall()

        return [dict(row) for row in rows]

    def get_logs_init(self, role: str) -> dict:
        """Get session logs for session initialization.

        Returns:
            Dict with keys: own_full, own_metadata, cross_role (or None)
        """
        executor_roles = ["erp_specialist", "analyst"]

        own_full = self.get_logs(role=role, limit=3, metadata_only=False)
        own_metadata = self.get_logs(role=role, offset=3, limit=7, metadata_only=True)

        cross_role = None
        if role not in executor_roles:
            cross_role = self.get_logs(limit=20, metadata_only=True)

        return {
            "own_full": own_full,
            "own_metadata": own_metadata,
            "cross_role": cross_role,
        }

    def upsert(
        self,
        session_id: str,
        role: Optional[str] = None,
        claude_session_id: Optional[str] = None,
        transcript_path: Optional[str] = None,
        ended_at: Optional[str] = None,
    ) -> None:
        """Insert or update a session record."""
        self._conn.execute(
            """INSERT INTO sessions (id, role, claude_session_id, transcript_path, ended_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   role              = COALESCE(excluded.role, role),
                   claude_session_id = COALESCE(excluded.claude_session_id, claude_session_id),
                   transcript_path   = COALESCE(excluded.transcript_path, transcript_path),
                   ended_at          = COALESCE(excluded.ended_at, ended_at)""",
            (session_id, role, claude_session_id, transcript_path, ended_at),
        )

    def add_conversation_entry(
        self,
        speaker: str,
        content: str,
        event_type: str,
        session_id: Optional[str] = None,
        raw_payload: Optional[str] = None,
    ) -> int:
        """Log a conversation event. Returns entry id."""
        cursor = self._conn.execute(
            """INSERT INTO conversation (session_id, speaker, content, event_type, raw_payload)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, speaker, content, event_type, raw_payload),
        )
        return cursor.lastrowid

    def get_conversation(self, session_id: str) -> list[dict]:
        """Get conversation entries for a session."""
        rows = self._conn.execute(
            """SELECT id, session_id, speaker, content, event_type, created_at
               FROM conversation WHERE session_id = ? ORDER BY id""",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]
