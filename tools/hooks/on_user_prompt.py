"""Hook: UserPromptSubmit — captures user messages to conversation table.

Claude Code sends JSON on stdin:
  {"prompt": "user message text", ...possibly more fields}

Writes to mrowisko.db conversation table.
Silently fails on any error (never blocks the agent).
"""

import io
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force UTF-8 on stdin (Windows default may be cp1250/cp852)
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

DEBUG_FILE = PROJECT_ROOT / "tmp" / "hook_user_prompt_debug.json"
SESSION_ID_FILE = PROJECT_ROOT / "tmp" / "session_id.txt"


def read_session_id() -> str | None:
    if SESSION_ID_FILE.exists():
        return SESSION_ID_FILE.read_text(encoding="utf-8").strip() or None
    return None


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}

        # Always dump for debugging (E2 experiment)
        DEBUG_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        prompt_text = payload.get("prompt") or payload.get("message") or str(payload)
        session_id = read_session_id()

        from tools.lib.agent_bus import AgentBus
        bus = AgentBus(db_path=str(PROJECT_ROOT / "mrowisko.db"))
        bus.add_conversation_entry(
            speaker="human",
            content=prompt_text[:2000],  # cap at 2000 chars
            event_type="user_prompt",
            session_id=session_id,
            raw_payload=raw[:4000],
        )

    except Exception as e:
        try:
            err_file = PROJECT_ROOT / "tmp" / "hook_user_prompt_error.txt"
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
