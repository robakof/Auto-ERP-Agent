"""AgentBus — message passing and state management for agent swarm via SQLite.

Provides structured communication between agent roles (erp_specialist, analyst,
developer, metodolog, human) and persistent state tracking (progress, reflections,
backlog items).
"""

import json
import sqlite3
from pathlib import Path

ALLOWED_MESSAGE_TYPES = {"suggestion", "task", "info", "flag_human"}

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS suggestions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    author      TEXT NOT NULL,
    recipients  TEXT,
    content     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',
    backlog_id  INTEGER REFERENCES backlog(id),
    session_id  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status);
CREATE INDEX IF NOT EXISTS idx_suggestions_author ON suggestions(author);

CREATE TABLE IF NOT EXISTS backlog (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    area        TEXT,
    value       TEXT,
    effort      TEXT,
    status      TEXT NOT NULL DEFAULT 'planned',
    source_id   INTEGER REFERENCES suggestions(id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_backlog_status ON backlog(status);

CREATE TABLE IF NOT EXISTS session_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    session_id  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_session_log_role ON session_log(role);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender      TEXT NOT NULL,
    recipient   TEXT NOT NULL,
    type        TEXT NOT NULL DEFAULT 'suggestion',
    content     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'unread',
    session_id  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    read_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_recipient_status
    ON messages(recipient, status);
CREATE INDEX IF NOT EXISTS idx_messages_session
    ON messages(session_id);

CREATE TABLE IF NOT EXISTS state (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role        TEXT NOT NULL,
    type        TEXT NOT NULL,
    content     TEXT NOT NULL,
    session_id  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    metadata    TEXT
);

CREATE INDEX IF NOT EXISTS idx_state_role_type ON state(role, type);
CREATE INDEX IF NOT EXISTS idx_state_session ON state(session_id);

CREATE TABLE IF NOT EXISTS trace (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    tool_name   TEXT NOT NULL,
    summary     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trace_session ON trace(session_id);

CREATE TABLE IF NOT EXISTS sessions (
    id                TEXT PRIMARY KEY,
    claude_session_id TEXT,
    role              TEXT,
    transcript_path   TEXT,
    started_at        TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at          TEXT
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT REFERENCES sessions(id),
    tool_name     TEXT NOT NULL,
    input_summary TEXT,
    is_error      INTEGER NOT NULL DEFAULT 0,
    tokens_out    INTEGER,
    timestamp     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_session ON tool_calls(session_id);

CREATE TABLE IF NOT EXISTS token_usage (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id           TEXT REFERENCES sessions(id),
    turn_index           INTEGER NOT NULL,
    input_tokens         INTEGER,
    output_tokens        INTEGER,
    cache_read_tokens    INTEGER,
    cache_create_tokens  INTEGER,
    duration_ms          INTEGER,
    timestamp            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_token_usage_session ON token_usage(session_id);

CREATE TABLE IF NOT EXISTS conversation (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT,
    speaker     TEXT NOT NULL,
    content     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    raw_payload TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation(session_id);
"""


class AgentBus:
    """SQLite-backed message bus for agent communication and state persistence."""

    def __init__(self, db_path: str = "mrowisko.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    # --- Messages ---

    def send_message(
        self,
        sender: str,
        recipient: str,
        content: str,
        type: str = "suggestion",
        session_id: str = None,
    ) -> int:
        """Send a message from one role to another. Returns message id."""
        if type not in ALLOWED_MESSAGE_TYPES:
            raise ValueError(f"Invalid message type '{type}'. Allowed: {sorted(ALLOWED_MESSAGE_TYPES)}")
        cursor = self._conn.execute(
            """INSERT INTO messages (sender, recipient, type, content, session_id)
               VALUES (?, ?, ?, ?, ?)""",
            (sender, recipient, type, content, session_id),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_inbox(self, role: str, status: str = "unread") -> list[dict]:
        """Get messages for a role filtered by status. Ordered by created_at ASC."""
        rows = self._conn.execute(
            """SELECT id, sender, recipient, type, content, status,
                      session_id, created_at, read_at
               FROM messages
               WHERE recipient = ? AND status = ?
               ORDER BY created_at ASC""",
            (role, status),
        ).fetchall()
        return [dict(row) for row in rows]

    def mark_read(self, message_id: int) -> None:
        """Mark a message as read and set read_at timestamp."""
        self._conn.execute(
            """UPDATE messages
               SET status = 'read', read_at = datetime('now')
               WHERE id = ?""",
            (message_id,),
        )
        self._conn.commit()

    def archive_message(self, message_id: int) -> None:
        """Archive a message (status='archived')."""
        self._conn.execute(
            "UPDATE messages SET status = 'archived' WHERE id = ?",
            (message_id,),
        )
        self._conn.commit()

    # --- State ---

    def write_state(
        self,
        role: str,
        type: str,
        content: str,
        session_id: str = None,
        metadata: dict = None,
    ) -> int:
        """Write a state entry (progress, reflection, backlog_item). Returns id."""
        meta_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        cursor = self._conn.execute(
            """INSERT INTO state (role, type, content, session_id, metadata)
               VALUES (?, ?, ?, ?, ?)""",
            (role, type, content, session_id, meta_json),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_state(
        self,
        role: str,
        type: str = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get state entries for a role. Newest first. Optional type filter."""
        if type:
            rows = self._conn.execute(
                """SELECT id, role, type, content, session_id, created_at, metadata
                   FROM state
                   WHERE role = ? AND type = ?
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (role, type, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT id, role, type, content, session_id, created_at, metadata
                   FROM state
                   WHERE role = ?
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (role, limit),
            ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d["metadata"]:
                d["metadata"] = json.loads(d["metadata"])
            result.append(d)
        return result

    # --- Suggestions ---

    def add_suggestion(
        self,
        author: str,
        content: str,
        recipients: list[str] = None,
        session_id: str = None,
    ) -> int:
        """Add a suggestion from an agent. Returns suggestion id."""
        recipients_json = json.dumps(recipients, ensure_ascii=False) if recipients else None
        cursor = self._conn.execute(
            """INSERT INTO suggestions (author, recipients, content, session_id)
               VALUES (?, ?, ?, ?)""",
            (author, recipients_json, content, session_id),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_suggestions(
        self,
        status: str = None,
        author: str = None,
    ) -> list[dict]:
        """Get suggestions. Newest first. Optional status and author filters."""
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if author:
            conditions.append("author = ?")
            params.append(author)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._conn.execute(
            f"""SELECT id, author, recipients, content, status, backlog_id,
                       session_id, created_at
                FROM suggestions
                {where}
                ORDER BY created_at DESC, id DESC""",
            params,
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d["recipients"]:
                d["recipients"] = json.loads(d["recipients"])
            result.append(d)
        return result

    def update_suggestion_status(
        self,
        suggestion_id: int,
        status: str,
        backlog_id: int = None,
    ) -> None:
        """Update suggestion status and optionally link to backlog item."""
        self._conn.execute(
            """UPDATE suggestions SET status = ?, backlog_id = ?
               WHERE id = ?""",
            (status, backlog_id, suggestion_id),
        )
        self._conn.commit()

    # --- Backlog ---

    def add_backlog_item(
        self,
        title: str,
        content: str,
        area: str = None,
        value: str = None,
        effort: str = None,
        source_id: int = None,
    ) -> int:
        """Add a backlog item. Returns backlog id."""
        cursor = self._conn.execute(
            """INSERT INTO backlog (title, content, area, value, effort, source_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, content, area, value, effort, source_id),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_backlog(self, status: str = None, area: str = None) -> list[dict]:
        """Get backlog items. Newest first. Optional status/area filter."""
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if area:
            conditions.append("area = ?")
            params.append(area)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self._conn.execute(
            f"""SELECT id, title, content, area, value, effort, status,
                      source_id, created_at, updated_at
               FROM backlog {where}
               ORDER BY created_at DESC, id DESC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def update_backlog_status(self, backlog_id: int, status: str) -> None:
        """Update backlog item status and set updated_at."""
        self._conn.execute(
            """UPDATE backlog SET status = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (status, backlog_id),
        )
        self._conn.commit()

    def update_backlog_content(self, backlog_id: int, content: str) -> None:
        """Update backlog item content and set updated_at."""
        self._conn.execute(
            """UPDATE backlog SET content = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (content, backlog_id),
        )
        self._conn.commit()

    # --- Session log ---

    def add_session_log(
        self,
        role: str,
        content: str,
        session_id: str = None,
    ) -> int:
        """Add a session log entry. Returns log id."""
        cursor = self._conn.execute(
            """INSERT INTO session_log (role, content, session_id)
               VALUES (?, ?, ?)""",
            (role, content, session_id),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_session_log(self, role: str, limit: int = 20) -> list[dict]:
        """Get session log entries for a role. Newest first."""
        rows = self._conn.execute(
            """SELECT id, role, content, session_id, created_at
               FROM session_log WHERE role = ?
               ORDER BY created_at DESC, id DESC
               LIMIT ?""",
            (role, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_messages(
        self,
        sender: str = None,
        recipient: str = None,
        status: str = None,
        limit: int = 200,
    ) -> list[dict]:
        """Get messages with optional filters. Newest first."""
        conditions, params = [], []
        if sender:
            conditions.append("sender = ?")
            params.append(sender)
        if recipient:
            conditions.append("recipient = ?")
            params.append(recipient)
        if status:
            conditions.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.append(limit)
        rows = self._conn.execute(
            f"""SELECT id, sender, recipient, type, content, status, session_id, created_at, read_at
                FROM messages {where}
                ORDER BY created_at DESC, id DESC
                LIMIT ?""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    # --- Human escalation ---

    def flag_for_human(
        self,
        sender: str,
        reason: str,
        urgency: str = "normal",
        session_id: str = None,
    ) -> int:
        """Shortcut: send a flag_human message to 'human' role."""
        content = f"[{urgency.upper()}] {reason}"
        return self.send_message(
            sender=sender,
            recipient="human",
            content=content,
            type="flag_human",
            session_id=session_id,
        )

    def mark_message_read(self, message_id: int) -> None:
        """Mark a message as read."""
        self._conn.execute(
            "UPDATE messages SET status = 'read', read_at = datetime('now') WHERE id = ?",
            (message_id,),
        )
        self._conn.commit()

    # --- Trace ---

    def add_trace_event(self, session_id: str, tool_name: str, summary: str = None) -> int:
        """Log a tool use event for a session."""
        cursor = self._conn.execute(
            "INSERT INTO trace (session_id, tool_name, summary) VALUES (?, ?, ?)",
            (session_id, tool_name, summary),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_trace(self, session_id: str) -> list[dict]:
        """Get all trace events for a session."""
        rows = self._conn.execute(
            "SELECT id, session_id, tool_name, summary, created_at FROM trace WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    # --- Sessions / trace module ---

    def upsert_session(
        self,
        session_id: str,
        role: str = None,
        claude_session_id: str = None,
        transcript_path: str = None,
        ended_at: str = None,
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
        self._conn.commit()

    def add_tool_call(
        self,
        session_id: str,
        tool_name: str,
        input_summary: str = None,
        is_error: int = 0,
        tokens_out: int = None,
        timestamp: str = None,
    ) -> int:
        """Log a tool call for a session. Returns row id."""
        cursor = self._conn.execute(
            """INSERT INTO tool_calls (session_id, tool_name, input_summary, is_error, tokens_out, timestamp)
               VALUES (?, ?, ?, ?, ?, COALESCE(?, datetime('now')))""",
            (session_id, tool_name, input_summary, is_error, tokens_out, timestamp),
        )
        self._conn.commit()
        return cursor.lastrowid

    def add_token_usage(
        self,
        session_id: str,
        turn_index: int,
        input_tokens: int = None,
        output_tokens: int = None,
        cache_read_tokens: int = None,
        cache_create_tokens: int = None,
        duration_ms: int = None,
        timestamp: str = None,
    ) -> int:
        """Log token usage for one assistant turn. Returns row id."""
        cursor = self._conn.execute(
            """INSERT INTO token_usage
               (session_id, turn_index, input_tokens, output_tokens,
                cache_read_tokens, cache_create_tokens, duration_ms, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now')))""",
            (session_id, turn_index, input_tokens, output_tokens,
             cache_read_tokens, cache_create_tokens, duration_ms, timestamp),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_session_trace(self, session_id: str) -> dict:
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

    # --- Conversation ---

    def add_conversation_entry(
        self,
        speaker: str,
        content: str,
        event_type: str,
        session_id: str = None,
        raw_payload: str = None,
    ) -> int:
        """Log a conversation event (user prompt, agent response, etc.)."""
        cursor = self._conn.execute(
            """INSERT INTO conversation (session_id, speaker, content, event_type, raw_payload)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, speaker, content, event_type, raw_payload),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_conversation(self, session_id: str) -> list[dict]:
        """Get conversation entries for a session."""
        rows = self._conn.execute(
            """SELECT id, session_id, speaker, content, event_type, created_at
               FROM conversation WHERE session_id = ? ORDER BY id""",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        """Close the database connection."""
        self._conn.close()
