"""Hook: PostToolUse — live zapis tool calls do DB po każdym wywołaniu narzędzia.

Cel: widoczność działania agentów w czasie rzeczywistym (nie post-session).
on_stop.py parsuje transcript dopiero po zakończeniu sesji — ten hook zapisuje natychmiast.

Payload od Claude Code (stdin JSON):
  {
    "tool_name": "Bash",
    "tool_input": {...},
    "tool_response": {
      "is_error": false,
      "content": [...]
    }
  }

session_id czytamy z tmp/session_id.txt (tak jak pozostałe hooki).
Env vars (do testów):
  MROWISKO_DB          — ścieżka do DB (domyślnie: PROJECT_ROOT/mrowisko.db)
  MROWISKO_SESSION_DIR — katalog z session_id.txt (domyślnie: PROJECT_ROOT/tmp)

Nigdy nie blokuje agenta — wszystkie błędy są ciche.
"""

import io
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

_DB_PATH = os.environ.get("MROWISKO_DB") or str(PROJECT_ROOT / "mrowisko.db")
_SESSION_DIR = Path(os.environ.get("MROWISKO_SESSION_DIR") or str(PROJECT_ROOT / "tmp"))
SESSION_ID_FILE = _SESSION_DIR / "session_id.txt"
DEBUG_FILE = PROJECT_ROOT / "tmp" / "hook_post_tool_use_debug.json"

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")


def _read_session_id() -> str | None:
    if SESSION_ID_FILE.exists():
        return SESSION_ID_FILE.read_text(encoding="utf-8").strip() or None
    return None


def _input_summary(tool_input: dict) -> str:
    """Zwraca skrót tool_input — maks. 200 znaków."""
    try:
        raw = json.dumps(tool_input, ensure_ascii=False)
    except Exception:
        raw = str(tool_input)
    return raw[:200]


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}

        DEBUG_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        tool_name: str = payload.get("tool_name", "unknown")
        tool_input: dict = payload.get("tool_input") or {}
        tool_response: dict = payload.get("tool_response") or {}
        is_error: int = int(bool(tool_response.get("is_error", False)))

        claude_uuid = payload.get("session_id") or ""
        file_session_id = _read_session_id()

        sys.path.insert(0, str(PROJECT_ROOT))
        from tools.lib.agent_bus import AgentBus
        bus = AgentBus(db_path=_DB_PATH)

        # Resolve mrowisko session_id: prefer claude_uuid lookup, fallback to file
        session_id = file_session_id
        if claude_uuid:
            row = bus._conn.execute(
                "SELECT session_id FROM live_agents WHERE claude_uuid = ? AND status != 'stopped'",
                (claude_uuid,),
            ).fetchone()
            if row:
                session_id = row[0]

        bus.add_tool_call(
            session_id=session_id,
            tool_name=tool_name,
            input_summary=_input_summary(tool_input),
            is_error=is_error,
        )

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
            err_file = PROJECT_ROOT / "tmp" / "hook_post_tool_use_error.txt"
            err_file.parent.mkdir(parents=True, exist_ok=True)
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
