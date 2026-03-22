"""
Encje domenowe dla komunikacji między agentami.

Zawiera:
- Message — wiadomość agent→agent
- Suggestion — sugestia/obserwacja od agenta
- BacklogItem — zadanie w backlogu
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from .base import Entity
from ..exceptions import InvalidStateError


# ============================================================================
# Message
# ============================================================================

class MessageStatus(Enum):
    """Status wiadomości."""
    UNREAD = "unread"
    READ = "read"


class MessageType(Enum):
    """Typ wiadomości."""
    DIRECT = "direct"
    SUGGESTION = "suggestion"
    TASK = "task"
    ESCALATION = "escalation"


@dataclass
class Message(Entity):
    """
    Wiadomość między agentami.

    Attributes:
        sender: Rola nadawcy (np. "developer", "erp_specialist")
        recipient: Rola odbiorcy (np. "analyst", "human")
        content: Treść wiadomości
        type: Typ wiadomości
        status: Status (unread/read)
        session_id: ID sesji nadawcy (opcjonalnie)
        read_at: Timestamp przeczytania (opcjonalnie)

    Example:
        >>> msg = Message(sender="developer", recipient="analyst", content="Sprawdź dane")
        >>> msg.mark_read()
        >>> msg.status
        <MessageStatus.READ: 'read'>
    """

    sender: str
    recipient: str
    content: str
    type: MessageType = MessageType.DIRECT
    status: MessageStatus = MessageStatus.UNREAD
    session_id: Optional[str] = None
    read_at: Optional[datetime] = None

    def mark_read(self) -> None:
        """
        Oznacza wiadomość jako przeczytaną.

        Raises:
            InvalidStateError: Jeśli wiadomość już jest przeczytana
        """
        if self.status == MessageStatus.READ:
            raise InvalidStateError(f"Message {self.id} is already read")

        self.status = MessageStatus.READ
        self.read_at = datetime.now()

    def reply(self, content: str) -> "Message":
        """
        Tworzy wiadomość zwrotną.

        Args:
            content: Treść odpowiedzi

        Returns:
            Nowa wiadomość z odwróconymi sender/recipient
        """
        return Message(
            sender=self.recipient,
            recipient=self.sender,
            content=content,
            type=self.type
        )


# ============================================================================
# Suggestion
# ============================================================================

class SuggestionStatus(Enum):
    """Status sugestii."""
    OPEN = "open"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class SuggestionType(Enum):
    """Typ sugestii."""
    RULE = "rule"          # Zasada do wdrożenia
    TOOL = "tool"          # Propozycja narzędzia
    DISCOVERY = "discovery"  # Odkrycie techniczne
    OBSERVATION = "observation"  # Spostrzeżenie procesowe


@dataclass
class Suggestion(Entity):
    """
    Sugestia/obserwacja od agenta.

    Attributes:
        author: Rola autora (np. "erp_specialist")
        content: Treść sugestii
        title: Krótki tytuł (opcjonalnie)
        type: Typ sugestii
        status: Status (open/implemented/rejected/deferred)
        backlog_id: ID powiązanego zadania w backlogu (jeśli wdrożone)
        session_id: ID sesji w której powstała sugestia

    Example:
        >>> suggestion = Suggestion(
        ...     author="developer",
        ...     content="Dodać indeks do tabeli X",
        ...     title="Indeks dla tabeli X",
        ...     type=SuggestionType.TOOL
        ... )
        >>> suggestion.implement(backlog_id=42)
        >>> suggestion.status
        <SuggestionStatus.IMPLEMENTED: 'implemented'>
    """

    author: str
    content: str
    title: str = ""
    type: SuggestionType = SuggestionType.OBSERVATION
    status: SuggestionStatus = SuggestionStatus.OPEN
    backlog_id: Optional[int] = None
    session_id: Optional[str] = None

    def implement(self, backlog_id: Optional[int] = None) -> None:
        """
        Oznacza sugestię jako wdrożoną.

        Args:
            backlog_id: ID zadania w backlogu (opcjonalnie)

        Raises:
            InvalidStateError: Jeśli sugestia nie jest w statusie OPEN
        """
        if self.status != SuggestionStatus.OPEN:
            raise InvalidStateError(
                f"Cannot implement suggestion in status {self.status.value}"
            )

        self.status = SuggestionStatus.IMPLEMENTED
        self.backlog_id = backlog_id

    def reject(self) -> None:
        """
        Odrzuca sugestię.

        Raises:
            InvalidStateError: Jeśli sugestia nie jest w statusie OPEN
        """
        if self.status != SuggestionStatus.OPEN:
            raise InvalidStateError(
                f"Cannot reject suggestion in status {self.status.value}"
            )

        self.status = SuggestionStatus.REJECTED

    def defer(self) -> None:
        """Odkłada sugestię na później."""
        self.status = SuggestionStatus.DEFERRED


# ============================================================================
# BacklogItem
# ============================================================================

class BacklogArea(Enum):
    """Obszar zadania w backlogu."""
    BOT = "Bot"
    DEV = "Dev"
    ARCH = "Arch"
    ERP = "ERP"


class BacklogStatus(Enum):
    """Status zadania w backlogu."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class BacklogValue(Enum):
    """Wartość biznesowa zadania."""
    HIGH = "wysoka"
    MEDIUM = "srednia"
    LOW = "niska"


