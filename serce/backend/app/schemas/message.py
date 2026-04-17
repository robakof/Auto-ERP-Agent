"""Message schemas — send, read, list."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SendMessageBody(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    exchange_id: UUID
    sender_id: UUID
    content: str
    is_hidden: bool
    created_at: datetime


class MessageListResponse(BaseModel):
    entries: list[MessageRead]
    total: int
    offset: int
    limit: int
