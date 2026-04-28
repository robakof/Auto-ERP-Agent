"""Testy dla tools/xl_attribute_set.py — XL API: XLDodajAtrybut (INSERT-only)."""

from unittest.mock import MagicMock, patch, call

import pytest

from tools.lib.sql_client import SqlClient
from tools.lib.xl_client import XlClient
import tools.xl_attribute_set as xs

_GID = (1590, 1464833, 16)
_XL_OK = {"ok": True, "data": {"Klasa": "KOLOR", "Wartosc": "Czerwony"}}
_XL_FAIL = {"ok": False, "error": {"type": "XL_ERROR", "message": "fail"}}


def _make_conn(gid=_GID, exists=False):
    cursor = MagicMock()
    cursor.fetchone.side_effect = [gid, (1 if exists else 0,)]
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestSetAttributeInsert:
    def test_new_attribute_returns_inserted(self):
        conn = _make_conn(exists=False)
        with patch.object(SqlClient, "get_connection", return_value=conn), \
             patch.object(XlClient, "dodaj_atrybut", return_value=_XL_OK):
            result = xs.set_attribute("KOLOR", "Czerwony", "FOTEL-01")
        assert result["ok"] is True
        assert result["data"]["action"] == "inserted"

    def test_existing_attribute_returns_skipped(self):
        conn = _make_conn(exists=True)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("KOLOR", "Czerwony", "FOTEL-01")
        assert result["ok"] is True
        assert result["data"]["action"] == "skipped"

    def test_xl_api_not_called_when_skipped(self):
        conn = _make_conn(exists=True)
        with patch.object(SqlClient, "get_connection", return_value=conn), \
             patch.object(XlClient, "dodaj_atrybut") as mock_xl:
            xs.set_attribute("KOLOR", "Czerwony", "FOTEL-01")
        mock_xl.assert_not_called()

    def test_xl_api_called_with_correct_gid(self):
        conn = _make_conn(gid=(999, 111, 16), exists=False)
        with patch.object(SqlClient, "get_connection", return_value=conn), \
             patch.object(XlClient, "dodaj_atrybut", return_value=_XL_OK) as mock_xl:
            xs.set_attribute("KOLOR", "Czerwony", "FOTEL-01")
        mock_xl.assert_called_once_with(
            gid_typ=16, gid_numer=999, gid_firma=111,
            klasa="KOLOR", wartosc="Czerwony",
        )

    def test_xl_api_error_returns_error(self):
        conn = _make_conn(exists=False)
        with patch.object(SqlClient, "get_connection", return_value=conn), \
             patch.object(XlClient, "dodaj_atrybut", return_value=_XL_FAIL):
            result = xs.set_attribute("KOLOR", "Czerwony", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_ERROR"

    def test_meta_contains_duration(self):
        conn = _make_conn(exists=False)
        with patch.object(SqlClient, "get_connection", return_value=conn), \
             patch.object(XlClient, "dodaj_atrybut", return_value=_XL_OK):
            result = xs.set_attribute("KOLOR", "Czerwony", "FOTEL-01")
        assert "duration_ms" in result["meta"]
        assert isinstance(result["meta"]["duration_ms"], int)


class TestSetAttributeErrors:
    def test_unsupported_type_returns_error(self):
        result = xs.set_attribute("WAGA", "1.5", "X", obj_type=32)
        assert result["ok"] is False
        assert result["error"]["type"] == "UNSUPPORTED_TYPE"

    def test_object_not_found_when_no_gid(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        conn = MagicMock()
        conn.cursor.return_value = cursor
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("KOLOR", "X", "BRAK-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "OBJECT_NOT_FOUND"

    def test_sql_exception_returns_sql_error(self):
        conn = MagicMock()
        conn.cursor.side_effect = Exception("connection refused")
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("KOLOR", "X", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_xl_api_exception_returns_xl_api_error(self):
        conn = _make_conn(exists=False)
        with patch.object(SqlClient, "get_connection", return_value=conn), \
             patch.object(XlClient, "dodaj_atrybut", side_effect=Exception("proxy down")):
            result = xs.set_attribute("KOLOR", "X", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "XL_API_ERROR"
