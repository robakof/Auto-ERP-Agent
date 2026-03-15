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

    def test_file_flag_reads_sql_from_file(self, tmp_path, capsys):
        sql_file = tmp_path / "query.sql"
        sql_file.write_text("SELECT n FROM t", encoding="utf-8")
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch("sys.argv", ["sql_query.py", "--file", str(sql_file)]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True

    def test_file_flag_missing_file_returns_error(self, tmp_path, capsys):
        with patch("sys.argv", ["sql_query.py", "--file", str(tmp_path / "brak.sql")]):
            sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_export_flag_writes_excel_and_returns_path(self, tmp_path, capsys):
        export_path = tmp_path / "out.xlsx"
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch("sys.argv", ["sql_query.py", "SELECT n FROM t", "--export", str(export_path)]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert export_path.exists()
        assert result["data"]["export_path"] == str(export_path.resolve())

    def test_export_not_written_on_query_error(self, tmp_path, capsys):
        export_path = tmp_path / "out.xlsx"
        with patch("sys.argv", ["sql_query.py", "DELETE FROM t", "--export", str(export_path)]):
            sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert not export_path.exists()

    def test_count_only_excludes_rows(self, capsys):
        mock_conn, _ = make_mock_conn(["a", "b"], [["x", 1], ["y", 2]])
        with patch("sys.argv", ["sql_query.py", "SELECT a, b FROM t", "--count-only"]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert result["data"]["columns"] == ["a", "b"]
        assert "rows" not in result["data"]

    def test_count_only_on_error_returns_normal_error(self, capsys):
        with patch("sys.argv", ["sql_query.py", "DELETE FROM t", "--count-only"]):
            sq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"

    def test_quiet_ok_prints_plain_text(self, capsys):
        mock_conn, _ = make_mock_conn(["n"], [[1], [2], [3]])
        with patch("sys.argv", ["sql_query.py", "SELECT n FROM t", "--quiet"]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                sq.main()
        out = capsys.readouterr().out.strip()
        assert out == "OK 3"

    def test_quiet_error_prints_plain_text(self, capsys):
        with patch("sys.argv", ["sql_query.py", "DELETE FROM t", "--quiet"]):
            sq.main()
        out = capsys.readouterr().out.strip()
        assert out.startswith("ERROR:")

    def test_count_only_and_quiet_combined(self, capsys):
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(5)])
        with patch("sys.argv", ["sql_query.py", "SELECT n FROM t", "--count-only", "--quiet"]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                sq.main()
        out = capsys.readouterr().out.strip()
        assert out == "OK 5"

    def test_export_limit_passes_inject_top(self, tmp_path, capsys):
        export_path = tmp_path / "out.xlsx"
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(5)])
        with patch("sys.argv", ["sql_query.py", "SELECT n FROM t",
                                "--export", str(export_path), "--export-limit", "100000"]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                with patch.object(SqlClient, "execute", wraps=None) as mock_exec:
                    mock_exec.return_value = {
                        "ok": True, "rows": [[i] for i in range(5)],
                        "columns": ["n"], "row_count": 5,
                        "duration_ms": 10, "truncated": False,
                    }
                    sq.main()
                    called_inject_top = mock_exec.call_args[1].get("inject_top") or mock_exec.call_args[0][1]
                    assert called_inject_top == 100000

    def test_export_default_limit_is_100k(self, tmp_path, capsys):
        export_path = tmp_path / "out.xlsx"
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch("sys.argv", ["sql_query.py", "SELECT n FROM t", "--export", str(export_path)]):
            with patch.object(SqlClient, "execute", wraps=None) as mock_exec:
                mock_exec.return_value = {
                    "ok": True, "rows": [[1]], "columns": ["n"],
                    "row_count": 1, "duration_ms": 10, "truncated": False,
                }
                sq.main()
                called_inject_top = mock_exec.call_args[1].get("inject_top") or mock_exec.call_args[0][1]
                assert called_inject_top == 100_000

    def test_run_query_accepts_inject_top_param(self):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT n FROM t", inject_top=100000)
        assert result["ok"] is True
