"""
Core entities — encje domenowe projektu.

Moduły:
- base: Entity, Status — klasy bazowe
- messaging: Message, Suggestion, BacklogItem — komunikacja między agentami
- agents: Role, Session, Agent, LiveAgent — agenci i sesje (Milestone 4)
- bot: User, Query, QueryResult, Conversation — bot Telegram (Milestone 5)
"""

# Milestone 1 exports
from .base import Entity, Status
from .messaging import (
    Message, MessageStatus, MessageType,
    Suggestion, SuggestionStatus, SuggestionType,
    BacklogItem, BacklogArea, BacklogStatus, BacklogValue, BacklogEffort
)

__all__ = [
    # Base
    "Entity",
    "Status",
    # Message
    "Message",
    "MessageStatus",
    "MessageType",
    # Suggestion
    "Suggestion",
    "SuggestionStatus",
    "SuggestionType",
    # BacklogItem
    "BacklogItem",
    "BacklogArea",
    "BacklogStatus",
    "BacklogValue",
    "BacklogEffort",
]
