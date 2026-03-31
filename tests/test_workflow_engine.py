"""Tests for WorkflowEngine — state machine for workflow enforcement (ADR-002, Faza 2)."""

import sqlite3
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.lib.workflow_engine import WorkflowEngine, StepState, StepResult
from tools.workflow_import import import_file

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "workflow_strict_sample.md"
HANDOFF = FIXTURES / "workflow_strict_handoff.md"


@pytest.fixture
def db(tmp_path):
    """Create temp DB with full schema."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE workflow_definitions (
            workflow_id TEXT NOT NULL, version TEXT NOT NULL,
            owner_role TEXT NOT NULL, trigger_desc TEXT,
            status TEXT DEFAULT 'active', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (workflow_id, version)
        );
        CREATE TABLE workflow_steps (
            id INTEGER PRIMARY KEY, workflow_id TEXT NOT NULL,
            workflow_version TEXT NOT NULL, step_id TEXT NOT NULL,
            phase TEXT, sort_order INTEGER NOT NULL, action TEXT NOT NULL,
            tool TEXT, command TEXT,
            verification_type TEXT, verification_value TEXT,
            on_failure_retry INTEGER DEFAULT 0, on_failure_skip INTEGER DEFAULT 0,
            on_failure_escalate INTEGER DEFAULT 1, on_failure_reason TEXT,
            next_step_pass TEXT, next_step_fail TEXT,
            is_handoff INTEGER DEFAULT 0, handoff_to TEXT,
            UNIQUE (workflow_id, workflow_version, step_id)
        );
        CREATE TABLE workflow_decisions (
            id INTEGER PRIMARY KEY, workflow_id TEXT NOT NULL,
            workflow_version TEXT NOT NULL, decision_id TEXT NOT NULL,
            condition TEXT NOT NULL, path_true TEXT NOT NULL,
            path_false TEXT NOT NULL, default_action TEXT,
            UNIQUE (workflow_id, workflow_version, decision_id)
        );
        CREATE TABLE workflow_exit_gates (
            id INTEGER PRIMARY KEY, workflow_id TEXT NOT NULL,
            workflow_version TEXT NOT NULL, phase TEXT NOT NULL,
            item_id TEXT NOT NULL, condition TEXT NOT NULL
        );
        CREATE TABLE workflow_execution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL, role TEXT NOT NULL,
            session_id TEXT, status TEXT NOT NULL DEFAULT 'running',
            started_at TEXT NOT NULL DEFAULT (datetime('now')), ended_at TEXT,
            CHECK (status IN ('running', 'completed', 'interrupted', 'failed'))
        );
        CREATE TABLE step_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id INTEGER NOT NULL, step_id TEXT NOT NULL,
            step_index INTEGER, status TEXT NOT NULL,
            output_summary TEXT, output_json TEXT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (execution_id) REFERENCES workflow_execution(id),
            CHECK (status IN ('PASS', 'FAIL', 'BLOCKED', 'SKIPPED', 'IN_PROGRESS'))
        );
    """)
    conn.close()
    return db_path


@pytest.fixture
def engine_with_sample(db):
    """Engine with test_sample workflow loaded."""
    import_file(SAMPLE, db_path=db)
    engine = WorkflowEngine(db_path=db)
    yield engine
    engine.close()


@pytest.fixture
def engine_with_handoff(db):
    """Engine with test_handoff workflow loaded."""
    import_file(HANDOFF, db_path=db)
    engine = WorkflowEngine(db_path=db)
    yield engine
    engine.close()


@pytest.fixture
def engine_empty(db):
    """Engine with no workflow definitions."""
    engine = WorkflowEngine(db_path=db)
    yield engine
    engine.close()


# --- 1. Happy path ---

