"""
Repository dla encji BacklogItem.

Mapowanie między BacklogItem (domain model) a tabela backlog (SQLite).
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from ..entities.messaging import BacklogArea, BacklogEffort, BacklogItem, BacklogStatus, BacklogValue
from ..exceptions import PersistenceError, ValidationError
from .base import Repository


class BacklogRepository(Repository[BacklogItem]):
    """
    Repository dla BacklogItem — persystencja do SQLite.

    Tabela: backlog
    Schema: id, title, content, area, status, value, effort, source_id, created_at, updated_at

    Example:
        >>> repo = BacklogRepository("mrowisko.db")
        >>> item = BacklogItem(title="Fix bug", content="Details...", area=BacklogArea.DEV)
        >>> item = repo.save(item)
        >>> item.id  # Auto-generated
        42
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
        conn.row_factory = sqlite3.Row
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
        Upewnia się że tabela backlog istnieje.

        Note: W produkcji tabela już istnieje (utworzona przez agent_bus).
        Ta metoda jest safety net dla testów.
        """
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backlog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT DEFAULT '',
                    area TEXT,
                    status TEXT DEFAULT 'planned',
                    value TEXT,
                    effort TEXT,
                    source_id INTEGER,
                    depends_on INTEGER REFERENCES backlog(id),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """)

    def _row_to_entity(self, row: sqlite3.Row) -> BacklogItem:
        """
        Konwertuje wiersz z DB na encję BacklogItem.

        Args:
            row: Wiersz z sqlite3 (Row object)

        Returns:
            BacklogItem z danymi z DB

        Raises:
            ValidationError: Jeśli nieprawidłowa wartość enuma w bazie
        """
        # Graceful degradation: mapowanie wariantów kodowania (legacy data)
        VALUE_ALIASES = {"średnia": "srednia", "�rednia": "srednia"}
        EFFORT_ALIASES = {
            "mała": "mala", "ma�a": "mala",
            "średnia": "srednia", "�rednia": "srednia",
            "duża": "duza", "du�a": "duza",
        }

        try:
            area_enum = BacklogArea(row["area"]) if row["area"] else None
            status_enum = BacklogStatus(row["status"])

            # Optional fields: graceful degradation dla nieprawidłowych wartości
            value_raw = row["value"]
            if value_raw:
                value_normalized = VALUE_ALIASES.get(value_raw, value_raw)
                try:
                    value_enum = BacklogValue(value_normalized)
                except ValueError:
                    value_enum = None  # Unknown value - keep as None
            else:
                value_enum = None

            effort_raw = row["effort"]
            if effort_raw:
                effort_normalized = EFFORT_ALIASES.get(effort_raw, effort_raw)
                try:
                    effort_enum = BacklogEffort(effort_normalized)
                except ValueError:
                    effort_enum = None  # Unknown effort - keep as None
            else:
                effort_enum = None

        except ValueError as e:
            raise ValidationError(f"Invalid enum value in database: {e}")

        # depends_on: graceful degradation for DBs without the column yet
        try:
            depends_on = row["depends_on"]
        except (IndexError, KeyError):
            depends_on = None

        return BacklogItem(
            title=row["title"],
            content=row["content"] or "",
            area=area_enum,
            status=status_enum,
            value=value_enum,
            effort=effort_enum,
            source_id=row["source_id"],
            depends_on=depends_on,
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )

    def _entity_to_row(self, entity: BacklogItem) -> dict:
        """
        Konwertuje encję BacklogItem na dict dla DB.

        Args:
            entity: BacklogItem do zapisu

        Returns:
            Dict z danymi gotowymi do INSERT/UPDATE
        """
        return {
            "title": entity.title,
            "content": entity.content,
            "area": entity.area.value if entity.area else None,
            "status": entity.status.value,
            "value": entity.value.value if entity.value else None,
            "effort": entity.effort.value if entity.effort else None,
            "source_id": entity.source_id,
            "depends_on": entity.depends_on,
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None
        }

    def get(self, id: int) -> Optional[BacklogItem]:
        """
        Pobiera BacklogItem po ID.

        Args:
            id: ID zadania

        Returns:
            BacklogItem jeśli istnieje, None jeśli nie znaleziono
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT id, title, content, area, status, value, effort, source_id, depends_on,
                          created_at, updated_at
                   FROM backlog
                   WHERE id = ?""",
                (id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None

    def save(self, entity: BacklogItem) -> BacklogItem:
        """
        Zapisuje BacklogItem do bazy.

        Jeśli entity.id is None → INSERT
        Jeśli entity.id is not None → UPDATE (auto-update updated_at)

        Args:
            entity: BacklogItem do zapisania

        Returns:
            BacklogItem z ustawionym ID

        Raises:
            ValidationError: Jeśli brak wymaganych pól
        """
        if not entity.title:
            raise ValidationError("BacklogItem must have a title")

        # Auto-update updated_at przy zapisie (INSERT i UPDATE)
        entity.updated_at = datetime.now()

        with self._connection() as conn:
            row_data = self._entity_to_row(entity)

            if entity.is_persisted():
                # UPDATE
                conn.execute(
                    """UPDATE backlog
                       SET title = ?, content = ?, area = ?, status = ?, value = ?,
                           effort = ?, source_id = ?, depends_on = ?, updated_at = ?
                       WHERE id = ?""",
                    (row_data["title"], row_data["content"], row_data["area"],
                     row_data["status"], row_data["value"], row_data["effort"],
                     row_data["source_id"], row_data["depends_on"], row_data["updated_at"], entity.id)
                )
            else:
                # INSERT
                cursor = conn.execute(
                    """INSERT INTO backlog (title, content, area, status, value, effort, source_id, depends_on, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (row_data["title"], row_data["content"], row_data["area"],
                     row_data["status"], row_data["value"], row_data["effort"],
                     row_data["source_id"], row_data["depends_on"], row_data["created_at"], row_data["updated_at"])
                )
                entity.id = cursor.lastrowid

            return entity

    def delete(self, id: int) -> bool:
        """
        Usuwa BacklogItem po ID.

        Args:
            id: ID zadania do usunięcia

        Returns:
            True jeśli usunięto, False jeśli zadanie nie istniało
        """
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM backlog WHERE id = ?", (id,))
            return cursor.rowcount > 0

    def exists(self, id: int) -> bool:
        """
        Sprawdza czy BacklogItem o podanym ID istnieje.

        Args:
            id: ID zadania

        Returns:
            True jeśli zadanie istnieje, False jeśli nie
        """
        with self._connection() as conn:
            cursor = conn.execute("SELECT 1 FROM backlog WHERE id = ? LIMIT 1", (id,))
            return cursor.fetchone() is not None

    def find_all(self) -> List[BacklogItem]:
        """
        Pobiera wszystkie zadania.

        Returns:
            Lista BacklogItem (pusta jeśli brak), posortowana po created_at DESC

        Note:
            Może zwrócić tysiące rekordów — używaj ostrożnie
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """SELECT id, title, content, area, status, value, effort, source_id, depends_on,
                          created_at, updated_at
                   FROM backlog
                   ORDER BY created_at DESC, id DESC"""
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def _find_by(self, field: str, value) -> List[BacklogItem]:
        """
        Generic query method dla prostych WHERE field = value.

        Args:
            field: Nazwa kolumny (np. "status", "area")
            value: Wartość do filtrowania

        Returns:
            Lista BacklogItem spełniających warunek
        """
        with self._connection() as conn:
            cursor = conn.execute(
                f"""SELECT id, title, content, area, status, value, effort, source_id,
                           created_at, updated_at
                    FROM backlog
                    WHERE {field} = ?
                    ORDER BY created_at DESC, id DESC""",
                (value,)
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def find_by_status(self, status: BacklogStatus) -> List[BacklogItem]:
        """
        Pobiera zadania po statusie.

        Args:
            status: Status do filtrowania (BacklogStatus enum)

        Returns:
            Lista BacklogItem o podanym statusie
        """
        return self._find_by("status", status.value)

    def find_by_area(self, area: BacklogArea) -> List[BacklogItem]:
        """
        Pobiera zadania po obszarze.

        Args:
            area: Obszar do filtrowania (BacklogArea enum)

        Returns:
            Lista BacklogItem z podanego obszaru
        """
        return self._find_by("area", area.value)
