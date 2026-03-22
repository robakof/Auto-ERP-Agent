"""
Repository dla encji Suggestion.

Mapowanie między Suggestion (domain model) a tabela suggestions (SQLite).
"""

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from .base import Repository
from ..entities.messaging import Suggestion, SuggestionStatus, SuggestionType
from ..exceptions import NotFoundError, ValidationError, PersistenceError


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

    def __init__(self, db_path: str = "mrowisko.db", conn: Optional[sqlite3.Connection] = None):
        """
        Args:
            db_path: Ścieżka do bazy SQLite (domyślnie mrowisko.db w root)
            conn: Optional shared connection (for transaction support).
                  If provided, repository uses it and does NOT commit/close.
                  If None, repository creates own connection and commits.
        """
        self.db_path = db_path
        self._shared_conn = conn
        self._ensure_table_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """Tworzy połączenie z bazą danych."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pozwala na dostęp do kolumn po nazwie
        return conn

    @contextmanager
    def _connection(self):
        """
        Context manager dla połączenia z bazą danych.

        Transaction-aware:
        - Jeśli shared connection (self._shared_conn) → używa go, NIE commituje, NIE zamyka
          (zarządza tym AgentBus transaction context)
        - Jeśli brak shared connection → tworzy własne, commituje, zamyka (standalone mode)

        Automatycznie:
        - rollbackuje przy wyjątku (tylko standalone mode)
        - tłumaczy wyjątki SQLite na domenowe

        Example:
            with self._connection() as conn:
                conn.execute("INSERT INTO ...")
                # Auto-commit tylko jeśli standalone
        """
        if self._shared_conn:
            # Transaction mode - używaj shared connection
            # NIE commituj, NIE zamykaj (zarządza tym AgentBus)
            try:
                yield self._shared_conn
            except sqlite3.IntegrityError as e:
                raise ValidationError(f"Integrity constraint violation: {e}")
            except sqlite3.OperationalError as e:
                raise PersistenceError(f"Database operation failed: {e}")
            except sqlite3.DatabaseError as e:
                raise PersistenceError(f"Database error: {e}")
        else:
            # Standalone mode - własne połączenie
            conn = self._get_connection()
            try:
                yield conn
                conn.commit()
            except sqlite3.IntegrityError as e:
                conn.rollback()
                raise ValidationError(f"Integrity constraint violation: {e}")
            except sqlite3.OperationalError as e:
                conn.rollback()
                raise PersistenceError(f"Database operation failed: {e}")
            except sqlite3.DatabaseError as e:
                conn.rollback()
                raise PersistenceError(f"Database error: {e}")
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

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

        Raises:
            ValidationError: Jeśli nieprawidłowa wartość enuma w bazie
        """
        try:
            type_enum = SuggestionType(row["type"])
            status_enum = SuggestionStatus(row["status"])
        except ValueError as e:
            raise ValidationError(f"Invalid enum value in database: {e}")

        # Deserialize recipients from JSON
        recipients = None
        if row["recipients"]:
            try:
                recipients = json.loads(row["recipients"])
            except (json.JSONDecodeError, TypeError):
                recipients = None

        return Suggestion(
            author=row["author"],
            content=row["content"],
            title=row["title"],
            type=type_enum,
            status=status_enum,
            recipients=recipients,
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
        # Serialize recipients to JSON
        recipients_json = None
        if entity.recipients:
            recipients_json = json.dumps(entity.recipients, ensure_ascii=False)

        return {
            "author": entity.author,
            "recipients": recipients_json,
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
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT id, author, recipients, title, content, type, status, backlog_id,
                          session_id, created_at
                   FROM suggestions
                   WHERE id = ?""",
                (id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None

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
            raise ValidationError("Suggestion must have a title (auto-generated in __post_init__)")

        with self._connection() as conn:
            row_data = self._entity_to_row(entity)

            if entity.is_persisted():
                # UPDATE
                conn.execute(
                    """UPDATE suggestions
                       SET author = ?, recipients = ?, title = ?, content = ?, type = ?,
                           status = ?, backlog_id = ?, session_id = ?
                       WHERE id = ?""",
                    (row_data["author"], row_data["recipients"], row_data["title"],
                     row_data["content"], row_data["type"], row_data["status"],
                     row_data["backlog_id"], row_data["session_id"], entity.id)
                )
            else:
                # INSERT
                cursor = conn.execute(
                    """INSERT INTO suggestions (author, recipients, title, content, type, status, backlog_id, session_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row_data["author"], row_data["recipients"], row_data["title"],
                     row_data["content"], row_data["type"], row_data["status"],
                     row_data["backlog_id"], row_data["session_id"], row_data["created_at"])
                )
                entity.id = cursor.lastrowid

            return entity

    def delete(self, id: int) -> bool:
        """
        Usuwa Suggestion po ID.

        Args:
            id: ID sugestii do usunięcia

        Returns:
            True jeśli usunięto, False jeśli sugestia nie istniała
        """
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM suggestions WHERE id = ?", (id,))
            return cursor.rowcount > 0

    def exists(self, id: int) -> bool:
        """
        Sprawdza czy Suggestion o podanym ID istnieje.

        Args:
            id: ID sugestii

        Returns:
            True jeśli sugestia istnieje, False jeśli nie
        """
        with self._connection() as conn:
            cursor = conn.execute("SELECT 1 FROM suggestions WHERE id = ? LIMIT 1", (id,))
            return cursor.fetchone() is not None

    def find_all(self) -> List[Suggestion]:
        """
        Pobiera wszystkie sugestie.

        Returns:
            Lista Suggestion (pusta jeśli brak), posortowana po created_at DESC

        Note:
            Może zwrócić tysiące rekordów — używaj ostrożnie
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT id, author, recipients, title, content, type, status, backlog_id,
                          session_id, created_at
                   FROM suggestions
                   ORDER BY created_at DESC, id DESC"""
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def _find_by(self, field: str, value) -> List[Suggestion]:
        """
        Generic query method dla prostych WHERE field = value.

        Args:
            field: Nazwa kolumny (np. "status", "author", "type")
            value: Wartość do filtrowania

        Returns:
            Lista Suggestion spełniających warunek
        """
        with self._connection() as conn:
            cursor = conn.execute(
                f"""SELECT id, author, recipients, title, content, type, status, backlog_id,
                           session_id, created_at
                    FROM suggestions
                    WHERE {field} = ?
                    ORDER BY created_at DESC, id DESC""",
                (value,)
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def find_by_status(self, status: SuggestionStatus) -> List[Suggestion]:
        """
        Pobiera sugestie po statusie.

        Args:
            status: Status do filtrowania (SuggestionStatus enum)

        Returns:
            Lista Suggestion o podanym statusie
        """
        return self._find_by("status", status.value)

    def find_by_author(self, author: str) -> List[Suggestion]:
        """
        Pobiera sugestie po autorze.

        Args:
            author: Autor sugestii (np. "developer", "erp_specialist")

        Returns:
            Lista Suggestion od podanego autora
        """
        return self._find_by("author", author)

    def find_by_type(self, type: SuggestionType) -> List[Suggestion]:
        """
        Pobiera sugestie po typie.

        Args:
            type: Typ sugestii (SuggestionType enum)

        Returns:
            Lista Suggestion o podanym typie
        """
        return self._find_by("type", type.value)
