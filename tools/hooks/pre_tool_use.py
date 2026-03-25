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


def split_chain(cmd: str) -> list[str]:
    """Split command by && into segments."""
    return [seg.strip() for seg in cmd.split("&&")]


def extract_paths(cmd: str) -> list[str]:
    """Extract paths from command, skipping flags."""
    try:
        tokens = shlex.split(cmd, posix=False)
    except ValueError:
        tokens = cmd.split()
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
    """Check powershell/cmd/start commands."""
    cmd_lower = cmd.lower().strip()
    if any(cmd_lower == allowed or cmd_lower.startswith(allowed + " ")
           for allowed in ALLOWED_EXECUTION_COMMANDS):
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


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

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
