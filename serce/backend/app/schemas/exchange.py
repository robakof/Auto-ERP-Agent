"""Exchange schemas — create, read, list."""
from __future__ import annotations

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models.exchange import ExchangeStatus


class CreateExchangeBody(BaseModel):
    request_id: UUID | None = None
    offer_id: UUID | None = None
    hearts_agreed: int = Field(ge=0, le=50)

    @model_validator(mode="after")
    def exactly_one_source(self) -> Self:
        if bool(self.request_id) == bool(self.offer_id):
            raise ValueError("Exactly one of request_id or offer_id required")
        return self


class ExchangeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID | None
    offer_id: UUID | None
    requester_id: UUID
    helper_id: UUID
    initiated_by: UUID
    hearts_agreed: int
    status: str
    created_at: datetime
    completed_at: datetime | None


class ExchangeListResponse(BaseModel):
    entries: list[ExchangeRead]
    total: int
    offset: int
    limit: int
