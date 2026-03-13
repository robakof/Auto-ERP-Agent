"""AgentBus — message passing and state management for agent swarm via SQLite.

Provides structured communication between agent roles (erp_specialist, analyst,
developer, metodolog, human) and persistent state tracking (progress, reflections,
backlog items).
"""

import json
import sqlite3
from pathlib import Path

_SCHEMA_SQL = """
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

    def close(self):
        """Close the database connection."""
        self._conn.close()
