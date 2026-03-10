"""Testy jednostkowe dla tools/lib/sql_client.py."""

import json
from unittest.mock import MagicMock, patch

import pyodbc
import pytest

from tests.conftest import make_mock_conn
from tools.lib.sql_client import SqlClient, SqlCredentials, create_bot_sql_client, create_erp_sql_client


# ── TestValidate ─────────────────────────────────────────────────────────────


class TestValidate:
    def setup_method(self):
        self.client = SqlClient()

    def test_valid_select(self):
        assert self.client.validate("SELECT * FROM CDN.ZamNag") is None

    def test_valid_select_with_top(self):
        assert self.client.validate("SELECT TOP 10 col FROM t") is None

    def test_semicolon_at_end_allowed(self):
        assert self.client.validate("SELECT * FROM t;") is None

    def test_blocks_insert(self):
        result = self.client.validate("INSERT INTO t VALUES (1)")
        assert result is not None
        assert "INSERT" in result

    def test_blocks_delete(self):
        result = self.client.validate("DELETE FROM t")
        assert result is not None
        assert "DELETE" in result

    def test_blocks_update(self):
        assert self.client.validate("UPDATE t SET col=1") is not None

    def test_blocks_drop(self):
        assert self.client.validate("DROP TABLE t") is not None

    def test_blocks_exec(self):
        result = self.client.validate("EXEC sp_who")
        assert result is not None
        assert "EXEC" in result

    def test_blocks_multiple_statements(self):
        result = self.client.validate("SELECT 1; SELECT 2")
        assert result is not None
        assert "MULTIPLE_STATEMENTS" in result

    def test_semicolon_in_string_literal_allowed(self):
        assert self.client.validate("SELECT 'klucz; opis' FROM t") is None

    def test_semicolon_in_where_string_allowed(self):
        assert self.client.validate("SELECT * FROM t WHERE col = 'val; other'") is None

    def test_escaped_quote_in_string_allowed(self):
        assert self.client.validate("SELECT * FROM t WHERE col = 'val''s; text'") is None

    def test_trailing_semicolon_after_string_allowed(self):
        assert self.client.validate("SELECT * FROM t WHERE col = 'ok';") is None

    def test_semicolon_after_string_blocks_second_statement(self):
        result = self.client.validate("SELECT 'ok'; SELECT 2")
        assert result is not None
        assert "MULTIPLE_STATEMENTS" in result

    def test_sql_comment_lines_stripped_before_validation(self):
        sql = "-- komentarz\n-- drugi komentarz\nSELECT * FROM t"
        assert self.client.validate(sql) is None

    def test_sql_comment_inline_does_not_affect_validation(self):
        sql = "SELECT * FROM t -- filtruj aktywne"
        assert self.client.validate(sql) is None

    def test_blocks_non_select(self):
        result = self.client.validate("SHOW TABLES")
        assert result is not None
        assert "NOT_SELECT" in result

    def test_case_insensitive(self):
        assert self.client.validate("insert into t values(1)") is not None
        assert self.client.validate("Delete from t") is not None

    def test_valid_with_cte(self):
        sql = "WITH cte AS (SELECT id FROM t) SELECT * FROM cte"
        assert self.client.validate(sql) is None

    def test_valid_with_cte_multiline(self):
        sql = "WITH Sciezka AS (\n    SELECT id, name FROM t\n    UNION ALL\n    SELECT id, name FROM t2\n)\nSELECT * FROM Sciezka"
        assert self.client.validate(sql) is None

    def test_with_cte_lowercase(self):
        sql = "with cte as (select id from t) select * from cte"
        assert self.client.validate(sql) is None


# ── TestExecute ──────────────────────────────────────────────────────────────


