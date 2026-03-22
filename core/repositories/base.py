"""
Bazowa abstrakcja repozytorium dla persystencji encji.

Repository[T] — interfejs CRUD dla encji typu T.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

from ..entities.base import Entity

T = TypeVar('T', bound=Entity)


class Repository(ABC, Generic[T]):
    """
    Bazowy interfejs repozytorium dla encji.

    Wzorzec Repository oddziela logikę biznesową od persystencji.
    Każda encja ma swoje repozytorium implementujące ten interfejs.

    Type parameter T musi być podtypem Entity.

    Example:
        >>> class UserRepository(Repository[User]):
        ...     def get(self, id: int) -> Optional[User]:
        ...         # SQL query
        ...         pass
        ...
        ...     def save(self, entity: User) -> User:
        ...         # INSERT or UPDATE
        ...         pass
    """

    @abstractmethod
    def get(self, id: int) -> Optional[T]:
        """
        Pobiera encję po ID.

        Args:
            id: Identyfikator encji

        Returns:
            Encja jeśli istnieje, None jeśli nie znaleziono

        Raises:
            NotFoundError: Opcjonalnie, zamiast zwracać None
        """
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Zapisuje encję do bazy danych.

        Jeśli encja.is_persisted() == False (id is None) → INSERT
        Jeśli encja.is_persisted() == True → UPDATE

        Args:
            entity: Encja do zapisania

        Returns:
            Encja z ustawionym id (dla nowo utworzonych)

        Raises:
            ValidationError: Jeśli dane encji są nieprawidłowe
        """
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Usuwa encję po ID.

        Args:
            id: Identyfikator encji do usunięcia

        Returns:
            True jeśli usunięto, False jeśli encja nie istniała

        Raises:
            NotFoundError: Opcjonalnie, jeśli encja nie istnieje
        """
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """
        Pobiera wszystkie encje danego typu.

        Returns:
            Lista encji (pusta jeśli brak)

        Note:
            Używaj ostrożnie — może zwrócić tysiące rekordów
        """
        pass
