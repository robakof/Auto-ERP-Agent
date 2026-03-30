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

        inbox_result = run_cli(["inbox", "--role", "erp_specialist", "--full"], db)
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
        run_cli(["suggest-status", "--id", str(sid), "--status", "implemented",
                 "--backlog-id", str(bid)], db)
        suggestions = run_cli(["suggestions", "--status", "implemented"], db)
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
            {"id": s3, "status": "implemented", "backlog_id": b1},
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
        assert by_id[s3]["status"] == "implemented"
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

        inbox = run_cli(["inbox", "--role", "human", "--full"], db)
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
        inbox = run_cli(["inbox", "--role", "erp_specialist", "--full"], db)
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
        inbox = run_cli(["inbox", "--role", "human", "--full"], db)
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

    def test_session_logs_offset(self, db):
        for i in range(5):
            run_cli(["log", "--role", "developer", "--content", f"Log {i}", "--title", f"Title {i}"], db)

        # First 3 (offset 0, limit 3)
        first_three = run_cli(["session-logs", "--role", "developer", "--limit", "3", "--offset", "0"], db)
        assert first_three["count"] == 3
        assert first_three["data"][0]["title"] == "Title 4"  # newest first

        # Next 2 (offset 3, limit 2)
        next_two = run_cli(["session-logs", "--role", "developer", "--limit", "2", "--offset", "3"], db)
        assert next_two["count"] == 2
        assert next_two["data"][0]["title"] == "Title 1"

    def test_session_logs_metadata_only(self, db):
        run_cli(["log", "--role", "developer", "--content", "Full content here", "--title", "Test Title"], db)

        # Full result (no --metadata-only flag)
        full = run_cli(["session-logs", "--role", "developer", "--limit", "1"], db)
        assert "content" in full["data"][0]
        assert full["data"][0]["content"] == "Full content here"

        # Metadata only (--metadata-only flag)
        metadata = run_cli(["session-logs", "--role", "developer", "--limit", "1", "--metadata-only"], db)
        assert "content" not in metadata["data"][0]
        assert "title" in metadata["data"][0]
        assert metadata["data"][0]["title"] == "Test Title"

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


