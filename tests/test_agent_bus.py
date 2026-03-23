"""Unit tests for AgentBus — message passing and state management via SQLite."""

import json
import sqlite3
from pathlib import Path

import pytest

from tools.lib.agent_bus import AgentBus


@pytest.fixture
def bus(tmp_path):
    """Create AgentBus with temporary database."""
    db_path = str(tmp_path / "test_mrowisko.db")
    return AgentBus(db_path=db_path)


class TestDatabaseSetup:
    def test_db_created_if_not_exists(self, tmp_path):
        db_path = str(tmp_path / "new.db")
        assert not Path(db_path).exists()
        AgentBus(db_path=db_path)
        assert Path(db_path).exists()

    def test_wal_mode(self, bus):
        result = bus._conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"

    def test_tables_exist(self, bus):
        tables = bus._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "messages" in table_names
        assert "state" in table_names
        assert "suggestions" in table_names
        assert "backlog" in table_names
        assert "session_log" in table_names


class TestMessages:
    def test_send_and_receive_message(self, bus):
        msg_id = bus.send_message(
            sender="developer",
            recipient="erp_specialist",
            content="Popraw CASE w widoku",
        )
        assert isinstance(msg_id, int)
        inbox = bus.get_inbox("erp_specialist")
        assert len(inbox) == 1
        assert inbox[0]["content"] == "Popraw CASE w widoku"
        assert inbox[0]["sender"] == "developer"
        assert inbox[0]["id"] == msg_id

    def test_inbox_filters_by_role(self, bus):
        bus.send_message("dev", "erp_specialist", "msg for erp")
        bus.send_message("dev", "analyst", "msg for analyst")
        erp_inbox = bus.get_inbox("erp_specialist")
        analyst_inbox = bus.get_inbox("analyst")
        assert len(erp_inbox) == 1
        assert len(analyst_inbox) == 1
        assert erp_inbox[0]["content"] == "msg for erp"
        assert analyst_inbox[0]["content"] == "msg for analyst"

    def test_inbox_filters_by_status(self, bus):
        msg_id = bus.send_message("dev", "erp_specialist", "test msg")
        assert len(bus.get_inbox("erp_specialist", status="unread")) == 1
        assert len(bus.get_inbox("erp_specialist", status="read")) == 0
        bus.mark_read(msg_id)
        assert len(bus.get_inbox("erp_specialist", status="unread")) == 0
        assert len(bus.get_inbox("erp_specialist", status="read")) == 1

    def test_mark_read(self, bus):
        msg_id = bus.send_message("dev", "erp_specialist", "test")
        bus.mark_read(msg_id)
        inbox = bus.get_inbox("erp_specialist", status="read")
        assert len(inbox) == 1
        assert inbox[0]["status"] == "read"
        assert inbox[0]["read_at"] is not None

    def test_archive_message(self, bus):
        msg_id = bus.send_message("dev", "erp_specialist", "old msg")
        bus.archive_message(msg_id)
        assert len(bus.get_inbox("erp_specialist", status="unread")) == 0
        assert len(bus.get_inbox("erp_specialist", status="archived")) == 1

    def test_empty_inbox(self, bus):
        inbox = bus.get_inbox("erp_specialist")
        assert inbox == []

    def test_message_type_default(self, bus):
        bus.send_message("dev", "erp_specialist", "test")
        msg = bus.get_inbox("erp_specialist")[0]
        assert msg["type"] == "suggestion"

    def test_message_type_task(self, bus):
        bus.send_message("dev", "erp_specialist", "zbadaj bug", type="task")
        msg = bus.get_inbox("erp_specialist")[0]
        assert msg["type"] == "task"

    def test_message_type_info(self, bus):
        bus.send_message("dev", "erp_specialist", "fyi", type="info")
        msg = bus.get_inbox("erp_specialist")[0]
        assert msg["type"] == "info"

    def test_message_type_invalid_raises(self, bus):
        import pytest
        with pytest.raises(ValueError, match="Invalid message type"):
            bus.send_message("dev", "erp_specialist", "test", type="nieznany")

    def test_message_with_session_id(self, bus):
        bus.send_message("dev", "erp_specialist", "test", session_id="sess-123")
        msg = bus.get_inbox("erp_specialist")[0]
        assert msg["session_id"] == "sess-123"

    def test_message_ordering_asc(self, bus):
        bus.send_message("dev", "erp_specialist", "first")
        bus.send_message("dev", "erp_specialist", "second")
        inbox = bus.get_inbox("erp_specialist")
        assert inbox[0]["content"] == "first"
        assert inbox[1]["content"] == "second"


