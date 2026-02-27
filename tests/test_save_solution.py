"""Testy jednostkowe dla tools/save_solution.py."""

import pytest

import tools.save_solution as ss


@pytest.fixture
def sol_base(tmp_path):
    """Pusty katalog solutions/ jako baza testowa."""
    base = tmp_path / "solutions"
    base.mkdir()
    return base


class TestSaveSolution:
    def test_creates_file(self, sol_base):
        result = ss.save_solution(
            window="Okno towary",
            view="Towary według EAN",
            sol_type="filters",
            name="brak jpg",
            sql="Twr_GIDNumer NOT IN (SELECT 1)",
            solutions_path=str(sol_base),
        )
        assert result["ok"] is True
        target = (
            sol_base / "solutions in ERP windows"
            / "Okno towary" / "Towary według EAN"
            / "filters" / "brak jpg.sql"
        )
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "Twr_GIDNumer NOT IN (SELECT 1)"

    def test_creates_missing_directories(self, sol_base):
        result = ss.save_solution(
            window="Nowe okno",
            view="Nowy widok",
            sol_type="columns",
            name="kolumna",
            sql="SELECT 1 [X] FROM cdn.T WHERE {filtrsql}",
            solutions_path=str(sol_base),
        )
        assert result["ok"] is True
        target = (
            sol_base / "solutions in ERP windows"
            / "Nowe okno" / "Nowy widok" / "columns" / "kolumna.sql"
        )
        assert target.exists()

    def test_returns_relative_path(self, sol_base):
        result = ss.save_solution(
            window="Okno towary",
            view="Towary według EAN",
            sol_type="filters",
            name="test",
            sql="1=1",
            solutions_path=str(sol_base),
        )
        assert result["ok"] is True
        assert "solutions in ERP windows" in result["data"]["path"]
        assert "\\" not in result["data"]["path"]

    def test_file_exists_without_force(self, sol_base):
        ss.save_solution(
            window="Okno", view="Widok", sol_type="filters",
            name="test", sql="1=1", solutions_path=str(sol_base),
        )
        result = ss.save_solution(
            window="Okno", view="Widok", sol_type="filters",
            name="test", sql="2=2", solutions_path=str(sol_base),
        )
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_EXISTS"

    def test_file_exists_with_force_overwrites(self, sol_base):
        ss.save_solution(
            window="Okno", view="Widok", sol_type="filters",
            name="test", sql="1=1", solutions_path=str(sol_base),
        )
        result = ss.save_solution(
            window="Okno", view="Widok", sol_type="filters",
            name="test", sql="2=2", force=True, solutions_path=str(sol_base),
        )
        assert result["ok"] is True
        target = (
            sol_base / "solutions in ERP windows"
            / "Okno" / "Widok" / "filters" / "test.sql"
        )
        assert target.read_text(encoding="utf-8") == "2=2"
