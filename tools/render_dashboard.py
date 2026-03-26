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
    """Render workstreams.md — aggregated workflows + in-progress table."""
    # Counts for header
    wf_count = conn.execute(
        "SELECT COUNT(*) FROM workflow_execution WHERE status = 'running'"
    ).fetchone()[0]
    ip_count = conn.execute(
        "SELECT COUNT(*) FROM backlog WHERE status = 'in_progress'"
    ).fetchone()[0]

    lines = [
        "# Aktywne watki\n",
        f"**Workflow running:** {wf_count} | **Backlog in_progress:** {ip_count}\n",
        "---\n",
    ]

    # Workflows aggregated by type
    wf_agg = conn.execute(
        """SELECT workflow_id, COUNT(*) as cnt
           FROM workflow_execution WHERE status = 'running'
           GROUP BY workflow_id ORDER BY cnt DESC"""
    ).fetchall()
    if wf_agg:
        lines.append("## Workflow\n")
        for wf in wf_agg:
            if wf["cnt"] == 1:
                # Single — show role and step progress
                detail = conn.execute(
                    """SELECT we.id, we.role,
                              (SELECT COUNT(*) FROM step_log sl WHERE sl.execution_id = we.id) as steps_done
                       FROM workflow_execution we
                       WHERE we.workflow_id = ? AND we.status = 'running'""",
                    (wf["workflow_id"],),
                ).fetchone()
                step_info = f" — etap {detail['steps_done']}" if detail["steps_done"] else ""
                lines.append(f"- **{wf['workflow_id']}** ({detail['role']}){step_info}")
            else:
                lines.append(f"- **{wf['workflow_id']}** x{wf['cnt']}")
        lines.append("")

    # In-progress backlog — table
    tasks = conn.execute(
        """SELECT id, title, area, value
           FROM backlog WHERE status = 'in_progress'
           ORDER BY area, id"""
    ).fetchall()
    if tasks:
        lines.append("## In progress\n")
        lines.append("| ID | Area | Tytul | Priorytet |")
        lines.append("|----|------|-------|-----------|")
        for t in tasks:
            lines.append(f"| {t['id']} | {t['area']} | {t['title']} | {t['value'] or '-'} |")
        lines.append("")

    return "\n".join(lines) + "\n"


def _render_backlog_overview(conn: sqlite3.Connection) -> str:
    """Render backlog_overview.md — summary table + planned tasks per area."""
    # Total + per-area summary
    area_counts = conn.execute(
        """SELECT area, COUNT(*) as cnt
           FROM backlog WHERE status = 'planned'
           GROUP BY area ORDER BY cnt DESC"""
    ).fetchall()
    total = sum(r["cnt"] for r in area_counts)

    lines = [
        "# Backlog\n",
        f"**Total planned:** {total}\n",
    ]

    if area_counts:
        lines.append("| Area | Planned | Est. context |")
        lines.append("|------|---------|-------------|")
        for r in area_counts:
            lines.append(f"| {r['area']} | {r['cnt']} | - |")
        lines.append("")

    lines.append("---\n")

    # Detailed tasks per area
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
