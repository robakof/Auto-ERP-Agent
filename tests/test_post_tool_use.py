"""Tests for post_tool_use hook — live tool call recording."""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
HOOK_SCRIPT = PROJECT_ROOT / "tools" / "hooks" / "post_tool_use.py"


def _make_db(tmp_path: Path, session_ids: list[str] = None) -> Path:
    """Create a minimal mrowisko.db with required tables and optional seed sessions."""
    db_path = tmp_path / "mrowisko.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS tool_calls (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT REFERENCES sessions(id),
            tool_name     TEXT NOT NULL,
            input_summary TEXT,
            is_error      INTEGER NOT NULL DEFAULT 0,
            tokens_out    INTEGER,
            timestamp     TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS live_agents (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            claude_uuid     TEXT UNIQUE,
            session_id      TEXT,
            role            TEXT,
            status          TEXT NOT NULL DEFAULT 'active',
            spawn_token     TEXT,
            last_activity   TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            stopped_at      TEXT,
            terminal_name   TEXT,
            task            TEXT,
            spawned_by      TEXT,
            transcript_path TEXT
        );
    """)
    for sid in (session_ids or []):
        conn.execute("INSERT OR IGNORE INTO sessions (id) VALUES (?)", (sid,))
        # Also create live_agents entry so hook can resolve session_id
        conn.execute(
            "INSERT OR IGNORE INTO live_agents (claude_uuid, session_id, role, status) VALUES (?,?,?,?)",
            (sid, sid, "test", "active"),
        )
    conn.commit()
    conn.close()
    return db_path


def run_hook(payload: dict, tmp_path: Path, session_id: str = None) -> subprocess.CompletedProcess:
    session_dir = tmp_path / "tmp"
    session_dir.mkdir(exist_ok=True)
    if session_id:
        (session_dir / "session_id.txt").write_text(session_id, encoding="utf-8")

    db_path = tmp_path / "mrowisko.db"
    env = {
        **os.environ,
        "PYTHONPATH": str(PROJECT_ROOT),
        "MROWISKO_DB": str(db_path),
        "MROWISKO_SESSION_DIR": str(session_dir),
    }
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


class TestPostToolUseSmoke:
    def test_runs_without_error_on_empty_payload(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_db(tmp_path)
        result = run_hook({}, tmp_path)
        assert result.returncode == 0

    def test_records_tool_call_in_db(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        db_path = _make_db(tmp_path, session_ids=["test-session-123"])

        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "python tools/agent_bus_cli.py backlog --area Dev"},
            "tool_response": {"is_error": False, "content": []},
            "session_id": "test-session-123",
        }
        result = run_hook(payload, tmp_path, session_id="test-session-123")
        assert result.returncode == 0

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT tool_name, input_summary, is_error, session_id FROM tool_calls").fetchall()
        conn.close()

        assert len(rows) == 1
        tool_name, input_summary, is_error, session_id = rows[0]
        assert tool_name == "Bash"
        assert "agent_bus_cli" in input_summary
        assert is_error == 0
        assert session_id == "test-session-123"

    def test_records_error_flag(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        db_path = _make_db(tmp_path, session_ids=["test-session-456"])

        payload = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/nonexistent/file.txt"},
            "tool_response": {"is_error": True, "content": []},
            "session_id": "test-session-456",
        }
        result = run_hook(payload, tmp_path, session_id="test-session-456")
        assert result.returncode == 0

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT tool_name, is_error FROM tool_calls").fetchall()
        conn.close()

        assert len(rows) == 1
        assert rows[0][0] == "Read"
        assert rows[0][1] == 1

    def test_no_session_id_still_records(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        db_path = _make_db(tmp_path)

        payload = {
            "tool_name": "Glob",
            "tool_input": {"pattern": "**/*.py"},
            "tool_response": {"is_error": False},
        }
        result = run_hook(payload, tmp_path)  # bez session_id
        assert result.returncode == 0

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT tool_name, session_id FROM tool_calls").fetchall()
        conn.close()

        assert len(rows) == 1
        assert rows[0][0] == "Glob"
        assert rows[0][1] is None

    def test_input_summary_truncated_to_200(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        db_path = _make_db(tmp_path)

        long_command = "x" * 500
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": long_command},
            "tool_response": {"is_error": False},
        }
        result = run_hook(payload, tmp_path)
        assert result.returncode == 0

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT input_summary FROM tool_calls").fetchall()
        conn.close()

        assert len(rows[0][0]) <= 200
