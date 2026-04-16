"""Session list schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_info: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime
