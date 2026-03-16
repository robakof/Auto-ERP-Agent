"""
git_commit.py — Narzędzie agenta: git add + commit + push bez dialogów.

CLI:
    python tools/git_commit.py --message "feat: opis"
    python tools/git_commit.py --message "feat: opis" --all
    python tools/git_commit.py --message "feat: opis" --files a.py b.py
    python tools/git_commit.py --message "feat: opis" --all --push
    python tools/git_commit.py --message "feat: opis" --dry-run
    python tools/git_commit.py --push-only

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


def _parse_status_files(status_output: str) -> list[str]:
    """Parsuje output git status --short → lista plików."""
    files = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        # format: "XY path" lub "XY old -> new"
        path_part = line[3:].strip()
        if " -> " in path_part:
            path_part = path_part.split(" -> ")[1]
        files.append(path_part.strip())
    return files


def _get_committed_files(path: str) -> list[str]:
    """Zwraca listę plików z ostatniego commita."""
    result = _run(
        ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD"],
        cwd=path,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().splitlines() if f]


def git_commit(
    message: str = "",
    files: list[str] | None = None,
    add_all: bool = False,
    push: bool = False,
    push_only: bool = False,
    dry_run: bool = False,
    path: str = ".",
) -> dict:
    """Wykonuje git add (opcjonalnie), commit i push (opcjonalnie).

    Args:
        message: Wiadomość commitu. Wymagane jeśli push_only=False i dry_run=False.
        files: Lista plików do ostage'owania przez git add.
        add_all: Jeśli True, uruchamia git add -A przed commitem.
        push: Jeśli True, uruchamia git push po commicie.
        push_only: Jeśli True, pomija commit i wykonuje tylko git push.
        dry_run: Jeśli True, pokazuje co zostałoby ostage'owane bez commitowania.
        path: Ścieżka do repozytorium. Domyślnie ".".

    Returns:
        Dict z kluczami: ok, data, error, meta.
    """
    if not push_only and not dry_run and not message:
        raise ValueError("message nie może być pusty")

    start = time.monotonic()

    def error_result(msg: str) -> dict:
        return {
            "ok": False,
            "data": None,
            "error": {"type": "GIT_ERROR", "message": msg},
            "meta": {"duration_ms": round((time.monotonic() - start) * 1000), "truncated": False},
        }

    # tryb push-only
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

    # tryb dry-run — pokaż co zostałoby ostage'owane
    if dry_run:
        if add_all:
            result = _run(["git", "status", "--short"], cwd=path)
            if result.returncode != 0:
                return error_result(result.stderr.strip() or result.stdout.strip())
            would_stage = _parse_status_files(result.stdout)
        else:
            would_stage = list(files) if files else []
        duration_ms = round((time.monotonic() - start) * 1000)
        return {
            "ok": True,
            "data": {"dry_run": True, "files_would_stage": would_stage},
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
    files_staged = _get_committed_files(path)

    data: dict = {"output": commit_output, "files_staged": files_staged}
    if add_all:
        data["warning"] = "Użyto --all. Sprawdź czy wszystkie pliki należą do tego zadania."

    # git push
    if push:
        result = _run(["git", "push"], cwd=path)
        if result.returncode != 0:
            return error_result(result.stderr.strip() or result.stdout.strip())

    duration_ms = round((time.monotonic() - start) * 1000)
    return {
        "ok": True,
        "data": data,
        "error": None,
        "meta": {"duration_ms": duration_ms, "truncated": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="git add + commit + push bez dialogów.")
    parser.add_argument("--message", default="", help="Wiadomość commitu (wymagane bez --push-only/--dry-run)")
    parser.add_argument("--files", nargs="+", default=None, help="Pliki do ostage'owania")
    parser.add_argument("--all", dest="add_all", action="store_true", help="git add -A przed commitem")
    parser.add_argument("--push", action="store_true", help="git push po commicie")
    parser.add_argument("--push-only", dest="push_only", action="store_true", help="tylko git push (bez commitu)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="pokaż co zostanie ostage'owane bez commitowania")
    parser.add_argument("--path", default=".", help="Ścieżka do repozytorium (domyślnie .)")
    args = parser.parse_args()

    result = git_commit(
        message=args.message,
        files=args.files,
        add_all=args.add_all,
        push=args.push,
        push_only=args.push_only,
        dry_run=args.dry_run,
        path=args.path,
    )
    print_json(result)


if __name__ == "__main__":
    main()
