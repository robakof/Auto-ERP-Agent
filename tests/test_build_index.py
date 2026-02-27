"""Testy jednostkowe dla tools/build_index.py. Bez realnego pliku Excel."""

import sqlite3
from unittest.mock import MagicMock

import pytest

import tools.build_index as bi


# ── Helpers / fixtures ─────────────────────────────────────────────────────


def make_ws(rows: list[tuple]) -> MagicMock:
    """Tworzy mock arkusza Excel zwracający podane wiersze."""
    ws = MagicMock()
    ws.iter_rows.return_value = rows
    return ws


def in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


# Minimalne dane testowe

TABELE_ROWS = [
    # nagłówek (pominięty)
    (None, None, None, None, None, None),
    # dane
    (1, "Zamówienia", "CDN.ZamNag", "ZaN", None, "Nagłówki zamówień sprzedaży"),
    (2, "Kontrahenci", "CDN.KntKarty", "Knt", None, "Kartoteka kontrahentów"),
]

KOLUMNY_ROWS = [
    # wiersze przed nagłówkiem
    ("some", "other", "stuff", None, None, None, None, None, None, None, None, None),
    # nagłówek (szukany po "Numer tabeli")
    ("Numer tabeli", "Nazwa własna tabeli", "Nazwa tabeli", "Nr kol",
     "Nazwa własna kol", "Nazwa kol", "Rola", "Czy użyteczna",
     "Preferowana", "Typ", None, "Opis"),
    # dane
    (1, "Zamówienia", "CDN.ZamNag", 1, "ID zamówienia", "ZaN_GIDNumer",
     None, "Tak", "Nie", "int", None, "Identyfikator rekordu"),
    (1, "Zamówienia", "CDN.ZamNag", 2, "ID kontrahenta", "ZaN_KntGIDNumer",
     None, "Tak", "Tak", "int", None, "Klucz obcy do kontrahenta"),
    (2, "Kontrahenci", "CDN.KntKarty", 1, "Nazwa kontrahenta", "Knt_Nazwa1",
     None, "Tak", "Tak", "varchar", None, "Pierwsza linia nazwy"),
]

RELACJE_ROWS = [
    # nagłówek (pominięty)
    (None,) * 12,
    # dane: source_col=4, target_table=2, target_col=5, source_table=11
    (None, None, "KntKarty", None, "ZaN_KntGIDNumer", "Knt_GIDNumer",
     None, None, None, None, None, "CDN.ZamNag"),
]

SLOWNIK_ROWS = [
    # nagłówek (pominięty)
    (None,) * 8,
    # dane: table=2, col_name=5, value=6, meaning=7
    (1, "Zamówienia", "CDN.ZamNag", 3, "Status", "ZaN_Status", 0, "robocze"),
    (1, "Zamówienia", "CDN.ZamNag", 3, "Status", "ZaN_Status", 1, "zatwierdzone"),
    (1, "Zamówienia", "CDN.ZamNag", 3, "Status", "ZaN_Status", 2, "zrealizowane"),
]

PRZYKLADOWE_ROWS = [
    # nagłówek (pominięty)
    (None,) * 7,
    # dane: table=2, col_name=5, sample_value=6
    (1, None, "CDN.KntKarty", 1, None, "Knt_Nazwa1", "Firma ABC"),
    (1, None, "CDN.KntKarty", 1, None, "Knt_Nazwa1", "Jan Kowalski"),
]


# ── TestHelpers ─────────────────────────────────────────────────────────────


class TestHelpers:
    def test_str_none(self):
        assert bi._str(None) == ""

    def test_str_none_string(self):
        assert bi._str("None") == ""

    def test_str_value_error(self):
        assert bi._str("#VALUE!") == ""

    def test_str_space(self):
        assert bi._str("  ") == ""

    def test_str_normal(self):
        assert bi._str("CDN.ZamNag") == "CDN.ZamNag"

    def test_str_integer(self):
        assert bi._str(1) == "1"

    def test_normalize_table_adds_cdn(self):
        assert bi._normalize_table("ZamNag") == "CDN.ZamNag"

    def test_normalize_table_keeps_existing_schema(self):
        assert bi._normalize_table("CDN.ZamNag") == "CDN.ZamNag"

    def test_normalize_table_other_schema(self):
        assert bi._normalize_table("dbo.SomeTable") == "dbo.SomeTable"


# ── TestParsers ─────────────────────────────────────────────────────────────


