"""
Repository dla encji Suggestion.

Mapowanie między Suggestion (domain model) a tabela suggestions (SQLite).
"""

import sqlite3
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from .base import Repository
from ..entities.messaging import Suggestion, SuggestionStatus, SuggestionType
from ..exceptions import NotFoundError, ValidationError


class SuggestionRepository(Repository[Suggestion]):
    """
    Repository dla Suggestion — persystencja do SQLite.

    Tabela: suggestions
    Schema: id, author, recipients, title, content, type, status, backlog_id, session_id, created_at

    Example:
        >>> repo = SuggestionRepository("mrowisko.db")
        >>> suggestion = Suggestion(author="dev", content="Test", title="Test")
        >>> suggestion = repo.save(suggestion)
        >>> suggestion.id  # Auto-generated
        42
        >>> loaded = repo.get(42)
        >>> loaded.author
        'dev'
    """

    def __init__(self, db_path: str = "mrowisko.db"):
        """
        Args:
            db_path: Ścieżka do bazy SQLite (domyślnie mrowisko.db w root)
        """
        self.db_path = db_path
        self._ensure_table_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """Tworzy połączenie z bazą danych."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pozwala na dostęp do kolumn po nazwie
        return conn

    def _ensure_table_exists(self) -> None:
        """
        Upewnia się że tabela suggestions istnieje.

        Note: W produkcji tabela już istnieje (utworzona przez agent_bus).
        Ta metoda jest safety net dla testów.
        """
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT NOT NULL,
                    recipients TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT DEFAULT 'observation',
                    status TEXT DEFAULT 'open',
                    backlog_id INTEGER,
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _row_to_entity(self, row: sqlite3.Row) -> Suggestion:
        """
        Konwertuje wiersz z DB na encję Suggestion.

        Args:
            row: Wiersz z sqlite3 (Row object)

        Returns:
            Suggestion z danymi z DB
        """
        return Suggestion(
            author=row["author"],
            content=row["content"],
            title=row["title"],
            type=SuggestionType(row["type"]),
            status=SuggestionStatus(row["status"]),
            backlog_id=row["backlog_id"],
            session_id=row["session_id"],
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )

    def _entity_to_row(self, entity: Suggestion) -> dict:
        """
        Konwertuje encję Suggestion na dict dla DB.

        Args:
            entity: Suggestion do zapisu

        Returns:
            Dict z danymi gotowymi do INSERT/UPDATE
        """
        return {
            "author": entity.author,
            "title": entity.title,
            "content": entity.content,
            "type": entity.type.value,
            "status": entity.status.value,
            "backlog_id": entity.backlog_id,
            "session_id": entity.session_id,
            "created_at": entity.created_at.isoformat()
        }

    def get(self, id: int) -> Optional[Suggestion]:
        """
        Pobiera Suggestion po ID.

        Args:
            id: ID sugestii

        Returns:
            Suggestion jeśli istnieje, None jeśli nie znaleziono
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, author, recipients, title, content, type, status, backlog_id,
                          session_id, created_at
                   FROM suggestions
                   WHERE id = ?""",
                (id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
        finally:
            conn.close()

    def save(self, entity: Suggestion) -> Suggestion:
        """
        Zapisuje Suggestion do bazy.

        Jeśli entity.id is None → INSERT
        Jeśli entity.id is not None → UPDATE

        Args:
            entity: Suggestion do zapisania

        Returns:
            Suggestion z ustawionym ID (dla nowo utworzonych)

        Raises:
            ValidationError: Jeśli brak wymaganych pól
        """
        if not entity.author or not entity.content:
            raise ValidationError("Suggestion must have author and content")

        if not entity.title:
            # Auto-generate title z pierwszych 80 znaków contentu
            entity.title = entity.content[:80].split("\n")[0]

        conn = self._get_connection()
        try:
            row_data = self._entity_to_row(entity)

            if entity.is_persisted():
                # UPDATE
                conn.execute(
                    """UPDATE suggestions
                       SET author = ?, title = ?, content = ?, type = ?, status = ?,
                           backlog_id = ?, session_id = ?
                       WHERE id = ?""",
                    (row_data["author"], row_data["title"], row_data["content"],
                     row_data["type"], row_data["status"], row_data["backlog_id"],
                     row_data["session_id"], entity.id)
                )
            else:
                # INSERT
                cursor = conn.execute(
                    """INSERT INTO suggestions (author, title, content, type, status, backlog_id, session_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row_data["author"], row_data["title"], row_data["content"],
                     row_data["type"], row_data["status"], row_data["backlog_id"],
                     row_data["session_id"], row_data["created_at"])
                )
                entity.id = cursor.lastrowid

            conn.commit()
            return entity
        finally:
            conn.close()

    def delete(self, id: int) -> bool:
        """
        Usuwa Suggestion po ID.

        Args:
            id: ID sugestii do usunięcia

        Returns:
            True jeśli usunięto, False jeśli sugestia nie istniała
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("DELETE FROM suggestions WHERE id = ?", (id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def find_all(self) -> List[Suggestion]:
        """
        Pobiera wszystkie sugestie.

        Returns:
            Lista Suggestion (pusta jeśli brak), posortowana po created_at DESC

        Note:
            Może zwrócić tysiące rekordów — używaj ostrożnie
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, author, recipients, title, content, type, status, backlog_id,
                          session_id, created_at
                   FROM suggestions
                   ORDER BY created_at DESC, id DESC"""
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def find_by_status(self, status: SuggestionStatus) -> List[Suggestion]:
        """
        Pobiera sugestie po statusie.

        Args:
            status: Status do filtrowania (SuggestionStatus enum)

        Returns:
            Lista Suggestion o podanym statusie
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, author, recipients, title, content, type, status, backlog_id,
                          session_id, created_at
                   FROM suggestions
                   WHERE status = ?
                   ORDER BY created_at DESC, id DESC""",
                (status.value,)
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def find_by_author(self, author: str) -> List[Suggestion]:
        """
        Pobiera sugestie po autorze.

        Args:
            author: Autor sugestii (np. "developer", "erp_specialist")

        Returns:
            Lista Suggestion od podanego autora
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, author, recipients, title, content, type, status, backlog_id,
                          session_id, created_at
                   FROM suggestions
                   WHERE author = ?
                   ORDER BY created_at DESC, id DESC""",
                (author,)
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def find_by_type(self, type: SuggestionType) -> List[Suggestion]:
        """
        Pobiera sugestie po typie.

        Args:
            type: Typ sugestii (SuggestionType enum)

        Returns:
            Lista Suggestion o podanym typie
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, author, recipients, title, content, type, status, backlog_id,
                          session_id, created_at
                   FROM suggestions
                   WHERE type = ?
                   ORDER BY created_at DESC, id DESC""",
                (type.value,)
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]
        finally:
            conn.close()
