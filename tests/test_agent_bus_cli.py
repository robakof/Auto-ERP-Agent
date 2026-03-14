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


class TestCliSuggestAndBacklog:
    def test_suggest_and_list(self, db):
        result = run_cli(
            ["suggest", "--from", "erp_specialist", "--content", "Dodaj indeks"],
            db,
        )
        assert result["ok"] is True
        assert isinstance(result["id"], int)

        suggestions = run_cli(["suggestions", "--status", "open"], db)
        assert suggestions["count"] == 1
        assert suggestions["data"][0]["content"] == "Dodaj indeks"

    def test_suggest_status_update(self, db):
        sid = run_cli(
            ["suggest", "--from", "analyst", "--content", "Sugestia"], db
        )["id"]
        bid = run_cli(
            ["backlog-add", "--title", "Task", "--content", "Opis"], db
        )["id"]
        run_cli(["suggest-status", "--id", str(sid), "--status", "in_backlog",
                 "--backlog-id", str(bid)], db)
        suggestions = run_cli(["suggestions", "--status", "in_backlog"], db)
        assert suggestions["count"] == 1
        assert suggestions["data"][0]["backlog_id"] == bid

    def test_backlog_add_and_list(self, db):
        result = run_cli(
            ["backlog-add", "--title", "Fix bot", "--content", "Opis problemu",
             "--area", "Bot", "--value", "wysoka", "--effort", "mala"],
            db,
        )
        assert result["ok"] is True
        backlog = run_cli(["backlog", "--status", "planned"], db)
        assert backlog["count"] == 1
        item = backlog["data"][0]
        assert item["title"] == "Fix bot"
        assert item["area"] == "Bot"

    def test_backlog_update_status(self, db):
        bid = run_cli(
            ["backlog-add", "--title", "Task", "--content", "Opis"], db
        )["id"]
        run_cli(["backlog-update", "--id", str(bid), "--status", "done"], db)
        done = run_cli(["backlog", "--status", "done"], db)
        assert done["count"] == 1


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

    def test_suggest_with_content_file(self, db, tmp_path):
        content_file = tmp_path / "suggestion.md"
        content_file.write_text("Długa sugestia\nz wieloma liniami", encoding="utf-8")
        result = run_cli(
            ["suggest", "--from", "erp_specialist",
             "--content-file", str(content_file)],
            db,
        )
        assert result["ok"] is True
        suggestions = run_cli(["suggestions"], db)
        assert "Długa sugestia" in suggestions["data"][0]["content"]

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


class TestBacklogAddBulk:
    def test_bulk_adds_all_items(self, db, tmp_path):
        items = [
            {"title": "Zadanie A", "area": "Dev", "value": "wysoka", "effort": "mala", "content": "Opis A"},
            {"title": "Zadanie B", "area": "Bot", "value": "srednia", "effort": "srednia", "content": "Opis B"},
            {"title": "Zadanie C", "content": "Opis C"},
        ]
        bulk_file = tmp_path / "items.json"
        bulk_file.write_text(json.dumps(items), encoding="utf-8")

        result = run_cli(["backlog-add-bulk", "--file", str(bulk_file)], db)
        assert result["ok"] is True
        assert result["count"] == 3
        assert len(result["ids"]) == 3

        backlog = run_cli(["backlog"], db)
        titles = [i["title"] for i in backlog["data"]]
        assert "Zadanie A" in titles
        assert "Zadanie B" in titles
        assert "Zadanie C" in titles

    def test_bulk_empty_list(self, db, tmp_path):
        bulk_file = tmp_path / "empty.json"
        bulk_file.write_text("[]", encoding="utf-8")
        result = run_cli(["backlog-add-bulk", "--file", str(bulk_file)], db)
        assert result["ok"] is True
        assert result["count"] == 0

    def test_bulk_preserves_fields(self, db, tmp_path):
        items = [{"title": "Test pól", "area": "Arch", "value": "niska", "effort": "duza", "content": "Szczegóły"}]
        bulk_file = tmp_path / "single.json"
        bulk_file.write_text(json.dumps(items), encoding="utf-8")
        run_cli(["backlog-add-bulk", "--file", str(bulk_file)], db)

        backlog = run_cli(["backlog"], db)
        item = backlog["data"][0]
        assert item["area"] == "Arch"
        assert item["value"] == "niska"
        assert item["effort"] == "duza"
