"""Testy dla tools/bi_verify.py."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from tests.conftest import make_mock_conn
from tools.lib.sql_client import SqlClient
import tools.bi_verify as bv


def _make_stats_result(row_count=10, columns=None):
    cols = columns or ["Typ", "Data"]
    return {
        "ok": True,
        "data": {
            "sheet": "Wynik",
            "row_count": row_count,
            "columns": [
                {"name": c, "total": row_count, "distinct": 2, "null_count": 0, "values": ["A", "B"]}
                for c in cols
            ],
        },
        "error": None,
    }


class TestVerify:
    def test_happy_path_returns_compact_report(self, tmp_path):
        draft = tmp_path / "Widok_draft.sql"
        draft.write_text("SELECT Typ FROM CDN.T", encoding="utf-8")
        export_path = tmp_path / "Widok_verify.xlsx"

        mock_conn, _ = make_mock_conn(["Typ"], [["ZS"], ["ZZ"]])
        stats = _make_stats_result(2, ["Typ"])

        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            with patch("tools.bi_verify.read_stats", return_value=stats):
                result = bv.verify(
                    draft_path=draft,
                    view_name="Widok",
                    export_path=export_path,
                )

        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert result["data"]["column_count"] == 1
        assert "stats" in result["data"]
        assert export_path.exists()

    def test_validation_error_returns_error_immediately(self, tmp_path):
        draft = tmp_path / "bad.sql"
        draft.write_text("DELETE FROM t", encoding="utf-8")

        result = bv.verify(draft_path=draft, view_name="Bad", export_path=tmp_path / "out.xlsx")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"

    def test_sql_error_returns_error(self, tmp_path):
        import pyodbc
        draft = tmp_path / "err.sql"
        draft.write_text("SELECT * FROM CDN.BrakTabeli", encoding="utf-8")

        mock_conn = make_mock_conn([], [])[0]
        mock_conn.cursor.return_value.execute.side_effect = pyodbc.Error(
            "42S02", "[42S02] Invalid object name"
        )
        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = bv.verify(draft_path=draft, view_name="Test", export_path=tmp_path / "out.xlsx")

        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_draft_not_found_returns_error(self, tmp_path):
        result = bv.verify(
            draft_path=tmp_path / "brak.sql",
            view_name="Test",
            export_path=tmp_path / "out.xlsx",
        )
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_stats_columns_present(self, tmp_path):
        draft = tmp_path / "W.sql"
        draft.write_text("SELECT Typ, Data FROM CDN.T", encoding="utf-8")
        export_path = tmp_path / "W_verify.xlsx"

        mock_conn, _ = make_mock_conn(["Typ", "Data"], [["ZS", "2024-01-01"]])
        stats = _make_stats_result(1, ["Typ", "Data"])

        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            with patch("tools.bi_verify.read_stats", return_value=stats):
                result = bv.verify(draft_path=draft, view_name="W", export_path=export_path)

        assert result["data"]["column_count"] == 2
        stat_names = [s["name"] for s in result["data"]["stats"]]
        assert "Typ" in stat_names
        assert "Data" in stat_names


class TestStableExport:
    def test_copies_to_stable_path_when_solutions_dir_exists(self, tmp_path):
        solutions_dir = tmp_path / "solutions" / "bi" / "TestWidok"
        solutions_dir.mkdir(parents=True)
        draft = tmp_path / "draft.sql"
        draft.write_text("SELECT n FROM t", encoding="utf-8")
        export_path = tmp_path / "out.xlsx"

        mock_conn, _ = make_mock_conn(["n"], [[1]])
        stats = _make_stats_result(1, ["n"])

        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            with patch("tools.bi_verify.read_stats", return_value=stats):
                with patch("tools.bi_verify.SOLUTIONS_BI_DIR", tmp_path / "solutions" / "bi"):
                    result = bv.verify(draft_path=draft, view_name="TestWidok", export_path=export_path)

        assert result["ok"] is True
        stable = solutions_dir / "TestWidok_export.xlsx"
        assert stable.exists()
        assert "stable_export_path" in result["data"]

    def test_no_stable_copy_when_solutions_dir_missing(self, tmp_path):
        draft = tmp_path / "draft.sql"
        draft.write_text("SELECT n FROM t", encoding="utf-8")
        export_path = tmp_path / "out.xlsx"

        mock_conn, _ = make_mock_conn(["n"], [[1]])
        stats = _make_stats_result(1, ["n"])

        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            with patch("tools.bi_verify.read_stats", return_value=stats):
                with patch("tools.bi_verify.SOLUTIONS_BI_DIR", tmp_path / "solutions" / "bi"):
                    result = bv.verify(draft_path=draft, view_name="Nieistniejacy", export_path=export_path)

        assert result["ok"] is True
        assert "stable_export_path" not in result["data"]


class TestMain:
    def test_valid_call_prints_json(self, tmp_path, capsys):
        draft = tmp_path / "W_draft.sql"
        draft.write_text("SELECT n FROM t", encoding="utf-8")
        export_path = tmp_path / "W_verify.xlsx"

        mock_conn, _ = make_mock_conn(["n"], [[1]])
        stats = _make_stats_result(1, ["n"])

        with patch("sys.argv", [
            "bi_verify.py", "--draft", str(draft),
            "--view-name", "W", "--export", str(export_path)
        ]):
            with patch.object(SqlClient, "get_connection", return_value=mock_conn):
                with patch("tools.bi_verify.read_stats", return_value=stats):
                    bv.main()

        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True

    def test_missing_draft_returns_error(self, tmp_path, capsys):
        with patch("sys.argv", [
            "bi_verify.py", "--draft", str(tmp_path / "brak.sql"), "--view-name", "W"
        ]):
            bv.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"
