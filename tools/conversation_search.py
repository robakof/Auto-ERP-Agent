"""conversation_search.py — search and browse agent conversation history.

Usage:
  python tools/conversation_search.py --list [--limit N] [--db PATH]
  python tools/conversation_search.py --query "keyword" [--limit N] [--db PATH]
  python tools/conversation_search.py --session <session_id> [--db PATH]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_DB = Path(__file__).parent.parent / "mrowisko.db"
SNIPPET_LEN = 150


def _conn(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def cmd_list(db_path, limit):
    with _conn(db_path) as conn:
        rows = conn.execute("""
            SELECT
                session_id,
                MIN(created_at)      AS date,
                COUNT(*)             AS message_count,
                SUM(LENGTH(content)) AS total_chars
            FROM conversation
            GROUP BY session_id
            ORDER BY date DESC
            LIMIT ?
        """, (limit,)).fetchall()
    data = [
        {
            "session_id":    r["session_id"],
            "date":          r["date"],
            "message_count": r["message_count"],
            "total_chars":   r["total_chars"],
        }
        for r in rows
    ]
    return {"ok": True, "data": data, "count": len(data)}


def cmd_query(db_path, query, limit):
    pattern = f"%{query}%"
    with _conn(db_path) as conn:
        rows = conn.execute("""
            SELECT session_id, speaker, content, created_at
            FROM conversation
            WHERE content LIKE ? COLLATE NOCASE
            ORDER BY created_at DESC
            LIMIT ?
        """, (pattern, limit)).fetchall()
    data = [
        {
            "session_id": r["session_id"],
            "speaker":    r["speaker"],
            "date":       r["created_at"],
            "char_count": len(r["content"]),
            "snippet":    r["content"][:SNIPPET_LEN],
        }
        for r in rows
    ]
    return {"ok": True, "data": data, "count": len(data)}


def cmd_session(db_path, session_id):
    with _conn(db_path) as conn:
        rows = conn.execute("""
            SELECT speaker, content, created_at
            FROM conversation
            WHERE session_id = ?
            ORDER BY created_at ASC
        """, (session_id,)).fetchall()
    messages = [
        {
            "speaker": r["speaker"],
            "content": r["content"],
            "date":    r["created_at"],
        }
        for r in rows
    ]
    total_chars = sum(len(m["content"]) for m in messages)
    return {
        "ok": True,
        "data": {
            "session_id":    session_id,
            "message_count": len(messages),
            "total_chars":   total_chars,
            "messages":      messages,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Search agent conversation history")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to mrowisko.db")
    parser.add_argument("--limit", type=int, default=10)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list",    action="store_true", help="List sessions with stats")
    group.add_argument("--query",   metavar="KEYWORD",   help="Search messages by keyword")
    group.add_argument("--session", metavar="SESSION_ID", help="Full conversation for a session")

    args = parser.parse_args()
    db_path = Path(args.db)

    if args.list:
        result = cmd_list(db_path, args.limit)
    elif args.query:
        result = cmd_query(db_path, args.query, args.limit)
    else:
        result = cmd_session(db_path, args.session)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