class TestState:
    def test_write_and_get_state(self, bus):
        state_id = bus.write_state(
            role="developer", type="progress", content="KM1 done"
        )
        assert isinstance(state_id, int)
        states = bus.get_state("developer")
        assert len(states) == 1
        assert states[0]["content"] == "KM1 done"

    def test_state_filters_by_type(self, bus):
        bus.write_state("developer", "progress", "step 1")
        bus.write_state("developer", "reflection", "lesson learned")
        bus.write_state("developer", "backlog_item", "fix X")
        progress = bus.get_state("developer", type="progress")
        reflections = bus.get_state("developer", type="reflection")
        backlog = bus.get_state("developer", type="backlog_item")
        assert len(progress) == 1
        assert len(reflections) == 1
        assert len(backlog) == 1

    def test_state_metadata_json(self, bus):
        meta = {"priority": "high", "area": "bot"}
        bus.write_state("developer", "backlog_item", "fix X", metadata=meta)
        states = bus.get_state("developer", type="backlog_item")
        assert states[0]["metadata"] == meta

    def test_get_state_limit(self, bus):
        for i in range(30):
            bus.write_state("developer", "progress", f"step {i}")
        assert len(bus.get_state("developer")) == 20  # default limit
        assert len(bus.get_state("developer", limit=5)) == 5

    def test_get_state_ordering_newest_first(self, bus):
        bus.write_state("developer", "progress", "old")
        bus.write_state("developer", "progress", "new")
        states = bus.get_state("developer", type="progress")
        assert states[0]["content"] == "new"
        assert states[1]["content"] == "old"

    def test_state_with_session_id(self, bus):
        bus.write_state("dev", "progress", "test", session_id="sess-456")
        states = bus.get_state("dev")
        assert states[0]["session_id"] == "sess-456"


class TestSuggestions:
    def test_add_suggestion_returns_id(self, bus):
        sid = bus.add_suggestion(author="erp_specialist", content="Dodaj indeks na KntNag")
        assert isinstance(sid, int)

    def test_get_suggestions_all(self, bus):
        bus.add_suggestion("erp_specialist", "sugestia 1")
        bus.add_suggestion("analyst", "sugestia 2")
        result = bus.get_suggestions()
        assert len(result) == 2

    def test_get_suggestions_filter_status(self, bus):
        bus.add_suggestion("erp_specialist", "otwarta")
        s2 = bus.add_suggestion("analyst", "w backlogu")
        bus.update_suggestion_status(s2, "in_backlog")
        open_s = bus.get_suggestions(status="open")
        assert len(open_s) == 1
        assert open_s[0]["content"] == "otwarta"

    def test_get_suggestions_filter_author(self, bus):
        bus.add_suggestion("erp_specialist", "moja sugestia")
        bus.add_suggestion("analyst", "inna sugestia")
        result = bus.get_suggestions(author="erp_specialist")
        assert len(result) == 1
        assert result[0]["author"] == "erp_specialist"

    def test_suggestion_default_status_open(self, bus):
        sid = bus.add_suggestion("erp_specialist", "test")
        result = bus.get_suggestions()
        assert result[0]["status"] == "open"

    def test_suggestion_with_recipients(self, bus):
        bus.add_suggestion("erp_specialist", "test", recipients=["developer", "metodolog"])
        result = bus.get_suggestions()
        assert result[0]["recipients"] == ["developer", "metodolog"]

    def test_suggestion_recipients_none_by_default(self, bus):
        bus.add_suggestion("erp_specialist", "test")
        result = bus.get_suggestions()
        assert result[0]["recipients"] is None

    def test_update_suggestion_status(self, bus):
        sid = bus.add_suggestion("erp_specialist", "test")
        bus.update_suggestion_status(sid, "implemented")
        result = bus.get_suggestions(status="implemented")
        assert len(result) == 1

    def test_update_suggestion_with_backlog_id(self, bus):
        sid = bus.add_suggestion("erp_specialist", "test")
        bid = bus.add_backlog_item(title="task", content="opis")
        bus.update_suggestion_status(sid, "in_backlog", backlog_id=bid)
        result = bus.get_suggestions()
        assert result[0]["backlog_id"] == bid

    def test_suggestion_ordering_newest_first(self, bus):
        bus.add_suggestion("erp_specialist", "starsza")
        bus.add_suggestion("analyst", "nowsza")
        result = bus.get_suggestions()
        assert result[0]["content"] == "nowsza"


