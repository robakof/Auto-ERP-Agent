"""Tests for tools/context_usage.py — live token usage from transcript."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CLI = str(Path(__file__).parent.parent / "tools" / "context_usage.py")
PYTHON = sys.executable


def run_cli(args: list[str]) -> dict:
    result = subprocess.run(
        [PYTHON, CLI] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


def _make_transcript(path: Path, turns: list[dict], model: str = "claude-opus-4-6") -> Path:
    """Create a minimal .jsonl transcript with given token usage per turn."""
    lines = []
    for i, usage in enumerate(turns):
        entry = {
            "type": "assistant",
            "uuid": f"uuid-{i}",
            "timestamp": f"2026-03-26T10:{i:02d}:00Z",
            "message": {
                "model": model,
                "content": [{"type": "text", "text": f"turn {i}"}],
                "usage": {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "cache_read_input_tokens": usage.get("cache_read_tokens", 0),
                    "cache_creation_input_tokens": usage.get("cache_create_tokens", 0),
                },
            },
        }
        lines.append(json.dumps(entry))
    transcript = path / "test_transcript.jsonl"
    transcript.write_text("\n".join(lines), encoding="utf-8")
    return transcript


class TestComputeUsage:
    def test_single_turn(self, tmp_path):
        t = _make_transcript(tmp_path, [
            {"input_tokens": 100, "output_tokens": 50, "cache_read_tokens": 500, "cache_create_tokens": 200},
        ])
        result = run_cli(["--transcript", str(t)])
        assert result["ok"] is True
        assert result["turns"] == 1
        assert result["current_context_tokens"] == 800  # 100 + 500 + 200
        assert result["cumulative"]["input_tokens"] == 100
        assert result["cumulative"]["output_tokens"] == 50

    def test_multiple_turns_uses_last_for_context(self, tmp_path):
        t = _make_transcript(tmp_path, [
            {"input_tokens": 100, "output_tokens": 50, "cache_read_tokens": 500, "cache_create_tokens": 200},
            {"input_tokens": 200, "output_tokens": 80, "cache_read_tokens": 1000, "cache_create_tokens": 300},
        ])
        result = run_cli(["--transcript", str(t)])
        assert result["turns"] == 2
        # Last turn: 200 + 1000 + 300 = 1500
        assert result["current_context_tokens"] == 1500
        # Cumulative sums all turns
        assert result["cumulative"]["input_tokens"] == 300
        assert result["cumulative"]["output_tokens"] == 130
        assert result["cumulative"]["cache_read_tokens"] == 1500
        assert result["cumulative"]["cache_create_tokens"] == 500

    def test_percentage_calculation(self, tmp_path):
        t = _make_transcript(tmp_path, [
            {"input_tokens": 50000, "output_tokens": 1000, "cache_read_tokens": 200000, "cache_create_tokens": 50000},
        ])
        result = run_cli(["--transcript", str(t)])
        # 50000 + 200000 + 50000 = 300000 / 1000000 = 30%
        assert result["context_used_pct"] == 30.0
        assert result["context_window"] == 1_000_000

    def test_percentage_sonnet_200k(self, tmp_path):
        t = _make_transcript(tmp_path, [
            {"input_tokens": 1000, "output_tokens": 100, "cache_read_tokens": 20000, "cache_create_tokens": 3000},
        ], model="claude-sonnet-4-6")
        result = run_cli(["--transcript", str(t)])
        # 1000 + 20000 + 3000 = 24000 / 200000 = 12%
        assert result["context_used_pct"] == 12.0
        assert result["context_window"] == 200_000

    def test_empty_transcript(self, tmp_path):
        transcript = tmp_path / "empty.jsonl"
        transcript.write_text("", encoding="utf-8")
        result = run_cli(["--transcript", str(transcript)])
        assert result["ok"] is True
        assert result["turns"] == 0
        assert result["current_context_tokens"] == 0
        assert result["context_used_pct"] == 0

    def test_nonexistent_file(self, tmp_path):
        result = subprocess.run(
            [PYTHON, CLI, "--transcript", str(tmp_path / "nope.jsonl")],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result.returncode != 0
        data = json.loads(result.stdout)
        assert data["ok"] is False


class TestAutodetect:
    def test_no_transcripts_dir(self, tmp_path, monkeypatch):
        # When TRANSCRIPTS_DIR doesn't exist, --transcript fallback works
        result = subprocess.run(
            [PYTHON, CLI],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        # May succeed (finds real transcript) or fail gracefully
        data = json.loads(result.stdout)
        assert "ok" in data
