"""Service for managing suggestions from agents."""

import sqlite3
from typing import Optional

from core.entities.messaging import Suggestion, SuggestionStatus, SuggestionType
from core.mappers.legacy_api import LegacyAPIMapper
from core.repositories.suggestion_repo import SuggestionRepository


class SuggestionService:
    """CRUD operations for suggestions, using repository layer."""

    def __init__(self, conn: sqlite3.Connection, db_path: str):
        self._conn = conn
        self._db_path = db_path

    def _get_repo(self, conn=None) -> SuggestionRepository:
        return SuggestionRepository(db_path=self._db_path, conn=conn)

    def add(
        self,
        author: str,
        content: str,
        title: str = "",
        type: str = "observation",
        recipients: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        conn=None,
    ) -> int:
        """Add a suggestion. Returns suggestion id."""
        try:
            type_enum = SuggestionType(type)
        except ValueError:
            type_enum = SuggestionType.OBSERVATION

        suggestion = Suggestion(
            author=author,
            content=content,
            title=title,
            type=type_enum,
            recipients=recipients,
            session_id=session_id,
        )

        repo = self._get_repo(conn)
        saved = repo.save(suggestion)
        return saved.id

    def get(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        type: Optional[str] = None,
        conn=None,
    ) -> list[dict]:
        """Get suggestions. Newest first. Optional filters."""
        repo = self._get_repo(conn)

        if status and author and type:
            suggestions = repo.find_all()
            suggestions = [
                s for s in suggestions
                if s.status.value == status and s.author == author and s.type.value == type
            ]
        elif status:
            suggestions = repo.find_by_status(SuggestionStatus(status))
        elif author:
            suggestions = repo.find_by_author(author)
        elif type:
            suggestions = repo.find_by_type(SuggestionType(type))
        else:
            suggestions = repo.find_all()

        return [LegacyAPIMapper.suggestion_to_dict(s) for s in suggestions]

    def update_status(
        self,
        suggestion_id: int,
        status: str,
        backlog_id: Optional[int] = None,
        conn=None,
    ) -> None:
        """Update suggestion status and optionally link to backlog item."""
        repo = self._get_repo(conn)

        suggestion = repo.get(suggestion_id)
        if not suggestion:
            return

        status_enum = LegacyAPIMapper.map_suggestion_status_to_domain(status)

        if status_enum == SuggestionStatus.IMPLEMENTED:
            suggestion.implement(backlog_id=backlog_id)
        elif status_enum == SuggestionStatus.REJECTED:
            suggestion.reject()
        elif status_enum == SuggestionStatus.DEFERRED:
            suggestion.defer()
        else:
            suggestion.status = status_enum
            if backlog_id is not None:
                suggestion.backlog_id = backlog_id

        repo.save(suggestion)
