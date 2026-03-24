"""
Testy integracyjne dla core/repositories/.

Testy używają tymczasowej bazy SQLite in-memory.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
from pathlib import Path

from core.entities.messaging import (
    Suggestion, SuggestionStatus, SuggestionType,
    BacklogItem, BacklogArea, BacklogStatus, BacklogValue, BacklogEffort,
    Message, MessageStatus, MessageType
)
from core.repositories.suggestion_repo import SuggestionRepository
from core.repositories.backlog_repo import BacklogRepository
from core.repositories.message_repo import MessageRepository
from core.exceptions import ValidationError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Tworzy tymczasową bazę danych dla testów."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def suggestion_repo(temp_db):
    """Tworzy SuggestionRepository z tymczasową bazą."""
    return SuggestionRepository(db_path=temp_db)


@pytest.fixture
def backlog_repo(temp_db):
    """Tworzy BacklogRepository z tymczasową bazą."""
    return BacklogRepository(db_path=temp_db)


@pytest.fixture
def message_repo(temp_db):
    """Tworzy MessageRepository z tymczasową bazą."""
    return MessageRepository(db_path=temp_db)


# ============================================================================
# SuggestionRepository tests
# ============================================================================

def test_save_new_suggestion(suggestion_repo):
    """save() dla nowej sugestii (INSERT) ustawia ID."""
    suggestion = Suggestion(
        author="developer",
        content="Test suggestion content",
        title="Test",
        type=SuggestionType.TOOL
    )

    assert suggestion.is_persisted() is False

    saved = suggestion_repo.save(suggestion)

    assert saved.id is not None
    assert saved.is_persisted() is True
    assert saved.author == "developer"
    assert saved.content == "Test suggestion content"


def test_save_update_existing(suggestion_repo):
    """save() dla istniejącej sugestii (UPDATE) zachowuje ID."""
    suggestion = Suggestion(author="dev", content="Original", title="Test")
    saved = suggestion_repo.save(suggestion)
    original_id = saved.id

    # Update
    saved.content = "Modified"
    saved.status = SuggestionStatus.IMPLEMENTED
    updated = suggestion_repo.save(saved)

    assert updated.id == original_id
    assert updated.content == "Modified"
    assert updated.status == SuggestionStatus.IMPLEMENTED


def test_get_existing_suggestion(suggestion_repo):
    """get() zwraca sugestię jeśli istnieje."""
    suggestion = Suggestion(author="dev", content="Test", title="Get test")
    saved = suggestion_repo.save(suggestion)

    loaded = suggestion_repo.get(saved.id)

    assert loaded is not None
    assert loaded.id == saved.id
    assert loaded.author == "dev"
    assert loaded.content == "Test"
    assert loaded.status == SuggestionStatus.OPEN  # Default


def test_get_nonexistent_suggestion(suggestion_repo):
    """get() zwraca None jeśli sugestia nie istnieje."""
    loaded = suggestion_repo.get(999)
    assert loaded is None


def test_delete_existing_suggestion(suggestion_repo):
    """delete() usuwa sugestię i zwraca True."""
    suggestion = Suggestion(author="dev", content="To delete", title="Delete test")
    saved = suggestion_repo.save(suggestion)

    result = suggestion_repo.delete(saved.id)

    assert result is True

    # Verify deleted
    loaded = suggestion_repo.get(saved.id)
    assert loaded is None


def test_delete_nonexistent_suggestion(suggestion_repo):
    """delete() zwraca False jeśli sugestia nie istnieje."""
    result = suggestion_repo.delete(999)
    assert result is False


def test_find_all(suggestion_repo):
    """find_all() zwraca wszystkie sugestie posortowane DESC."""
    s1 = Suggestion(author="dev", content="First", title="1")
    s2 = Suggestion(author="dev", content="Second", title="2")
    s3 = Suggestion(author="dev", content="Third", title="3")

    suggestion_repo.save(s1)
    suggestion_repo.save(s2)
    suggestion_repo.save(s3)

    all_suggestions = suggestion_repo.find_all()

    assert len(all_suggestions) == 3
    # Posortowane DESC (newest first)
    assert all_suggestions[0].content == "Third"
    assert all_suggestions[1].content == "Second"
    assert all_suggestions[2].content == "First"


def test_find_all_empty(suggestion_repo):
    """find_all() zwraca pustą listę gdy brak sugestii."""
    all_suggestions = suggestion_repo.find_all()
    assert all_suggestions == []


def test_find_by_status(suggestion_repo):
    """find_by_status() filtruje po statusie."""
    s1 = Suggestion(author="dev", content="Open", title="1")
    s2 = Suggestion(author="dev", content="Implemented", title="2")
    s3 = Suggestion(author="dev", content="Also open", title="3")

    suggestion_repo.save(s1)
    s2.implement()
    suggestion_repo.save(s2)
    suggestion_repo.save(s3)

    open_suggestions = suggestion_repo.find_by_status(SuggestionStatus.OPEN)

    assert len(open_suggestions) == 2
    assert all(s.status == SuggestionStatus.OPEN for s in open_suggestions)


def test_find_by_author(suggestion_repo):
    """find_by_author() filtruje po autorze."""
    s1 = Suggestion(author="developer", content="Dev suggestion", title="1")
    s2 = Suggestion(author="analyst", content="Analyst suggestion", title="2")
    s3 = Suggestion(author="developer", content="Another dev", title="3")

    suggestion_repo.save(s1)
    suggestion_repo.save(s2)
    suggestion_repo.save(s3)

    dev_suggestions = suggestion_repo.find_by_author("developer")

    assert len(dev_suggestions) == 2
    assert all(s.author == "developer" for s in dev_suggestions)


def test_find_by_type(suggestion_repo):
    """find_by_type() filtruje po typie."""
    s1 = Suggestion(author="dev", content="Tool", title="1", type=SuggestionType.TOOL)
    s2 = Suggestion(author="dev", content="Rule", title="2", type=SuggestionType.RULE)
    s3 = Suggestion(author="dev", content="Another tool", title="3", type=SuggestionType.TOOL)

    suggestion_repo.save(s1)
    suggestion_repo.save(s2)
    suggestion_repo.save(s3)

    tool_suggestions = suggestion_repo.find_by_type(SuggestionType.TOOL)

    assert len(tool_suggestions) == 2
    assert all(s.type == SuggestionType.TOOL for s in tool_suggestions)


def test_save_auto_generates_title(suggestion_repo):
    """save() auto-generuje title z contentu jeśli pusty."""
    suggestion = Suggestion(author="dev", content="This is a long content that should be truncated", title="")

    saved = suggestion_repo.save(suggestion)

    assert saved.title != ""
    assert len(saved.title) <= 80


def test_save_validation_error_no_author(suggestion_repo):
    """save() rzuca ValidationError jeśli brak autora."""
    suggestion = Suggestion(author="", content="Test", title="Test")

    with pytest.raises(ValidationError, match="must have author"):
        suggestion_repo.save(suggestion)


def test_save_validation_error_no_content(suggestion_repo):
    """save() rzuca ValidationError jeśli brak contentu."""
    suggestion = Suggestion(author="dev", content="", title="Test")

    with pytest.raises(ValidationError, match="must have.*content"):
        suggestion_repo.save(suggestion)


def test_enum_serialization(suggestion_repo):
    """Enumy są poprawnie serializowane i deserializowane."""
    suggestion = Suggestion(
        author="dev",
        content="Test",
        title="Enum test",
        type=SuggestionType.DISCOVERY,
        status=SuggestionStatus.DEFERRED
    )

    saved = suggestion_repo.save(suggestion)
    loaded = suggestion_repo.get(saved.id)

    assert loaded.type == SuggestionType.DISCOVERY
    assert loaded.status == SuggestionStatus.DEFERRED
    # Verify it's enum, not string
    assert isinstance(loaded.type, SuggestionType)
    assert isinstance(loaded.status, SuggestionStatus)


def test_backlog_id_nullable(suggestion_repo):
    """backlog_id może być None."""
    suggestion = Suggestion(author="dev", content="Test", title="Test")
    suggestion.backlog_id = None

    saved = suggestion_repo.save(suggestion)
    loaded = suggestion_repo.get(saved.id)

    assert loaded.backlog_id is None


def test_session_id_nullable(suggestion_repo):
    """session_id może być None."""
    suggestion = Suggestion(author="dev", content="Test", title="Test")
    suggestion.session_id = None

    saved = suggestion_repo.save(suggestion)
    loaded = suggestion_repo.get(saved.id)

    assert loaded.session_id is None


# ============================================================================
# BacklogRepository tests
# ============================================================================

def test_backlog_save_new(backlog_repo):
    """save() dla nowego zadania (INSERT) ustawia ID."""
    item = BacklogItem(
        title="Fix bug X",
        content="Details about bug X",
        area=BacklogArea.DEV,
        value=BacklogValue.HIGH,
        effort=BacklogEffort.SMALL
    )

    assert item.is_persisted() is False

    saved = backlog_repo.save(item)

    assert saved.id is not None
    assert saved.is_persisted() is True
    assert saved.title == "Fix bug X"
    assert saved.area == BacklogArea.DEV


def test_backlog_save_update(backlog_repo):
    """save() dla istniejącego zadania (UPDATE) aktualizuje updated_at."""
    item = BacklogItem(title="Original", area=BacklogArea.DEV)
    saved = backlog_repo.save(item)
    original_id = saved.id
    original_updated = saved.updated_at

    # Update
    saved.title = "Modified"
    saved.status = BacklogStatus.IN_PROGRESS
    updated = backlog_repo.save(saved)

    assert updated.id == original_id
    assert updated.title == "Modified"
    assert updated.status == BacklogStatus.IN_PROGRESS
    assert updated.updated_at is not None
    # updated_at should change (but might be same if fast)


def test_backlog_get_existing(backlog_repo):
    """get() zwraca zadanie jeśli istnieje."""
    item = BacklogItem(title="Test task", content="Details", area=BacklogArea.ARCH)
    saved = backlog_repo.save(item)

    loaded = backlog_repo.get(saved.id)

    assert loaded is not None
    assert loaded.id == saved.id
    assert loaded.title == "Test task"
    assert loaded.status == BacklogStatus.PLANNED  # Default


def test_backlog_get_nonexistent(backlog_repo):
    """get() zwraca None jeśli zadanie nie istnieje."""
    loaded = backlog_repo.get(999)
    assert loaded is None


def test_backlog_delete(backlog_repo):
    """delete() usuwa zadanie."""
    item = BacklogItem(title="To delete", area=BacklogArea.ERP)
    saved = backlog_repo.save(item)

    result = backlog_repo.delete(saved.id)

    assert result is True
    assert backlog_repo.get(saved.id) is None


def test_backlog_exists(backlog_repo):
    """exists() sprawdza istnienie zadania."""
    item = BacklogItem(title="Exists test")
    saved = backlog_repo.save(item)

    assert backlog_repo.exists(saved.id) is True
    assert backlog_repo.exists(999) is False


def test_backlog_find_all(backlog_repo):
    """find_all() zwraca wszystkie zadania."""
    i1 = BacklogItem(title="Task 1")
    i2 = BacklogItem(title="Task 2")
    i3 = BacklogItem(title="Task 3")

    backlog_repo.save(i1)
    backlog_repo.save(i2)
    backlog_repo.save(i3)

    all_items = backlog_repo.find_all()

    assert len(all_items) == 3


def test_backlog_find_by_status(backlog_repo):
    """find_by_status() filtruje po statusie."""
    i1 = BacklogItem(title="Planned task")
    i2 = BacklogItem(title="In progress task")

    backlog_repo.save(i1)

    i2_saved = backlog_repo.save(i2)
    i2_saved.status = BacklogStatus.IN_PROGRESS
    backlog_repo.save(i2_saved)

    planned = backlog_repo.find_by_status(BacklogStatus.PLANNED)
    in_progress = backlog_repo.find_by_status(BacklogStatus.IN_PROGRESS)

    assert len(planned) == 1
    assert planned[0].title == "Planned task"
    assert len(in_progress) == 1
    assert in_progress[0].title == "In progress task"


def test_backlog_find_by_area(backlog_repo):
    """find_by_area() filtruje po obszarze."""
    i1 = BacklogItem(title="Dev task", area=BacklogArea.DEV)
    i2 = BacklogItem(title="ERP task", area=BacklogArea.ERP)
    i3 = BacklogItem(title="Another dev task", area=BacklogArea.DEV)

    backlog_repo.save(i1)
    backlog_repo.save(i2)
    backlog_repo.save(i3)

    dev_items = backlog_repo.find_by_area(BacklogArea.DEV)
    erp_items = backlog_repo.find_by_area(BacklogArea.ERP)

    assert len(dev_items) == 2
    assert len(erp_items) == 1


def test_backlog_validation_empty_title(backlog_repo):
    """save() rzuca ValidationError gdy brak title."""
    item = BacklogItem(title="")

    with pytest.raises(ValidationError, match="title"):
        backlog_repo.save(item)


# ============================================================================
# MessageRepository tests
# ============================================================================

def test_message_save_new(message_repo):
    """save() dla nowej wiadomości (INSERT) ustawia ID."""
    msg = Message(
        sender="developer",
        recipient="analyst",
        content="Check data quality"
    )

    assert msg.is_persisted() is False

    saved = message_repo.save(msg)

    assert saved.id is not None
    assert saved.is_persisted() is True
    assert saved.sender == "developer"
    assert saved.recipient == "analyst"


def test_message_save_update(message_repo):
    """save() dla istniejącej wiadomości (UPDATE)."""
    msg = Message(sender="dev", recipient="analyst", content="Original")
    saved = message_repo.save(msg)
    original_id = saved.id

    # Mark as read
    saved.mark_read()
    updated = message_repo.save(saved)

    assert updated.id == original_id
    assert updated.status == MessageStatus.READ
    assert updated.read_at is not None


def test_message_get_existing(message_repo):
    """get() zwraca wiadomość jeśli istnieje."""
    msg = Message(sender="architect", recipient="developer", content="Test message")
    saved = message_repo.save(msg)

    loaded = message_repo.get(saved.id)

    assert loaded is not None
    assert loaded.id == saved.id
    assert loaded.content == "Test message"
    assert loaded.status == MessageStatus.UNREAD  # Default


def test_message_get_nonexistent(message_repo):
    """get() zwraca None jeśli wiadomość nie istnieje."""
    loaded = message_repo.get(999)
    assert loaded is None


def test_message_delete(message_repo):
    """delete() usuwa wiadomość."""
    msg = Message(sender="dev", recipient="analyst", content="To delete")
    saved = message_repo.save(msg)

    result = message_repo.delete(saved.id)

    assert result is True
    assert message_repo.get(saved.id) is None


def test_message_exists(message_repo):
    """exists() sprawdza istnienie wiadomości."""
    msg = Message(sender="dev", recipient="analyst", content="Exists test")
    saved = message_repo.save(msg)

    assert message_repo.exists(saved.id) is True
    assert message_repo.exists(999) is False


def test_message_find_all(message_repo):
    """find_all() zwraca wszystkie wiadomości."""
    m1 = Message(sender="dev", recipient="analyst", content="Msg 1")
    m2 = Message(sender="architect", recipient="dev", content="Msg 2")

    message_repo.save(m1)
    message_repo.save(m2)

    all_messages = message_repo.find_all()

    assert len(all_messages) == 2


def test_message_find_by_status(message_repo):
    """find_by_status() filtruje po statusie."""
    m1 = Message(sender="dev", recipient="analyst", content="Unread")
    m2 = Message(sender="dev", recipient="analyst", content="Read")

    message_repo.save(m1)

    m2_saved = message_repo.save(m2)
    m2_saved.mark_read()
    message_repo.save(m2_saved)

    unread = message_repo.find_by_status(MessageStatus.UNREAD)
    read = message_repo.find_by_status(MessageStatus.READ)

    assert len(unread) == 1
    assert len(read) == 1


def test_message_find_by_recipient(message_repo):
    """find_by_recipient() filtruje po odbiorcy."""
    m1 = Message(sender="dev", recipient="analyst", content="For analyst")
    m2 = Message(sender="architect", recipient="developer", content="For developer")
    m3 = Message(sender="dev", recipient="analyst", content="Another for analyst")

    message_repo.save(m1)
    message_repo.save(m2)
    message_repo.save(m3)

    analyst_msgs = message_repo.find_by_recipient("analyst")
    dev_msgs = message_repo.find_by_recipient("developer")

    assert len(analyst_msgs) == 2
    assert len(dev_msgs) == 1


def test_message_find_by_sender(message_repo):
    """find_by_sender() filtruje po nadawcy."""
    m1 = Message(sender="developer", recipient="analyst", content="From dev")
    m2 = Message(sender="architect", recipient="analyst", content="From architect")

    message_repo.save(m1)
    message_repo.save(m2)

    dev_msgs = message_repo.find_by_sender("developer")
    arch_msgs = message_repo.find_by_sender("architect")

    assert len(dev_msgs) == 1
    assert len(arch_msgs) == 1


def test_message_validation(message_repo):
    """save() rzuca ValidationError gdy brak wymaganych pól."""
    msg = Message(sender="", recipient="analyst", content="No sender")

    with pytest.raises(ValidationError, match="sender"):
        message_repo.save(msg)


def test_message_created_at_uses_db_default(message_repo):
    """save() używa DB DEFAULT datetime('now') dla created_at (UTC)."""
    msg = Message(sender="developer", recipient="analyst", content="Test")

    saved = message_repo.save(msg)

    # created_at should be set from DB (not from Python Entity default)
    assert saved.created_at is not None
    # Re-load from DB to verify it's persisted correctly
    loaded = message_repo.get(saved.id)
    assert loaded.created_at is not None


def test_message_read_at_after_created_at_invariant(message_repo):
    """Invariant: read_at >= created_at (timezone spójność UTC)."""
    # Create message
    msg = Message(sender="architect", recipient="developer", content="Review request")
    saved = message_repo.save(msg)

    # Mark as read
    saved.mark_read()
    updated = message_repo.save(saved)

    # CRITICAL INVARIANT: read_at must be >= created_at
    # Bug #118: read_at < created_at gdy timezone mismatch (local vs UTC)
    assert updated.read_at is not None
    assert updated.created_at is not None
    assert updated.read_at >= updated.created_at, \
        f"read_at ({updated.read_at}) < created_at ({updated.created_at}) — timezone mismatch!"
