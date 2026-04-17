"""User read schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    email_verified: bool
    phone_verified: bool
    phone_number: str | None = None
    bio: str | None = None
    location_id: int | None = None
    heart_balance: int
    status: str
    role: str
    created_at: datetime
