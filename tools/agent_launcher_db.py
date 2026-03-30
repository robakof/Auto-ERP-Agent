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
        """INSERT INTO live_agents (spawn_token, role, task, terminal_name, status, spawned_by)
           VALUES (?, ?, ?, ?, 'starting', ?)""",
        (args.spawn_token, args.role, args.task, args.terminal_name, args.spawned_by),
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
        "UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now') WHERE status IN ('starting', 'active') AND last_activity IS NOT NULL AND last_activity < datetime('now', '-1 hour')"
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "cleaned": cur.rowcount}))


def cmd_pending_invocations(args):
    conn = _connect()
    rows = conn.execute(
        """SELECT i.*, la.terminal_name AS agent_terminal_name,
                  la.claude_uuid AS agent_claude_uuid
           FROM invocations i
           LEFT JOIN live_agents la ON i.target_session_id = la.session_id
           WHERE i.status = 'pending'
           ORDER BY i.created_at ASC"""
    ).fetchall()
    conn.close()
    print(json.dumps({"ok": True, "data": [dict(r) for r in rows]}))


def cmd_approve_invocation(args):
    conn = _connect()
    conn.execute(
        "UPDATE invocations SET status = 'approved' WHERE id = ? AND status = 'pending'",
        (args.id,),
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True}))


def cmd_reject_invocation(args):
    conn = _connect()
    conn.execute(
        "UPDATE invocations SET status = 'rejected', ended_at = datetime('now') WHERE id = ? AND status = 'pending'",
        (args.id,),
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True}))


def cmd_complete_invocation(args):
    conn = _connect()
    conn.execute(
        "UPDATE invocations SET status = 'completed', ended_at = datetime('now') WHERE id = ?",
        (args.id,),
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True}))


def main():
    parser = argparse.ArgumentParser(description="Live agents DB helper")
    sub = parser.add_subparsers(dest="command")

    p_insert = sub.add_parser("insert")
    p_insert.add_argument("--spawn-token", required=True)
    p_insert.add_argument("--role", required=True)
    p_insert.add_argument("--task", required=True)
    p_insert.add_argument("--terminal-name", required=True)
    p_insert.add_argument("--spawned-by", default="human")

    sub.add_parser("list-active")

    p_stop = sub.add_parser("mark-stopped")
    p_stop.add_argument("--session-id", required=True)

    sub.add_parser("cleanup")

    sub.add_parser("pending-invocations")

    p_approve = sub.add_parser("approve-invocation")
    p_approve.add_argument("--id", type=int, required=True)

    p_reject = sub.add_parser("reject-invocation")
    p_reject.add_argument("--id", type=int, required=True)

    p_complete = sub.add_parser("complete-invocation")
    p_complete.add_argument("--id", type=int, required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    handlers = {
        "insert": cmd_insert,
        "list-active": cmd_list_active,
        "mark-stopped": cmd_mark_stopped,
        "cleanup": cmd_cleanup,
        "pending-invocations": cmd_pending_invocations,
        "approve-invocation": cmd_approve_invocation,
        "reject-invocation": cmd_reject_invocation,
        "complete-invocation": cmd_complete_invocation,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
