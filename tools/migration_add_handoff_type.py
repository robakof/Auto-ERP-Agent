#!/usr/bin/env python3
"""
Migration: Add 'handoff' to messages.type CHECK constraint.

Usage:
  python tools/migration_add_handoff_type.py           # dry run
  python tools/migration_add_handoff_type.py --execute # apply
"""

import sqlite3
import sys
import json

DB_PATH = "mrowisko.db"

NEW_CHECK = "CHECK (type IN ('direct', 'suggestion', 'task', 'escalation', 'flag_human', 'info', 'handoff'))"


def migrate(execute: bool = False):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")

    # Get current schema
    schema = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='messages'"
    ).fetchone()[0]

    # Check if handoff already in CHECK
    if "'handoff'" in schema:
        return {"ok": True, "status": "skip", "reason": "handoff already in CHECK"}

    # Build new schema
    old_check = "CHECK (type IN ('direct', 'suggestion', 'task', 'escalation', 'flag_human', 'info'))"
    new_schema = schema.replace(old_check, NEW_CHECK)
    new_schema = new_schema.replace("CREATE TABLE \"messages\"", "CREATE TABLE messages_new")

    if not execute:
        return {
            "ok": True,
            "mode": "dry_run",
            "old_check": old_check,
            "new_check": NEW_CHECK,
            "message": "Use --execute to apply"
        }

    # Execute migration
    try:
        conn.execute("BEGIN TRANSACTION")

        # Create new table
        conn.execute(new_schema)

        # Copy data
        conn.execute("""
            INSERT INTO messages_new
            SELECT * FROM messages
        """)

        # Swap tables
        conn.execute("DROP TABLE messages")
        conn.execute("ALTER TABLE messages_new RENAME TO messages")

        conn.execute("COMMIT")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

        return {"ok": True, "status": "applied", "message": "handoff type added to CHECK"}

    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    execute = "--execute" in sys.argv
    result = migrate(execute)
    print(json.dumps(result, indent=2))
