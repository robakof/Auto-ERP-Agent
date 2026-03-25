"""
Core services — domain logic extracted from AgentBus (#149).

Services accept a shared sqlite3.Connection and contain business logic.
AgentBus (tools/lib/agent_bus.py) delegates to these services.
"""

from .backlog_service import BacklogService
from .instance_service import InstanceService
from .known_gaps_service import KnownGapsService
from .message_service import MessageService
from .session_service import SessionService
from .suggestion_service import SuggestionService
from .telemetry_service import TelemetryService
from .workflow_service import WorkflowService

__all__ = [
    "BacklogService",
    "InstanceService",
    "KnownGapsService",
    "MessageService",
    "SessionService",
    "SuggestionService",
    "TelemetryService",
    "WorkflowService",
]
