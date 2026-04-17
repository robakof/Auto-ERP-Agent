"""Hearts endpoints — gift, balance, ledger."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.heart import HeartLedgerType
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.hearts import (
    BalanceResponse,
    GiftRequest,
    LedgerEntryRead,
    LedgerResponse,
)
from app.services import hearts_service

router = APIRouter(prefix="/hearts", tags=["hearts"])


@router.post("/gift", response_model=LedgerEntryRead, status_code=201)
@limiter.limit("30/hour")
async def gift_hearts(
    request: Request,
    req: GiftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ledger = await hearts_service.gift_hearts(
        db, current_user.id, req.to_user_id, req.amount, req.note,
    )
    await db.commit()
    return ledger


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    balance = await hearts_service.get_balance(db, current_user.id)
    return BalanceResponse(
        heart_balance=balance,
        heart_balance_cap=settings.heart_balance_cap,
    )


@router.get("/ledger", response_model=LedgerResponse)
async def get_ledger(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    type: str | None = Query(None, description="Filter by ledger type"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    type_filter = None
    if type:
        try:
            type_filter = HeartLedgerType(type)
        except ValueError:
            pass  # invalid type → no filter, return all

    entries, total = await hearts_service.get_ledger(
        db, current_user.id, type_filter=type_filter, offset=offset, limit=limit,
    )
    return LedgerResponse(entries=entries, total=total, offset=offset, limit=limit)
