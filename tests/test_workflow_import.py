"""Tests for workflow_import.py — parse strict .md → DB, upsert, render."""

import sqlite3
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.workflow_import import (
    assign_phases,
    import_all,
    import_file,
    parse_decisions,
    parse_exit_gates,
    parse_steps,
    parse_workflow,
    parse_yaml_header,
    upsert_workflow,
)
from tools.lib.renderers import render_workflow_list_md, render_workflow_md

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "workflow_strict_sample.md"
HANDOFF = FIXTURES / "workflow_strict_handoff.md"


@pytest.fixture
def db(tmp_path):
    """Create in-memory-like temp DB with schema."""
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
            path_false TEXT NOT NULL, default_action TEXT
        );
        CREATE TABLE workflow_exit_gates (
            id INTEGER PRIMARY KEY, workflow_id TEXT NOT NULL,
            workflow_version TEXT NOT NULL, phase TEXT NOT NULL,
            item_id TEXT NOT NULL, condition TEXT NOT NULL
        );
    """)
    conn.close()
    return db_path


# --- Parse tests ---

class TestParseYamlHeader:
    def test_valid_header(self):
        text = SAMPLE.read_text(encoding="utf-8")
        h = parse_yaml_header(text)
        assert h is not None
        assert h["workflow_id"] == "test_sample"
        assert h["version"] == "1.0"
        assert h["owner_role"] == "developer"

    def test_missing_header(self):
        assert parse_yaml_header("# No YAML here\nJust text.") is None

    def test_no_workflow_id(self):
        text = "---\nversion: 1.0\nowner_role: dev\n---\n"
        assert parse_yaml_header(text) is None


class TestParseSteps:
    def test_sample_steps(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        assert len(steps) == 5
        ids = [s["step_id"] for s in steps]
        assert "verify_git" in ids
        assert "send_review" in ids

    def test_step_fields(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        git_step = [s for s in steps if s["step_id"] == "verify_git"][0]
        assert git_step["tool"] == "Bash"
        assert git_step["command"] == "git status"
        assert git_step["on_failure_escalate"] == 1
        assert git_step["on_failure_retry"] == 0

    def test_next_step_parsing(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        git_step = [s for s in steps if s["step_id"] == "verify_git"][0]
        assert git_step["next_step_pass"] == "read_context"
        assert git_step["next_step_fail"] == "escalate"

    def test_handoff_detection(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        review = [s for s in steps if s["step_id"] == "send_review"][0]
        assert review["is_handoff"] == 1
        assert review["handoff_to"] == "architect"

    def test_non_handoff_step(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        impl = [s for s in steps if s["step_id"] == "implement"][0]
        assert impl["is_handoff"] == 0


class TestParseDecisions:
    def test_sample_decisions(self):
        text = SAMPLE.read_text(encoding="utf-8")
        decisions = parse_decisions(text)
        assert len(decisions) == 1
        assert decisions[0]["decision_id"] == "review_result"
        assert decisions[0]["path_true"] == "end"
        assert decisions[0]["path_false"] == "implement"

    def test_no_decisions(self):
        text = HANDOFF.read_text(encoding="utf-8")
        decisions = parse_decisions(text)
        assert len(decisions) == 0


class TestParseExitGates:
    def test_sample_gates(self):
        text = SAMPLE.read_text(encoding="utf-8")
        gates = parse_exit_gates(text)
        assert len(gates) == 5
        ids = [g["item_id"] for g in gates]
        assert "gate_verify_clean" in ids
        assert "gate_impl_tests" in ids

    def test_phase_assignment(self):
        text = SAMPLE.read_text(encoding="utf-8")
        gates = parse_exit_gates(text)
        verify_gates = [g for g in gates if g["phase"] == "Verify"]
        assert len(verify_gates) == 2


class TestAssignPhases:
    def test_phases_assigned(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        steps = assign_phases(steps, text)
        git_step = [s for s in steps if s["step_id"] == "verify_git"][0]
        assert git_step["phase"] == "Verify"
        impl_step = [s for s in steps if s["step_id"] == "implement"][0]
        assert impl_step["phase"] == "Implement"


# --- Full parse tests ---

class TestParseWorkflow:
    def test_sample(self):
        result = parse_workflow(SAMPLE)
        assert result["ok"]
        assert result["workflow_id"] == "test_sample"
        assert len(result["steps"]) == 5
        assert len(result["decisions"]) == 1
        assert len(result["exit_gates"]) == 5

    def test_handoff(self):
        result = parse_workflow(HANDOFF)
        assert result["ok"]
        assert result["workflow_id"] == "test_handoff"
        assert len(result["steps"]) == 2
        handoff_step = [s for s in result["steps"] if s["step_id"] == "send_approval"][0]
        assert handoff_step["is_handoff"] == 1
        assert handoff_step["handoff_to"] == "human"

    def test_human_readable_skipped(self, tmp_path):
        """Workflow without strict steps returns warning, not error."""
        md = tmp_path / "workflow_hr.md"
        md.write_text("---\nworkflow_id: hr_test\nversion: '1.0'\nowner_role: dev\n---\n\n## Steps\n1. Do something\n2. Do another\n", encoding="utf-8")
        result = parse_workflow(md)
        assert not result["ok"]
        assert "warning" in result


# --- DB upsert tests ---

class TestUpsert:
    def test_import_and_query(self, db):
        result = import_file(SAMPLE, db_path=db)
        assert result["ok"]
        assert result["steps"] == 5
        assert result["decisions"] == 1
        assert result["exit_gates"] == 5

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        defns = conn.execute("SELECT * FROM workflow_definitions").fetchall()
        assert len(defns) == 1
        assert defns[0]["workflow_id"] == "test_sample"
        steps = conn.execute("SELECT * FROM workflow_steps ORDER BY sort_order").fetchall()
        assert len(steps) == 5
        conn.close()

    def test_reimport_upsert(self, db):
        """Re-import replaces, doesn't duplicate."""
        import_file(SAMPLE, db_path=db)
        import_file(SAMPLE, db_path=db)

        conn = sqlite3.connect(db)
        defns = conn.execute("SELECT COUNT(*) FROM workflow_definitions").fetchone()[0]
        steps = conn.execute("SELECT COUNT(*) FROM workflow_steps").fetchone()[0]
        assert defns == 1
        assert steps == 5
        conn.close()

    def test_multiple_workflows(self, db):
        import_file(SAMPLE, db_path=db)
        import_file(HANDOFF, db_path=db)

        conn = sqlite3.connect(db)
        defns = conn.execute("SELECT COUNT(*) FROM workflow_definitions").fetchone()[0]
        assert defns == 2
        conn.close()

    def test_handoff_flags_in_db(self, db):
        import_file(HANDOFF, db_path=db)

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        steps = conn.execute(
            "SELECT step_id, is_handoff, handoff_to FROM workflow_steps WHERE workflow_id='test_handoff'"
        ).fetchall()
        handoff_step = [dict(s) for s in steps if s["step_id"] == "send_approval"][0]
        assert handoff_step["is_handoff"] == 1
        assert handoff_step["handoff_to"] == "human"
        conn.close()


