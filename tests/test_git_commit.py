"""Testy dla tools/git_commit.py."""

import subprocess
from unittest.mock import call, patch

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.git_commit import git_commit


def make_result(returncode=0, stdout="", stderr=""):
    result = subprocess.CompletedProcess(args=[], returncode=returncode)
    result.stdout = stdout
    result.stderr = stderr
    return result


# --- happy path ---

def test_commit_message_only():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message="feat: test")
    assert result["ok"] is True
    mock_run.assert_called_once_with(
        ["git", "commit", "-m", "feat: test"],
        capture_output=True, text=True, cwd="."
    )


def test_commit_with_all_flag():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message="feat: test", add_all=True)
    assert result["ok"] is True
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0] == call(
        ["git", "add", "-A"],
        capture_output=True, text=True, cwd="."
    )
    assert mock_run.call_args_list[1] == call(
        ["git", "commit", "-m", "feat: test"],
        capture_output=True, text=True, cwd="."
    )


def test_commit_with_specific_files():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message="feat: test", files=["a.py", "b.py"])
    assert result["ok"] is True
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0] == call(
        ["git", "add", "a.py", "b.py"],
        capture_output=True, text=True, cwd="."
    )


def test_commit_with_push():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message="feat: test", push=True)
    assert result["ok"] is True
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[1] == call(
        ["git", "push"],
        capture_output=True, text=True, cwd="."
    )


def test_commit_all_and_push():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message="feat: test", add_all=True, push=True)
    assert result["ok"] is True
    assert mock_run.call_count == 3
    commands = [c.args[0] for c in mock_run.call_args_list]
    assert commands[0] == ["git", "add", "-A"]
    assert commands[1] == ["git", "commit", "-m", "feat: test"]
    assert commands[2] == ["git", "push"]


def test_multiline_message():
    msg = "feat: test\n\nDodatkowy opis."
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message=msg)
    assert result["ok"] is True
    mock_run.assert_called_once_with(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True, cwd="."
    )


def test_custom_path():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message="feat: test", path="/some/repo")
    assert result["ok"] is True
    mock_run.assert_called_once_with(
        ["git", "commit", "-m", "feat: test"],
        capture_output=True, text=True, cwd="/some/repo"
    )


# --- błędy ---

def test_commit_git_error_propagates():
    with patch("subprocess.run", return_value=make_result(returncode=1, stderr="nothing to commit")):
        result = git_commit(message="feat: test")
    assert result["ok"] is False
    assert result["error"]["type"] == "GIT_ERROR"
    assert "nothing to commit" in result["error"]["message"]


def test_add_error_stops_before_commit():
    add_fail = make_result(returncode=1, stderr="pathspec error")
    with patch("subprocess.run", return_value=add_fail) as mock_run:
        result = git_commit(message="feat: test", add_all=True)
    assert result["ok"] is False
    assert mock_run.call_count == 1  # commit nie był wywołany


def test_push_error_after_successful_commit():
    commit_ok = make_result(returncode=0, stdout="[main abc1234] feat: test")
    push_fail = make_result(returncode=1, stderr="remote rejected")

    with patch("subprocess.run", side_effect=[commit_ok, push_fail]):
        result = git_commit(message="feat: test", push=True)
    assert result["ok"] is False
    assert result["error"]["type"] == "GIT_ERROR"


def test_message_required():
    with pytest.raises(ValueError, match="message"):
        git_commit(message="")


def test_push_only():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(push_only=True)
    assert result["ok"] is True
    mock_run.assert_called_once_with(
        ["git", "push"],
        capture_output=True, text=True, cwd="."
    )


def test_push_only_ignores_message():
    with patch("subprocess.run", return_value=make_result()) as mock_run:
        result = git_commit(message="", push_only=True)
    assert result["ok"] is True
    assert mock_run.call_count == 1


def test_push_only_error():
    with patch("subprocess.run", return_value=make_result(returncode=1, stderr="rejected")):
        result = git_commit(push_only=True)
    assert result["ok"] is False
    assert "rejected" in result["error"]["message"]
