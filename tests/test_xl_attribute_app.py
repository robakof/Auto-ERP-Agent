"""Testy dla tools/xl_attribute_app.py.

Uwaga: renderowanie okna tkinter nie jest testowane jednostkowo (wymaga ekranu).
Testujemy tylko logikę pomocniczą (format_summary).
"""

import pytest
from tools.xl_attribute_app import format_summary


class TestFormatSummary:
    def test_all_success(self):
        data = {"success": 10, "failed": 0, "skipped": 0}
        result = format_summary(data)
        assert "✓ 10" in result
        assert "✗ 0" in result
        assert "— 0" in result

    def test_mixed_results(self):
        data = {"success": 5, "failed": 2, "skipped": 3}
        result = format_summary(data)
        assert "✓ 5" in result
        assert "✗ 2" in result
        assert "— 3" in result

    def test_all_failed(self):
        data = {"success": 0, "failed": 7, "skipped": 0}
        result = format_summary(data)
        assert "✓ 0" in result
        assert "✗ 7" in result

    def test_all_skipped(self):
        data = {"success": 0, "failed": 0, "skipped": 15}
        result = format_summary(data)
        assert "— 15" in result
