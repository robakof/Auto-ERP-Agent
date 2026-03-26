"""Tests for tools/render_dashboard.py — markdown dashboard generation."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CLI = str(Path(__file__).parent.parent / "tools" / "render_dashboard.py")
PYTHON = sys.executable
BUS_CLI = str(Path(__file__).parent.parent / "tools" / "agent_bus_cli.py")


def run_cli(args: list[str], db_path: str) -> dict:
    result = subprocess.run(
        [PYTHON, CLI, "--db", db_path] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


def run_bus(args: list[str], db_path: str) -> dict:
    result = subprocess.run(
        [PYTHON, BUS_CLI, "--db", db_path] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "test_dashboard.db")


@pytest.fixture
def output_dir(tmp_path):
    d = tmp_path / "dashboard"
    d.mkdir()
    return str(d)


class TestDashboardGeneration:
    def test_generates_three_files(self, db, output_dir):
        result = run_cli(["--output-dir", output_dir], db)
        assert result["ok"] is True
        assert result["files_written"] == 3
        for name in ["status.md", "workstreams.md", "backlog_overview.md"]:
            assert (Path(output_dir) / name).exists()

    def test_status_contains_sections(self, db, output_dir):
        result = run_cli(["--output-dir", output_dir], db)
        content = (Path(output_dir) / "status.md").read_text(encoding="utf-8")
        assert "# Status mrowiska" in content
        assert "Live agents" in content or "Aktywni agenci" in content

    def test_backlog_overview_with_data(self, db, output_dir):
        run_bus(["backlog-add", "--title", "Task1", "--area", "Dev",
                 "--value", "wysoka", "--content", "x"], db)
        run_bus(["backlog-add", "--title", "Task2", "--area", "Arch",
                 "--content", "y"], db)
        result = run_cli(["--output-dir", output_dir], db)
        content = (Path(output_dir) / "backlog_overview.md").read_text(encoding="utf-8")
        assert "Dev" in content
        assert "Arch" in content

    def test_empty_db_no_crash(self, db, output_dir):
        result = run_cli(["--output-dir", output_dir], db)
        assert result["ok"] is True
        # Files should still be created (empty state)
        for name in ["status.md", "workstreams.md", "backlog_overview.md"]:
            assert (Path(output_dir) / name).exists()
