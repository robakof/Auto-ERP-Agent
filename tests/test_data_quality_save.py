"""Testy dla tools/data_quality_save.py."""

import json
import sqlite3

import pytest

import tools.data_quality_save as dqs


def _make_db(tmp_path):
    """Tworzy minimalny SQLite z tabelą findings i zwraca ścieżkę."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column TEXT,
            observation TEXT,
            rows_affected INTEGER,
            created_at TEXT
        );
        CREATE TABLE dane (n TEXT);
    """)
    conn.commit()
    conn.close()
    return db_path


class TestSaveFinding:
    def test_happy_path_inserts_row(self, tmp_path):
        db_path = _make_db(tmp_path)
        result = dqs.save_finding(db_path, "Telefon", "Email w polu telefonu.", 47)
        assert result["ok"] is True
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT column, observation, rows_affected FROM findings").fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0] == ("Telefon", "Email w polu telefonu.", 47)

    def test_returns_finding_id(self, tmp_path):
        db_path = _make_db(tmp_path)
        result = dqs.save_finding(db_path, "Telefon", "Obserwacja.", 10)
        assert result["ok"] is True
        assert result["data"]["id"] == 1

    def test_appends_multiple_findings(self, tmp_path):
        db_path = _make_db(tmp_path)
        dqs.save_finding(db_path, "Telefon", "Obserwacja 1.", 5)
        dqs.save_finding(db_path, "NIP", "Obserwacja 2.", 3)
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
        conn.close()
        assert count == 2

    def test_id_increments(self, tmp_path):
        db_path = _make_db(tmp_path)
        r1 = dqs.save_finding(db_path, "A", "Obs 1.", 1)
        r2 = dqs.save_finding(db_path, "B", "Obs 2.", 2)
        assert r1["data"]["id"] == 1
        assert r2["data"]["id"] == 2

    def test_db_not_found_returns_error(self, tmp_path):
        result = dqs.save_finding(tmp_path / "brak.db", "Telefon", "Obs.", 1)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"

    def test_created_at_is_set(self, tmp_path):
        db_path = _make_db(tmp_path)
        dqs.save_finding(db_path, "Telefon", "Obs.", 1)
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT created_at FROM findings").fetchone()
        conn.close()
        assert row[0] is not None
        assert len(row[0]) == 10  # YYYY-MM-DD


class TestMain:
    def test_happy_path_prints_json(self, tmp_path, capsys):
        db_path = _make_db(tmp_path)
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", [
                "dqs.py", "--db", str(db_path),
                "--column", "Telefon",
                "--observation", "Email w telefonie.",
                "--rows-affected", "47",
            ])
            dqs.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is True
        assert result["data"]["id"] == 1

    def test_db_not_found_prints_error(self, tmp_path, capsys):
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("sys.argv", [
                "dqs.py", "--db", str(tmp_path / "brak.db"),
                "--column", "X", "--observation", "Y", "--rows-affected", "1",
            ])
            dqs.main()
        result = json.loads(capsys.readouterr().out)
        assert result["ok"] is False
        assert result["error"]["type"] == "FILE_NOT_FOUND"
