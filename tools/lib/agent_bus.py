"""AgentBus — message passing and state management for agent swarm via SQLite.

Provides structured communication between agent roles (erp_specialist, analyst,
developer, metodolog, human) and persistent state tracking (progress, reflections,
backlog items).
"""

import json
import sqlite3
from contextlib import contextmanager


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

CREATE TABLE IF NOT EXISTS workflow_execution (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id     TEXT NOT NULL,
    role            TEXT NOT NULL,
    session_id      TEXT,
    status          TEXT NOT NULL DEFAULT 'running',
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    CHECK (status IN ('running', 'completed', 'interrupted', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_workflow_execution_role_status ON workflow_execution(role, status);

CREATE TABLE IF NOT EXISTS step_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id    INTEGER NOT NULL,
    step_id         TEXT NOT NULL,
    step_index      INTEGER,
    status          TEXT NOT NULL,
    output_summary  TEXT,
    output_json     TEXT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (execution_id) REFERENCES workflow_execution(id),
    CHECK (status IN ('PASS', 'FAIL', 'BLOCKED', 'SKIPPED', 'IN_PROGRESS'))
);

CREATE INDEX IF NOT EXISTS idx_step_log_execution ON step_log(execution_id);

CREATE TABLE IF NOT EXISTS known_gaps (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    title                TEXT NOT NULL,
    description          TEXT NOT NULL,
    area                 TEXT NOT NULL,
    trigger_condition    TEXT NOT NULL,
    source_suggestion_id INTEGER REFERENCES suggestions(id),
    reported_by          TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'open',
    resolved_by_backlog_id INTEGER REFERENCES backlog(id),
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at          TEXT,
    CHECK (status IN ('open', 'resolved'))
);

CREATE INDEX IF NOT EXISTS idx_known_gaps_area_status ON known_gaps(area, status);

CREATE TABLE IF NOT EXISTS workflow_definitions (
    workflow_id   TEXT NOT NULL,
    version       TEXT NOT NULL,
    owner_role    TEXT NOT NULL,
    trigger_desc  TEXT,
    status        TEXT DEFAULT 'active' CHECK (status IN ('active', 'deprecated')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workflow_id, version)
);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id                INTEGER PRIMARY KEY,
    workflow_id       TEXT NOT NULL,
    workflow_version  TEXT NOT NULL,
    step_id           TEXT NOT NULL,
    phase             TEXT,
    sort_order        INTEGER NOT NULL,
    action            TEXT NOT NULL,
    tool              TEXT,
    command           TEXT,
    verification_type  TEXT,
    verification_value TEXT,
    on_failure_retry   INTEGER DEFAULT 0,
    on_failure_skip    INTEGER DEFAULT 0,
    on_failure_escalate INTEGER DEFAULT 1,
    on_failure_reason  TEXT,
    next_step_pass    TEXT,
    next_step_fail    TEXT,
    is_handoff        INTEGER DEFAULT 0,
    handoff_to        TEXT,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version),
    UNIQUE (workflow_id, workflow_version, step_id)
);

CREATE TABLE IF NOT EXISTS workflow_decisions (
    id               INTEGER PRIMARY KEY,
    workflow_id      TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    decision_id      TEXT NOT NULL,
    condition        TEXT NOT NULL,
    path_true        TEXT NOT NULL,
    path_false       TEXT NOT NULL,
    default_action   TEXT,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version),
    UNIQUE (workflow_id, workflow_version, decision_id)
);

