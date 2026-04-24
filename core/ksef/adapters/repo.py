"""ShipmentRepository — SQLite persistence for KSeF shadow DB.

Single writer + N readers pattern, WAL mode. Atomic state transitions
with audit logging in `ksef_transition`. Raw SQL from `core/ksef/schema.sql`.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable


def _default_clock() -> datetime:
    """Naive UTC timestamp — avoids deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _adapt_date(value: date) -> str:
    return value.isoformat()


def _adapt_datetime(value: datetime) -> str:
    return value.isoformat(sep=" ")


def _convert_date(raw: bytes) -> date:
    return date.fromisoformat(raw.decode("utf-8"))


def _convert_timestamp(raw: bytes) -> datetime:
    return datetime.fromisoformat(raw.decode("utf-8"))


sqlite3.register_adapter(date, _adapt_date)
sqlite3.register_adapter(datetime, _adapt_datetime)
sqlite3.register_converter("DATE", _convert_date)
sqlite3.register_converter("TIMESTAMP", _convert_timestamp)

from core.ksef.domain.shipment import (
    ShipmentStatus,
    Wysylka,
    is_active,
    is_valid_transition,
)
from core.ksef.exceptions import (
    InvalidTransitionError,
    ShipmentAlreadyActiveError,
    ShipmentNotFoundError,
)

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"

_TERMINAL_TIMESTAMP_COL: dict[ShipmentStatus, str] = {
    ShipmentStatus.QUEUED: "queued_at",
    ShipmentStatus.SENT: "sent_at",
    ShipmentStatus.ACCEPTED: "accepted_at",
    ShipmentStatus.REJECTED: "rejected_at",
    ShipmentStatus.ERROR: "errored_at",
}

_ALLOWED_TRANSITION_FIELDS = frozenset({
    "ksef_session_ref", "ksef_invoice_ref", "ksef_number",
    "upo_path", "error_code", "error_msg",
})


