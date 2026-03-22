"""AgentBus — message passing and state management for agent swarm via SQLite.

Provides structured communication between agent roles (erp_specialist, analyst,
developer, metodolog, human) and persistent state tracking (progress, reflections,
backlog items).
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ALLOWED_MESSAGE_TYPES = {"suggestion", "task", "info", "flag_human"}

HEARTBEAT_TTL_SECONDS = 60

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS suggestions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    author      TEXT NOT NULL,
    recipients  TEXT,
    title       TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL,
    type        TEXT NOT NULL DEFAULT 'observation',
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

CREATE TABLE IF NOT EXISTS agent_instances (
    instance_id    TEXT PRIMARY KEY,
    role           TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'idle',
    active_task_id INTEGER,
    started_at     TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agent_instances_role_status ON agent_instances(role, status);
"""

_MIGRATE_SQL = [
    "ALTER TABLE messages ADD COLUMN claimed_by TEXT",
    "ALTER TABLE suggestions ADD COLUMN type TEXT NOT NULL DEFAULT 'observation'",
    "ALTER TABLE suggestions ADD COLUMN title TEXT NOT NULL DEFAULT ''",
]


class AgentBus:
    """SQLite-backed message bus for agent communication and state persistence."""

    def __init__(self, db_path: str = "mrowisko.db"):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=3000")
        self._conn.executescript(_SCHEMA_SQL)
        self._run_migrations()
        self._conn.commit()
        self._in_transaction = False

    def _run_migrations(self) -> None:
        for stmt in _MIGRATE_SQL:
            try:
                self._conn.execute(stmt)
            except Exception:
                pass  # kolumna/tabela już istnieje

    def _auto_commit(self) -> None:
        """Commit only if NOT in explicit transaction context."""
        if not self._in_transaction:
            self._conn.commit()

    @contextmanager
    def transaction(self):
        """Explicit transaction context manager for atomic operations.

        Usage:
            with bus.transaction():
                bus.update_backlog_status(...)
                bus.update_backlog_content(...)
                # commit on exit, rollback on exception

        Raises:
            RuntimeError: If already in a transaction (nested not supported).
        """
        if self._in_transaction:
            raise RuntimeError("Nested transactions not supported")

        self._in_transaction = True
        try:
            yield
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            self._in_transaction = False

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
        self._auto_commit()
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
        self._auto_commit()

    def archive_message(self, message_id: int) -> None:
        """Archive a message (status='archived')."""
        self._conn.execute(
            "UPDATE messages SET status = 'archived' WHERE id = ?",
            (message_id,),
        )
        self._auto_commit()

    # --- State ---

    # --- Suggestions ---

    def add_suggestion(
        self,
        author: str,
        content: str,
        title: str = "",
        type: str = "observation",
        recipients: list[str] = None,
        session_id: str = None,
    ) -> int:
        """Add a suggestion from an agent. Returns suggestion id.

        NOTE: Delegates to SuggestionRepository (M3 adapter pattern).
        """
        from core.repositories.suggestion_repo import SuggestionRepository
        from core.entities.messaging import Suggestion, SuggestionType

        # Convert string type to enum (backward compatibility)
        try:
            type_enum = SuggestionType(type)
        except ValueError:
            type_enum = SuggestionType.OBSERVATION

        # Create entity (title auto-generated in __post_init__ if empty)
        suggestion = Suggestion(
            author=author,
            content=content,
            title=title,
            type=type_enum,
            recipients=recipients,
            session_id=session_id
        )

        # Save via repository (transaction-aware)
        conn = self._conn if self._in_transaction else None
        repo = SuggestionRepository(db_path=self._db_path, conn=conn)
        saved = repo.save(suggestion)

        return saved.id

    def get_suggestions(
        self,
        status: str = None,
        author: str = None,
        type: str = None,
    ) -> list[dict]:
        """Get suggestions. Newest first. Optional status, author, type filters.

        NOTE: Delegates to SuggestionRepository (M3 adapter pattern).
        """
        from core.repositories.suggestion_repo import SuggestionRepository
        from core.entities.messaging import SuggestionStatus, SuggestionType

        conn = self._conn if self._in_transaction else None
        repo = SuggestionRepository(db_path=self._db_path, conn=conn)

        # Query based on filters
        if status and author and type:
            # Multiple filters - use find_all and filter manually (TODO: optimize with composite query)
            suggestions = repo.find_all()
            suggestions = [s for s in suggestions if s.status.value == status and s.author == author and s.type.value == type]
        elif status:
            suggestions = repo.find_by_status(SuggestionStatus(status))
        elif author:
            suggestions = repo.find_by_author(author)
        elif type:
            suggestions = repo.find_by_type(SuggestionType(type))
        else:
            suggestions = repo.find_all()

        # Convert entities to dicts (backward compatibility)
        # Reverse status mapping: new → old API names
        status_reverse_map = {
            "implemented": "in_backlog",  # Map back to old API name
        }

        result = []
        for s in suggestions:
            # Apply reverse mapping for backward compatibility
            status_value = s.status.value
            api_status = status_reverse_map.get(status_value, status_value)

            d = {
                "id": s.id,
                "author": s.author,
                "recipients": s.recipients,
                "title": s.title,
                "content": s.content,
                "type": s.type.value,
                "status": api_status,  # Use mapped status for old API
                "backlog_id": s.backlog_id,
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat()
            }
            result.append(d)

        return result

    def update_suggestion_status(
        self,
        suggestion_id: int,
        status: str,
        backlog_id: int = None,
    ) -> None:
        """Update suggestion status and optionally link to backlog item.

        NOTE: Delegates to SuggestionRepository (M3 adapter pattern).
        """
        from core.repositories.suggestion_repo import SuggestionRepository
        from core.entities.messaging import SuggestionStatus

        conn = self._conn if self._in_transaction else None
        repo = SuggestionRepository(db_path=self._db_path, conn=conn)

        # Load entity
        suggestion = repo.get(suggestion_id)
        if not suggestion:
            return  # Silently ignore if not found (backward compatible behavior)

        # Map old status names to new ones (backward compatibility)
        status_map = {
            "in_backlog": "implemented",  # Old name for implemented + linked to backlog
            "open": "open",
            "implemented": "implemented",
            "rejected": "rejected",
            "deferred": "deferred"
        }
        normalized_status = status_map.get(status, status)

        # Update status using entity methods when possible
        if normalized_status == "implemented":
            suggestion.implement(backlog_id=backlog_id)
        elif normalized_status == "rejected":
            suggestion.reject()
        elif normalized_status == "deferred":
            suggestion.defer()
        else:
            # Direct status update for other cases
            try:
                suggestion.status = SuggestionStatus(normalized_status)
            except ValueError:
                # Unknown status - keep suggestion unchanged
                pass
            if backlog_id is not None:
                suggestion.backlog_id = backlog_id

        # Save
        repo.save(suggestion)

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
        """Add a backlog item. Returns backlog id.

        NOTE: Delegates to BacklogRepository (M3 adapter pattern).
        """
        from core.repositories.backlog_repo import BacklogRepository
        from core.entities.messaging import BacklogItem, BacklogArea, BacklogValue, BacklogEffort

        # Convert string values to enums (optional fields)
        area_enum = BacklogArea(area) if area else None
        value_enum = BacklogValue(value) if value else None
        effort_enum = BacklogEffort(effort) if effort else None

        # Create entity
        item = BacklogItem(
            title=title,
            content=content,
            area=area_enum,
            value=value_enum,
            effort=effort_enum,
            source_id=source_id
        )

        # Save via repository (transaction-aware)
        conn = self._conn if self._in_transaction else None
        repo = BacklogRepository(db_path=self._db_path, conn=conn)
        saved = repo.save(item)

        return saved.id

    def get_backlog(self, status: str = None, area: str = None) -> list[dict]:
        """Get backlog items. Newest first. Optional status/area filter.

        NOTE: Delegates to BacklogRepository (M3 adapter pattern).
        """
        from core.repositories.backlog_repo import BacklogRepository
        from core.entities.messaging import BacklogStatus, BacklogArea

        conn = self._conn if self._in_transaction else None
        repo = BacklogRepository(db_path=self._db_path, conn=conn)

        # Query based on filters
        if status and area:
            # Both filters - manual filter in-memory (TODO: optimize with composite query)
            items = repo.find_all()
            items = [item for item in items if item.status.value == status and item.area and item.area.value == area]
        elif status:
            items = repo.find_by_status(BacklogStatus(status))
        elif area:
            items = repo.find_by_area(BacklogArea(area))
        else:
            items = repo.find_all()

        # Convert entities to dicts (backward compatibility)
        result = []
        for item in items:
            d = {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "area": item.area.value if item.area else None,
                "value": item.value.value if item.value else None,
                "effort": item.effort.value if item.effort else None,
                "status": item.status.value,
                "source_id": item.source_id,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            }
            result.append(d)

        return result

    def update_backlog_status(self, backlog_id: int, status: str) -> None:
        """Update backlog item status and set updated_at.

        NOTE: Delegates to BacklogRepository (M3 adapter pattern).
        """
        from core.repositories.backlog_repo import BacklogRepository
        from core.entities.messaging import BacklogStatus

        conn = self._conn if self._in_transaction else None
        repo = BacklogRepository(db_path=self._db_path, conn=conn)

        # Load entity
        item = repo.get(backlog_id)
        if not item:
            return  # Silently ignore if not found (backward compatible)

        # Update status
        try:
            item.status = BacklogStatus(status)
        except ValueError:
            # Unknown status - keep item unchanged
            return

        # Save (updated_at auto-updated in repository)
        repo.save(item)

    def update_backlog_content(self, backlog_id: int, content: str) -> None:
        """Update backlog item content and set updated_at.

        NOTE: Delegates to BacklogRepository (M3 adapter pattern).
        """
        from core.repositories.backlog_repo import BacklogRepository

        conn = self._conn if self._in_transaction else None
        repo = BacklogRepository(db_path=self._db_path, conn=conn)

        # Load entity
        item = repo.get(backlog_id)
        if not item:
            return  # Silently ignore if not found (backward compatible)

        # Update content
        item.content = content

        # Save (updated_at auto-updated in repository)
        repo.save(item)

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
        self._auto_commit()
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
        self._auto_commit()

    def mark_all_read(self, role: str) -> int:
        """Mark all unread messages for a role as read. Returns count of updated rows."""
        cursor = self._conn.execute(
            "UPDATE messages SET status = 'read', read_at = datetime('now') WHERE recipient = ? AND status = 'unread'",
            (role,),
        )
        self._auto_commit()
        return cursor.rowcount

    # --- Trace ---

    # --- Sessions module ---

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
        self._auto_commit()

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
        self._auto_commit()
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
        self._auto_commit()
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
        self._auto_commit()
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

    # --- Agent instances ---

    def register_instance(self, instance_id: str, role: str) -> None:
        """Register a runner instance. Upsert — safe to call on restart."""
        self._conn.execute(
            """INSERT INTO agent_instances (instance_id, role, status, started_at, last_seen_at)
               VALUES (?, ?, 'idle', datetime('now'), datetime('now'))
               ON CONFLICT(instance_id) DO UPDATE SET
                   status = 'idle', active_task_id = NULL,
                   started_at = datetime('now'), last_seen_at = datetime('now')""",
            (instance_id, role),
        )
        self._auto_commit()

    def heartbeat(self, instance_id: str) -> None:
        """Update last_seen_at for a running instance."""
        self._conn.execute(
            "UPDATE agent_instances SET last_seen_at = datetime('now') WHERE instance_id = ?",
            (instance_id,),
        )
        self._auto_commit()

    def set_instance_busy(self, instance_id: str, task_id: int) -> None:
        """Mark instance as busy with an active task."""
        self._conn.execute(
            "UPDATE agent_instances SET status = 'busy', active_task_id = ? WHERE instance_id = ?",
            (task_id, instance_id),
        )
        self._auto_commit()

    def set_instance_idle(self, instance_id: str) -> None:
        """Mark instance as idle and clear active task."""
        self._conn.execute(
            "UPDATE agent_instances SET status = 'idle', active_task_id = NULL WHERE instance_id = ?",
            (instance_id,),
        )
        self._auto_commit()

    def terminate_instance(self, instance_id: str) -> None:
        """Mark instance as terminated."""
        self._conn.execute(
            "UPDATE agent_instances SET status = 'terminated' WHERE instance_id = ?",
            (instance_id,),
        )
        self._auto_commit()

    def get_free_instances(self, role: str) -> list[dict]:
        """Return idle instances for role with recent heartbeat (TTL=60s)."""
        rows = self._conn.execute(
            """SELECT instance_id, role, status, started_at, last_seen_at
               FROM agent_instances
               WHERE role = ? AND status = 'idle'
                 AND last_seen_at >= datetime('now', '-60 seconds')
               ORDER BY last_seen_at DESC""",
            (role,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_instances(self) -> list[dict]:
        """Return all non-terminated instances with recent heartbeat."""
        rows = self._conn.execute(
            """SELECT instance_id, role, status, active_task_id, started_at, last_seen_at
               FROM agent_instances
               WHERE status != 'terminated'
                 AND last_seen_at >= datetime('now', '-60 seconds')
               ORDER BY role, last_seen_at DESC""",
        ).fetchall()
        return [dict(r) for r in rows]

    def claim_task(self, msg_id: int, instance_id: str) -> bool:
        """Atomically claim a task. Returns True if claimed, False if already taken."""
        cursor = self._conn.execute(
            """UPDATE messages
               SET status = 'claimed', claimed_by = ?
               WHERE id = ? AND status = 'unread'""",
            (instance_id, msg_id),
        )
        self._auto_commit()
        return cursor.rowcount > 0

    def unclaim_task(self, msg_id: int) -> None:
        """Release a claimed task back to unread (e.g. after invocation failure)."""
        self._conn.execute(
            """UPDATE messages
               SET status = 'unread', claimed_by = NULL
               WHERE id = ? AND status = 'claimed'""",
            (msg_id,),
        )
        self._auto_commit()

    def get_pending_tasks(self, role: str, instance_id: str) -> list[dict]:
        """Return unread/unclaimed tasks for role OR specific instance_id."""
        rows = self._conn.execute(
            """SELECT id, sender, recipient, type, content, created_at
               FROM messages
               WHERE (recipient = ? OR recipient = ?)
                 AND type = 'task'
                 AND status = 'unread'
               ORDER BY created_at ASC""",
            (role, instance_id),
        ).fetchall()
        return [dict(r) for r in rows]
