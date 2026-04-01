"""Read last messages from active agent's live transcript.

Usage:
    py tools/read_transcript.py                    # last active agent
    py tools/read_transcript.py --session-id UUID  # specific agent
    py tools/read_transcript.py --lines 30         # more lines
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "mrowisko.db"

# Derive Claude Code projects dir from project root path
# Claude Code format: C:\Users\foo\bar → C--Users-foo-bar
_root_str = str(PROJECT_ROOT).replace("\\", "/")
_project_key = _root_str.replace(":/", "--").replace("/", "-")
TRANSCRIPTS_DIR = Path.home() / ".claude" / "projects" / _project_key


def get_active_session_id() -> str | None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    r = conn.execute(
        "SELECT session_id FROM live_agents WHERE status='active' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return r["session_id"] if r else None


def resolve_claude_uuid(session_id: str) -> str:
    """Resolve session_id to claude_uuid (transcript filename). Falls back to session_id."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    r = conn.execute(
        "SELECT claude_uuid FROM live_agents WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return r["claude_uuid"] if r and r["claude_uuid"] else session_id


def read_transcript(session_id: str, lines: int = 20):
    claude_uuid = resolve_claude_uuid(session_id)
    transcript = TRANSCRIPTS_DIR / f"{claude_uuid}.jsonl"
    if not transcript.exists():
        print(json.dumps({"ok": False, "error": f"Transcript not found: {transcript}"}))
        return

    all_lines = transcript.read_text(encoding="utf-8").strip().split("\n")
    messages = []
    for line in all_lines[-lines:]:
        d = json.loads(line)
        t = d.get("type", "")
        if t == "assistant":
            for block in d.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    messages.append({"role": "agent", "text": block["text"][:500]})
        elif t == "user":
            msg = d.get("message", {}).get("content", "")
            if isinstance(msg, str) and msg.strip():
                messages.append({"role": "human", "text": msg[:300]})
            elif isinstance(msg, list):
                for b in msg:
                    if isinstance(b, dict) and b.get("type") == "text":
                        messages.append({"role": "human", "text": b["text"][:300]})

    print(json.dumps({"ok": True, "session_id": session_id, "messages": messages}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Read agent transcript")
    parser.add_argument("--session-id", help="Agent session ID (default: last active)")
    parser.add_argument("--lines", type=int, default=20, help="How many transcript lines to scan")
    parser.add_argument("--pretty", action="store_true", help="Human-readable output")
    args = parser.parse_args()

    sid = args.session_id or get_active_session_id()
    if not sid:
        print(json.dumps({"ok": False, "error": "No active agent found"}))
        sys.exit(1)

    if args.pretty:
        claude_uuid = resolve_claude_uuid(sid)
        transcript = TRANSCRIPTS_DIR / f"{claude_uuid}.jsonl"
        if not transcript.exists():
            print(f"Transcript not found: {transcript}")
            return
        all_lines = transcript.read_text(encoding="utf-8").strip().split("\n")
        for line in all_lines[-args.lines:]:
            d = json.loads(line)
            t = d.get("type", "")
            if t == "assistant":
                for block in d.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        print(f"AGENT: {block['text'][:500]}")
            elif t == "user":
                msg = d.get("message", {}).get("content", "")
                if isinstance(msg, str) and msg.strip():
                    print(f"HUMAN: {msg[:300]}")
    else:
        read_transcript(sid, args.lines)


if __name__ == "__main__":
    main()