class TestBacklog:
    def test_add_backlog_item_returns_id(self, bus):
        bid = bus.add_backlog_item(title="Fix X", content="Opis problemu")
        assert isinstance(bid, int)

    def test_get_backlog_all(self, bus):
        bus.add_backlog_item("Task 1", "opis 1")
        bus.add_backlog_item("Task 2", "opis 2")
        result = bus.get_backlog()
        assert len(result) == 2

    def test_backlog_default_status_planned(self, bus):
        bus.add_backlog_item("task", "opis")
        result = bus.get_backlog()
        assert result[0]["status"] == "planned"

    def test_get_backlog_filter_status(self, bus):
        bus.add_backlog_item("planned task", "opis")
        bid2 = bus.add_backlog_item("done task", "opis")
        bus.update_backlog_status(bid2, "done")
        planned = bus.get_backlog(status="planned")
        assert len(planned) == 1
        assert planned[0]["title"] == "planned task"

    def test_backlog_with_metadata(self, bus):
        bus.add_backlog_item("task", "opis", area="Bot", value="wysoka", effort="mala")
        result = bus.get_backlog()
        assert result[0]["area"] == "Bot"
        assert result[0]["value"] == "wysoka"
        assert result[0]["effort"] == "mala"

    def test_backlog_with_source_id(self, bus):
        sid = bus.add_suggestion("erp_specialist", "sugestia")
        bid = bus.add_backlog_item("task", "opis", source_id=sid)
        result = bus.get_backlog()
        assert result[0]["source_id"] == sid

    def test_update_backlog_status(self, bus):
        bid = bus.add_backlog_item("task", "opis")
        bus.update_backlog_status(bid, "in_progress")
        result = bus.get_backlog(status="in_progress")
        assert len(result) == 1

    def test_backlog_ordering_newest_first(self, bus):
        bus.add_backlog_item("stary", "opis")
        bus.add_backlog_item("nowy", "opis")
        result = bus.get_backlog()
        assert result[0]["title"] == "nowy"

    def test_get_backlog_filter_area(self, bus):
        bus.add_backlog_item("ERP task", "opis", area="ERP")
        bus.add_backlog_item("Bot task", "opis", area="Bot")
        erp = bus.get_backlog(area="ERP")
        assert len(erp) == 1
        assert erp[0]["title"] == "ERP task"

    def test_get_backlog_filter_area_and_status(self, bus):
        bid = bus.add_backlog_item("ERP done", "opis", area="ERP")
        bus.add_backlog_item("ERP planned", "opis", area="ERP")
        bus.update_backlog_status(bid, "done")
        result = bus.get_backlog(area="ERP", status="done")
        assert len(result) == 1
        assert result[0]["title"] == "ERP done"


