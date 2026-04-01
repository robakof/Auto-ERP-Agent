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


def _update_live_agent(bus, transcript_path: str, spawn_token: str = "", claude_uuid: str = "") -> None:
    """Update last_activity and transcript_path in live_agents if agent is registered."""
    if not spawn_token and not claude_uuid:
        return
    try:
        updated = 0
        if spawn_token:
            cur = bus._conn.execute(
                """UPDATE live_agents
                   SET last_activity = datetime('now', 'localtime'),
                       transcript_path = COALESCE(?, transcript_path)
                   WHERE spawn_token = ? AND status = 'active'""",
                (transcript_path or None, spawn_token),
            )
            updated = cur.rowcount
        if updated == 0 and claude_uuid:
            bus._conn.execute(
                """UPDATE live_agents
                   SET last_activity = datetime('now', 'localtime'),
                       transcript_path = COALESCE(?, transcript_path)
                   WHERE claude_uuid = ? AND status = 'active'""",
                (transcript_path or None, claude_uuid),
            )
        bus._conn.commit()
    except Exception:
        pass


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

        import os
        spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN", "")
        transcript_path = payload.get("transcript_path", "")

        debug_data = {
            "spawn_token": spawn_token,
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

        claude_uuid = payload.get("session_id", "")

        # Resolve mrowisko session_id via public AgentBus method
        session_id = bus.resolve_session_id(spawn_token=spawn_token, claude_uuid=claude_uuid)

        _save_last_message(bus, payload.get("last_assistant_message", ""), session_id, raw)
        _parse_transcript(bus, transcript_path, session_id)
        _update_live_agent(bus, transcript_path, spawn_token=spawn_token, claude_uuid=claude_uuid)


    except Exception as e:
        try:
            err_file = PROJECT_ROOT / "tmp" / "hook_stop_error.txt"
            err_file.parent.mkdir(parents=True, exist_ok=True)
            err_file.write_text(str(e), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    main()
