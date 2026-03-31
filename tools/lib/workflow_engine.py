"""WorkflowEngine — state machine for workflow enforcement (ADR-002, Faza 2).

Reads workflow definitions from DB (Faza 1 tables), manages state transitions,
validates step ordering. No .md parsing at runtime — DB is the source of truth.

Usage:
    engine = WorkflowEngine(db_path)
    exec_id = engine.start("suggestions_processing", "developer", "session123")
    state = engine.get_current_state(exec_id)
    allowed = engine.can_transition(exec_id, "next_step_id")
    result = engine.complete_step(exec_id, "step_id")
    engine.end(exec_id, "completed")
"""

import sqlite3
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StepState:
    """Current position in workflow."""
    execution_id: int
    workflow_id: str
    step_id: Optional[str]  # None = not started yet, first step expected
    phase: str
    status: str  # PASS, FAIL, IN_PROGRESS, etc.
    sort_order: int
    allowed_transitions: list[str] = field(default_factory=list)
    is_handoff: bool = False
    handoff_to: str = ""
    is_exploratory: bool = False


@dataclass
class StepResult:
    """Result of complete_step attempt."""
    ok: bool
    step_id: str
    status: str  # PASS, BLOCKED, FAIL
    message: str = ""


class WorkflowEngine:
    """State machine engine reading workflow definitions from DB."""

    def __init__(self, db_path: str = "mrowisko.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=3000")

    def close(self):
        self._conn.close()

    # --- Core API ---

    def start(self, workflow_id: str, role: str, session_id: str = None) -> int:
        """Create execution, return execution_id. Validates workflow exists (unless exploratory)."""
        is_exploratory = workflow_id == "exploratory"
        if not is_exploratory:
            defn = self._get_definition(workflow_id)
            if not defn:
                raise ValueError(f"Workflow '{workflow_id}' not found in DB")

        cursor = self._conn.execute(
            "INSERT INTO workflow_execution (workflow_id, role, session_id) VALUES (?,?,?)",
            (workflow_id, role, session_id),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_current_state(self, execution_id: int) -> StepState:
        """Return current step state based on last step_log entry."""
        execution = self._get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        wf_id = execution["workflow_id"]
        is_exploratory = wf_id == "exploratory"

        if is_exploratory:
            last = self._get_last_step_log(execution_id)
            return StepState(
                execution_id=execution_id,
                workflow_id=wf_id,
                step_id=last["step_id"] if last else None,
                phase="",
                status=last["status"] if last else "NOT_STARTED",
                sort_order=0,
                allowed_transitions=[],
                is_exploratory=True,
            )

        steps = self._get_steps(wf_id)
        last = self._get_last_step_log(execution_id)

        if not last:
            # Not started — first step expected
            first = steps[0] if steps else None
            return StepState(
                execution_id=execution_id,
                workflow_id=wf_id,
                step_id=None,
                phase=first["phase"] if first else "",
                status="NOT_STARTED",
                sort_order=0,
                allowed_transitions=[first["step_id"]] if first else [],
            )

        last_step_id = last["step_id"]
        last_status = last["status"]
        step_def = self._find_step(steps, last_step_id)

        if last_status == "PASS" and step_def:
            # Determine next allowed step
            next_id = step_def["next_step_pass"]
            return StepState(
                execution_id=execution_id,
                workflow_id=wf_id,
                step_id=last_step_id,
                phase=step_def["phase"],
                status="PASS",
                sort_order=step_def["sort_order"],
                allowed_transitions=[next_id] if next_id and next_id != "end" else [],
                is_handoff=bool(step_def["is_handoff"]),
                handoff_to=step_def["handoff_to"] or "",
            )

        if last_status == "FAIL" and step_def:
            next_fail = step_def["next_step_fail"]
            transitions = [next_fail] if next_fail and next_fail != "escalate" else []
            # Also allow retry of current step
            transitions.append(last_step_id)
            return StepState(
                execution_id=execution_id,
                workflow_id=wf_id,
                step_id=last_step_id,
                phase=step_def["phase"],
                status="FAIL",
                sort_order=step_def["sort_order"],
                allowed_transitions=transitions,
            )

        # IN_PROGRESS, BLOCKED, SKIPPED — stay on current step
        return StepState(
            execution_id=execution_id,
            workflow_id=wf_id,
            step_id=last_step_id,
            phase=step_def["phase"] if step_def else "",
            status=last_status,
            sort_order=step_def["sort_order"] if step_def else 0,
            allowed_transitions=[last_step_id],
        )

    def can_transition(self, execution_id: int, target_step: str) -> bool:
        """Check if transition to target_step is legal from current state."""
        state = self.get_current_state(execution_id)
        if state.is_exploratory:
            return True
        if state.is_handoff:
            return False  # HANDOFF blocks all transitions
        return target_step in state.allowed_transitions

    def get_allowed_tools(self, execution_id: int) -> list[str]:
        """Return tools allowed in current step. Empty = all allowed."""
        state = self.get_current_state(execution_id)
        if state.is_exploratory:
            return []  # no restrictions

        if state.is_handoff:
            return ["agent_bus_cli"]  # only communication

        if not state.step_id:
            return []  # not started, no restrictions

        execution = self._get_execution(execution_id)
        steps = self._get_steps(execution["workflow_id"])

        # Find next step (where we should be transitioning to)
        if state.status == "PASS" and state.allowed_transitions:
            next_def = self._find_step(steps, state.allowed_transitions[0])
            if next_def and next_def.get("tool"):
                return [next_def["tool"]]

        # Current step tool
        current_def = self._find_step(steps, state.step_id)
        if current_def and current_def.get("tool"):
            return [current_def["tool"]]

        return []

    def complete_step(self, execution_id: int, step_id: str,
                      status: str = "PASS", output_summary: str = None) -> StepResult:
        """Attempt to complete a step. Returns StepResult with PASS or BLOCKED."""
        state = self.get_current_state(execution_id)

        # Exploratory: accept any step
        if state.is_exploratory:
            self._log_step(execution_id, step_id, status, output_summary)
            return StepResult(ok=True, step_id=step_id, status=status)

        # HANDOFF blocks completion of next steps
        if state.is_handoff and step_id != state.step_id:
            return StepResult(
                ok=False, step_id=step_id, status="BLOCKED",
                message=f"HANDOFF active at '{state.step_id}' → {state.handoff_to}. Cannot proceed.",
            )

        # Validate transition
        is_retry = step_id == state.step_id and state.status in ("FAIL", "IN_PROGRESS", "BLOCKED")
        is_valid = step_id in state.allowed_transitions or is_retry

        # First step case
        if state.step_id is None and state.allowed_transitions:
            is_valid = step_id == state.allowed_transitions[0]

        if not is_valid:
            return StepResult(
                ok=False, step_id=step_id, status="BLOCKED",
                message=f"Invalid transition: '{state.step_id}' → '{step_id}'. "
                        f"Allowed: {state.allowed_transitions}",
            )

        self._log_step(execution_id, step_id, status, output_summary)
        return StepResult(ok=True, step_id=step_id, status=status)

    def end(self, execution_id: int, status: str = "completed") -> dict:
        """End execution."""
        execution = self._get_execution(execution_id)
        if not execution:
            return {"ok": False, "message": f"Execution {execution_id} not found"}

        if execution["ended_at"] is not None:
            return {"ok": False, "message": f"Already ended with '{execution['status']}'"}

        self._conn.execute(
            "UPDATE workflow_execution SET status=?, ended_at=datetime('now') WHERE id=?",
            (status, execution_id),
        )
        self._conn.commit()
        return {"ok": True, "message": f"Execution {execution_id} ended with status '{status}'"}

    def get_logged_steps(self, execution_id: int) -> list[dict]:
        """Return all logged steps for an execution (useful for exploratory post-analysis)."""
        rows = self._conn.execute(
            "SELECT step_id, status, output_summary, timestamp FROM step_log "
            "WHERE execution_id=? ORDER BY timestamp ASC, id ASC",
            (execution_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Internal helpers ---

    def _get_definition(self, workflow_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM workflow_definitions WHERE workflow_id=? AND status='active' "
            "ORDER BY version DESC LIMIT 1",
            (workflow_id,),
        ).fetchone()
        return dict(row) if row else None

    def _get_execution(self, execution_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM workflow_execution WHERE id=?",
            (execution_id,),
        ).fetchone()
        return dict(row) if row else None

    def _get_steps(self, workflow_id: str) -> list[dict]:
        """Get steps for latest active version of workflow."""
        defn = self._get_definition(workflow_id)
        if not defn:
            return []
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM workflow_steps WHERE workflow_id=? AND workflow_version=? "
            "ORDER BY sort_order",
            (workflow_id, defn["version"]),
        ).fetchall()]

    def _find_step(self, steps: list[dict], step_id: str) -> Optional[dict]:
        for s in steps:
            if s["step_id"] == step_id:
                return s
        return None

    def _get_last_step_log(self, execution_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT step_id, status FROM step_log "
            "WHERE execution_id=? ORDER BY timestamp DESC, id DESC LIMIT 1",
            (execution_id,),
        ).fetchone()
        return dict(row) if row else None

    def _log_step(self, execution_id: int, step_id: str,
                  status: str, output_summary: str = None):
        self._conn.execute(
            "INSERT INTO step_log (execution_id, step_id, status, output_summary) VALUES (?,?,?,?)",
            (execution_id, step_id, status, output_summary),
        )
        self._conn.commit()
