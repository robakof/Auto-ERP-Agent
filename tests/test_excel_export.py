"""Testy dla tools/excel_export.py. Logika SQL/Excel testowana w test_lib_*."""

import json
from pathlib import Path
from unittest.mock import patch

import pyodbc
import pytest

from tests.conftest import make_mock_conn
from tools.lib.sql_client import SqlClient
import tools.excel_export as ee


class TestExportToExcel:
    def test_happy_path(self, tmp_path):
        mock_conn, _ = make_mock_conn(["Kod", "Ilosc"], [["ABC", 5], ["XYZ", 10]])
        output = tmp_path / "out.xlsx"
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = ee.export_to_excel("SELECT Kod, Ilosc FROM t", output)
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert result["data"]["columns"] == ["Kod", "Ilosc"]
        assert result["data"]["path"] == str(output.resolve())
        assert output.exists()

    def test_validation_error(self, tmp_path):
        output = tmp_path / "out.xlsx"
        result = ee.export_to_excel("DELETE FROM t", output)
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"
        assert not output.exists()

    def test_sql_error(self, tmp_path):
        mock_conn = make_mock_conn([], [])[0]
        mock_conn.cursor.return_value.execute.side_effect = pyodbc.Error(
            "42S02", "[42S02] Invalid object name 'X'"
        )
        output = tmp_path / "out.xlsx"
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = ee.export_to_excel("SELECT * FROM X", output)
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_default_output_path(self, tmp_path):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            with patch("tools.excel_export.EXPORTS_DIR", tmp_path):
                result = ee.export_to_excel("SELECT n FROM t")
        assert result["ok"] is True
        assert result["data"]["path"].endswith(".xlsx")

    def test_view_name_in_filename(self, tmp_path):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            with patch("tools.excel_export.EXPORTS_DIR", tmp_path):
                result = ee.export_to_excel("SELECT n FROM t", view_name="Rezerwacje")
        assert "Rezerwacje" in result["data"]["path"]

    def test_stable_output_path(self, tmp_path):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        output = tmp_path / "plan.xlsx"
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = ee.export_to_excel("SELECT n FROM t", output_path=output)
        assert result["data"]["path"] == str(output.resolve())

    def test_injects_top_1000(self, tmp_path):
        mock_conn, mock_cursor = make_mock_conn(["n"], [[1]])
        output = tmp_path / "out.xlsx"
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            ee.export_to_excel("SELECT n FROM t", output)
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TOP 1000" in executed_sql.upper()


class TestMain:
    def test_valid_query_prints_json(self, tmp_path, capsys):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        output = tmp_path / "out.xlsx"
        with patch("sys.argv", ["excel_export.py", "SELECT n FROM t", "--output", str(output)]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                ee.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True

    def test_output_flag(self, tmp_path, capsys):
        mock_conn, _ = make_mock_conn(["n"], [[42]])
        output = tmp_path / "custom.xlsx"
        with patch("sys.argv", ["excel_export.py", "SELECT n FROM t", "-o", str(output)]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                ee.main()
        assert output.exists()
