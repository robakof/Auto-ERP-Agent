"""Service for agent instances and task claiming (runner operations)."""

import sqlite3


class InstanceService:
    """Manage runner instances: register, heartbeat, busy/idle, claim/unclaim tasks."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def register(self, instance_id: str, role: str) -> None:
        """Register a runner instance. Upsert — safe to call on restart."""
        self._conn.execute(
            """INSERT INTO agent_instances (instance_id, role, status, started_at, last_seen_at)
               VALUES (?, ?, 'idle', datetime('now'), datetime('now'))
               ON CONFLICT(instance_id) DO UPDATE SET
                   status = 'idle', active_task_id = NULL,
                   started_at = datetime('now'), last_seen_at = datetime('now')""",
            (instance_id, role),
        )

    def heartbeat(self, instance_id: str) -> None:
        """Update last_seen_at for a running instance."""
        self._conn.execute(
            "UPDATE agent_instances SET last_seen_at = datetime('now') WHERE instance_id = ?",
            (instance_id,),
        )

    def set_busy(self, instance_id: str, task_id: int) -> None:
        """Mark instance as busy with an active task."""
        self._conn.execute(
            "UPDATE agent_instances SET status = 'busy', active_task_id = ? WHERE instance_id = ?",
            (task_id, instance_id),
        )

    def set_idle(self, instance_id: str) -> None:
        """Mark instance as idle and clear active task."""
        self._conn.execute(
            "UPDATE agent_instances SET status = 'idle', active_task_id = NULL WHERE instance_id = ?",
            (instance_id,),
        )

    def terminate(self, instance_id: str) -> None:
        """Mark instance as terminated."""
        self._conn.execute(
            "UPDATE agent_instances SET status = 'terminated' WHERE instance_id = ?",
            (instance_id,),
        )

    def get_free(self, role: str) -> list[dict]:
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

    def get_all(self) -> list[dict]:
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
               SET claimed_by = ?
               WHERE id = ? AND status = 'unread' AND claimed_by IS NULL""",
            (instance_id, msg_id),
        )
        return cursor.rowcount > 0

    def unclaim_task(self, msg_id: int) -> None:
        """Release a claimed task (e.g. after invocation failure)."""
        self._conn.execute(
            """UPDATE messages
               SET claimed_by = NULL
               WHERE id = ? AND claimed_by IS NOT NULL""",
            (msg_id,),
        )

    def get_pending_tasks(self, role: str, instance_id: str) -> list[dict]:
        """Return unread/unclaimed tasks for role OR specific instance_id."""
        rows = self._conn.execute(
            """SELECT id, sender, recipient, type, content, title, status, session_id,
                      created_at, read_at, claimed_by, reply_to_id
               FROM messages
               WHERE (recipient = ? OR recipient = ?)
                 AND type = 'task'
                 AND status = 'unread'
                 AND claimed_by IS NULL
               ORDER BY created_at ASC""",
            (role, instance_id),
        ).fetchall()
        return [dict(r) for r in rows]
