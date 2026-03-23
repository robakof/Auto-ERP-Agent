# M4.1.2 Handoff Plan — Centralna Mapping Layer

**Date:** 2026-03-23
**From:** Developer session 09c6427095b0
**To:** Developer (next session)
**Context:** M4 Cleanup (DRY Refactors) — Phase M4.1.1 complete ✓

---

## Quick Start

**Role:** Developer
**Workflow:** Architektoniczny refaktor (tight loop Developer ↔ Architect)

**Context:**
- M4.1.1 complete, code review GREEN LIGHT (msg #212 od architect)
- M4.1.2 scope: Centralna mapping layer (~2h estimated)
- Reference: `documents/human/reports/architectural_decisions_m3_m4_transition.md`

**Start:**
1. Przeczytaj architectural decision (sekcja M4.1.2)
2. Implementuj zgodnie z planem poniżej
3. Review request do architect when done

---

## M4.1.1 Recap (COMPLETE)

**Co zostało zrobione:**
- Helper method `_get_repository()` dodany do AgentBus
- 10× duplikacja zamieniona na helper
- Tests: 60/60 PASS
- Architect code review: GREEN LIGHT (Senior-level)

**File modified:** `tools/lib/agent_bus.py`

---

## M4.1.2 Scope

**Goal:** Centralize legacy API mapping logic (6× inline → 1 location)

**Estimated time:** ~2 hours

**Success criteria:**
- All inline TYPE_MAP/REVERSE_MAP centralized
- Dict conversion helpers (~40 linii boilerplate eliminated)
- Tests: 60/60 PASS (backward compatibility intact)
- Code review architect: GREEN LIGHT

---

## Implementation Plan

### Step 1: Create mapper file structure (~10 min)

**Create:**
```
core/mappers/
├── __init__.py         # Can be empty
└── legacy_api.py       # Main mapper class
```

**Directory already created** (previous session did `os.makedirs('core/mappers')`).

---

### Step 2: Implement LegacyAPIMapper (~1h)

**File:** `core/mappers/legacy_api.py`

**Class structure:**
```python
"""Legacy API mapper — single source of truth for backward compatibility."""

from core.entities.messaging import (
    Message, Suggestion, BacklogItem,
    MessageType, MessageStatus,
    SuggestionType, SuggestionStatus,
    BacklogStatus, BacklogArea, BacklogValue, BacklogEffort
)


class LegacyAPIMapper:
    """Centralized mapping between legacy API values and domain model enums.

    Provides:
    - Type mapping (legacy strings ↔ domain enums)
    - Dict conversion (domain entities → legacy dict format)
    """

    # === Type Mappings ===

    MESSAGE_TYPE_TO_DOMAIN = {
        "suggestion": MessageType.SUGGESTION,
        "task": MessageType.TASK,
        "info": MessageType.DIRECT,
        "flag_human": MessageType.ESCALATION,
    }

    MESSAGE_TYPE_FROM_DOMAIN = {
        MessageType.DIRECT: "info",
        MessageType.ESCALATION: "flag_human",
        MessageType.SUGGESTION: "suggestion",
        MessageType.TASK: "task",
    }

    SUGGESTION_STATUS_TO_DOMAIN = {
        "in_backlog": SuggestionStatus.IMPLEMENTED,  # Legacy name
        "open": SuggestionStatus.OPEN,
        "implemented": SuggestionStatus.IMPLEMENTED,
    }

    SUGGESTION_STATUS_FROM_DOMAIN = {
        SuggestionStatus.IMPLEMENTED: "in_backlog",  # Reverse mapping
        SuggestionStatus.OPEN: "open",
    }

    # === Mapping Methods ===

    @classmethod
    def map_message_type_to_domain(cls, legacy_type: str) -> MessageType:
        """Convert legacy message type to domain enum."""
        return cls.MESSAGE_TYPE_TO_DOMAIN.get(legacy_type, MessageType.DIRECT)

    @classmethod
    def map_message_type_from_domain(cls, domain_type: MessageType) -> str:
        """Convert domain message type to legacy string."""
        return cls.MESSAGE_TYPE_FROM_DOMAIN.get(domain_type, "info")

    @classmethod
    def map_suggestion_status_to_domain(cls, legacy_status: str) -> SuggestionStatus:
        """Convert legacy suggestion status to domain enum."""
        return cls.SUGGESTION_STATUS_TO_DOMAIN.get(legacy_status, SuggestionStatus.OPEN)

    @classmethod
    def map_suggestion_status_from_domain(cls, domain_status: SuggestionStatus) -> str:
        """Convert domain suggestion status to legacy string."""
        return cls.SUGGESTION_STATUS_FROM_DOMAIN.get(domain_status, "open")

    # === Dict Conversion Helpers ===

    @classmethod
    def message_to_dict(cls, message: Message) -> dict:
        """Convert Message entity to legacy dict format."""
        return {
            "id": message.id,
            "sender": message.sender,
            "recipient": message.recipient,
            "content": message.content,
            "type": cls.map_message_type_from_domain(message.type),
            "status": message.status.value,
            "session_id": message.session_id,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "read_at": message.read_at.isoformat() if message.read_at else None,
        }

    @classmethod
    def suggestion_to_dict(cls, suggestion: Suggestion) -> dict:
        """Convert Suggestion entity to legacy dict format."""
        return {
            "id": suggestion.id,
            "author": suggestion.author,
            "recipients": suggestion.recipients,
            "title": suggestion.title,
            "content": suggestion.content,
            "type": suggestion.type.value,
            "status": cls.map_suggestion_status_from_domain(suggestion.status),
            "backlog_id": suggestion.backlog_id,
            "session_id": suggestion.session_id,
            "created_at": suggestion.created_at.isoformat() if suggestion.created_at else None,
        }

    @classmethod
    def backlog_to_dict(cls, item: BacklogItem) -> dict:
        """Convert BacklogItem entity to legacy dict format."""
        return {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "area": item.area.value if item.area else None,
            "value": item.value.value if item.value else None,
            "effort": item.effort.value if item.effort else None,
            "status": item.status.value,
            "source_id": item.source_id,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
```

**Notes:**
- BacklogStatus nie ma legacy mappings (per architectural decision)
- MessageType/SuggestionStatus mają reverse mappings (backward compat API)

---

### Step 3: Refactor adapters to use mapper (~40 min)

**File:** `tools/lib/agent_bus.py`

**Locations to refactor (6×):**

**1. send_message() — TYPE_MAP:**
```python
# Before:
TYPE_MAP = {
    "suggestion": MessageType.SUGGESTION,
    "task": MessageType.TASK,
    "info": MessageType.DIRECT,
    "flag_human": MessageType.ESCALATION,
}
type_enum = TYPE_MAP.get(type, MessageType.DIRECT)

# After:
from core.mappers.legacy_api import LegacyAPIMapper
type_enum = LegacyAPIMapper.map_message_type_to_domain(type)
```

**2. get_inbox() — dict conversion + reverse mapping:**
```python
# Before:
TYPE_REVERSE_MAP = {
    MessageType.DIRECT: "info",
    MessageType.ESCALATION: "flag_human",
    ...
}
result = []
for m in filtered:
    result.append({
        "id": m.id,
        "sender": m.sender,
        ...
        "type": TYPE_REVERSE_MAP.get(m.type, "info"),
    })

# After:
from core.mappers.legacy_api import LegacyAPIMapper
result = [LegacyAPIMapper.message_to_dict(m) for m in filtered]
```

**3. get_suggestions() — dict conversion + reverse mapping:**
```python
# Before:
status_reverse_map = {
    SuggestionStatus.IMPLEMENTED: "in_backlog",
    SuggestionStatus.OPEN: "open",
}
result = []
for s in suggestions:
    result.append({
        ...
        "status": status_reverse_map.get(s.status, "open"),
    })

# After:
from core.mappers.legacy_api import LegacyAPIMapper
result = [LegacyAPIMapper.suggestion_to_dict(s) for s in suggestions]
```

**4. update_suggestion_status() — status mapping:**
```python
# Before:
status_map = {
    "in_backlog": "implemented",
    "open": "open",
    "implemented": "implemented",
}
normalized = status_map.get(status, status)

# After:
from core.mappers.legacy_api import LegacyAPIMapper
status_enum = LegacyAPIMapper.map_suggestion_status_to_domain(status)
suggestion.status = status_enum
```

**5. get_backlog() — dict conversion:**
```python
# Before:
result = []
for item in items:
    result.append({
        "id": item.id,
        "title": item.title,
        ...
    })

# After:
from core.mappers.legacy_api import LegacyAPIMapper
result = [LegacyAPIMapper.backlog_to_dict(item) for item in items]
```

**6. (Optional) mark_read() — IF has dict conversion:**
Check if mark_read() returns dict — if yes, use message_to_dict().

---

### Step 4: Tests (~10 min)

**Run:**
```bash
py -m pytest tests/test_agent_bus.py -v
```

**Expected:**
- 60/60 PASS (backward compatibility intact)
- TestMessages: 12/12 PASS
- TestSuggestions: 10/10 PASS
- TestBacklog: 10/10 PASS
- TestTransactions: 6/6 PASS (atomicity)

**If failures:**
- Check reverse mapping logic (from_domain methods)
- Verify dict conversion includes all fields
- Debug inline — compare before/after dict output

---

### Step 5: Review request (~5 min)

**Send to architect:**
```bash
# Write review request
# tools/agent_bus_cli.py send --from developer --to architect --content-file tmp/msg_architect_m4_1_2.md
```

**Review request content:**
- M4.1.2 COMPLETE
- 6× inline mappings centralized
- ~40 linii dict boilerplate eliminated
- Tests: 60/60 PASS
- Request: GREEN LIGHT M4.1.3

---

## Verification Checklist

Before review request:
- [ ] `core/mappers/legacy_api.py` created
- [ ] LegacyAPIMapper class implements all mappings
- [ ] All 6 locations in agent_bus.py refactored
- [ ] Tests: 60/60 PASS
- [ ] Backward compatibility intact (CLI działa bez zmian)
- [ ] No inline TYPE_MAP/REVERSE_MAP remain

---

## Context References

**Architectural decision:**
`documents/human/reports/architectural_decisions_m3_m4_transition.md`

**Previous session log:**
Session ID 09c6427095b0 (logged as #175 in agent_bus)

**Architect messages:**
- #207: GREEN LIGHT M4 Cleanup (architectural decision)
- #212: GREEN LIGHT M4.1.2 (M4.1.1 review PASS)

**Files to read if needed:**
- `tools/lib/agent_bus.py` (current adapters — search for TYPE_MAP, TYPE_REVERSE_MAP, dict conversion)
- `core/entities/messaging.py` (entity definitions)

---

## Estimated Timeline

- Step 1 (file structure): 10 min ✓ (already done)
- Step 2 (mapper implementation): 1h
- Step 3 (refactor adapters): 40 min
- Step 4 (tests): 10 min
- Step 5 (review request): 5 min

**Total:** ~2h (per architectural estimate)

---

## After M4.1.2

**Next:** M4.1.3 (Dict conversion helpers — if any remain after M4.1.2) OR M4.2 (Enum audit)

Check with architect review feedback — may skip M4.1.3 if M4.1.2 eliminated all dict boilerplate.

---

**Handoff complete.** Next session: start Step 2 (implement LegacyAPIMapper).