class TestSessionLog:
    def test_add_session_log_returns_id(self, bus):
        lid = bus.add_session_log(role="developer", content="Sesja 2026-03-13")
        assert isinstance(lid, int)

    def test_get_session_log_by_role(self, bus):
        bus.add_session_log("developer", "wpis developera")
        bus.add_session_log("erp_specialist", "wpis erp")
        result = bus.get_session_log("developer")
        assert len(result) == 1
        assert result[0]["content"] == "wpis developera"

    def test_session_log_ordering_newest_first(self, bus):
        bus.add_session_log("developer", "stary")
        bus.add_session_log("developer", "nowy")
        result = bus.get_session_log("developer")
        assert result[0]["content"] == "nowy"

    def test_session_log_limit(self, bus):
        for i in range(25):
            bus.add_session_log("developer", f"wpis {i}")
        assert len(bus.get_session_log("developer")) == 20
        assert len(bus.get_session_log("developer", limit=5)) == 5

    def test_session_log_with_session_id(self, bus):
        bus.add_session_log("developer", "wpis", session_id="sess-abc")
        result = bus.get_session_log("developer")
        assert result[0]["session_id"] == "sess-abc"

    def test_add_session_log_with_title(self, bus):
        lid = bus.add_session_log("developer", "content", title="Test Title")
        result = bus.get_session_log("developer")
        assert result[0]["title"] == "Test Title"

    def test_session_log_title_optional(self, bus):
        bus.add_session_log("developer", "no title")
        result = bus.get_session_log("developer")
        assert result[0]["title"] is None

    def test_get_session_logs_without_role_filter(self, bus):
        bus.add_session_log("developer", "dev log")
        bus.add_session_log("erp_specialist", "erp log")
        result = bus.get_session_logs(limit=10)
        assert len(result) == 2
        roles = {r["role"] for r in result}
        assert "developer" in roles
        assert "erp_specialist" in roles

    def test_get_session_logs_with_role_filter(self, bus):
        bus.add_session_log("developer", "dev log")
        bus.add_session_log("erp_specialist", "erp log")
        result = bus.get_session_logs(role="developer", limit=10)
        assert len(result) == 1
        assert result[0]["role"] == "developer"

    def test_get_session_logs_includes_title(self, bus):
        bus.add_session_log("developer", "content", title="With Title")
        bus.add_session_log("developer", "content2")
        result = bus.get_session_logs(role="developer", limit=10)
        assert result[0]["title"] is None  # newest first, no title
        assert result[1]["title"] == "With Title"


class TestMarkAllRead:
    def test_marks_all_unread_for_role(self, bus):
        bus.send_message("developer", "analyst", "msg1")
        bus.send_message("developer", "analyst", "msg2")
        bus.send_message("developer", "erp_specialist", "other role")
        count = bus.mark_all_read("analyst")
        assert count == 2
        assert bus.get_inbox("analyst") == []

    def test_does_not_affect_other_roles(self, bus):
        bus.send_message("developer", "analyst", "msg analyst")
        bus.send_message("developer", "erp_specialist", "msg erp")
        bus.mark_all_read("analyst")
        assert len(bus.get_inbox("erp_specialist")) == 1

    def test_returns_zero_when_nothing_unread(self, bus):
        count = bus.mark_all_read("analyst")
        assert count == 0


class TestFlagForHuman:
    def test_flag_for_human(self, bus):
        flag_id = bus.flag_for_human(
            sender="erp_specialist",
            reason="Potrzebuję zatwierdzenia widoku",
            urgency="high",
        )
        assert isinstance(flag_id, int)
        inbox = bus.get_inbox("human")
        assert len(inbox) == 1
        assert inbox[0]["type"] == "flag_human"
        assert inbox[0]["sender"] == "erp_specialist"
        assert "Potrzebuję zatwierdzenia widoku" in inbox[0]["content"]

    def test_flag_includes_urgency(self, bus):
        bus.flag_for_human("analyst", "problem z danymi", urgency="high")
        msg = bus.get_inbox("human")[0]
        assert "high" in msg["content"].lower() or "high" in json.dumps(msg)


