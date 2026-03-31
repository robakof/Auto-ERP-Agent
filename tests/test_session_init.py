"""Tests for session_init.py and new DB methods (trace, conversation)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.lib.agent_bus import AgentBus

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def bus(tmp_path):
    return AgentBus(db_path=str(tmp_path / "test.db"))


# TestTrace removed — add_trace_event/get_trace never existed in AgentBus (dead tests)


# --- AgentBus: conversation ---

class TestConversation:
    def test_add_and_get_conversation(self, bus):
        bus.add_conversation_entry(
            speaker="human",
            content="zrób widok TraNag",
            event_type="user_prompt",
            session_id="s1",
        )
        result = bus.get_conversation("s1")
        assert len(result) == 1
        assert result[0]["speaker"] == "human"
        assert result[0]["content"] == "zrób widok TraNag"

    def test_conversation_without_session_id_stored(self, bus):
        entry_id = bus.add_conversation_entry(
            speaker="human",
            content="test",
            event_type="user_prompt",
        )
        assert isinstance(entry_id, int)

    def test_conversation_filtered_by_session(self, bus):
        bus.add_conversation_entry("human", "msg1", "user_prompt", session_id="s1")
        bus.add_conversation_entry("human", "msg2", "user_prompt", session_id="s2")
        assert len(bus.get_conversation("s1")) == 1
        assert len(bus.get_conversation("s2")) == 1

    def test_conversation_stores_raw_payload(self, bus):
        raw = '{"prompt": "test", "extra": 1}'
        bus.add_conversation_entry(
            speaker="human", content="test", event_type="user_prompt",
            session_id="s1", raw_payload=raw,
        )
        result = bus.get_conversation("s1")
        assert result[0]["content"] == "test"


# --- session_init.py ---

class TestSessionInit:
    def run_session_init(self, tmp_path, role, extra_args=None):
        import os
        cmd = [
            sys.executable, str(PROJECT_ROOT / "tools" / "session_init.py"),
            "--role", role,
            "--db", str(tmp_path / "test.db"),
        ]
        if extra_args:
            cmd += extra_args
        env = os.environ.copy()
        env.pop("MROWISKO_SPAWN_TOKEN", None)
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(PROJECT_ROOT), env=env)
        return json.loads(result.stdout)

    def test_session_init_returns_session_id(self, tmp_path):
        result = self.run_session_init(tmp_path, "developer")
        assert result["ok"] is True
        assert len(result["session_id"]) == 12
        assert result["role"] == "developer"
        assert result["resumed"] is False

    def test_session_init_writes_session_id_file(self, tmp_path, monkeypatch):
        # Run session_init and check tmp/session_id.txt is created
        cmd = [
            sys.executable, str(PROJECT_ROOT / "tools" / "session_init.py"),
            "--role", "developer",
            "--db", str(tmp_path / "test.db"),
        ]
        subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        sid_file = PROJECT_ROOT / "tmp" / "session_id.txt"
        assert sid_file.exists()
        assert len(sid_file.read_text().strip()) == 12

    def test_session_init_logs_to_session_log(self, tmp_path):
        self.run_session_init(tmp_path, "erp_specialist")
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        logs = bus.get_session_log(role="erp_specialist")
        assert len(logs) == 1
        assert logs[0]["content"] == "session started"

    def test_session_init_doc_path_correct(self, tmp_path):
        result = self.run_session_init(tmp_path, "erp_specialist")
        assert "ERP_SPECIALIST.md" in result["doc_path"]

    def test_each_call_generates_new_session_id(self, tmp_path):
        """Each call without matching claude_uuid generates a new session_id."""
        r1 = self.run_session_init(tmp_path, "developer")
        r2 = self.run_session_init(tmp_path, "developer")
        assert r1["session_id"] != r2["session_id"]

    def test_session_init_returns_doc_content(self, tmp_path):
        result = self.run_session_init(tmp_path, "developer")
        assert "doc_content" in result
        assert isinstance(result["doc_content"], str)
        assert len(result["doc_content"]) > 100

    def test_session_init_doc_content_matches_role(self, tmp_path):
        result = self.run_session_init(tmp_path, "developer")
        assert "Developer" in result["doc_content"]

    def test_session_init_doc_content_erp_specialist(self, tmp_path):
        result = self.run_session_init(tmp_path, "erp_specialist")
        assert "ERP" in result["doc_content"]


# --- session_init.py: context loading ---

class TestSessionInitContext:
    """Tests for configurable session_init with full context loading."""

    def run_session_init(self, tmp_path, role):
        import os
        cmd = [
            sys.executable, str(PROJECT_ROOT / "tools" / "session_init.py"),
            "--role", role,
            "--db", str(tmp_path / "test.db"),
        ]
        env = os.environ.copy()
        env.pop("MROWISKO_SPAWN_TOKEN", None)
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(PROJECT_ROOT), env=env)
        return json.loads(result.stdout)

    def test_session_init_returns_context(self, tmp_path):
        """Verify that session_init returns 'context' field."""
        result = self.run_session_init(tmp_path, "developer")
        assert result["ok"] is True
        assert "context" in result
        assert isinstance(result["context"], dict)

    def test_context_inbox_enabled(self, tmp_path):
        """Verify inbox is returned when enabled in config (developer)."""
        # Add message to inbox
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.send_message(sender="architect", recipient="developer", content="Test message", type="task")

        result = self.run_session_init(tmp_path, "developer")
        context = result["context"]

        assert "inbox" in context
        assert "messages" in context["inbox"]
        assert "count" in context["inbox"]
        assert context["inbox"]["count"] == 1
        assert context["inbox"]["messages"][0]["content"] == "Test message"

    def test_context_backlog_multiple_areas(self, tmp_path):
        """Verify backlog combines multiple areas (developer has Dev + Arch)."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.add_backlog_item(title="Dev task", content="...", area="Dev")
        bus.add_backlog_item(title="Arch task", content="...", area="Arch")
        bus.add_backlog_item(title="ERP task", content="...", area="ERP")

        result = self.run_session_init(tmp_path, "developer")
        context = result["context"]

        assert "backlog" in context
        assert context["backlog"]["count"] == 2  # Dev + Arch, not ERP
        titles = [item["title"] for item in context["backlog"]["items"]]
        assert "Dev task" in titles
        assert "Arch task" in titles
        assert "ERP task" not in titles

    def test_context_session_logs_own_full(self, tmp_path):
        """Verify session_logs returns own_full for role."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.add_session_log(role="developer", content="Log 1", title="Task 1")
        bus.add_session_log(role="developer", content="Log 2", title="Task 2")
        bus.add_session_log(role="architect", content="Arch log", title="Arch task")

        result = self.run_session_init(tmp_path, "developer")
        context = result["context"]

        assert "session_logs" in context
        assert "own_full" in context["session_logs"]

        # Should have 2 developer logs + 1 "session started" log = 3 total
        own_full = context["session_logs"]["own_full"]
        assert len(own_full) >= 2

        # Verify content is included (not metadata-only)
        assert "content" in own_full[0]

    def test_context_flags_human(self, tmp_path):
        """Verify flags_human returns unread messages to human."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.send_message(sender="developer", recipient="human", content="Flag for human", type="flag_human")

        result = self.run_session_init(tmp_path, "developer")
        context = result["context"]

        assert "flags_human" in context
        assert context["flags_human"]["count"] == 1
        assert context["flags_human"]["items"][0]["content"] == "Flag for human"

    def test_backlog_items_have_no_content(self, tmp_path):
        """Backlog items should contain only metadata, no content field."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.add_backlog_item(title="Task", content="Long description here", area="Dev")

        result = self.run_session_init(tmp_path, "developer")
        items = result["context"]["backlog"]["items"]

        assert len(items) == 1
        assert items[0]["title"] == "Task"
        assert "content" not in items[0]
        assert "id" in items[0]

    def test_inbox_long_content_truncated(self, tmp_path):
        """Inbox messages with content > 200 chars should be truncated."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        long_content = "A" * 500
        bus.send_message(sender="architect", recipient="developer", content=long_content, type="task")

        result = self.run_session_init(tmp_path, "developer")
        msg = result["context"]["inbox"]["messages"][0]

        assert len(msg["content"]) == 200
        assert msg["truncated"] is True

    def test_inbox_short_content_not_truncated(self, tmp_path):
        """Inbox messages with short content should not have truncated flag."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.send_message(sender="architect", recipient="developer", content="Short", type="task")

        result = self.run_session_init(tmp_path, "developer")
        msg = result["context"]["inbox"]["messages"][0]

        assert msg["content"] == "Short"
        assert "truncated" not in msg

    def test_session_logs_content_truncated(self, tmp_path):
        """Session logs with content > 300 chars should be truncated."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        long_log = "B" * 600
        bus.add_session_log(role="developer", content=long_log, title="Big log")

        result = self.run_session_init(tmp_path, "developer")
        own_full = result["context"]["session_logs"]["own_full"]

        # Find the log with truncated content (not the "session started" one)
        big = [l for l in own_full if l.get("truncated")]
        assert len(big) == 1
        assert len(big[0]["content"]) == 300


