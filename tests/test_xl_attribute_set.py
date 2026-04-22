"""Testy dla tools/xl_attribute_set.py."""

from unittest.mock import MagicMock, call, patch

import pyodbc
import pytest

from tools.lib.sql_client import SqlClient
import tools.xl_attribute_set as xs


def _make_conn(proc_return_code: int, exists: bool = True) -> MagicMock:
    """exists=True → UPDATE path, exists=False → INSERT path."""
    cursor = MagicMock()
    exists_row = (1,) if exists else (0,)
    # fetchone: pierwsze wywołanie to check_exists, drugie to wynik procedury (tylko w UPDATE path)
    if exists:
        cursor.fetchone.side_effect = [exists_row, (proc_return_code,)]
    else:
        cursor.fetchone.side_effect = [exists_row]
        cursor.rowcount = 1  # INSERT OK
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestSetAttribute:
    def test_success_update_existing(self):
        conn = _make_conn(0, exists=True)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA PRODUKTU", "1.5", "FOTEL-01")
        assert result["ok"] is True
        assert result["error"] is None
        assert result["data"]["class"] == "WAGA PRODUKTU"
        assert result["data"]["action"] == "updated"

    def test_success_insert_new(self):
        conn = _make_conn(0, exists=False)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA PRODUKTU", "1.5", "FOTEL-01")
        assert result["ok"] is True
        assert result["data"]["action"] == "inserted"

    def test_success_commits_connection(self):
        conn = _make_conn(0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            xs.set_attribute("WAGA PRODUKTU", "1.5", "FOTEL-01")
        conn.commit.assert_called_once()

    def test_class_not_found(self):
        conn = _make_conn(-113)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("NIEISTNIEJACA_KLASA", "X", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "CLASS_NOT_FOUND"
        assert result["error"]["code"] == -113

    def test_object_not_found(self):
        conn = _make_conn(-112)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA PRODUKTU", "1.5", "KOD-NIEISTNIEJACY")
        assert result["ok"] is False
        assert result["error"]["type"] == "OBJECT_NOT_FOUND"

    def test_value_not_on_list(self):
        conn = _make_conn(-110)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("SEZON", "ZIMA_EXTRA", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALUE_NOT_ON_LIST"

    def test_unknown_return_code(self):
        conn = _make_conn(-999)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA PRODUKTU", "1.5", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "UNKNOWN_ERROR"
        assert "-999" in result["error"]["message"]

    def test_sql_exception_returns_error(self):
        conn = MagicMock()
        conn.cursor.return_value.execute.side_effect = pyodbc.Error(
            "08001", "connection failed"
        )
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA PRODUKTU", "1.5", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_kontrahent_type(self):
        conn = _make_conn(0, exists=True)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("STATUS CEIM", "VIP", "KOWALSKI", obj_type=32)
        assert result["ok"] is True
        assert result["data"]["type"] == 32

    def test_passes_operator_param(self):
        conn = _make_conn(0, exists=True)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            xs.set_attribute("WAGA PRODUKTU", "1.5", "FOTEL-01", operator="ADMIN")
        cursor = conn.cursor.return_value
        # Drugie wywołanie execute to procedura (pierwsze to check_exists)
        proc_call_params = cursor.execute.call_args_list[1][0][1]
        assert proc_call_params[4] == "ADMIN"

    def test_meta_contains_duration(self):
        conn = _make_conn(0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA PRODUKTU", "1.5", "FOTEL-01")
        assert "duration_ms" in result["meta"]
        assert isinstance(result["meta"]["duration_ms"], int)

    def test_insert_fail_returns_error(self):
        conn = _make_conn(0, exists=False)
        conn.cursor.return_value.rowcount = 0  # INSERT nie wstawił żadnego wiersza
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA PRODUKTU", "1.5", "KOD-BRAK")
        assert result["ok"] is False
        assert result["error"]["type"] == "OBJECT_NOT_FOUND"