class TestSessionsTraceModule:
    def test_upsert_session_creates_record(self, bus):
        bus.upsert_session("abc123", role="developer")
        row = bus._conn.execute("SELECT id, role FROM sessions WHERE id='abc123'").fetchone()
        assert row is not None
        assert row["role"] == "developer"

    def test_upsert_session_update_claude_session_id(self, bus):
        bus.upsert_session("abc123", role="developer")
        bus.upsert_session("abc123", claude_session_id="uuid-1234")
        row = bus._conn.execute("SELECT claude_session_id, role FROM sessions WHERE id='abc123'").fetchone()
        assert row["claude_session_id"] == "uuid-1234"
        assert row["role"] == "developer"  # original value preserved

    def test_upsert_session_update_ended_at(self, bus):
        bus.upsert_session("abc123", role="erp_specialist")
        bus.upsert_session("abc123", ended_at="2026-03-15 13:00:00")
        row = bus._conn.execute("SELECT ended_at FROM sessions WHERE id='abc123'").fetchone()
        assert row["ended_at"] == "2026-03-15 13:00:00"

    def test_add_tool_call_returns_id(self, bus):
        bus.upsert_session("sess1", role="developer")
        tc_id = bus.add_tool_call("sess1", "Read", input_summary="CLAUDE.md")
        assert isinstance(tc_id, int)

    def test_add_tool_call_error_flag(self, bus):
        bus.upsert_session("sess1", role="developer")
        bus.add_tool_call("sess1", "Bash", input_summary="python ...", is_error=1)
        rows = bus._conn.execute("SELECT is_error FROM tool_calls WHERE session_id='sess1'").fetchall()
        assert rows[0]["is_error"] == 1

    def test_add_token_usage_returns_id(self, bus):
        bus.upsert_session("sess1", role="developer")
        tu_id = bus.add_token_usage("sess1", turn_index=0, input_tokens=1000, output_tokens=200)
        assert isinstance(tu_id, int)

    def test_get_session_trace_returns_all_data(self, bus):
        bus.upsert_session("sess1", role="developer", claude_session_id="uuid-xyz")
        bus.add_tool_call("sess1", "Read", input_summary="file.md")
        bus.add_tool_call("sess1", "Bash", input_summary="python ...", is_error=1)
        bus.add_token_usage("sess1", 0, input_tokens=500, output_tokens=100)
        bus.add_token_usage("sess1", 1, input_tokens=600, output_tokens=150, duration_ms=3000)

        trace = bus.get_session_trace("sess1")
        assert trace["session"]["role"] == "developer"
        assert trace["session"]["claude_session_id"] == "uuid-xyz"
        assert len(trace["tool_calls"]) == 2
        assert trace["tool_calls"][1]["is_error"] == 1
        assert len(trace["token_usage"]) == 2
        assert trace["token_usage"][1]["duration_ms"] == 3000

    def test_get_session_trace_nonexistent_returns_none(self, bus):
        assert bus.get_session_trace("nonexistent") is None

    def test_tables_include_new_trace_tables(self, bus):
        tables = bus._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = [t[0] for t in tables]
        assert "sessions" in names
        assert "tool_calls" in names
        assert "token_usage" in names


class TestTransactions:
    """Test transaction context manager for atomic operations."""

    def test_transaction_commit(self, bus):
        """Transaction commits all operations on success."""
        with bus.transaction():
            id1 = bus.add_backlog_item(title="Task 1", content="Content 1")
            id2 = bus.add_backlog_item(title="Task 2", content="Content 2")

        items = bus.get_backlog()
        assert len(items) == 2
        assert items[0]["title"] == "Task 2"  # newest first
        assert items[1]["title"] == "Task 1"

    def test_transaction_rollback(self, bus):
        """Transaction rolls back all operations on exception."""
        try:
            with bus.transaction():
                bus.add_backlog_item(title="Task 1", content="Content 1")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        items = bus.get_backlog()
        assert len(items) == 0  # rollback — nothing saved

    def test_transaction_nested_not_supported(self, bus):
        """Nested transactions raise RuntimeError."""
        with pytest.raises(RuntimeError, match="Nested transactions"):
            with bus.transaction():
                with bus.transaction():
                    pass

    def test_backward_compat_auto_commit(self, bus):
        """Without transaction context, operations auto-commit as before."""
        id1 = bus.add_backlog_item(title="Task 1", content="Content 1")
        items = bus.get_backlog()
        assert len(items) == 1  # auto-commit worked

    def test_transaction_multiple_operations(self, bus):
        """Transaction supports mixed operations across tables."""
        with bus.transaction():
            sid = bus.add_suggestion(author="developer", content="Suggestion 1")
            bid = bus.add_backlog_item(title="Task 1", content="From suggestion", source_id=sid)
            bus.update_suggestion_status(sid, "in_backlog", backlog_id=bid)

        suggestions = bus.get_suggestions()
        backlog = bus.get_backlog()
        assert len(suggestions) == 1
        assert len(backlog) == 1
        assert suggestions[0]["status"] == "in_backlog"
        assert suggestions[0]["backlog_id"] == bid
        assert backlog[0]["source_id"] == sid

    def test_transaction_rollback_mixed_operations(self, bus):
        """Failed transaction rolls back operations across multiple tables."""
        try:
            with bus.transaction():
                bus.add_suggestion(author="developer", content="Suggestion 1")
                bus.add_backlog_item(title="Task 1", content="Content 1")
                bus.send_message(sender="dev", recipient="analyst", content="Test msg")
                raise ValueError("Simulated error")
        except ValueError:
            pass

        assert len(bus.get_suggestions()) == 0
        assert len(bus.get_backlog()) == 0
        assert len(bus.get_inbox("analyst")) == 0
