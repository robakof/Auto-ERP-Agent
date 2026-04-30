"""Schema tests — DDL, constraints, indexes, schema_version."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core.ksef.adapters.repo import ShipmentRepository

_EXPECTED_TABLES = {"ksef_wysylka", "ksef_transition", "schema_version"}
_EXPECTED_INDEXES = {
    "idx_ksef_status",
    "idx_ksef_gid_rodzaj",
    "idx_ksef_xml_hash",
    "idx_ksef_transition_wysylka",
}


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "ksef.db"
    ShipmentRepository(path).init_schema()
    return path


def test_init_schema_creates_all_tables(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    tables = {r[0] for r in rows}
    assert _EXPECTED_TABLES <= tables


def test_init_schema_creates_indexes(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    indexes = {r[0] for r in rows}
    assert _EXPECTED_INDEXES <= indexes


def test_init_schema_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "ksef.db"
    repo = ShipmentRepository(path)
    repo.init_schema()
    repo.init_schema()  # second run must not raise
    with sqlite3.connect(path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
    assert count == 3  # v1 (base) + v2 (FSK_SKONTO) + v3 (FSK_RABAT migration)


def test_schema_version_is_current(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version == 3


def test_status_check_constraint_rejects_invalid(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO ksef_wysylka"
                " (gid_erp, rodzaj, nr_faktury, data_wystawienia, xml_path,"
                "  xml_hash, status)"
                " VALUES (1, 'FS', 'FS/1', '2026-04-15', 'x.xml', 'h', 'BOGUS')"
            )


def test_rodzaj_check_constraint_rejects_invalid(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO ksef_wysylka"
                " (gid_erp, rodzaj, nr_faktury, data_wystawienia, xml_path,"
                "  xml_hash, status)"
                " VALUES (1, 'XYZ', 'FS/1', '2026-04-15', 'x.xml', 'h', 'DRAFT')"
            )


def test_unique_gid_rodzaj_attempt(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO ksef_wysylka"
            " (gid_erp, rodzaj, nr_faktury, data_wystawienia, xml_path,"
            "  xml_hash, status, attempt)"
            " VALUES (10, 'FS', 'FS/1', '2026-04-15', 'x.xml', 'h', 'DRAFT', 1)"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO ksef_wysylka"
                " (gid_erp, rodzaj, nr_faktury, data_wystawienia, xml_path,"
                "  xml_hash, status, attempt)"
                " VALUES (10, 'FS', 'FS/1b', '2026-04-15', 'x.xml', 'h', 'DRAFT', 1)"
            )
