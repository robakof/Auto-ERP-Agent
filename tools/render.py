"""Universal renderer for mrowisko.db views.

Usage:
    python tools/render.py backlog --format xlsx
    python tools/render.py backlog --format md --status planned --area Bot Dev Arch
    python tools/render.py backlog --format json
    python tools/render.py suggestions --format md --status open --author erp_specialist
    python tools/render.py inbox --role developer --format md
    python tools/render.py session-log --role developer --format json --limit 50
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus
from tools.lib.renderers import (
    render_json,
    render_md,
    render_backlog_md,
    render_suggestions_md,
    render_xlsx,
    render_session_trace_xlsx,
)

DB_PATH = "mrowisko.db"

# --- View definitions ---

VIEWS = {
    "backlog": {
        "title": "Backlog",
        "columns": ["id", "title", "area", "value", "effort", "status", "created_at"],
    },
    "suggestions": {
        "title": "Suggestions",
        "columns": ["id", "type", "author", "title", "status", "created_at"],
    },
    "inbox": {
        "title": "Inbox",
        "columns": ["id", "sender", "type", "content", "status", "created_at"],
    },
    "session-log": {
        "title": "Session Log",
        "columns": ["id", "role", "content", "session_id", "created_at"],
    },
    "messages": {
        "title": "Messages",
        "columns": ["id", "sender", "recipient", "type", "content", "status", "created_at", "read_at"],
    },
}

# --- Data fetch ---

def fetch(view: str, bus: AgentBus, args: argparse.Namespace) -> list[dict]:
    if view == "backlog":
        status = getattr(args, "status", "planned")
        items = bus.get_backlog(status=None if status == "all" else status)
        area = getattr(args, "area", None)
        if area:
            items = [i for i in items if i.get("area") in area]
        return items
    if view == "suggestions":
        return bus.get_suggestions(
            status=getattr(args, "status", None),
            author=getattr(args, "author", None),
            type=getattr(args, "type", None),
        )
    if view == "inbox":
        return bus.get_inbox(
            role=args.role,
            status=getattr(args, "status", "unread"),
        )
    if view == "session-log":
        return bus.get_session_log(
            role=args.role,
            limit=getattr(args, "limit", 20),
        )
    if view == "messages":
        return bus.get_messages(
            sender=getattr(args, "sender", None),
            recipient=getattr(args, "recipient", None),
            status=getattr(args, "status", None),
            limit=getattr(args, "limit", 200),
        )
    return []

# --- CLI ---

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render mrowisko.db views to md/xlsx/json")
    parser.add_argument("--db", default=DB_PATH)
    sub = parser.add_subparsers(dest="view", required=True)

    for view in ["backlog", "suggestions"]:
        p = sub.add_parser(view)
        p.add_argument("--format", required=True, choices=["md", "xlsx", "json"])
        p.add_argument("--output", default=None)
        if view == "backlog":
            p.add_argument("--status", default="planned",
                           help="Filter by status (default: planned). Use 'all' to show everything.")
            p.add_argument("--area", nargs="+", default=None)
        else:
            p.add_argument("--status", default=None)
            p.add_argument("--author", default=None)
            p.add_argument("--type", default=None,
                           choices=["rule", "tool", "discovery", "observation"])

    p = sub.add_parser("messages")
    p.add_argument("--format", required=True, choices=["md", "xlsx", "json"])
    p.add_argument("--output", default=None)
    p.add_argument("--sender", default=None)
    p.add_argument("--recipient", default=None)
    p.add_argument("--status", default=None)
    p.add_argument("--limit", type=int, default=200)

    for view in ["inbox", "session-log"]:
        p = sub.add_parser(view)
        p.add_argument("--format", required=True, choices=["md", "xlsx", "json"])
        p.add_argument("--output", default=None)
        p.add_argument("--role", required=True)
        p.add_argument("--status", default="unread")
        if view == "session-log":
            p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("session-trace")
    p.add_argument("--session", required=True, help="Our session ID (12 hex)")
    p.add_argument("--output", default=None)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    bus = AgentBus(db_path=args.db)
    view = args.view

    if view == "session-trace":
        trace = bus.get_session_trace(args.session)
        if not trace:
            print(f"Sesja '{args.session}' nie znaleziona w DB.", file=sys.stderr)
            sys.exit(1)
        output = Path(args.output) if args.output else Path("views") / f"session_trace_{args.session}.xlsx"
        output.parent.mkdir(parents=True, exist_ok=True)
        render_session_trace_xlsx(trace, output)
        tc_count = len(trace["tool_calls"])
        tu_count = len(trace["token_usage"])
        print(f"{output} ({tc_count} tool_calls, {tu_count} turns)")
        return

    cfg = VIEWS[view]
    data = fetch(view, bus, args)

    ext = args.format
    output = Path(args.output) if args.output else Path("views") / f"{view}.{ext}"
    output.parent.mkdir(parents=True, exist_ok=True)

    if ext == "json":
        render_json(data, cfg["title"], output)
    elif ext == "md":
        if view == "backlog":
            render_backlog_md(data, cfg["title"], output)
        elif view == "suggestions":
            render_suggestions_md(data, cfg["title"], output)
        else:
            render_md(data, cfg["columns"], cfg["title"], output)
    elif ext == "xlsx":
        render_xlsx(data, cfg["columns"], cfg["title"], output)

    print(f"{output} ({len(data)} pozycji)")


if __name__ == "__main__":
    main()
