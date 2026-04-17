"""Hearts schemas — gift, balance, ledger."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GiftRequest(BaseModel):
    to_user_id: UUID
    amount: int = Field(gt=0, le=50)
    note: str | None = Field(None, max_length=200)


class BalanceResponse(BaseModel):
    heart_balance: int
    heart_balance_cap: int


class LedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_user_id: UUID | None
    to_user_id: UUID | None
    amount: int
    type: str
    note: str | None
    created_at: datetime


class LedgerResponse(BaseModel):
    entries: list[LedgerEntryRead]
    total: int
    offset: int
    limit: int
