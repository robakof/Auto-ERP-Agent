"""Tests for conversation_search.py — search and browse conversation history."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversation (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT,
    speaker     TEXT NOT NULL,
    content     TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    raw_payload TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(DB_SCHEMA)
    rows = [
        ("sess-aaa", "user",      "Jak zbudować widok TraNag?",           "user_message",      "2026-03-14 10:00:00"),
        ("sess-aaa", "assistant", "Zaczynam od discovery tabeli CDN.TraNag.", "assistant_message", "2026-03-14 10:01:00"),
        ("sess-aaa", "user",      "Sprawdź prefiksy dokumentów.",          "user_message",      "2026-03-14 10:02:00"),
        ("sess-aaa", "assistant", "Prefiksy: (s) sprzedaż, (A) zakup.",    "assistant_message", "2026-03-14 10:03:00"),
        ("sess-bbb", "user",      "Zrób widok dla Kontrahentów.",          "user_message",      "2026-03-15 09:00:00"),
        ("sess-bbb", "assistant", "Widok KntKarty gotowy — 143 kolumny.",  "assistant_message", "2026-03-15 09:05:00"),
    ]
    conn.executemany(
        "INSERT INTO conversation (session_id, speaker, content, event_type, created_at) VALUES (?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return db_path


def run(args, db_path):
    result = subprocess.run(
        [sys.executable, "tools/conversation_search.py"] + args + ["--db", str(db_path)],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)


class TestList:
    def test_returns_sessions(self, db):
        out = run(["--list"], db)
        assert out["ok"]
        assert len(out["data"]) == 2

    def test_session_has_stats(self, db):
        out = run(["--list"], db)
        sess = next(s for s in out["data"] if s["session_id"] == "sess-aaa")
        assert sess["message_count"] == 4
        assert sess["total_chars"] > 0
        assert "date" in sess

    def test_sorted_newest_first(self, db):
        out = run(["--list"], db)
        dates = [s["date"] for s in out["data"]]
        assert dates == sorted(dates, reverse=True)


class TestQuery:
    def test_finds_keyword(self, db):
        out = run(["--query", "TraNag"], db)
        assert out["ok"]
        assert len(out["data"]) > 0

    def test_result_fields(self, db):
        out = run(["--query", "TraNag"], db)
        r = out["data"][0]
        assert "session_id" in r
        assert "speaker" in r
        assert "date" in r
        assert "char_count" in r
        assert "snippet" in r

    def test_snippet_max_150_chars(self, db):
        out = run(["--query", "TraNag"], db)
        for r in out["data"]:
            assert len(r["snippet"]) <= 150

    def test_case_insensitive(self, db):
        out = run(["--query", "tranag"], db)
        assert len(out["data"]) > 0

    def test_no_results(self, db):
        out = run(["--query", "nieistniejaceslowo123"], db)
        assert out["ok"]
        assert out["data"] == []

    def test_limit(self, db):
        out = run(["--query", "a", "--limit", "2"], db)
        assert len(out["data"]) <= 2

    def test_returns_message_count(self, db):
        out = run(["--query", "TraNag"], db)
        assert "count" in out


class TestSession:
    def test_returns_all_messages(self, db):
        out = run(["--session", "sess-aaa"], db)
        assert out["ok"]
        assert len(out["data"]["messages"]) == 4

    def test_message_fields(self, db):
        out = run(["--session", "sess-aaa"], db)
        msg = out["data"]["messages"][0]
        assert "speaker" in msg
        assert "content" in msg
        assert "date" in msg

    def test_sorted_oldest_first(self, db):
        out = run(["--session", "sess-aaa"], db)
        dates = [m["date"] for m in out["data"]["messages"]]
        assert dates == sorted(dates)

    def test_unknown_session(self, db):
        out = run(["--session", "sess-xxx"], db)
        assert out["ok"]
        assert out["data"]["messages"] == []

    def test_includes_session_stats(self, db):
        out = run(["--session", "sess-aaa"], db)
        assert "message_count" in out["data"]
        assert "total_chars" in out["data"]
