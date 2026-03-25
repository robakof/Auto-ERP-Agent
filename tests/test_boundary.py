"""
Boundary tests — testy na granicach modułów.

Backlog #145. Testują interakcje MIĘDZY modułami:
- Runner ↔ Repository (claimed_by persistence)
- Live ↔ Replay (telemetry dedup)
- Safety hook ↔ Bash (command validation)
- Legacy API ↔ Domain model (type mapping)
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from core.entities.messaging import (
    Message, MessageStatus, MessageType,
    SuggestionStatus,
)
from core.repositories.message_repo import MessageRepository
from core.mappers.legacy_api import LegacyAPIMapper
from tools.lib.agent_bus import AgentBus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_db(tmp_path):
    return str(tmp_path / "test_boundary.db")


@pytest.fixture
def msg_repo(temp_db):
    AgentBus(db_path=temp_db)
    return MessageRepository(db_path=temp_db)


@pytest.fixture
def bus(temp_db):
    return AgentBus(db_path=temp_db)


# ============================================================================
# Suite 1: Runner ↔ Repository (claimed_by)
# ============================================================================

class TestClaimedByBoundary:
    """claimed_by field must survive domain layer round-trip."""

    def test_repository_reads_claimed_by(self, temp_db, bus):
        """claim_task() sets claimed_by → repository.get() returns it."""
        msg_id = bus.send_message("developer", "erp_specialist", "Task", type="task")
        bus.claim_task(msg_id, "runner-abc")

        repo = MessageRepository(db_path=temp_db)
        msg = repo.get(msg_id)
        assert msg is not None
        assert msg.claimed_by == "runner-abc"
        assert msg.status == MessageStatus.UNREAD  # status unchanged

    def test_repository_saves_claimed_by_on_insert(self, msg_repo):
        """New message with claimed_by → persisted on INSERT."""
        msg = Message(
            sender="dev", recipient="analyst", content="Test",
            claimed_by="runner-123"
        )
        saved = msg_repo.save(msg)
        loaded = msg_repo.get(saved.id)
        assert loaded.claimed_by == "runner-123"

    def test_repository_saves_claimed_by_on_update(self, temp_db, msg_repo):
        """Update claimed_by on existing message → persisted."""
        msg = Message(sender="dev", recipient="analyst", content="Test")
        saved = msg_repo.save(msg)
        assert saved.claimed_by is None

        saved.claimed_by = "runner-456"
        msg_repo.save(saved)

        loaded = msg_repo.get(saved.id)
        assert loaded.claimed_by == "runner-456"

    def test_graceful_degradation_claimed_status(self, temp_db, bus):
        """Legacy 'claimed' status in DB → read as UNREAD (graceful degradation)."""
        msg_id = bus.send_message("dev", "analyst", "Legacy")

        conn = sqlite3.connect(temp_db)
        conn.execute("UPDATE messages SET status = 'claimed' WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()

        repo = MessageRepository(db_path=temp_db)
        msg = repo.get(msg_id)
        assert msg.status == MessageStatus.UNREAD


# ============================================================================
# Suite 2: Telemetry dedup (live ↔ replay)
# ============================================================================

class TestTelemetryDedupBoundary:
    """Unique index on tool_calls prevents duplicate entries."""

    @staticmethod
    def _create_session(bus, session_id):
        """Create a session record to satisfy FK constraint."""
        bus._conn.execute(
            "INSERT OR IGNORE INTO sessions (id, role, started_at) VALUES (?, 'test', datetime('now'))",
            (session_id,),
        )
        bus._auto_commit()

    def test_duplicate_tool_call_ignored(self, bus):
        """Same (session_id, tool_name, timestamp) → only 1 row."""
        self._create_session(bus, "sess-1")
        bus.add_tool_call(
            session_id="sess-1", tool_name="Read", timestamp="2026-03-25T10:00:00",
            input_summary="file.py"
        )
        bus.add_tool_call(
            session_id="sess-1", tool_name="Read", timestamp="2026-03-25T10:00:00",
            input_summary="file.py (replay)"
        )

        count = bus._conn.execute(
            "SELECT COUNT(*) FROM tool_calls WHERE session_id = 'sess-1' AND tool_name = 'Read'"
        ).fetchone()[0]
        assert count == 1

    def test_different_timestamp_allowed(self, bus):
        """Same session+tool but different timestamp → 2 rows."""
        self._create_session(bus, "sess-2")
        bus.add_tool_call(
            session_id="sess-2", tool_name="Bash", timestamp="2026-03-25T10:00:00",
            input_summary="cmd1"
        )
        bus.add_tool_call(
            session_id="sess-2", tool_name="Bash", timestamp="2026-03-25T10:00:01",
            input_summary="cmd2"
        )

        count = bus._conn.execute(
            "SELECT COUNT(*) FROM tool_calls WHERE session_id = 'sess-2' AND tool_name = 'Bash'"
        ).fetchone()[0]
        assert count == 2

    def test_different_tool_same_timestamp_allowed(self, bus):
        """Same session+timestamp but different tool → 2 rows."""
        self._create_session(bus, "sess-3")
        bus.add_tool_call(
            session_id="sess-3", tool_name="Read", timestamp="2026-03-25T10:00:00",
            input_summary="a"
        )
        bus.add_tool_call(
            session_id="sess-3", tool_name="Write", timestamp="2026-03-25T10:00:00",
            input_summary="b"
        )

        count = bus._conn.execute(
            "SELECT COUNT(*) FROM tool_calls WHERE session_id = 'sess-3'"
        ).fetchone()[0]
        assert count == 2


# ============================================================================
# Suite 3: Safety gate precision
# ============================================================================

HOOK = Path("tools/hooks/pre_tool_use.py")


def run_hook(payload: dict) -> tuple:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    output = None
    if result.stdout.strip():
        output = json.loads(result.stdout.strip())
    return result.returncode, output


def make_bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def get_decision(output: dict) -> str:
    return output["hookSpecificOutput"]["permissionDecision"]


class TestSafetyGateBoundary:
    """Edge cases at safety gate boundaries."""

    def test_rm_protected_file_denied(self):
        """rm on protected document → denied."""
        _, out = run_hook(make_bash("rm documents/erp_specialist/ERP_SPECIALIST.md"))
        assert get_decision(out) == "deny"

    def test_rm_tmp_file_allowed(self):
        """rm in tmp/ → allowed."""
        _, out = run_hook(make_bash("rm tmp/scratch.md"))
        assert get_decision(out) == "allow"

    def test_command_chain_safe_then_unsafe_denied(self):
        """git status && rm -rf core/ → denied (chain validated per segment)."""
        _, out = run_hook(make_bash("git status && rm -rf core/"))
        assert get_decision(out) == "deny"

    def test_del_wildcard_denied(self):
        """del *.py → denied (wildcard destructive)."""
        _, out = run_hook(make_bash("del *.py"))
        assert get_decision(out) == "deny"


# ============================================================================
# Suite 4: Legacy API mapping
# ============================================================================

class TestLegacyMappingBoundary:
    """Legacy API values must map correctly to domain model."""

    def test_flag_human_maps_to_escalation(self):
        result = LegacyAPIMapper.MESSAGE_TYPE_TO_DOMAIN["flag_human"]
        assert result == MessageType.ESCALATION

    def test_info_maps_to_direct(self):
        result = LegacyAPIMapper.MESSAGE_TYPE_TO_DOMAIN["info"]
        assert result == MessageType.DIRECT

    def test_in_backlog_maps_to_implemented(self):
        result = LegacyAPIMapper.SUGGESTION_STATUS_TO_DOMAIN["in_backlog"]
        assert result == SuggestionStatus.IMPLEMENTED

    def test_message_type_round_trip(self):
        """TO_DOMAIN and FROM_DOMAIN are consistent inverses."""
        for legacy_key, domain_val in LegacyAPIMapper.MESSAGE_TYPE_TO_DOMAIN.items():
            back = LegacyAPIMapper.MESSAGE_TYPE_FROM_DOMAIN[domain_val]
            re_mapped = LegacyAPIMapper.MESSAGE_TYPE_TO_DOMAIN[back]
            assert re_mapped == domain_val, f"Round-trip failed for {legacy_key}"


# ============================================================================
# Suite 5: Entity ↔ Repository field sync (meta-test)
# ============================================================================

class TestEntityRepoFieldSync:
    """Detect when entity fields diverge from repository SELECT columns."""

    def test_message_entity_fields_match_db_columns(self, temp_db):
        """All Message dataclass fields must exist as DB columns."""
        import dataclasses
        bus = AgentBus(db_path=temp_db)

        # Get DB columns
        columns = bus._conn.execute("PRAGMA table_info(messages)").fetchall()
        db_column_names = {col[1] for col in columns}

        # Get entity fields (excluding base Entity fields: id, created_at, updated_at)
        entity_fields = {f.name for f in dataclasses.fields(Message)}
        # Map entity field names to DB column names (1:1 in this project)
        # Exclude 'updated_at' — base Entity field, not in messages table
        entity_fields.discard("updated_at")

        missing_in_db = entity_fields - db_column_names
        assert not missing_in_db, (
            f"Message entity fields missing from DB: {missing_in_db}. "
            f"Add columns or update entity."
        )
