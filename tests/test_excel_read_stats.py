"""Testy dla tools/excel_read_stats.py. Logika ExcelReader testowana w test_lib_excel_reader.py."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from openpyxl import Workbook

import tools.excel_read_stats as rs


def make_xlsx(tmp_path, headers, rows, filename="test.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    path = tmp_path / filename
    wb.save(path)
    return path


class TestReadStats:
    def test_happy_path(self, tmp_path):
        path = make_xlsx(tmp_path, ["A", "B"], [["x", 1], ["y", 2]])
        result = rs.read_stats(path)
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2

    def test_file_not_found(self, tmp_path):
        result = rs.read_stats(tmp_path / "missing.xlsx")
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_sheet_not_found(self, tmp_path):
        path = make_xlsx(tmp_path, ["A"], [[1]])
        result = rs.read_stats(path, sheet_name="Missing")
        assert result["ok"] is False
        assert result["error"]["type"] == "SHEET_NOT_FOUND"

    def test_filter_columns(self, tmp_path):
        path = make_xlsx(tmp_path, ["A", "B", "C"], [[1, 2, 3]])
        result = rs.read_stats(path, columns=["A", "C"])
        names = [c["name"] for c in result["data"]["columns"]]
        assert names == ["A", "C"]


class TestMain:
    def test_valid_call_prints_json(self, tmp_path, capsys):
        path = make_xlsx(tmp_path, ["X"], [[1]])
        with patch("sys.argv", ["excel_read_stats.py", "--file", str(path)]):
            rs.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
