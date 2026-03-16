"""Testy pre_tool_use.py hook."""

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path("tools/hooks/pre_tool_use.py")


def run_hook(payload: dict) -> tuple[int, dict | None]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    output = None
    if result.stdout.strip():
        output = json.loads(result.stdout.strip())
    return result.returncode, output


def make_bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


class TestSafeCommands:
    def test_python_allowed(self):
        rc, out = run_hook(make_bash("python tools/render.py backlog --format md"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_git_allowed(self):
        rc, out = run_hook(make_bash("git status"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_pytest_allowed(self):
        rc, out = run_hook(make_bash("pytest tests/ -q"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_mv_allowed(self):
        rc, out = run_hook(make_bash("mv tmp/a.md tmp/b.md"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_mkdir_allowed(self):
        rc, out = run_hook(make_bash("mkdir -p tmp/foo"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestNewlineNormalization:
    def test_newline_prefix_python(self):
        rc, out = run_hook(make_bash("\npython tools/render.py backlog --format md"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert out["hookSpecificOutput"]["updatedInput"]["command"] == "python tools/render.py backlog --format md"

    def test_newline_prefix_git(self):
        rc, out = run_hook(make_bash("\ngit log --oneline"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_multiple_newlines(self):
        rc, out = run_hook(make_bash("\n\n\npython -m pytest"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestDangerousCommands:
    def test_rm_rf_root_denied(self):
        rc, out = run_hook(make_bash("rm -rf /"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_rm_rf_star_denied(self):
        rc, out = run_hook(make_bash("rm -rf *"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_force_push_main_denied(self):
        rc, out = run_hook(make_bash("git push --force origin main"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_drop_table_denied(self):
        rc, out = run_hook(make_bash("sqlcmd -Q \"DROP TABLE users\""))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestNonBashTools:
    def test_read_tool_passes_through(self):
        rc, out = run_hook({"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.txt"}})
        assert rc == 0
        assert out is None

    def test_write_tool_passes_through(self):
        rc, out = run_hook({"tool_name": "Write", "tool_input": {"file_path": "/tmp/test.txt", "content": "x"}})
        assert rc == 0
        assert out is None


class TestDenyWithRepair:
    def test_cat_denied(self):
        rc, out = run_hook(make_bash("cat tools/render.py"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Read" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_head_denied(self):
        rc, out = run_hook(make_bash("head -n 50 file.txt"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Read" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_tail_denied(self):
        rc, out = run_hook(make_bash("tail -n 20 file.txt"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Read" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_grep_denied(self):
        rc, out = run_hook(make_bash("grep -r pattern ."))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Grep" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_rg_denied(self):
        rc, out = run_hook(make_bash("rg pattern src/"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Grep" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_find_denied(self):
        rc, out = run_hook(make_bash("find . -name '*.py'"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Glob" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_ls_denied(self):
        rc, out = run_hook(make_bash("ls -la tools/"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Glob" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_sed_denied(self):
        rc, out = run_hook(make_bash("sed -i 's/old/new/' file.py"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Edit" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_awk_denied(self):
        rc, out = run_hook(make_bash("awk '{print $1}' file.txt"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Edit" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_newline_prefix_cat_still_denied(self):
        rc, out = run_hook(make_bash("\ncat file.txt"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestUnknownCommands:
    def test_unknown_command_exits_zero(self):
        rc, out = run_hook(make_bash("someunknowntool --flag"))
        assert rc == 0
        assert out is None
