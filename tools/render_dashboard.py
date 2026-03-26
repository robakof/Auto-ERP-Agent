"""Generate markdown dashboard files from mrowisko.db.

Labels and translations from config/dashboard_config.json.

Usage:
    py tools/render_dashboard.py
    py tools/render_dashboard.py --output-dir documents/human/dashboard
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.lib.agent_bus import AgentBus
from tools.lib.output import print_json

DB_PATH = "mrowisko.db"
DEFAULT_OUTPUT = "documents/human/dashboard"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "dashboard_config.json"

SCORE_SQL = """
ROUND(
  (CASE value WHEN 'wysoka' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END +
   CASE effort WHEN 'mala' THEN 3 WHEN 'srednia' THEN 2 ELSE 1 END - 2
  ) * 9.0 / 4 + 1
)
"""


def _load_config() -> dict:
    defaults = {
        "max_title_length": 45,
        "top_n": 10,
        "labels": {},
        "status_translations": {},
        "workflow_translations": {},
    }
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            defaults.update(cfg)
        except Exception:
            pass
    return defaults


def _l(cfg: dict, key: str) -> str:
    return cfg["labels"].get(key, key)


def _tw(cfg: dict, workflow_id: str) -> str:
    return cfg.get("workflow_translations", {}).get(workflow_id, workflow_id)


def _trunc(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _session_status(conn: sqlite3.Connection, role: str) -> str:
    """Determine session status: Praca / Czeka / Stoi / empty."""
    wf = conn.execute(
        """SELECT we.id,
                  (SELECT COUNT(*) FROM step_log sl WHERE sl.execution_id = we.id) as steps,
                  we.started_at
           FROM workflow_execution we
           WHERE we.role = ? AND we.status = 'running'
           ORDER BY we.started_at DESC LIMIT 1""",
        (role,),
    ).fetchone()
    if not wf:
        return "Stoi"
    return "Praca"


def _render_status(conn: sqlite3.Connection, cfg: dict) -> str:
    now = datetime.now()
    c = lambda sql: conn.execute(sql).fetchone()[0]
    unread = c("SELECT COUNT(*) FROM messages WHERE status='unread'")
    L = lambda k: _l(cfg, k)
    sess_n = c("SELECT COUNT(DISTINCT role) FROM session_log WHERE content LIKE '%session started%' AND created_at > datetime('now', '-24 hours')")
    wf = c("SELECT COUNT(*) FROM workflow_execution WHERE status='running'")
    ip = c("SELECT COUNT(*) FROM backlog WHERE status='in_progress'")
    planned = c("SELECT COUNT(*) FROM backlog WHERE status='planned'")
    lines = [
        f"**{now.strftime('%H:%M')}** {now.strftime('%Y-%m-%d')}",
        "",
        "| Metryka | |",
        "|---|---|",
        f"| {L('sessions')} | **{sess_n}** |",
        f"| {L('unread')} | **{unread}** |",
        f"| {L('workflow')} | **{wf}** |",
        f"| {L('in_progress')} | **{ip}** |",
        f"| {L('planned')} | **{planned}** |",
    ]
    # Sessions
    sessions = conn.execute(
        """SELECT role, session_id, created_at
           FROM session_log
           WHERE content LIKE '%session started%'
             AND created_at > datetime('now', '-24 hours')
           GROUP BY role
           HAVING created_at = MAX(created_at)
           ORDER BY created_at DESC"""
    ).fetchall()
    if sessions:
        lines += ["", f"#### {L('sessions')}", ""]
        lines.append(f"| {L('role')} | Status | Kontekst |")
        lines.append("|------|--------|----------|")
        for s in sessions:
            status = _session_status(conn, s["role"])
            lines.append(f"| {s['role']} | {status} | |")
    # Unread per role
    rows = conn.execute(
        "SELECT recipient, COUNT(*) as n FROM messages WHERE status='unread' GROUP BY recipient ORDER BY n DESC"
    ).fetchall()
    if rows:
        lines += ["", f"#### {L('unread')}", ""]
        lines.append(f"| {L('role')} | # |")
        lines.append("|------|---|")
        for r in rows:
            lines.append(f"| {r['recipient']} | {r['n']} |")
    return "\n".join(lines) + "\n"


def _render_workstreams(conn: sqlite3.Connection, cfg: dict) -> str:
    wf_n = conn.execute("SELECT COUNT(*) FROM workflow_execution WHERE status='running'").fetchone()[0]
    ip_n = conn.execute("SELECT COUNT(*) FROM backlog WHERE status='in_progress'").fetchone()[0]
    L = lambda k: _l(cfg, k)
    lines = [
        f"{L('workflow')} **{wf_n}** {L('in_progress')} **{ip_n}**",
    ]
    # Workflows aggregated
    wf_agg = conn.execute(
        """SELECT workflow_id, COUNT(*) as cnt
           FROM workflow_execution WHERE status='running'
           GROUP BY workflow_id ORDER BY cnt DESC"""
    ).fetchall()
    if wf_agg:
        lines += ["", f"#### {L('workflow')}", ""]
        lines.append(f"| {L('type')} | {L('count')} | {L('stage')} |")
        lines.append("|-----|-----|------|")
        for wf in wf_agg:
            name = _tw(cfg, wf["workflow_id"])
            if wf["cnt"] == 1:
                detail = conn.execute(
                    """SELECT we.role,
                              (SELECT COUNT(*) FROM step_log sl WHERE sl.execution_id=we.id) as steps
                       FROM workflow_execution we
                       WHERE we.workflow_id=? AND we.status='running'""",
                    (wf["workflow_id"],),
                ).fetchone()
                step = str(detail["steps"]) if detail["steps"] else "-"
                lines.append(f"| {name} | 1 ({detail['role']}) | {step} |")
            else:
                lines.append(f"| {name} | {wf['cnt']} | - |")
    # In-progress backlog
    tasks = conn.execute(
        "SELECT id, title, area FROM backlog WHERE status='in_progress' ORDER BY area, id"
    ).fetchall()
    if tasks:
        maxl = cfg["max_title_length"]
        lines += ["", f"#### {L('in_progress')}", ""]
        lines.append(f"| {L('id')} | {L('area')} | {L('task')} |")
        lines.append("|----|------|------|")
        for t in tasks:
            lines.append(f"| {t['id']} | {t['area']} | {_trunc(t['title'], maxl)} |")
    return "\n".join(lines) + "\n"


def _render_backlog(conn: sqlite3.Connection, cfg: dict) -> str:
    total_planned = conn.execute("SELECT COUNT(*) FROM backlog WHERE status='planned'").fetchone()[0]
    total_deferred = conn.execute("SELECT COUNT(*) FROM backlog WHERE status='deferred'").fetchone()[0]
    open_suggestions = conn.execute("SELECT COUNT(*) FROM suggestions WHERE status='open'").fetchone()[0]
    top_n = cfg["top_n"]
    L = lambda k: _l(cfg, k)
    maxl = cfg["max_title_length"]
    lines = [
        f"{L('planned')} **{total_planned}** {L('deferred')} **{total_deferred}** {L('suggestions')} **{open_suggestions}**",
    ]
    # Top N planned
    rows = conn.execute(f"""
        SELECT id, title, {SCORE_SQL} as score
        FROM backlog WHERE status='planned'
        ORDER BY score DESC, id
        LIMIT ?
    """, (top_n,)).fetchall()
    if rows:
        lines += ["", f"#### {L('planned')}", ""]
        lines.append(f"| {L('id')} | {L('task')} | {L('score')} |")
        lines.append("|----|------|---|")
        for r in rows:
            lines.append(f"| {r['id']} | {_trunc(r['title'], maxl)} | {int(r['score'])} |")
    # Deferred
    deferred = conn.execute(f"""
        SELECT id, title, {SCORE_SQL} as score
        FROM backlog WHERE status='deferred'
        ORDER BY score DESC, id
        LIMIT ?
    """, (top_n,)).fetchall()
    if deferred:
        lines += ["", f"#### {L('deferred')}", ""]
        lines.append(f"| {L('id')} | {L('task')} | {L('score')} |")
        lines.append("|----|------|---|")
        for r in deferred:
            lines.append(f"| {r['id']} | {_trunc(r['title'], maxl)} | {int(r['score'])} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate markdown dashboard from mrowisko.db")
    parser.add_argument("--db", default=DB_PATH, help="Path to mrowisko.db")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT, help="Output directory for .md files")
    args = parser.parse_args()

    cfg = _load_config()
    bus = AgentBus(db_path=args.db)
    conn = bus._conn
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    L = lambda k: _l(cfg, k)
    files = {
        f"{L('header_status')}.md": _render_status(conn, cfg),
        f"{L('header_work')}.md": _render_workstreams(conn, cfg),
        f"{L('header_queue')}.md": _render_backlog(conn, cfg),
    }

    # Clean old files
    for old in ["status.md", "workstreams.md", "backlog_overview.md",
                "Status.md", "Praca.md", "Kolejka.md"]:
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
