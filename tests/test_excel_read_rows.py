"""Testy dla tools/excel_read_rows.py."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from openpyxl import Workbook

import tools.excel_read_rows as rr


def make_xlsx(tmp_path, headers, rows, filename="test.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    path = tmp_path / filename
    wb.save(path)
    return path


class TestReadRows:
    def test_happy_path(self, tmp_path):
        path = make_xlsx(tmp_path,
                         ["CDN_Pole", "Alias", "Komentarz_Usera"],
                         [["Rez_GIDTyp", "Typ", "ok"], ["Rez_GIDNumer", "ID", ""]])
        result = rr.read_rows(path)
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert result["data"]["columns"] == ["CDN_Pole", "Alias", "Komentarz_Usera"]

    def test_filter_columns(self, tmp_path):
        path = make_xlsx(tmp_path, ["A", "B", "C"], [["a", "b", "c"]])
        result = rr.read_rows(path, columns=["A", "C"])
        assert result["data"]["columns"] == ["A", "C"]
        assert result["data"]["rows"][0] == ["a", "c"]

    def test_file_not_found(self, tmp_path):
        result = rr.read_rows(tmp_path / "missing.xlsx")
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_sheet_not_found(self, tmp_path):
        path = make_xlsx(tmp_path, ["A"], [[1]])
        result = rr.read_rows(path, sheet_name="Missing")
        assert result["ok"] is False
        assert result["error"]["type"] == "SHEET_NOT_FOUND"

    def test_all_columns_when_no_filter(self, tmp_path):
        path = make_xlsx(tmp_path, ["A", "B", "C"], [[1, 2, 3]])
        result = rr.read_rows(path)
        assert result["data"]["columns"] == ["A", "B", "C"]


class TestMain:
    def test_valid_call_prints_json(self, tmp_path, capsys):
        path = make_xlsx(tmp_path, ["X", "Y"], [[1, 2]])
        with patch("sys.argv", ["excel_read_rows.py", "--file", str(path)]):
            rr.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["row_count"] == 1

    def test_columns_filter_via_cli(self, tmp_path, capsys):
        path = make_xlsx(tmp_path, ["A", "B", "C"], [["a", "b", "c"]])
        with patch("sys.argv", ["excel_read_rows.py", "--file", str(path), "--columns", "A,C"]):
            rr.main()
        result = json.loads(capsys.readouterr().out)
        assert result["data"]["columns"] == ["A", "C"]