# --- import_all tests ---

class TestImportAll:
    def test_all_includes_skipped(self, db):
        """Some workflows are human-readable and should be skipped."""
        result = import_all(workflows_dir="workflows", db_path=db)
        assert result["ok"]
        assert result["skipped"] > 0
        assert result["errors"] == 0

    def test_all_from_fixtures(self, db):
        result = import_all(workflows_dir=str(FIXTURES), db_path=db)
        # Fixtures don't match workflow_*.md pattern — they are workflow_strict_*.md
        # So we test with the fixture dir which has matching files
        assert result["ok"]


# --- Render tests ---

class TestRender:
    def test_render_workflow_detail(self, db, tmp_path):
        import_file(SAMPLE, db_path=db)

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        from tools.lib.agent_bus import AgentBus
        bus = AgentBus(db_path=db)
        detail = bus.get_workflow_detail("test_sample")
        assert detail is not None

        output = tmp_path / "rendered.md"
        render_workflow_md(detail, output)
        content = output.read_text(encoding="utf-8")
        assert "test_sample" in content
        assert "verify_git" in content
        assert "[HANDOFF]" in content
        assert "Exit Gate" in content
        assert "Decision Points" in content

    def test_render_workflow_list(self, db, tmp_path):
        import_file(SAMPLE, db_path=db)
        import_file(HANDOFF, db_path=db)

        from tools.lib.agent_bus import AgentBus
        bus = AgentBus(db_path=db)
        workflows = bus.get_workflow_definitions()
        assert len(workflows) == 2

        output = tmp_path / "list.md"
        render_workflow_list_md(workflows, output)
        content = output.read_text(encoding="utf-8")
        assert "test_sample" in content
        assert "test_handoff" in content