class ShipmentRepository:
    """Persistence boundary — row (sqlite) ↔ Wysylka (domain) in one place."""

    def __init__(
        self,
        db_path: Path,
        *,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self._db_path = Path(db_path)
        self._clock = clock

    # ---- schema ------------------------------------------------------

    def init_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)
            self._migrate(conn)

    def _migrate(self, conn) -> None:
        """Run schema migrations beyond v1."""
        ver = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()[0] or 1
        if ver < 2:
            # v2: widen rodzaj CHECK to include FSK_SKONTO
            # SQLite cannot ALTER CHECK — recreate table
            conn.executescript("""
                PRAGMA foreign_keys = OFF;
                CREATE TABLE IF NOT EXISTS ksef_wysylka_new (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    gid_erp           INTEGER NOT NULL,
                    rodzaj            TEXT    NOT NULL CHECK (rodzaj IN ('FS', 'FSK', 'FSK_SKONTO')),
                    nr_faktury        TEXT    NOT NULL,
                    data_wystawienia  DATE    NOT NULL,
                    xml_path          TEXT    NOT NULL,
                    xml_hash          TEXT    NOT NULL,
                    status            TEXT    NOT NULL CHECK (status IN (
                                          'DRAFT','QUEUED','AUTH_PENDING',
                                          'SENT','ACCEPTED','REJECTED','ERROR'
                                      )),
                    ksef_session_ref  TEXT,
                    ksef_invoice_ref  TEXT,
                    ksef_number       TEXT,
                    upo_path          TEXT,
                    error_code        TEXT,
                    error_msg         TEXT,
                    attempt           INTEGER NOT NULL DEFAULT 1,
                    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    queued_at         TIMESTAMP,
                    sent_at           TIMESTAMP,
                    accepted_at       TIMESTAMP,
                    rejected_at       TIMESTAMP,
                    errored_at        TIMESTAMP,
                    UNIQUE (gid_erp, rodzaj, attempt)
                );
                INSERT OR IGNORE INTO ksef_wysylka_new SELECT * FROM ksef_wysylka;
                DROP TABLE ksef_wysylka;
                ALTER TABLE ksef_wysylka_new RENAME TO ksef_wysylka;
                CREATE INDEX IF NOT EXISTS idx_ksef_status ON ksef_wysylka(status);
                CREATE INDEX IF NOT EXISTS idx_ksef_gid_rodzaj ON ksef_wysylka(gid_erp, rodzaj);
                CREATE INDEX IF NOT EXISTS idx_ksef_xml_hash ON ksef_wysylka(xml_hash);
                INSERT OR IGNORE INTO schema_version(version) VALUES (2);
                PRAGMA foreign_keys = ON;
            """)

    # ---- queries -----------------------------------------------------

    def get(self, wysylka_id: int) -> Wysylka | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM ksef_wysylka WHERE id = ?", (wysylka_id,)
            ).fetchone()
        return _row_to_wysylka(row) if row else None

    def get_latest(self, gid_erp: int, rodzaj: str) -> Wysylka | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM ksef_wysylka WHERE gid_erp = ? AND rodzaj = ?"
                " ORDER BY attempt DESC LIMIT 1",
                (gid_erp, rodzaj),
            ).fetchone()
        return _row_to_wysylka(row) if row else None

    def has_pending_or_sent(self, gid_erp: int, rodzaj: str) -> bool:
        placeholders = ",".join("?" * len(_ACTIVE_STATUS_NAMES))
        with self._connect() as conn:
            row = conn.execute(
                f"SELECT 1 FROM ksef_wysylka WHERE gid_erp = ? AND rodzaj = ?"
                f" AND status IN ({placeholders}) LIMIT 1",
                (gid_erp, rodzaj, *_ACTIVE_STATUS_NAMES),
            ).fetchone()
        return row is not None

    def list_by_status(self, status: ShipmentStatus, limit: int = 100) -> list[Wysylka]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ksef_wysylka WHERE status = ?"
                " ORDER BY id DESC LIMIT ?",
                (status.value, limit),
            ).fetchall()
        return [_row_to_wysylka(r) for r in rows]

    def list_by_gid(
        self,
        gid_erp: int,
        rodzaj: str | None = None,
        limit: int = 100,
    ) -> list[Wysylka]:
        """Wszystkie attempts dla GID — dla audytu historii wysyłek."""
        sql = "SELECT * FROM ksef_wysylka WHERE gid_erp = ?"
        params: list[Any] = [gid_erp]
        if rodzaj is not None:
            sql += " AND rodzaj = ?"
            params.append(rodzaj)
        sql += " ORDER BY rodzaj, attempt DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_wysylka(r) for r in rows]

    def list_recent(self, limit: int = 50) -> list[Wysylka]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ksef_wysylka ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [_row_to_wysylka(r) for r in rows]

    def list_stuck(self, stale_minutes: int = 30) -> list[Wysylka]:
        """Return QUEUED/AUTH_PENDING/SENT records older than stale_minutes."""
        cutoff = self._clock() - __import__("datetime").timedelta(minutes=stale_minutes)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM ksef_wysylka"
                " WHERE status IN ('QUEUED','AUTH_PENDING','SENT')"
                " AND created_at < ?"
                " ORDER BY id",
                (cutoff,),
            ).fetchall()
        return [_row_to_wysylka(r) for r in rows]

    def count_by_status(
        self, since: datetime | None = None,
    ) -> dict[ShipmentStatus, int]:
        """Count shipments per status. `since` filters by created_at >= since."""
        sql = "SELECT status, COUNT(*) AS n FROM ksef_wysylka"
        params: list[Any] = []
        if since is not None:
            sql += " WHERE created_at >= ?"
            params.append(since)
        sql += " GROUP BY status"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        counts = {s: 0 for s in ShipmentStatus}
        for row in rows:
            counts[ShipmentStatus(row["status"])] = row["n"]
        return counts

    # ---- mutations ---------------------------------------------------

    def create(
        self,
        *,
        gid_erp: int,
        rodzaj: str,
        nr_faktury: str,
        data_wystawienia: date,
        xml_path: str,
        xml_hash: str,
        attempt: int = 1,
    ) -> Wysylka:
        if self.has_pending_or_sent(gid_erp, rodzaj):
            raise ShipmentAlreadyActiveError(
                f"Aktywna wysylka dla (gid={gid_erp}, rodzaj={rodzaj})"
            )
        return self._insert(
            gid_erp=gid_erp, rodzaj=rodzaj, nr_faktury=nr_faktury,
            data_wystawienia=data_wystawienia, xml_path=xml_path,
            xml_hash=xml_hash, attempt=attempt,
        )

    def new_attempt(
        self,
        gid_erp: int,
        rodzaj: str,
        *,
        nr_faktury: str,
        data_wystawienia: date,
        xml_path: str,
        xml_hash: str,
    ) -> Wysylka:
        prev = self.get_latest(gid_erp, rodzaj)
        if prev is None:
            raise ShipmentNotFoundError(
                f"Brak poprzedniej wysylki dla (gid={gid_erp}, rodzaj={rodzaj})"
            )
        if is_active(prev.status):
            raise ShipmentAlreadyActiveError(
                f"Nie mozna retry — poprzednia proba w stanie {prev.status.value}"
            )
        return self._insert(
            gid_erp=gid_erp, rodzaj=rodzaj, nr_faktury=nr_faktury,
            data_wystawienia=data_wystawienia, xml_path=xml_path,
            xml_hash=xml_hash, attempt=prev.attempt + 1,
        )

    def transition(
        self,
        wysylka_id: int,
        new_status: ShipmentStatus,
        *,
        meta: dict[str, Any] | None = None,
        **fields: Any,
    ) -> Wysylka:
        unknown = set(fields) - _ALLOWED_TRANSITION_FIELDS
        if unknown:
            raise ValueError(f"Niedozwolone pola w transition: {sorted(unknown)}")
        with self._connect() as conn:
            current = self._fetch_for_update(conn, wysylka_id)
            if not is_valid_transition(current.status, new_status):
                raise InvalidTransitionError(
                    f"{current.status.value} -> {new_status.value} niedozwolone"
                )
            self._apply_transition(conn, current, new_status, fields, meta)
            return self._load(conn, wysylka_id)

    # ---- internals ---------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10.0,
            isolation_level="DEFERRED",
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _insert(self, **kw: Any) -> Wysylka:
        now = self._clock()
        with self._connect() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO ksef_wysylka"
                    " (gid_erp, rodzaj, nr_faktury, data_wystawienia, xml_path,"
                    "  xml_hash, status, attempt, created_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?)",
                    (kw["gid_erp"], kw["rodzaj"], kw["nr_faktury"],
                     kw["data_wystawienia"], kw["xml_path"], kw["xml_hash"],
                     kw["attempt"], now),
                )
            except sqlite3.IntegrityError as exc:
                raise ShipmentAlreadyActiveError(
                    f"Konflikt (gid={kw['gid_erp']}, rodzaj={kw['rodzaj']}, "
                    f"attempt={kw['attempt']})"
                ) from exc
            return self._load(conn, int(cur.lastrowid))

    def _fetch_for_update(self, conn: sqlite3.Connection, wysylka_id: int) -> Wysylka:
        row = conn.execute(
            "SELECT * FROM ksef_wysylka WHERE id = ?", (wysylka_id,)
        ).fetchone()
        if row is None:
            raise ShipmentNotFoundError(f"Brak wysylki id={wysylka_id}")
        return _row_to_wysylka(row)

    def _apply_transition(
        self,
        conn: sqlite3.Connection,
        current: Wysylka,
        new_status: ShipmentStatus,
        fields: dict[str, Any],
        meta: dict[str, Any] | None,
    ) -> None:
        now = self._clock()
        cols = ["status = ?"]
        vals: list[Any] = [new_status.value]
        ts_col = _TERMINAL_TIMESTAMP_COL.get(new_status)
        if ts_col:
            cols.append(f"{ts_col} = ?")
            vals.append(now)
        for k, v in fields.items():
            cols.append(f"{k} = ?")
            vals.append(v)
        vals.append(current.id)
        conn.execute(
            f"UPDATE ksef_wysylka SET {', '.join(cols)} WHERE id = ?", vals
        )
        conn.execute(
            "INSERT INTO ksef_transition"
            " (wysylka_id, from_status, to_status, occurred_at, meta_json)"
            " VALUES (?, ?, ?, ?, ?)",
            (current.id, current.status.value, new_status.value, now,
             json.dumps(meta) if meta is not None else None),
        )

    def _load(self, conn: sqlite3.Connection, wysylka_id: int) -> Wysylka:
        row = conn.execute(
            "SELECT * FROM ksef_wysylka WHERE id = ?", (wysylka_id,)
        ).fetchone()
        if row is None:
            raise ShipmentNotFoundError(f"Brak wysylki id={wysylka_id}")
        return _row_to_wysylka(row)


