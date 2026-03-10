"""
git_commit.py — Narzędzie agenta: git add + commit + push bez dialogów.

CLI:
    python tools/git_commit.py --message "feat: opis"
    python tools/git_commit.py --message "feat: opis" --all
    python tools/git_commit.py --message "feat: opis" --files a.py b.py
    python tools/git_commit.py --message "feat: opis" --all --push
    python tools/git_commit.py --message "feat: opis" --push --path /ścieżka/repo

Output: JSON na stdout.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.lib.output import print_json


def _run(cmd: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def git_commit(
    message: str = "",
    files: list[str] | None = None,
    add_all: bool = False,
    push: bool = False,
    push_only: bool = False,
    path: str = ".",
) -> dict:
    """Wykonuje git add (opcjonalnie), commit i push (opcjonalnie).

    Args:
        message: Wiadomość commitu. Wymagane jeśli push_only=False.
        files: Lista plików do ostage'owania przez git add.
        add_all: Jeśli True, uruchamia git add -A przed commitem.
        push: Jeśli True, uruchamia git push po commicie.
        push_only: Jeśli True, pomija commit i wykonuje tylko git push.
        path: Ścieżka do repozytorium. Domyślnie ".".

    Returns:
        Dict z kluczami: ok, data, error, meta.
    """
    if not push_only and not message:
        raise ValueError("message nie może być pusty")

    start = time.monotonic()

    def error_result(msg: str) -> dict:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "GIT_ERROR", "message": msg},
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000), "truncated": False},
        }

    # tryb push-only — pomiń add i commit
    if push_only:
        result = _run(["git", "push"], cwd=path)
        duration_ms = round((time.monotonic() - start) * 1000)
        if result.returncode != 0:
            return error_result(result.stderr.strip() or result.stdout.strip())
        return {
            "ok": True,
            "data": {"output": result.stdout.strip()},
            "error": None,
            "meta": {"duration_ms": duration_ms, "truncated": False},
        }

    # git add
    if add_all:
        result = _run(["git", "add", "-A"], cwd=path)
        if result.returncode != 0:
            return error_result(result.stderr.strip() or result.stdout.strip())
    elif files:
        result = _run(["git", "add"] + files, cwd=path)
        if result.returncode != 0:
            return error_result(result.stderr.strip() or result.stdout.strip())

    # git commit
    result = _run(["git", "commit", "-m", message], cwd=path)
    if result.returncode != 0:
        return error_result(result.stderr.strip() or result.stdout.strip())

    commit_output = result.stdout.strip()

    # git push
    if push:
        result = _run(["git", "push"], cwd=path)
        if result.returncode != 0:
            return error_result(result.stderr.strip() or result.stdout.strip())

    duration_ms = round((time.monotonic() - start) * 1000)
    return {
        "ok": True,
        "data": {"output": commit_output},
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="git add + commit + push bez dialogów.")
    parser.add_argument("--message", default="", help="Wiadomość commitu (wymagane bez --push-only)")
    parser.add_argument("--files", nargs="+", default=None, help="Pliki do ostage'owania")
    parser.add_argument("--all", dest="add_all", action="store_true", help="git add -A przed commitem")
    parser.add_argument("--push", action="store_true", help="git push po commicie")
    parser.add_argument("--push-only", dest="push_only", action="store_true", help="tylko git push (bez commitu)")
    parser.add_argument("--path", default=".", help="Ścieżka do repozytorium (domyślnie .)")
    args = parser.parse_args()

    result = git_commit(
        message=args.message,
        files=args.files,
        add_all=args.add_all,
        push=args.push,
        push_only=args.push_only,
        path=args.path,
    )
    print_json(result)


if __name__ == "__main__":
    main()
