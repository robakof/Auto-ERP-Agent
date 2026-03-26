"""Legacy API mapper — single source of truth for backward compatibility."""

from core.entities.messaging import BacklogItem, Message, MessageType, Suggestion, SuggestionStatus


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
        "handoff": MessageType.HANDOFF,
    }

    MESSAGE_TYPE_FROM_DOMAIN = {
        MessageType.DIRECT: "info",
        MessageType.ESCALATION: "flag_human",
        MessageType.SUGGESTION: "suggestion",
        MessageType.TASK: "task",
        MessageType.HANDOFF: "handoff",
    }

    SUGGESTION_STATUS_TO_DOMAIN = {
        "in_backlog": SuggestionStatus.IMPLEMENTED,  # Legacy name
        "open": SuggestionStatus.OPEN,
        "implemented": SuggestionStatus.IMPLEMENTED,
        "rejected": SuggestionStatus.REJECTED,
        "deferred": SuggestionStatus.DEFERRED,
    }

    SUGGESTION_STATUS_FROM_DOMAIN = {
        SuggestionStatus.IMPLEMENTED: "implemented",
        SuggestionStatus.OPEN: "open",
        SuggestionStatus.REJECTED: "rejected",
        SuggestionStatus.DEFERRED: "deferred",
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
            "reply_to_id": message.reply_to_id,
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
            "depends_on": item.depends_on,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
