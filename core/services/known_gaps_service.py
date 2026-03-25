"""Service for managing known gaps (documented limitations with trigger conditions)."""

import sqlite3
from typing import Optional


class KnownGapsService:
    """CRUD operations for known_gaps table."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(
        self,
        title: str,
        description: str,
        area: str,
        trigger_condition: str,
        reported_by: str,
        source_suggestion_id: Optional[int] = None,
    ) -> int:
        """Add a known gap. Returns row id."""
        cursor = self._conn.execute(
            """INSERT INTO known_gaps
               (title, description, area, trigger_condition, reported_by, source_suggestion_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, description, area, trigger_condition, reported_by, source_suggestion_id),
        )
        return cursor.lastrowid

    def get(self, area: Optional[str] = None, status: str = "open") -> list[dict]:
        """Get known gaps, optionally filtered by area and status."""
        conditions: list[str] = []
        params: list = []

        if status and status != "all":
            conditions.append("status = ?")
            params.append(status)
        if area:
            conditions.append("area = ?")
            params.append(area)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._conn.execute(
            f"""SELECT id, title, description, area, trigger_condition,
                       source_suggestion_id, reported_by, status,
                       resolved_by_backlog_id, created_at, resolved_at
                FROM known_gaps {where}
                ORDER BY created_at DESC""",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def resolve(self, gap_id: int, backlog_id: int) -> dict:
        """Resolve a known gap by linking it to a backlog item."""
        row = self._conn.execute(
            "SELECT status FROM known_gaps WHERE id = ?", (gap_id,)
        ).fetchone()

        if not row:
            return {"ok": False, "message": f"Gap {gap_id} not found"}
        if row["status"] == "resolved":
            return {"ok": False, "message": f"Gap {gap_id} already resolved"}

        self._conn.execute(
            """UPDATE known_gaps
               SET status = 'resolved', resolved_by_backlog_id = ?, resolved_at = datetime('now')
               WHERE id = ?""",
            (backlog_id, gap_id),
        )
        return {"ok": True, "message": f"Gap {gap_id} resolved with backlog {backlog_id}"}
