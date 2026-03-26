"""Hook: SessionEnd — marks agent as stopped in live_agents table.

Observability-only hook. Fires when a Claude Code session terminates.
Only affects agents pre-registered by the launcher (spawned agents).
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

        session_id = payload.get("session_id") or _read_session_id()
        if not session_id:
            return

        transcript_path = payload.get("transcript_path", "")

        conn = _connect()
        conn.execute(
            """UPDATE live_agents
               SET status = 'stopped',
                   stopped_at = datetime('now'),
                   transcript_path = COALESCE(?, transcript_path)
               WHERE session_id = ? AND status != 'stopped'""",
            (transcript_path or None, session_id),
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
