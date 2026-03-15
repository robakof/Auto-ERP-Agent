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


# --- AgentBus: trace ---

class TestTrace:
    def test_add_and_get_trace(self, bus):
        session_id = "abc123"
        bus.add_trace_event(session_id, "Bash", "git status")
        result = bus.get_trace(session_id)
        assert len(result) == 1
        assert result[0]["tool_name"] == "Bash"
        assert result[0]["summary"] == "git status"

    def test_trace_filtered_by_session(self, bus):
        bus.add_trace_event("s1", "Bash", "cmd1")
        bus.add_trace_event("s2", "Edit", "file.py")
        assert len(bus.get_trace("s1")) == 1
        assert len(bus.get_trace("s2")) == 1

    def test_trace_ordering(self, bus):
        bus.add_trace_event("s1", "Read", "a")
        bus.add_trace_event("s1", "Write", "b")
        result = bus.get_trace("s1")
        assert result[0]["tool_name"] == "Read"
        assert result[1]["tool_name"] == "Write"


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
        cmd = [
            sys.executable, str(PROJECT_ROOT / "tools" / "session_init.py"),
            "--role", role,
            "--db", str(tmp_path / "test.db"),
        ]
        if extra_args:
            cmd += extra_args
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(PROJECT_ROOT))
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
