"""Generate markdown dashboard files from mrowisko.db.

Labels and translations from config/dashboard_config.json.
Designed for 5s auto-refresh — queries are simple SELECTs.

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

DISPLAY_STATUS_LABELS = {
    "working": "Praca",
    "stale": "Stoi",
    "dead": "Martwy",
    "starting": "Startuje",
    "stopped": "Stop",
}


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


def _display_status_label(display_status: str) -> str:
    return DISPLAY_STATUS_LABELS.get(display_status, display_status)


def _render_status(conn: sqlite3.Connection, cfg: dict) -> str:
    now = datetime.now()
    c = lambda sql: conn.execute(sql).fetchone()[0]
    L = lambda k: _l(cfg, k)
    sess_n = c("SELECT COUNT(*) FROM v_agent_status")
    wf_n = c("SELECT COUNT(*) FROM workflow_execution WHERE status='running'")
    planned = c("SELECT COUNT(*) FROM backlog WHERE status='planned'")
    unread = c("SELECT COUNT(*) FROM messages WHERE status='unread'")
    lines = [
        f"{now.strftime('%d . %m')}                                                                                                   **{now.strftime('%H:%M')}**",
        "",
        f"**{L('sessions')}**                    {sess_n}",
        f"{L('workflow')}             {wf_n}",
    ]
    # Sessions table — from v_agent_status view
    sessions = conn.execute(
        """SELECT role, session_id, display_status, task, created_at
           FROM v_agent_status
           ORDER BY created_at DESC"""
    ).fetchall()
    if sessions:
        lines += [""]
        lines.append(f"| **{L('sessions')}** | **Status** | **Kontekst** |")
        lines.append("| --------------- | ------------- | ------------ |")
        for s in sessions:
            status = _display_status_label(s["display_status"])
            task = s["task"] or ""
            lines.append(f"| {s['role']} | {status} | {task} |")
    # Tasks / Messages mini table
    lines += [""]
    lines.append(f"| {L('tasks_label')} | {L('messages_label')} |")
    lines.append("| :-----: | :--------: |")
    lines.append(f"| **{planned}** | **{unread}** |")
    # Unread per role — right-aligned numbers
    rows = conn.execute(
        "SELECT recipient, COUNT(*) as n FROM messages WHERE status='unread' GROUP BY recipient ORDER BY n DESC"
    ).fetchall()
    if rows:
        lines += [""]
        lines.append(f"| **{L('role')}** | {L('unread')} |")
        lines.append("| --------------- | -------------: |")
        for r in rows:
            lines.append(f"| {r['recipient']} | {r['n']} |")
    return "\n".join(lines) + "\n"


def _render_workstreams(conn: sqlite3.Connection, cfg: dict) -> str:
    L = lambda k: _l(cfg, k)
    completed_today = conn.execute(
        "SELECT COUNT(*) FROM workflow_execution WHERE status='completed' AND ended_at > datetime('now', 'start of day')"
    ).fetchone()[0]
    lines = [
        f"{L('completed_today')}                {completed_today}",
    ]
    # Workflows aggregated
    wf_agg = conn.execute(
        """SELECT workflow_id, COUNT(*) as cnt
           FROM workflow_execution WHERE status='running'
           GROUP BY workflow_id ORDER BY cnt DESC"""
    ).fetchall()
    if wf_agg:
        lines += [""]
        lines.append(f"| **{L('workflow_running')}** | **{L('count')}** | **{L('stage')}** |")
        lines.append("| ---------------------- | ------------------- | -------- |")
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
    # In-progress backlog — no ID column
    tasks = conn.execute(
        "SELECT title, area FROM backlog WHERE status='in_progress' ORDER BY area"
    ).fetchall()
    if tasks:
        maxl = cfg["max_title_length"]
        lines += [""]
        lines.append(f"| **{L('area')}** | **{L('task_in_progress')}** |")
        lines.append("| ---------- | --------------------------------------------- |")
        for t in tasks:
            lines.append(f"| {t['area']} | {_trunc(t['title'], maxl)} |")
    return "\n".join(lines) + "\n"


def _render_backlog(conn: sqlite3.Connection, cfg: dict) -> str:
    total_planned = conn.execute("SELECT COUNT(*) FROM backlog WHERE status='planned'").fetchone()[0]
    total_deferred = conn.execute("SELECT COUNT(*) FROM backlog WHERE status='deferred'").fetchone()[0]
    open_suggestions = conn.execute("SELECT COUNT(*) FROM suggestions WHERE status='open'").fetchone()[0]
    top_n = cfg["top_n"]
    L = lambda k: _l(cfg, k)
    maxl = cfg["max_title_length"]
    lines = [
        f"**{L('planned')}**      {total_planned}",
        f"{L('deferred')}            {total_deferred}",
        f"{L('suggestions')}            {open_suggestions}",
    ]
    # Top N planned — uses v_backlog_scored view
    rows = conn.execute("""
        SELECT id, title, score
        FROM v_backlog_scored WHERE status='planned'
        ORDER BY score DESC, id
        LIMIT ?
    """, (top_n,)).fetchall()
    if rows:
        lines += [""]
        lines.append(f"| **{L('number')}** | **{L('task_in_queue')}** | **{L('score')}** |")
        lines.append("| --------- | --------------------------------------------- | ------- |")
        for r in rows:
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
