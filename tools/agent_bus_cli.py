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
SESSION_DATA_FILE = Path("tmp/session_data.json")
SESSION_INIT_CONFIG = Path("config/session_init_config.json")


def _get_all_roles() -> list[str]:
    """Read role list from session_init_config.json keys."""
    try:
        config = json.loads(SESSION_INIT_CONFIG.read_text(encoding="utf-8"))
        return list(config.keys())
    except Exception:
        return ["erp_specialist", "analyst", "developer", "architect", "metodolog", "prompt_engineer"]


def _get_session_data() -> dict:
    """Read session data from tmp/session_data.json."""
    if not SESSION_DATA_FILE.exists():
        return {}
    try:
        return json.loads(SESSION_DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_session_role() -> str | None:
    """Read current session role from tmp/session_data.json."""
    return _get_session_data().get("role")


def get_session_id() -> str | None:
    """Read current session_id from tmp/session_data.json."""
    return _get_session_data().get("session_id")


INLINE_CONTENT_LIMIT = 500


def _read_content(args: argparse.Namespace) -> str:
    """Read content from --content or --content-file.

    If --content exceeds INLINE_CONTENT_LIMIT, auto-saves to tmp/ and logs path.
    """
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    content = args.content or ""
    if len(content) > INLINE_CONTENT_LIMIT:
        import hashlib
        h = hashlib.md5(content.encode()).hexdigest()[:8]
        path = Path(f"tmp/auto_content_{h}.md")
        path.parent.mkdir(exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return content


def _bulk_json_processor(file_path: str, handler) -> list:
    """Process JSON array file with handler function.

    Reads JSON array from file and applies handler to each item.

    Args:
        file_path: Path to JSON file containing array of items
        handler: Function that processes each item and returns a result

    Returns:
        List of results from handler calls
    """
    items = json.loads(Path(file_path).read_text(encoding="utf-8"))
    results = []
    for item in items:
        result = handler(item)
        results.append(result)
    return results


def cmd_send(args: argparse.Namespace, bus: AgentBus) -> dict:
    sender = args.sender or get_session_role()
    if not sender:
        return {"ok": False, "error": "No --from specified and no session found. Run session_init.py first."}
    content = _read_content(args)
    session_id = args.session_id or get_session_id()
    reply_to_id = getattr(args, "reply_to_id", None)

    if args.to == "all":
        recipients = [r for r in _get_all_roles() if r != sender]
        ids = []
        with bus.transaction():
            for recipient in recipients:
                mid = bus.send_message(
                    sender=sender, recipient=recipient,
                    content=content, type=args.type,
                    session_id=session_id, reply_to_id=reply_to_id,
                )
                ids.append(mid)
        return {"ok": True, "ids": ids, "recipients": recipients, "count": len(ids)}

    msg_id = bus.send_message(
        sender=sender, recipient=args.to,
        content=content, type=args.type,
        session_id=session_id, reply_to_id=reply_to_id,
    )
    return {"ok": True, "id": msg_id}


def cmd_handoff(args: argparse.Namespace, bus: AgentBus) -> dict:
    """Send a structured handoff message between roles."""
    if args.to == "all":
        return {"ok": False, "error": "Handoff is 1:1 — use 'send --to all' for broadcast."}
    # Build structured content
    parts = [f"## Handoff: {args.phase}"]
    parts.append(f"**Status:** {args.status}")

    if args.artifacts_file:
        artifacts = Path(args.artifacts_file).read_text(encoding="utf-8")
        parts.append(f"\n**Artifacts:**\n{artifacts}")

    if args.summary:
        parts.append(f"\n**Verification summary:**\n{args.summary}")

    if args.next_action:
        parts.append(f"\n**Next expected action:**\n{args.next_action}")

    if args.content_file:
        extra = Path(args.content_file).read_text(encoding="utf-8")
        parts.append(f"\n**Details:**\n{extra}")

    content = "\n".join(parts)

    msg_id = bus.send_message(
        sender=args.sender,
        recipient=args.to,
        content=content,
        type="handoff",
        session_id=args.session_id or get_session_id(),
    )
    return {"ok": True, "id": msg_id}


def cmd_inbox(args: argparse.Namespace, bus: AgentBus) -> dict:
    # Single message by ID (full content)
    if args.id:
        msg = bus.get_message_by_id(args.id)
        if msg is None:
            return {"ok": False, "error": f"Message #{args.id} not found"}
        return {"ok": True, "data": msg}

    # Full content or summary mode
    full_mode = getattr(args, "full", False)
    summary_only = not full_mode
    messages = bus.get_inbox(role=args.role, status=args.status, summary_only=summary_only)

    # Filter by sender if specified
    if args.sender:
        messages = [m for m in messages if m.get("sender") == args.sender]

    # M3: auto mark-read when reading full content
    if full_mode and messages:
        for msg in messages:
            if msg.get("status") == "unread":
                bus.mark_read(msg["id"])

    return {"ok": True, "data": messages, "count": len(messages)}


def cmd_message(args: argparse.Namespace, bus: AgentBus) -> dict:
    """Get single message by ID (alias for inbox --id)."""
    msg = bus.get_message_by_id(args.id)
    if msg is None:
        return {"ok": False, "error": f"Message #{args.id} not found"}
    return {"ok": True, "data": msg}


_SUGGEST_TYPES = ("rule", "tool", "discovery", "observation")


def cmd_suggest(args: argparse.Namespace, bus: AgentBus) -> dict:
    author = args.sender or get_session_role()
    if not author:
        return {"ok": False, "error": "No --from specified and no session found. Run session_init.py first."}
    recipients = json.loads(args.recipients) if args.recipients else None
    session_id = args.session_id or get_session_id()
    sid = bus.add_suggestion(
        author=author,
        content=_read_content(args),
        title=args.title or "",
        type=args.type or "observation",
        recipients=recipients,
        session_id=session_id,
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
    session_id = args.session_id or get_session_id()
    ids = []
    with bus.transaction():
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
                session_id=session_id,
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
    def handler(item):
        bus.update_suggestion_status(item["id"], item["status"], backlog_id=item.get("backlog_id"))
        return item["id"]

    with bus.transaction():
        results = _bulk_json_processor(args.file, handler)
    return {"ok": True, "updated": len(results)}


def cmd_mark_read(args: argparse.Namespace, bus: AgentBus) -> dict:
    if getattr(args, "all", False):
        count = bus.mark_all_read(args.role)
        return {"ok": True, "marked_all": True, "role": args.role, "count": count}
    for msg_id in args.ids:
        bus.mark_message_read(msg_id)
    return {"ok": True, "marked": args.ids}


def cmd_mark_unread(args: argparse.Namespace, bus: AgentBus) -> dict:
    for msg_id in args.ids:
        bus.mark_unread(msg_id)
    return {"ok": True, "marked_unread": args.ids}


def cmd_backlog_add(args: argparse.Namespace, bus: AgentBus) -> dict:
    bid = bus.add_backlog_item(
        title=args.title,
        content=_read_content(args),
        area=args.area,
        value=args.value,
        effort=args.effort,
        source_id=args.source_id,
        depends_on=args.depends_on,
    )
    return {"ok": True, "id": bid}


def cmd_backlog_add_bulk(args: argparse.Namespace, bus: AgentBus) -> dict:
    def handler(item):
        return bus.add_backlog_item(
            title=item["title"],
            content=item.get("content", ""),
            area=item.get("area"),
            value=item.get("value"),
            effort=item.get("effort"),
            source_id=item.get("source_id"),
        )

    with bus.transaction():
        ids = _bulk_json_processor(args.file, handler)
    return {"ok": True, "ids": ids, "count": len(ids)}


def cmd_backlog(args: argparse.Namespace, bus: AgentBus) -> dict:
      if args.id:
          item = bus.get_backlog_by_id(args.id)
          if item is None:
              return {"ok": False, "error": f"Backlog item #{args.id} not found"}
          return {"ok": True, "data": item}
      entries = bus.get_backlog(status=args.status, area=args.area)
      return {"ok": True, "data": entries, "count": len(entries)}


def cmd_backlog_update(args: argparse.Namespace, bus: AgentBus) -> dict:
    result: dict = {"ok": True}
    with bus.transaction():
        if args.status:
            status_result = bus.update_backlog_status(args.id, args.status)
            if status_result.get("warning"):
                result["warning"] = status_result["warning"]
        if hasattr(args, "depends_on") and args.depends_on is not None:
            dep_val = None if args.depends_on == 0 else args.depends_on
            bus.update_backlog_depends_on(args.id, dep_val)
        if args.content_file or args.content:
            bus.update_backlog_content(args.id, _read_content(args))
    return result


def cmd_backlog_update_bulk(args: argparse.Namespace, bus: AgentBus) -> dict:
    def handler(item):
        if "status" in item:
            bus.update_backlog_status(item["id"], item["status"])
        if "depends_on" in item:
            dep_val = None if item["depends_on"] == 0 else item["depends_on"]
            bus.update_backlog_depends_on(item["id"], dep_val)
        if "content" in item:
            bus.update_backlog_content(item["id"], item["content"])
        return item["id"]

    with bus.transaction():
        results = _bulk_json_processor(args.file, handler)
    return {"ok": True, "updated": len(results)}


def cmd_log(args: argparse.Namespace, bus: AgentBus) -> dict:
    role = args.role or get_session_role()
    if not role:
        return {"ok": False, "error": "No --role specified and no session found. Run session_init.py first."}
    lid = bus.add_session_log(
        role=role,
        content=_read_content(args),
        title=args.title,
        session_id=args.session_id or get_session_id(),
    )
    return {"ok": True, "id": lid}


def cmd_session_logs(args: argparse.Namespace, bus: AgentBus) -> dict:
    # --init mode: session initialization (3 full + 7 metadata + 20 cross-role)
    if args.init:
        if not args.role:
            return {"ok": False, "error": "--init requires --role"}

        data = bus.get_session_logs_init(role=args.role)
        return {"ok": True, "role": args.role, "data": data}

    # Normal mode
    logs = bus.get_session_logs(
        role=args.role,
        limit=args.limit,
        offset=args.offset,
        metadata_only=args.metadata_only,
    )
    return {"ok": True, "data": logs, "count": len(logs)}


def cmd_delete(args: argparse.Namespace, bus: AgentBus) -> dict:
    for msg_id in args.ids:
        bus.archive_message(msg_id)
    return {"ok": True, "archived": args.ids}


# --- Workflow execution tracking ---

def cmd_workflow_start(args: argparse.Namespace, bus: AgentBus) -> dict:
    execution_id = bus.start_workflow_execution(
        workflow_id=args.workflow_id,
        role=args.role,
        session_id=args.session_id or get_session_id(),
    )
    return {"ok": True, "execution_id": execution_id}


def cmd_step_log(args: argparse.Namespace, bus: AgentBus) -> dict:
    output_json = None
    if args.output_file:
        import json as json_mod
        output_json = json_mod.loads(Path(args.output_file).read_text(encoding="utf-8"))

    step_id = bus.log_step(
        execution_id=args.execution_id,
        step_id=args.step_id,
        status=args.status,
        step_index=args.step_index,
        output_summary=args.summary,
        output_json=output_json,
    )
    return {"ok": True, "step_log_id": step_id}


def cmd_workflow_end(args: argparse.Namespace, bus: AgentBus) -> dict:
    result = bus.end_workflow_execution(args.execution_id, args.status)
    return result


def cmd_execution_status(args: argparse.Namespace, bus: AgentBus) -> dict:
    status = bus.get_execution_status(args.execution_id)
    if status is None:
        return {"ok": False, "error": f"Execution #{args.execution_id} not found"}
    return {"ok": True, "data": status}


def cmd_interrupted_workflows(args: argparse.Namespace, bus: AgentBus) -> dict:
    executions = bus.get_interrupted_executions(role=args.role)
    return {"ok": True, "data": executions, "count": len(executions)}


def cmd_flag(args: argparse.Namespace, bus: AgentBus) -> dict:
    reason = Path(args.reason_file).read_text(encoding="utf-8") if args.reason_file else args.reason
    flag_id = bus.flag_for_human(
        sender=args.sender,
        reason=reason,
        urgency=args.urgency,
        session_id=args.session_id or get_session_id(),
    )
    return {"ok": True, "id": flag_id}


def cmd_gap_add(args: argparse.Namespace, bus: AgentBus) -> dict:
    description = Path(args.content_file).read_text(encoding="utf-8") if args.content_file else args.description
    gap_id = bus.add_known_gap(
        title=args.title,
        description=description,
        area=args.area,
        trigger_condition=args.trigger,
        reported_by=args.reported_by,
        source_suggestion_id=args.source_id,
    )
    return {"ok": True, "id": gap_id}


def cmd_gaps(args: argparse.Namespace, bus: AgentBus) -> dict:
    gaps = bus.get_known_gaps(area=args.area, status=args.status)
    return {"ok": True, "data": gaps, "count": len(gaps)}


def cmd_gap_resolve(args: argparse.Namespace, bus: AgentBus) -> dict:
    result = bus.resolve_known_gap(args.id, args.backlog_id)
    return result


def cmd_spawn(args: argparse.Namespace, bus: AgentBus) -> dict:
    """Spawn another agent via VS Code URI handler + record invocation."""
    import subprocess
    from pathlib import Path

    sender = args.sender or _detect_role()
    project_root = Path(__file__).parent.parent
    vscode_uri = project_root / "tools" / "vscode_uri.py"

    # Record invocation in DB
    conn = bus._conn
    conn.execute(
        """INSERT INTO invocations (invoker_type, invoker_id, target_role, task, status)
           VALUES ('agent', ?, ?, ?, 'approved')""",
        (sender, args.role, args.task),
    )
    conn.commit()
    inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Call vscode_uri.py to trigger spawn
    cmd = [sys.executable, str(vscode_uri), "--command", "spawnAgent", "--role", args.role, "--task", args.task]
    if args.permission_mode:
        cmd.extend(["--permission-mode", args.permission_mode])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    uri_result = {}
    if result.stdout.strip():
        try:
            uri_result = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    ok = uri_result.get("ok", False)

    # Update invocation status
    new_status = "running" if ok else "failed"
    conn.execute(
        "UPDATE invocations SET status = ? WHERE id = ?",
        (new_status, inv_id),
    )
    conn.commit()

    return {
        "ok": ok,
        "invocation_id": inv_id,
        "target_role": args.role,
        "task": args.task,
        "uri": uri_result.get("uri", ""),
    }


def cmd_spawn_request(args: argparse.Namespace, bus: AgentBus) -> dict:
    """Request agent spawn — inserts as 'pending' for human approval via wtyczka."""
    sender = args.sender or _detect_role()
    conn = bus._conn
    conn.execute(
        """INSERT INTO invocations (invoker_type, invoker_id, target_role, task, status)
           VALUES ('agent', ?, ?, ?, 'pending')""",
        (sender, args.role, args.task),
    )
    conn.commit()
    inv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return {
        "ok": True,
        "invocation_id": inv_id,
        "status": "pending",
        "target_role": args.role,
        "task": args.task,
        "message": "Spawn request created. Awaiting human approval in VS Code.",
    }


def cmd_invocations(args: argparse.Namespace, bus: AgentBus) -> dict:
    """List invocations, optionally filtered by status."""
    conn = bus._conn
    if args.status:
        rows = conn.execute(
            "SELECT * FROM invocations WHERE status = ? ORDER BY id DESC", (args.status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM invocations ORDER BY id DESC").fetchall()
    return {"ok": True, "data": [dict(r) for r in rows], "count": len(rows)}


def cmd_inbox_summary(args: argparse.Namespace, bus: AgentBus) -> dict:
    """Unread message counts per role, grouped by type."""
    conn = bus._conn
    rows = conn.execute(
        """SELECT recipient, type, COUNT(*) as cnt
           FROM messages
           WHERE status = 'unread'
           GROUP BY recipient, type
           ORDER BY recipient, cnt DESC"""
    ).fetchall()
    summary: dict = {}
    for r in rows:
        role = r["recipient"]
        if role not in summary:
            summary[role] = {"total": 0, "types": {}}
        summary[role]["total"] += r["cnt"]
        summary[role]["types"][r["type"]] = r["cnt"]
    # Ensure all known roles appear (even with 0)
    for role in _get_all_roles():
        if role not in summary:
            summary[role] = {"total": 0, "types": {}}
    return {"ok": True, "data": summary}


def cmd_live_agents(args: argparse.Namespace, bus: AgentBus) -> dict:
    """List agents with status starting or active."""
    conn = bus._conn
    rows = conn.execute(
        """SELECT id, session_id, role, task, status, created_at, last_activity
           FROM live_agents
           WHERE status IN ('starting', 'active')
           ORDER BY created_at DESC"""
    ).fetchall()
    return {"ok": True, "data": [dict(r) for r in rows], "count": len(rows)}


def cmd_backlog_summary(args: argparse.Namespace, bus: AgentBus) -> dict:
    """Backlog counts per area, grouped by status."""
    conn = bus._conn
    rows = conn.execute(
        """SELECT area, status, COUNT(*) as cnt
           FROM backlog
           GROUP BY area, status
           ORDER BY area, cnt DESC"""
    ).fetchall()
    summary: dict = {}
    for r in rows:
        area = r["area"] or "unknown"
        if area not in summary:
            summary[area] = {}
        summary[area][r["status"]] = r["cnt"]
    return {"ok": True, "data": summary}


def cmd_handoffs_pending(args: argparse.Namespace, bus: AgentBus) -> dict:
    """Unread handoffs whose recipient has no active agent."""
    conn = bus._conn
    rows = conn.execute(
        """SELECT m.id, m.sender, m.recipient, m.title, m.created_at,
                  CASE WHEN la.id IS NOT NULL THEN 1 ELSE 0 END as recipient_live
           FROM messages m
           LEFT JOIN live_agents la
             ON la.role = m.recipient AND la.status IN ('starting', 'active')
           WHERE m.type = 'handoff' AND m.status = 'unread'
             AND la.id IS NULL
           ORDER BY m.created_at DESC"""
    ).fetchall()
    return {"ok": True, "data": [dict(r) for r in rows], "count": len(rows)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AgentBus CLI — message passing and state for agent swarm"
    )
    parser.add_argument("--db", default=DB_PATH, help="Path to mrowisko.db")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # send
    p_send = subparsers.add_parser("send", help="Send a message to a role")
    p_send.add_argument("--from", dest="sender", help="Sender role (default: from session)")
    p_send.add_argument("--to", required=True)
    g_send = p_send.add_mutually_exclusive_group(required=True)
    g_send.add_argument("--content")
    g_send.add_argument("--content-file", dest="content_file")
    p_send.add_argument("--type", default="suggestion",
                        choices=["suggestion", "task", "info", "flag_human"])
    p_send.add_argument("--session-id", dest="session_id", default=None)
    p_send.add_argument("--reply-to", dest="reply_to_id", type=int, default=None, help="ID of message being replied to")

    # handoff
    p_handoff = subparsers.add_parser("handoff", help="Send structured handoff between roles")
    p_handoff.add_argument("--from", dest="sender", required=True)
    p_handoff.add_argument("--to", required=True)
    p_handoff.add_argument("--phase", required=True, help="Workflow phase completed")
    p_handoff.add_argument("--status", required=True, choices=["PASS", "BLOCKED", "ESCALATE"])
    p_handoff.add_argument("--artifacts-file", dest="artifacts_file", default=None,
                           help="Path to artifacts list (JSON or markdown)")
    p_handoff.add_argument("--summary", default=None, help="Verification summary")
    p_handoff.add_argument("--next-action", dest="next_action", default=None,
                           help="Next expected action for recipient")
    p_handoff.add_argument("--content-file", dest="content_file", default=None,
                           help="Additional details")
    p_handoff.add_argument("--session-id", dest="session_id", default=None)

    # inbox
    p_inbox = subparsers.add_parser("inbox", help="Get messages for a role")
    p_inbox.add_argument("--role", required=True)
    p_inbox.add_argument("--status", default="unread",
                         choices=["unread", "read", "archived"])
    p_inbox.add_argument("--id", type=int, help="Get single message by ID (full content)")
    p_inbox.add_argument("--full", action="store_true", help="Include full content for all messages")
    p_inbox.add_argument("--sender", default=None, help="Filter by sender role")

    # message (alias for inbox --id)
    p_message = subparsers.add_parser("message", help="Get single message by ID")
    p_message.add_argument("--id", type=int, required=True, help="Message ID")

    # suggest
    p_suggest = subparsers.add_parser("suggest", help="Add a suggestion from an agent")
    p_suggest.add_argument("--from", dest="sender", help="Author role (default: from session)")
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
                               choices=["open", "rejected", "implemented", "deferred"])
    p_suggestions.add_argument("--from", dest="author", default=None)
    p_suggestions.add_argument("--type", default=None, choices=list(_SUGGEST_TYPES))

    # suggest-status
    p_ss = subparsers.add_parser("suggest-status", help="Update suggestion status")
    p_ss.add_argument("--id", type=int, required=True)
    p_ss.add_argument("--status", required=True,
                      choices=["open", "rejected", "implemented", "deferred"])
    p_ss.add_argument("--backlog-id", dest="backlog_id", type=int, default=None)

    # suggest-status-bulk
    p_ss_bulk = subparsers.add_parser("suggest-status-bulk", help="Update multiple suggestion statuses from JSON file")
    p_ss_bulk.add_argument("--file", required=True, help="JSON file with list of {id, status, backlog_id?}")

    # mark-read
    p_mr = subparsers.add_parser("mark-read", help="Mark messages as read")
    p_mr.add_argument("--ids", type=int, nargs="+", default=None)
    p_mr.add_argument("--all", action="store_true", help="Mark all unread for a role")
    p_mr.add_argument("--role", default=None, help="Role (required with --all)")

    # mark-unread
    p_mu = subparsers.add_parser("mark-unread", help="Revert messages to unread")
    p_mu.add_argument("--ids", type=int, nargs="+", required=True)

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
    p_badd.add_argument("--depends-on", dest="depends_on", type=int, default=None,
                        help="ID of backlog item this depends on")

    # backlog-add-bulk
    p_bulk = subparsers.add_parser("backlog-add-bulk", help="Add multiple backlog items from JSON file")
    p_bulk.add_argument("--file", required=True, help="JSON file with list of items")

    # backlog
    p_backlog = subparsers.add_parser("backlog", help="Get backlog items")
    p_backlog.add_argument("--status", default=None,
                           choices=["planned", "in_progress", "done", "cancelled", "deferred"])
    p_backlog.add_argument("--area", default=None,
                           help="Filter by area (ERP, Bot, Arch, Dev, ...)")
    p_backlog.add_argument("--id", type=int, default=None,
                           help="Get single item by ID")

    # backlog-update
    p_bupd = subparsers.add_parser("backlog-update", help="Update backlog item status and/or content")
    p_bupd.add_argument("--id", type=int, required=True)
    p_bupd.add_argument("--status", default=None,
                        choices=["planned", "in_progress", "done", "cancelled", "deferred"])
    p_bupd.add_argument("--depends-on", dest="depends_on", type=int, default=None,
                        help="ID of dependency (0 to clear)")
    g_bupd = p_bupd.add_mutually_exclusive_group()
    g_bupd.add_argument("--content")
    g_bupd.add_argument("--content-file", dest="content_file")

    # backlog-update-bulk
    p_bupd_bulk = subparsers.add_parser("backlog-update-bulk", help="Update multiple backlog items from JSON file")
    p_bupd_bulk.add_argument("--file", required=True, help="JSON file with list of {id, status?, content?}")

    # log
    p_log = subparsers.add_parser("log", help="Add a session log entry")
    p_log.add_argument("--role", help="Role (default: from session)")
    p_log.add_argument("--title", default=None)
    g_log = p_log.add_mutually_exclusive_group(required=True)
    g_log.add_argument("--content")
    g_log.add_argument("--content-file", dest="content_file")
    p_log.add_argument("--session-id", dest="session_id", default=None)

    # session-logs
    p_session_logs = subparsers.add_parser("session-logs", help="Get session log entries")
    p_session_logs.add_argument("--role", default=None, help="Filter by role (optional)")
    p_session_logs.add_argument("--limit", type=int, default=10, help="Max number of entries (default: 10)")
    p_session_logs.add_argument("--offset", type=int, default=0, help="Number of entries to skip (default: 0)")
    p_session_logs.add_argument("--metadata-only", action="store_true", help="Exclude content field (metadata only)")
    p_session_logs.add_argument("--init", action="store_true", help="Session initialization mode (returns own_full + own_metadata + cross_role)")

    # delete
    p_delete = subparsers.add_parser("delete", help="Archive (soft-delete) messages by id")
    p_delete.add_argument("--id", dest="ids", type=int, nargs="+", required=True)

    # workflow-start
    p_wstart = subparsers.add_parser("workflow-start", help="Start workflow execution")
    p_wstart.add_argument("--workflow-id", dest="workflow_id", required=True)
    p_wstart.add_argument("--role", required=True)
    p_wstart.add_argument("--session-id", dest="session_id", default=None)

    # step-log
    p_step = subparsers.add_parser("step-log", help="Log a workflow step")
    p_step.add_argument("--execution-id", dest="execution_id", type=int, required=True)
    p_step.add_argument("--step-id", dest="step_id", required=True)
    p_step.add_argument("--status", required=True, choices=["PASS", "FAIL", "BLOCKED", "SKIPPED", "IN_PROGRESS"])
    p_step.add_argument("--step-index", dest="step_index", type=int, default=None)
    p_step.add_argument("--summary", default=None)
    p_step.add_argument("--output-file", dest="output_file", default=None)

    # workflow-end
    p_wend = subparsers.add_parser("workflow-end", help="End workflow execution")
    p_wend.add_argument("--execution-id", dest="execution_id", type=int, required=True)
    p_wend.add_argument("--status", default="completed", choices=["completed", "interrupted", "failed"])

    # execution-status
    p_estatus = subparsers.add_parser("execution-status", help="Get workflow execution status")
    p_estatus.add_argument("--execution-id", dest="execution_id", type=int, required=True)

    # interrupted-workflows
    p_inter = subparsers.add_parser("interrupted-workflows", help="List interrupted/running workflows")
    p_inter.add_argument("--role", default=None)

    # flag
    p_flag = subparsers.add_parser("flag", help="Flag something for human review")
    p_flag.add_argument("--from", dest="sender", required=True)
    g_flag = p_flag.add_mutually_exclusive_group(required=True)
    g_flag.add_argument("--reason")
    g_flag.add_argument("--reason-file", dest="reason_file")
    p_flag.add_argument("--urgency", default="normal",
                        choices=["normal", "high"])
    p_flag.add_argument("--session-id", dest="session_id", default=None)

    # gap-add
    p_gap_add = subparsers.add_parser("gap-add", help="Add a known gap")
    p_gap_add.add_argument("--title", required=True)
    p_gap_add.add_argument("--area", required=True)
    p_gap_add.add_argument("--trigger", required=True, help="Trigger condition for revisiting")
    p_gap_add.add_argument("--reported-by", dest="reported_by", required=True)
    g_gap_add = p_gap_add.add_mutually_exclusive_group(required=True)
    g_gap_add.add_argument("--description")
    g_gap_add.add_argument("--content-file", dest="content_file")
    p_gap_add.add_argument("--source-id", dest="source_id", type=int, default=None)

    # gaps
    p_gaps = subparsers.add_parser("gaps", help="List known gaps")
    p_gaps.add_argument("--area", default=None)
    p_gaps.add_argument("--status", default="open", choices=["open", "resolved", "all"])

    # gap-resolve
    p_gap_res = subparsers.add_parser("gap-resolve", help="Resolve a known gap")
    p_gap_res.add_argument("--id", type=int, required=True)
    p_gap_res.add_argument("--backlog-id", dest="backlog_id", type=int, required=True)

    # spawn — direct agent invocation (M2, wariant A — no approval)
    p_spawn = subparsers.add_parser("spawn", help="Spawn another agent via VS Code URI handler")
    p_spawn.add_argument("--from", dest="sender", help="Invoker role")
    p_spawn.add_argument("--role", required=True, help="Target agent role")
    p_spawn.add_argument("--task", required=True, help="Task for the agent")
    p_spawn.add_argument("--permission-mode", dest="permission_mode", help="Permission mode override")

    # spawn-request — request spawn with approval gate (M2, wariant B)
    p_spawn_req = subparsers.add_parser("spawn-request", help="Request agent spawn (pending approval)")
    p_spawn_req.add_argument("--from", dest="sender", help="Invoker role")
    p_spawn_req.add_argument("--role", required=True, help="Target agent role")
    p_spawn_req.add_argument("--task", required=True, help="Task for the agent")

    # invocations — list invocations
    p_invocations = subparsers.add_parser("invocations", help="List invocations")
    p_invocations.add_argument("--status", default=None, help="Filter by status")

    # backlog-summary — backlog counts per area (PM tool)
    subparsers.add_parser("backlog-summary", help="Backlog counts per area and status")

    # inbox-summary — unread counts per role (PM tool)
    subparsers.add_parser("inbox-summary", help="Unread message counts per role")

    # live-agents — active agents list (PM tool)
    subparsers.add_parser("live-agents", help="List active/starting agents")

    # handoffs-pending — unread handoffs with no live recipient (PM tool)
    subparsers.add_parser("handoffs-pending", help="Handoffs awaiting delivery")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    bus = AgentBus(db_path=args.db)
    commands = {
        "send": cmd_send,
        "handoff": cmd_handoff,
        "inbox": cmd_inbox,
        "message": cmd_message,
        "suggest": cmd_suggest,
        "suggest-bulk": cmd_suggest_bulk,
        "suggestions": cmd_suggestions,
        "suggest-status": cmd_suggest_status,
        "suggest-status-bulk": cmd_suggest_status_bulk,
        "mark-read": cmd_mark_read,
        "mark-unread": cmd_mark_unread,
        "backlog-add": cmd_backlog_add,
        "backlog-add-bulk": cmd_backlog_add_bulk,
        "backlog": cmd_backlog,
        "backlog-update": cmd_backlog_update,
        "backlog-update-bulk": cmd_backlog_update_bulk,
        "log": cmd_log,
        "session-logs": cmd_session_logs,
        "delete": cmd_delete,
        "workflow-start": cmd_workflow_start,
        "step-log": cmd_step_log,
        "workflow-end": cmd_workflow_end,
        "execution-status": cmd_execution_status,
        "interrupted-workflows": cmd_interrupted_workflows,
        "flag": cmd_flag,
        "gap-add": cmd_gap_add,
        "gaps": cmd_gaps,
        "gap-resolve": cmd_gap_resolve,
        "spawn": cmd_spawn,
        "spawn-request": cmd_spawn_request,
        "invocations": cmd_invocations,
        "backlog-summary": cmd_backlog_summary,
        "inbox-summary": cmd_inbox_summary,
        "live-agents": cmd_live_agents,
        "handoffs-pending": cmd_handoffs_pending,
    }
    try:
        result = commands[args.command](args, bus)
        print_json(result)
    except Exception as e:
        print_json({"ok": False, "error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    main()
