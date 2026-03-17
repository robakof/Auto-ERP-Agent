"""Mrowisko Runner — Faza 1 PoC z approval gate.

Czyta inbox wybranej roli (typ: task), wyświetla zadanie człowiekowi,
wywołuje agenta Claude Code CLI po zatwierdzeniu i loguje wynik.

Użycie:
    python tools/mrowisko_runner.py --role erp_specialist
    python tools/mrowisko_runner.py --role erp_specialist --db mrowisko.db
"""

import argparse
import json
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DB_DEFAULT = str(PROJECT_ROOT / "mrowisko.db")

# Permission mode per role
PERMISSION_MODE: dict[str, str] = {
    "erp_specialist": "acceptEdits",
    "analyst": "acceptEdits",
    "developer": "default",
}

# Tool scope per role
TOOL_SCOPE: dict[str, str] = {
    "erp_specialist": "Read,Grep,Glob,Bash",
    "analyst": "Read,Grep,Glob",
    "developer": "Read,Grep,Glob,Bash,Write,Edit",
}

MAX_TURNS = "8"
MAX_BUDGET_USD = "1.50"
TIMEOUT_SEC = 600


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_CREATE_INVOCATION_LOG = """
CREATE TABLE IF NOT EXISTS invocation_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT,
    parent_session_id TEXT,
    from_role         TEXT,
    to_role           TEXT,
    task_id           INTEGER,
    depth             INTEGER NOT NULL DEFAULT 0,
    turns             INTEGER,
    cost_usd          REAL,
    status            TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


def ensure_invocation_log(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(_CREATE_INVOCATION_LOG)
    conn.commit()
    conn.close()


def get_pending_tasks(db_path: str, role: str) -> list[dict]:
    """Return unread task messages for *role*, ordered by created_at ASC."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, sender, recipient, type, content, created_at
        FROM messages
        WHERE recipient = ? AND type = 'task' AND status = 'unread'
        ORDER BY created_at ASC
        """,
        (role,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_message_read(db_path: str, msg_id: int) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE messages SET status = 'read', read_at = datetime('now') WHERE id = ?",
        (msg_id,),
    )
    conn.commit()
    conn.close()


def log_invocation(
    db_path: str,
    session_id: str,
    from_role: str,
    to_role: str,
    task_id: int,
    turns: int,
    cost_usd: float,
    status: str,
) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO invocation_log
            (session_id, from_role, to_role, task_id, turns, cost_usd, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (session_id, from_role, to_role, task_id, turns, cost_usd, status),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Stream-json renderer
# ---------------------------------------------------------------------------

def render_event(event: dict) -> dict | None:
    """Print event to stdout. Returns result event if this is the final one."""
    etype = event.get("type", "")

    if etype == "assistant":
        for block in event.get("message", {}).get("content", []):
            btype = block.get("type", "")
            if btype == "text":
                print(block["text"], end="", flush=True)
            elif btype == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {})
                inp_preview = str(inp)[:120].replace("\n", " ")
                print(f"\n[tool: {name}] {inp_preview}", flush=True)

    elif etype == "user":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_result" and block.get("is_error"):
                print("\n[tool error]", flush=True)

    elif etype == "result":
        return event

    return None


# ---------------------------------------------------------------------------
# Agent invocation
# ---------------------------------------------------------------------------

def build_cmd(role: str, prompt: str) -> list[str]:
    permission_mode = PERMISSION_MODE.get(role, "default")
    tool_scope = TOOL_SCOPE.get(role, "Read,Grep,Glob")
    return [
        "claude",
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--max-turns", MAX_TURNS,
        "--max-budget-usd", MAX_BUDGET_USD,
        "--permission-mode", permission_mode,
        "--tools", tool_scope,
    ]


def invoke_agent(
    role: str,
    task: dict,
    db_path: str,
) -> tuple[str, str]:
    """Invoke Claude Code CLI for *role* with *task*. Returns (session_id, status)."""
    prompt = f"[TASK od: {task['sender']}]\n{task['content']}"
    cmd = build_cmd(role, prompt)

    session_id = str(uuid.uuid4())[:12]
    turns = 0
    cost_usd = 0.0
    status = "running"

    print(f"\n-> Uruchamiam agenta... (Ctrl+C aby przerwać)\n", flush=True)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=str(PROJECT_ROOT),
        )

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                result = render_event(event)
                if result is not None:
                    session_id = result.get("session_id", session_id)
                    turns = result.get("num_turns", 0)
                    cost_usd = result.get("cost_usd", 0.0)
            except json.JSONDecodeError:
                print(line, flush=True)

        proc.wait(timeout=TIMEOUT_SEC)
        status = "done" if proc.returncode == 0 else "error"

    except subprocess.TimeoutExpired:
        proc.kill()
        status = "timeout"
        print("\n[RUNNER] Timeout — agent zatrzymany.", flush=True)
    except KeyboardInterrupt:
        proc.kill()
        status = "interrupted"
        print("\n[RUNNER] Przerwano przez użytkownika.", flush=True)

    print(
        f"\n-> Zakończono. session_id: {session_id}."
        f" Koszt: ${cost_usd:.2f}. Turns: {turns}/{MAX_TURNS}."
    )

    log_invocation(db_path, session_id, task["sender"], role, task["id"], turns, cost_usd, status)
    return session_id, status


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Mrowisko Runner — wywołuje agentów z inbox (Faza 1: approval gate)"
    )
    parser.add_argument("--role", required=True, help="Rola do sprawdzenia (np. erp_specialist)")
    parser.add_argument("--db", default=DB_DEFAULT, help="Ścieżka do mrowisko.db")
    args = parser.parse_args(argv)

    ensure_invocation_log(args.db)
    tasks = get_pending_tasks(args.db, args.role)

    if not tasks:
        print(f"[RUNNER] Rola: {args.role} | Brak oczekujących tasków.")
        return

    print(f"[RUNNER] Rola: {args.role} | Oczekujące taski: {len(tasks)}\n")

    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] Od: {task['sender']} | ID: {task['id']} | {task['created_at']}")
        print("-" * 60)
        print(task["content"])
        print("-" * 60)

        try:
            answer = input("\nInvoke? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n[RUNNER] Przerwano.")
            break

        if answer in ("", "y", "yes"):
            mark_message_read(args.db, task["id"])
            invoke_agent(role=args.role, task=task, db_path=args.db)
            print()
        else:
            print("[RUNNER] Pominięto.\n")


if __name__ == "__main__":
    main()
