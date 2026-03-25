"""
Repository dla encji Message.

Mapowanie między Message (domain model) a tabela messages (SQLite).
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from ..entities.messaging import Message, MessageStatus, MessageType
from ..exceptions import PersistenceError, ValidationError
from .base import Repository


class MessageRepository(Repository[Message]):
    """
    Repository dla Message — persystencja do SQLite.

    Tabela: messages
    Schema: id, sender, recipient, content, type, status, session_id, created_at, read_at

    Example:
        >>> repo = MessageRepository("mrowisko.db")
        >>> msg = Message(sender="developer", recipient="analyst", content="Check data")
        >>> msg = repo.save(msg)
        >>> msg.id  # Auto-generated
        42
    """

    def __init__(self, db_path: str = "mrowisko.db", conn: Optional[sqlite3.Connection] = None):
        """
        Args:
            db_path: Ścieżka do bazy SQLite (domyślnie mrowisko.db w root)
            conn: Opcjonalne zewnętrzne połączenie (dla transaction support w AgentBus)
        """
        self._db_path = db_path
        self._external_conn = conn  # Shared connection from AgentBus transaction
        # Tylko tworzymy tabelę gdy standalone mode (nie w transaction)
        if not conn:
            self._ensure_table_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Zwraca połączenie z bazą danych.

        Jeśli repository ma zewnętrzne połączenie (transaction mode) — używa go.
        W przeciwnym razie tworzy nowe połączenie (standalone mode).
        """
        if self._external_conn:
            return self._external_conn
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _connection(self):
        """
        Context manager dla połączenia z bazą danych.

        Transaction-aware:
        - Jeśli repository ma external_conn (transaction mode):
          używa go, NIE commituje, NIE zamyka (zarządza tym AgentBus)
        - Jeśli standalone mode:
          tworzy własne połączenie, commituje, zamyka

        Error handling:
        - IntegrityError → ValidationError
        - OperationalError, DatabaseError → PersistenceError
        - Rollback tylko w standalone mode
        """
        conn = self._get_connection()
        shared_conn = (self._external_conn is not None)

        try:
            yield conn
            # Commit tylko jeśli standalone mode (nie transaction)
            if not shared_conn:
                conn.commit()
        except sqlite3.IntegrityError as e:
            if not shared_conn:
                conn.rollback()
            raise ValidationError(f"Integrity constraint violation: {e}")
        except sqlite3.OperationalError as e:
            if not shared_conn:
                conn.rollback()
            raise PersistenceError(f"Database operation failed: {e}")
        except sqlite3.DatabaseError as e:
            if not shared_conn:
                conn.rollback()
            raise PersistenceError(f"Database error: {e}")
        except Exception:
            if not shared_conn:
                conn.rollback()
            raise
        finally:
            # Zamykamy tylko jeśli standalone mode
            if not shared_conn:
                conn.close()

    def _ensure_table_exists(self) -> None:
        """
        Upewnia się że tabela messages istnieje.

        Note: W produkcji tabela już istnieje (utworzona przez agent_bus).
        Ta metoda jest safety net dla testów.
        """
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT DEFAULT 'direct',
                    status TEXT DEFAULT 'unread',
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    read_at DATETIME,
                    claimed_by TEXT
                )
            """)

    def _row_to_entity(self, row: sqlite3.Row) -> Message:
        """
        Konwertuje wiersz z DB na encję Message.

        Args:
            row: Wiersz z sqlite3 (Row object)

        Returns:
            Message z danymi z DB

        Raises:
            ValidationError: Jeśli nieprawidłowa wartość enuma w bazie
        """
        # Graceful degradation: mapowanie legacy wartości type
        TYPE_ALIASES = {
            "flag_human": "escalation",
            "info": "direct",
        }

        # Graceful degradation: 'claimed' → 'unread' (legacy status leak)
        STATUS_ALIASES = {
            "claimed": "unread",
        }

        try:
            type_raw = row["type"]
            type_normalized = TYPE_ALIASES.get(type_raw, type_raw)
            type_enum = MessageType(type_normalized)
            status_raw = row["status"]
            status_normalized = STATUS_ALIASES.get(status_raw, status_raw)
            status_enum = MessageStatus(status_normalized)
        except ValueError as e:
            raise ValidationError(f"Invalid enum value in database: {e}")

        # Backward compat: title może nie istnieć w starych DB
        try:
            title = row["title"]
        except (KeyError, IndexError):
            title = ""

        # Backward compat: claimed_by może nie istnieć w starych DB
        try:
            claimed_by = row["claimed_by"]
        except (KeyError, IndexError):
            claimed_by = None

        return Message(
            sender=row["sender"],
            recipient=row["recipient"],
            content=row["content"],
            title=title,
            type=type_enum,
            status=status_enum,
            session_id=row["session_id"],
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            read_at=datetime.fromisoformat(row["read_at"]) if row["read_at"] else None,
            claimed_by=claimed_by
        )

    def _entity_to_row(self, entity: Message) -> dict:
        """
        Konwertuje encję Message na dict dla DB.

        Args:
            entity: Message do zapisu

        Returns:
            Dict z danymi gotowymi do INSERT/UPDATE
        """
        return {
            "sender": entity.sender,
            "recipient": entity.recipient,
            "content": entity.content,
            "title": entity.title,
            "type": entity.type.value,
            "status": entity.status.value,
            "session_id": entity.session_id,
            "created_at": entity.created_at.isoformat(),
            "read_at": entity.read_at.isoformat() if entity.read_at else None,
            "claimed_by": entity.claimed_by
        }

    def get(self, id: int) -> Optional[Message]:
        """
        Pobiera Message po ID.

        Args:
            id: ID wiadomości

        Returns:
            Message jeśli istnieje, None jeśli nie znaleziono
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT id, sender, recipient, content, title, type, status, session_id,
                          created_at, read_at, claimed_by
                   FROM messages
                   WHERE id = ?""",
                (id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None

    def save(self, entity: Message) -> Message:
        """
        Zapisuje Message do bazy.

        Jeśli entity.id is None → INSERT
        Jeśli entity.id is not None → UPDATE

        Args:
            entity: Message do zapisania

        Returns:
            Message z ustawionym ID

        Raises:
            ValidationError: Jeśli brak wymaganych pól
        """
        if not entity.sender or not entity.recipient or not entity.content:
            raise ValidationError("Message must have sender, recipient, and content")

        with self._connection() as conn:
            row_data = self._entity_to_row(entity)

            if entity.is_persisted():
                # UPDATE
                conn.execute(
                    """UPDATE messages
                       SET sender = ?, recipient = ?, content = ?, title = ?, type = ?, status = ?,
                           session_id = ?, read_at = ?, claimed_by = ?
                       WHERE id = ?""",
                    (row_data["sender"], row_data["recipient"], row_data["content"], row_data["title"],
                     row_data["type"], row_data["status"], row_data["session_id"],
                     row_data["read_at"], row_data["claimed_by"], entity.id)
                )
            else:
                # INSERT
                cursor = conn.execute(
                    """INSERT INTO messages (sender, recipient, content, title, type, status, session_id, read_at, claimed_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row_data["sender"], row_data["recipient"], row_data["content"], row_data["title"],
                     row_data["type"], row_data["status"], row_data["session_id"],
                     row_data["read_at"], row_data["claimed_by"])
                )
                entity.id = cursor.lastrowid

                # Read created_at from DB (uses DEFAULT datetime('now') = UTC)
                row = conn.execute("SELECT created_at FROM messages WHERE id = ?", (entity.id,)).fetchone()
                entity.created_at = datetime.fromisoformat(row["created_at"])

            return entity

    def delete(self, id: int) -> bool:
        """
        Usuwa Message po ID.

        Args:
            id: ID wiadomości do usunięcia

        Returns:
            True jeśli usunięto, False jeśli wiadomość nie istniała
        """
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM messages WHERE id = ?", (id,))
            return cursor.rowcount > 0

    def exists(self, id: int) -> bool:
        """
        Sprawdza czy Message o podanym ID istnieje.

        Args:
            id: ID wiadomości

        Returns:
            True jeśli wiadomość istnieje, False jeśli nie
        """
        with self._connection() as conn:
            cursor = conn.execute("SELECT 1 FROM messages WHERE id = ? LIMIT 1", (id,))
            return cursor.fetchone() is not None

    def find_all(self) -> List[Message]:
        """
        Pobiera wszystkie wiadomości.

        Returns:
            Lista Message (pusta jeśli brak), posortowana po created_at DESC

        Note:
            Może zwrócić tysiące rekordów — używaj ostrożnie
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT id, sender, recipient, content, title, type, status, session_id,
                          created_at, read_at, claimed_by
                   FROM messages
                   ORDER BY created_at DESC, id DESC"""
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def _find_by(self, field: str, value) -> List[Message]:
        """
        Generic query method dla prostych WHERE field = value.

        Args:
            field: Nazwa kolumny (np. "status", "sender", "recipient")
            value: Wartość do filtrowania

        Returns:
            Lista Message spełniających warunek
        """
        with self._connection() as conn:
            cursor = conn.execute(
                f"""SELECT id, sender, recipient, content, title, type, status, session_id,
                           created_at, read_at, claimed_by
                    FROM messages
                    WHERE {field} = ?
                    ORDER BY created_at DESC, id DESC""",
                (value,)
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def find_by_status(self, status: MessageStatus) -> List[Message]:
        """
        Pobiera wiadomości po statusie.

        Args:
            status: Status do filtrowania (MessageStatus enum)

        Returns:
            Lista Message o podanym statusie
        """
        return self._find_by("status", status.value)

    def find_by_recipient(self, recipient: str) -> List[Message]:
        """
        Pobiera wiadomości po odbiorcy.

        Args:
            recipient: Nazwa roli odbiorcy (np. "developer", "analyst")

        Returns:
            Lista Message dla podanego odbiorcy
        """
        return self._find_by("recipient", recipient)

    def find_by_sender(self, sender: str) -> List[Message]:
        """
        Pobiera wiadomości po nadawcy.

        Args:
            sender: Nazwa roli nadawcy (np. "architect", "erp_specialist")

        Returns:
            Lista Message od podanego nadawcy
        """
        return self._find_by("sender", sender)
