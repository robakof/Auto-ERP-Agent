"""CLI helper for live_agents CRUD — called by VS Code extension via execSync.

Usage:
    py tools/agent_launcher_db.py insert --session-id UUID --role ROLE --task TASK --terminal-name NAME --permission-mode MODE --spawned-by WHO
    py tools/agent_launcher_db.py list-active
    py tools/agent_launcher_db.py mark-stopped --session-id UUID
    py tools/agent_launcher_db.py cleanup
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "mrowisko.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=3000")
    return conn


def cmd_insert(args):
    conn = _connect()
    conn.execute(
        """INSERT INTO live_agents (session_id, role, task, terminal_name, status, permission_mode, spawned_by)
           VALUES (?, ?, ?, ?, 'starting', ?, ?)""",
        (args.session_id, args.role, args.task, args.terminal_name, args.permission_mode, args.spawned_by),
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True}))


def cmd_list_active(args):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM live_agents WHERE status IN ('starting', 'active') ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    print(json.dumps({"ok": True, "data": result}))


def cmd_mark_stopped(args):
    conn = _connect()
    conn.execute(
        "UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now') WHERE session_id = ? AND status != 'stopped'",
        (args.session_id,),
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True}))


def cmd_cleanup(args):
    conn = _connect()
    cur = conn.execute(
        "UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now') WHERE status IN ('starting', 'active') AND last_activity < datetime('now', '-1 hour')"
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "cleaned": cur.rowcount}))


def main():
    parser = argparse.ArgumentParser(description="Live agents DB helper")
    sub = parser.add_subparsers(dest="command")

    p_insert = sub.add_parser("insert")
    p_insert.add_argument("--session-id", required=True)
    p_insert.add_argument("--role", required=True)
    p_insert.add_argument("--task", required=True)
    p_insert.add_argument("--terminal-name", required=True)
    p_insert.add_argument("--permission-mode", default="default")
    p_insert.add_argument("--spawned-by", default="human")

    sub.add_parser("list-active")

    p_stop = sub.add_parser("mark-stopped")
    p_stop.add_argument("--session-id", required=True)

    sub.add_parser("cleanup")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    handlers = {
        "insert": cmd_insert,
        "list-active": cmd_list_active,
        "mark-stopped": cmd_mark_stopped,
        "cleanup": cmd_cleanup,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
