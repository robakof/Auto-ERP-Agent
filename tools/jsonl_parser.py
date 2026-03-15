"""Parser transkryptów sesji Claude Code (.jsonl) → mrowisko.db.

Parsuje:
- sessions: metadane sesji (claude_session_id, started_at, ended_at)
- tool_calls: wywołania narzędzi per sesja (name, input_summary, is_error, tokens_out)
- token_usage: zużycie tokenów per tura asystenta

Użycie:
    python tools/jsonl_parser.py <transcript_path> --session-id <our_session_id>
    python tools/jsonl_parser.py <transcript_path> --session-id <our_session_id> --db mrowisko.db
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.agent_bus import AgentBus

DB_PATH = "mrowisko.db"

INPUT_SUMMARY_KEYS = ["file_path", "command", "pattern", "query", "path", "prompt", "url"]
INPUT_SUMMARY_MAX = 200


def _input_summary(tool_input: dict) -> str:
    """Extract meaningful summary from tool input dict."""
    for key in INPUT_SUMMARY_KEYS:
        if key in tool_input:
            return str(tool_input[key])[:INPUT_SUMMARY_MAX]
    raw = json.dumps(tool_input, ensure_ascii=False)
    return raw[:INPUT_SUMMARY_MAX]


def parse_jsonl(transcript_path: str) -> dict:
    """Parse a .jsonl transcript file into structured data.

    Returns:
        {
            "claude_session_id": str,
            "started_at": str,
            "ended_at": str,
            "tool_calls": list[dict],  # {tool_name, input_summary, is_error, tokens_out, timestamp}
            "token_usage": list[dict], # {turn_index, input_tokens, output_tokens, ...}
        }
    """
    path = Path(transcript_path)
    lines = path.read_text(encoding="utf-8").splitlines()

    claude_session_id = None
    started_at = None
    ended_at = None

    # Maps built in first pass
    tool_error_map: dict[str, bool] = {}   # tool_use_id → is_error
    duration_map: dict[str, int] = {}      # assistant uuid → duration_ms (from parentUuid)

    assistant_turns: list[dict] = []

    for line in lines:
        if not line.strip():
            continue
        obj = json.loads(line)
        t = obj.get("type")
        ts = obj.get("timestamp")

        if claude_session_id is None:
            claude_session_id = obj.get("sessionId")
        if ts:
            if started_at is None:
                started_at = ts
            ended_at = ts

        if t == "user":
            msg = obj.get("message", {})
            for c in msg.get("content", []):
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    tool_use_id = c.get("tool_use_id")
                    if tool_use_id:
                        tool_error_map[tool_use_id] = bool(c.get("is_error"))

        elif t == "system" and obj.get("subtype") == "turn_duration":
            parent = obj.get("parentUuid")
            if parent and "durationMs" in obj:
                duration_map[parent] = obj["durationMs"]

        elif t == "assistant":
            msg = obj.get("message", {})
            content = msg.get("content", [])
            if any(isinstance(c, dict) and c.get("type") in ("tool_use", "text") for c in content):
                assistant_turns.append({
                    "uuid": obj.get("uuid"),
                    "timestamp": ts,
                    "content": content,
                    "usage": msg.get("usage", {}),
                })

    tool_calls = []
    token_usage = []

    for turn_index, turn in enumerate(assistant_turns):
        usage = turn["usage"]
        if usage:
            token_usage.append({
                "turn_index": turn_index,
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "cache_read_tokens": usage.get("cache_read_input_tokens"),
                "cache_create_tokens": usage.get("cache_creation_input_tokens"),
                "duration_ms": duration_map.get(turn["uuid"]),
                "timestamp": turn["timestamp"],
            })

        tokens_out = usage.get("output_tokens") if usage else None
        for c in turn["content"]:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                tool_id = c.get("id", "")
                is_err = tool_error_map.get(tool_id, False)
                tool_calls.append({
                    "tool_name": c.get("name", ""),
                    "input_summary": _input_summary(c.get("input", {})),
                    "is_error": 1 if is_err else 0,
                    "tokens_out": tokens_out,
                    "timestamp": turn["timestamp"],
                })

    return {
        "claude_session_id": claude_session_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "tool_calls": tool_calls,
        "token_usage": token_usage,
    }


def save_to_db(
    bus: AgentBus,
    our_session_id: str,
    parsed: dict,
    role: str = None,
    transcript_path: str = None,
) -> None:
    """Write parsed transcript data to mrowisko.db."""
    bus.upsert_session(
        session_id=our_session_id,
        role=role,
        claude_session_id=parsed["claude_session_id"],
        transcript_path=transcript_path,
        ended_at=parsed["ended_at"],
    )
    for tc in parsed["tool_calls"]:
        bus.add_tool_call(
            session_id=our_session_id,
            tool_name=tc["tool_name"],
            input_summary=tc["input_summary"],
            is_error=tc["is_error"],
            tokens_out=tc["tokens_out"],
            timestamp=tc["timestamp"],
        )
    for tu in parsed["token_usage"]:
        bus.add_token_usage(
            session_id=our_session_id,
            turn_index=tu["turn_index"],
            input_tokens=tu["input_tokens"],
            output_tokens=tu["output_tokens"],
            cache_read_tokens=tu["cache_read_tokens"],
            cache_create_tokens=tu["cache_create_tokens"],
            duration_ms=tu["duration_ms"],
            timestamp=tu["timestamp"],
        )


def main():
    parser = argparse.ArgumentParser(description="Parse .jsonl transcript to mrowisko.db")
    parser.add_argument("transcript_path", help="Path to .jsonl file")
    parser.add_argument("--session-id", required=True, help="Our session ID (12 hex from session_init)")
    parser.add_argument("--role", help="Agent role for this session")
    parser.add_argument("--db", default=DB_PATH)
    args = parser.parse_args()

    parsed = parse_jsonl(args.transcript_path)
    bus = AgentBus(db_path=args.db)
    save_to_db(bus, args.session_id, parsed, role=args.role, transcript_path=args.transcript_path)

    from tools.lib.output import print_json
    print_json({
        "ok": True,
        "session_id": args.session_id,
        "claude_session_id": parsed["claude_session_id"],
        "tool_calls": len(parsed["tool_calls"]),
        "token_usage_turns": len(parsed["token_usage"]),
    })


if __name__ == "__main__":
    main()