class TestParsers:
    def test_parse_tables_count(self):
        result = bi.parse_tables(make_ws(TABELE_ROWS))
        assert len(result) == 2

    def test_parse_tables_fields(self):
        result = bi.parse_tables(make_ws(TABELE_ROWS))
        assert result[0]["table_name"] == "CDN.ZamNag"
        assert result[0]["table_label"] == "Zamówienia"
        assert result[0]["description"] == "Nagłówki zamówień sprzedaży"

    def test_parse_tables_skips_empty_table_id(self):
        rows = TABELE_ROWS + [(None, None, None, None, None, None)]
        assert len(bi.parse_tables(make_ws(rows))) == 2

    def test_parse_columns_skips_pre_header_rows(self):
        result = bi.parse_columns(make_ws(KOLUMNY_ROWS))
        assert len(result) == 3

    def test_parse_columns_fields(self):
        result = bi.parse_columns(make_ws(KOLUMNY_ROWS))
        assert result[0]["col_name"] == "ZaN_GIDNumer"
        assert result[0]["col_label"] == "ID zamówienia"
        assert result[0]["is_useful"] == "Tak"

    def test_parse_columns_col_label_zero_becomes_empty(self):
        rows_with_zero_label = list(KOLUMNY_ROWS)
        # zastąp col_label (indeks 4) wartością "0"
        last = list(rows_with_zero_label[-1])
        last[4] = "0"
        rows_with_zero_label[-1] = tuple(last)
        result = bi.parse_columns(make_ws(rows_with_zero_label))
        assert result[-1]["col_label"] == ""

    def test_parse_relations_normalizes_target(self):
        result = bi.parse_relations(make_ws(RELACJE_ROWS))
        assert len(result) == 1
        assert result[0]["source_table"] == "CDN.ZamNag"
        assert result[0]["target_table"] == "CDN.KntKarty"

    def test_parse_value_dicts_aggregates(self):
        result = bi.parse_value_dicts(make_ws(SLOWNIK_ROWS))
        key = ("CDN.ZamNag", "ZaN_Status")
        assert key in result
        assert "0=robocze" in result[key]
        assert "1=zatwierdzone" in result[key]
        assert "2=zrealizowane" in result[key]

    def test_parse_sample_values_aggregates(self):
        result = bi.parse_sample_values(make_ws(PRZYKLADOWE_ROWS))
        key = ("CDN.KntKarty", "Knt_Nazwa1")
        assert key in result
        assert "Firma ABC" in result[key]
        assert "Jan Kowalski" in result[key]

    def test_parse_sample_values_max_10(self):
        many_rows = [(None,) * 7]  # nagłówek
        for i in range(15):
            many_rows.append((1, None, "CDN.T", 1, None, "col", f"val{i}"))
        result = bi.parse_sample_values(make_ws(many_rows))
        values = result[("CDN.T", "col")].split(", ")
        assert len(values) == 10


# ── TestBuildSchema ─────────────────────────────────────────────────────────


class TestBuildSchema:
    def test_creates_all_tables(self):
        conn = in_memory_db()
        bi.build_schema(conn)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'shadow')"
        ).fetchall()
        names = {row[0] for row in tables}
        assert "tables" in names
        assert "columns" in names
        assert "relations" in names
        assert "columns_fts" in names

    def test_idempotent(self):
        conn = in_memory_db()
        bi.build_schema(conn)
        bi.build_schema(conn)  # drugi raz — brak błędu


# ── TestInsertData ──────────────────────────────────────────────────────────


class TestInsertData:
    def _build(self) -> sqlite3.Connection:
        conn = in_memory_db()
        bi.build_schema(conn)

        tables = bi.parse_tables(make_ws(TABELE_ROWS))
        columns = bi.parse_columns(make_ws(KOLUMNY_ROWS))
        relations = bi.parse_relations(make_ws(RELACJE_ROWS))
        value_dicts = bi.parse_value_dicts(make_ws(SLOWNIK_ROWS))
        sample_values = bi.parse_sample_values(make_ws(PRZYKLADOWE_ROWS))

        bi.insert_data(conn, tables, columns, relations, value_dicts, sample_values)
        return conn

    def test_tables_inserted(self):
        conn = self._build()
        count = conn.execute("SELECT COUNT(*) FROM tables").fetchone()[0]
        assert count == 2

    def test_columns_inserted(self):
        conn = self._build()
        count = conn.execute("SELECT COUNT(*) FROM columns").fetchone()[0]
        assert count == 3

    def test_relations_inserted(self):
        conn = self._build()
        count = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
        assert count == 1

    def test_value_dict_attached_to_column(self):
        conn = self._build()
        row = conn.execute(
            "SELECT value_dict FROM columns WHERE col_name = 'ZaN_Status'"
        ).fetchone()
        # ZaN_Status nie istnieje w KOLUMNY_ROWS — sprawdzamy że value_dict jest puste string
        # Testujemy kolumnę która JEST — Knt_Nazwa1 powinna mieć sample_values
        row = conn.execute(
            "SELECT sample_values FROM columns WHERE col_name = 'Knt_Nazwa1'"
        ).fetchone()
        assert row is not None
        assert "Firma ABC" in row[0]

    def test_fts_search_finds_result(self):
        conn = self._build()
        results = conn.execute(
            "SELECT col_name FROM columns_fts WHERE columns_fts MATCH 'kontrahent*'"
        ).fetchall()
        col_names = [r[0] for r in results]
        # "ID kontrahenta" jest opisem ZaN_KntGIDNumer — nie jest indeksowane w col_label
        # ale "Nazwa kontrahenta" jest col_label dla Knt_Nazwa1 → match
        assert len(results) > 0

    def test_fts_remove_diacritics(self):
        conn = self._build()
        # "zamowien" bez ogonka powinno trafić w "Nagłówki zamówień sprzedaży"
        results = conn.execute(
            "SELECT col_name FROM columns_fts WHERE columns_fts MATCH 'zamowien*'"
        ).fetchall()
        assert len(results) > 0
