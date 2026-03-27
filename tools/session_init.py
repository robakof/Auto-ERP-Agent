"""Session initializer — generates session ID and loads role context.

Usage:
    python tools/session_init.py --role erp_specialist
    python tools/session_init.py --role developer

Returns JSON with session_id, role prompt path, and full context (inbox, backlog, logs).
Context is controlled by config/session_init_config.json.
Writes session_id to tmp/session_id.txt.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json

DB_PATH = "mrowisko.db"
SESSION_ID_FILE = Path("tmp/session_id.txt")  # legacy
SESSION_DATA_FILE = Path("tmp/session_data.json")
CONFIG_FILE = Path("config/session_init_config.json")

BACKLOG_META_KEYS = ("id", "title", "area", "value", "effort", "status", "depends_on", "created_at")
INBOX_SNIPPET_LEN = 200
LOG_SNIPPET_LEN = 300


def _snippet(text: str, max_len: int) -> tuple[str, bool]:
    """Return (truncated_text, was_truncated)."""
    if not text or len(text) <= max_len:
        return text, False
    return text[:max_len], True


ROLE_DOCUMENTS = {
    "erp_specialist": "documents/erp_specialist/ERP_SPECIALIST.md",
    "analyst":        "documents/analyst/ANALYST.md",
    "developer":      "documents/dev/DEVELOPER.md",
    "architect":      "documents/architect/ARCHITECT.md",
    "metodolog":      "documents/methodology/METHODOLOGY.md",
    "prompt_engineer": "documents/prompt_engineer/PROMPT_ENGINEER.md",
    "dispatcher":      "documents/dispatcher/DISPATCHER.md",
}


def generate_session_id() -> str:
    return uuid.uuid4().hex[:12]


def write_session_id(session_id: str, role: str = None) -> None:
    SESSION_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_ID_FILE.write_text(session_id, encoding="utf-8")
    # Also write session_data.json with role for CLI session-awareness
    if role:
        import datetime
        data = {
            "session_id": session_id,
            "role": role,
            "created_at": datetime.datetime.now().isoformat()
        }
        SESSION_DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_session_id() -> str | None:
    if SESSION_ID_FILE.exists():
        return SESSION_ID_FILE.read_text(encoding="utf-8").strip()
    return None


def load_config(role: str) -> dict:
    """Load session_init config for given role."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if role not in config:
        raise ValueError(f"Role '{role}' not found in {CONFIG_FILE}")

    return config[role]


