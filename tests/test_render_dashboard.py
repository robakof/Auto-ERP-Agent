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
        for name in ["Status.md", "Praca.md", "Kolejka.md"]:
            assert (Path(output_dir) / name).exists()

    def test_status_contains_metrics_header(self, db, output_dir):
        run_cli(["--output-dir", output_dir], db)
        content = (Path(output_dir) / "Status.md").read_text(encoding="utf-8")
        assert "Mrowisko" in content
        assert "Agenci" in content
        assert "Unread" in content

    def test_kolejka_with_scoring(self, db, output_dir):
        run_bus(["backlog-add", "--title", "High-Low", "--area", "Dev",
                 "--value", "wysoka", "--effort", "mala", "--content", "x"], db)
        run_bus(["backlog-add", "--title", "Low-High", "--area", "Arch",
                 "--value", "niska", "--effort", "duza", "--content", "y"], db)
        run_cli(["--output-dir", output_dir], db)
        content = (Path(output_dir) / "Kolejka.md").read_text(encoding="utf-8")
        assert "High-Low" in content
        assert "Pkt" in content
        # High-value/low-effort should be first (score 10)
        high_pos = content.index("High-Low")
        low_pos = content.index("Low-High")
        assert high_pos < low_pos

    def test_empty_db_no_crash(self, db, output_dir):
        result = run_cli(["--output-dir", output_dir], db)
        assert result["ok"] is True
        for name in ["Status.md", "Praca.md", "Kolejka.md"]:
            assert (Path(output_dir) / name).exists()
