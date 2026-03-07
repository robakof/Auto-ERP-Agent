"""Testy jednostkowe dla tools/search_solutions.py. Używa tmp_path z przykładową strukturą."""

import pytest

import tools.solutions_search as ss


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture
def solutions_dir(tmp_path):
    """
    Tworzy minimalną strukturę solutions/:

    solutions/
    └── solutions in ERP windows/
        ├── Okno towary/
        │   └── Towary według EAN/
        │       ├── filtr.sql
        │       ├── columns/
        │       │   └── ean.sql
        │       └── filters/
        │           ├── archiwalny.sql
        │           └── kontrahent.sql
        └── Okno zamówień/
            └── Lista ZO/
                ├── filtr.sql
                └── filters/
                    └── status.sql
    """
    root = tmp_path / "solutions in ERP windows"

    # Okno towary / Towary według EAN
    ean_dir = root / "Okno towary" / "Towary według EAN"
    (ean_dir / "columns").mkdir(parents=True)
    (ean_dir / "filters").mkdir(parents=True)
    (ean_dir / "filtr.sql").write_text("(Twr_GIDNumer=3282)", encoding="utf-8")
    (ean_dir / "columns" / "ean.sql").write_text(
        "SELECT Twr_Ean [EAN] FROM cdn.TwrKarty WHERE {filtrsql}", encoding="utf-8"
    )
    (ean_dir / "filters" / "archiwalny.sql").write_text(
        "twr_archiwalny = 1", encoding="utf-8"
    )
    (ean_dir / "filters" / "kontrahent.sql").write_text(
        "Twr_GIDNumer IN (SELECT Knt_GIDNumer FROM cdn.KntKarty WHERE Knt_Nazwa1 LIKE '%ABC%')",
        encoding="utf-8",
    )

    # Okno zamówień / Lista ZO
    zo_dir = root / "Okno zamówień" / "Lista ZO"
    (zo_dir / "filters").mkdir(parents=True)
    (zo_dir / "filtr.sql").write_text("(ZaN_Typ=256)", encoding="utf-8")
    (zo_dir / "filters" / "status.sql").write_text(
        "ZaN_Status = 1", encoding="utf-8"
    )

    return tmp_path


# ── TestParsePath ────────────────────────────────────────────────────────────


class TestParsePath:
    def test_valid_path_columns(self, solutions_dir):
        from pathlib import Path
        sql_path = solutions_dir / "solutions in ERP windows" / "Okno towary" / "Towary według EAN" / "columns" / "ean.sql"
        result = ss._parse_path(sql_path, solutions_dir)
        assert result is not None
        assert result["window"] == "Okno towary"
        assert result["view"] == "Towary według EAN"
        assert result["type"] == "columns"
        assert result["name"] == "ean"

    def test_valid_path_filters(self, solutions_dir):
        from pathlib import Path
        sql_path = solutions_dir / "solutions in ERP windows" / "Okno towary" / "Towary według EAN" / "filters" / "archiwalny.sql"
        result = ss._parse_path(sql_path, solutions_dir)
        assert result["type"] == "filters"
        assert result["name"] == "archiwalny"

    def test_filtr_sql_excluded_by_name(self, solutions_dir):
        from pathlib import Path
        # filtr.sql jest pomijany w pętli głównej, nie przez _parse_path
        # _parse_path nie obsługuje filtr.sql — test weryfikuje że struktura ścieżki jest zła
        sql_path = solutions_dir / "solutions in ERP windows" / "Okno towary" / "Towary według EAN" / "filtr.sql"
        # ścieżka ma tylko 4 parts, nie 5 — zwraca None
        result = ss._parse_path(sql_path, solutions_dir)
        assert result is None


# ── TestSearchSolutions ──────────────────────────────────────────────────────


class TestSearchSolutions:
    def test_returns_all_without_phrase(self, solutions_dir):
        result = ss.search_solutions("", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        assert len(result["data"]["results"]) == 4  # ean, archiwalny, kontrahent, status

    def test_search_by_filename(self, solutions_dir):
        result = ss.search_solutions("archiwalny", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        names = [r["name"] for r in result["data"]["results"]]
        assert "archiwalny" in names

    def test_search_by_sql_content(self, solutions_dir):
        result = ss.search_solutions("KntKarty", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        names = [r["name"] for r in result["data"]["results"]]
        assert "kontrahent" in names

    def test_search_by_window_name(self, solutions_dir):
        result = ss.search_solutions("zamówień", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        windows = {r["window"] for r in result["data"]["results"]}
        assert "Okno zamówień" in windows

    def test_window_filter(self, solutions_dir):
        result = ss.search_solutions("", window_filter="towary", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        for r in result["data"]["results"]:
            assert "towary" in r["window"].lower()

    def test_type_filter_columns(self, solutions_dir):
        result = ss.search_solutions("", type_filter="columns", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        for r in result["data"]["results"]:
            assert r["type"] == "columns"

    def test_type_filter_filters(self, solutions_dir):
        result = ss.search_solutions("", type_filter="filters", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        for r in result["data"]["results"]:
            assert r["type"] == "filters"

    def test_filtr_sql_included(self, solutions_dir):
        result = ss.search_solutions("archiwalny", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        r = result["data"]["results"][0]
        assert r["filtr_sql"] == "(Twr_GIDNumer=3282)"

    def test_path_uses_forward_slashes(self, solutions_dir):
        result = ss.search_solutions("ean", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        r = result["data"]["results"][0]
        assert "\\" not in r["path"]

    def test_no_results_returns_ok(self, solutions_dir):
        result = ss.search_solutions("xyznonexistentabc", solutions_path=str(solutions_dir))
        assert result["ok"] is True
        assert result["data"]["results"] == []

    def test_missing_solutions_dir_returns_error(self, tmp_path):
        result = ss.search_solutions("test", solutions_path=str(tmp_path / "nonexistent"))
        assert result["ok"] is False
        assert result["error"]["type"] == "NOT_FOUND"

    def test_limit_respected(self, solutions_dir):
        result = ss.search_solutions("", limit=2, solutions_path=str(solutions_dir))
        assert result["ok"] is True
        assert len(result["data"]["results"]) == 2
        assert result["meta"]["truncated"] is True
