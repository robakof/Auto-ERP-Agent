"""Testy jednostkowe dla bot/sql_executor.py."""

from unittest.mock import patch

import pytest

from bot.sql_executor import ExecutionResult, SqlExecutor
from tests.conftest import make_mock_conn


class TestExecutionResult:
    def test_ok_result(self):
        r = ExecutionResult(ok=True, columns=["a"], rows=[[1]], row_count=1, error=None, duration_ms=10)
        assert r.ok is True
        assert r.row_count == 1

    def test_error_result(self):
        r = ExecutionResult(ok=False, columns=[], rows=[], row_count=0, error="SQL_ERROR", duration_ms=0)
        assert r.ok is False
        assert r.error == "SQL_ERROR"


class TestSqlExecutor:
    def setup_method(self):
        self.executor = SqlExecutor()

    def test_happy_path(self):
        mock_conn, _ = make_mock_conn(["Nazwa", "ID"], [["Bolsius", 1], ["Firma X", 2]])
        with patch.object(self.executor.client, "get_connection", return_value=mock_conn):
            result = self.executor.execute("SELECT TOP 2 Nazwa, ID FROM AIBI.Zamowienia")
        assert result.ok is True
        assert result.row_count == 2
        assert result.columns == ["Nazwa", "ID"]
        assert result.rows[0] == ["Bolsius", 1]
        assert result.error is None

    def test_empty_result(self):
        mock_conn, _ = make_mock_conn(["Nazwa"], [])
        with patch.object(self.executor.client, "get_connection", return_value=mock_conn):
            result = self.executor.execute("SELECT TOP 50 Nazwa FROM AIBI.Zamowienia WHERE 1=0")
        assert result.ok is True
        assert result.row_count == 0
        assert result.rows == []

    def test_validation_error_propagated(self):
        result = self.executor.execute("DELETE FROM AIBI.Zamowienia")
        assert result.ok is False
        assert result.error is not None

    def test_duration_ms_present(self):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch.object(self.executor.client, "get_connection", return_value=mock_conn):
            result = self.executor.execute("SELECT TOP 1 n FROM AIBI.Zamowienia")
        assert isinstance(result.duration_ms, int)
        assert result.duration_ms >= 0

    def test_uses_bot_sql_client(self):
        """SqlExecutor używa create_bot_sql_client — sprawdzamy że klient jest tworzony."""
        from tools.lib.sql_client import SqlClient
        assert isinstance(self.executor.client, SqlClient)
