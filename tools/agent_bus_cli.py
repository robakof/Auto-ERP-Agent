"""CLI wrapper for AgentBus — for use from Bash when direct Python import is not possible.

Usage:
    python tools/agent_bus_cli.py send --from developer --to erp_specialist --content "..."
    python tools/agent_bus_cli.py inbox --role developer
    python tools/agent_bus_cli.py inbox --role developer --status read
    python tools/agent_bus_cli.py state --role developer
    python tools/agent_bus_cli.py state --role developer --type progress
    python tools/agent_bus_cli.py write-state --role developer --type progress --content "..."
    python tools/agent_bus_cli.py flag --from analyst --reason "..." --urgency high

All output is JSON.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json

DB_PATH = "mrowisko.db"


def _read_content(args: argparse.Namespace) -> str:
    """Read content from --content or --content-file."""
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    return args.content


def cmd_send(args: argparse.Namespace, bus: AgentBus) -> dict:
    msg_id = bus.send_message(
        sender=args.sender,
        recipient=args.to,
        content=_read_content(args),
        type=args.type,
        session_id=args.session_id,
    )
    return {"ok": True, "id": msg_id}


def cmd_inbox(args: argparse.Namespace, bus: AgentBus) -> dict:
    messages = bus.get_inbox(role=args.role, status=args.status)
    return {"ok": True, "data": messages, "count": len(messages)}


def cmd_state(args: argparse.Namespace, bus: AgentBus) -> dict:
    entries = bus.get_state(role=args.role, type=args.type, limit=args.limit)
    return {"ok": True, "data": entries, "count": len(entries)}



_SUGGEST_TYPES = ("rule", "tool", "discovery", "observation")


def cmd_suggest(args: argparse.Namespace, bus: AgentBus) -> dict:
    recipients = json.loads(args.recipients) if args.recipients else None
    sid = bus.add_suggestion(
        author=args.sender,
        content=_read_content(args),
        title=args.title or "",
        type=args.type or "observation",
        recipients=recipients,
        session_id=args.session_id,
    )
    return {"ok": True, "id": sid}


def _parse_suggest_block(block: str) -> tuple[str, str, str]:
    """Parse a suggestion block into (type, title, content).

    Metadata lines at the top of the block: 'type: <value>' and 'title: <value>'.
    Remaining lines (after stripping leading metadata) become the content.
    """
    lines = block.splitlines()
    suggest_type = "observation"
    title = ""
    content_start = 0
    for i, line in enumerate(lines):
        lower = line.strip().lower()
        if lower.startswith("type:"):
            value = line.split(":", 1)[1].strip()
            if value in _SUGGEST_TYPES:
                suggest_type = value
            content_start = i + 1
        elif lower.startswith("title:"):
            title = line.split(":", 1)[1].strip()
            content_start = i + 1
        else:
            break
    content = "\n".join(lines[content_start:]).strip()
    return suggest_type, title, content


def cmd_suggest_bulk(args: argparse.Namespace, bus: AgentBus) -> dict:
    text = Path(args.bulk_file).read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.split("\n---\n") if b.strip()]
    recipients = json.loads(args.recipients) if args.recipients else None
    ids = []
    for block in blocks:
        suggest_type, title, content = _parse_suggest_block(block)
        if not content:
            continue
        sid = bus.add_suggestion(
            author=args.sender,
            content=content,
            title=title,
            type=suggest_type,
            recipients=recipients,
            session_id=args.session_id,
        )
        ids.append(sid)
    return {"ok": True, "ids": ids, "count": len(ids)}


def cmd_suggestions(args: argparse.Namespace, bus: AgentBus) -> dict:
    entries = bus.get_suggestions(
        status=args.status, author=args.author, type=getattr(args, "type", None)
    )
    return {"ok": True, "data": entries, "count": len(entries)}


def cmd_suggest_status(args: argparse.Namespace, bus: AgentBus) -> dict:
    bus.update_suggestion_status(args.id, args.status, backlog_id=args.backlog_id)
    return {"ok": True}


def cmd_suggest_status_bulk(args: argparse.Namespace, bus: AgentBus) -> dict:
    import json as _json
    updates = _json.loads(Path(args.file).read_text(encoding="utf-8"))
    updated = 0
    for item in updates:
        item_id = item["id"]
        status = item["status"]
        backlog_id = item.get("backlog_id")
        bus.update_suggestion_status(item_id, status, backlog_id=backlog_id)
        updated += 1
    return {"ok": True, "updated": updated}


def cmd_mark_read(args: argparse.Namespace, bus: AgentBus) -> dict:
    if getattr(args, "all", False):
        count = bus.mark_all_read(args.role)
        return {"ok": True, "marked_all": True, "role": args.role, "count": count}
    for msg_id in args.ids:
        bus.mark_message_read(msg_id)
    return {"ok": True, "marked": args.ids}


def cmd_backlog_add(args: argparse.Namespace, bus: AgentBus) -> dict:
    bid = bus.add_backlog_item(
        title=args.title,
        content=_read_content(args),
        area=args.area,
        value=args.value,
        effort=args.effort,
        source_id=args.source_id,
    )
    return {"ok": True, "id": bid}


def cmd_backlog_add_bulk(args: argparse.Namespace, bus: AgentBus) -> dict:
    import json as _json
    items = _json.loads(Path(args.file).read_text(encoding="utf-8"))
    ids = []
    for item in items:
        bid = bus.add_backlog_item(
            title=item["title"],
            content=item.get("content", ""),
            area=item.get("area"),
            value=item.get("value"),
            effort=item.get("effort"),
            source_id=item.get("source_id"),
        )
        ids.append(bid)
    return {"ok": True, "ids": ids, "count": len(ids)}


def cmd_backlog(args: argparse.Namespace, bus: AgentBus) -> dict:
    entries = bus.get_backlog(status=args.status, area=args.area)
    return {"ok": True, "data": entries, "count": len(entries)}


def cmd_backlog_update(args: argparse.Namespace, bus: AgentBus) -> dict:
    if args.status:
        bus.update_backlog_status(args.id, args.status)
    if args.content_file or args.content:
        bus.update_backlog_content(args.id, _read_content(args))
    return {"ok": True}


def cmd_backlog_update_bulk(args: argparse.Namespace, bus: AgentBus) -> dict:
    import json as _json
    updates = _json.loads(Path(args.file).read_text(encoding="utf-8"))
    updated = 0
    for item in updates:
        item_id = item["id"]
        if "status" in item:
            bus.update_backlog_status(item_id, item["status"])
        if "content" in item:
            bus.update_backlog_content(item_id, item["content"])
        updated += 1
    return {"ok": True, "updated": updated}


def cmd_log(args: argparse.Namespace, bus: AgentBus) -> dict:
    lid = bus.add_session_log(
        role=args.role,
        content=_read_content(args),
        session_id=args.session_id,
    )
    return {"ok": True, "id": lid}


def cmd_delete(args: argparse.Namespace, bus: AgentBus) -> dict:
    for msg_id in args.ids:
        bus.archive_message(msg_id)
    return {"ok": True, "archived": args.ids}


def cmd_flag(args: argparse.Namespace, bus: AgentBus) -> dict:
    reason = Path(args.reason_file).read_text(encoding="utf-8") if args.reason_file else args.reason
    flag_id = bus.flag_for_human(
        sender=args.sender,
        reason=reason,
        urgency=args.urgency,
        session_id=args.session_id,
    )
    return {"ok": True, "id": flag_id}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AgentBus CLI — message passing and state for agent swarm"
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to mrowisko.db")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # send
    p_send = subparsers.add_parser("send", help="Send a message to a role")
    p_send.add_argument("--from", dest="sender", required=True)
    p_send.add_argument("--to", required=True)
    g_send = p_send.add_mutually_exclusive_group(required=True)
    g_send.add_argument("--content")
    g_send.add_argument("--content-file", dest="content_file")
    p_send.add_argument("--type", default="suggestion",
                        choices=["suggestion", "task", "info", "flag_human"])
    p_send.add_argument("--session-id", dest="session_id", default=None)

    # inbox
    p_inbox = subparsers.add_parser("inbox", help="Get messages for a role")
    p_inbox.add_argument("--role", required=True)
    p_inbox.add_argument("--status", default="unread",
                         choices=["unread", "read", "archived"])

    # state
    p_state = subparsers.add_parser("state", help="Get state entries for a role")
    p_state.add_argument("--role", required=True)
    p_state.add_argument("--type", default=None)
    p_state.add_argument("--limit", type=int, default=20)

    # suggest
    p_suggest = subparsers.add_parser("suggest", help="Add a suggestion from an agent")
    p_suggest.add_argument("--from", dest="sender", required=True)
    g_suggest = p_suggest.add_mutually_exclusive_group(required=True)
    g_suggest.add_argument("--content")
    g_suggest.add_argument("--content-file", dest="content_file")
    p_suggest.add_argument("--title", default=None, help="Short title (one line)")
    p_suggest.add_argument("--type", default=None, choices=list(_SUGGEST_TYPES),
                           help="Suggestion type")
    p_suggest.add_argument("--recipients", default=None, help="JSON array of roles")
    p_suggest.add_argument("--session-id", dest="session_id", default=None)

    # suggest-bulk
    p_sbulk = subparsers.add_parser(
        "suggest-bulk",
        help="Add multiple suggestions from a file (blocks separated by '\\n---\\n')",
    )
    p_sbulk.add_argument("--from", dest="sender", required=True)
    p_sbulk.add_argument("--bulk-file", dest="bulk_file", required=True,
                         help="File with suggestion blocks separated by '\\n---\\n'")
    p_sbulk.add_argument("--recipients", default=None, help="JSON array of roles")
    p_sbulk.add_argument("--session-id", dest="session_id", default=None)

    # suggestions
    p_suggestions = subparsers.add_parser("suggestions", help="Get suggestions")
    p_suggestions.add_argument("--status", default=None,
                               choices=["open", "in_backlog", "rejected", "implemented"])
    p_suggestions.add_argument("--from", dest="author", default=None)
    p_suggestions.add_argument("--type", default=None, choices=list(_SUGGEST_TYPES))

    # suggest-status
    p_ss = subparsers.add_parser("suggest-status", help="Update suggestion status")
    p_ss.add_argument("--id", type=int, required=True)
    p_ss.add_argument("--status", required=True,
                      choices=["open", "in_backlog", "rejected", "implemented"])
    p_ss.add_argument("--backlog-id", dest="backlog_id", type=int, default=None)

    # suggest-status-bulk
    p_ss_bulk = subparsers.add_parser("suggest-status-bulk", help="Update multiple suggestion statuses from JSON file")
    p_ss_bulk.add_argument("--file", required=True, help="JSON file with list of {id, status, backlog_id?}")

    # mark-read
    p_mr = subparsers.add_parser("mark-read", help="Mark messages as read")
    p_mr.add_argument("--ids", type=int, nargs="+", default=None)
    p_mr.add_argument("--all", action="store_true", help="Mark all unread for a role")
    p_mr.add_argument("--role", default=None, help="Role (required with --all)")

    # backlog-add
    p_badd = subparsers.add_parser("backlog-add", help="Add a backlog item")
    p_badd.add_argument("--title", required=True)
    g_badd = p_badd.add_mutually_exclusive_group(required=True)
    g_badd.add_argument("--content")
    g_badd.add_argument("--content-file", dest="content_file")
    p_badd.add_argument("--area", default=None)
    p_badd.add_argument("--value", default=None, choices=["wysoka", "srednia", "niska"])
    p_badd.add_argument("--effort", default=None, choices=["mala", "srednia", "duza"])
    p_badd.add_argument("--source-id", dest="source_id", type=int, default=None)

    # backlog-add-bulk
    p_bulk = subparsers.add_parser("backlog-add-bulk", help="Add multiple backlog items from JSON file")
    p_bulk.add_argument("--file", required=True, help="JSON file with list of items")

    # backlog
    p_backlog = subparsers.add_parser("backlog", help="Get backlog items")
    p_backlog.add_argument("--status", default=None,
                           choices=["planned", "in_progress", "done", "cancelled", "deferred"])
    p_backlog.add_argument("--area", default=None,
                           help="Filter by area (ERP, Bot, Arch, Dev, ...)")

    # backlog-update
    p_bupd = subparsers.add_parser("backlog-update", help="Update backlog item status and/or content")
    p_bupd.add_argument("--id", type=int, required=True)
    p_bupd.add_argument("--status", default=None,
                        choices=["planned", "in_progress", "done", "cancelled", "deferred"])
    g_bupd = p_bupd.add_mutually_exclusive_group()
    g_bupd.add_argument("--content")
    g_bupd.add_argument("--content-file", dest="content_file")

    # backlog-update-bulk
    p_bupd_bulk = subparsers.add_parser("backlog-update-bulk", help="Update multiple backlog items from JSON file")
    p_bupd_bulk.add_argument("--file", required=True, help="JSON file with list of {id, status?, content?}")

    # log
    p_log = subparsers.add_parser("log", help="Add a session log entry")
    p_log.add_argument("--role", required=True)
    g_log = p_log.add_mutually_exclusive_group(required=True)
    g_log.add_argument("--content")
    g_log.add_argument("--content-file", dest="content_file")
    p_log.add_argument("--session-id", dest="session_id", default=None)

    # delete
    p_delete = subparsers.add_parser("delete", help="Archive (soft-delete) messages by id")
    p_delete.add_argument("--id", dest="ids", type=int, nargs="+", required=True)

    # flag
    p_flag = subparsers.add_parser("flag", help="Flag something for human review")
    p_flag.add_argument("--from", dest="sender", required=True)
    g_flag = p_flag.add_mutually_exclusive_group(required=True)
    g_flag.add_argument("--reason")
    g_flag.add_argument("--reason-file", dest="reason_file")
    p_flag.add_argument("--urgency", default="normal",
                        choices=["normal", "high"])
    p_flag.add_argument("--session-id", dest="session_id", default=None)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    bus = AgentBus(db_path=args.db)
    commands = {
        "send": cmd_send,
        "inbox": cmd_inbox,
        "state": cmd_state,
        "suggest": cmd_suggest,
        "suggest-bulk": cmd_suggest_bulk,
        "suggestions": cmd_suggestions,
        "suggest-status": cmd_suggest_status,
        "suggest-status-bulk": cmd_suggest_status_bulk,
        "mark-read": cmd_mark_read,
        "backlog-add": cmd_backlog_add,
        "backlog-add-bulk": cmd_backlog_add_bulk,
        "backlog": cmd_backlog,
        "backlog-update": cmd_backlog_update,
        "backlog-update-bulk": cmd_backlog_update_bulk,
        "log": cmd_log,
        "delete": cmd_delete,
        "flag": cmd_flag,
    }
    result = commands[args.command](args, bus)
    print_json(result)


if __name__ == "__main__":
    main()
