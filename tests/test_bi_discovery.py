"""Testy dla tools/bi_discovery.py."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.lib.sql_client import SqlClient
import tools.bi_discovery as bd


def _make_multi_cursor(results: list[tuple[list, list]]) -> MagicMock:
    """
    results: lista (columns, rows) — każde wywołanie cursor.execute() przesuwa indeks.
    Odpowiednik make_mock_conn dla scenariuszy z wieloma różnymi zapytaniami.
    """
    cursor = MagicMock()
    call_idx = [0]

    def on_execute(sql):
        i = call_idx[0]
        cols, rows = results[i]
        cursor.description = [(col, None, None, None, None, None, None) for col in cols]
        cursor.fetchall.return_value = [tuple(row) for row in rows]
        call_idx[0] += 1

    cursor.execute.side_effect = on_execute
    return cursor


def _mock_conn(results):
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = _make_multi_cursor(results)
    return mock_conn


class TestClassifyHelpers:
    def test_classify_clarion_date(self):
        assert bd._classify_clarion(70000, 82000) == "Clarion_DATE"

    def test_classify_clarion_timestamp(self):
        assert bd._classify_clarion(1000000000, 1200000000) == "Clarion_TIMESTAMP"

    def test_classify_numeric_out_of_range(self):
        assert bd._classify_clarion(300000, 500000) == "numeric"

    def test_looks_like_date_true(self):
        assert bd._looks_like_date("ZaN_DataWystawienia") is True

    def test_looks_like_date_false(self):
        assert bd._looks_like_date("ZaN_Status") is False


class TestDiscover:
    def test_happy_path_three_column_types(self):
        """id + enum + Clarion_DATE — 5 zapytań."""
        conn = _mock_conn([
            # 1. INFORMATION_SCHEMA
            (["COLUMN_NAME", "DATA_TYPE"],
             [["TestId", "int"], ["Status", "int"], ["DataWyst", "int"]]),
            # 2. COUNT baseline
            (["cnt"], [[1000]]),
            # 3. COUNT DISTINCT
            (["d0", "d1", "d2"], [[1000, 2, 800]]),
            # 4. GROUP BY Status (enum)
            (["v", "cnt"], [[1, 600], [0, 400]]),
            # 5. MIN/MAX DataWyst
            (["mn", "mx"], [[80000, 82000]]),
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.TestTable")

        assert result["ok"] is True
        cols = {c["name"]: c for c in result["data"]["columns"]}
        assert cols["TestId"]["role"] == "id"
        assert cols["Status"]["role"] == "enum"
        assert cols["Status"]["values"] == [1, 0]
        assert cols["DataWyst"]["role"] == "Clarion_DATE"
        assert cols["DataWyst"]["min"] == 80000
        assert cols["DataWyst"]["max"] == 82000

    def test_constant_column(self):
        """Kolumna z distinct=1 → role=constant, value=960."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["GIDTyp", "int"]]),
            (["cnt"], [[500]]),
            (["d0"], [[1]]),
            (["v", "cnt"], [[960, 500]]),
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T")

        col = result["data"]["columns"][0]
        assert col["role"] == "constant"
        assert col["value"] == 960

    def test_clarion_timestamp(self):
        """int z 'Data' w nazwie i MAX > 1B → Clarion_TIMESTAMP."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["DataRez", "int"]]),
            (["cnt"], [[100]]),
            (["d0"], [[100]]),
            # distinct=100=row_count → id (nie wchodzi do date branch)
            # DataRez ma 'data' ale distinct==row_count, więc role=id
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T")
        # distinct=100=row_count → id
        assert result["data"]["columns"][0]["role"] == "id"

    def test_clarion_timestamp_high_distinct(self):
        """int z 'Data', distinct duże ale < row_count → MIN/MAX → Clarion_TIMESTAMP."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["DataRez", "int"]]),
            (["cnt"], [[5000]]),
            (["d0"], [[3000]]),
            (["mn", "mx"], [[1072800000, 1100000000]]),
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T")
        col = result["data"]["columns"][0]
        assert col["role"] == "Clarion_TIMESTAMP"

    def test_sql_date_type(self):
        """Kolumna typu date → SQL_DATE + MIN/MAX."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["TrN_Data2", "date"]]),
            (["cnt"], [[200]]),
            (["d0"], [[200]]),
            # distinct=200=row_count → id, nie wchodzi do SQL_DATE
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T")
        # distinct == row_count → id
        assert result["data"]["columns"][0]["role"] == "id"

    def test_sql_date_type_non_unique(self):
        """Kolumna typu date z distinct < row_count → SQL_DATE."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["TrN_Data2", "date"]]),
            (["cnt"], [[500]]),
            (["d0"], [[200]]),
            # distinct=200 > max_enum=30, distinct != row_count → SQL_DATE branch
            (["mn", "mx"], [["2023-01-01", "2025-12-31"]]),
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T")
        col = result["data"]["columns"][0]
        assert col["role"] == "SQL_DATE"
        assert col["min"] == "2023-01-01"

    def test_text_column(self):
        """varchar z dużym distinct → role=text."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["Knt_Nazwa1", "nvarchar"]]),
            (["cnt"], [[1000]]),
            (["d0"], [[980]]),
            # distinct=980 > max_enum=30, != row_count=1000 → text
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T")
        assert result["data"]["columns"][0]["role"] == "text"

    def test_with_pk_returns_pk_distinct(self):
        """--pk → pk_distinct w wyniku."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["ZaN_GIDNumer", "int"]]),
            (["cnt", "pk_d"], [[500, 500]]),
            (["d0"], [[500]]),
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.ZamNag", pk="ZaN_GIDNumer")

        assert result["data"]["pk_distinct"] == 500

    def test_with_filter_in_result(self):
        """--filter → filter_expr w data. distinct=50>max_enum, !=row_count → numeric (0 extra queries)."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["n", "int"]]),
            (["cnt"], [[100]]),
            (["d0"], [[50]]),
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T", filter_expr="n > 0")

        assert result["data"]["filter"] == "n > 0"
        assert result["data"]["row_count"] == 100

    def test_db_error_returns_error(self):
        """Błąd INFORMATION_SCHEMA → ok=False."""
        import pyodbc
        mock_conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = pyodbc.Error("42S02", "Invalid object name")
        mock_conn.cursor.return_value = cursor

        with patch.object(SqlClient, "get_connection", return_value=mock_conn):
            result = bd.discover("CDN.NieIstnieje")

        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_meta_duration_present(self):
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["n", "int"]]),
            (["cnt"], [[100]]),
            (["d0"], [[50]]),  # distinct=50>30, !=100 → numeric, 0 extra queries
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T")
        assert isinstance(result["meta"]["duration_ms"], int)


class TestNoEnum:
    def test_no_enum_skips_group_by(self):
        """no_enum=True → enum/constant bez listy wartości, brak dodatkowych zapytań."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["Status", "int"], ["GIDTyp", "int"]]),
            (["cnt"], [[1000]]),
            (["d0", "d1"], [[5, 1]]),
            # brak GROUP BY — no_enum=True
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T", no_enum=True)

        cols = {c["name"]: c for c in result["data"]["columns"]}
        assert cols["Status"]["role"] == "enum"
        assert "values" not in cols["Status"]
        assert cols["GIDTyp"]["role"] == "constant"
        assert "value" not in cols["GIDTyp"]

    def test_no_enum_false_still_fetches_values(self):
        """no_enum=False (domyślnie) → wartości enum obecne."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["Status", "int"]]),
            (["cnt"], [[1000]]),
            (["d0"], [[2]]),
            (["v", "cnt"], [[1, 800], [0, 200]]),
        ])
        with patch.object(SqlClient, "get_connection", return_value=conn):
            result = bd.discover("CDN.T", no_enum=False)

        col = result["data"]["columns"][0]
        assert col["role"] == "enum"
        assert col["values"] == [1, 0]

    def test_no_enum_cli_flag(self, capsys):
        """--no-enum w CLI → no_enum=True."""
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["Status", "int"]]),
            (["cnt"], [[500]]),
            (["d0"], [[3]]),
        ])
        with patch("sys.argv", ["bi_discovery.py", "CDN.T", "--no-enum"]):
            with patch.object(SqlClient, "get_connection", return_value=conn):
                bd.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        col = result["data"]["columns"][0]
        assert col["role"] == "enum"
        assert "values" not in col


class TestMain:
    def test_valid_call_prints_json(self, capsys):
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["n", "int"]]),
            (["cnt"], [[100]]),
            (["d0"], [[50]]),  # distinct=50>30, !=100 → numeric
        ])
        with patch("sys.argv", ["bi_discovery.py", "CDN.T"]):
            with patch.object(SqlClient, "get_connection", return_value=conn):
                bd.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["table"] == "CDN.T"

    def test_pk_and_filter_flags(self, capsys):
        conn = _mock_conn([
            (["COLUMN_NAME", "DATA_TYPE"], [["n", "int"]]),
            (["cnt", "pk_d"], [[100, 100]]),
            (["d0"], [[100]]),  # distinct=100=row_count → id
        ])
        with patch("sys.argv", [
            "bi_discovery.py", "CDN.T", "--pk", "n", "--filter", "n > 0"
        ]):
            with patch.object(SqlClient, "get_connection", return_value=conn):
                bd.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["pk_distinct"] == 100
        assert result["data"]["filter"] == "n > 0"
