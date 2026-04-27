"""Testy dla tools/xl_attribute_set.py — SP-only: CDN.XLDodajAktualizujAtr."""

from unittest.mock import MagicMock, patch

import pytest

from tools.lib.sql_client import SqlClient
import tools.xl_attribute_set as xs


def _make_conn(sp_return: int = 0) -> MagicMock:
    cursor = MagicMock()
    cursor.fetchone.return_value = (sp_return,)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestSetAttributeSpPath:
    """Wszystkie typy obiektów → CDN.XLDodajAktualizujAtr SP."""

    def test_success_returns_ok(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["ok"] is True
        assert result["data"]["action"] == "upserted"

    def test_commits_connection(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        conn.commit.assert_called_once()

    def test_sp_error_maps_to_error_type(self):
        conn = _make_conn(sp_return=-113)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("BRAK_KLASY", "X", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "CLASS_NOT_FOUND"
        assert result["error"]["code"] == -113

    def test_unknown_sp_code_returns_unknown_error(self):
        conn = _make_conn(sp_return=-999)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "UNKNOWN_ERROR"
        assert "-999" in result["error"]["message"]

    def test_passes_operator_to_sp(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            xs.set_attribute("WAGA", "1.5", "FOTEL-01", operator="ADMIN")
        cursor = conn.cursor.return_value
        sp_params = cursor.execute.call_args_list[0][0][1]
        assert sp_params[4] == "ADMIN"

    def test_kontrahent_type(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("STATUS", "VIP", "KOWALSKI", obj_type=32)
        assert result["ok"] is True
        assert result["data"]["type"] == 32

    def test_srodek_trwaly_type(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("KATEGORIA", "X", "ST-001", obj_type=368)
        assert result["ok"] is True

    def test_sp_called_with_correct_params(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            xs.set_attribute("KOLOR", "CZERWONY", "FOTEL-01", obj_type=16, operator="AR")
        cursor = conn.cursor.return_value
        sp_params = cursor.execute.call_args_list[0][0][1]
        assert sp_params[0] == "KOLOR"
        assert sp_params[1] == "CZERWONY"
        assert sp_params[2] == "FOTEL-01"
        assert sp_params[3] == 16
        assert sp_params[4] == "AR"

    def test_dokument_type_numeric_akronim(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("OPIS", "test", "9999", obj_type=1617)
        assert result["ok"] is True

    def test_meta_contains_duration(self):
        conn = _make_conn(sp_return=0)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert "duration_ms" in result["meta"]
        assert isinstance(result["meta"]["duration_ms"], int)

    def test_product_not_found_sp_code(self):
        conn = _make_conn(sp_return=-107)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "KOD-BRAK")
        assert result["ok"] is False
        assert result["error"]["type"] == "PRODUCT_NOT_FOUND"

    def test_value_not_on_list_sp_code(self):
        conn = _make_conn(sp_return=-110)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("STATUS", "INVALID", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALUE_NOT_ON_LIST"


class TestSetAttributeErrors:
    def test_unsupported_type(self):
        result = xs.set_attribute("WAGA", "1.5", "X", obj_type=999)
        assert result["ok"] is False
        assert result["error"]["type"] == "UNSUPPORTED_TYPE"

    def test_dokument_non_numeric_akronim(self):
        result = xs.set_attribute("OPIS", "v", "NIENUM", obj_type=1617)
        assert result["ok"] is False
        assert result["error"]["type"] == "OBJECT_NOT_FOUND"

    def test_umowa_non_numeric_akronim(self):
        result = xs.set_attribute("OPIS", "v", "ABC", obj_type=4800)
        assert result["ok"] is False
        assert result["error"]["type"] == "OBJECT_NOT_FOUND"

    def test_sql_exception(self):
        conn = MagicMock()
        conn.cursor.side_effect = Exception("connection refused")
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_sp_returns_none_row(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        conn.cursor.return_value = cursor
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "UNKNOWN_ERROR"
