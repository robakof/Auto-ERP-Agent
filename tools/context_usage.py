"""Live context/token usage from Claude Code transcript.

Parses the live .jsonl transcript and sums token usage per turn.
Agents call this mid-session to know actual context consumption.

Usage:
    py tools/context_usage.py                    # current session (most recent transcript)
    py tools/context_usage.py --transcript PATH  # specific file
    py tools/context_usage.py --session-id UUID  # lookup from live_agents
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.jsonl_parser import parse_jsonl
from tools.lib.output import print_json

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "mrowisko.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "context_usage_config.json"

_root_str = str(PROJECT_ROOT).replace("\\", "/")
_project_key = _root_str.replace(":/", "--").replace("/", "-")
TRANSCRIPTS_DIR = Path.home() / ".claude" / "projects" / _project_key


MODEL_CONTEXT_WINDOWS = {
    "claude-opus-4-6": 1_000_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-4-5": 200_000,
}
DEFAULT_CONTEXT_WINDOW = 200_000


def _load_config() -> dict:
    """Load context window config. Falls back to defaults."""
    defaults = {"context_window": DEFAULT_CONTEXT_WINDOW}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            defaults.update(cfg)
        except Exception:
            pass
    return defaults


def _detect_context_window(transcript_path: str) -> int:
    """Detect context window from model name in transcript."""
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("type") == "assistant":
                model = obj.get("message", {}).get("model", "")
                for prefix, window in MODEL_CONTEXT_WINDOWS.items():
                    if model.startswith(prefix):
                        return window
                break
    return DEFAULT_CONTEXT_WINDOW


def find_latest_transcript() -> Path | None:
    """Find the most recently modified .jsonl transcript."""
    if not TRANSCRIPTS_DIR.exists():
        return None
    candidates = [
        p for p in TRANSCRIPTS_DIR.glob("*.jsonl")
        if p.stat().st_size > 100
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_transcript_by_session(session_id: str) -> Path | None:
    """Lookup transcript path from live_agents table."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT transcript_path FROM live_agents WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    if row and row["transcript_path"]:
        p = Path(row["transcript_path"])
        if p.exists():
            return p
    return None


def compute_usage(transcript_path: str) -> dict:
    """Parse transcript and compute token usage totals.

    Context window usage = last turn's input side (input + cache_read + cache_create),
    because each API call sends the full conversation history.
    Cumulative totals are for cost estimation.
    """
    parsed = parse_jsonl(transcript_path)
    token_entries = parsed.get("token_usage", [])

    cumulative = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_create_tokens": 0,
    }
    for entry in token_entries:
        for key in cumulative:
            cumulative[key] += entry.get(key) or 0

    # Last turn = current context window fill
    last = token_entries[-1] if token_entries else {}
    last_input = (last.get("input_tokens") or 0)
    last_cache_read = (last.get("cache_read_tokens") or 0)
    last_cache_create = (last.get("cache_create_tokens") or 0)
    current_context = last_input + last_cache_read + last_cache_create

    return {
        "turns": len(token_entries),
        "current_context_tokens": current_context,
        "cumulative": cumulative,
    }


def main():
    parser = argparse.ArgumentParser(description="Live context/token usage from transcript")
    parser.add_argument("--transcript", help="Path to .jsonl transcript file")
    parser.add_argument("--session-id", help="Lookup transcript from live_agents by session ID")
    args = parser.parse_args()

    if args.transcript:
        tp = Path(args.transcript)
    elif args.session_id:
        tp = find_transcript_by_session(args.session_id)
        if not tp:
            print_json({"ok": False, "error": f"No transcript found for session {args.session_id}"})
            sys.exit(1)
    else:
        tp = find_latest_transcript()
        if not tp:
            print_json({"ok": False, "error": "No transcript files found"})
            sys.exit(1)

    if not tp.exists():
        print_json({"ok": False, "error": f"Transcript not found: {tp}"})
        sys.exit(1)

    context_window = _detect_context_window(str(tp))
    usage = compute_usage(str(tp))

    current = usage["current_context_tokens"]
    pct = round(current / context_window * 100, 1) if context_window else 0

    print_json({
        "ok": True,
        "transcript": str(tp),
        "turns": usage["turns"],
        "current_context_tokens": current,
        "context_window": context_window,
        "context_used_pct": pct,
        "cumulative": usage["cumulative"],
    })


if __name__ == "__main__":
    main()