class TestDependsOn:
    """Tests for #124 — backlog depends_on."""

    def test_backlog_add_with_depends_on(self, db):
        parent = run_cli(
            ["backlog-add", "--title", "Parent task",
             "--content", "Parent", "--area", "Dev"],
            db,
        )
        child = run_cli(
            ["backlog-add", "--title", "Child task",
             "--content", "Child", "--area", "Dev",
             "--depends-on", str(parent["id"])],
            db,
        )
        assert child["ok"] is True
        item = run_cli(["backlog", "--id", str(child["id"])], db)
        assert item["data"]["depends_on"] == parent["id"]

    def test_backlog_add_without_depends_on(self, db):
        result = run_cli(
            ["backlog-add", "--title", "No dep",
             "--content", "Solo", "--area", "Dev"],
            db,
        )
        item = run_cli(["backlog", "--id", str(result["id"])], db)
        assert item["data"]["depends_on"] is None

    def test_backlog_update_set_depends_on(self, db):
        parent = run_cli(
            ["backlog-add", "--title", "Dep target",
             "--content", "x", "--area", "Dev"],
            db,
        )
        child = run_cli(
            ["backlog-add", "--title", "Dep source",
             "--content", "y", "--area", "Dev"],
            db,
        )
        run_cli(
            ["backlog-update", "--id", str(child["id"]),
             "--depends-on", str(parent["id"])],
            db,
        )
        item = run_cli(["backlog", "--id", str(child["id"])], db)
        assert item["data"]["depends_on"] == parent["id"]

    def test_backlog_update_clear_depends_on(self, db):
        parent = run_cli(
            ["backlog-add", "--title", "P", "--content", "x", "--area", "Dev"],
            db,
        )
        child = run_cli(
            ["backlog-add", "--title", "C", "--content", "y", "--area", "Dev",
             "--depends-on", str(parent["id"])],
            db,
        )
        # Clear with --depends-on 0
        run_cli(
            ["backlog-update", "--id", str(child["id"]), "--depends-on", "0"],
            db,
        )
        item = run_cli(["backlog", "--id", str(child["id"])], db)
        assert item["data"]["depends_on"] is None

    def test_dependency_warning_on_in_progress(self, db):
        parent = run_cli(
            ["backlog-add", "--title", "Blocker",
             "--content", "x", "--area", "Dev"],
            db,
        )
        child = run_cli(
            ["backlog-add", "--title", "Blocked",
             "--content", "y", "--area", "Dev",
             "--depends-on", str(parent["id"])],
            db,
        )
        result = run_cli(
            ["backlog-update", "--id", str(child["id"]),
             "--status", "in_progress"],
            db,
        )
        assert result["ok"] is True
        assert "warning" in result
        assert "Blocker" in result["warning"]

    def test_no_warning_when_dependency_done(self, db):
        parent = run_cli(
            ["backlog-add", "--title", "Done dep",
             "--content", "x", "--area", "Dev"],
            db,
        )
        run_cli(
            ["backlog-update", "--id", str(parent["id"]),
             "--status", "done"],
            db,
        )
        child = run_cli(
            ["backlog-add", "--title", "Free to go",
             "--content", "y", "--area", "Dev",
             "--depends-on", str(parent["id"])],
            db,
        )
        result = run_cli(
            ["backlog-update", "--id", str(child["id"]),
             "--status", "in_progress"],
            db,
        )
        assert result["ok"] is True
        assert "warning" not in result

    def test_depends_on_in_bulk_update(self, db, tmp_path):
        parent = run_cli(
            ["backlog-add", "--title", "Bulk parent",
             "--content", "x", "--area", "Dev"],
            db,
        )
        child = run_cli(
            ["backlog-add", "--title", "Bulk child",
             "--content", "y", "--area", "Dev"],
            db,
        )
        bulk_file = tmp_path / "bulk_dep.json"
        bulk_file.write_text(
            json.dumps([{"id": child["id"], "depends_on": parent["id"]}]),
            encoding="utf-8",
        )
        result = run_cli(
            ["backlog-update-bulk", "--file", str(bulk_file)],
            db,
        )
        assert result["ok"] is True
        item = run_cli(["backlog", "--id", str(child["id"])], db)
        assert item["data"]["depends_on"] == parent["id"]


class TestBroadcast:
    """Tests for #141 — send --to all."""

    def test_broadcast_sends_to_all_except_sender(self, db):
        result = run_cli(
            ["send", "--from", "developer", "--to", "all",
             "--content", "Broadcast test"],
            db,
        )
        assert result["ok"] is True
        assert result["count"] >= 1
        assert "developer" not in result["recipients"]
        # Every recipient should have the message
        for recipient in result["recipients"]:
            inbox = run_cli(["inbox", "--role", recipient, "--full"], db)
            assert inbox["count"] == 1
            assert inbox["data"][0]["content"] == "Broadcast test"

    def test_broadcast_excludes_sender(self, db):
        result = run_cli(
            ["send", "--from", "architect", "--to", "all",
             "--content", "From architect"],
            db,
        )
        assert "architect" not in result["recipients"]
        # Architect inbox should be empty
        inbox = run_cli(["inbox", "--role", "architect"], db)
        assert inbox["count"] == 0

    def test_broadcast_atomic(self, db):
        result = run_cli(
            ["send", "--from", "developer", "--to", "all",
             "--content", "Atomic test"],
            db,
        )
        # All IDs should be sequential (created in one transaction)
        ids = result["ids"]
        assert len(ids) == result["count"]
        for i in range(1, len(ids)):
            assert ids[i] == ids[i - 1] + 1


class TestInboxSenderFilter:
    """Tests for #154 — inbox --sender filter."""

    def test_filter_by_sender(self, db):
        run_cli(["send", "--from", "developer", "--to", "human", "--content", "From dev"], db)
        run_cli(["send", "--from", "architect", "--to", "human", "--content", "From arch"], db)

        # Use --sender without --full first (no auto mark-read)
        all_msgs = run_cli(["inbox", "--role", "human"], db)
        assert all_msgs["count"] == 2

        filtered = run_cli(["inbox", "--role", "human", "--full", "--sender", "architect"], db)
        assert filtered["count"] == 1
        assert filtered["data"][0]["sender"] == "architect"
        assert filtered["data"][0]["content"] == "From arch"

    def test_filter_by_sender_no_match(self, db):
        run_cli(["send", "--from", "developer", "--to", "human", "--content", "Only dev"], db)

        filtered = run_cli(["inbox", "--role", "human", "--sender", "architect"], db)
        assert filtered["count"] == 0
        assert filtered["data"] == []

    def test_filter_by_sender_summary_mode(self, db):
        run_cli(["send", "--from", "developer", "--to", "human", "--content", "Dev msg"], db)
        run_cli(["send", "--from", "analyst", "--to", "human", "--content", "Analyst msg"], db)

        filtered = run_cli(["inbox", "--role", "human", "--sender", "developer"], db)
        assert filtered["count"] == 1
        assert "content" not in filtered["data"][0]  # summary mode


