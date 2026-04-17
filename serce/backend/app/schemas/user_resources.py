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
    username: str | None = None
    bio: str | None = None
    location_id: int | None = None
    heart_balance: int = 0
    created_at: datetime
    reviews_received: int = 0
    completed_exchanges: int = 0
    is_deleted: bool = False
