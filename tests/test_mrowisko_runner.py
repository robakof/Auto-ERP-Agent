"""Tests for mrowisko_runner and AgentBus instance routing."""

import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import tools.mrowisko_runner as runner
from tools.lib.agent_bus import AgentBus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bus(tmp_path):
    db_path = str(tmp_path / "test.db")
    return AgentBus(db_path=db_path)


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    AgentBus(db_path=db_path)  # init schema
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
# AgentBus.get_pending_tasks
# ---------------------------------------------------------------------------

def test_get_pending_tasks_returns_only_tasks(bus):
    bus.send_message("developer", "erp_specialist", "Zbuduj widok X", type="task")
    bus.send_message("developer", "erp_specialist", "Sugestia Y", type="suggestion")

    tasks = bus.get_pending_tasks("erp_specialist", "erp_specialist:abc123")
    assert len(tasks) == 1
    assert tasks[0]["content"] == "Zbuduj widok X"


def test_get_pending_tasks_ignores_claimed(tmp_db):
    msg_id = insert_message(tmp_db, "developer", "erp_specialist", "task", "Stare")
    conn = sqlite3.connect(tmp_db)
    conn.execute("UPDATE messages SET claimed_by = 'runner-123' WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()
    insert_message(tmp_db, "developer", "erp_specialist", "task", "Nowe")

    b = AgentBus(db_path=tmp_db)
    tasks = b.get_pending_tasks("erp_specialist", "erp_specialist:xyz")
    assert len(tasks) == 1
    assert tasks[0]["content"] == "Nowe"


def test_get_pending_tasks_by_instance_id(bus):
    bus.send_message("analyst", "erp_specialist:abc", "Dla konkretnej instancji", type="task")
    bus.send_message("analyst", "erp_specialist", "Dla roli", type="task")

    tasks = bus.get_pending_tasks("erp_specialist", "erp_specialist:abc")
    assert len(tasks) == 2

    tasks_other = bus.get_pending_tasks("erp_specialist", "erp_specialist:xyz")
    assert len(tasks_other) == 1
    assert tasks_other[0]["content"] == "Dla roli"


def test_get_pending_tasks_filters_by_role(bus):
    bus.send_message("developer", "erp_specialist", "Dla ERP", type="task")
    bus.send_message("developer", "analyst", "Dla Analityka", type="task")

    tasks = bus.get_pending_tasks("erp_specialist", "erp_specialist:abc")
    assert len(tasks) == 1
    assert tasks[0]["content"] == "Dla ERP"


# ---------------------------------------------------------------------------
# AgentBus.claim_task
# ---------------------------------------------------------------------------

def test_claim_task_returns_true_on_success(bus):
    msg_id = bus.send_message("developer", "erp_specialist", "Zadanie", type="task")
    assert bus.claim_task(msg_id, "erp_specialist:abc") is True


def test_claim_task_returns_false_if_already_claimed(bus):
    msg_id = bus.send_message("developer", "erp_specialist", "Zadanie", type="task")
    bus.claim_task(msg_id, "erp_specialist:abc")
    assert bus.claim_task(msg_id, "erp_specialist:xyz") is False


def test_claim_task_sets_claimed_by(tmp_db):
    msg_id = insert_message(tmp_db, "developer", "erp_specialist", "task", "Zadanie")
    b = AgentBus(db_path=tmp_db)
    b.claim_task(msg_id, "erp_specialist:abc")

    conn = sqlite3.connect(tmp_db)
    row = conn.execute("SELECT status, claimed_by FROM messages WHERE id = ?", (msg_id,)).fetchone()
    conn.close()
    assert row[0] == "unread"  # status unchanged — claim uses claimed_by only
    assert row[1] == "erp_specialist:abc"


# ---------------------------------------------------------------------------
# AgentBus.unclaim_task
# ---------------------------------------------------------------------------

def test_unclaim_task_restores_unread(bus):
    msg_id = bus.send_message("developer", "erp_specialist", "Zadanie", type="task")
    bus.claim_task(msg_id, "erp_specialist:abc")
    bus.unclaim_task(msg_id)
    tasks = bus.get_pending_tasks("erp_specialist", "erp_specialist:xyz")
    assert any(t["id"] == msg_id for t in tasks)


def test_unclaim_task_clears_claimed_by(tmp_db):
    msg_id = insert_message(tmp_db, "developer", "erp_specialist", "task", "Zadanie")
    b = AgentBus(db_path=tmp_db)
    b.claim_task(msg_id, "erp_specialist:abc")
    b.unclaim_task(msg_id)

    conn = sqlite3.connect(tmp_db)
    row = conn.execute("SELECT status, claimed_by FROM messages WHERE id = ?", (msg_id,)).fetchone()
    conn.close()
    assert row[0] == "unread"
    assert row[1] is None


# ---------------------------------------------------------------------------
# AgentBus — instance registry
# ---------------------------------------------------------------------------

def test_register_instance(bus):
    bus.register_instance("erp_specialist:abc", "erp_specialist")
    instances = bus.get_all_instances()
    assert len(instances) == 1
    assert instances[0]["instance_id"] == "erp_specialist:abc"
    assert instances[0]["status"] == "idle"


def test_set_instance_busy_and_idle(bus):
    bus.register_instance("erp_specialist:abc", "erp_specialist")
    bus.set_instance_busy("erp_specialist:abc", 42)

    instances = bus.get_all_instances()
    assert instances[0]["status"] == "busy"
    assert instances[0]["active_task_id"] == 42

    bus.set_instance_idle("erp_specialist:abc")
    instances = bus.get_all_instances()
    assert instances[0]["status"] == "idle"
    assert instances[0]["active_task_id"] is None


def test_get_free_instances(bus):
    bus.register_instance("erp_specialist:abc", "erp_specialist")
    bus.register_instance("erp_specialist:xyz", "erp_specialist")
    bus.set_instance_busy("erp_specialist:xyz", 1)

    free = bus.get_free_instances("erp_specialist")
    assert len(free) == 1
    assert free[0]["instance_id"] == "erp_specialist:abc"


def test_terminate_instance_not_in_all(bus):
    bus.register_instance("erp_specialist:abc", "erp_specialist")
    bus.terminate_instance("erp_specialist:abc")
    assert bus.get_all_instances() == []


# ---------------------------------------------------------------------------
# log_invocation
# ---------------------------------------------------------------------------

def test_log_invocation_writes_record(tmp_db):
    runner.log_invocation(tmp_db, "sess-abc", "developer", "erp_specialist", 42, 5, 0.35, "done")
    conn = sqlite3.connect(tmp_db)
    row = conn.execute("SELECT * FROM invocation_log WHERE session_id = 'sess-abc'").fetchone()
    conn.close()
    assert row is not None
    assert row[9] == "done"


# ---------------------------------------------------------------------------
# render_event
# ---------------------------------------------------------------------------

def test_render_event_text(capsys):
    event = {"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}}
    result = runner.render_event(event)
    assert "Hello" in capsys.readouterr().out
    assert result is None


def test_render_event_tool_use(capsys):
    event = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}
    ]}}
    runner.render_event(event)
    assert "[tool: Bash]" in capsys.readouterr().out