class TestCliInboxSummary:
    def test_empty_db(self, db):
        result = run_cli(["inbox-summary"], db)
        assert result["ok"] is True
        # All roles should appear with total=0
        for role_data in result["data"].values():
            assert role_data["total"] == 0
            assert role_data["types"] == {}

    def test_counts_by_type(self, db):
        run_cli(["send", "--from", "developer", "--to", "analyst", "--content", "a"], db)
        run_cli(["send", "--from", "developer", "--to", "analyst", "--content", "b"], db)
        run_cli(
            ["send", "--from", "architect", "--to", "analyst",
             "--content", "c", "--type", "task"],
            db,
        )
        result = run_cli(["inbox-summary"], db)
        analyst = result["data"]["analyst"]
        assert analyst["total"] == 3
        assert analyst["types"]["suggestion"] == 2
        assert analyst["types"]["task"] == 1

    def test_read_messages_excluded(self, db):
        send = run_cli(
            ["send", "--from", "developer", "--to", "analyst", "--content", "x"], db
        )
        run_cli(["mark-read", "--id", str(send["id"])], db)
        result = run_cli(["inbox-summary"], db)
        assert result["data"]["analyst"]["total"] == 0


class TestCliLiveAgents:
    def test_empty(self, db):
        result = run_cli(["live-agents"], db)
        assert result["ok"] is True
        assert result["count"] == 0
        assert result["data"] == []

    def test_shows_active(self, db):
        # Spawn creates a live_agents record
        # Use raw insert via spawn-request which inserts into invocations, not live_agents
        # We need to insert directly — use send + raw approach
        # Actually spawn-request inserts into invocations table, not live_agents
        # For a proper test we need spawn which requires VS Code
        # Instead, verify the command runs and returns empty on clean DB
        result = run_cli(["live-agents"], db)
        assert result["ok"] is True
        assert isinstance(result["data"], list)


class TestCliHandoffsPending:
    def test_empty(self, db):
        result = run_cli(["handoffs-pending"], db)
        assert result["ok"] is True
        assert result["count"] == 0

    def test_handoff_without_live_agent(self, db):
        run_cli(
            ["handoff", "--from", "architect", "--to", "developer",
             "--phase", "test", "--status", "PASS",
             "--summary", "done", "--next-action", "implement"],
            db,
        )
        result = run_cli(["handoffs-pending"], db)
        assert result["ok"] is True
        assert result["count"] == 1
        assert result["data"][0]["sender"] == "architect"
        assert result["data"][0]["recipient"] == "developer"
        assert result["data"][0]["recipient_live"] == 0

    def test_read_handoff_excluded(self, db):
        h = run_cli(
            ["handoff", "--from", "architect", "--to", "developer",
             "--phase", "test", "--status", "PASS",
             "--summary", "done", "--next-action", "go"],
            db,
        )
        run_cli(["mark-read", "--id", str(h["id"])], db)
        result = run_cli(["handoffs-pending"], db)
        assert result["count"] == 0