# --- Verification type parsing ---

class TestVerificationParsing:
    def test_file_exists(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        read_step = [s for s in steps if s["step_id"] == "read_context"][0]
        assert read_step["verification_type"] == "file_exists"
        assert "DEVELOPER.md" in read_step["verification_value"]

    def test_manual_verification(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        test_step = [s for s in steps if s["step_id"] == "run_tests"][0]
        assert test_step["verification_type"] == "manual"

    def test_send_review_manual(self):
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        review = [s for s in steps if s["step_id"] == "send_review"][0]
        assert review["verification_type"] == "manual"


# --- Review fixes (C1, W1, W2, S2, S3) ---

class TestReviewFixes:
    def test_c1_faza_regex_phases_assigned(self):
        """C1: Fixtures use ## Faza N: — phases must be non-empty."""
        text = SAMPLE.read_text(encoding="utf-8")
        steps = parse_steps(text)
        steps = assign_phases(steps, text)
        for s in steps:
            assert s["phase"] != "", f"Step {s['step_id']} has empty phase"

    def test_c1_faza_exit_gates_have_phase(self):
        """C1: Exit gates must have phase from ## Faza headers."""
        text = SAMPLE.read_text(encoding="utf-8")
        gates = parse_exit_gates(text)
        for g in gates:
            assert g["phase"] != "", f"Gate {g['item_id']} has empty phase"

    def test_w1_yaml_lists_parsed(self):
        """W1: YAML lists (participants, outputs) should not be silently dropped."""
        text = SAMPLE.read_text(encoding="utf-8")
        h = parse_yaml_header(text)
        assert isinstance(h.get("participants"), list)
        assert "developer" in h["participants"]
        assert "architect" in h["participants"]

    def test_w2_verification_word_boundary(self):
        """W2: 'file_exists_custom' should NOT match as file_exists type."""
        from tools.workflow_import import _parse_verification
        t, v = _parse_verification("file_exists_custom foo")
        assert t == "manual"  # should not match file_exists

        t2, v2 = _parse_verification("file_exists foo/bar.py")
        assert t2 == "file_exists"
        assert v2 == "foo/bar.py"

    def test_s2_exit_gate_hyphen_item_id(self, tmp_path):
        """S2: Exit gate item_id with hyphens should parse."""
        md = tmp_path / "workflow_hyphen.md"
        md.write_text(
            "---\nworkflow_id: hyphen_test\nversion: '1.0'\nowner_role: dev\n---\n\n"
            "## Faza 1: Test\n\n### Step 1: Do\n\n**step_id:** do_thing\n"
            "**action:** Do it\n**tool:** Bash\n**command:** `echo hi`\n"
            "**next_step:** end (if PASS), escalate (if FAIL)\n\n"
            "### Exit Gate\n\n- **gate-with-hyphens:** Check passed\n",
            encoding="utf-8",
        )
        result = parse_workflow(md)
        assert result["ok"]
        assert any(g["item_id"] == "gate-with-hyphens" for g in result["exit_gates"])
