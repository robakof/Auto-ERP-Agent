"""Notification schemas — read, list, unread count, mark-all-read."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    type: str
    reason: str | None
    related_exchange_id: UUID | None
    related_message_id: UUID | None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    entries: list[NotificationRead]
    total: int
    offset: int
    limit: int


class UnreadCountResponse(BaseModel):
    count: int


class MarkAllReadResponse(BaseModel):
    updated: int
