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
            ["suggest", "--from", "erp_specialist", "--content", "Dodaj indeks",
             "--title", "Dodaj indeks na tabeli X", "--type", "rule"],
            db,
        )
        assert result["ok"] is True
        assert isinstance(result["id"], int)

        suggestions = run_cli(["suggestions", "--status", "open"], db)
        assert suggestions["count"] == 1
        s = suggestions["data"][0]
        assert s["content"] == "Dodaj indeks"
        assert s["title"] == "Dodaj indeks na tabeli X"
        assert s["type"] == "rule"

    def test_suggest_default_type_and_title_fallback(self, db):
        run_cli(["suggest", "--from", "developer", "--content", "Krótka obserwacja"], db)
        suggestions = run_cli(["suggestions"], db)
        s = suggestions["data"][0]
        assert s["type"] == "observation"
        assert s["title"] == "Krótka obserwacja"

    def test_suggestions_filter_by_type(self, db):
        run_cli(["suggest", "--from", "developer", "--content", "R1", "--type", "rule"], db)
        run_cli(["suggest", "--from", "developer", "--content", "T1", "--type", "tool"], db)
        run_cli(["suggest", "--from", "developer", "--content", "O1"], db)

        rules = run_cli(["suggestions", "--type", "rule"], db)
        assert rules["count"] == 1
        assert rules["data"][0]["content"] == "R1"

        tools = run_cli(["suggestions", "--type", "tool"], db)
        assert tools["count"] == 1

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

    def test_suggest_status_bulk(self, db, tmp_path):
        s1 = run_cli(["suggest", "--from", "developer", "--content", "S1"], db)["id"]
        s2 = run_cli(["suggest", "--from", "developer", "--content", "S2"], db)["id"]
        s3 = run_cli(["suggest", "--from", "developer", "--content", "S3"], db)["id"]
        b1 = run_cli(["backlog-add", "--title", "B1", "--content", "x"], db)["id"]

        updates = [
            {"id": s1, "status": "implemented"},
            {"id": s2, "status": "rejected"},
            {"id": s3, "status": "in_backlog", "backlog_id": b1},
        ]
        bulk_file = tmp_path / "sug_updates.json"
        bulk_file.write_text(json.dumps(updates), encoding="utf-8")

        result = run_cli(["suggest-status-bulk", "--file", str(bulk_file)], db)
        assert result["ok"] is True
        assert result["updated"] == 3

        all_sugg = run_cli(["suggestions"], db)
        by_id = {s["id"]: s for s in all_sugg["data"]}
        assert by_id[s1]["status"] == "implemented"
        assert by_id[s2]["status"] == "rejected"
        assert by_id[s3]["status"] == "in_backlog"
        assert by_id[s3]["backlog_id"] == b1

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

    def test_backlog_filter_area(self, db):
        run_cli(["backlog-add", "--title", "ERP task", "--content", "x", "--area", "ERP"], db)
        run_cli(["backlog-add", "--title", "Bot task", "--content", "x", "--area", "Bot"], db)
        result = run_cli(["backlog", "--area", "ERP"], db)
        assert result["count"] == 1
        assert result["data"][0]["title"] == "ERP task"


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


class TestSuggestBulk:
    def test_bulk_adds_all_blocks(self, db, tmp_path):
        bulk_file = tmp_path / "bulk.md"
        bulk_file.write_text(
            "type: rule\ntitle: Tytuł A\nObserwacja A\nwieloliniowa"
            "\n---\n"
            "type: discovery\ntitle: Tytuł B\nObserwacja B"
            "\n---\n"
            "Obserwacja C bez metadanych",
            encoding="utf-8",
        )
        result = run_cli(
            ["suggest-bulk", "--from", "erp_specialist", "--bulk-file", str(bulk_file)],
            db,
        )
        assert result["ok"] is True
        assert result["count"] == 3
        assert len(result["ids"]) == 3

        suggestions = run_cli(["suggestions", "--status", "open"], db)
        by_title = {s["title"]: s for s in suggestions["data"]}
        assert by_title["Tytuł A"]["type"] == "rule"
        assert by_title["Tytuł B"]["type"] == "discovery"
        assert "Obserwacja C" in by_title["Obserwacja C bez metadanych"]["content"]

    def test_bulk_default_type_observation(self, db, tmp_path):
        bulk_file = tmp_path / "no_meta.md"
        bulk_file.write_text("Blok bez type i title", encoding="utf-8")
        result = run_cli(
            ["suggest-bulk", "--from", "developer", "--bulk-file", str(bulk_file)],
            db,
        )
        assert result["ok"] is True
        s = run_cli(["suggestions"], db)["data"][0]
        assert s["type"] == "observation"
        assert s["title"] == "Blok bez type i title"

    def test_bulk_empty_blocks_skipped(self, db, tmp_path):
        bulk_file = tmp_path / "empty_blocks.md"
        bulk_file.write_text(
            "type: rule\ntitle: T\nBlok A\n---\n\n   \n---\ntype: tool\ntitle: U\nBlok C",
            encoding="utf-8",
        )
        result = run_cli(
            ["suggest-bulk", "--from", "developer", "--bulk-file", str(bulk_file)],
            db,
        )
        assert result["ok"] is True
        assert result["count"] == 2


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


