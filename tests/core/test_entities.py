"""
Testy jednostkowe dla core/entities/.

Testy pokrywają:
- Entity.is_persisted()
- Message: mark_read(), reply(), edge cases
- Suggestion: implement(), reject(), defer(), edge cases
- BacklogItem: start(), complete(), defer(), cancel(), edge cases
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from datetime import datetime

from core.entities import (
    Entity,
    Message, MessageStatus, MessageType,
    Suggestion, SuggestionStatus, SuggestionType,
    BacklogItem, BacklogArea, BacklogStatus, BacklogValue, BacklogEffort
)
from core.exceptions import InvalidStateError


# ============================================================================
# Entity tests
# ============================================================================

def test_entity_is_persisted():
    """Entity.is_persisted() zwraca False gdy id=None, True gdy id ustawione."""
    entity = Entity()
    assert entity.is_persisted() is False

    entity.id = 1
    assert entity.is_persisted() is True


def test_entity_created_at():
    """Entity ma automatycznie ustawiony created_at."""
    entity = Entity()
    assert isinstance(entity.created_at, datetime)


# ============================================================================
# Message tests
# ============================================================================

def test_message_creation():
    """Message tworzy się z wymaganymi polami."""
    msg = Message(
        sender="developer",
        recipient="analyst",
        content="Test message"
    )

    assert msg.sender == "developer"
    assert msg.recipient == "analyst"
    assert msg.content == "Test message"
    assert msg.status == MessageStatus.UNREAD
    assert msg.type == MessageType.DIRECT
    assert msg.read_at is None


def test_message_mark_read():
    """Message.mark_read() zmienia status na READ i ustawia read_at."""
    msg = Message(sender="dev", recipient="analyst", content="Test")

    msg.mark_read()

    assert msg.status == MessageStatus.READ
    assert isinstance(msg.read_at, datetime)


def test_message_mark_read_already_read():
    """Message.mark_read() rzuca InvalidStateError jeśli już przeczytana."""
    msg = Message(sender="dev", recipient="analyst", content="Test")
    msg.mark_read()

    with pytest.raises(InvalidStateError, match="already read"):
        msg.mark_read()


def test_message_reply():
    """Message.reply() tworzy wiadomość zwrotną z odwróconymi sender/recipient."""
    msg = Message(sender="dev", recipient="analyst", content="Question")

    reply = msg.reply("Answer")

    assert reply.sender == "analyst"
    assert reply.recipient == "dev"
    assert reply.content == "Answer"
    assert reply.type == msg.type


# ============================================================================
# Suggestion tests
# ============================================================================

def test_suggestion_creation():
    """Suggestion tworzy się z wymaganymi polami."""
    suggestion = Suggestion(
        author="erp_specialist",
        content="Add index to table X"
    )

    assert suggestion.author == "erp_specialist"
    assert suggestion.content == "Add index to table X"
    assert suggestion.status == SuggestionStatus.OPEN
    assert suggestion.type == SuggestionType.OBSERVATION


def test_suggestion_implement():
    """Suggestion.implement() zmienia status na IMPLEMENTED."""
    suggestion = Suggestion(author="dev", content="Test")

    suggestion.implement(backlog_id=42)

    assert suggestion.status == SuggestionStatus.IMPLEMENTED
    assert suggestion.backlog_id == 42


def test_suggestion_implement_non_open():
    """Suggestion.implement() rzuca InvalidStateError jeśli status != OPEN."""
    suggestion = Suggestion(author="dev", content="Test")
    suggestion.implement()

    with pytest.raises(InvalidStateError, match="Cannot implement"):
        suggestion.implement()


def test_suggestion_reject():
    """Suggestion.reject() zmienia status na REJECTED."""
    suggestion = Suggestion(author="dev", content="Test")

    suggestion.reject()

    assert suggestion.status == SuggestionStatus.REJECTED


def test_suggestion_reject_non_open():
    """Suggestion.reject() rzuca InvalidStateError jeśli status != OPEN."""
    suggestion = Suggestion(author="dev", content="Test")
    suggestion.reject()

    with pytest.raises(InvalidStateError, match="Cannot reject"):
        suggestion.reject()


def test_suggestion_defer():
    """Suggestion.defer() zmienia status na DEFERRED."""
    suggestion = Suggestion(author="dev", content="Test")

    suggestion.defer()

    assert suggestion.status == SuggestionStatus.DEFERRED


# ============================================================================
# BacklogItem tests
# ============================================================================

def test_backlog_item_creation():
    """BacklogItem tworzy się z wymaganymi polami."""
    item = BacklogItem(
        title="Add feature X",
        content="Details...",
        area=BacklogArea.DEV,
        value=BacklogValue.HIGH,
        effort=BacklogEffort.SMALL
    )

    assert item.title == "Add feature X"
    assert item.content == "Details..."
    assert item.area == BacklogArea.DEV
    assert item.status == BacklogStatus.PLANNED
    assert item.value == BacklogValue.HIGH
    assert item.effort == BacklogEffort.SMALL


def test_backlog_item_start():
    """BacklogItem.start() zmienia status na IN_PROGRESS."""
    item = BacklogItem(title="Task", area=BacklogArea.DEV)

    item.start()

    assert item.status == BacklogStatus.IN_PROGRESS
    assert isinstance(item.updated_at, datetime)


def test_backlog_item_start_from_deferred():
    """BacklogItem.start() działa z statusu DEFERRED."""
    item = BacklogItem(title="Task", area=BacklogArea.DEV)
    item.defer()

    item.start()

    assert item.status == BacklogStatus.IN_PROGRESS


def test_backlog_item_start_invalid_state():
    """BacklogItem.start() rzuca InvalidStateError jeśli status != PLANNED/DEFERRED."""
    item = BacklogItem(title="Task", area=BacklogArea.DEV)
    item.start()

    with pytest.raises(InvalidStateError, match="Cannot start"):
        item.start()


def test_backlog_item_complete():
    """BacklogItem.complete() zmienia status na DONE."""
    item = BacklogItem(title="Task", area=BacklogArea.DEV)
    item.start()

    item.complete()

    assert item.status == BacklogStatus.DONE
    assert isinstance(item.updated_at, datetime)


def test_backlog_item_complete_not_in_progress():
    """BacklogItem.complete() rzuca InvalidStateError jeśli status != IN_PROGRESS."""
    item = BacklogItem(title="Task", area=BacklogArea.DEV)

    with pytest.raises(InvalidStateError, match="Cannot complete"):
        item.complete()


def test_backlog_item_defer():
    """BacklogItem.defer() zmienia status na DEFERRED."""
    item = BacklogItem(title="Task", area=BacklogArea.DEV)

    item.defer()

    assert item.status == BacklogStatus.DEFERRED
    assert isinstance(item.updated_at, datetime)


def test_backlog_item_cancel():
    """BacklogItem.cancel() zmienia status na CANCELLED."""
    item = BacklogItem(title="Task", area=BacklogArea.DEV)

    item.cancel()

    assert item.status == BacklogStatus.CANCELLED
    assert isinstance(item.updated_at, datetime)


# ============================================================================
# Edge cases
# ============================================================================

def test_message_with_custom_type():
    """Message może mieć custom type."""
    msg = Message(
        sender="dev",
        recipient="human",
        content="Urgent!",
        type=MessageType.ESCALATION
    )

    assert msg.type == MessageType.ESCALATION


def test_suggestion_with_custom_type():
    """Suggestion może mieć custom type."""
    suggestion = Suggestion(
        author="dev",
        content="Use tool X",
        type=SuggestionType.TOOL
    )

    assert suggestion.type == SuggestionType.TOOL


def test_backlog_item_minimal():
    """BacklogItem może być utworzony tylko z title."""
    item = BacklogItem(title="Minimal task")

    assert item.title == "Minimal task"
    assert item.content == ""
    assert item.area is None
    assert item.value is None
    assert item.effort is None
