"""Service for managing backlog items."""

import sqlite3
from typing import Optional

from core.entities.messaging import (
    BacklogArea, BacklogEffort, BacklogItem, BacklogStatus, BacklogValue,
)
from core.mappers.legacy_api import LegacyAPIMapper
from core.repositories.backlog_repo import BacklogRepository


class BacklogService:
    """CRUD operations for backlog items, using repository layer."""

    def __init__(self, conn: sqlite3.Connection, db_path: str):
        self._conn = conn
        self._db_path = db_path

    def _get_repo(self, conn=None) -> BacklogRepository:
        return BacklogRepository(db_path=self._db_path, conn=conn)

    def add(
        self,
        title: str,
        content: str,
        area: Optional[str] = None,
        value: Optional[str] = None,
        effort: Optional[str] = None,
        source_id: Optional[int] = None,
        conn=None,
    ) -> int:
        """Add a backlog item. Returns backlog id."""
        area_enum = BacklogArea(area) if area else None
        value_enum = BacklogValue(value) if value else None
        effort_enum = BacklogEffort(effort) if effort else None

        item = BacklogItem(
            title=title, content=content,
            area=area_enum, value=value_enum, effort=effort_enum,
            source_id=source_id,
        )

        repo = self._get_repo(conn)
        saved = repo.save(item)
        return saved.id

    def get(
        self,
        status: Optional[str] = None,
        area: Optional[str] = None,
        conn=None,
    ) -> list[dict]:
        """Get backlog items. Newest first. Optional filters."""
        repo = self._get_repo(conn)

        if status and area:
            items = repo.find_all()
            items = [i for i in items if i.status.value == status and i.area and i.area.value == area]
        elif status:
            items = repo.find_by_status(BacklogStatus(status))
        elif area:
            items = repo.find_by_area(BacklogArea(area))
        else:
            items = repo.find_all()

        return [LegacyAPIMapper.backlog_to_dict(item) for item in items]

    def get_by_id(self, backlog_id: int, conn=None) -> Optional[dict]:
        """Get a single backlog item by ID."""
        repo = self._get_repo(conn)
        item = repo.get(backlog_id)
        if item is None:
            return None
        return LegacyAPIMapper.backlog_to_dict(item)

    def update_status(self, backlog_id: int, status: str, conn=None) -> None:
        """Update backlog item status."""
        repo = self._get_repo(conn)
        item = repo.get(backlog_id)
        if not item:
            return

        try:
            item.status = BacklogStatus(status)
        except ValueError:
            return

        repo.save(item)

    def update_content(self, backlog_id: int, content: str, conn=None) -> None:
        """Update backlog item content."""
        repo = self._get_repo(conn)
        item = repo.get(backlog_id)
        if not item:
            return

        item.content = content
        repo.save(item)
