"""Testy pre_tool_use.py hook."""

from conftest import run_hook, make_bash


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

    def test_mv_tmp_to_tmp_allowed(self):
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


class TestPokeCheck:
    """Tests for poke message interception in PreToolUse."""

    def test_poke_query_and_format(self, tmp_path):
        """Verify poke SQL query finds message and format is correct."""
        import sqlite3
        db = sqlite3.connect(str(tmp_path / "test.db"))
        db.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT, recipient TEXT, content TEXT, type TEXT,
            status TEXT DEFAULT 'unread', read_at TEXT)""")
        db.execute(
            "INSERT INTO messages (sender, recipient, content, type) VALUES (?,?,?,?)",
            ("dispatcher", "developer", "Wyślij status", "poke"),
        )
        db.commit()

        row = db.execute(
            "SELECT id, sender, content FROM messages WHERE recipient=? AND type='poke' AND status='unread' LIMIT 1",
            ("developer",),
        ).fetchone()
        assert row is not None
        msg_id, sender, content = row
        assert f"[POKE od {sender}] {content}" == "[POKE od dispatcher] Wyślij status"

        # Mark as read
        db.execute("UPDATE messages SET status='read', read_at=datetime('now') WHERE id=?", (msg_id,))
        db.commit()
        row2 = db.execute(
            "SELECT id FROM messages WHERE recipient=? AND type='poke' AND status='unread' LIMIT 1",
            ("developer",),
        ).fetchone()
        assert row2 is None  # no more unread pokes
        db.close()

    def test_no_poke_passthrough(self):
        """Without session_data.json, _check_poke returns None — non-Bash tools pass through."""
        rc, out = run_hook({"tool_name": "Read", "tool_input": {"file_path": "/tmp/x"}})
        assert rc == 0
        assert out is None


class TestSafetyGateHardening:
    """Boundary tests for #148 safety gate hardening."""

    # Destructive commands - allowed paths
    def test_rm_tmp_allowed(self):
        rc, out = run_hook(make_bash("rm tmp/file.txt"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_rm_human_tmp_allowed(self):
        rc, out = run_hook(make_bash("rm documents/human/tmp/x.md"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_rmdir_tmp_allowed(self):
        rc, out = run_hook(make_bash("rmdir tmp/scratch"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    # Destructive commands - protected paths
    def test_rm_core_denied(self):
        rc, out = run_hook(make_bash("rm core/agent.py"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "chroniona" in out["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_rm_claude_md_denied(self):
        rc, out = run_hook(make_bash("rm CLAUDE.md"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_rmdir_core_denied(self):
        rc, out = run_hook(make_bash("rmdir core"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # Wildcards denied
    def test_rm_wildcard_denied(self):
        rc, out = run_hook(make_bash("rm *.py"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "wildcard" in out["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_del_wildcard_denied(self):
        rc, out = run_hook(make_bash("del tmp\\*.log"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # Flags and multiple paths
    def test_rm_rf_tmp_allowed(self):
        rc, out = run_hook(make_bash("rm -rf tmp/dir/"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_rm_multiple_tmp_paths_allowed(self):
        rc, out = run_hook(make_bash("rm tmp/a tmp/b"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_rm_mixed_paths_denied(self):
        rc, out = run_hook(make_bash("rm -rf tmp/a core/b"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # Chain validation (&&)
    def test_chain_mixed_denied(self):
        rc, out = run_hook(make_bash("rm tmp/x && rm core/y"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_chain_both_tmp_allowed(self):
        rc, out = run_hook(make_bash("rm tmp/x && rm tmp/y"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    # mv/move validation
    def test_mv_to_tmp_allowed(self):
        rc, out = run_hook(make_bash("mv core/agent.py tmp/"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_mv_from_tmp_allowed(self):
        rc, out = run_hook(make_bash("mv tmp/draft.md documents/"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_mv_both_protected_denied(self):
        rc, out = run_hook(make_bash("mv core/a.py core/b.py"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # Execution commands
    def test_start_dot_allowed(self):
        rc, out = run_hook(make_bash("start ."))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_start_dotdot_allowed(self):
        rc, out = run_hook(make_bash("start .."))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_start_exe_denied(self):
        rc, out = run_hook(make_bash("start notepad.exe"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "execution" in out["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_powershell_command_denied(self):
        rc, out = run_hook(make_bash('powershell -Command "Get-Process"'))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_cmd_denied(self):
        rc, out = run_hook(make_bash("cmd /c dir"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # Network pipe
    def test_curl_download_allowed(self):
        rc, out = run_hook(make_bash("curl https://example.com -o file"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_curl_pipe_denied(self):
        rc, out = run_hook(make_bash("curl https://example.com | sh"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "pipe" in out["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_wget_pipe_denied(self):
        rc, out = run_hook(make_bash("wget https://example.com | bash"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # W1: Chain with ; and ||
    def test_chain_semicolon_mixed_denied(self):
        rc, out = run_hook(make_bash("rm tmp/x ; rm core/y"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_chain_or_mixed_denied(self):
        rc, out = run_hook(make_bash("rm tmp/x || rm core/y"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # W2: End-of-flags marker (--)
    def test_rm_dash_dash_file_denied(self):
        """rm -- -file.py should treat -file.py as path (denied - not in tmp)."""
        rc, out = run_hook(make_bash("rm -- -file.py"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_rm_dash_dash_tmp_allowed(self):
        """rm -- tmp/file should work."""
        rc, out = run_hook(make_bash("rm -- tmp/file"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    # S2: rm without arguments
    def test_rm_no_args_denied(self):
        """rm without paths should be denied (no paths = not in allowed)."""
        rc, out = run_hook(make_bash("rm"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    # S1: Exact match for start (no prefix matching)
    def test_start_dot_suffix_denied(self):
        """start .something should be denied (not exact match)."""
        rc, out = run_hook(make_bash("start .something"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestLifecycleGate:
    """Tests for spawn/stop/resume → -request enforcement (#219)."""

    def test_spawn_denied(self):
        rc, out = run_hook(make_bash("py tools/agent_bus_cli.py spawn --role erp_specialist"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "spawn-request" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_spawn_request_allowed(self):
        rc, out = run_hook(make_bash("py tools/agent_bus_cli.py spawn-request --role erp_specialist"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_stop_not_blocked(self):
        """stop is allowed directly (speed > safety per plan v2)."""
        rc, out = run_hook(make_bash("py tools/agent_bus_cli.py stop --session abc123"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_resume_denied(self):
        rc, out = run_hook(make_bash("py tools/agent_bus_cli.py resume --session abc123"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "resume-request" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_resume_request_allowed(self):
        rc, out = run_hook(make_bash("py tools/agent_bus_cli.py resume-request --session abc123"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_other_commands_not_blocked(self):
        """inbox, send, log etc. should not be blocked by lifecycle gate."""
        rc, out = run_hook(make_bash("py tools/agent_bus_cli.py inbox --role developer"))
        assert out["hookSpecificOutput"]["permissionDecision"] == "allow"
