"""Flag endpoints — report content violations (request, offer, exchange, user)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.admin import FlagTargetType
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.flag import CreateFlagBody, FlagRead
from app.services import flag_service

router = APIRouter(tags=["flags"])


@router.post("/requests/{target_id}/flag", response_model=FlagRead, status_code=201)
@limiter.limit("10/hour")
async def flag_request(
    request: FastAPIRequest,
    target_id: UUID,
    body: CreateFlagBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await flag_service.create_flag(
        db, current_user.id, FlagTargetType.REQUEST, target_id,
        reason=body.reason, description=body.description,
    )
    await db.commit()
    return result


@router.post("/offers/{target_id}/flag", response_model=FlagRead, status_code=201)
@limiter.limit("10/hour")
async def flag_offer(
    request: FastAPIRequest,
    target_id: UUID,
    body: CreateFlagBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await flag_service.create_flag(
        db, current_user.id, FlagTargetType.OFFER, target_id,
        reason=body.reason, description=body.description,
    )
    await db.commit()
    return result


@router.post("/exchanges/{target_id}/flag", response_model=FlagRead, status_code=201)
@limiter.limit("10/hour")
async def flag_exchange(
    request: FastAPIRequest,
    target_id: UUID,
    body: CreateFlagBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await flag_service.create_flag(
        db, current_user.id, FlagTargetType.EXCHANGE, target_id,
        reason=body.reason, description=body.description,
    )
    await db.commit()
    return result


@router.post("/users/{target_id}/flag", response_model=FlagRead, status_code=201)
@limiter.limit("10/hour")
async def flag_user(
    request: FastAPIRequest,
    target_id: UUID,
    body: CreateFlagBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await flag_service.create_flag(
        db, current_user.id, FlagTargetType.USER, target_id,
        reason=body.reason, description=body.description,
    )
    await db.commit()
    return result
