"""Review schemas — create, read, list."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateReviewBody(BaseModel):
    comment: str = Field(min_length=10, max_length=2000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    exchange_id: UUID
    reviewer_id: UUID
    reviewed_id: UUID
    comment: str
    created_at: datetime


class ReviewListResponse(BaseModel):
    entries: list[ReviewRead]
    total: int
    offset: int
    limit: int
