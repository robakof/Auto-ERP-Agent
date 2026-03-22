"""
Klasy bazowe dla encji domenowych.

Entity — bazowa klasa dla wszystkich encji z ID.
Status — bazowy enum dla statusów.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Status(Enum):
    """
    Bazowy enum dla statusów encji.

    Klasy potomne definiują konkretne wartości statusów.
    """
    pass


@dataclass
class Entity:
    """
    Bazowa klasa dla wszystkich encji domenowych z ID.

    Attributes:
        id: Identyfikator encji w bazie danych (None = nie zapisana)
        created_at: Timestamp utworzenia encji

    Usage:
        >>> @dataclass
        ... class User(Entity):
        ...     name: str
        ...     email: str
        >>>
        >>> user = User(name="Alice", email="alice@example.com")
        >>> user.is_persisted()
        False
        >>> user.id = 1
        >>> user.is_persisted()
        True
    """

    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def is_persisted(self) -> bool:
        """
        Sprawdza czy encja została zapisana do bazy danych.

        Returns:
            True jeśli encja ma ID (została zapisana), False w przeciwnym razie
        """
        return self.id is not None
