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


def cmd_write_state(args: argparse.Namespace, bus: AgentBus) -> dict:
    metadata = json.loads(args.metadata) if args.metadata else None
    state_id = bus.write_state(
        role=args.role,
        type=args.type,
        content=_read_content(args),
        session_id=args.session_id,
        metadata=metadata,
    )
    return {"ok": True, "id": state_id}


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
    p_send.add_argument("--type", default="suggestion")
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

    # write-state
    p_write = subparsers.add_parser("write-state", help="Write a state entry")
    p_write.add_argument("--role", required=True)
    p_write.add_argument("--type", required=True,
                         choices=["progress", "reflection", "backlog_item"])
    g_write = p_write.add_mutually_exclusive_group(required=True)
    g_write.add_argument("--content")
    g_write.add_argument("--content-file", dest="content_file")
    p_write.add_argument("--session-id", dest="session_id", default=None)
    p_write.add_argument("--metadata", default=None, help="JSON string")

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
        "write-state": cmd_write_state,
        "flag": cmd_flag,
    }
    result = commands[args.command](args, bus)
    print_json(result)


if __name__ == "__main__":
    main()
