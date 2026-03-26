"""Generate markdown dashboard files from mrowisko.db.

Produces Obsidian-friendly .md files in output directory:
- Status.md — live agents, inbox, pending handoffs
- Praca.md — running workflows, in-progress backlog
- Kolejka.md — top 10 planned tasks by priority score

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

SCORE_SQL = """
ROUND(
  (CASE value WHEN 'wysoka' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END +
   CASE effort WHEN 'mala' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END - 2
  ) * 9.0 / 4 + 1
)
"""


def _render_status(conn: sqlite3.Connection) -> str:
    """Render Status.md — metrics + agents + inbox + handoffs."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c = lambda sql: conn.execute(sql).fetchone()[0]
    agents = c("SELECT COUNT(*) FROM live_agents WHERE status IN ('starting','active')")
    unread = c("SELECT COUNT(*) FROM messages WHERE status='unread'")
    handoffs = c(
        """SELECT COUNT(*) FROM messages m
           LEFT JOIN live_agents la ON la.role=m.recipient AND la.status IN ('starting','active')
           WHERE m.type='handoff' AND m.status='unread' AND la.id IS NULL""")
    wf = c("SELECT COUNT(*) FROM workflow_execution WHERE status='running'")
    ip = c("SELECT COUNT(*) FROM backlog WHERE status='in_progress'")
    planned = c("SELECT COUNT(*) FROM backlog WHERE status='planned'")
    lines = [
        f"# Mrowisko {now}",
        f"Agenci **{agents}** Unread **{unread}** Handoffy **{handoffs}** Workflow **{wf}** Backlog **{ip}** w toku **{planned}** planned",
        "---"]
    # Agents
    rows = conn.execute(
        "SELECT role, task FROM live_agents WHERE status IN ('starting','active') ORDER BY created_at DESC"
    ).fetchall()
    if rows:
        lines.append("## Agenci")
        lines.append("| Rola | Task |")
        lines.append("|------|------|")
        for a in rows:
            lines.append(f"| {a['role']} | {a['task'] or '-'} |")
    # Inbox
    rows = conn.execute(
        "SELECT recipient, COUNT(*) as n FROM messages WHERE status='unread' GROUP BY recipient ORDER BY n DESC"
    ).fetchall()
    if rows:
        lines.append("## Inbox")
        lines.append(" ".join(f"**{r['recipient']}** {r['n']}" for r in rows))
    # Handoffs
    rows = conn.execute(
        """SELECT m.sender, m.recipient, m.title FROM messages m
           LEFT JOIN live_agents la ON la.role=m.recipient AND la.status IN ('starting','active')
           WHERE m.type='handoff' AND m.status='unread' AND la.id IS NULL
           ORDER BY m.created_at DESC"""
    ).fetchall()
    if rows:
        lines.append("## Handoffy")
        for p in rows:
            lines.append(f"- {p['sender']} > {p['recipient']}: {p['title']}")
    return "\n".join(lines) + "\n"


def _render_workstreams(conn: sqlite3.Connection) -> str:
    """Render Praca.md — workflows aggregated + in-progress table."""
    wf_n = conn.execute("SELECT COUNT(*) FROM workflow_execution WHERE status='running'").fetchone()[0]
    ip_n = conn.execute("SELECT COUNT(*) FROM backlog WHERE status='in_progress'").fetchone()[0]
    lines = [
        "# Praca",
        f"Workflow **{wf_n}** In progress **{ip_n}**",
        "---"]
    # Workflows aggregated
    wf_agg = conn.execute(
        """SELECT workflow_id, COUNT(*) as cnt
           FROM workflow_execution WHERE status='running'
           GROUP BY workflow_id ORDER BY cnt DESC"""
    ).fetchall()
    if wf_agg:
        lines.append("## Workflow")
        lines.append("| Typ | Ile | Etap |")
        lines.append("|-----|-----|------|")
        for wf in wf_agg:
            if wf["cnt"] == 1:
                detail = conn.execute(
                    """SELECT we.role,
                              (SELECT COUNT(*) FROM step_log sl WHERE sl.execution_id=we.id) as steps
                       FROM workflow_execution we
                       WHERE we.workflow_id=? AND we.status='running'""",
                    (wf["workflow_id"],),
                ).fetchone()
                step = str(detail["steps"]) if detail["steps"] else "-"
                lines.append(f"| {wf['workflow_id']} | 1 ({detail['role']}) | {step} |")
            else:
                lines.append(f"| {wf['workflow_id']} | {wf['cnt']} | - |")
    # In-progress backlog
    tasks = conn.execute(
        "SELECT id, title, area, value FROM backlog WHERE status='in_progress' ORDER BY area, id"
    ).fetchall()
    if tasks:
        lines.append("## In progress")
        lines.append("| ID | Area | Tytul | Priorytet |")
        lines.append("|----|------|-------|-----------|")
        for t in tasks:
            lines.append(f"| {t['id']} | {t['area']} | {t['title']} | {t['value'] or '-'} |")
    return "\n".join(lines) + "\n"


def _render_backlog(conn: sqlite3.Connection) -> str:
    """Render Kolejka.md — top 10 by score (impact/effort)."""
    total = conn.execute("SELECT COUNT(*) FROM backlog WHERE status='planned'").fetchone()[0]
    lines = [
        "# Kolejka",
        f"Planned **{total}**",
        "---"]
    # Top 10 scored
    rows = conn.execute(f"""
        SELECT id, title, value, effort, {SCORE_SQL} as score
        FROM backlog WHERE status='planned'
        ORDER BY score DESC, id
        LIMIT 10
    """).fetchall()
    if rows:
        lines.append("| # | Pkt | ID | Tytul | Efekt | Wysilek |")
        lines.append("|---|-----|----|-------|-------|---------|")
        for i, r in enumerate(rows, 1):
            lines.append(
                f"| {i} | {int(r['score'])} | {r['id']} | {r['title']} | {r['value'] or '-'} | {r['effort'] or '-'} |")
    else:
        lines.append("Brak zaplanowanych zadan.")
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
        "Status.md": _render_status(conn),
        "Praca.md": _render_workstreams(conn),
        "Kolejka.md": _render_backlog(conn),
    }

    # Clean old files
    for old in ["status.md", "workstreams.md", "backlog_overview.md"]:
        old_path = output / old
        if old_path.exists():
            old_path.unlink()

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
