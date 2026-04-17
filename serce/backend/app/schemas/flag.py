"""Flag schemas — create body, read response."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.admin import FlagReason


class CreateFlagBody(BaseModel):
    reason: FlagReason
    description: str | None = Field(None, max_length=1000)


class FlagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID | None
    target_type: str
    target_id: UUID
    reason: str
    description: str | None
    status: str
    created_at: datetime