def get_context(role: str, config: dict, bus: AgentBus) -> dict:
    """Gather all context per config."""
    context = {}

    # Inbox
    if config.get("inbox", {}).get("enabled", False):
        inbox_config = config["inbox"]
        messages = bus.get_messages(
            recipient=role,
            status=inbox_config.get("status", "unread"),
            limit=inbox_config.get("limit", 10)
        )
        # Truncate content to snippet
        for msg in messages:
            if "content" in msg:
                msg["content"], truncated = _snippet(msg["content"], INBOX_SNIPPET_LEN)
                if truncated:
                    msg["truncated"] = True
        context["inbox"] = {
            "messages": messages,
            "count": len(messages)
        }

    # Backlog
    if config.get("backlog", {}).get("enabled", False):
        backlog_config = config["backlog"]
        areas = backlog_config.get("areas", [])
        statuses = backlog_config.get("statuses", ["planned"])
        limit = backlog_config.get("limit", 20)

        items = []
        seen_ids = set()  # Deduplicate if same item matches multiple filters

        # Iterate over all combinations of areas and statuses
        for area in areas:
            for status in statuses:
                area_items = bus.get_backlog(area=area, status=status)
                for item in area_items:
                    if item["id"] not in seen_ids:
                        items.append(item)
                        seen_ids.add(item["id"])
                        if len(items) >= limit:
                            break
                if len(items) >= limit:
                    break
            if len(items) >= limit:
                break

        # Sort by created_at DESC (newest first) and apply limit
        items = sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

        # Strip content — agent fetches details per item via backlog --id X
        slim_items = [{k: item[k] for k in BACKLOG_META_KEYS if k in item} for item in items]

        context["backlog"] = {
            "items": slim_items,
            "count": len(slim_items)
        }

    # Session logs
    if config.get("session_logs", {}).get("own_full", {}).get("enabled", False):
        logs_config = config["session_logs"]

        # Own full (with snippet)
        own_full_config = logs_config.get("own_full", {})
        own_full = bus.get_session_logs(
            role=role,
            limit=own_full_config.get("limit", 3),
            metadata_only=False
        )
        for log in own_full:
            if "content" in log:
                log["content"], truncated = _snippet(log["content"], LOG_SNIPPET_LEN)
                if truncated:
                    log["truncated"] = True

        # Own metadata (optional)
        own_metadata = []
        if logs_config.get("own_metadata", {}).get("enabled", False):
            own_meta_config = logs_config["own_metadata"]
            own_metadata = bus.get_session_logs(
                role=role,
                offset=own_meta_config.get("offset", 3),
                limit=own_meta_config.get("limit", 7),
                metadata_only=True
            )

        # Cross-role (optional)
        cross_role = []
        if logs_config.get("cross_role", {}).get("enabled", False):
            cross_config = logs_config["cross_role"]
            cross_role = bus.get_session_logs(
                limit=cross_config.get("limit", 20),
                metadata_only=True
            )

        context["session_logs"] = {
            "own_full": own_full,
            "own_metadata": own_metadata,
            "cross_role": cross_role
        }

    # Flags human
    if config.get("flags_human", {}).get("enabled", False):
        flags = bus.get_messages(recipient="human", status="unread")
        context["flags_human"] = {
            "items": flags,
            "count": len(flags)
        }

    return context


def main():
    parser = argparse.ArgumentParser(description="Initialize agent session with full context")
    parser.add_argument("--role", required=True, choices=list(ROLE_DOCUMENTS.keys()))
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--resume", action="store_true", help="Resume existing session if tmp/session_id.txt exists")
    args = parser.parse_args()

    if args.resume:
        existing = read_session_id()
        if existing:
            print_json({"ok": True, "session_id": existing, "role": args.role, "resumed": True})
            return

    session_id = generate_session_id()
    write_session_id(session_id, role=args.role)

    doc_path = Path(ROLE_DOCUMENTS[args.role])
    doc_exists = doc_path.exists()
    doc_content = doc_path.read_text(encoding="utf-8") if doc_exists else ""

    bus = AgentBus(db_path=args.db)

    # Register in live_agents so dashboard sees every session (manual + spawned).
    # Spawned sessions have a pre-existing row (from agent_launcher_db) with a different
    # session_id (full UUID vs our 12-char hex). Stop that row — we take over identity.
    bus._conn.execute(
        """UPDATE live_agents SET status = 'stopped', stopped_at = datetime('now')
           WHERE role = ? AND status IN ('starting', 'active') AND session_id != ?""",
        (args.role, session_id),
    )
    bus._conn.execute(
        """INSERT INTO live_agents (session_id, role, status, spawned_by, last_activity)
           VALUES (?, ?, 'active', 'manual', datetime('now'))
           ON CONFLICT(session_id) DO UPDATE SET
             status = 'active',
             last_activity = datetime('now')""",
        (session_id, args.role),
    )
    bus._conn.commit()

    bus.add_session_log(
        role=args.role,
        content="session started",
        session_id=session_id,
    )

    # Load config and gather context
    try:
        config = load_config(args.role)
        context = get_context(args.role, config, bus)
    except (FileNotFoundError, ValueError) as e:
        print_json({"ok": False, "error": str(e)})
        return

    print_json({
        "ok": True,
        "session_id": session_id,
        "role": args.role,
        "doc_path": str(doc_path),
        "doc_exists": doc_exists,
        "doc_content": doc_content,
        "context": context,
        "resumed": False,
    })


if __name__ == "__main__":
    main()
