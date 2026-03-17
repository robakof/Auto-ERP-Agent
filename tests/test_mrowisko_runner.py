"""Tests for mrowisko_runner helpers (DB, renderer)."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

# Patch PROJECT_ROOT before import so DB default points to a temp path
import tools.mrowisko_runner as runner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    # Bootstrap messages table (subset of agent_bus schema)
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sender      TEXT NOT NULL,
            recipient   TEXT NOT NULL,
            type        TEXT NOT NULL DEFAULT 'suggestion',
            content     TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'unread',
            session_id  TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            read_at     TEXT
        );
    """)
    conn.commit()
    conn.close()
    runner.ensure_invocation_log(db_path)
    return db_path


def insert_message(db_path, sender, recipient, msg_type, content, status="unread"):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "INSERT INTO messages (sender, recipient, type, content, status) VALUES (?,?,?,?,?)",
        (sender, recipient, msg_type, content, status),
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id


# ---------------------------------------------------------------------------
# get_pending_tasks
# ---------------------------------------------------------------------------

def test_get_pending_tasks_returns_only_tasks(tmp_db):
    insert_message(tmp_db, "developer", "erp_specialist", "task", "Zbuduj widok X")
    insert_message(tmp_db, "developer", "erp_specialist", "suggestion", "Sugestia Y")
    insert_message(tmp_db, "analyst", "erp_specialist", "info", "Info Z")

    tasks = runner.get_pending_tasks(tmp_db, "erp_specialist")
    assert len(tasks) == 1
    assert tasks[0]["content"] == "Zbuduj widok X"
    assert tasks[0]["sender"] == "developer"


def test_get_pending_tasks_ignores_read(tmp_db):
    insert_message(tmp_db, "developer", "erp_specialist", "task", "Stare", status="read")
    insert_message(tmp_db, "developer", "erp_specialist", "task", "Nowe", status="unread")

    tasks = runner.get_pending_tasks(tmp_db, "erp_specialist")
    assert len(tasks) == 1
    assert tasks[0]["content"] == "Nowe"


def test_get_pending_tasks_empty_when_none(tmp_db):
    tasks = runner.get_pending_tasks(tmp_db, "erp_specialist")
    assert tasks == []


def test_get_pending_tasks_filters_by_role(tmp_db):
    insert_message(tmp_db, "developer", "erp_specialist", "task", "Dla ERP")
    insert_message(tmp_db, "developer", "analyst", "task", "Dla Analityka")

    tasks = runner.get_pending_tasks(tmp_db, "erp_specialist")
    assert len(tasks) == 1
    assert tasks[0]["content"] == "Dla ERP"


# ---------------------------------------------------------------------------
# mark_message_read
# ---------------------------------------------------------------------------

def test_mark_message_read(tmp_db):
    msg_id = insert_message(tmp_db, "developer", "erp_specialist", "task", "Zadanie")
    runner.mark_message_read(tmp_db, msg_id)

    conn = sqlite3.connect(tmp_db)
    row = conn.execute("SELECT status, read_at FROM messages WHERE id = ?", (msg_id,)).fetchone()
    conn.close()

    assert row[0] == "read"
    assert row[1] is not None


# ---------------------------------------------------------------------------
# log_invocation
# ---------------------------------------------------------------------------

def test_log_invocation_writes_record(tmp_db):
    runner.log_invocation(tmp_db, "sess-abc", "developer", "erp_specialist", 42, 5, 0.35, "done")

    conn = sqlite3.connect(tmp_db)
    row = conn.execute("SELECT * FROM invocation_log WHERE session_id = 'sess-abc'").fetchone()
    conn.close()

    assert row is not None
    # (id, session_id, parent_session_id, from_role, to_role, task_id, depth, turns, cost_usd, status, created_at)
    assert row[3] == "developer"   # from_role
    assert row[4] == "erp_specialist"  # to_role
    assert row[5] == 42            # task_id
    assert row[7] == 5             # turns
    assert abs(row[8] - 0.35) < 0.001  # cost_usd
    assert row[9] == "done"        # status


# ---------------------------------------------------------------------------
# render_event
# ---------------------------------------------------------------------------

def test_render_event_text(capsys):
    event = {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": "Hello world"}]},
    }
    result = runner.render_event(event)
    captured = capsys.readouterr()
    assert "Hello world" in captured.out
    assert result is None


def test_render_event_tool_use(capsys):
    event = {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]},
    }
    result = runner.render_event(event)
    captured = capsys.readouterr()
    assert "[tool: Bash]" in captured.out
    assert result is None


def test_render_event_result_returns_event():
    event = {"type": "result", "session_id": "xyz", "num_turns": 3, "cost_usd": 0.12}
    result = runner.render_event(event)
    assert result == event


def test_render_event_unknown_type_returns_none(capsys):
    event = {"type": "unknown_xyz"}
    result = runner.render_event(event)
    assert result is None


# ---------------------------------------------------------------------------
# build_cmd
# ---------------------------------------------------------------------------

def test_build_cmd_erp_specialist():
    cmd = runner.build_cmd("erp_specialist", "test prompt")
    assert "--permission-mode" in cmd
    idx = cmd.index("--permission-mode")
    assert cmd[idx + 1] == "acceptEdits"
    assert "--tools" in cmd
    idx = cmd.index("--tools")
    assert "Bash" in cmd[idx + 1]


def test_build_cmd_developer_default_permission():
    cmd = runner.build_cmd("developer", "test prompt")
    idx = cmd.index("--permission-mode")
    assert cmd[idx + 1] == "default"


def test_build_cmd_analyst_no_write():
    cmd = runner.build_cmd("analyst", "test prompt")
    idx = cmd.index("--tools")
    tools = cmd[idx + 1]
    assert "Write" not in tools
    assert "Edit" not in tools
