"""Admin schemas — flags, suspend, hearts grant, audit log."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.admin import ResolutionAction


class FlagDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reporter_id: UUID | None
    target_type: str
    target_id: UUID
    reason: str
    description: str | None
    status: str
    resolved_by: UUID | None
    resolved_at: datetime | None
    resolution_action: str | None
    resolution_reason: str | None
    created_at: datetime


class FlagListResponse(BaseModel):
    entries: list[FlagDetailRead]
    total: int
    offset: int
    limit: int


class ResolveFlagBody(BaseModel):
    action: ResolutionAction
    reason: str = Field(max_length=1000)
    params: dict | None = None


class SuspendUserBody(BaseModel):
    reason: str = Field(max_length=1000)
    duration_days: int | None = Field(None, ge=1, le=365)


class UserAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    status: str
    role: str
    suspended_at: datetime | None
    suspended_until: datetime | None
    suspension_reason: str | None
    heart_balance: int
    created_at: datetime


class GrantHeartsBody(BaseModel):
    user_id: UUID
    amount: int = Field(gt=0)
    type: Literal["ADMIN_GRANT", "ADMIN_REFUND"]
    reason: str = Field(max_length=1000)


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    admin_id: UUID
    action: str
    target_type: str
    target_id: UUID | None
    payload: dict
    reason: str | None
    created_at: datetime


class AuditListResponse(BaseModel):
    entries: list[AuditLogRead]
    total: int
    offset: int
    limit: int
