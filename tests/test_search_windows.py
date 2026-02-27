"""Testy jednostkowe dla tools/search_windows.py."""

import json

import pytest

import tools.search_windows as sw

SAMPLE_WINDOWS = [
    {
        "id": "okno_towary_ean",
        "name": "Towary według EAN",
        "aliases": ["okno towarów", "lista EAN"],
        "primary_table": "CDN.TwrKarty",
        "config_types": ["columns", "filters"],
    },
    {
        "id": "lista_zamowien_sprzedazy",
        "name": "Lista zamówień sprzedaży",
        "aliases": ["okno zamówień", "lista ZO"],
        "primary_table": "CDN.ZamNag",
        "config_types": ["columns", "filters"],
    },
    {
        "id": "kartoteka_kontrahenta",
        "name": "Kartoteka kontrahenta",
        "aliases": ["CRM", "kontrahenci"],
        "primary_table": "CDN.KntKarty",
        "config_types": ["columns"],
    },
]


@pytest.fixture
def windows_dir(tmp_path):
    """Tworzy solutions/ z erp_windows.json."""
    (tmp_path / "erp_windows.json").write_text(
        json.dumps(SAMPLE_WINDOWS), encoding="utf-8"
    )
    return tmp_path


class TestSearchWindows:
    def test_match_by_name(self, windows_dir):
        result = sw.search_windows("EAN", solutions_path=str(windows_dir))
        assert result["ok"] is True
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["id"] == "okno_towary_ean"

    def test_match_by_alias(self, windows_dir):
        result = sw.search_windows("lista ZO", solutions_path=str(windows_dir))
        assert result["ok"] is True
        assert result["data"]["results"][0]["id"] == "lista_zamowien_sprzedazy"

    def test_case_insensitive(self, windows_dir):
        result = sw.search_windows("ean", solutions_path=str(windows_dir))
        assert result["ok"] is True
        assert len(result["data"]["results"]) == 1

    def test_no_phrase_returns_all(self, windows_dir):
        result = sw.search_windows("", solutions_path=str(windows_dir))
        assert result["ok"] is True
        assert len(result["data"]["results"]) == 3

    def test_type_filter(self, windows_dir):
        # kartoteka_kontrahenta ma tylko "columns" — powinna być wykluczona dla "filters"
        result = sw.search_windows("", type_filter="filters", solutions_path=str(windows_dir))
        assert result["ok"] is True
        ids = [r["id"] for r in result["data"]["results"]]
        assert "kartoteka_kontrahenta" not in ids
        assert "okno_towary_ean" in ids

    def test_no_match_returns_empty(self, windows_dir):
        result = sw.search_windows("xyznonexistent", solutions_path=str(windows_dir))
        assert result["ok"] is True
        assert result["data"]["results"] == []

    def test_missing_file_returns_empty(self, tmp_path):
        result = sw.search_windows("ean", solutions_path=str(tmp_path))
        assert result["ok"] is True
        assert result["data"]["results"] == []

    def test_invalid_json_returns_error(self, tmp_path):
        (tmp_path / "erp_windows.json").write_text("not valid json", encoding="utf-8")
        result = sw.search_windows("ean", solutions_path=str(tmp_path))
        assert result["ok"] is False
        assert result["error"]["type"] == "PARSE_ERROR"

    def test_result_fields_present(self, windows_dir):
        result = sw.search_windows("EAN", solutions_path=str(windows_dir))
        r = result["data"]["results"][0]
        for field in ("id", "name", "aliases", "primary_table", "config_types"):
            assert field in r
