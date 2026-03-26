"""jas_db.py — SQLite tracking store for JAS shipment exports.

Osobna baza jas.db (niezależna od mrowisko.db).
Schemat tworzony automatycznie przy pierwszym użyciu.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_DB_PATH = _PROJECT_ROOT / "jas.db"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jas_shipments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    wz_id       INTEGER NOT NULL,
    numer_wz    TEXT    NOT NULL,
    jas_id      INTEGER,
    status      TEXT    NOT NULL DEFAULT 'sent',
    error_msg   TEXT,
    sent_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_jas_shipments_wz_sent
    ON jas_shipments(wz_id)
    WHERE status = 'sent';

CREATE INDEX IF NOT EXISTS ix_jas_shipments_wz
    ON jas_shipments(wz_id);
"""


class JasDb:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self._db_path = Path(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA_SQL)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def already_sent(self, wz_id: int) -> bool:
        """Zwraca True jeśli wz_id ma rekord 'sent'."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM jas_shipments WHERE wz_id = ? AND status = 'sent'",
                (int(wz_id),),
            ).fetchone()
        return row is not None

    def record_result(
        self,
        wz_id: int,
        numer_wz: str,
        jas_id: int | None = None,
        error_msg: str | None = None,
    ) -> None:
        """Zapisuje wynik wysłania (sent lub error)."""
        status = "sent" if error_msg is None else "error"
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO jas_shipments (wz_id, numer_wz, jas_id, status, error_msg) "
                "VALUES (?, ?, ?, ?, ?)",
                (int(wz_id), numer_wz, jas_id, status, error_msg),
            )
