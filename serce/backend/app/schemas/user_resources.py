"""User resources schemas — summary, public profile."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserSummary(BaseModel):
    active_requests: int
    active_offers: int
    pending_exchanges: int
    completed_exchanges: int
    heart_balance: int
    reviews_received: int


class PublicProfileRead(BaseModel):
    id: UUID
    username: str
    bio: str | None
    location_id: int | None
    heart_balance: int
    created_at: datetime
    reviews_received: int
    completed_exchanges: int
