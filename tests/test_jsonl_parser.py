"""Unit tests for jsonl_parser — transcript parsing to structured data."""

import json
import pytest
from pathlib import Path

from tools.jsonl_parser import parse_jsonl, save_to_db, _input_summary
from tools.lib.agent_bus import AgentBus


def make_jsonl(tmp_path: Path, entries: list[dict]) -> Path:
    """Write list of dicts to a .jsonl file."""
    p = tmp_path / "session.jsonl"
    p.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries), encoding="utf-8")
    return p


def make_assistant_turn(uuid: str, tool_name: str, tool_id: str, input_dict: dict, usage: dict, timestamp: str) -> dict:
    return {
        "type": "assistant",
        "uuid": uuid,
        "timestamp": timestamp,
        "sessionId": "uuid-abc",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": tool_id, "name": tool_name, "input": input_dict}
            ],
            "usage": usage,
        },
    }


def make_tool_result(tool_use_id: str, is_error: bool, timestamp: str) -> dict:
    return {
        "type": "user",
        "timestamp": timestamp,
        "sessionId": "uuid-abc",
        "message": {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": tool_use_id, "is_error": is_error or None, "content": "result"}
            ],
        },
    }


def make_turn_duration(parent_uuid: str, duration_ms: int, timestamp: str) -> dict:
    return {
        "type": "system",
        "subtype": "turn_duration",
        "parentUuid": parent_uuid,
        "durationMs": duration_ms,
        "timestamp": timestamp,
        "sessionId": "uuid-abc",
    }


USAGE = {"input_tokens": 1000, "output_tokens": 200, "cache_read_input_tokens": 500, "cache_creation_input_tokens": 300}


class TestInputSummary:
    def test_extracts_file_path(self):
        assert _input_summary({"file_path": "CLAUDE.md"}) == "CLAUDE.md"

    def test_extracts_command(self):
        assert _input_summary({"command": "python tools/x.py"}) == "python tools/x.py"

    def test_extracts_pattern(self):
        assert _input_summary({"pattern": "**/*.py"}) == "**/*.py"

    def test_fallback_to_json(self):
        result = _input_summary({"unknown": "value"})
        assert "unknown" in result

    def test_truncates_to_200(self):
        result = _input_summary({"command": "x" * 300})
        assert len(result) <= 200


class TestParseJsonl:
    def test_extracts_claude_session_id(self, tmp_path):
        turn = make_assistant_turn("u1", "Read", "t1", {"file_path": "a.md"}, USAGE, "2026-03-15T10:00:00Z")
        f = make_jsonl(tmp_path, [turn])
        result = parse_jsonl(str(f))
        assert result["claude_session_id"] == "uuid-abc"

    def test_extracts_timestamps(self, tmp_path):
        t1 = make_assistant_turn("u1", "Read", "t1", {"file_path": "a.md"}, USAGE, "2026-03-15T10:00:00Z")
        tr = make_tool_result("t1", False, "2026-03-15T10:01:00Z")
        f = make_jsonl(tmp_path, [t1, tr])
        result = parse_jsonl(str(f))
        assert result["started_at"] == "2026-03-15T10:00:00Z"
        assert result["ended_at"] == "2026-03-15T10:01:00Z"

    def test_parses_tool_call(self, tmp_path):
        turn = make_assistant_turn("u1", "Read", "t1", {"file_path": "CLAUDE.md"}, USAGE, "2026-03-15T10:00:00Z")
        f = make_jsonl(tmp_path, [turn])
        result = parse_jsonl(str(f))
        assert len(result["tool_calls"]) == 1
        tc = result["tool_calls"][0]
        assert tc["tool_name"] == "Read"
        assert tc["input_summary"] == "CLAUDE.md"
        assert tc["is_error"] == 0

    def test_marks_error_tool_call(self, tmp_path):
        turn = make_assistant_turn("u1", "Bash", "t1", {"command": "bad cmd"}, USAGE, "2026-03-15T10:00:00Z")
        tr = make_tool_result("t1", True, "2026-03-15T10:01:00Z")
        f = make_jsonl(tmp_path, [turn, tr])
        result = parse_jsonl(str(f))
        assert result["tool_calls"][0]["is_error"] == 1

    def test_non_error_tool_result_is_zero(self, tmp_path):
        turn = make_assistant_turn("u1", "Read", "t1", {"file_path": "x.md"}, USAGE, "2026-03-15T10:00:00Z")
        tr = make_tool_result("t1", False, "2026-03-15T10:01:00Z")
        f = make_jsonl(tmp_path, [turn, tr])
        result = parse_jsonl(str(f))
        assert result["tool_calls"][0]["is_error"] == 0

    def test_parses_token_usage(self, tmp_path):
        turn = make_assistant_turn("u1", "Read", "t1", {"file_path": "x.md"}, USAGE, "2026-03-15T10:00:00Z")
        f = make_jsonl(tmp_path, [turn])
        result = parse_jsonl(str(f))
        assert len(result["token_usage"]) == 1
        tu = result["token_usage"][0]
        assert tu["input_tokens"] == 1000
        assert tu["output_tokens"] == 200
        assert tu["cache_read_tokens"] == 500
        assert tu["cache_create_tokens"] == 300

    def test_links_duration_to_turn(self, tmp_path):
        turn = make_assistant_turn("u1", "Read", "t1", {"file_path": "x.md"}, USAGE, "2026-03-15T10:00:00Z")
        dur = make_turn_duration("u1", 3500, "2026-03-15T10:00:03Z")
        f = make_jsonl(tmp_path, [turn, dur])
        result = parse_jsonl(str(f))
        assert result["token_usage"][0]["duration_ms"] == 3500

    def test_multiple_turns_indexed(self, tmp_path):
        t1 = make_assistant_turn("u1", "Read", "tid1", {"file_path": "a.md"}, USAGE, "2026-03-15T10:00:00Z")
        t2 = make_assistant_turn("u2", "Bash", "tid2", {"command": "python x.py"}, USAGE, "2026-03-15T10:01:00Z")
        f = make_jsonl(tmp_path, [t1, t2])
        result = parse_jsonl(str(f))
        assert len(result["token_usage"]) == 2
        assert result["token_usage"][0]["turn_index"] == 0
        assert result["token_usage"][1]["turn_index"] == 1

    def test_tokens_out_on_tool_call(self, tmp_path):
        turn = make_assistant_turn("u1", "Read", "t1", {"file_path": "x.md"}, USAGE, "2026-03-15T10:00:00Z")
        f = make_jsonl(tmp_path, [turn])
        result = parse_jsonl(str(f))
        assert result["tool_calls"][0]["tokens_out"] == 200  # from USAGE output_tokens

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        result = parse_jsonl(str(p))
        assert result["claude_session_id"] is None
        assert result["tool_calls"] == []
        assert result["token_usage"] == []


