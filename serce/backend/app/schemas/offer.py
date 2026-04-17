"""Offer schemas — create, update, status, read, list."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.offer import OfferStatus
from app.db.models.request import LocationScope


class CreateOfferBody(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    hearts_asked: int = Field(ge=0, le=50)
    category_id: int
    location_id: int
    location_scope: LocationScope


class UpdateOfferBody(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=2000)
    hearts_asked: int | None = Field(None, ge=0, le=50)


class ChangeOfferStatusBody(BaseModel):
    status: OfferStatus


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    description: str
    hearts_asked: int
    category_id: int
    location_id: int
    location_scope: str
    status: str
    created_at: datetime
    updated_at: datetime


class OfferListResponse(BaseModel):
    entries: list[OfferRead]
    total: int
    offset: int
    limit: int
