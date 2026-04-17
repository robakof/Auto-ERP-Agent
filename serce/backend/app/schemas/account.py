"""Account schemas — soft delete."""
from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SoftDeleteBody(BaseModel):
    password: str = Field(min_length=1)
    balance_disposition: Literal["void", "transfer"]
    transfer_to_user_id: UUID | None = None
