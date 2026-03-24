#!/usr/bin/env python3
"""
Migration: Add workflow_execution and step_log tables.
Backlog #153 — Wielowarstwowe progress logi.

Usage:
  python tools/migration_workflow_tracking.py           # dry run
  python tools/migration_workflow_tracking.py --execute # apply
"""

import sqlite3
import sys
import json

DB_PATH = "mrowisko.db"

TABLES_SQL = """
CREATE TABLE IF NOT EXISTS workflow_execution (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id     TEXT NOT NULL,
    role            TEXT NOT NULL,
    session_id      TEXT,
    status          TEXT NOT NULL DEFAULT 'running',
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    CHECK (status IN ('running', 'completed', 'interrupted', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_workflow_execution_role_status ON workflow_execution(role, status);

CREATE TABLE IF NOT EXISTS step_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id    INTEGER NOT NULL,
    step_id         TEXT NOT NULL,
    step_index      INTEGER,
    status          TEXT NOT NULL,
    output_summary  TEXT,
    output_json     TEXT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (execution_id) REFERENCES workflow_execution(id),
    CHECK (status IN ('PASS', 'FAIL', 'BLOCKED', 'SKIPPED', 'IN_PROGRESS'))
);

CREATE INDEX IF NOT EXISTS idx_step_log_execution ON step_log(execution_id);
"""


def table_exists(conn, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def migrate(execute: bool = False):
    conn = sqlite3.connect(DB_PATH)

    # Check existing tables
    we_exists = table_exists(conn, "workflow_execution")
    sl_exists = table_exists(conn, "step_log")

    if we_exists and sl_exists:
        return {"ok": True, "status": "skip", "reason": "Tables already exist"}

    if not execute:
        return {
            "ok": True,
            "mode": "dry_run",
            "workflow_execution_exists": we_exists,
            "step_log_exists": sl_exists,
            "message": "Use --execute to create tables"
        }

    try:
        conn.executescript(TABLES_SQL)
        conn.commit()
        conn.close()
        return {"ok": True, "status": "applied", "message": "Tables created"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    execute = "--execute" in sys.argv
    result = migrate(execute)
    print(json.dumps(result, indent=2))
