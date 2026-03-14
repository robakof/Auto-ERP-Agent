"""Hook: Stop — E3 experiment: dump everything to debug file.

Goal: discover what data Claude Code sends on session stop.
Does it include the agent's response? Full transcript? Just a signal?

Output: tmp/hook_stop_debug.json — inspect after session ends.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEBUG_FILE = PROJECT_ROOT / "tmp" / "hook_stop_debug.json"
SESSION_ID_FILE = PROJECT_ROOT / "tmp" / "session_id.txt"


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}

        session_id = None
        if SESSION_ID_FILE.exists():
            session_id = SESSION_ID_FILE.read_text(encoding="utf-8").strip() or None

        debug_data = {
            "session_id": session_id,
            "payload_keys": list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__,
            "payload": payload,
            "raw_length": len(raw),
        }

        DEBUG_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_FILE.write_text(
            json.dumps(debug_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    except Exception as e:
        try:
            err_file = PROJECT_ROOT / "tmp" / "hook_stop_error.txt"
            err_file.parent.mkdir(parents=True, exist_ok=True)
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
