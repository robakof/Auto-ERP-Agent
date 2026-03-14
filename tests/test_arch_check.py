"""Tests for arch_check.py."""

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.arch_check import check_file


def make_md(tmp_path, content):
    f = tmp_path / "test.md"
    f.write_text(content, encoding="utf-8")
    return f


class TestCheckFile:
    def test_no_issues_when_all_paths_exist(self, tmp_path):
        (tmp_path / "tools").mkdir()
        (tmp_path / "tools" / "existing.py").write_text("")
        f = make_md(tmp_path, "Use `tools/existing.py` to run")
        import tools.arch_check as mod
        original = mod.PROJECT_ROOT
        mod.PROJECT_ROOT = tmp_path
        try:
            assert check_file(f) == []
        finally:
            mod.PROJECT_ROOT = original

    def test_returns_issue_for_missing_path(self, tmp_path):
        f = make_md(tmp_path, "See `documents/missing/file.md` for details")
        import tools.arch_check as mod
        original = mod.PROJECT_ROOT
        mod.PROJECT_ROOT = tmp_path
        try:
            issues = check_file(f)
            assert len(issues) == 1
            assert issues[0]["ref"] == "documents/missing/file.md"
        finally:
            mod.PROJECT_ROOT = original

    def test_skips_wildcard_patterns(self, tmp_path):
        f = make_md(tmp_path, "Files: `solutions/bi/views/*.sql`")
        import tools.arch_check as mod
        original = mod.PROJECT_ROOT
        mod.PROJECT_ROOT = tmp_path
        try:
            assert check_file(f) == []
        finally:
            mod.PROJECT_ROOT = original

    def test_skips_placeholder_patterns(self, tmp_path):
        f = make_md(tmp_path, "Path: `solutions/bi/{Widok}/draft.sql`")
        import tools.arch_check as mod
        original = mod.PROJECT_ROOT
        mod.PROJECT_ROOT = tmp_path
        try:
            assert check_file(f) == []
        finally:
            mod.PROJECT_ROOT = original

    def test_reports_correct_line_number(self, tmp_path):
        f = make_md(tmp_path, "line1\nline2\nSee `tools/missing.py`\nline4")
        import tools.arch_check as mod
        original = mod.PROJECT_ROOT
        mod.PROJECT_ROOT = tmp_path
        try:
            issues = check_file(f)
            assert issues[0]["line"] == 3
        finally:
            mod.PROJECT_ROOT = original
