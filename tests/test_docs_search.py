"""Testy jednostkowe dla tools/search_docs.py. Używa in-memory SQLite."""

import sqlite3

import pytest

import tools.docs_search as sd
import tools.docs_build_index as bi
from tests.conftest import make_ws, TABELE_ROWS, KOLUMNY_ROWS, RELACJE_ROWS, SLOWNIK_ROWS, PRZYKLADOWE_ROWS


# ── Fixture ─────────────────────────────────────────────────────────────────


SAMPLE_GID_TYPES = [
    {"gid_type": 960,   "internal_name": "Typ_Zam",        "symbol": "Zam",   "description": "Zamówienie"},
    {"gid_type": 14346, "internal_name": "Typ_ProdZasoby", "symbol": "ZPZ",   "description": "Zasób procesu produkcyjnego"},
    {"gid_type": 2592,  "internal_name": "Typ_BkRez",      "symbol": "BkRez", "description": "Rezerwacja u dostawcy"},
]


@pytest.fixture
def docs_db(tmp_path):
    """Buduje docs.db w tmp_path z minimalnych danych testowych."""
    db_path = str(tmp_path / "docs.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    bi.build_schema(conn)
    tables = bi.parse_tables(make_ws(TABELE_ROWS))
    columns = bi.parse_columns(make_ws(KOLUMNY_ROWS))
    relations = bi.parse_relations(make_ws(RELACJE_ROWS))
    value_dicts = bi.parse_value_dicts(make_ws(SLOWNIK_ROWS))
    sample_values = bi.parse_sample_values(make_ws(PRZYKLADOWE_ROWS))
    bi.insert_data(conn, tables, columns, relations, value_dicts, sample_values,
                   gid_types=SAMPLE_GID_TYPES)
    conn.close()
    return db_path


# ── TestBuildFtsQuery ────────────────────────────────────────────────────────


class TestBuildFtsQuery:
    def test_single_word(self):
        assert sd.build_fts_query("kontrahent") == "kontrahent*"

    def test_multiple_words(self):
        assert sd.build_fts_query("kontrahent zamowienie") == "kontrahent* zamowienie*"

    def test_already_has_star(self):
        assert sd.build_fts_query("kontrah*") == "kontrah*"

    def test_strips_whitespace(self):
        assert sd.build_fts_query("  kontrahent  ") == "kontrahent*"


# ── TestSearchDocs ───────────────────────────────────────────────────────────


class TestSearchDocs:
    def test_returns_results(self, docs_db):
        result = sd.search_docs("kontrahent", db_path=docs_db)
        assert result["ok"] is True
        assert len(result["data"]["results"]) > 0

    def test_result_fields_present(self, docs_db):
        result = sd.search_docs("zamowien", db_path=docs_db)
        assert result["ok"] is True
        r = result["data"]["results"][0]
        for field in ("table_name", "col_name", "col_label", "data_type", "is_useful"):
            assert field in r

    def test_prefix_matching(self, docs_db):
        # "zamowien*" powinno trafić w "Nagłówki zamówień sprzedaży" (remove_diacritics)
        result = sd.search_docs("zamowien", db_path=docs_db)
        assert result["ok"] is True
        assert len(result["data"]["results"]) > 0

    def test_table_filter(self, docs_db):
        result = sd.search_docs("kontrahent", table_filter="CDN.KntKarty", db_path=docs_db)
        assert result["ok"] is True
        for r in result["data"]["results"]:
            assert r["table_name"] == "CDN.KntKarty"

    def test_empty_phrase_returns_empty(self, docs_db):
        result = sd.search_docs("", db_path=docs_db)
        assert result["ok"] is True
        assert result["data"]["results"] == []

    def test_no_results_returns_ok(self, docs_db):
        result = sd.search_docs("xyzabcnonexistent", db_path=docs_db)
        assert result["ok"] is True
        assert result["data"]["results"] == []

    def test_missing_db_returns_error(self, tmp_path):
        result = sd.search_docs("kontrahent", db_path=str(tmp_path / "nonexistent.db"))
        # get_db tworzy plik jeśli nie istnieje — ale pusta baza nie ma tabeli columns_fts
        # więc powinniśmy dostać QUERY_ERROR
        assert result["ok"] is False

    def test_truncated_flag(self, docs_db):
        result = sd.search_docs("a", limit=1, db_path=docs_db)
        # limit=1, jeśli jest więcej wyników → truncated=True
        if len(result["data"]["results"]) == 1:
            assert result["meta"]["truncated"] is True

    def test_gid_types_present_in_data(self, docs_db):
        result = sd.search_docs("zamowien", db_path=docs_db)
        assert "gid_types" in result["data"]

    def test_gid_types_search_by_symbol(self, docs_db):
        result = sd.search_docs("ZPZ", db_path=docs_db)
        assert result["ok"] is True
        gids = result["data"]["gid_types"]
        assert any(g["gid_type"] == 14346 for g in gids)

    def test_gid_types_search_by_number(self, docs_db):
        result = sd.search_docs("14346", db_path=docs_db)
        assert result["ok"] is True
        gids = result["data"]["gid_types"]
        assert any(g["gid_type"] == 14346 for g in gids)

    def test_gid_types_fields(self, docs_db):
        result = sd.search_docs("ZPZ", db_path=docs_db)
        gid = next(g for g in result["data"]["gid_types"] if g["gid_type"] == 14346)
        assert gid["internal_name"] == "Typ_ProdZasoby"
        assert gid["symbol"] == "ZPZ"
        assert "produkcyjnego" in gid["description"]

    def test_gid_types_empty_when_no_match(self, docs_db):
        result = sd.search_docs("xyznonexistent", db_path=docs_db)
        assert result["data"]["gid_types"] == []

    def test_gid_types_empty_phrase_returns_empty(self, docs_db):
        result = sd.search_docs("", db_path=docs_db)
        assert result["data"]["gid_types"] == []
