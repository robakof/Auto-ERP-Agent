"""Testy jednostkowe dla tools/lib/output.py."""

import io
import json
import sys

import pytest

from tools.lib.output import print_json


class TestPrintJson:
    def _capture(self, result: dict) -> str:
        """Przechwytuje stdout z print_json jako string UTF-8."""
        buf = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        original = sys.stdout
        sys.stdout = buf
        try:
            print_json(result)
        finally:
            sys.stdout = original
        buf.seek(0)
        return buf.read()

    def test_polish_chars_preserved(self):
        result = {"ok": True, "data": {"label": "Nagłówki dokumentów"}}
        captured = self._capture(result)
        parsed = json.loads(captured)
        assert parsed["data"]["label"] == "Nagłówki dokumentów"

    def test_all_polish_letters(self):
        polish = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"
        result = {"ok": True, "data": {"text": polish}}
        captured = self._capture(result)
        parsed = json.loads(captured)
        assert parsed["data"]["text"] == polish

    def test_valid_json_output(self):
        result = {"ok": True, "data": {"col": "wartość"}, "error": None}
        captured = self._capture(result)
        parsed = json.loads(captured)
        assert parsed["ok"] is True

    def test_nested_structure_preserved(self):
        result = {
            "ok": True,
            "data": {"results": [{"table_name": "CDN.TrNag", "col_label": "Numer zamówienia"}]},
        }
        captured = self._capture(result)
        parsed = json.loads(captured)
        assert parsed["data"]["results"][0]["col_label"] == "Numer zamówienia"
