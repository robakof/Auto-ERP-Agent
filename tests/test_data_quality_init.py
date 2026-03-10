"""Testy dla tools/data_quality_init.py."""

import json
import sqlite3
from unittest.mock import patch

import pytest

from tools.lib.sql_client import SqlClient
import tools.data_quality_init as dqi


def _mock_sql_result(columns, rows):
    return {
        "ok": True,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": False,
        "duration_ms": 5,
        "error": None,
    }


def _mock_sql_error(msg="connection failed"):
    return {
        "ok": False,
        "columns": [],
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "duration_ms": 0,
        "error": {"type": "SQL_ERROR", "message": msg},
    }


class TestInitWorkdb:
    def test_happy_path_creates_db(self, tmp_path):
        db_path = tmp_path / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(
            ["Kod", "Nazwa"], [["ABC", "Firma ABC"], ["XYZ", "Firma XYZ"]]
        )):
            result = dqi.init_workdb("BI.KntKarty", db_path)
        assert result["ok"] is True
        assert db_path.exists()

    def test_happy_path_creates_dane_table(self, tmp_path):
        db_path = tmp_path / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(
            ["Kod", "Nazwa"], [["ABC", "Firma ABC"]]
        )):
            dqi.init_workdb("BI.KntKarty", db_path)
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT Kod, Nazwa FROM dane").fetchall()
        conn.close()
        assert rows == [("ABC", "Firma ABC")]

    def test_happy_path_creates_findings_and_records_tables(self, tmp_path):
        db_path = tmp_path / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(["col"], [[1]])):
            dqi.init_workdb("BI.KntKarty", db_path)
        conn = sqlite3.connect(db_path)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert "findings" in tables
        assert "records" in tables

    def test_returns_row_count(self, tmp_path):
        db_path = tmp_path / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(
            ["n"], [[1], [2], [3]]
        )):
            result = dqi.init_workdb("BI.KntKarty", db_path)
        assert result["data"]["row_count"] == 3

    def test_returns_columns(self, tmp_path):
        db_path = tmp_path / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(
            ["Kod", "Nazwa", "NIP"], [["A", "B", "C"]]
        )):
            result = dqi.init_workdb("BI.KntKarty", db_path)
        assert result["data"]["columns"] == ["Kod", "Nazwa", "NIP"]

    def test_file_exists_without_force_returns_error(self, tmp_path):
        db_path = tmp_path / "test.db"
        db_path.touch()
        result = dqi.init_workdb("BI.KntKarty", db_path, force=False)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_EXISTS"

    def test_file_exists_with_force_overwrites(self, tmp_path):
        db_path = tmp_path / "test.db"
        db_path.touch()
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(["n"], [[1]])):
            result = dqi.init_workdb("BI.KntKarty", db_path, force=True)
        assert result["ok"] is True

    def test_sql_error_returns_error(self, tmp_path):
        db_path = tmp_path / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_error("Invalid object")):
            result = dqi.init_workdb("BI.Brak", db_path)
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"
        assert not db_path.exists()

    def test_creates_parent_directory(self, tmp_path):
        db_path = tmp_path / "subdir" / "nested" / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(["n"], [[1]])):
            result = dqi.init_workdb("BI.KntKarty", db_path)
        assert result["ok"] is True
        assert db_path.exists()

    def test_type_conversion_decimal(self, tmp_path):
        from decimal import Decimal
        db_path = tmp_path / "test.db"
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(
            ["val"], [[Decimal("3.14")]]
        )):
            dqi.init_workdb("BI.X", db_path)
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT val FROM dane").fetchone()
        conn.close()
        assert float(row[0]) == pytest.approx(3.14)

    def test_type_conversion_datetime(self, tmp_path):
        from datetime import datetime
        db_path = tmp_path / "test.db"
        dt = datetime(2024, 3, 15, 10, 30)
        with patch.object(SqlClient, "execute", return_value=_mock_sql_result(
            ["dt"], [[dt]]
        )):
            dqi.init_workdb("BI.X", db_path)
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT dt FROM dane").fetchone()
        conn.close()
        assert "2024-03-15" in row[0]


class TestMain:
    def test_happy_path_prints_json(self, tmp_path, capsys):
        db_path = tmp_path / "test.db"
        with patch("sys.argv", ["dqi.py", "--source", "BI.KntKarty", "--output", str(db_path)]):
            with patch.object(SqlClient, "execute", return_value=_mock_sql_result(["n"], [[1]])):
                dqi.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True

    def test_file_exists_without_force_prints_error(self, tmp_path, capsys):
        db_path = tmp_path / "test.db"
        db_path.touch()
        with patch("sys.argv", ["dqi.py", "--source", "BI.KntKarty", "--output", str(db_path)]):
            dqi.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_EXISTS"

    def test_force_flag_overwrites(self, tmp_path, capsys):
        db_path = tmp_path / "test.db"
        db_path.touch()
        with patch("sys.argv", ["dqi.py", "--source", "BI.X", "--output", str(db_path), "--force"]):
            with patch.object(SqlClient, "execute", return_value=_mock_sql_result(["n"], [[1]])):
                dqi.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
