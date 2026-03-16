"""Testy dla tools/git_commit.py."""

import subprocess
from unittest.mock import call, patch

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.git_commit import git_commit, _parse_status_files


def make_result(returncode=0, stdout="", stderr=""):
    result = subprocess.CompletedProcess(args=[], returncode=returncode)
    result.stdout = stdout
    result.stderr = stderr
    return result


# --- _parse_status_files ---

def test_parse_status_files_modified():
    output = " M tools/git_commit.py\n M tests/test_git_commit.py\n"
    assert _parse_status_files(output) == ["tools/git_commit.py", "tests/test_git_commit.py"]


def test_parse_status_files_untracked():
    output = "?? new_file.py\n"
    assert _parse_status_files(output) == ["new_file.py"]


def test_parse_status_files_renamed():
    output = "R  old.py -> new.py\n"
    assert _parse_status_files(output) == ["new.py"]


def test_parse_status_files_empty():
    assert _parse_status_files("") == []


# --- happy path ---

def test_commit_message_only():
    commit_ok = make_result(stdout="[main abc] feat: test")
    diff_tree_ok = make_result(stdout="tools/git_commit.py\n")

    with patch("subprocess.run", side_effect=[commit_ok, diff_tree_ok]) as mock_run:
        result = git_commit(message="feat: test")

    assert result["ok"] is True
    assert result["data"]["files_staged"] == ["tools/git_commit.py"]
    assert "warning" not in result["data"]
    mock_run.call_args_list[0] == call(
        ["git", "commit", "-m", "feat: test"],
        capture_output=True, text=True, cwd="."
    )


def test_commit_with_all_flag_includes_warning():
    add_ok = make_result()
    commit_ok = make_result(stdout="[main abc] feat: test")
    diff_tree_ok = make_result(stdout="a.py\nb.py\n")

    with patch("subprocess.run", side_effect=[add_ok, commit_ok, diff_tree_ok]):
        result = git_commit(message="feat: test", add_all=True)

    assert result["ok"] is True
    assert result["data"]["warning"] is not None
    assert result["data"]["files_staged"] == ["a.py", "b.py"]


def test_commit_with_specific_files_no_warning():
    add_ok = make_result()
    commit_ok = make_result(stdout="[main abc] feat: test")
    diff_tree_ok = make_result(stdout="a.py\n")

    with patch("subprocess.run", side_effect=[add_ok, commit_ok, diff_tree_ok]):
        result = git_commit(message="feat: test", files=["a.py"])

    assert result["ok"] is True
    assert "warning" not in result["data"]
    assert result["data"]["files_staged"] == ["a.py"]


def test_commit_with_push():
    commit_ok = make_result(stdout="[main abc] feat: test")
    diff_tree_ok = make_result(stdout="a.py\n")
    push_ok = make_result()

    with patch("subprocess.run", side_effect=[commit_ok, diff_tree_ok, push_ok]) as mock_run:
        result = git_commit(message="feat: test", push=True)

    assert result["ok"] is True
    last_call = mock_run.call_args_list[-1]
    assert last_call == call(["git", "push"], capture_output=True, text=True, cwd=".")


def test_commit_all_and_push():
    add_ok = make_result()
    commit_ok = make_result(stdout="[main abc] feat: test")
    diff_tree_ok = make_result(stdout="a.py\n")
    push_ok = make_result()

    with patch("subprocess.run", side_effect=[add_ok, commit_ok, diff_tree_ok, push_ok]) as mock_run:
        result = git_commit(message="feat: test", add_all=True, push=True)

    assert result["ok"] is True
    commands = [c.args[0] for c in mock_run.call_args_list]
    assert commands[0] == ["git", "add", "-A"]
    assert commands[1] == ["git", "commit", "-m", "feat: test"]
    assert commands[3] == ["git", "push"]


def test_multiline_message():
    msg = "feat: test\n\nDodatkowy opis."
    commit_ok = make_result(stdout="[main abc] feat: test")
    diff_tree_ok = make_result(stdout="")

    with patch("subprocess.run", side_effect=[commit_ok, diff_tree_ok]) as mock_run:
        result = git_commit(message=msg)

    assert result["ok"] is True
    mock_run.call_args_list[0] == call(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True, cwd="."
    )


def test_custom_path():
    commit_ok = make_result(stdout="[main abc] feat: test")
    diff_tree_ok = make_result(stdout="")

    with patch("subprocess.run", side_effect=[commit_ok, diff_tree_ok]) as mock_run:
        result = git_commit(message="feat: test", path="/some/repo")

    assert result["ok"] is True
    mock_run.call_args_list[0] == call(
        ["git", "commit", "-m", "feat: test"],
        capture_output=True, text=True, cwd="/some/repo"
    )


# --- dry-run ---

def test_dry_run_with_all():
    status_ok = make_result(stdout=" M tools/git_commit.py\n?? new.py\n")

    with patch("subprocess.run", return_value=status_ok) as mock_run:
        result = git_commit(add_all=True, dry_run=True)

    assert result["ok"] is True
    assert result["data"]["dry_run"] is True
    assert "tools/git_commit.py" in result["data"]["files_would_stage"]
    assert "new.py" in result["data"]["files_would_stage"]
    mock_run.assert_called_once_with(
        ["git", "status", "--short"],
        capture_output=True, text=True, cwd="."
    )


def test_dry_run_with_files():
    with patch("subprocess.run") as mock_run:
        result = git_commit(files=["a.py", "b.py"], dry_run=True)

    assert result["ok"] is True
    assert result["data"]["files_would_stage"] == ["a.py", "b.py"]
    mock_run.assert_not_called()


def test_dry_run_no_files():
    with patch("subprocess.run") as mock_run:
        result = git_commit(dry_run=True)

    assert result["ok"] is True
    assert result["data"]["files_would_stage"] == []
    mock_run.assert_not_called()


def test_dry_run_git_status_error():
    with patch("subprocess.run", return_value=make_result(returncode=1, stderr="not a git repo")):
        result = git_commit(add_all=True, dry_run=True)

    assert result["ok"] is False
    assert "not a git repo" in result["error"]["message"]


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
    assert mock_run.call_count == 1


def test_push_error_after_successful_commit():
    commit_ok = make_result(returncode=0, stdout="[main abc1234] feat: test")
    diff_tree_ok = make_result(stdout="a.py\n")
    push_fail = make_result(returncode=1, stderr="remote rejected")

    with patch("subprocess.run", side_effect=[commit_ok, diff_tree_ok, push_fail]):
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
