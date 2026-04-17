"""Request schemas — create, update, read, list, cancel."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.request import LocationScope


class CreateRequestBody(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    hearts_offered: int = Field(ge=0, le=50)
    category_id: int
    location_id: int
    location_scope: LocationScope
    expires_at: datetime | None = None


class UpdateRequestBody(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=2000)
    hearts_offered: int | None = Field(None, ge=0, le=50)
    expires_at: datetime | None = None


class RequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    description: str
    hearts_offered: int
    category_id: int
    location_id: int
    location_scope: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    updated_at: datetime


class RequestListResponse(BaseModel):
    entries: list[RequestRead]
    total: int
    offset: int
    limit: int


class CancelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