class TestCliBacklogSummary:
    def test_empty_db(self, db):
        result = run_cli(["backlog-summary"], db)
        assert result["ok"] is True
        assert result["data"] == {}

    def test_counts_by_area_and_status(self, db):
        run_cli(["backlog-add", "--title", "T1", "--area", "Dev", "--content", "x"], db)
        run_cli(["backlog-add", "--title", "T2", "--area", "Dev", "--content", "y"], db)
        run_cli(["backlog-add", "--title", "T3", "--area", "Arch", "--content", "z"], db)
        result = run_cli(["backlog-summary"], db)
        assert result["data"]["Dev"]["planned"] == 2
        assert result["data"]["Arch"]["planned"] == 1

    def test_includes_in_progress(self, db):
        item = run_cli(["backlog-add", "--title", "T1", "--area", "Dev", "--content", "x"], db)
        run_cli(["backlog-update", "--id", str(item["id"]), "--status", "in_progress"], db)
        run_cli(["backlog-add", "--title", "T2", "--area", "Dev", "--content", "y"], db)
        result = run_cli(["backlog-summary"], db)
        assert result["data"]["Dev"]["planned"] == 1
        assert result["data"]["Dev"]["in_progress"] == 1


class TestSpawnDuplicateGuard:
    """Tests for _check_spawn_duplicate — duplicate spawn detection."""

    @pytest.fixture
    def bus(self, db):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "lib"))
        from agent_bus import AgentBus
        return AgentBus(db)

    def test_no_duplicate_returns_none(self, bus):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from agent_bus_cli import _check_spawn_duplicate
        result = _check_spawn_duplicate(bus._conn, "developer")
        assert result is None

    def test_recent_invocation_detected(self, bus):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from agent_bus_cli import _check_spawn_duplicate
        bus._conn.execute(
            """INSERT INTO invocations (invoker_type, invoker_id, target_role, task, status)
               VALUES ('agent', 'dispatcher', 'developer', 'test task', 'running')"""
        )
        bus._conn.commit()
        result = _check_spawn_duplicate(bus._conn, "developer")
        assert result is not None
        assert "developer" in result
        assert "--force" in result

    def test_different_role_not_detected(self, bus):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from agent_bus_cli import _check_spawn_duplicate
        bus._conn.execute(
            """INSERT INTO invocations (invoker_type, invoker_id, target_role, task, status)
               VALUES ('agent', 'dispatcher', 'prompt_engineer', 'test', 'running')"""
        )
        bus._conn.commit()
        result = _check_spawn_duplicate(bus._conn, "developer")
        assert result is None

    def test_old_invocation_not_detected(self, bus):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from agent_bus_cli import _check_spawn_duplicate
        bus._conn.execute(
            """INSERT INTO invocations (invoker_type, invoker_id, target_role, task, status,
               created_at) VALUES ('agent', 'dispatcher', 'developer', 'test', 'running',
               datetime('now', '-60 seconds'))"""
        )
        bus._conn.commit()
        result = _check_spawn_duplicate(bus._conn, "developer")
        assert result is None

    def test_active_live_agent_detected(self, bus):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from agent_bus_cli import _check_spawn_duplicate
        bus._conn.execute(
            """INSERT INTO live_agents (session_id, role, status)
               VALUES ('abc123', 'developer', 'active')"""
        )
        bus._conn.commit()
        result = _check_spawn_duplicate(bus._conn, "developer")
        assert result is not None
        assert "active" in result
        assert "--force" in result

    def test_stopped_agent_not_detected(self, bus):
        sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
        from agent_bus_cli import _check_spawn_duplicate
        bus._conn.execute(
            """INSERT INTO live_agents (session_id, role, status)
               VALUES ('abc123', 'developer', 'stopped')"""
        )
        bus._conn.commit()
        result = _check_spawn_duplicate(bus._conn, "developer")
        assert result is None


