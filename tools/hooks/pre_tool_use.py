"""PreToolUse hook — normalizacja i whitelist dla komend Bash.

Rozwiązuje dwa problemy:
1. Komendy z wiodącym newline (\n) nie matchują wzorców w settings.local.json (id=24)
2. Statyczna lista wzorców JSON wymaga manualnej konserwacji (id=58)

Logika:
- Normalizuje komendę (strip leading whitespace/newlines)
- Sprawdza DANGEROUS_PATTERNS → deny z komunikatem
- Sprawdza SAFE_PREFIXES → allow (bez dialogu uprawnień)
- Nieznana komenda → exit 0 (domyślne zachowanie Claude Code, pokaż dialog)
"""

import json
import re
import shlex
import sys
from typing import Optional

# Ścieżki dozwolone dla destrukcyjnych komend (rm/del/rmdir/mv)
ALLOWED_DESTRUCTIVE_PATHS = (
    "tmp/", "tmp\\",
    "documents/human/tmp/", "documents\\human\\tmp\\",
)

# Whitelista bezpiecznych komend execution
ALLOWED_EXECUTION_COMMANDS = ("start .", "start ..")

# Komendy wymagające walidacji ścieżek
DESTRUCTIVE_COMMANDS = frozenset(["rm", "del", "rmdir", "rd"])
MOVE_COMMANDS = frozenset(["mv", "move"])
EXECUTION_COMMANDS = frozenset(["powershell", "cmd", "start"])
NETWORK_COMMANDS = frozenset(["curl", "wget"])

# Repair messages
REPAIR_MSG_WILDCARD = "Wildcard w komendzie destrukcyjnej zablokowany. Użyj explicit path."
REPAIR_MSG_PROTECTED = "Ścieżka chroniona. Dozwolone tylko: tmp/, documents/human/tmp/"
REPAIR_MSG_EXECUTION = "Komenda execution zablokowana. Dozwolone: start ."
REPAIR_MSG_PIPE = "Pipe z curl/wget zablokowany (execution risk). Użyj -o file."
REPAIR_MSG_MV = "mv/move: target lub source musi być w tmp/ lub documents/human/tmp/"
REPAIR_MSG_MEMORY = "Użyj agent_bus_cli.py suggest zamiast .claude/memory/. Reguła: CLAUDE.md sekcja Refleksja."

SAFE_PREFIXES = [
    "py", "python", "python3",
    "git",
    "pytest", "py.test",
    "pip", "pip3",
    "mkdir", "md",
    "mv", "move",
    "cp", "copy",
    "rm", "del", "rmdir",
    "wc",
    "echo",
    "cd",
    "start",
    "powershell", "cmd",
    "where", "which",
    "curl", "wget",
]

# Komendy zakazane w Bash — agent ma użyć dedykowanego narzędzia.
# Hook zwraca deny z komunikatem naprawczym zamiast pytać użytkownika.
DENY_WITH_REPAIR: dict[str, str] = {
    "cat":  "Użyj narzędzia Read zamiast cat.",
    "type": "Użyj narzędzia Read zamiast type.",
    "head": "Użyj narzędzia Read (parametr limit) zamiast head.",
    "tail": "Użyj narzędzia Read (parametry offset+limit) zamiast tail.",
    "grep": "Użyj narzędzia Grep zamiast grep.",
    "rg":   "Użyj narzędzia Grep zamiast rg.",
    "find": "Użyj narzędzia Glob zamiast find.",
    "ls":   "Użyj narzędzia Glob zamiast ls.",
    "dir":  "Użyj narzędzia Glob zamiast dir.",
    "sed":  "Użyj narzędzia Edit zamiast sed.",
    "awk":  "Użyj narzędzia Edit zamiast awk.",
}

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s*/",
    r"rm\s+-rf\s*~",
    r"rm\s+-rf\s*\*",
    r"rd\s+/s\s+/q\s+[a-zA-Z]:\\$",
    r"git\s+push\s+.*--force[^-].*\b(main|master)\b",
    r"git\s+reset\s+--hard\s+HEAD",
    r"DROP\s+TABLE",
    r"TRUNCATE\s+TABLE",
    r"DELETE\s+FROM\s+\w+\s*;?\s*$",
]


def _is_memory_path(path: str) -> bool:
    """Check if path targets Claude memory directory (.claude/memory/ or .claude/projects/*/memory/)."""
    n = path.replace("\\", "/").lower()
    return ".claude/memory/" in n or (".claude/projects/" in n and "/memory/" in n)