CREATE TABLE IF NOT EXISTS workflow_exit_gates (
    id               INTEGER PRIMARY KEY,
    workflow_id      TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    phase            TEXT NOT NULL,
    item_id          TEXT NOT NULL,
    condition        TEXT NOT NULL,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version)
);
"""

_MIGRATE_SQL = [
    "ALTER TABLE messages ADD COLUMN claimed_by TEXT",
    "ALTER TABLE suggestions ADD COLUMN type TEXT NOT NULL DEFAULT 'observation'",
    "ALTER TABLE suggestions ADD COLUMN title TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE session_log ADD COLUMN title TEXT",
    # #147: Telemetry deduplication - cleanup duplicates before unique constraint
    """DELETE FROM tool_calls WHERE rowid NOT IN (
        SELECT MIN(rowid) FROM tool_calls GROUP BY session_id, tool_name, timestamp
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_tool_calls_dedup ON tool_calls(session_id, tool_name, timestamp)",
    # #146: Fix claimed status leak — migrate 'claimed' to proper claimed_by
    "UPDATE messages SET claimed_by = 'legacy-runner', status = 'unread' WHERE status = 'claimed'",
    # #187 M4: reply_to_id for thread correlation
    "ALTER TABLE messages ADD COLUMN reply_to_id INTEGER REFERENCES messages(id)",
    # #124: depends_on for backlog dependency tracking
    "ALTER TABLE backlog ADD COLUMN depends_on INTEGER REFERENCES backlog(id)",
    # Agent Launcher M1: live_agents table
    """CREATE TABLE IF NOT EXISTS live_agents (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id      TEXT UNIQUE NOT NULL,
        role            TEXT NOT NULL,
        task            TEXT,
        terminal_name   TEXT,
        window_id       TEXT,
        status          TEXT NOT NULL DEFAULT 'starting',
        spawned_by      TEXT,
        permission_mode TEXT NOT NULL DEFAULT 'default',
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),
        last_activity   TEXT,
        stopped_at      TEXT,
        transcript_path TEXT,
        CHECK (status IN ('starting', 'active', 'stopped'))
    )""",
    "CREATE INDEX IF NOT EXISTS idx_live_agents_status ON live_agents(status)",
    "CREATE INDEX IF NOT EXISTS idx_live_agents_role ON live_agents(role)",
    # Agent Launcher M1: invocations table
    """CREATE TABLE IF NOT EXISTS invocations (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        invoker_type    TEXT NOT NULL,
        invoker_id      TEXT NOT NULL,
        target_role     TEXT NOT NULL,
        task            TEXT NOT NULL,
        session_id      TEXT REFERENCES sessions(id),
        status          TEXT NOT NULL DEFAULT 'pending',
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),
        ended_at        TEXT,
        CHECK (invoker_type IN ('human', 'agent', 'orchestrator')),
        CHECK (status IN ('pending', 'approved', 'running', 'completed', 'failed', 'rejected'))
    )""",
    "CREATE INDEX IF NOT EXISTS idx_invocations_status ON invocations(status)",
    # Bezpiecznik #219: action type + target_session_id for stop/resume requests
    "ALTER TABLE invocations ADD COLUMN action TEXT NOT NULL DEFAULT 'spawn'",
    "ALTER TABLE invocations ADD COLUMN target_session_id TEXT",
    "CREATE INDEX IF NOT EXISTS idx_invocations_session ON invocations(session_id)",
    # live_agents: claude_uuid for reliable session_end matching
    "ALTER TABLE live_agents ADD COLUMN claude_uuid TEXT",
    # SQL Views: single interpretation layer (Dashboard = Dispatcher) — backlog #201
    "DROP VIEW IF EXISTS v_agent_status",
    """CREATE VIEW IF NOT EXISTS v_agent_status AS
    SELECT
        session_id,
        role,
        task,
        status AS raw_status,
        last_activity,
        claude_uuid,
        terminal_name,
        CASE
            WHEN status = 'starting' THEN 'starting'
            WHEN last_activity > datetime('now', '-5 minutes') THEN 'working'
            WHEN last_activity > datetime('now', '-30 minutes') THEN 'stale'
            ELSE 'dead'
        END AS display_status,
        created_at
    FROM live_agents
    WHERE status IN ('starting', 'active')""",
    """CREATE VIEW IF NOT EXISTS v_backlog_scored AS
    SELECT *,
        ROUND(
            (CASE value WHEN 'wysoka' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END +
             CASE effort WHEN 'mala' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END - 2
            ) * 9.0 / 4 + 1
        ) AS score
    FROM backlog""",
    """CREATE VIEW IF NOT EXISTS v_handoffs_blocked AS
    SELECT m.*
    FROM messages m
    LEFT JOIN live_agents la
        ON la.role = m.recipient AND la.status IN ('starting', 'active')
    WHERE m.type = 'handoff' AND m.status = 'unread' AND la.id IS NULL""",
    # uuid_bridge: atomic mapping claude_uuid ↔ session_id (replaces shared pending file)
    """CREATE TABLE IF NOT EXISTS uuid_bridge (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        claude_uuid TEXT NOT NULL,
        session_id  TEXT,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )""",
    # Identity Redesign: handled in _run_migrations() as conditional migration
]

