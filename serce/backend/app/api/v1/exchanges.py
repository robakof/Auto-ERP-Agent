"""Exchange endpoints — create, get, accept, complete, cancel, list."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.exchange import ExchangeStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.exchange import (
    CreateExchangeBody,
    ExchangeListResponse,
    ExchangeRead,
)
from app.services import exchange_service

router = APIRouter(prefix="/exchanges", tags=["exchanges"])


@router.post("", response_model=ExchangeRead, status_code=201)
@limiter.limit("20/hour")
async def create_exchange(
    request: FastAPIRequest,
    req: CreateExchangeBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await exchange_service.create_exchange(
        db, current_user.id,
        request_id=req.request_id,
        offer_id=req.offer_id,
        hearts_agreed=req.hearts_agreed,
    )
    await db.commit()
    return result


@router.get("/{exchange_id}", response_model=ExchangeRead)
async def get_exchange(
    exchange_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await exchange_service.get_exchange(db, exchange_id, current_user.id)


@router.patch("/{exchange_id}/accept", response_model=ExchangeRead)
async def accept_exchange(
    exchange_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await exchange_service.accept_exchange(db, exchange_id, current_user.id)
    await db.commit()
    return result


@router.patch("/{exchange_id}/complete", response_model=ExchangeRead)
async def complete_exchange(
    exchange_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await exchange_service.complete_exchange(db, exchange_id, current_user.id)
    await db.commit()
    return result


@router.patch("/{exchange_id}/cancel", response_model=ExchangeRead)
async def cancel_exchange(
    exchange_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await exchange_service.cancel_exchange(db, exchange_id, current_user.id)
    await db.commit()
    return result


@router.get("", response_model=ExchangeListResponse)
async def list_exchanges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    role: str | None = Query(None, pattern=r"^(requester|helper)$"),
    status: ExchangeStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await exchange_service.list_exchanges(
        db, current_user.id, role=role, status=status, offset=offset, limit=limit,
    )
    return ExchangeListResponse(entries=entries, total=total, offset=offset, limit=limit)
