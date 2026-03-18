"""Mrowisko Runner — Faza 1b: instance routing + approval gate.

Każda instancja runnera rejestruje się w DB z unikalnym instance_id.
Heartbeat co 10s — instancja bez heartbeatu przez 60s uznana za nieaktywną.
Atomic claim taska — race condition między wieloma instancjami tej samej roli niemożliwy.
Wiadomości adresowane do roli (np. "analyst") lub do konkretnej instancji ("analyst:a1b2c3").

Użycie:
    python tools/mrowisko_runner.py --role erp_specialist
    python tools/mrowisko_runner.py --role analyst --db mrowisko.db
"""

import argparse
import atexit
import json
import signal
import sqlite3
import subprocess
import sys
import threading
import uuid
from pathlib import Path

CLAUDE_CMD = "claude.cmd" if sys.platform == "win32" else "claude"

PROJECT_ROOT = Path(__file__).parent.parent
DB_DEFAULT = str(PROJECT_ROOT / "mrowisko.db")

PERMISSION_MODE: dict[str, str] = {
    "erp_specialist": "acceptEdits",
    "analyst": "acceptEdits",
    "developer": "default",
}

TOOL_SCOPE: dict[str, str] = {
    "erp_specialist": "Read,Grep,Glob,Bash",
    "analyst": "Read,Grep,Glob",
    "developer": "Read,Grep,Glob,Bash,Write,Edit",
}

MAX_TURNS = "8"
MAX_BUDGET_USD = "1.50"
TIMEOUT_SEC = 600
HEARTBEAT_INTERVAL = 10


# ---------------------------------------------------------------------------
# DB helpers (own connection per function — multi-process safe)
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=3000")
    return conn


def ensure_invocation_log(db_path: str) -> None:
    conn = _connect(db_path)
    conn.execute("""
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
    """)
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
    conn = _connect(db_path)
    conn.execute(
        """INSERT INTO invocation_log
               (session_id, from_role, to_role, task_id, turns, cost_usd, status)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (session_id, from_role, to_role, task_id, turns, cost_usd, status),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Instance registry (via AgentBus)
# ---------------------------------------------------------------------------

def build_instance_id(role: str) -> str:
    return f"{role}:{uuid.uuid4().hex[:6]}"


class HeartbeatThread(threading.Thread):
    """Daemon thread that updates last_seen_at every HEARTBEAT_INTERVAL seconds."""

    def __init__(self, instance_id: str, db_path: str):
        super().__init__(daemon=True)
        self._instance_id = instance_id
        self._db_path = db_path
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.wait(HEARTBEAT_INTERVAL):
            try:
                conn = _connect(self._db_path)
                conn.execute(
                    "UPDATE agent_instances SET last_seen_at = datetime('now') WHERE instance_id = ?",
                    (self._instance_id,),
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

    def stop(self) -> None:
        self._stop_event.set()


# ---------------------------------------------------------------------------
# Stream-json renderer
# ---------------------------------------------------------------------------

def render_event(event: dict) -> dict | None:
    etype = event.get("type", "")
    if etype == "assistant":
        for block in event.get("message", {}).get("content", []):
            btype = block.get("type", "")
            if btype == "text":
                print(block["text"], end="", flush=True)
            elif btype == "tool_use":
                name = block.get("name", "")
                inp_preview = str(block.get("input", {}))[:120].replace("\n", " ")
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
    return [
        CLAUDE_CMD, "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--no-session-persistence",
        "--max-turns", MAX_TURNS,
        "--max-budget-usd", MAX_BUDGET_USD,
        "--permission-mode", PERMISSION_MODE.get(role, "default"),
        "--tools", TOOL_SCOPE.get(role, "Read,Grep,Glob"),
    ]


def build_prompt(task: dict, instance_id: str, role: str) -> str:
    return (
        f"{role}\n"
        f"[TASK od: {task['sender']}]\n"
        f"[ADRES ZWROTNY: {instance_id}]\n"
        f"{task['content']}"
    )


def invoke_agent(role: str, task: dict, instance_id: str, db_path: str) -> tuple[str, str]:
    prompt = build_prompt(task, instance_id, role)
    cmd = build_cmd(role, prompt)

    session_id = uuid.uuid4().hex[:12]
    turns, cost_usd = 0, 0.0
    status = "running"

    print(f"\n-> Uruchamiam agenta... (Ctrl+C aby przerwać)\n", flush=True)

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", cwd=str(PROJECT_ROOT),
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
        print("\n[RUNNER] Przerwano.", flush=True)

    print(f"\n-> Zakończono. session_id: {session_id}. Koszt: ${cost_usd:.2f}. Turns: {turns}/{MAX_TURNS}.")
    log_invocation(db_path, session_id, task["sender"], role, task["id"], turns, cost_usd, status)
    return session_id, status


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Mrowisko Runner — wywołuje agentów z inbox (Faza 1b: instance routing)"
    )
    parser.add_argument("--role", required=True)
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args(argv)

    ensure_invocation_log(args.db)

    # Import AgentBus only after ensure (creates tables)
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from tools.lib.agent_bus import AgentBus

    bus = AgentBus(db_path=args.db)
    instance_id = build_instance_id(args.role)
    bus.register_instance(instance_id, args.role)

    print(f"[RUNNER] Instancja: {instance_id}")

    # Heartbeat
    hb = HeartbeatThread(instance_id, args.db)
    hb.start()

    # Cleanup on exit
    def _cleanup():
        hb.stop()
        try:
            bus.terminate_instance(instance_id)
        except Exception:
            pass

    atexit.register(_cleanup)
    signal.signal(signal.SIGINT, lambda s, f: (_cleanup(), exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (_cleanup(), exit(0)))

    tasks = bus.get_pending_tasks(args.role, instance_id)

    if not tasks:
        print(f"[RUNNER] Rola: {args.role} | Brak oczekujących tasków.")
        _cleanup()
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
            claimed = bus.claim_task(task["id"], instance_id)
            if not claimed:
                print(f"[RUNNER] Task #{task['id']} już claimed przez inną instancję — pomijam.\n")
                continue
            bus.set_instance_busy(instance_id, task["id"])
            try:
                invoke_agent(role=args.role, task=task, instance_id=instance_id, db_path=args.db)
            except Exception as exc:
                print(f"[RUNNER] Błąd invocation: {exc} — cofam claim taska #{task['id']}.\n")
                bus.unclaim_task(task["id"])
            bus.set_instance_idle(instance_id)
            print()
        else:
            print("[RUNNER] Pominięto.\n")

    _cleanup()


if __name__ == "__main__":
    main()
