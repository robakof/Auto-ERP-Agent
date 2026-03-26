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

    def test_no_h1_duplicate(self, db, output_dir):
        """Files should NOT start with H1 matching filename (Obsidian shows filename as title)."""
        run_cli(["--output-dir", output_dir], db)
        for f in Path(output_dir).glob("*.md"):
            content = f.read_text(encoding="utf-8")
            stem = f.stem
            assert not content.startswith(f"# {stem}"), f"{f.name} has duplicate H1"

    def test_polish_labels(self, db, output_dir):
        run_cli(["--output-dir", output_dir], db)
        # Check that Polish labels from config are used
        for f in Path(output_dir).glob("*.md"):
            content = f.read_text(encoding="utf-8")
            assert "Unread" not in content, f"{f.name} has English 'Unread'"
            assert "In progress" not in content or "in_progress" not in content

    def test_kolejka_with_scoring(self, db, output_dir):
        run_bus(["backlog-add", "--title", "High-Low", "--area", "Dev",
                 "--value", "wysoka", "--effort", "mala", "--content", "x"], db)
        run_bus(["backlog-add", "--title", "Low-High", "--area", "Arch",
                 "--value", "niska", "--effort", "duza", "--content", "y"], db)
        run_cli(["--output-dir", output_dir], db)
        files = list(Path(output_dir).glob("*.md"))
        # Find the queue file (Kolejka.md by default config)
        queue = [f for f in files if "Kolejka" in f.name][0]
        content = queue.read_text(encoding="utf-8")
        high_pos = content.index("High-Low")
        low_pos = content.index("Low-High")
        assert high_pos < low_pos

    def test_empty_db_no_crash(self, db, output_dir):
        result = run_cli(["--output-dir", output_dir], db)
        assert result["ok"] is True
        assert result["files_written"] == 3

    def test_title_truncation(self, db, output_dir):
        long_title = "A" * 80
        run_bus(["backlog-add", "--title", long_title, "--area", "Dev", "--content", "x"], db)
        run_cli(["--output-dir", output_dir], db)
        files = list(Path(output_dir).glob("*.md"))
        queue = [f for f in files if "Kolejka" in f.name][0]
        content = queue.read_text(encoding="utf-8")
        assert long_title not in content
        assert "..." in content