def test_render_event_result_returns_event():
    event = {"type": "result", "session_id": "xyz", "num_turns": 3, "total_cost_usd": 0.12}
    assert runner.render_event(event) == event


# ---------------------------------------------------------------------------
# build_cmd / build_instance_id / build_prompt
# ---------------------------------------------------------------------------

def test_build_instance_id_format():
    iid = runner.build_instance_id("erp_specialist")
    assert iid.startswith("erp_specialist:")
    assert len(iid.split(":")[1]) == 6


def test_build_cmd_erp_permission():
    cmd = runner.build_cmd("erp_specialist", "prompt", "task content")
    idx = cmd.index("--permission-mode")
    assert cmd[idx + 1] == "acceptEdits"


def test_build_cmd_developer_default():
    cmd = runner.build_cmd("developer", "prompt", "task content")
    idx = cmd.index("--permission-mode")
    assert cmd[idx + 1] == "default"


def test_build_cmd_injects_autonomous_system_prompt():
    cmd = runner.build_cmd("erp_specialist", "prompt", "Zbuduj widok")
    idx = cmd.index("--append-system-prompt")
    injected = cmd[idx + 1]
    assert "[TRYB AUTONOMICZNY]" in injected
    assert "Zbuduj widok" in injected


def test_build_prompt_contains_return_address():
    task = {"sender": "developer:abc", "content": "Zbuduj widok"}
    prompt = runner.build_prompt(task, "erp_specialist:xyz", "erp_specialist")
    assert "erp_specialist" in prompt
    assert "[TASK od: developer:abc]" in prompt
    assert "[ADRES ZWROTNY: erp_specialist:xyz]" in prompt
    assert "Zbuduj widok" in prompt