class BacklogEffort(Enum):
    """Pracochłonność zadania."""
    SMALL = "mala"
    MEDIUM = "srednia"
    LARGE = "duza"


@dataclass
class BacklogItem(Entity):
    """
    Zadanie w backlogu.

    Attributes:
        title: Tytuł zadania
        content: Szczegółowy opis
        area: Obszar (Bot/Dev/Arch/ERP)
        status: Status (planned/in_progress/done/deferred/cancelled)
        value: Wartość biznesowa
        effort: Pracochłonność
        source_id: ID sugestii która dała początek zadaniu (opcjonalnie)
        updated_at: Timestamp ostatniej aktualizacji

    Example:
        >>> item = BacklogItem(
        ...     title="Dodać indeks do tabeli X",
        ...     content="Tabela X ma wolne query...",
        ...     area=BacklogArea.DEV,
        ...     value=BacklogValue.HIGH,
        ...     effort=BacklogEffort.SMALL
        ... )
        >>> item.start()
        >>> item.status
        <BacklogStatus.IN_PROGRESS: 'in_progress'>
        >>> item.complete()
        >>> item.status
        <BacklogStatus.DONE: 'done'>
    """

    title: str
    content: str = ""
    area: Optional[BacklogArea] = None
    status: BacklogStatus = BacklogStatus.PLANNED
    value: Optional[BacklogValue] = None
    effort: Optional[BacklogEffort] = None
    source_id: Optional[int] = None  # FK do Suggestion
    updated_at: Optional[datetime] = None

    def start(self) -> None:
        """
        Rozpoczyna pracę nad zadaniem.

        Raises:
            InvalidStateError: Jeśli zadanie nie jest w statusie PLANNED lub DEFERRED
        """
        if self.status not in (BacklogStatus.PLANNED, BacklogStatus.DEFERRED):
            raise InvalidStateError(
                f"Cannot start item in status {self.status.value}"
            )

        self.status = BacklogStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def complete(self) -> None:
        """
        Kończy zadanie.

        Raises:
            InvalidStateError: Jeśli zadanie nie jest w statusie IN_PROGRESS
        """
        if self.status != BacklogStatus.IN_PROGRESS:
            raise InvalidStateError(
                f"Cannot complete item not in progress (current: {self.status.value})"
            )

        self.status = BacklogStatus.DONE
        self.updated_at = datetime.now()

    def defer(self) -> None:
        """Odkłada zadanie na później."""
        self.status = BacklogStatus.DEFERRED
        self.updated_at = datetime.now()

    def cancel(self) -> None:
        """Anuluje zadanie."""
        self.status = BacklogStatus.CANCELLED
        self.updated_at = datetime.now()
