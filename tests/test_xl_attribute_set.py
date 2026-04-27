"""Testy dla tools/xl_attribute_set.py — migracja na XL API (XlClient)."""

from unittest.mock import MagicMock, call, patch

import pytest

from tools.lib.sql_client import SqlClient
from tools.lib.xl_client import XlClient
import tools.xl_attribute_set as xs


# --- helpers ---

def _make_sql_conn(row=None) -> MagicMock:
    """row = (gid_typ, gid_numer, gid_firma) lub None (nie znaleziono)."""
    cursor = MagicMock()
    cursor.fetchone.return_value = row
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


def _xl_ok() -> dict:
    return {"ok": True, "data": {"Wersja": 20251}}


def _xl_fail(msg: str = "błąd API") -> dict:
    return {"ok": False, "error": {"type": "ATRYBUT_FAIL", "message": msg}}


GID_TOWAR = (16, 100, 1)
GID_KNT   = (32, 200, 1)
GID_SRT   = (368, 300, 1)


# --- testy głównej ścieżki ---

class TestSetAttributeHappyPath:
    def test_success_returns_ok(self):
        conn = _make_sql_conn(GID_TOWAR)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()) as mock_api:
                result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["ok"] is True
        assert result["error"] is None

    def test_success_data_fields(self):
        conn = _make_sql_conn(GID_TOWAR)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()):
                result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["data"]["class"] == "WAGA"
        assert result["data"]["value"] == "1.5"
        assert result["data"]["akronim"] == "FOTEL-01"
        assert result["data"]["type"] == 16
        assert result["data"]["action"] == "set"

    def test_success_meta_contains_duration(self):
        conn = _make_sql_conn(GID_TOWAR)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()):
                result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert "duration_ms" in result["meta"]
        assert isinstance(result["meta"]["duration_ms"], int)

    def test_passes_gid_to_api(self):
        conn = _make_sql_conn(GID_TOWAR)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()) as mock_api:
                xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        mock_api.assert_called_once_with(16, 100, 1, "WAGA", "1.5")

    def test_kontrahent_type(self):
        conn = _make_sql_conn(GID_KNT)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()) as mock_api:
                result = xs.set_attribute("STATUS", "VIP", "KOWALSKI", obj_type=32)
        assert result["ok"] is True
        mock_api.assert_called_once_with(32, 200, 1, "STATUS", "VIP")

    def test_srodek_trwaly_type(self):
        conn = _make_sql_conn(GID_SRT)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()) as mock_api:
                result = xs.set_attribute("KATEGORIA", "A", "SRT-01", obj_type=368)
        assert result["ok"] is True
        mock_api.assert_called_once_with(368, 300, 1, "KATEGORIA", "A")

    def test_dokument_type_uses_akronim_as_numer(self):
        with patch.object(SqlClient, "get_connection"):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()) as mock_api:
                result = xs.set_attribute("OPIS", "test", "9999", obj_type=1617)
        assert result["ok"] is True
        mock_api.assert_called_once_with(1617, 9999, 0, "OPIS", "test")

    def test_operator_param_accepted_for_compat(self):
        conn = _make_sql_conn(GID_TOWAR)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_ok()):
                result = xs.set_attribute("WAGA", "1.5", "FOTEL-01", operator="ADMIN")
        assert result["ok"] is True


# --- testy błędów SQL/GID lookup ---

class TestSetAttributeLookupErrors:
    def test_object_not_found_when_sql_returns_none(self):
        conn = _make_sql_conn(None)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "KOD-BRAK")
        assert result["ok"] is False
        assert result["error"]["type"] == "OBJECT_NOT_FOUND"

    def test_sql_exception_returns_sql_error(self):
        conn = MagicMock()
        conn.cursor.side_effect = Exception("connection refused")
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_unsupported_type(self):
        result = xs.set_attribute("WAGA", "1.5", "X", obj_type=999)
        assert result["ok"] is False
        assert result["error"]["type"] == "UNSUPPORTED_TYPE"

    def test_dokument_non_numeric_akronim(self):
        with patch.object(SqlClient, "get_connection"):
            result = xs.set_attribute("OPIS", "v", "NIENUM", obj_type=1617)
        assert result["ok"] is False
        assert result["error"]["type"] == "OBJECT_NOT_FOUND"


# --- testy błędów z XL API ---

class TestSetAttributeApiErrors:
    def test_api_fail_returns_atrybut_fail(self):
        conn = _make_sql_conn(GID_TOWAR)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", return_value=_xl_fail("klasa nie istnieje")):
                result = xs.set_attribute("NIEISTNIEJACA", "X", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "ATRYBUT_FAIL"
        assert "klasa nie istnieje" in result["error"]["message"]

    def test_api_exception_returns_api_error(self):
        conn = _make_sql_conn(GID_TOWAR)
        with patch.object(SqlClient, "get_connection", return_value=conn):
            with patch.object(XlClient, "dodaj_atrybut", side_effect=Exception("proxy crash")):
                result = xs.set_attribute("WAGA", "1.5", "FOTEL-01")
        assert result["ok"] is False
        assert result["error"]["type"] == "API_ERROR"
