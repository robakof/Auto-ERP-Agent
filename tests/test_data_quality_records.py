"""Testy dla tools/data_quality_records.py."""

import json
import sqlite3

import pytest

import tools.data_quality_records as dqr


def _make_db(tmp_path, dane_columns=None, dane_rows=None):
    """Tworzy SQLite z tabelami dane/records i zwraca ścieżkę."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column TEXT,
            data TEXT,
            created_at TEXT
        );
    """)
    if dane_columns:
        col_defs = ", ".join(f'"{c}" TEXT' for c in dane_columns)
        conn.execute(f"CREATE TABLE dane ({col_defs})")
        if dane_rows:
            placeholders = ", ".join("?" * len(dane_columns))
            conn.executemany(f"INSERT INTO dane VALUES ({placeholders})", dane_rows)
    conn.commit()
    conn.close()
    return db_path


class TestSaveRecords:
    def test_happy_path_inserts_records(self, tmp_path):
        db_path = _make_db(tmp_path,
                           dane_columns=["Kod", "Telefon"],
                           dane_rows=[("ABC", "jan@firma.pl"), ("XYZ", "info@x.com")])
        result = dqr.save_records(
            db_path, "Telefon",
            "SELECT Kod, Telefon FROM dane WHERE Telefon LIKE '%@%'"
        )
        assert result["ok"] is True
        assert result["data"]["records_saved"] == 2

    def test_records_stored_as_json(self, tmp_path):
        db_path = _make_db(tmp_path,
                           dane_columns=["Kod", "Telefon"],
                           dane_rows=[("ABC", "jan@firma.pl")])
        dqr.save_records(db_path, "Telefon", "SELECT Kod, Telefon FROM dane")
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT column, data FROM records").fetchone()
        conn.close()
        assert row[0] == "Telefon"
        parsed = json.loads(row[1])
        assert parsed["Kod"] == "ABC"
        assert parsed["Telefon"] == "jan@firma.pl"

    def test_empty_result_saves_zero_records(self, tmp_path):
        db_path = _make_db(tmp_path,
                           dane_columns=["Telefon"],
                           dane_rows=[("123456789",)])
        result = dqr.save_records(
            db_path, "Telefon",
            "SELECT Telefon FROM dane WHERE Telefon LIKE '%@%'"
        )
        assert result["ok"] is True
        assert result["data"]["records_saved"] == 0

    def test_appends_to_existing_records(self, tmp_path):
        db_path = _make_db(tmp_path,
                           dane_columns=["Kod"],
                           dane_rows=[("A",), ("B",), ("C",)])
        dqr.save_records(db_path, "Kod", "SELECT Kod FROM dane WHERE Kod = 'A'")
        dqr.save_records(db_path, "Kod", "SELECT Kod FROM dane WHERE Kod = 'B'")
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        conn.close()
        assert count == 2

    def test_db_not_found_returns_error(self, tmp_path):
        result = dqr.save_records(tmp_path / "brak.db", "Telefon", "SELECT 1")
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_not_select_returns_validation_error(self, tmp_path):
        db_path = _make_db(tmp_path, dane_columns=["n"], dane_rows=[("1",)])
        result = dqr.save_records(db_path, "n", "DELETE FROM dane")
        assert result["ok"] is False
        assert result["error"]["type"] == "VALIDATION_ERROR"

    def test_sql_error_returns_error(self, tmp_path):
        db_path = _make_db(tmp_path, dane_columns=["n"], dane_rows=[("1",)])
        result = dqr.save_records(db_path, "n", "SELECT brak FROM dane")
        assert result["ok"] is False
        assert result["error"]["type"] == "SQL_ERROR"

    def test_created_at_is_set(self, tmp_path):
        db_path = _make_db(tmp_path, dane_columns=["n"], dane_rows=[("1",)])
        dqr.save_records(db_path, "n", "SELECT n FROM dane")
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT created_at FROM records").fetchone()
        conn.close()
        assert row[0] is not None
        assert len(row[0]) == 10  # YYYY-MM-DD


class TestMain:
    def test_happy_path_prints_json(self, tmp_path, capsys):
        db_path = _make_db(tmp_path,
                           dane_columns=["Kod", "Telefon"],
                           dane_rows=[("ABC", "jan@firma.pl")])
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", [
                "dqr.py", "--db", str(db_path),
                "--column", "Telefon",
                "--sql", "SELECT Kod, Telefon FROM dane",
            ])
            dqr.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["records_saved"] == 1

    def test_db_not_found_prints_error(self, tmp_path, capsys):
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", [
                "dqr.py", "--db", str(tmp_path / "brak.db"),
                "--column", "X", "--sql", "SELECT 1",
            ])
            dqr.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"
