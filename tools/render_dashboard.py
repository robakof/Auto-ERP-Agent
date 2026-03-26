"""Generate markdown dashboard files from mrowisko.db.

Produces Obsidian-friendly .md files in output directory:
- status.md — live agents, inbox summary, pending handoffs
- workstreams.md — running workflows, in-progress backlog
- backlog_overview.md — planned tasks per area with priorities

Usage:
    py tools/render_dashboard.py
    py tools/render_dashboard.py --output-dir documents/human/dashboard
    py tools/render_dashboard.py --db mrowisko.db
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json

DB_PATH = "mrowisko.db"
DEFAULT_OUTPUT = "documents/human/dashboard"


def _render_status(conn: sqlite3.Connection) -> str:
    """Render status.md — compact metrics header + details below."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Collect counts
    agent_count = conn.execute(
        "SELECT COUNT(*) FROM live_agents WHERE status IN ('starting', 'active')"
    ).fetchone()[0]
    unread_total = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE status = 'unread'"
    ).fetchone()[0]
    handoff_count = conn.execute(
        """SELECT COUNT(*) FROM messages m
           LEFT JOIN live_agents la ON la.role = m.recipient AND la.status IN ('starting', 'active')
           WHERE m.type = 'handoff' AND m.status = 'unread' AND la.id IS NULL"""
    ).fetchone()[0]
    workflow_count = conn.execute(
        "SELECT COUNT(*) FROM workflow_execution WHERE status = 'running'"
    ).fetchone()[0]
    backlog_ip = conn.execute(
        "SELECT COUNT(*) FROM backlog WHERE status = 'in_progress'"
    ).fetchone()[0]
    backlog_planned = conn.execute(
        "SELECT COUNT(*) FROM backlog WHERE status = 'planned'"
    ).fetchone()[0]

    lines = [
        f"# Mrowisko — {now}\n",
        f"**Agenci:** {agent_count} | "
        f"**Unread:** {unread_total} | "
        f"**Handoffy pending:** {handoff_count} | "
        f"**Workflow running:** {workflow_count} | "
        f"**Backlog:** {backlog_ip} in_progress, {backlog_planned} planned\n",
        "---\n",
    ]

    # Live agents — compact
    agents = conn.execute(
        """SELECT role, task, created_at
           FROM live_agents WHERE status IN ('starting', 'active')
           ORDER BY created_at DESC"""
    ).fetchall()
    if agents:
        lines.append("## Agenci\n")
        for a in agents:
            lines.append(f"- **{a['role']}** — {a['task'] or '(brak task)'}")
        lines.append("")

    # Inbox — one-liner per role
    inbox = conn.execute(
        """SELECT recipient, COUNT(*) as cnt
           FROM messages WHERE status = 'unread'
           GROUP BY recipient ORDER BY cnt DESC"""
    ).fetchall()
    if inbox:
        lines.append("## Inbox\n")
        lines.append(" | ".join(f"**{i['recipient']}** {i['cnt']}" for i in inbox))
        lines.append("")

    # Pending handoffs — compact
    pending = conn.execute(
        """SELECT m.sender, m.recipient, m.title
           FROM messages m
           LEFT JOIN live_agents la
             ON la.role = m.recipient AND la.status IN ('starting', 'active')
           WHERE m.type = 'handoff' AND m.status = 'unread' AND la.id IS NULL
           ORDER BY m.created_at DESC"""
    ).fetchall()
    if pending:
        lines.append("## Handoffy pending\n")
        for p in pending:
            lines.append(f"- {p['sender']} -> {p['recipient']}: {p['title']}")
        lines.append("")

    return "\n".join(lines) + "\n"


def _render_workstreams(conn: sqlite3.Connection) -> str:
    """Render workstreams.md — running workflows, in-progress backlog."""
    lines = ["# Aktywne watki\n"]

    # Running workflows — compact
    workflows = conn.execute(
        """SELECT id, workflow_id, role, started_at
           FROM workflow_execution WHERE status = 'running'
           ORDER BY started_at DESC"""
    ).fetchall()
    if workflows:
        lines.append("## Workflow\n")
        for w in workflows:
            lines.append(f"- **#{w['id']}** {w['role']}/{w['workflow_id']} (od {w['started_at'][:10]})")
        lines.append("")
    else:
        lines.append("Brak aktywnych workflow.\n")

    # In-progress backlog — compact
    tasks = conn.execute(
        """SELECT id, title, area, value
           FROM backlog WHERE status = 'in_progress'
           ORDER BY area, id"""
    ).fetchall()
    if tasks:
        lines.append("## In progress\n")
        for t in tasks:
            prio = f"[{t['value']}]" if t['value'] else ""
            lines.append(f"- **#{t['id']}** [{t['area']}] {t['title']} {prio}")
        lines.append("")
    else:
        lines.append("Brak taskow w toku.\n")

    return "\n".join(lines) + "\n"


def _render_backlog_overview(conn: sqlite3.Connection) -> str:
    """Render backlog_overview.md — planned tasks per area with priorities."""
    lines = ["# Backlog — planned\n"]

    tasks = conn.execute(
        """SELECT id, title, area, value, effort, depends_on
           FROM backlog WHERE status = 'planned'
           ORDER BY area,
                    CASE value WHEN 'wysoka' THEN 1 WHEN 'srednia' THEN 2 WHEN 'niska' THEN 3 ELSE 4 END,
                    id"""
    ).fetchall()

    if not tasks:
        lines.append("Brak zaplanowanych taskow.\n")
        return "\n".join(lines) + "\n"

    current_area = None
    for t in tasks:
        if t["area"] != current_area:
            current_area = t["area"]
            lines.append(f"\n## {current_area}\n")
            lines.append("| ID | Tytul | Priorytet | Effort | Depends |")
            lines.append("|----|-------|-----------|--------|---------|")
        dep = f"#{t['depends_on']}" if t["depends_on"] else "-"
        lines.append(f"| {t['id']} | {t['title']} | {t['value'] or '-'} | {t['effort'] or '-'} | {dep} |")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate markdown dashboard from mrowisko.db")
    parser.add_argument("--db", default=DB_PATH, help="Path to mrowisko.db")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT, help="Output directory for .md files")
    args = parser.parse_args()

    bus = AgentBus(db_path=args.db)
    conn = bus._conn
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    files = {
        "status.md": _render_status(conn),
        "workstreams.md": _render_workstreams(conn),
        "backlog_overview.md": _render_backlog_overview(conn),
    }

    for name, content in files.items():
        (output / name).write_text(content, encoding="utf-8")

    print_json({
        "ok": True,
        "output_dir": str(output),
        "files_written": len(files),
        "files": list(files.keys()),
    })


if __name__ == "__main__":
    main()