class TestHappyPath:
    def test_start_returns_execution_id(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer", "sess1")
        assert isinstance(exec_id, int)
        assert exec_id > 0

    def test_full_workflow(self, engine_with_sample):
        """start → step1 PASS → step2 PASS → ... → end completed."""
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        # Initial state: not started, first step expected
        state = e.get_current_state(exec_id)
        assert state.step_id is None
        assert state.status == "NOT_STARTED"
        assert "verify_git" in state.allowed_transitions

        # Step 1: verify_git
        r = e.complete_step(exec_id, "verify_git", "PASS")
        assert r.ok
        state = e.get_current_state(exec_id)
        assert state.step_id == "verify_git"
        assert state.status == "PASS"
        assert "read_context" in state.allowed_transitions

        # Step 2: read_context
        r = e.complete_step(exec_id, "read_context", "PASS")
        assert r.ok
        state = e.get_current_state(exec_id)
        assert "implement" in state.allowed_transitions

        # Step 3: implement
        r = e.complete_step(exec_id, "implement", "PASS")
        assert r.ok

        # Step 4: run_tests
        r = e.complete_step(exec_id, "run_tests", "PASS")
        assert r.ok

        # Step 5: send_review
        r = e.complete_step(exec_id, "send_review", "PASS")
        assert r.ok

        # End
        result = e.end(exec_id, "completed")
        assert result["ok"]


# --- 2. Blocked: step FAIL → cannot proceed ---

class TestBlocked:
    def test_fail_blocks_next_step(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        # Complete first step with FAIL
        e.complete_step(exec_id, "verify_git", "FAIL")
        state = e.get_current_state(exec_id)
        assert state.status == "FAIL"
        # Cannot go to step2 directly — only retry or fail path
        assert "read_context" not in state.allowed_transitions

    def test_fail_allows_retry(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "FAIL")
        state = e.get_current_state(exec_id)
        # Can retry same step
        assert "verify_git" in state.allowed_transitions

    def test_fail_allows_fail_path(self, engine_with_sample):
        """run_tests FAIL → next_step_fail = implement."""
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        e.complete_step(exec_id, "read_context", "PASS")
        e.complete_step(exec_id, "implement", "PASS")
        e.complete_step(exec_id, "run_tests", "FAIL")

        state = e.get_current_state(exec_id)
        assert "implement" in state.allowed_transitions  # fail path
        assert "run_tests" in state.allowed_transitions  # retry


# --- 3. HANDOFF: blocks transition ---

class TestHandoff:
    def test_handoff_detected(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        e.complete_step(exec_id, "read_context", "PASS")
        e.complete_step(exec_id, "implement", "PASS")
        e.complete_step(exec_id, "run_tests", "PASS")
        e.complete_step(exec_id, "send_review", "PASS")

        state = e.get_current_state(exec_id)
        assert state.is_handoff
        assert state.handoff_to == "architect"

    def test_handoff_blocks_can_transition(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        e.complete_step(exec_id, "read_context", "PASS")
        e.complete_step(exec_id, "implement", "PASS")
        e.complete_step(exec_id, "run_tests", "PASS")
        e.complete_step(exec_id, "send_review", "PASS")

        assert not e.can_transition(exec_id, "end")

    def test_handoff_blocks_complete_step(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        e.complete_step(exec_id, "read_context", "PASS")
        e.complete_step(exec_id, "implement", "PASS")
        e.complete_step(exec_id, "run_tests", "PASS")
        e.complete_step(exec_id, "send_review", "PASS")

        r = e.complete_step(exec_id, "some_next_step", "PASS")
        assert not r.ok
        assert r.status == "BLOCKED"
        assert "HANDOFF" in r.message

    def test_handoff_only_agent_bus_allowed(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        e.complete_step(exec_id, "read_context", "PASS")
        e.complete_step(exec_id, "implement", "PASS")
        e.complete_step(exec_id, "run_tests", "PASS")
        e.complete_step(exec_id, "send_review", "PASS")

        tools = e.get_allowed_tools(exec_id)
        assert tools == ["agent_bus_cli"]

    def test_handoff_workflow_step(self, engine_with_handoff):
        """Dedicated handoff workflow: send_approval is handoff."""
        e = engine_with_handoff
        exec_id = e.start("test_handoff", "erp_specialist")

        e.complete_step(exec_id, "create_draft", "PASS")
        e.complete_step(exec_id, "send_approval", "PASS")

        state = e.get_current_state(exec_id)
        assert state.is_handoff
        assert state.handoff_to == "human"


# --- 4. Resume: interrupted → get_current_state ---

class TestResume:
    def test_resume_returns_last_pass(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        e.complete_step(exec_id, "read_context", "PASS")
        # "interrupt" — just get state later
        state = e.get_current_state(exec_id)
        assert state.step_id == "read_context"
        assert state.status == "PASS"
        assert "implement" in state.allowed_transitions


# --- 5. Invalid transition: skip step ---

class TestInvalidTransition:
    def test_skip_step_rejected(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        # Try to skip to step3 without completing step1
        r = e.complete_step(exec_id, "implement", "PASS")
        assert not r.ok
        assert r.status == "BLOCKED"
        assert "Invalid transition" in r.message

    def test_skip_middle_step(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        # Try to skip read_context → implement
        r = e.complete_step(exec_id, "implement", "PASS")
        assert not r.ok
        assert r.status == "BLOCKED"

    def test_can_transition_false_for_invalid(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        assert not e.can_transition(exec_id, "implement")
        assert e.can_transition(exec_id, "verify_git")


# --- 6. Exploratory workflow ---

class TestExploratory:
    def test_start_exploratory(self, engine_empty):
        e = engine_empty
        exec_id = e.start("exploratory", "developer")
        assert exec_id > 0

    def test_exploratory_any_step(self, engine_empty):
        e = engine_empty
        exec_id = e.start("exploratory", "developer")

        r1 = e.complete_step(exec_id, "research_api", "PASS")
        assert r1.ok
        r2 = e.complete_step(exec_id, "write_prototype", "PASS")
        assert r2.ok
        r3 = e.complete_step(exec_id, "test_prototype", "FAIL")
        assert r3.ok  # exploratory accepts any status

    def test_exploratory_can_transition_always_true(self, engine_empty):
        e = engine_empty
        exec_id = e.start("exploratory", "developer")
        assert e.can_transition(exec_id, "anything")

    def test_exploratory_no_tool_restrictions(self, engine_empty):
        e = engine_empty
        exec_id = e.start("exploratory", "developer")
        assert e.get_allowed_tools(exec_id) == []

    def test_exploratory_logged_steps(self, engine_empty):
        e = engine_empty
        exec_id = e.start("exploratory", "developer")

        e.complete_step(exec_id, "step_a", "PASS")
        e.complete_step(exec_id, "step_b", "PASS")
        e.complete_step(exec_id, "step_c", "FAIL")

        logged = e.get_logged_steps(exec_id)
        assert len(logged) == 3
        assert [s["step_id"] for s in logged] == ["step_a", "step_b", "step_c"]

    def test_exploratory_end(self, engine_empty):
        e = engine_empty
        exec_id = e.start("exploratory", "developer")
        e.complete_step(exec_id, "step_a", "PASS")
        result = e.end(exec_id, "completed")
        assert result["ok"]

    def test_exploratory_state_is_marked(self, engine_empty):
        e = engine_empty
        exec_id = e.start("exploratory", "developer")
        state = e.get_current_state(exec_id)
        assert state.is_exploratory


# --- Edge cases ---

class TestEdgeCases:
    def test_start_unknown_workflow_raises(self, engine_empty):
        with pytest.raises(ValueError, match="not found"):
            engine_empty.start("nonexistent", "developer")

    def test_end_idempotent(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")
        e.end(exec_id, "completed")
        result = e.end(exec_id, "completed")
        assert not result["ok"]
        assert "Already ended" in result["message"]

    def test_get_allowed_tools_for_step(self, engine_with_sample):
        e = engine_with_sample
        exec_id = e.start("test_sample", "developer")

        e.complete_step(exec_id, "verify_git", "PASS")
        # Next step is read_context, tool=Read
        tools = e.get_allowed_tools(exec_id)
        assert "Read" in tools
