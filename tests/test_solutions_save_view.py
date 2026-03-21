"""Testy dla tools/solutions_save_view.py."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import tools.solutions_save_view as sv


class TestSaveView:
    def test_happy_path_creates_view_file(self, tmp_path):
        draft = tmp_path / "Rezerwacje_draft.sql"
        draft.write_text("SELECT * FROM CDN.Rezerwacje", encoding="utf-8")
        views_dir = tmp_path / "views"

        with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
            result = sv.save_view(draft_path=draft, view_name="Rezerwacje")

        assert result["ok"] is True
        view_file = views_dir / "Rezerwacje.sql"
        assert view_file.exists()
        content = view_file.read_text(encoding="utf-8")
        assert "CREATE OR ALTER VIEW AIBI.Rezerwacje AS" in content
        assert "SELECT * FROM CDN.Rezerwacje" in content

    def test_strips_top_n_from_draft(self, tmp_path):
        draft = tmp_path / "Test_draft.sql"
        draft.write_text("SELECT TOP 100000 * FROM CDN.Test", encoding="utf-8")
        views_dir = tmp_path / "views"

        with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
            sv.save_view(draft_path=draft, view_name="Test")

        content = (views_dir / "Test.sql").read_text(encoding="utf-8")
        assert "TOP" not in content
        assert "SELECT  * FROM CDN.Test" in content or "SELECT * FROM CDN.Test" in content

    def test_view_name_derived_from_filename(self, tmp_path):
        draft = tmp_path / "Zamowienia_draft.sql"
        draft.write_text("SELECT 1", encoding="utf-8")
        views_dir = tmp_path / "views"

        with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
            result = sv.save_view(draft_path=draft)

        assert result["ok"] is True
        assert (views_dir / "Zamowienia.sql").exists()
        assert result["data"]["view_name"] == "Zamowienia"

    def test_custom_schema(self, tmp_path):
        draft = tmp_path / "Raport.sql"
        draft.write_text("SELECT 1", encoding="utf-8")
        views_dir = tmp_path / "views"

        with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
            result = sv.save_view(draft_path=draft, view_name="Raport", schema="DWH")

        content = (views_dir / "Raport.sql").read_text(encoding="utf-8")
        assert "CREATE OR ALTER VIEW DWH.Raport AS" in content

    def test_overwrites_existing_file(self, tmp_path):
        draft = tmp_path / "Widok.sql"
        draft.write_text("SELECT 2", encoding="utf-8")
        views_dir = tmp_path / "views"
        views_dir.mkdir()
        (views_dir / "Widok.sql").write_text("stara treść", encoding="utf-8")

        with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
            result = sv.save_view(draft_path=draft, view_name="Widok")

        assert result["ok"] is True
        content = (views_dir / "Widok.sql").read_text(encoding="utf-8")
        assert "SELECT 2" in content
        assert "stara treść" not in content

    def test_draft_not_found_returns_error(self, tmp_path):
        result = sv.save_view(draft_path=tmp_path / "brak.sql", view_name="Test")
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_result_contains_path(self, tmp_path):
        draft = tmp_path / "Widok.sql"
        draft.write_text("SELECT 1", encoding="utf-8")
        views_dir = tmp_path / "views"

        with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
            result = sv.save_view(draft_path=draft, view_name="Widok")

        assert "path" in result["data"]
        assert result["data"]["path"].endswith("Widok.sql")


class TestMain:
    def test_valid_call_prints_json(self, tmp_path, capsys):
        draft = tmp_path / "Test_draft.sql"
        draft.write_text("SELECT 1", encoding="utf-8")
        views_dir = tmp_path / "views"

        with patch("sys.argv", ["solutions_save_view.py", "--draft", str(draft), "--view-name", "Test"]):
            with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
                sv.main()

        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True

    def test_view_name_optional_in_cli(self, tmp_path, capsys):
        draft = tmp_path / "Faktury_draft.sql"
        draft.write_text("SELECT 1", encoding="utf-8")
        views_dir = tmp_path / "views"

        with patch("sys.argv", ["solutions_save_view.py", "--draft", str(draft)]):
            with patch("tools.solutions_save_view.VIEWS_DIR", views_dir):
                sv.main()

        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["view_name"] == "Faktury"

    def test_missing_draft_returns_error(self, tmp_path, capsys):
        with patch("sys.argv", ["solutions_save_view.py", "--draft", str(tmp_path / "brak.sql")]):
            sv.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"
