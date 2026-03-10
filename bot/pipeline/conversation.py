"""
ConversationManager — kontekst konwersacji per user.

- Przechowuje ostatnie N tur (pytanie + odpowiedź) per user_id
- TTL: reset po zadanym czasie nieaktywności
- Stan w pamięci (utracony przy restarcie serwisu — akceptowalne)
"""

import time
from dataclasses import dataclass, field


@dataclass
class Turn:
    question: str
    answer: str
    ts: float


@dataclass
class _UserSession:
    turns: list[Turn] = field(default_factory=list)
    last_active: float = field(default_factory=time.monotonic)


class ConversationManager:
    def __init__(self, ttl_seconds: int = 900, max_turns: int = 3):
        self.ttl_seconds = ttl_seconds
        self.max_turns = max_turns
        self._sessions: dict[str, _UserSession] = {}

    def _get_session(self, user_id: str) -> _UserSession | None:
        session = self._sessions.get(user_id)
        if session is None:
            return None
        if time.monotonic() - session.last_active > self.ttl_seconds:
            del self._sessions[user_id]
            return None
        return session

    def get_turns(self, user_id: str) -> list[Turn]:
        session = self._get_session(user_id)
        return list(session.turns) if session else []

    def save_turn(self, user_id: str, question: str, answer: str) -> None:
        session = self._get_session(user_id)
        if session is None:
            session = _UserSession()
            self._sessions[user_id] = session

        session.turns.append(Turn(question=question, answer=answer, ts=time.monotonic()))
        session.turns = session.turns[-self.max_turns :]
        session.last_active = time.monotonic()

    def format_history(self, user_id: str) -> str:
        turns = self.get_turns(user_id)
        if not turns:
            return ""
        lines = []
        for turn in turns:
            lines.append(f"Użytkownik: {turn.question}")
            lines.append(f"Bot: {turn.answer}")
        return "\n".join(lines)
