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
import sys


SAFE_PREFIXES = [
    "python", "python3",
    "git",
    "pytest", "py.test",
    "pip", "pip3",
    "mkdir", "md",
    "ls", "dir",
    "mv", "move",
    "cp", "copy",
    "rm", "del", "rmdir",
    "sed", "awk",
    "wc", "find",
    "cat", "type",
    "echo",
    "cd",
    "start",
    "powershell", "cmd",
    "where", "which",
    "curl", "wget",
]

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
