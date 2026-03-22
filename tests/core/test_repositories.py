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

from core.entities.messaging import Suggestion, SuggestionStatus, SuggestionType
from core.repositories.suggestion_repo import SuggestionRepository
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