def split_chain(cmd: str) -> list[str]:
    """Split command by &&, || and ; into segments."""
    import re
    # Split on &&, ||, or ; (command separators)
    segments = re.split(r'\s*(?:&&|\|\||;)\s*', cmd)
    return [seg.strip() for seg in segments if seg.strip()]


def extract_paths(cmd: str) -> list[str]:
    """Extract paths from command, skipping flags. Handles -- (end-of-flags)."""
    try:
        tokens = shlex.split(cmd, posix=False)
    except ValueError:
        tokens = cmd.split()

    # Find -- marker (everything after is a path, not a flag)
    try:
        dash_dash_idx = tokens.index("--")
        before_dash = tokens[1:dash_dash_idx]
        after_dash = tokens[dash_dash_idx + 1:]
        # Before --: skip flags. After --: everything is a path.
        paths_before = [t for t in before_dash if not t.startswith("-")]
        return paths_before + after_dash
    except ValueError:
        pass  # No -- found
    # Skip command and flags (start with -)
    return [t for t in tokens[1:] if not t.startswith("-")]


def has_wildcard(paths: list[str]) -> bool:
    """Check if any path contains wildcard."""
    return any("*" in p or "?" in p for p in paths)


def path_in_allowed(path: str) -> bool:
    """Check if path starts with allowed prefix."""
    p = path.replace("\\", "/").lower()
    return any(p.startswith(allowed.replace("\\", "/").lower())
               for allowed in ALLOWED_DESTRUCTIVE_PATHS)


def all_paths_allowed(paths: list[str]) -> bool:
    """Check if ALL paths are in allowed locations."""
    return all(path_in_allowed(p) for p in paths) if paths else False


def check_destructive(cmd: str) -> tuple[bool, str]:
    """Check rm/del/rmdir commands. Returns (deny, reason)."""
    paths = extract_paths(cmd)
    if has_wildcard(paths):
        return True, REPAIR_MSG_WILDCARD
    if not all_paths_allowed(paths):
        return True, REPAIR_MSG_PROTECTED
    return False, ""


def check_mv(cmd: str) -> tuple[bool, str]:
    """Check mv/move commands. Target OR source must be in allowed paths."""
    paths = extract_paths(cmd)
    if len(paths) < 2:
        return True, REPAIR_MSG_MV
    source_paths, target = paths[:-1], paths[-1]
    # Allow if target in allowed OR all sources in allowed
    if path_in_allowed(target) or all(path_in_allowed(s) for s in source_paths):
        return False, ""
    return True, REPAIR_MSG_MV


def check_execution(cmd: str) -> tuple[bool, str]:
    """Check powershell/cmd/start commands. Exact match only."""
    cmd_lower = cmd.lower().strip()
    if cmd_lower in ALLOWED_EXECUTION_COMMANDS:
        return False, ""
    return True, REPAIR_MSG_EXECUTION


def check_network_pipe(cmd: str) -> tuple[bool, str]:
    """Check curl/wget for pipe."""
    if "|" in cmd:
        return True, REPAIR_MSG_PIPE
    return False, ""


