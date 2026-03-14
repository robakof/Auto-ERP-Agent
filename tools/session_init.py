"""Session initializer — generates session ID and loads role context.

Usage:
    python tools/session_init.py --role erp_specialist
    python tools/session_init.py --role developer

Returns JSON with session_id and role prompt path.
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
SESSION_ID_FILE = Path("tmp/session_id.txt")

ROLE_DOCUMENTS = {
    "erp_specialist": "documents/erp_specialist/ERP_SPECIALIST.md",
    "analyst":        "documents/analyst/ANALYST.md",
    "developer":      "documents/dev/DEVELOPER.md",
    "metodolog":      "documents/methodology/METHODOLOGY.md",
}


def generate_session_id() -> str:
    return uuid.uuid4().hex[:12]


def write_session_id(session_id: str) -> None:
    SESSION_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_ID_FILE.write_text(session_id, encoding="utf-8")


def read_session_id() -> str | None:
    if SESSION_ID_FILE.exists():
        return SESSION_ID_FILE.read_text(encoding="utf-8").strip()
    return None


def main():
    parser = argparse.ArgumentParser(description="Initialize agent session")
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
    write_session_id(session_id)

    doc_path = Path(ROLE_DOCUMENTS[args.role])
    doc_exists = doc_path.exists()

    bus = AgentBus(db_path=args.db)
    bus.add_session_log(
        role=args.role,
        content=f"session started",
        session_id=session_id,
    )

    print_json({
        "ok": True,
        "session_id": session_id,
        "role": args.role,
        "doc_path": str(doc_path),
        "doc_exists": doc_exists,
        "resumed": False,
    })


if __name__ == "__main__":
    main()