class TestExecute:
    def setup_method(self):
        self.client = SqlClient()

    def test_happy_path(self):
        mock_conn, _ = make_mock_conn(["col1", "col2"], [["a", 1], ["b", 2]])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            result = self.client.execute("SELECT col1, col2 FROM t")
        assert result["ok"] is True
        assert result["row_count"] == 2
        assert result["columns"] == ["col1", "col2"]
        assert result["rows"] == [["a", 1], ["b", 2]]
        assert result["error"] is None

    def test_injects_top_default(self):
        mock_conn, mock_cursor = make_mock_conn(["n"], [[i] for i in range(100)])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            self.client.execute("SELECT n FROM t")
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TOP 100" in executed_sql.upper()

    def test_injects_custom_top(self):
        mock_conn, mock_cursor = make_mock_conn(["n"], [[1]])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            self.client.execute("SELECT n FROM t", inject_top=1000)
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TOP 1000" in executed_sql.upper()

    def test_no_injection_when_top_present(self):
        mock_conn, mock_cursor = make_mock_conn(["n"], [[1]])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            self.client.execute("SELECT TOP 5 n FROM t")
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert executed_sql.upper().count("TOP") == 1

    def test_no_injection_when_inject_top_none(self):
        mock_conn, mock_cursor = make_mock_conn(["n"], [[1]])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            self.client.execute("SELECT n FROM t", inject_top=None)
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TOP" not in executed_sql.upper()

    def test_no_injection_for_with_cte(self):
        """inject_top nie modyfikuje CTE — TOP trafiłby do anchora, nie do głównego SELECT."""
        mock_conn, mock_cursor = make_mock_conn(["id"], [[1]])
        sql = "WITH cte AS (SELECT id FROM t) SELECT * FROM cte"
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            self.client.execute(sql, inject_top=100)
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "TOP" not in executed_sql.upper()

    def test_truncated_true_when_row_count_equals_inject_top(self):
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(100)])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            result = self.client.execute("SELECT n FROM t", inject_top=100)
        assert result["truncated"] is True

    def test_truncated_false_when_fewer_rows(self):
        mock_conn, _ = make_mock_conn(["n"], [[i] for i in range(42)])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            result = self.client.execute("SELECT n FROM t", inject_top=100)
        assert result["truncated"] is False

    def test_truncated_false_when_inject_top_none(self):
        mock_conn, _ = make_mock_conn(["n"], [[1], [2]])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            result = self.client.execute("SELECT n FROM t", inject_top=None)
        assert result["truncated"] is False

    def test_validation_error(self):
        result = self.client.execute("DELETE FROM t")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"

    def test_sql_error(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.execute.side_effect = pyodbc.Error(
            "42S02", "[42S02] Invalid object name 'X'"
        )
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            result = self.client.execute("SELECT * FROM X")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_duration_ms_present(self):
        mock_conn, _ = make_mock_conn(["n"], [[1]])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            result = self.client.execute("SELECT n FROM t")
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0

    def test_result_json_serializable(self):
        from datetime import datetime
        from decimal import Decimal
        mock_conn, _ = make_mock_conn(["d", "v"], [[datetime(2024, 1, 1), Decimal("3.14")]])
        with patch.object(self.client, "get_connection", return_value=mock_conn):
            result = self.client.execute("SELECT d, v FROM t")
        json.dumps(result, default=str)


# ── TestSqlCredentials ────────────────────────────────────────────────────────


class TestSqlCredentials:
    def test_from_env_reads_sql_prefix(self, monkeypatch):
        monkeypatch.setenv("SQL_SERVER", "srv")
        monkeypatch.setenv("SQL_DATABASE", "db")
        monkeypatch.setenv("SQL_USERNAME", "usr")
        monkeypatch.setenv("SQL_PASSWORD", "pwd")
        creds = SqlCredentials.from_env("SQL_")
        assert creds.server == "srv"
        assert creds.database == "db"
        assert creds.username == "usr"
        assert creds.password == "pwd"

    def test_from_env_custom_prefix(self, monkeypatch):
        monkeypatch.setenv("BOT_SQL_SERVER", "bot_srv")
        monkeypatch.setenv("BOT_SQL_DATABASE", "bot_db")
        monkeypatch.setenv("BOT_SQL_USERNAME", "CEIM_AIBI")
        monkeypatch.setenv("BOT_SQL_PASSWORD", "bot_pwd")
        creds = SqlCredentials.from_env("BOT_SQL_")
        assert creds.server == "bot_srv"
        assert creds.username == "CEIM_AIBI"

    def test_frozen(self):
        creds = SqlCredentials(server="s", database="d", username="u", password="p")
        with pytest.raises(Exception):
            creds.server = "other"  # type: ignore[misc]


# ── TestSqlClientCredentials ──────────────────────────────────────────────────


class TestSqlClientCredentials:
    def test_explicit_credentials_stored(self):
        creds = SqlCredentials(server="s", database="d", username="u", password="p")
        client = SqlClient(credentials=creds)
        assert client.credentials.server == "s"
        assert client.credentials.username == "u"

    def test_default_credentials_from_sql_prefix(self, monkeypatch):
        monkeypatch.setenv("SQL_SERVER", "erp_srv")
        monkeypatch.setenv("SQL_DATABASE", "erp_db")
        monkeypatch.setenv("SQL_USERNAME", "erp_usr")
        monkeypatch.setenv("SQL_PASSWORD", "erp_pwd")
        client = SqlClient()
        assert client.credentials.server == "erp_srv"
        assert client.credentials.username == "erp_usr"


# ── TestFactories ─────────────────────────────────────────────────────────────


class TestFactories:
    def test_create_erp_sql_client(self, monkeypatch):
        monkeypatch.setenv("SQL_SERVER", "erp_srv")
        monkeypatch.setenv("SQL_DATABASE", "erp_db")
        monkeypatch.setenv("SQL_USERNAME", "erp_usr")
        monkeypatch.setenv("SQL_PASSWORD", "erp_pwd")
        client = create_erp_sql_client()
        assert client.credentials.username == "erp_usr"

    def test_create_bot_sql_client(self, monkeypatch):
        monkeypatch.setenv("SQL_SERVER", "srv")
        monkeypatch.setenv("SQL_DATABASE", "db")
        monkeypatch.setenv("BOT_SQL_USERNAME", "CEIM_AIBI")
        monkeypatch.setenv("BOT_SQL_PASSWORD", "bot_pwd")
        client = create_bot_sql_client()
        assert client.credentials.server == "srv"
        assert client.credentials.database == "db"
        assert client.credentials.username == "CEIM_AIBI"
