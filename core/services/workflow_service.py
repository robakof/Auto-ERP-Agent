"""Service for workflow execution tracking."""

import json
import sqlite3
from typing import Optional


class WorkflowService:
    """Track workflow executions and steps."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def start(self, workflow_id: str, role: str, session_id: Optional[str] = None) -> int:
        """Start a new workflow execution. Returns execution_id."""
        cursor = self._conn.execute(
            """INSERT INTO workflow_execution (workflow_id, role, session_id)
               VALUES (?, ?, ?)""",
            (workflow_id, role, session_id),
        )
        return cursor.lastrowid

    def log_step(
        self,
        execution_id: int,
        step_id: str,
        status: str,
        step_index: Optional[int] = None,
        output_summary: Optional[str] = None,
        output_json: Optional[dict] = None,
    ) -> int:
        """Log a workflow step. Returns step_log.id."""
        json_str = json.dumps(output_json) if output_json else None
        cursor = self._conn.execute(
            """INSERT INTO step_log (execution_id, step_id, step_index, status, output_summary, output_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (execution_id, step_id, step_index, status, output_summary, json_str),
        )
        return cursor.lastrowid

    def end(self, execution_id: int, status: str = "completed") -> dict:
        """End a workflow execution. Idempotency guard: returns ok=False if already ended."""
        row = self._conn.execute(
            "SELECT status, ended_at FROM workflow_execution WHERE id = ?",
            (execution_id,),
        ).fetchone()

        if not row:
            return {"ok": False, "message": f"Execution {execution_id} not found"}

        if row["ended_at"] is not None:
            return {
                "ok": False,
                "message": f"Execution {execution_id} already ended with status '{row['status']}'"
            }

        self._conn.execute(
            """UPDATE workflow_execution
               SET status = ?, ended_at = datetime('now', 'localtime')
               WHERE id = ?""",
            (status, execution_id),
        )
        return {"ok": True, "message": f"Execution {execution_id} ended with status '{status}'"}

    def get_status(self, execution_id: int) -> Optional[dict]:
        """Get execution status with steps."""
        row = self._conn.execute(
            """SELECT id, workflow_id, role, session_id, status, started_at, ended_at
               FROM workflow_execution WHERE id = ?""",
            (execution_id,),
        ).fetchone()
        if not row:
            return None

        steps = self._conn.execute(
            """SELECT step_id, status, output_summary, timestamp
               FROM step_log WHERE execution_id = ?
               ORDER BY timestamp ASC, id ASC""",
            (execution_id,),
        ).fetchall()

        result = dict(row)
        result["steps"] = [dict(s) for s in steps]
        if steps:
            result["last_step"] = steps[-1]["step_id"]
            result["last_status"] = steps[-1]["status"]
        return result

    def get_interrupted(self, role: Optional[str] = None) -> list[dict]:
        """Get interrupted/running executions (no ended_at)."""
        if role:
            rows = self._conn.execute(
                """SELECT id, workflow_id, role, session_id, status, started_at
                   FROM workflow_execution
                   WHERE role = ? AND ended_at IS NULL
                   ORDER BY started_at DESC""",
                (role,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT id, workflow_id, role, session_id, status, started_at
                   FROM workflow_execution
                   WHERE ended_at IS NULL
                   ORDER BY started_at DESC""",
            ).fetchall()
        return [dict(r) for r in rows]
