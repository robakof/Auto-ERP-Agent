"""Testy jednostkowe dla tools/sql_query.py. Logika SQL testowana w test_lib_sql_client.py."""

import json
from unittest.mock import patch

import pyodbc
import pytest

from tests.conftest import make_mock_conn
from tools.lib.sql_client import SqlClient
import tools.sql_query as sq


class TestRunQuery:
    def test_happy_path(self):
        mock_conn, _ = make_mock_conn(["col1", "col2"], [["a", 1], ["b", 2]])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT col1, col2 FROM t")
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert result["data"]["columns"] == ["col1", "col2"]
        assert result["data"]["rows"] == [["a", 1], ["b", 2]]
        assert result["error"] is None

    def test_validation_error(self):
        result = sq.run_query("DELETE FROM t")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"
        assert result["data"] is None

    def test_sql_error(self):
        mock_conn = make_mock_conn([], [])[0]
        mock_conn.cursor.return_value.execute.side_effect = pyodbc.Error(
            "42S02", "[42S02] Invalid object name 'X'"
        )
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT * FROM X")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_truncated_true_when_100_rows(self):
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(100)])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT n FROM t")
        assert result["meta"]["truncated"] is True

    def test_truncated_false_when_fewer_rows(self):
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(42)])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT n FROM t")
        assert result["meta"]["truncated"] is False

    def test_duration_ms_present(self):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT n FROM t")
        assert isinstance(result["meta"]["duration_ms"], int)

    def test_result_json_serializable(self):
        from datetime import datetime
        from decimal import Decimal
        mock_conn, _ = make_mock_conn(["d", "v"], [[datetime(2024, 1, 1), Decimal("3.14")]])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT d, v FROM t")
        json.dumps(result, default=str)


class TestMain:
    def test_no_argument_returns_error_json(self, capsys):
        with patch("sys.argv", ["sql_query.py"]):
            sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "MISSING_ARGUMENT"

    def test_valid_query_prints_json(self, capsys):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch("sys.argv", ["sql_query.py", "SELECT n FROM t"]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
