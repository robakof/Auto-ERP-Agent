"""AgentBus — message passing and state management for agent swarm via SQLite.

Provides structured communication between agent roles (erp_specialist, analyst,
developer, metodolog, human) and persistent state tracking (progress, reflections,
backlog items).
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ALLOWED_MESSAGE_TYPES = {"suggestion", "task", "info", "flag_human", "handoff"}

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
    title       TEXT,
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
    read_at     TEXT,
    claimed_by  TEXT,
    title       TEXT NOT NULL DEFAULT '',
    CHECK (type IN ('direct', 'suggestion', 'task', 'escalation', 'flag_human', 'info', 'handoff'))
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
    "ALTER TABLE session_log ADD COLUMN title TEXT",
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

    def _get_repository(self, repo_class):
        """Helper: create repository with transaction support.

        Args:
            repo_class: Repository class to instantiate (e.g., SuggestionRepository)

        Returns:
            Repository instance with shared connection if in transaction,
            or standalone connection otherwise.

        Example:
            repo = self._get_repository(SuggestionRepository)
            suggestion = repo.save(...)
        """
        conn = self._conn if self._in_transaction else None
        return repo_class(db_path=self._db_path, conn=conn)

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

    @staticmethod
    def _extract_title_from_markdown(content: str) -> tuple[str, str]:
        """
        Extract title from markdown header (# or ##).

        Args:
            content: Message content (potentially with markdown header)

        Returns:
            (title, body): Extracted title and content without header.
                          If no header found, returns ("", content).

        Example:
            >>> _extract_title_from_markdown("# Title\\n\\nBody text")
            ('Title', 'Body text')
            >>> _extract_title_from_markdown("## Title\\nContent")
            ('Title', 'Content')
            >>> _extract_title_from_markdown("No header")
            ('', 'No header')
        """
        if not content:
            return "", content

        lines = content.split('\n', 1)
        first_line = lines[0].strip()

        # Check for markdown header (# or ##)
        if first_line.startswith('#'):
            title = first_line.lstrip('#').strip()
            # Content without header (skip first line + potential empty lines)
            if len(lines) > 1:
                body = lines[1].lstrip('\n')
            else:
                body = ""
            return title, body

        # No header found
        return "", content

    def send_message(
        self,
        sender: str,
        recipient: str,
        content: str,
        type: str = "suggestion",
        session_id: str = None,
    ) -> int:
        """Send a message from one role to another. Returns message id."""
        from core.repositories.message_repo import MessageRepository
        from core.entities.messaging import Message
        from core.mappers.legacy_api import LegacyAPIMapper

        # Legacy API validation (backward compatible)
        if type not in ALLOWED_MESSAGE_TYPES:
            raise ValueError(f"Invalid message type '{type}'. Allowed: {sorted(ALLOWED_MESSAGE_TYPES)}")

        # Type mapping: legacy API → domain model (centralized)
        type_enum = LegacyAPIMapper.map_message_type_to_domain(type)

        # Extract title from markdown header (transparent for agent)
        title, body = self._extract_title_from_markdown(content)

        # Convert dict → entity
        message = Message(
            sender=sender,
            recipient=recipient,
            content=body if title else content,  # Use body if title extracted, otherwise original
            title=title,
            type=type_enum,
            session_id=session_id
        )

        # Save via repository (CRITICAL: pass connection for transaction support)
        repo = self._get_repository(MessageRepository)
        saved = repo.save(message)

        # Return ID (backward compatible)
        return saved.id

    def get_inbox(self, role: str, status: str = "unread") -> list[dict]:
        """Get messages for a role filtered by status. Ordered by created_at ASC."""
        from core.repositories.message_repo import MessageRepository
        from core.entities.messaging import MessageStatus

        # Query via repository (transaction support)
        repo = self._get_repository(MessageRepository)
        messages = repo.find_by_recipient(recipient=role)

        # Filter by status (str → enum)
        status_enum = MessageStatus(status)
        filtered = [m for m in messages if m.status == status_enum]

        # Sort by created_at ASC (backward compatible)
        filtered.sort(key=lambda m: m.created_at)

        # Convert entity → dict (backward compatible, centralized)
        from core.mappers.legacy_api import LegacyAPIMapper
        result = [LegacyAPIMapper.message_to_dict(m) for m in filtered]
        return result

    def mark_read(self, message_id: int) -> None:
        """Mark a message as read and set read_at timestamp."""
        from core.repositories.message_repo import MessageRepository

        # Repository query (transaction support)
        repo = self._get_repository(MessageRepository)

        # Get message
        message = repo.get(message_id)
        if not message:
            return  # Silent failure (backward compatible)

        # Call entity method (updates status + read_at)
        try:
            message.mark_read()
        except Exception:
            # If already read — graceful (backward compatible)
            return

        # Save updated message
        repo.save(message)

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
        repo = self._get_repository(SuggestionRepository)
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

        repo = self._get_repository(SuggestionRepository)

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

        # Convert entities to dicts (backward compatibility, centralized)
        from core.mappers.legacy_api import LegacyAPIMapper
        result = [LegacyAPIMapper.suggestion_to_dict(s) for s in suggestions]

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

        repo = self._get_repository(SuggestionRepository)

        # Load entity
        suggestion = repo.get(suggestion_id)
        if not suggestion:
            return  # Silently ignore if not found (backward compatible behavior)

        # Map old status names to new ones (backward compatibility, centralized)
        from core.mappers.legacy_api import LegacyAPIMapper
        status_enum = LegacyAPIMapper.map_suggestion_status_to_domain(status)

        # Update status using entity methods when possible
        if status_enum == SuggestionStatus.IMPLEMENTED:
            suggestion.implement(backlog_id=backlog_id)
        elif status_enum == SuggestionStatus.REJECTED:
            suggestion.reject()
        elif status_enum == SuggestionStatus.DEFERRED:
            suggestion.defer()
        else:
            # Direct status update for other cases (e.g. OPEN)
            suggestion.status = status_enum
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
        repo = self._get_repository(BacklogRepository)
        saved = repo.save(item)

        return saved.id

    def get_backlog(self, status: str = None, area: str = None) -> list[dict]:
        """Get backlog items. Newest first. Optional status/area filter.

        NOTE: Delegates to BacklogRepository (M3 adapter pattern).
        """
        from core.repositories.backlog_repo import BacklogRepository
        from core.entities.messaging import BacklogStatus, BacklogArea

        repo = self._get_repository(BacklogRepository)

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

        # Convert entities to dicts (backward compatibility, centralized)
        from core.mappers.legacy_api import LegacyAPIMapper
        result = [LegacyAPIMapper.backlog_to_dict(item) for item in items]

        return result

    def get_backlog_by_id(self, backlog_id: int) -> dict | None:
          """Get a single backlog item by ID.

          NOTE: Delegates to BacklogRepository (M3 adapter pattern).
          """
          from core.repositories.backlog_repo import BacklogRepository
          from core.mappers.legacy_api import LegacyAPIMapper

          repo = self._get_repository(BacklogRepository)
          item = repo.get(backlog_id)
          if item is None:
              return None
          return LegacyAPIMapper.backlog_to_dict(item)






    def update_backlog_status(self, backlog_id: int, status: str) -> None:
        """Update backlog item status and set updated_at.

        NOTE: Delegates to BacklogRepository (M3 adapter pattern).
        """
        from core.repositories.backlog_repo import BacklogRepository
        from core.entities.messaging import BacklogStatus

        repo = self._get_repository(BacklogRepository)

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

        repo = self._get_repository(BacklogRepository)

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
        title: str = None,
        session_id: str = None,
    ) -> int:
        """Add a session log entry. Returns log id."""
        cursor = self._conn.execute(
            """INSERT INTO session_log (role, content, title, session_id)
               VALUES (?, ?, ?, ?)""",
            (role, content, title, session_id),
        )
        self._auto_commit()
        return cursor.lastrowid

    def get_session_log(self, role: str, limit: int = 20) -> list[dict]:
        """Get session log entries for a role. Newest first."""
        rows = self._conn.execute(
            """SELECT id, role, content, title, session_id, created_at
               FROM session_log WHERE role = ?
               ORDER BY created_at DESC, id DESC
               LIMIT ?""",
            (role, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_session_logs(
        self,
        role: str = None,
        limit: int = 10,
        offset: int = 0,
        metadata_only: bool = False,
    ) -> list[dict]:
        """Get session log entries. Optionally filter by role. Newest first.

        Args:
            role: Filter by role (optional)
            limit: Max number of logs to return (default 10)
            offset: Number of logs to skip (default 0)
            metadata_only: If True, exclude content field (default False)

        Returns:
            List of session log dicts
        """
        # Select fields based on metadata_only flag
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

    def get_session_logs_init(self, role: str) -> dict:
        """Get session logs for session initialization (--init flag).

        Returns structured output for session_start workflow:
        - own_full: 3 latest logs (full content) for this role
        - own_metadata: 7 next logs (metadata only) for this role
        - cross_role: 20 latest logs (metadata only) for all roles (only for non-executor roles)

        Args:
            role: Role to get logs for

        Returns:
            Dict with keys: own_full, own_metadata, cross_role (or None)
        """
        # Executor roles (focused on their domain, noise from other roles not needed)
        executor_roles = ["erp_specialist", "analyst"]

        # 3 latest logs (full content)
        own_full = self.get_session_logs(role=role, limit=3, metadata_only=False)

        # 7 next logs (metadata only)
        own_metadata = self.get_session_logs(
            role=role, offset=3, limit=7, metadata_only=True
        )

        # 20 latest cross-role logs (metadata only) — only for non-executor roles
        cross_role = None
        if role not in executor_roles:
            cross_role = self.get_session_logs(limit=20, metadata_only=True)

        return {
            "own_full": own_full,
            "own_metadata": own_metadata,
            "cross_role": cross_role,
        }

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