class TestBacklogUpdate:
    def test_update_status(self, db):
        add = run_cli(["backlog-add", "--title", "Do aktualizacji", "--content", "x"], db)
        bid = add["id"]
        run_cli(["backlog-update", "--id", str(bid), "--status", "done"], db)
        backlog = run_cli(["backlog"], db)
        item = next(i for i in backlog["data"] if i["id"] == bid)
        assert item["status"] == "done"

    def test_update_content(self, db, tmp_path):
        add = run_cli(["backlog-add", "--title", "Treść do zmiany", "--content", "stara treść"], db)
        bid = add["id"]
        cf = tmp_path / "new_content.md"
        cf.write_text("nowa treść po aktualizacji", encoding="utf-8")
        run_cli(["backlog-update", "--id", str(bid), "--content-file", str(cf)], db)
        backlog = run_cli(["backlog"], db)
        item = next(i for i in backlog["data"] if i["id"] == bid)
        assert item["content"] == "nowa treść po aktualizacji"

    def test_update_status_and_content_together(self, db, tmp_path):
        add = run_cli(["backlog-add", "--title", "Oba pola", "--content", "stare"], db)
        bid = add["id"]
        cf = tmp_path / "upd.md"
        cf.write_text("nowe", encoding="utf-8")
        run_cli(["backlog-update", "--id", str(bid), "--status", "in_progress", "--content-file", str(cf)], db)
        backlog = run_cli(["backlog"], db)
        item = next(i for i in backlog["data"] if i["id"] == bid)
        assert item["status"] == "in_progress"
        assert item["content"] == "nowe"


class TestCliDelete:
    def test_delete_archives_message(self, db):
        send = run_cli(
            ["send", "--from", "developer", "--to", "erp_specialist", "--content", "do usunięcia"],
            db,
        )
        msg_id = send["id"]

        result = run_cli(["delete", "--id", str(msg_id)], db)
        assert result["ok"] is True
        assert msg_id in result["archived"]

        inbox = run_cli(["inbox", "--role", "erp_specialist"], db)
        assert all(m["id"] != msg_id for m in inbox["data"])

    def test_delete_multiple_ids(self, db):
        id1 = run_cli(["send", "--from", "developer", "--to", "analyst", "--content", "msg1"], db)["id"]
        id2 = run_cli(["send", "--from", "developer", "--to", "analyst", "--content", "msg2"], db)["id"]

        result = run_cli(["delete", "--id", str(id1), str(id2)], db)
        assert result["ok"] is True
        assert id1 in result["archived"]
        assert id2 in result["archived"]

        inbox = run_cli(["inbox", "--role", "analyst"], db)
        ids_in_inbox = [m["id"] for m in inbox["data"]]
        assert id1 not in ids_in_inbox
        assert id2 not in ids_in_inbox