def deny_response(reason: str) -> None:
    """Print deny response and exit."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def validate_segment(segment: str) -> Optional[str]:
    """Validate single command segment. Returns deny reason or None."""
    seg_lower = segment.lower()
    tokens = seg_lower.split()
    if not tokens:
        return None
    first_token = tokens[0]

    if first_token in DESTRUCTIVE_COMMANDS:
        deny, reason = check_destructive(segment)
        if deny:
            return reason
    elif first_token in MOVE_COMMANDS:
        deny, reason = check_mv(segment)
        if deny:
            return reason
    elif first_token in EXECUTION_COMMANDS:
        deny, reason = check_execution(segment)
        if deny:
            return reason
    elif first_token in NETWORK_COMMANDS:
        deny, reason = check_network_pipe(segment)
        if deny:
            return reason
    return None




# --- Workflow awareness (Faza 3 — nudge mode) ---

# Tools exempt from workflow enforcement — never checked
EXEMPT_TOOLS = frozenset([
    "Read", "Glob", "Grep",           # read-only
    "Agent", "AskUserQuestion",        # delegation / user interaction
])

# Bash commands exempt from workflow enforcement
EXEMPT_BASH_PREFIXES = (
    "py tools/agent_bus_cli.py",       # communication + workflow-start
    "py tools/context_usage.py",       # monitoring
    "py tools/session_init.py",        # session setup
    "py tools/render.py",             # view rendering
    "py tools/conversation_search.py", # history search
    "git status", "git log", "git diff", "git branch",  # git read-only
    "which ", "where ",                # discovery
)

# Workflow nudge config
WF_NUDGE_EVERY = 5     # warn every Nth non-exempt tool call
WF_HARD_BLOCK_AFTER = 10  # hard block after N warnings (= N * WF_NUDGE_EVERY calls)

def _check_workflow_awareness(tool_name: str, tool_input: dict, claude_uuid: str) -> bool:
    """Nudge mode: periodic deny when agent works outside workflow.

    Every WF_NUDGE_EVERY non-exempt tool calls → deny with counter.
    After WF_HARD_BLOCK_AFTER warnings → hard block (dispatcher must unblock).
    Agent should retry after seeing nudge — next call goes through.
    Returns True if deny was issued (main must stop).
    """
    # Exempt tools — never checked
    if tool_name in EXEMPT_TOOLS:
        return False
    if tool_name == "Bash":
        cmd = tool_input.get("command", "").strip()
        if any(cmd.startswith(p) for p in EXEMPT_BASH_PREFIXES):
            return False
    from pathlib import Path
    try:
        import sqlite3
        db_path = Path(__file__).parent.parent.parent / "mrowisko.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA busy_timeout=1000")

        session_id, role = None, None

        # Strategy 1: claude_uuid → live_agents (spawned agents)
        if claude_uuid:
            agent = conn.execute(
                "SELECT session_id, role FROM live_agents "
                "WHERE claude_uuid=? AND status IN ('starting','active','warned')",
                (claude_uuid,),
            ).fetchone()
            if agent:
                session_id, role = agent

        # Strategy 2: claude_uuid → sessions table (all agents via session_init)
        if not session_id and claude_uuid:
            sess = conn.execute(
                "SELECT id, role FROM sessions WHERE claude_session_id=?",
                (claude_uuid,),
            ).fetchone()
            if sess:
                session_id = sess[0]
                role = sess[1]

        if not session_id:
            conn.close()
            return False

        # Check for running workflow
        row = conn.execute(
            "SELECT id, workflow_id FROM workflow_execution "
            "WHERE session_id=? AND status='running' ORDER BY started_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if row:
            conn.close()
            return False  # has workflow — all good

        # No workflow — track + nudge
        conn.execute(
            "INSERT OR IGNORE INTO workflow_execution (id, workflow_id, role, session_id, status) "
            "VALUES (0, 'untracked', 'system', '', 'running')"
        )
        conn.execute(
            "INSERT INTO step_log (execution_id, step_id, status, output_summary) "
            "VALUES (0, ?, 'SKIPPED', ?)",
            (f"untracked:tool:{tool_name}", f"session={session_id} role={role}"),
        )
        conn.commit()

        # Count untracked calls for THIS session
        count = conn.execute(
            "SELECT COUNT(*) FROM step_log WHERE execution_id=0 "
            "AND output_summary LIKE ?",
            (f"session={session_id}%",),
        ).fetchone()[0]
        conn.close()

        warning_number = count // WF_NUDGE_EVERY
        is_nudge = count % WF_NUDGE_EVERY == 0 and count > 0

        if warning_number >= WF_HARD_BLOCK_AFTER:
            deny_response(
                f"[workflow-BLOCK #{warning_number}] Agent {role or '?'} zablokowany — "
                f"{count} tool calls bez workflow. "
                f"Wymagana inspekcja dispatchera. "
                f"Dispatcher: py tools/agent_bus_cli.py workflow-resume lub workflow-start."
            )
            return True

        if is_nudge:
            deny_response(
                f"[workflow-warning #{warning_number}/{WF_HARD_BLOCK_AFTER}] "
                f"Pracujesz bez workflow ({count} calls). "
                f"Wejdź w workflow: py tools/agent_bus_cli.py workflow-start --workflow-id <ID> --role {role or '<rola>'}. "
                f"PONÓW komendę — to tylko przypomnienie."
            )
            return True

        return False  # not a nudge call — allow silently

    except Exception as e:
        from pathlib import Path as _P
        try:
            _P(__file__).parent.parent.parent.joinpath("tmp", "workflow_hook_debug.log").write_text(
                f"{type(e).__name__}: {e}\n", encoding="utf-8",
            )
        except Exception:
            pass
        return False


_last_heartbeat: float = 0.0
HEARTBEAT_INTERVAL = 60  # seconds — throttle DB writes


def _heartbeat(claude_uuid: str = "") -> None:
    """Update last_activity + revive agent if GC stopped it. Throttled to once per 60s."""
    global _last_heartbeat
    import time
    now = time.monotonic()
    if now - _last_heartbeat < HEARTBEAT_INTERVAL:
        return
    _last_heartbeat = now

    from pathlib import Path
    import os
    spawn_token = os.environ.get("MROWISKO_SPAWN_TOKEN", "")
    if not spawn_token and not claude_uuid:
        return
    try:
        import sqlite3
        db_path = Path(__file__).parent.parent.parent / "mrowisko.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA busy_timeout=1000")
        if spawn_token:
            conn.execute(
                "UPDATE live_agents SET last_activity = datetime('now', 'localtime'), status = 'active' "
                "WHERE spawn_token = ? AND status IN ('starting', 'active', 'warned', 'stopped')",
                (spawn_token,),
            )
        elif claude_uuid:
            conn.execute(
                "UPDATE live_agents SET last_activity = datetime('now', 'localtime'), status = 'active' "
                "WHERE claude_uuid = ? AND status IN ('starting', 'active', 'warned', 'stopped')",
                (claude_uuid,),
            )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _check_poke() -> Optional[str]:
    """Check for unread poke messages for current agent. Returns deny reason or None.

    Reads role from tmp/session_data.json, queries inbox for type='poke'.
    Marks poke as read after retrieval. ~1-3ms overhead per call.
    Known limitation: multi-agent session_data.json conflict (MVP accepts this).
    """
    from pathlib import Path
    session_data_file = Path(__file__).parent.parent.parent / "tmp" / "session_data.json"
    if not session_data_file.exists():
        return None
    try:
        import sqlite3
        sd = json.loads(session_data_file.read_text(encoding="utf-8"))
        role = sd.get("role")
        if not role:
            return None
        db_path = Path(__file__).parent.parent.parent / "mrowisko.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA busy_timeout=1000")
        row = conn.execute(
            "SELECT id, sender, content FROM messages WHERE recipient=? AND type='poke' AND status='unread' LIMIT 1",
            (role,),
        ).fetchone()
        if not row:
            conn.close()
            return None
        msg_id, sender, content = row
        conn.execute("UPDATE messages SET status='read', read_at=datetime('now', 'localtime') WHERE id=?", (msg_id,))
        conn.commit()
        conn.close()
        return f"[POKE od {sender}] {content}"
    except Exception:
        return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    # Heartbeat — fires for ALL tool types, throttled to 60s
    _heartbeat(data.get("session_id", ""))

    # Workflow awareness — soft mode warning (claude_uuid → live_agents/sessions lookup)
    denied = _check_workflow_awareness(
        data.get("tool_name", ""),
        data.get("tool_input", {}),
        data.get("session_id", ""),
    )
    if denied:
        return

    # Poke check — fires for ALL tool types (before Bash-only gate)
    poke_reason = _check_poke()
    if poke_reason:
        deny_response(poke_reason)
        return

    # Memory redirect — block Write/Edit to .claude/memory/
    if data.get("tool_name") in ("Write", "Edit"):
        file_path = data.get("tool_input", {}).get("file_path", "")
        if _is_memory_path(file_path):
            deny_response(REPAIR_MSG_MEMORY)
            return

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command: str = data.get("tool_input", {}).get("command", "")
    normalized = command.lstrip("\n\r\t ")

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Hook bezpieczenstwa zablokował komendę: {normalized[:120]}"
                    ),
                }
            }))
            return

    cmd_lower = normalized.lower()

    first_token = cmd_lower.split()[0] if cmd_lower.split() else ""
    if first_token in DENY_WITH_REPAIR:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": DENY_WITH_REPAIR[first_token],
            }
        }))
        return

    # Validate all segments in chain (split by &&)
    for segment in split_chain(normalized):
        deny_reason = validate_segment(segment)
        if deny_reason:
            deny_response(deny_reason)
            return

    for prefix in SAFE_PREFIXES:
        if cmd_lower == prefix or cmd_lower.startswith(prefix + " ") or cmd_lower.startswith(prefix + "\t"):
            output: dict = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            }
            if normalized != command:
                output["hookSpecificOutput"]["updatedInput"] = {"command": normalized}
            print(json.dumps(output))
            return

    sys.exit(0)


if __name__ == "__main__":
    main()
