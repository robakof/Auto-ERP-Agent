"""Testy dla tools/data_quality_query.py."""

import json
import sqlite3

import pytest

import tools.data_quality_query as dqq


def _make_db(tmp_path, columns, rows):
    """Tworzy SQLite z tabelą dane i zwraca ścieżkę."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
    conn.execute(f"CREATE TABLE dane ({col_defs})")
    placeholders = ", ".join("?" * len(columns))
    conn.executemany(f"INSERT INTO dane VALUES ({placeholders})", rows)
    conn.commit()
    conn.close()
    return db_path


class TestRunQuery:
    def test_happy_path_returns_rows(self, tmp_path):
        db_path = _make_db(tmp_path, ["Kod", "Nazwa"], [("ABC", "Firma"), ("XYZ", "Inna")])
        result = dqq.run_query(db_path, "SELECT Kod, Nazwa FROM dane")
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert result["data"]["columns"] == ["Kod", "Nazwa"]

    def test_file_not_found_returns_error(self, tmp_path):
        result = dqq.run_query(tmp_path / "brak.db", "SELECT 1")
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_sql_error_returns_error(self, tmp_path):
        db_path = _make_db(tmp_path, ["n"], [("1",)])
        result = dqq.run_query(db_path, "SELECT brak_kolumny FROM dane")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_not_select_returns_error(self, tmp_path):
        db_path = _make_db(tmp_path, ["n"], [("1",)])
        result = dqq.run_query(db_path, "DELETE FROM dane")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"

    def test_cross_column_filter(self, tmp_path):
        db_path = _make_db(tmp_path, ["Telefon", "Email"],
                           [("jan@firma.pl", "jan@firma.pl"), ("123456789", "jan@firma.pl")])
        result = dqq.run_query(db_path, "SELECT Telefon FROM dane WHERE Telefon LIKE '%@%'")
        assert result["ok"] is True
        assert result["data"]["row_count"] == 1

    def test_duration_ms_present(self, tmp_path):
        db_path = _make_db(tmp_path, ["n"], [("1",)])
        result = dqq.run_query(db_path, "SELECT n FROM dane")
        assert isinstance(result["meta"]["duration_ms"], int)


class TestMain:
    def test_happy_path_prints_json(self, tmp_path, capsys):
        db_path = _make_db(tmp_path, ["n"], [("1",), ("2",)])
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", ["dqq.py", "--db", str(db_path), "--sql", "SELECT n FROM dane"])
            dqq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2

    def test_count_only_excludes_rows(self, tmp_path, capsys):
        db_path = _make_db(tmp_path, ["n"], [("1",), ("2",)])
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", ["dqq.py", "--db", str(db_path), "--sql", "SELECT n FROM dane", "--count-only"])
            dqq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["row_count"] == 2
        assert "rows" not in result["data"]

    def test_quiet_ok(self, tmp_path, capsys):
        db_path = _make_db(tmp_path, ["n"], [("1",), ("2",), ("3",)])
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", ["dqq.py", "--db", str(db_path), "--sql", "SELECT n FROM dane", "--quiet"])
            dqq.main()
        out = capsys.readouterr().out.strip()
        assert out == "OK 3"

    def test_quiet_error(self, tmp_path, capsys):
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", ["dqq.py", "--db", str(tmp_path / "brak.db"), "--sql", "SELECT 1", "--quiet"])
            dqq.main()
        out = capsys.readouterr().out.strip()
        assert out.startswith("ERROR:")

    def test_file_not_found_prints_error_json(self, tmp_path, capsys):
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", ["dqq.py", "--db", str(tmp_path / "brak.db"), "--sql", "SELECT 1"])
            dqq.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"
