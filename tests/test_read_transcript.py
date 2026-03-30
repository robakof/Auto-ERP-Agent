"""Tests for read_transcript.py — session_id → claude_uuid resolution."""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import after patching is set up
import tools.read_transcript as rt


@pytest.fixture
def tmp_env(tmp_path):
    """Create temp DB + transcript dir with known data."""
    db_path = tmp_path / "mrowisko.db"
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE live_agents (
            id INTEGER PRIMARY KEY,
            session_id TEXT,
            claude_uuid TEXT,
            status TEXT,
            transcript_path TEXT
        )"""
    )
    conn.execute(
        "INSERT INTO live_agents (session_id, claude_uuid, status) VALUES (?, ?, ?)",
        ("sess-abc", "uuid-123", "active"),
    )
    conn.execute(
        "INSERT INTO live_agents (session_id, claude_uuid, status) VALUES (?, ?, ?)",
        ("sess-def", None, "stopped"),
    )
    conn.commit()
    conn.close()

    # Create transcript file named after claude_uuid
    transcript = transcripts_dir / "uuid-123.jsonl"
    transcript.write_text(
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "hello"}]}}) + "\n",
        encoding="utf-8",
    )

    return db_path, transcripts_dir


def test_resolve_claude_uuid_found(tmp_env):
    db_path, _ = tmp_env
    with patch.object(rt, "DB_PATH", db_path):
        assert rt.resolve_claude_uuid("sess-abc") == "uuid-123"


def test_resolve_claude_uuid_fallback_when_null(tmp_env):
    db_path, _ = tmp_env
    with patch.object(rt, "DB_PATH", db_path):
        assert rt.resolve_claude_uuid("sess-def") == "sess-def"


def test_resolve_claude_uuid_fallback_when_missing(tmp_env):
    db_path, _ = tmp_env
    with patch.object(rt, "DB_PATH", db_path):
        assert rt.resolve_claude_uuid("nonexistent") == "nonexistent"


def test_read_transcript_uses_claude_uuid(tmp_env, capsys):
    db_path, transcripts_dir = tmp_env
    with patch.object(rt, "DB_PATH", db_path), patch.object(rt, "TRANSCRIPTS_DIR", transcripts_dir):
        rt.read_transcript("sess-abc", lines=10)
        out = json.loads(capsys.readouterr().out)
        assert out["ok"] is True
        assert out["session_id"] == "sess-abc"
        assert len(out["messages"]) == 1
        assert out["messages"][0]["text"] == "hello"


def test_read_transcript_not_found_without_resolve(tmp_env, capsys):
    """Without resolve, session_id file doesn't exist."""
    _, transcripts_dir = tmp_env
    # sess-abc.jsonl doesn't exist, only uuid-123.jsonl
    assert not (transcripts_dir / "sess-abc.jsonl").exists()
    assert (transcripts_dir / "uuid-123.jsonl").exists()