class TestResumeDetection:
    """Tests for auto resume detection via claude_uuid."""

    def run_session_init(self, tmp_path, role, claude_uuid=None):
        import os
        cmd = [
            sys.executable, str(PROJECT_ROOT / "tools" / "session_init.py"),
            "--role", role,
            "--db", str(tmp_path / "test.db"),
        ]
        env = os.environ.copy()
        env.pop("MROWISKO_SPAWN_TOKEN", None)
        if claude_uuid:
            env["CLAUDE_SESSION_ID"] = claude_uuid
        else:
            env.pop("CLAUDE_SESSION_ID", None)
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(PROJECT_ROOT), env=env)
        return json.loads(result.stdout)

    def test_new_session_not_resumed(self, tmp_path):
        """First call without pending claude_uuid → new session, resumed=False."""
        result = self.run_session_init(tmp_path, "developer", claude_uuid="fresh-uuid-no-match")
        assert result["ok"] is True
        assert result["resumed"] is False
        assert len(result["session_id"]) == 12

    def test_resume_reuses_session_id(self, tmp_path):
        """When claude_uuid exists in DB, session_init reuses session_id."""
        import sqlite3
        db_file = str(tmp_path / "test.db")
        bus = AgentBus(db_path=db_file)
        bus._conn.execute(
            """INSERT INTO live_agents (session_id, role, status, spawned_by, last_activity, claude_uuid)
               VALUES ('orig123', 'developer', 'stopped', 'manual', datetime('now'), 'test-uuid-abc')""",
        )
        bus._conn.commit()

        result = self.run_session_init(tmp_path, "developer", claude_uuid="test-uuid-abc")
        assert result["ok"] is True
        assert result["resumed"] is True
        assert result["session_id"] == "orig123"  # reused, not new

    def test_resume_reactivates_stopped_session(self, tmp_path):
        """Resume should set status back to 'active'."""
        import sqlite3
        db_file = str(tmp_path / "test.db")
        bus = AgentBus(db_path=db_file)
        bus._conn.execute(
            """INSERT INTO live_agents (session_id, role, status, spawned_by, last_activity, claude_uuid)
               VALUES ('stopped1', 'developer', 'stopped', 'manual', datetime('now'), 'uuid-stopped')""",
        )
        bus._conn.commit()

        self.run_session_init(tmp_path, "developer", claude_uuid="uuid-stopped")
        # Fresh connection to see subprocess changes
        conn = sqlite3.connect(db_file)
        row = conn.execute(
            "SELECT status FROM live_agents WHERE session_id='stopped1'"
        ).fetchone()
        conn.close()
        assert row[0] == "active"

    def test_different_uuid_creates_new_session(self, tmp_path):
        """Unknown claude_uuid → new session, not resume."""
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus._conn.execute(
            """INSERT INTO live_agents (session_id, role, status, spawned_by, last_activity, claude_uuid)
               VALUES ('old1', 'developer', 'stopped', 'manual', datetime('now'), 'uuid-old')""",
        )
        bus._conn.commit()

        result = self.run_session_init(tmp_path, "developer", claude_uuid="uuid-completely-new")
        assert result["ok"] is True
        assert result["resumed"] is False
        assert result["session_id"] != "old1"  # new session_id


# TestSessionDataContract removed — session_data.json eliminated per ADR (msg #664)