class TestBacklogUpdateBulk:
    def test_bulk_update_status(self, db, tmp_path):
        id1 = run_cli(["backlog-add", "--title", "Task 1", "--content", "C1"], db)["id"]
        id2 = run_cli(["backlog-add", "--title", "Task 2", "--content", "C2"], db)["id"]
        id3 = run_cli(["backlog-add", "--title", "Task 3", "--content", "C3"], db)["id"]

        updates = [
            {"id": id1, "status": "done"},
            {"id": id2, "status": "in_progress"},
            {"id": id3, "status": "cancelled"},
        ]
        bulk_file = tmp_path / "updates.json"
        bulk_file.write_text(json.dumps(updates), encoding="utf-8")

        result = run_cli(["backlog-update-bulk", "--file", str(bulk_file)], db)
        assert result["ok"] is True
        assert result["updated"] == 3

        backlog = run_cli(["backlog"], db)
        by_id = {i["id"]: i for i in backlog["data"]}
        assert by_id[id1]["status"] == "done"
        assert by_id[id2]["status"] == "in_progress"
        assert by_id[id3]["status"] == "cancelled"

    def test_bulk_update_content(self, db, tmp_path):
        id1 = run_cli(["backlog-add", "--title", "Task A", "--content", "old A"], db)["id"]
        id2 = run_cli(["backlog-add", "--title", "Task B", "--content", "old B"], db)["id"]

        updates = [
            {"id": id1, "content": "new content A"},
            {"id": id2, "content": "new content B"},
        ]
        bulk_file = tmp_path / "updates.json"
        bulk_file.write_text(json.dumps(updates), encoding="utf-8")

        result = run_cli(["backlog-update-bulk", "--file", str(bulk_file)], db)
        assert result["ok"] is True
        assert result["updated"] == 2

        backlog = run_cli(["backlog"], db)
        by_id = {i["id"]: i for i in backlog["data"]}
        assert by_id[id1]["content"] == "new content A"
        assert by_id[id2]["content"] == "new content B"

    def test_bulk_update_status_and_content(self, db, tmp_path):
        id1 = run_cli(["backlog-add", "--title", "Combined", "--content", "old"], db)["id"]

        updates = [
            {"id": id1, "status": "done", "content": "zaktualizowane"},
        ]
        bulk_file = tmp_path / "updates.json"
        bulk_file.write_text(json.dumps(updates), encoding="utf-8")

        result = run_cli(["backlog-update-bulk", "--file", str(bulk_file)], db)
        assert result["ok"] is True

        backlog = run_cli(["backlog"], db)
        item = next(i for i in backlog["data"] if i["id"] == id1)
        assert item["status"] == "done"
        assert item["content"] == "zaktualizowane"

    def test_bulk_empty_list(self, db, tmp_path):
        bulk_file = tmp_path / "empty.json"
        bulk_file.write_text("[]", encoding="utf-8")
        result = run_cli(["backlog-update-bulk", "--file", str(bulk_file)], db)
        assert result["ok"] is True
        assert result["updated"] == 0


class TestCliSessionLog:
    def test_log_with_title(self, db):
        result = run_cli(
            ["log", "--role", "developer", "--title", "Test Title",
             "--content", "Test content"],
            db,
        )
        assert result["ok"] is True
        assert isinstance(result["id"], int)

        logs = run_cli(["session-logs", "--role", "developer", "--limit", "1"], db)
        assert logs["count"] == 1
        assert logs["data"][0]["title"] == "Test Title"
        assert logs["data"][0]["content"] == "Test content"

    def test_log_without_title_backward_compatible(self, db):
        result = run_cli(
            ["log", "--role", "developer", "--content", "No title"],
            db,
        )
        assert result["ok"] is True

        logs = run_cli(["session-logs", "--role", "developer", "--limit", "1"], db)
        assert logs["data"][0]["title"] is None

    def test_session_logs_without_role_filter(self, db):
        run_cli(["log", "--role", "developer", "--content", "Dev log"], db)
        run_cli(["log", "--role", "erp_specialist", "--content", "ERP log"], db)

        logs = run_cli(["session-logs", "--limit", "10"], db)
        assert logs["count"] == 2
        roles = {log["role"] for log in logs["data"]}
        assert "developer" in roles
        assert "erp_specialist" in roles

    def test_session_logs_with_role_filter(self, db):
        run_cli(["log", "--role", "developer", "--content", "Dev log"], db)
        run_cli(["log", "--role", "erp_specialist", "--content", "ERP log"], db)

        logs = run_cli(["session-logs", "--role", "developer", "--limit", "10"], db)
        assert logs["count"] == 1
        assert logs["data"][0]["role"] == "developer"

    def test_session_logs_limit(self, db):
        for i in range(5):
            run_cli(["log", "--role", "developer", "--content", f"Log {i}"], db)

        logs = run_cli(["session-logs", "--role", "developer", "--limit", "3"], db)
        assert logs["count"] == 3

    def test_log_with_content_file(self, db, tmp_path):
        content_file = tmp_path / "log.txt"
        content_file.write_text("Content from file", encoding="utf-8")

        result = run_cli(
            ["log", "--role", "developer", "--title", "File Test",
             "--content-file", str(content_file)],
            db,
        )
        assert result["ok"] is True

        logs = run_cli(["session-logs", "--role", "developer", "--limit", "1"], db)
        assert logs["data"][0]["content"] == "Content from file"
        assert logs["data"][0]["title"] == "File Test"
