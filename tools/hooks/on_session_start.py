"""Hook: SessionStart — links spawn_token to claude_uuid in live_agents.

Identity Redesign: uses MROWISKO_SPAWN_TOKEN env var (set by spawner)
to deterministically link the spawned record with the actual Claude Code session.
Manual sessions (no spawn_token) get inserted directly with claude_uuid.
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
        if not claude_uuid:
            return

        spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN", "")
        conn = _connect()

        if spawn_token:
            # Spawned agent: link claude_uuid to pre-registered record
            cur = conn.execute(
                """UPDATE live_agents
                   SET claude_uuid = ?,
                       status = 'active',
                       last_activity = datetime('now')
                   WHERE spawn_token = ? AND status = 'starting'""",
                (claude_uuid, spawn_token),
            )
            if cur.rowcount == 0:
                # Fallback for resume: spawn_token not pre-registered, but claude_uuid may exist
                # (e.g. resumeAgent created terminal with new spawn_token for existing conversation)
                cur2 = conn.execute(
                    """UPDATE live_agents
                       SET status = 'active',
                           last_activity = datetime('now'),
                           spawn_token = ?,
                           stopped_at = NULL
                       WHERE claude_uuid = ?""",
                    (spawn_token, claude_uuid),
                )
                if cur2.rowcount == 0:
                    # Completely new — insert
                    conn.execute(
                        """INSERT INTO live_agents (claude_uuid, spawn_token, status, spawned_by, last_activity)
                           VALUES (?, ?, 'active', 'manual', datetime('now'))""",
                        (claude_uuid, spawn_token),
                    )
        else:
            # Manual session: insert new record (or reactivate if claude_uuid exists)
            conn.execute(
                """INSERT INTO live_agents (claude_uuid, status, spawned_by, last_activity)
                   VALUES (?, 'active', 'manual', datetime('now'))
                   ON CONFLICT(claude_uuid) DO UPDATE SET
                     status = 'active',
                     last_activity = datetime('now'),
                     stopped_at = NULL""",
                (claude_uuid,),
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
