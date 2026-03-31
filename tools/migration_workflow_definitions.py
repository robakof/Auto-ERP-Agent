#!/usr/bin/env python3
"""
Migration: Add workflow definition tables for Workflow Enforcement (ADR-002 D1).

Tables: workflow_definitions, workflow_steps, workflow_decisions, workflow_exit_gates.
These store parsed workflow .md files as DB-native definitions consumed by the state machine engine.

Usage:
  python tools/migration_workflow_definitions.py           # dry run
  python tools/migration_workflow_definitions.py --execute # apply
"""

import json
import sqlite3
import sys

DB_PATH = "mrowisko.db"

TABLES = ["workflow_definitions", "workflow_steps", "workflow_decisions", "workflow_exit_gates"]

TABLES_SQL = """
-- Definicja workflow (1 row per workflow version)
CREATE TABLE IF NOT EXISTS workflow_definitions (
    workflow_id   TEXT NOT NULL,
    version       TEXT NOT NULL,
    owner_role    TEXT NOT NULL,
    trigger_desc  TEXT,
    status        TEXT DEFAULT 'active' CHECK (status IN ('active', 'deprecated')),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workflow_id, version)
);

-- Kroki workflow (building blocks)
CREATE TABLE IF NOT EXISTS workflow_steps (
    id                INTEGER PRIMARY KEY,
    workflow_id       TEXT NOT NULL,
    workflow_version  TEXT NOT NULL,
    step_id           TEXT NOT NULL,
    phase             TEXT,
    sort_order        INTEGER NOT NULL,
    action            TEXT NOT NULL,
    tool              TEXT,
    command           TEXT,
    verification_type  TEXT,
    verification_value TEXT,
    on_failure_retry   INTEGER DEFAULT 0,
    on_failure_skip    INTEGER DEFAULT 0,
    on_failure_escalate INTEGER DEFAULT 1,
    on_failure_reason  TEXT,
    next_step_pass    TEXT,
    next_step_fail    TEXT,
    is_handoff        INTEGER DEFAULT 0,
    handoff_to        TEXT,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version),
    UNIQUE (workflow_id, workflow_version, step_id)
);

-- Decision points
CREATE TABLE IF NOT EXISTS workflow_decisions (
    id               INTEGER PRIMARY KEY,
    workflow_id      TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    decision_id      TEXT NOT NULL,
    condition        TEXT NOT NULL,
    path_true        TEXT NOT NULL,
    path_false       TEXT NOT NULL,
    default_action   TEXT,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version)
);

-- Exit gates (checklist items per phase)
CREATE TABLE IF NOT EXISTS workflow_exit_gates (
    id               INTEGER PRIMARY KEY,
    workflow_id      TEXT NOT NULL,
    workflow_version TEXT NOT NULL,
    phase            TEXT NOT NULL,
    item_id          TEXT NOT NULL,
    condition        TEXT NOT NULL,
    FOREIGN KEY (workflow_id, workflow_version)
        REFERENCES workflow_definitions(workflow_id, version)
);
"""


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def migrate(execute: bool = False) -> dict:
    conn = sqlite3.connect(DB_PATH)
    existing = {t: table_exists(conn, t) for t in TABLES}

    if all(existing.values()):
        conn.close()
        return {"ok": True, "status": "skip", "reason": "All tables already exist"}

    if not execute:
        conn.close()
        return {
            "ok": True,
            "mode": "dry_run",
            "tables": existing,
            "message": "Use --execute to create tables",
        }

    try:
        conn.executescript(TABLES_SQL)
        conn.commit()
        created = [t for t, exists in existing.items() if not exists]
        conn.close()
        return {"ok": True, "status": "applied", "created": created}
    except Exception as e:
        conn.close()
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    execute = "--execute" in sys.argv
    result = migrate(execute)
    print(json.dumps(result, indent=2))
