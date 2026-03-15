"""Smoke tests for on_stop hook — integration via subprocess."""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ON_STOP_SCRIPT = PROJECT_ROOT / "tools" / "hooks" / "on_stop.py"


def run_hook(payload: dict, tmp_path: Path, session_id: str = None) -> subprocess.CompletedProcess:
    """Run on_stop hook with given payload via stdin."""
    session_id_file = tmp_path / "session_id.txt"
    if session_id:
        session_id_file.write_text(session_id, encoding="utf-8")

    env_override = {"PYTHONPATH": str(PROJECT_ROOT)}
    import os
    env = {**os.environ, **env_override}

    return subprocess.run(
        [sys.executable, str(ON_STOP_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


class TestOnStopSmoke:
    def test_runs_without_error_on_empty_payload(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tmp").mkdir()
        result = run_hook({}, tmp_path)
        assert result.returncode == 0

    def test_runs_without_error_with_last_message(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tmp").mkdir()
        payload = {"last_assistant_message": "Sesja zakończona.", "transcript_path": ""}
        result = run_hook(payload, tmp_path, session_id="abc123")
        assert result.returncode == 0

    def test_handles_invalid_json_gracefully(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tmp").mkdir()
        import os
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
        result = subprocess.run(
            [sys.executable, str(ON_STOP_SCRIPT)],
            input="not-json",
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        assert result.returncode == 0
