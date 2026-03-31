"""Hook: SessionEnd — marks agent as stopped in live_agents table.

Identity Redesign: matches by spawn_token (env) or claude_uuid (payload).
No shared file fallback.
"""

import io
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "mrowisko.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=3000")
    return conn


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}

        claude_uuid = payload.get("session_id", "")
        transcript_path = payload.get("transcript_path", "")
        spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN", "")

        if not claude_uuid and not spawn_token:
            return

        conn = _connect()

        updated = 0
        if spawn_token:
            cur = conn.execute(
                """UPDATE live_agents
                   SET status = 'stopped',
                       stopped_at = datetime('now', 'localtime'),
                       transcript_path = COALESCE(?, transcript_path)
                   WHERE spawn_token = ? AND status != 'stopped'""",
                (transcript_path or None, spawn_token),
            )
            updated = cur.rowcount

        if updated == 0 and claude_uuid:
            conn.execute(
                """UPDATE live_agents
                   SET status = 'stopped',
                       stopped_at = datetime('now', 'localtime'),
                       transcript_path = COALESCE(?, transcript_path)
                   WHERE claude_uuid = ? AND status != 'stopped'""",
                (transcript_path or None, claude_uuid),
            )

        conn.commit()
        conn.close()

    except Exception as e:
        try:
            err_file = PROJECT_ROOT / "tmp" / "hook_session_end_error.txt"
            err_file.parent.mkdir(parents=True, exist_ok=True)
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
