"""Tests for ksef_config_gui .env reader/writer."""
from __future__ import annotations

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.ksef_config_gui import read_env, write_env


def test_read_env_parses_key_value(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nBAZ=123\n", encoding="utf-8")

    lines, values = read_env(env)

    assert values["FOO"] == "bar"
    assert values["BAZ"] == "123"
    assert len(lines) == 2


def test_read_env_skips_comments(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comment\nFOO=bar\n", encoding="utf-8")

    _, values = read_env(env)

    assert "comment" not in values
    assert values["FOO"] == "bar"


def test_read_env_missing_file(tmp_path):
    env = tmp_path / "nonexistent"

    lines, values = read_env(env)

    assert lines == []
    assert values == {}


def test_write_env_preserves_comments(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# header\nFOO=old\n# footer\n", encoding="utf-8")

    lines, _ = read_env(env)
    write_env(env, lines, {"FOO": "new"})

    content = env.read_text(encoding="utf-8")
    assert "# header" in content
    assert "# footer" in content
    assert "FOO=new" in content
    assert "FOO=old" not in content


def test_write_env_preserves_order(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\nB=2\nC=3\n", encoding="utf-8")

    lines, _ = read_env(env)
    write_env(env, lines, {"A": "10", "B": "20", "C": "30"})

    result_lines = env.read_text(encoding="utf-8").strip().split("\n")
    assert result_lines[0] == "A=10"
    assert result_lines[1] == "B=20"
    assert result_lines[2] == "C=30"


def test_write_env_adds_new_keys(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n", encoding="utf-8")

    lines, _ = read_env(env)
    write_env(env, lines, {"FOO": "bar", "NEW_KEY": "value"})

    _, values = read_env(env)
    assert values["FOO"] == "bar"
    assert values["NEW_KEY"] == "value"


def test_roundtrip_no_changes(tmp_path):
    env = tmp_path / ".env"
    original = "# Config\nFOO=bar\nBAZ=123\n"
    env.write_text(original, encoding="utf-8")

    lines, values = read_env(env)
    write_env(env, lines, values)

    result = env.read_text(encoding="utf-8")
    # Should preserve structure (comments + values)
    assert "# Config" in result
    assert "FOO=bar" in result
    assert "BAZ=123" in result
