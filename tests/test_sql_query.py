"""Testy jednostkowe dla tools/sql_query.py. Połączenie z bazą jest mockowane."""

import json
import sys
from unittest.mock import MagicMock, patch

import pyodbc
import pytest

import tools.sql_query as sq


# ── Helpers ────────────────────────────────────────────────────────────────


def make_mock_conn(columns: list[str], rows: list[list]) -> tuple[MagicMock, MagicMock]:
    """Zwraca (mock_conn, mock_cursor) z zaprogramowanymi kolumnami i wierszami."""
    mock_cursor = MagicMock()
    mock_cursor.description = [(col, None, None, None, None, None, None) for col in columns]
    mock_cursor.fetchall.return_value = [tuple(row) for row in rows]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


# ── TestValidateQuery ───────────────────────────────────────────────────────


class TestValidateQuery:
    def test_valid_select(self):
        assert sq.validate_query("SELECT * FROM CDN.ZamNag") is None

    def test_valid_select_with_top(self):
        assert sq.validate_query("SELECT TOP 10 col FROM t") is None

    def test_blocks_insert(self):
        result = sq.validate_query("INSERT INTO CDN.ZamNag VALUES (1)")
        assert result is not None
        assert "INSERT" in result

    def test_blocks_delete(self):
        result = sq.validate_query("DELETE FROM CDN.ZamNag")
        assert result is not None
        assert "DELETE" in result

    def test_blocks_update(self):
        result = sq.validate_query("UPDATE CDN.ZamNag SET col=1")
        assert result is not None

    def test_blocks_drop(self):
        result = sq.validate_query("DROP TABLE CDN.ZamNag")
        assert result is not None

    def test_blocks_exec(self):
        result = sq.validate_query("EXEC sp_who")
        assert result is not None
        assert "EXEC" in result

    def test_blocks_xp_cmdshell(self):
        result = sq.validate_query("SELECT * FROM t; EXEC xp_cmdshell('dir')")
        assert result is not None

    def test_blocks_multiple_statements(self):
        result = sq.validate_query("SELECT 1; SELECT 2")
        assert result is not None
        assert "MULTIPLE_STATEMENTS" in result

    def test_blocks_non_select(self):
        result = sq.validate_query("SHOW TABLES")
        assert result is not None
        assert "NOT_SELECT" in result

    def test_case_insensitive_blocking(self):
        assert sq.validate_query("insert into t values(1)") is not None
        assert sq.validate_query("Delete from t") is not None

    def test_semicolon_at_end_allowed(self):
        # Jedno zapytanie zakończone średnikiem — dozwolone
        assert sq.validate_query("SELECT * FROM t;") is None


# ── TestRunQuery ────────────────────────────────────────────────────────────


class TestRunQuery:
    def test_happy_path(self):
        mock_conn, _ = make_mock_conn(["col1", "col2"], [["a", 1], ["b", 2]])
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT col1, col2 FROM t")
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert result["data"]["columns"] == ["col1", "col2"]
        assert result["data"]["rows"] == [["a", 1], ["b", 2]]
        assert result["error"] is None

    def test_injects_top_100(self):
        mock_conn, mock_cursor = make_mock_conn(["n"], [[i] for i in range(100)])
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            sq.run_query("SELECT n FROM t")
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TOP 100" in executed_sql.upper()

    def test_no_top_injection_when_top_present(self):
        mock_conn, mock_cursor = make_mock_conn(["n"], [[1]])
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            sq.run_query("SELECT TOP 5 n FROM t")
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TOP 5" in executed_sql.upper()
        assert executed_sql.upper().count("TOP") == 1

    def test_validation_error_returned_as_json(self):
        result = sq.run_query("DELETE FROM t")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"
        assert result["data"] is None

    def test_sql_error_returned_as_json(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.execute.side_effect = pyodbc.Error(
            "42S02", "[42S02] Invalid object name 'NonExistent'"
        )
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT * FROM NonExistent")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"
        assert "NonExistent" in result["error"]["message"]

    def test_truncated_true_when_exactly_100_rows(self):
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(100)])
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT n FROM t")
        assert result["meta"]["truncated"] is True

    def test_truncated_false_when_less_than_100_rows(self):
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(42)])
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT n FROM t")
        assert result["meta"]["truncated"] is False

    def test_duration_ms_present(self):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT n FROM t")
        assert isinstance(result["meta"]["duration_ms"], int)
        assert result["meta"]["duration_ms"] >= 0

    def test_result_is_json_serializable(self):
        """Datetime i Decimal nie mogą blokować serializacji (default=str w main)."""
        from datetime import datetime
        from decimal import Decimal
        mock_conn, _ = make_mock_conn(["d", "v"], [[datetime(2024, 1, 1), Decimal("3.14")]])
        with patch("tools.sql_query.get_connection", return_value=mock_conn):
            result = sq.run_query("SELECT d, v FROM t")
        # json.dumps z default=str nie może rzucić wyjątku
        json.dumps(result, default=str)


# ── TestMain ────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_argument_returns_error_json(self, capsys):
        with patch("sys.argv", ["sql_query.py"]):
            sq.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is False
        assert result["error"]["type"] == "MISSING_ARGUMENT"

    def test_valid_query_prints_json(self, capsys):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch("sys.argv", ["sql_query.py", "SELECT n FROM t"]):
            with patch("tools.sql_query.get_connection", return_value=mock_conn):
                sq.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["ok"] is True