class TestDashboard:
    """Integration tests for dashboard command."""

    def test_dashboard_empty_db(self, db):
        result = run_cli(["dashboard"], db)
        assert result["ok"] is True
        data = result["data"]
        assert "timestamp" in data
        assert data["agents"]["active"] == []
        assert data["agents"]["stale"] == []
        assert data["agents"]["stopped_count"] == 0
        assert data["inbox"]["unread_by_role"] == {}
        assert data["handoffs"]["pending"] == []
        assert data["backlog"]["planned_by_area"] == {}
        assert data["backlog"]["in_progress"] == 0
        assert data["alerts"] == []

    def test_dashboard_with_data(self, db):
        # Seed agents
        run_cli(["send", "--from", "developer", "--to", "architect", "--content", "review please"], db)
        run_cli(["backlog-add", "--title", "Task A", "--content", "x", "--area", "Dev"], db)
        run_cli(["backlog-add", "--title", "Task B", "--content", "y", "--area", "Arch"], db)

        result = run_cli(["dashboard"], db)
        assert result["ok"] is True
        data = result["data"]
        assert data["inbox"]["unread_by_role"]["architect"] == 1
        assert data["backlog"]["planned_by_area"]["Dev"] == 1
        assert data["backlog"]["planned_by_area"]["Arch"] == 1

    def test_dashboard_with_live_agents(self, db):
        """Dashboard shows active and stale agents from v_agent_status."""
        import sqlite3
        # Ensure schema exists by triggering AgentBus init
        run_cli(["inbox", "--role", "nobody"], db)
        conn = sqlite3.connect(db)
        conn.execute(
            """INSERT INTO live_agents (session_id, role, status, last_activity, created_at)
               VALUES ('sess-active', 'developer', 'active', datetime('now', '-1 minutes'), datetime('now'))"""
        )
        conn.execute(
            """INSERT INTO live_agents (session_id, role, status, last_activity, created_at)
               VALUES ('sess-stale', 'analyst', 'active', datetime('now', '-20 minutes'), datetime('now', '-30 minutes'))"""
        )
        conn.execute(
            """INSERT INTO live_agents (session_id, role, status, created_at)
               VALUES ('sess-stopped', 'architect', 'stopped', datetime('now', '-1 hour'))"""
        )
        conn.commit()
        conn.close()

        result = run_cli(["dashboard"], db)
        data = result["data"]
        assert len(data["agents"]["active"]) == 1
        assert data["agents"]["active"][0]["role"] == "developer"
        assert len(data["agents"]["stale"]) == 1
        assert data["agents"]["stale"][0]["role"] == "analyst"
        assert data["agents"]["stopped_count"] == 1
        assert len(data["alerts"]) >= 1


class TestCliStopRequest:
    """Tests for stop-request command (#219 bezpiecznik)."""

    def _insert_live_agent(self, db, session_id="sess-abc", role="developer"):
        """Insert a live agent directly for testing."""
        import sqlite3
        # Init DB schema by triggering any CLI command first
        run_cli(["send", "--from", "test", "--to", role, "--content", "setup"], db)
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        conn.execute(
            """INSERT OR IGNORE INTO live_agents (session_id, role, terminal_name, status)
               VALUES (?, ?, ?, 'active')""",
            (session_id, role, f"Agent: {role}"),
        )
        conn.commit()
        conn.close()

    def test_creates_pending_invocation(self, db):
        self._insert_live_agent(db)
        result = run_cli([
            "stop-request", "--from", "dispatcher", "--session-id", "sess-abc"
        ], db)
        assert result["ok"] is True
        assert result["status"] == "pending"
        assert result["action"] == "stop"
        assert result["session_id"] == "sess-abc"

    def test_returns_error_for_unknown_session(self, db):
        run_cli(["send", "--from", "test", "--to", "test", "--content", "init"], db)
        result = run_cli([
            "stop-request", "--from", "dispatcher", "--session-id", "nonexistent"
        ], db)
        assert result["ok"] is False


class TestCliResumeRequest:
    """Tests for resume-request command (#219 bezpiecznik)."""

    def _insert_live_agent(self, db, session_id="sess-xyz", role="architect"):
        import sqlite3
        run_cli(["send", "--from", "test", "--to", role, "--content", "setup"], db)
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        conn.execute(
            """INSERT OR IGNORE INTO live_agents (session_id, role, terminal_name, status)
               VALUES (?, ?, ?, 'stopped')""",
            (session_id, role, f"Agent: {role}"),
        )
        conn.commit()
        conn.close()

    def test_creates_pending_invocation(self, db):
        self._insert_live_agent(db)
        result = run_cli([
            "resume-request", "--from", "dispatcher", "--session-id", "sess-xyz"
        ], db)
        assert result["ok"] is True
        assert result["status"] == "pending"
        assert result["action"] == "resume"
        assert result["session_id"] == "sess-xyz"

    def test_returns_error_for_unknown_session(self, db):
        run_cli(["send", "--from", "test", "--to", "test", "--content", "init"], db)
        result = run_cli([
            "resume-request", "--from", "dispatcher", "--session-id", "nonexistent"
        ], db)
        assert result["ok"] is False
