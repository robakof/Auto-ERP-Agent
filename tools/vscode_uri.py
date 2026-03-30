"""VS Code URI helper — calls Code.exe directly (bypasses code.cmd & parsing issue).

Usage:
    py tools/vscode_uri.py --uri "vscode://mrowisko.mrowisko-terminal-control?command=spawnAgent&role=dev&task=test"
    py tools/vscode_uri.py --command spawnAgent --role developer --task "check backlog"
    py tools/vscode_uri.py --command listAgents
    py tools/vscode_uri.py --command stopAgent --session-id UUID
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

EXTENSION_ID = "mrowisko.mrowisko-terminal-control"


def _find_code_exe() -> str | None:
    """Find Code.exe (not code.cmd) on Windows."""
    # Try common locations
    candidates = [
        Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code" / "Code.exe",
        Path("C:/Program Files/Microsoft VS Code/Code.exe"),
        Path("C:/Program Files (x86)/Microsoft VS Code/Code.exe"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)

    # Fallback: shutil.which finds code.cmd — derive Code.exe from it
    code_cmd = shutil.which("code")
    if code_cmd:
        code_dir = Path(code_cmd).resolve().parent.parent
        exe = code_dir / "Code.exe"
        if exe.exists():
            return str(exe)

    return None


def _build_uri(command: str, **params: str) -> str:
    """Build vscode:// URI with query parameters."""
    parts = [f"command={quote_plus(command)}"]
    for key, value in params.items():
        if value:
            parts.append(f"{key}={quote_plus(value)}")
    query = "&".join(parts)
    return f"vscode://{EXTENSION_ID}?{query}"


def main():
    parser = argparse.ArgumentParser(description="VS Code URI helper")
    parser.add_argument("--uri", help="Full URI to open")
    parser.add_argument("--command", help="Extension command (spawnAgent, listAgents, stopAgent, pokeAgent, focusAgent, rotateTab)")
    parser.add_argument("--role", help="Agent role")
    parser.add_argument("--task", help="Agent task")
    parser.add_argument("--session-id", help="Session ID (for stopAgent)")
    parser.add_argument("--permission-mode", help="Permission mode override")
    parser.add_argument("--terminal-name", help="Terminal name (for pokeAgent)")
    parser.add_argument("--message", help="Message text (for pokeAgent)")
    parser.add_argument("--claude-uuid", help="Claude session UUID (for resumeAgent)")

    args = parser.parse_args()

    if not args.uri and not args.command:
        parser.print_help()
        sys.exit(1)

    # Build URI
    if args.uri:
        uri = args.uri
    else:
        params = {}
        if args.role:
            params["role"] = args.role
        if args.task:
            params["task"] = args.task
        if args.session_id:
            params["sessionId"] = args.session_id
        if args.permission_mode:
            params["permissionMode"] = args.permission_mode
        if args.terminal_name:
            params["terminalName"] = args.terminal_name
        if args.message:
            params["message"] = args.message
        if args.claude_uuid:
            params["claudeUuid"] = args.claude_uuid
        uri = _build_uri(args.command, **params)

    # Find Code.exe
    code_exe = _find_code_exe()
    if not code_exe:
        print(json.dumps({"ok": False, "error": "Code.exe not found"}))
        sys.exit(1)

    # Call Code.exe directly (bypass code.cmd)
    result = subprocess.run(
        [code_exe, "--open-url", uri],
        capture_output=True,
        text=True,
        timeout=10,
    )

    print(json.dumps({
        "ok": result.returncode == 0,
        "uri": uri,
        "code_exe": code_exe,
        "returncode": result.returncode,
    }))


if __name__ == "__main__":
    main()
