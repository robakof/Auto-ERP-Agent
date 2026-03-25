"""Migrate state table to suggestions, backlog, session_log.

Mapping:
    state type=backlog_item  -> backlog (status=planned)
    state type=reflection    -> suggestions (status=open)
    state type=progress      -> session_log  (currently 0 rows)
"""

import json
import re
import sqlite3
import sys

DB_PATH = "mrowisko.db"


def extract_title(content: str) -> str:
    """Extract title from '### [Area] Title' pattern or use first line."""
    first_line = content.strip().splitlines()[0] if content.strip() else "Bez tytułu"
    match = re.match(r"^###\s+(?:\[[^\]]+\]\s+)?(.+)$", first_line)
    if match:
        return match.group(1).strip()
    return first_line[:120].strip()


def migrate(db_path: str = DB_PATH, dry_run: bool = False) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    rows = conn.execute(
        "SELECT id, role, type, content, session_id, created_at, metadata FROM state ORDER BY id ASC"
    ).fetchall()

    backlog_count = 0
    suggestions_count = 0
    session_log_count = 0

    for row in rows:
        content = row["content"]
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        created_at = row["created_at"]

        if row["type"] == "backlog_item":
            title = extract_title(content)
            area = meta.get("area")
            value = meta.get("value")
            effort = meta.get("effort")
            if not dry_run:
                conn.execute(
                    """INSERT INTO backlog (title, content, area, value, effort, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, 'planned', ?, ?)""",
                    (title, content, area, value, effort, created_at, created_at),
                )
            backlog_count += 1
            print(f"  backlog  [{row['id']:3}] {title[:70]}")

        elif row["type"] == "reflection":
            author = row["role"]
            if not dry_run:
                conn.execute(
                    """INSERT INTO suggestions (author, content, status, session_id, created_at)
                       VALUES (?, ?, 'open', ?, ?)""",
                    (author, content, row["session_id"], created_at),
                )
            suggestions_count += 1
            print(f"  suggest  [{row['id']:3}] {author}: {content[:60].strip()}")

        elif row["type"] == "progress":
            if not dry_run:
                conn.execute(
                    """INSERT INTO session_log (role, content, session_id, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (row["role"], content, row["session_id"], created_at),
                )
            session_log_count += 1
            print(f"  log      [{row['id']:3}] {row['role']}: {content[:60].strip()}")

    if not dry_run:
        conn.commit()

    conn.close()

    print()
    print(f"backlog:     {backlog_count}")
    print(f"suggestions: {suggestions_count}")
    print(f"session_log: {session_log_count}")
    print(f"total:       {backlog_count + suggestions_count + session_log_count}")
    if dry_run:
        print("[DRY RUN — brak zmian w bazie]")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    db_path = DB_PATH
    for arg in sys.argv[1:]:
        if arg.startswith("--db="):
            db_path = arg.split("=", 1)[1]
    print(f"Migracja: {db_path}" + (" [DRY RUN]" if dry_run else ""))
    print()
    migrate(db_path=db_path, dry_run=dry_run)
