"""Integration tests for agent_bus_cli.py — full roundtrip through CLI."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CLI = str(Path(__file__).parent.parent / "tools" / "agent_bus_cli.py")
PYTHON = sys.executable


def run_cli(args: list[str], db_path: str) -> dict:
    result = subprocess.run(
        [PYTHON, CLI, "--db", db_path] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "test_cli.db")


class TestCliSendAndInbox:
    def test_send_and_inbox_roundtrip(self, db):
        send_result = run_cli(
            ["send", "--from", "developer", "--to", "erp_specialist",
             "--content", "Popraw widok"],
            db,
        )
        assert send_result["ok"] is True
        assert isinstance(send_result["id"], int)

        inbox_result = run_cli(["inbox", "--role", "erp_specialist"], db)
        assert inbox_result["ok"] is True
        assert inbox_result["count"] == 1
        assert inbox_result["data"][0]["content"] == "Popraw widok"

    def test_send_with_type_and_session(self, db):
        run_cli(
            ["send", "--from", "analyst", "--to", "human",
             "--content", "Potrzebuję decyzji", "--type", "flag_human",
             "--session-id", "sess-abc"],
            db,
        )
        inbox = run_cli(["inbox", "--role", "human"], db)
        msg = inbox["data"][0]
        assert msg["type"] == "flag_human"
        assert msg["session_id"] == "sess-abc"

    def test_empty_inbox(self, db):
        result = run_cli(["inbox", "--role", "nobody"], db)
        assert result["ok"] is True
        assert result["count"] == 0
        assert result["data"] == []


class TestCliWriteState:
    def test_write_and_read_state(self, db):
        write_result = run_cli(
            ["write-state", "--role", "developer",
             "--type", "progress", "--content", "KM1 done"],
            db,
        )
        assert write_result["ok"] is True

        state_result = run_cli(
            ["state", "--role", "developer", "--type", "progress"], db
        )
        assert state_result["count"] == 1
        assert state_result["data"][0]["content"] == "KM1 done"

    def test_write_state_with_metadata(self, db):
        run_cli(
            ["write-state", "--role", "developer", "--type", "backlog_item",
             "--content", "Fix X",
             "--metadata", '{"priority": "high"}'],
            db,
        )
        result = run_cli(["state", "--role", "developer", "--type", "backlog_item"], db)
        assert result["data"][0]["metadata"]["priority"] == "high"


class TestCliFlag:
    def test_flag_for_human(self, db):
        result = run_cli(
            ["flag", "--from", "erp_specialist",
             "--reason", "Potrzebuję zatwierdzenia", "--urgency", "high"],
            db,
        )
        assert result["ok"] is True

        inbox = run_cli(["inbox", "--role", "human"], db)
        assert inbox["count"] == 1
        msg = inbox["data"][0]
        assert msg["type"] == "flag_human"
        assert "HIGH" in msg["content"].upper()


class TestContentFile:
    def test_send_with_content_file(self, db, tmp_path):
        content_file = tmp_path / "msg.txt"
        content_file.write_text("Treść z pliku", encoding="utf-8")
        result = run_cli(
            ["send", "--from", "developer", "--to", "erp_specialist",
             "--content-file", str(content_file)],
            db,
        )
        assert result["ok"] is True
        inbox = run_cli(["inbox", "--role", "erp_specialist"], db)
        assert inbox["data"][0]["content"] == "Treść z pliku"

    def test_write_state_with_content_file(self, db, tmp_path):
        content_file = tmp_path / "reflection.md"
        content_file.write_text("Długa refleksja\nz wieloma liniami", encoding="utf-8")
        result = run_cli(
            ["write-state", "--role", "erp_specialist", "--type", "reflection",
             "--content-file", str(content_file)],
            db,
        )
        assert result["ok"] is True
        states = run_cli(["state", "--role", "erp_specialist", "--type", "reflection"], db)
        assert "Długa refleksja" in states["data"][0]["content"]

    def test_flag_with_reason_file(self, db, tmp_path):
        reason_file = tmp_path / "reason.txt"
        reason_file.write_text("Potrzebuję decyzji w sprawie widoku", encoding="utf-8")
        result = run_cli(
            ["flag", "--from", "analyst",
             "--reason-file", str(reason_file)],
            db,
        )
        assert result["ok"] is True
        inbox = run_cli(["inbox", "--role", "human"], db)
        assert "Potrzebuję decyzji" in inbox["data"][0]["content"]