_ACTIVE_STATUS_NAMES: tuple[str, ...] = (
    ShipmentStatus.QUEUED.value,
    ShipmentStatus.AUTH_PENDING.value,
    ShipmentStatus.SENT.value,
    ShipmentStatus.ACCEPTED.value,
)


def _row_to_wysylka(row: sqlite3.Row) -> Wysylka:
    return Wysylka(
        id=row["id"],
        gid_erp=row["gid_erp"],
        rodzaj=row["rodzaj"],
        nr_faktury=row["nr_faktury"],
        data_wystawienia=_as_date(row["data_wystawienia"]),
        xml_path=row["xml_path"],
        xml_hash=row["xml_hash"],
        status=ShipmentStatus(row["status"]),
        ksef_session_ref=row["ksef_session_ref"],
        ksef_invoice_ref=row["ksef_invoice_ref"],
        ksef_number=row["ksef_number"],
        upo_path=row["upo_path"],
        error_code=row["error_code"],
        error_msg=row["error_msg"],
        attempt=row["attempt"],
        created_at=_as_datetime(row["created_at"]),
        queued_at=_as_datetime(row["queued_at"]),
        sent_at=_as_datetime(row["sent_at"]),
        accepted_at=_as_datetime(row["accepted_at"]),
        rejected_at=_as_datetime(row["rejected_at"]),
        errored_at=_as_datetime(row["errored_at"]),
    )


def _as_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
