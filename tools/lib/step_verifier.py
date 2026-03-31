"""StepVerifier — external artifact verification for workflow steps (ADR-002, Faza 4).

Dispatches verification per type defined in workflow_steps.verification_type.
Called by WorkflowEngine.complete_step() when agent declares PASS.

Verification types:
    file_exists    — os.path.exists(path)
    file_not_empty — os.path.getsize(path) > 0
    test_pass      — pytest exit code 0
    commit_exists  — git log --grep=pattern finds match
    message_sent   — messages table has recent entry
    git_clean      — git status --porcelain is empty
    manual         — always PASS (human/semantic review)
"""

import os
import sqlite3
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class VerifyResult:
    """Result of step verification."""
    ok: bool
    verification_type: str
    message: str = ""


class StepVerifier:
    """Dispatch verification per type."""

    def __init__(self, db_path: str = "mrowisko.db"):
        self._db_path = db_path

    def verify(self, verification_type: str, verification_value: str) -> VerifyResult:
        """Verify step artifact. Returns VerifyResult."""
        dispatch = {
            "file_exists": self._verify_file_exists,
            "file_not_empty": self._verify_file_not_empty,
            "test_pass": self._verify_test_pass,
            "commit_exists": self._verify_commit_exists,
            "message_sent": self._verify_message_sent,
            "git_clean": self._verify_git_clean,
            "manual": self._verify_manual,
        }
        handler = dispatch.get(verification_type, self._verify_manual)
        return handler(verification_value)

    def _verify_file_exists(self, path: str) -> VerifyResult:
        if os.path.exists(path):
            return VerifyResult(ok=True, verification_type="file_exists")
        return VerifyResult(
            ok=False, verification_type="file_exists",
            message=f"File not found: {path}",
        )

    def _verify_file_not_empty(self, path: str) -> VerifyResult:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return VerifyResult(ok=True, verification_type="file_not_empty")
        if not os.path.exists(path):
            return VerifyResult(
                ok=False, verification_type="file_not_empty",
                message=f"File not found: {path}",
            )
        return VerifyResult(
            ok=False, verification_type="file_not_empty",
            message=f"File is empty: {path}",
        )

    def _verify_test_pass(self, test_path: str) -> VerifyResult:
        try:
            result = subprocess.run(
                ["py", "-m", "pytest", test_path, "--tb=no", "-q"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                return VerifyResult(ok=True, verification_type="test_pass")
            return VerifyResult(
                ok=False, verification_type="test_pass",
                message=f"Tests failed (exit {result.returncode}): {result.stdout[-200:]}",
            )
        except Exception as e:
            return VerifyResult(
                ok=False, verification_type="test_pass",
                message=f"Test execution error: {e}",
            )

    def _verify_commit_exists(self, pattern: str) -> VerifyResult:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-1", f"--grep={pattern}"],
                capture_output=True, text=True, timeout=10,
            )
            if result.stdout.strip():
                return VerifyResult(ok=True, verification_type="commit_exists")
            return VerifyResult(
                ok=False, verification_type="commit_exists",
                message=f"No commit matching: {pattern}",
            )
        except Exception as e:
            return VerifyResult(
                ok=False, verification_type="commit_exists",
                message=f"Git error: {e}",
            )

    def _verify_message_sent(self, value: str) -> VerifyResult:
        """Check if a recent message exists. Value can be message_id or empty (check last)."""
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA busy_timeout=1000")
            if value and value.isdigit():
                row = conn.execute(
                    "SELECT id FROM messages WHERE id=?", (int(value),)
                ).fetchone()
            else:
                # Check if any message was sent in last 5 minutes
                row = conn.execute(
                    "SELECT id FROM messages WHERE created_at > datetime('now', '-5 minutes') "
                    "ORDER BY id DESC LIMIT 1"
                ).fetchone()
            conn.close()
            if row:
                return VerifyResult(ok=True, verification_type="message_sent")
            return VerifyResult(
                ok=False, verification_type="message_sent",
                message="No matching message found",
            )
        except Exception as e:
            return VerifyResult(
                ok=False, verification_type="message_sent",
                message=f"DB error: {e}",
            )

    def _verify_git_clean(self, _value: str) -> VerifyResult:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=10,
            )
            if not result.stdout.strip():
                return VerifyResult(ok=True, verification_type="git_clean")
            return VerifyResult(
                ok=False, verification_type="git_clean",
                message=f"Working tree not clean: {result.stdout[:200]}",
            )
        except Exception as e:
            return VerifyResult(
                ok=False, verification_type="git_clean",
                message=f"Git error: {e}",
            )

    def _verify_manual(self, _value: str = "") -> VerifyResult:
        return VerifyResult(ok=True, verification_type="manual")
