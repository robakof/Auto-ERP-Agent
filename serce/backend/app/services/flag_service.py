"""Flag service — create content flag with target validation."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.admin import ContentFlag, FlagReason, FlagStatus, FlagTargetType
from app.db.models.exchange import Exchange
from app.db.models.offer import Offer
from app.db.models.request import Request
from app.db.models.user import User, UserStatus


async def create_flag(
    db: AsyncSession,
    reporter_id: UUID,
    target_type: FlagTargetType,
    target_id: UUID,
    *,
    reason: FlagReason,
    description: str | None = None,
) -> ContentFlag:
    """Create flag. Validates target, prevents self-flag and duplicates."""
    # 1. Duplicate check — one OPEN flag per (reporter, target_type, target_id)
    dup = await db.execute(
        select(func.count()).select_from(
            select(ContentFlag).where(
                ContentFlag.reporter_id == reporter_id,
                ContentFlag.target_type == target_type,
                ContentFlag.target_id == target_id,
                ContentFlag.status == FlagStatus.OPEN,
            ).subquery()
        )
    )
    if (dup.scalar() or 0) > 0:
        raise HTTPException(status_code=422, detail="ALREADY_FLAGGED")

    # 2. Target validation + self-flag prevention
    await _validate_target(db, reporter_id, target_type, target_id)

    # 3. Create
    flag = ContentFlag(
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        description=description,
    )
    db.add(flag)
    await db.flush()
    return flag


async def _validate_target(
    db: AsyncSession,
    reporter_id: UUID,
    target_type: FlagTargetType,
    target_id: UUID,
) -> None:
    """Validate target exists and reporter is not flagging own resource."""
    if target_type == FlagTargetType.REQUEST:
        obj = await db.get(Request, target_id)
        if not obj:
            raise HTTPException(status_code=404, detail="TARGET_NOT_FOUND")
        if reporter_id == obj.user_id:
            raise HTTPException(status_code=422, detail="CANNOT_FLAG_OWN_RESOURCE")

    elif target_type == FlagTargetType.OFFER:
        obj = await db.get(Offer, target_id)
        if not obj:
            raise HTTPException(status_code=404, detail="TARGET_NOT_FOUND")
        if reporter_id == obj.user_id:
            raise HTTPException(status_code=422, detail="CANNOT_FLAG_OWN_RESOURCE")

    elif target_type == FlagTargetType.EXCHANGE:
        obj = await db.get(Exchange, target_id)
        if not obj:
            raise HTTPException(status_code=404, detail="TARGET_NOT_FOUND")
        if reporter_id not in (obj.requester_id, obj.helper_id):
            raise HTTPException(status_code=404, detail="TARGET_NOT_FOUND")

    elif target_type == FlagTargetType.USER:
        obj = await db.get(User, target_id)
        if not obj or obj.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=404, detail="TARGET_NOT_FOUND")
        if reporter_id == target_id:
            raise HTTPException(status_code=422, detail="CANNOT_FLAG_OWN_RESOURCE")
