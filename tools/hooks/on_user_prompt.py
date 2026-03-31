"""Hook: UserPromptSubmit — captures user messages to conversation table.

Identity Redesign: heartbeat uses MROWISKO_SPAWN_TOKEN env var (deterministic)
or claude_uuid from payload (fallback for manual sessions). No shared files.
Also runs inline GC to auto-stop dead sessions (>10 min no heartbeat).
"""

import io
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force UTF-8 on stdin (Windows default may be cp1250/cp852)
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

DEBUG_FILE = PROJECT_ROOT / "tmp" / "hook_user_prompt_debug.json"


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}

        # Always dump for debugging
        DEBUG_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        prompt_text = payload.get("prompt") or payload.get("message") or str(payload)
        claude_uuid = payload.get("session_id") or ""
        spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN", "")

        from tools.lib.agent_bus import AgentBus
        bus = AgentBus(db_path=str(PROJECT_ROOT / "mrowisko.db"))

        # Resolve mrowisko session_id for conversation logging
        session_id = None
        if spawn_token:
            row = bus._conn.execute(
                "SELECT session_id FROM live_agents WHERE spawn_token = ?",
                (spawn_token,),
            ).fetchone()
            if row:
                session_id = row[0]
        if not session_id and claude_uuid:
            row = bus._conn.execute(
                "SELECT session_id FROM live_agents WHERE claude_uuid = ?",
                (claude_uuid,),
            ).fetchone()
            if row:
                session_id = row[0]

        bus.add_conversation_entry(
            speaker="human",
            content=prompt_text[:2000],
            event_type="user_prompt",
            session_id=session_id,
            raw_payload=raw[:4000],
        )

        # Heartbeat: update last_activity for active agents only.
        # Revival from stopped is handled by pre_tool_use (actual tool usage).
        if spawn_token:
            bus._conn.execute(
                """UPDATE live_agents SET last_activity = datetime('now', 'localtime')
                   WHERE spawn_token = ? AND status IN ('starting', 'active')""",
                (spawn_token,),
            )
        elif claude_uuid:
            bus._conn.execute(
                """UPDATE live_agents SET last_activity = datetime('now', 'localtime')
                   WHERE claude_uuid = ? AND status IN ('starting', 'active')""",
                (claude_uuid,),
            )

        # GC: auto-stop dead sessions (no heartbeat for >10 min)
        bus._conn.execute(
            """UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now', 'localtime')
               WHERE status IN ('active', 'starting')
                 AND last_activity IS NOT NULL
                 AND last_activity < datetime('now', '-10 minutes')""",
        )

        bus._conn.commit()

        # Refresh dashboard (fire-and-forget, skip if already rendering)
        if not os.environ.get("MROWISKO_DASHBOARD_RENDERING"):
            import subprocess
            env = os.environ.copy()
            env["MROWISKO_DASHBOARD_RENDERING"] = "1"
            subprocess.Popen(
                [sys.executable, str(PROJECT_ROOT / "tools" / "render_dashboard.py")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env=env,
            )

    except Exception as e:
        try:
            err_file = PROJECT_ROOT / "tmp" / "hook_user_prompt_error.txt"
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
