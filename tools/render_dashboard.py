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
    """Render status.md — live agents, inbox summary, pending handoffs."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# Status mrowiska\n", f"*Wygenerowano: {now}*\n"]

    # Live agents
    agents = conn.execute(
        """SELECT role, task, status, created_at
           FROM live_agents WHERE status IN ('starting', 'active')
           ORDER BY created_at DESC"""
    ).fetchall()
    lines.append("## Aktywni agenci\n")
    if agents:
        lines.append("| Rola | Task | Status | Od |")
        lines.append("|------|------|--------|----|")
        for a in agents:
            lines.append(f"| {a['role']} | {a['task'] or '-'} | {a['status']} | {a['created_at']} |")
    else:
        lines.append("Brak aktywnych agentow.\n")

    # Inbox summary
    inbox = conn.execute(
        """SELECT recipient, COUNT(*) as cnt
           FROM messages WHERE status = 'unread'
           GROUP BY recipient ORDER BY cnt DESC"""
    ).fetchall()
    lines.append("\n## Inbox (unread)\n")
    if inbox:
        lines.append("| Rola | Nieprzeczytane |")
        lines.append("|------|---------------|")
        for i in inbox:
            lines.append(f"| {i['recipient']} | {i['cnt']} |")
    else:
        lines.append("Wszystkie inboxy puste.\n")

    # Pending handoffs
    pending = conn.execute(
        """SELECT m.sender, m.recipient, m.title, m.created_at
           FROM messages m
           LEFT JOIN live_agents la
             ON la.role = m.recipient AND la.status IN ('starting', 'active')
           WHERE m.type = 'handoff' AND m.status = 'unread' AND la.id IS NULL
           ORDER BY m.created_at DESC"""
    ).fetchall()
    lines.append("\n## Handoffy oczekujace\n")
    if pending:
        lines.append("| Od | Do | Tytul | Data |")
        lines.append("|----|-----|-------|------|")
        for p in pending:
            lines.append(f"| {p['sender']} | {p['recipient']} | {p['title']} | {p['created_at']} |")
    else:
        lines.append("Brak oczekujacych handoffow.\n")

    return "\n".join(lines) + "\n"


def _render_workstreams(conn: sqlite3.Connection) -> str:
    """Render workstreams.md — running workflows, in-progress backlog."""
    lines = ["# Aktywne watki pracy\n"]

    # Running workflows
    workflows = conn.execute(
        """SELECT id, workflow_id, role, started_at
           FROM workflow_execution WHERE status = 'running'
           ORDER BY started_at DESC"""
    ).fetchall()
    lines.append("## Workflow w toku\n")
    if workflows:
        lines.append("| ID | Workflow | Rola | Start |")
        lines.append("|----|----------|------|-------|")
        for w in workflows:
            lines.append(f"| {w['id']} | {w['workflow_id']} | {w['role']} | {w['started_at']} |")
    else:
        lines.append("Brak aktywnych workflow.\n")

    # In-progress backlog
    tasks = conn.execute(
        """SELECT id, title, area, value
           FROM backlog WHERE status = 'in_progress'
           ORDER BY area, id"""
    ).fetchall()
    lines.append("\n## Backlog in_progress\n")
    if tasks:
        lines.append("| ID | Tytul | Area | Priorytet |")
        lines.append("|----|-------|------|-----------|")
        for t in tasks:
            lines.append(f"| {t['id']} | {t['title']} | {t['area']} | {t['value'] or '-'} |")
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