class TestSaveToDb:
    def test_saves_session(self, tmp_path):
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.upsert_session("sess1", role="developer")  # pre-create session
        parsed = {
            "claude_session_id": "uuid-xyz",
            "started_at": "2026-03-15T10:00:00Z",
            "ended_at": "2026-03-15T11:00:00Z",
            "tool_calls": [],
            "token_usage": [],
        }
        save_to_db(bus, "sess1", parsed, role="developer", transcript_path="/path/uuid-xyz.jsonl")
        trace = bus.get_session_trace("sess1")
        assert trace["session"]["claude_session_id"] == "uuid-xyz"

    def test_saves_tool_calls(self, tmp_path):
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.upsert_session("sess1", role="developer")
        parsed = {
            "claude_session_id": "uuid-xyz",
            "started_at": "2026-03-15T10:00:00Z",
            "ended_at": "2026-03-15T11:00:00Z",
            "tool_calls": [
                {"tool_name": "Read", "input_summary": "file.md", "is_error": 0, "tokens_out": 100, "timestamp": "2026-03-15T10:00:01Z"},
                {"tool_name": "Bash", "input_summary": "cmd", "is_error": 1, "tokens_out": 50, "timestamp": "2026-03-15T10:00:02Z"},
            ],
            "token_usage": [],
        }
        save_to_db(bus, "sess1", parsed)
        trace = bus.get_session_trace("sess1")
        assert len(trace["tool_calls"]) == 2
        assert trace["tool_calls"][1]["is_error"] == 1

    def test_no_duplicate_conversation_on_reparse(self, tmp_path):
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.upsert_session("sess1", role="developer")
        parsed = {
            "claude_session_id": "uuid-xyz",
            "started_at": "2026-03-15T10:00:00Z",
            "ended_at": "2026-03-15T11:00:00Z",
            "tool_calls": [],
            "token_usage": [],
            "messages": [
                {"speaker": "human", "content": "hello"},
                {"speaker": "assistant", "content": "hi there"},
            ],
        }
        save_to_db(bus, "sess1", parsed)
        save_to_db(bus, "sess1", parsed)  # second parse — should NOT duplicate
        entries = bus.get_conversation("sess1")
        assert len(entries) == 2  # not 4

    def test_saves_token_usage(self, tmp_path):
        bus = AgentBus(db_path=str(tmp_path / "test.db"))
        bus.upsert_session("sess1", role="developer")
        parsed = {
            "claude_session_id": "uuid-xyz",
            "started_at": "2026-03-15T10:00:00Z",
            "ended_at": "2026-03-15T11:00:00Z",
            "tool_calls": [],
            "token_usage": [
                {"turn_index": 0, "input_tokens": 1000, "output_tokens": 200,
                 "cache_read_tokens": 500, "cache_create_tokens": 300, "duration_ms": 4000,
                 "timestamp": "2026-03-15T10:00:00Z"},
            ],
        }
        save_to_db(bus, "sess1", parsed)
        trace = bus.get_session_trace("sess1")
        assert len(trace["token_usage"]) == 1
        assert trace["token_usage"][0]["input_tokens"] == 1000
        assert trace["token_usage"][0]["duration_ms"] == 4000