# Conditional migration — only runs once (checks for spawn_token column)
_IDENTITY_REDESIGN_SQL = [
    "DROP TABLE IF EXISTS uuid_bridge",
    "DROP VIEW IF EXISTS v_agent_status",
    "DROP VIEW IF EXISTS v_handoffs_blocked",
    "DROP TABLE IF EXISTS live_agents",
    """CREATE TABLE live_agents (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        claude_uuid     TEXT UNIQUE,
        session_id      TEXT UNIQUE,
        role            TEXT,
        terminal_name   TEXT,
        task            TEXT,
        status          TEXT NOT NULL DEFAULT 'starting',
        spawned_by      TEXT,
        spawn_token     TEXT UNIQUE,
        last_activity   TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),
        stopped_at      TEXT,
        transcript_path TEXT,
        CHECK (status IN ('starting', 'active', 'stopped'))
    )""",
    "CREATE INDEX IF NOT EXISTS idx_live_agents_status ON live_agents(status)",
    "CREATE INDEX IF NOT EXISTS idx_live_agents_role ON live_agents(role)",
    """CREATE VIEW IF NOT EXISTS v_agent_status AS
    SELECT
        session_id,
        role,
        task,
        status AS raw_status,
        last_activity,
        claude_uuid,
        terminal_name,
        spawn_token,
        CASE
            WHEN status = 'starting' THEN 'starting'
            WHEN last_activity > datetime('now', '-5 minutes') THEN 'working'
            WHEN last_activity > datetime('now', '-30 minutes') THEN 'stale'
            ELSE 'dead'
        END AS display_status,
        created_at
    FROM live_agents
    WHERE status IN ('starting', 'active')""",
    """CREATE VIEW IF NOT EXISTS v_handoffs_blocked AS
    SELECT m.*
    FROM messages m
    LEFT JOIN live_agents la
        ON la.role = m.recipient AND la.status IN ('starting', 'active')
    WHERE m.type = 'handoff' AND m.status = 'unread' AND la.id IS NULL""",
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

        # Services (extracted from AgentBus — separation of concerns #149)
        from core.services.known_gaps_service import KnownGapsService
        from core.services.workflow_service import WorkflowService
        from core.services.telemetry_service import TelemetryService
        from core.services.suggestion_service import SuggestionService
        from core.services.backlog_service import BacklogService
        from core.services.session_service import SessionService
        from core.services.instance_service import InstanceService
        from core.services.message_service import MessageService
        self._known_gaps = KnownGapsService(self._conn)
        self._workflows = WorkflowService(self._conn)
        self._telemetry = TelemetryService(self._conn)
        self._suggestions = SuggestionService(self._conn, db_path)
        self._backlog = BacklogService(self._conn, db_path)
        self._sessions = SessionService(self._conn)
        self._instances = InstanceService(self._conn)
        self._messages = MessageService(self._conn, db_path)

    def _run_migrations(self) -> None:
        for stmt in _MIGRATE_SQL:
            try:
                self._conn.execute(stmt)
            except Exception:
                pass  # kolumna/tabela już istnieje

        # Identity Redesign: one-time migration (check for spawn_token column)
        try:
            self._conn.execute("SELECT spawn_token FROM live_agents LIMIT 0")
        except Exception:
            # spawn_token column missing → run identity redesign migration
            for stmt in _IDENTITY_REDESIGN_SQL:
                try:
                    self._conn.execute(stmt)
                except Exception:
                    pass
            self._conn.commit()

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

    def send_message(self, sender: str, recipient: str, content: str, type: str = "suggestion", session_id: str = None, reply_to_id: int = None) -> int:
        """Delegates to MessageService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._messages.send(sender, recipient, content, type, session_id, reply_to_id, txn_conn)

    def get_inbox(self, role: str, status: str = "unread", summary_only: bool = False) -> list[dict]:
        """Delegates to MessageService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._messages.get_inbox(role, status, summary_only, txn_conn)

    def get_message_by_id(self, message_id: int) -> dict | None:
        """Delegates to MessageService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._messages.get_by_id(message_id, txn_conn)

    def mark_read(self, message_id: int) -> None:
        """Delegates to MessageService."""
        txn_conn = self._conn if self._in_transaction else None
        self._messages.mark_read(message_id, txn_conn)

    def archive_message(self, message_id: int) -> None:
        """Delegates to MessageService."""
        self._messages.archive(message_id)
        self._auto_commit()

    def mark_unread(self, message_id: int) -> None:
        """Delegates to MessageService."""
        self._messages.mark_unread(message_id)
        self._auto_commit()

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
        """Delegates to SuggestionService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._suggestions.add(author, content, title, type, recipients, session_id, txn_conn)

    def get_suggestions(
        self,
        status: str = None,
        author: str = None,
        type: str = None,
    ) -> list[dict]:
        """Delegates to SuggestionService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._suggestions.get(status, author, type, txn_conn)

    def update_suggestion_status(
        self,
        suggestion_id: int,
        status: str,
        backlog_id: int = None,
    ) -> None:
        """Delegates to SuggestionService."""
        txn_conn = self._conn if self._in_transaction else None
        self._suggestions.update_status(suggestion_id, status, backlog_id, txn_conn)

    # --- Backlog ---

    def add_backlog_item(
        self,
        title: str,
        content: str,
        area: str = None,
        value: str = None,
        effort: str = None,
        source_id: int = None,
        depends_on: int = None,
    ) -> int:
        """Delegates to BacklogService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._backlog.add(title, content, area, value, effort, source_id, depends_on, txn_conn)

    def get_backlog(self, status: str = None, area: str = None) -> list[dict]:
        """Delegates to BacklogService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._backlog.get(status, area, txn_conn)

    def get_backlog_by_id(self, backlog_id: int) -> dict | None:
        """Delegates to BacklogService."""
        txn_conn = self._conn if self._in_transaction else None
        return self._backlog.get_by_id(backlog_id, txn_conn)

    def update_backlog_status(self, backlog_id: int, status: str) -> dict:
        """Delegates to BacklogService. Returns warning dict if dependency not done."""
        txn_conn = self._conn if self._in_transaction else None
        return self._backlog.update_status(backlog_id, status, txn_conn)

    def update_backlog_depends_on(self, backlog_id: int, depends_on: int | None) -> None:
        """Delegates to BacklogService."""
        txn_conn = self._conn if self._in_transaction else None
        self._backlog.update_depends_on(backlog_id, depends_on, txn_conn)

    def update_backlog_content(self, backlog_id: int, content: str) -> None:
        """Delegates to BacklogService."""
        txn_conn = self._conn if self._in_transaction else None
        self._backlog.update_content(backlog_id, content, txn_conn)

    # --- Session log ---

    def add_session_log(self, role: str, content: str, title: str = None, session_id: str = None) -> int:
        """Delegates to SessionService."""
        result = self._sessions.add_log(role, content, title, session_id)
        self._auto_commit()
        return result

    def get_session_log(self, role: str, limit: int = 20) -> list[dict]:
        """Delegates to SessionService."""
        return self._sessions.get_log(role, limit)

    def get_session_logs(self, role: str = None, limit: int = 10, offset: int = 0, metadata_only: bool = False) -> list[dict]:
        """Delegates to SessionService."""
        return self._sessions.get_logs(role, limit, offset, metadata_only)

    def get_session_logs_init(self, role: str) -> dict:
        """Delegates to SessionService."""
        return self._sessions.get_logs_init(role)

    def get_messages(self, sender: str = None, recipient: str = None, status: str = None, limit: int = 200) -> list[dict]:
        """Delegates to MessageService."""
        return self._messages.get_messages(sender, recipient, status, limit)

    # --- Workflow execution tracking ---

    def start_workflow_execution(
        self, workflow_id: str, role: str, session_id: str = None
    ) -> int:
        """Delegates to WorkflowService."""
        result = self._workflows.start(workflow_id, role, session_id)
        self._auto_commit()
        return result

    def log_step(
        self,
        execution_id: int,
        step_id: str,
        status: str,
        step_index: int = None,
        output_summary: str = None,
        output_json: dict = None,
    ) -> int:
        """Delegates to WorkflowService."""
        result = self._workflows.log_step(execution_id, step_id, status, step_index, output_summary, output_json)
        self._auto_commit()
        return result

    def end_workflow_execution(self, execution_id: int, status: str = "completed") -> dict:
        """Delegates to WorkflowService."""
        result = self._workflows.end(execution_id, status)
        if result["ok"]:
            self._auto_commit()
        return result

    def get_execution_status(self, execution_id: int) -> dict | None:
        """Delegates to WorkflowService."""
        return self._workflows.get_status(execution_id)

    def get_interrupted_executions(self, role: str = None) -> list[dict]:
        """Delegates to WorkflowService."""
        return self._workflows.get_interrupted(role)

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
        """Alias for mark_read (backward compat)."""
        self.mark_read(message_id)

    def mark_all_read(self, role: str) -> int:
        """Delegates to MessageService."""
        result = self._messages.mark_all_read(role)
        self._auto_commit()
        return result

    # --- Sessions ---

    def upsert_session(self, session_id: str, role: str = None, claude_session_id: str = None, transcript_path: str = None, ended_at: str = None) -> None:
        """Delegates to SessionService."""
        self._sessions.upsert(session_id, role, claude_session_id, transcript_path, ended_at)
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
        """Delegates to TelemetryService."""
        result = self._telemetry.add_tool_call(session_id, tool_name, input_summary, is_error, tokens_out, timestamp)
        self._auto_commit()
        return result

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
        """Delegates to TelemetryService."""
        result = self._telemetry.add_token_usage(
            session_id, turn_index, input_tokens, output_tokens,
            cache_read_tokens, cache_create_tokens, duration_ms, timestamp
        )
        self._auto_commit()
        return result

    def get_session_trace(self, session_id: str) -> dict:
        """Delegates to TelemetryService."""
        return self._telemetry.get_session_trace(session_id)

    # --- Conversation ---

    def add_conversation_entry(self, speaker: str, content: str, event_type: str, session_id: str = None, raw_payload: str = None) -> int:
        """Delegates to SessionService."""
        result = self._sessions.add_conversation_entry(speaker, content, event_type, session_id, raw_payload)
        self._auto_commit()
        return result

    def get_conversation(self, session_id: str) -> list[dict]:
        """Delegates to SessionService."""
        return self._sessions.get_conversation(session_id)

    def close(self):
        """Close the database connection."""
        self._conn.close()

    # --- Agent instances ---

    def register_instance(self, instance_id: str, role: str) -> None:
        """Delegates to InstanceService."""
        self._instances.register(instance_id, role)
        self._auto_commit()

    def heartbeat(self, instance_id: str) -> None:
        """Delegates to InstanceService."""
        self._instances.heartbeat(instance_id)
        self._auto_commit()

    def set_instance_busy(self, instance_id: str, task_id: int) -> None:
        """Delegates to InstanceService."""
        self._instances.set_busy(instance_id, task_id)
        self._auto_commit()

    def set_instance_idle(self, instance_id: str) -> None:
        """Delegates to InstanceService."""
        self._instances.set_idle(instance_id)
        self._auto_commit()

    def terminate_instance(self, instance_id: str) -> None:
        """Delegates to InstanceService."""
        self._instances.terminate(instance_id)
        self._auto_commit()

    def get_free_instances(self, role: str) -> list[dict]:
        """Delegates to InstanceService."""
        return self._instances.get_free(role)

    def get_all_instances(self) -> list[dict]:
        """Delegates to InstanceService."""
        return self._instances.get_all()

    def claim_task(self, msg_id: int, instance_id: str) -> bool:
        """Delegates to InstanceService."""
        result = self._instances.claim_task(msg_id, instance_id)
        self._auto_commit()
        return result

    def unclaim_task(self, msg_id: int) -> None:
        """Delegates to InstanceService."""
        self._instances.unclaim_task(msg_id)
        self._auto_commit()

    def get_pending_tasks(self, role: str, instance_id: str) -> list[dict]:
        """Delegates to InstanceService."""
        return self._instances.get_pending_tasks(role, instance_id)

    # --- Known Gaps ---

    def add_known_gap(
        self,
        title: str,
        description: str,
        area: str,
        trigger_condition: str,
        reported_by: str,
        source_suggestion_id: int = None,
    ) -> int:
        """Add a known gap. Delegates to KnownGapsService."""
        result = self._known_gaps.add(
            title, description, area, trigger_condition, reported_by, source_suggestion_id
        )
        self._auto_commit()
        return result

    def get_known_gaps(self, area: str = None, status: str = "open") -> list[dict]:
        """Get known gaps. Delegates to KnownGapsService."""
        return self._known_gaps.get(area, status)

    def resolve_known_gap(self, gap_id: int, backlog_id: int) -> dict:
        """Resolve a known gap. Delegates to KnownGapsService."""
        result = self._known_gaps.resolve(gap_id, backlog_id)
        if result["ok"]:
            self._auto_commit()
        return result

    # --- Workflow Definitions ---

    def get_workflow_definitions(self, status: str = None) -> list[dict]:
        """List all workflow definitions, optionally filtered by status."""
        if status:
            rows = self._conn.execute(
                "SELECT * FROM workflow_definitions WHERE status=? ORDER BY workflow_id",
                (status,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM workflow_definitions ORDER BY workflow_id",
            ).fetchall()
        return [dict(r) for r in rows]

    def get_workflow_detail(self, workflow_id: str, version: str = None) -> dict | None:
        """Get full workflow detail (definition + steps + decisions + exit_gates)."""
        if version:
            defn = self._conn.execute(
                "SELECT * FROM workflow_definitions WHERE workflow_id=? AND version=?",
                (workflow_id, version),
            ).fetchone()
        else:
            defn = self._conn.execute(
                "SELECT * FROM workflow_definitions WHERE workflow_id=? ORDER BY version DESC LIMIT 1",
                (workflow_id,),
            ).fetchone()
        if not defn:
            return None
        defn = dict(defn)
        ver = defn["version"]
        steps = [dict(r) for r in self._conn.execute(
            "SELECT * FROM workflow_steps WHERE workflow_id=? AND workflow_version=? ORDER BY sort_order",
            (workflow_id, ver),
        ).fetchall()]
        decisions = [dict(r) for r in self._conn.execute(
            "SELECT * FROM workflow_decisions WHERE workflow_id=? AND workflow_version=?",
            (workflow_id, ver),
        ).fetchall()]
        gates = [dict(r) for r in self._conn.execute(
            "SELECT * FROM workflow_exit_gates WHERE workflow_id=? AND workflow_version=?",
            (workflow_id, ver),
        ).fetchall()]
        return {
            "definition": defn,
            "steps": steps,
            "decisions": decisions,
            "exit_gates": gates,
        }
