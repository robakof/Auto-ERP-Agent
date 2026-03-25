"""Service for messaging between agents."""

import sqlite3
from typing import Optional

from core.entities.messaging import Message, MessageStatus
from core.mappers.legacy_api import LegacyAPIMapper
from core.repositories.message_repo import MessageRepository

ALLOWED_MESSAGE_TYPES = {"suggestion", "task", "info", "flag_human", "handoff"}


class MessageService:
    """Send, receive, and manage messages between agent roles."""

    def __init__(self, conn: sqlite3.Connection, db_path: str):
        self._conn = conn
        self._db_path = db_path

    def _get_repo(self, conn=None) -> MessageRepository:
        return MessageRepository(db_path=self._db_path, conn=conn)

    @staticmethod
    def extract_title_from_markdown(content: str) -> tuple[str, str]:
        """Extract title from markdown header (# or ##)."""
        if not content:
            return "", content

        lines = content.split('\n', 1)
        first_line = lines[0].strip()

        if first_line.startswith('#'):
            title = first_line.lstrip('#').strip()
            body = lines[1].lstrip('\n') if len(lines) > 1 else ""
            return title, body

        return "", content

    def send(
        self,
        sender: str,
        recipient: str,
        content: str,
        type: str = "suggestion",
        session_id: Optional[str] = None,
        conn=None,
    ) -> int:
        """Send a message. Returns message id."""
        if type not in ALLOWED_MESSAGE_TYPES:
            raise ValueError(f"Invalid message type '{type}'. Allowed: {sorted(ALLOWED_MESSAGE_TYPES)}")

        type_enum = LegacyAPIMapper.map_message_type_to_domain(type)
        title, body = self.extract_title_from_markdown(content)

        message = Message(
            sender=sender,
            recipient=recipient,
            content=body if title else content,
            title=title,
            type=type_enum,
            session_id=session_id,
        )

        repo = self._get_repo(conn)
        saved = repo.save(message)
        return saved.id

    def get_inbox(
        self,
        role: str,
        status: str = "unread",
        summary_only: bool = False,
        conn=None,
    ) -> list[dict]:
        """Get messages for a role filtered by status."""
        repo = self._get_repo(conn)
        messages = repo.find_by_recipient(recipient=role)

        status_enum = MessageStatus(status)
        filtered = [m for m in messages if m.status == status_enum]
        filtered.sort(key=lambda m: (m.created_at, m.id))

        result = [LegacyAPIMapper.message_to_dict(m) for m in filtered]

        if summary_only:
            for msg in result:
                msg.pop("content", None)

        return result

    def get_by_id(self, message_id: int, conn=None) -> Optional[dict]:
        """Get single message by ID."""
        repo = self._get_repo(conn)
        message = repo.get(message_id)
        if message is None:
            return None
        return LegacyAPIMapper.message_to_dict(message)

    def mark_read(self, message_id: int, conn=None) -> None:
        """Mark a message as read."""
        repo = self._get_repo(conn)
        message = repo.get(message_id)
        if not message:
            return

        try:
            message.mark_read()
        except Exception:
            return

        repo.save(message)

    def archive(self, message_id: int) -> None:
        """Archive a message (status='archived').

        Note: Direct SQL (not via repo) — trade-off: 1 UPDATE vs repo.get+entity+repo.save (3 ops).
        Acceptable per Architect review #326.
        """
        self._conn.execute(
            "UPDATE messages SET status = 'archived' WHERE id = ?",
            (message_id,),
        )

    def mark_all_read(self, role: str) -> int:
        """Mark all unread messages for a role as read. Returns count."""
        cursor = self._conn.execute(
            "UPDATE messages SET status = 'read', read_at = datetime('now') WHERE recipient = ? AND status = 'unread'",
            (role,),
        )
        return cursor.rowcount

    def get_messages(
        self,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> list[dict]:
        """Get messages with optional filters. Newest first."""
        conditions: list[str] = []
        params: list = []
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
            f"""SELECT id, sender, recipient, type, content, title, status, session_id, created_at, read_at, claimed_by
                FROM messages {where}
                ORDER BY created_at DESC, id DESC
                LIMIT ?""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
