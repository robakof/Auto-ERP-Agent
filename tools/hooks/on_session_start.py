"""Hook: SessionStart — registers agent in live_agents table.

Observability-only hook. Fires when a Claude Code session starts.
Updates live_agents status from 'starting' to 'active' if pre-registered,
or skips for manually started sessions (only spawned agents are tracked).
"""

import io
import json
import sqlite3
import sys
from pathlib import Path

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "mrowisko.db"
SESSION_ID_FILE = PROJECT_ROOT / "tmp" / "session_id.txt"


def _read_session_id() -> str | None:
    if SESSION_ID_FILE.exists():
        return SESSION_ID_FILE.read_text(encoding="utf-8").strip() or None
    return None


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

        # Write claude_uuid for session_init to pick up (bootstrap bridge)
        if claude_uuid:
            pending_file = PROJECT_ROOT / "tmp" / "pending_claude_uuid.txt"
            pending_file.parent.mkdir(parents=True, exist_ok=True)
            pending_file.write_text(claude_uuid, encoding="utf-8")

        file_session_id = _read_session_id()
        session_id = file_session_id or claude_uuid
        if not session_id:
            return

        conn = _connect()

        # Only update pre-registered agents (spawned by launcher, status='starting').
        # Manual sessions (started by human typing `claude`) are not tracked in live_agents.
        row = conn.execute(
            "SELECT id FROM live_agents WHERE session_id = ?",
            (session_id,),
        ).fetchone()

        if row:
            conn.execute(
                """UPDATE live_agents
                   SET status = 'active',
                       last_activity = datetime('now'),
                       claude_uuid = COALESCE(?, claude_uuid)
                   WHERE session_id = ?""",
                (claude_uuid or None, session_id),
            )
            conn.commit()

        conn.close()

    except Exception as e:
        try:
            err_file = PROJECT_ROOT / "tmp" / "hook_session_start_error.txt"
            err_file.parent.mkdir(parents=True, exist_ok=True)
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
