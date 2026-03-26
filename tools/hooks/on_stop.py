"""Hook: Stop — saves last assistant message and parses session transcript.

On session stop:
1. Saves last_assistant_message to conversation table
2. Parses .jsonl transcript → sessions/tool_calls/token_usage in mrowisko.db
"""

import io
import json
import sys
from pathlib import Path

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEBUG_FILE = PROJECT_ROOT / "tmp" / "hook_stop_debug.json"
SESSION_ID_FILE = PROJECT_ROOT / "tmp" / "session_id.txt"


def _read_session_id() -> str | None:
    if SESSION_ID_FILE.exists():
        return SESSION_ID_FILE.read_text(encoding="utf-8").strip() or None
    return None


def _save_last_message(bus, last_msg: str, session_id: str | None, raw: str) -> None:
    if not last_msg:
        return
    bus.add_conversation_entry(
        speaker="agent",
        content=str(last_msg)[:2000],
        event_type="agent_stop",
        session_id=session_id,
        raw_payload=raw[:4000],
    )


def _update_live_agent(bus, session_id: str | None, transcript_path: str) -> None:
    """Update last_activity and transcript_path in live_agents if agent is registered."""
    if not session_id:
        return
    try:
        bus._conn.execute(
            """UPDATE live_agents
               SET last_activity = datetime('now'),
                   transcript_path = COALESCE(?, transcript_path)
               WHERE session_id = ? AND status = 'active'""",
            (transcript_path or None, session_id),
        )
        bus._conn.commit()
    except Exception:
        pass  # Table may not exist yet


def _parse_transcript(bus, transcript_path: str, session_id: str | None) -> None:
    if not transcript_path or not session_id:
        return
    tp = Path(transcript_path)
    if not tp.exists():
        return
    sys.path.insert(0, str(PROJECT_ROOT))
    from tools.jsonl_parser import parse_jsonl, save_to_db
    parsed = parse_jsonl(transcript_path)
    save_to_db(bus, session_id, parsed, transcript_path=transcript_path)


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}

        session_id = _read_session_id()
        transcript_path = payload.get("transcript_path", "")

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

        sys.path.insert(0, str(PROJECT_ROOT))
        from tools.lib.agent_bus import AgentBus
        bus = AgentBus(db_path=str(PROJECT_ROOT / "mrowisko.db"))

        _save_last_message(bus, payload.get("last_assistant_message", ""), session_id, raw)
        _parse_transcript(bus, transcript_path, session_id)
        _update_live_agent(bus, session_id, transcript_path)


    except Exception as e:
        try:
            err_file = PROJECT_ROOT / "tmp" / "hook_stop_error.txt"
            err_file.parent.mkdir(parents=True, exist_ok=True)
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
