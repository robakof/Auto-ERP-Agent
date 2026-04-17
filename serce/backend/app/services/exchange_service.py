"""Exchange service — create, accept, complete, cancel, list, get."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import Request, RequestStatus
from app.db.models.user import User


async def create_exchange(
    db: AsyncSession,
    current_user_id: UUID,
    *,
    request_id: UUID | None,
    offer_id: UUID | None,
    hearts_agreed: int,
) -> Exchange:
    """Create a new PENDING Exchange from a Request or Offer."""
    if request_id:
        req = await db.get(Request, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="REQUEST_NOT_FOUND")
        if req.status != RequestStatus.OPEN:
            raise HTTPException(status_code=422, detail="REQUEST_NOT_OPEN")
        if req.user_id == current_user_id:
            raise HTTPException(status_code=422, detail="CANNOT_EXCHANGE_SELF")

        # Duplicate check
        dup = await db.execute(
            select(func.count()).select_from(
                select(Exchange).where(
                    Exchange.request_id == request_id,
                    Exchange.initiated_by == current_user_id,
                    Exchange.status == ExchangeStatus.PENDING,
                ).subquery()
            )
        )
        if (dup.scalar() or 0) > 0:
            raise HTTPException(status_code=422, detail="EXCHANGE_ALREADY_EXISTS")

        exchange = Exchange(
            request_id=request_id,
            requester_id=req.user_id,
            helper_id=current_user_id,
            initiated_by=current_user_id,
            hearts_agreed=hearts_agreed,
            status=ExchangeStatus.PENDING,
        )

    elif offer_id:
        offer = await db.get(Offer, offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="OFFER_NOT_FOUND")
        if offer.status != OfferStatus.ACTIVE:
            raise HTTPException(status_code=422, detail="OFFER_NOT_ACTIVE")
        if offer.user_id == current_user_id:
            raise HTTPException(status_code=422, detail="CANNOT_EXCHANGE_SELF")

        # Duplicate check
        dup = await db.execute(
            select(func.count()).select_from(
                select(Exchange).where(
                    Exchange.offer_id == offer_id,
                    Exchange.initiated_by == current_user_id,
                    Exchange.status == ExchangeStatus.PENDING,
                ).subquery()
            )
        )
        if (dup.scalar() or 0) > 0:
            raise HTTPException(status_code=422, detail="EXCHANGE_ALREADY_EXISTS")

        exchange = Exchange(
            offer_id=offer_id,
            requester_id=current_user_id,
            helper_id=offer.user_id,
            initiated_by=current_user_id,
            hearts_agreed=hearts_agreed,
            status=ExchangeStatus.PENDING,
        )
    else:
        raise HTTPException(status_code=422, detail="INVALID_SOURCE")

    db.add(exchange)
    await db.flush()
    return exchange


async def get_exchange(
    db: AsyncSession, exchange_id: UUID, current_user_id: UUID,
) -> Exchange:
    """Get exchange — participant only."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if current_user_id not in (exchange.requester_id, exchange.helper_id):
        raise HTTPException(status_code=403, detail="NOT_PARTICIPANT")
    return exchange


async def accept_exchange(
    db: AsyncSession, exchange_id: UUID, current_user_id: UUID,
) -> Exchange:
    """Accept exchange — non-initiator. Escrow hearts from requester."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if exchange.status != ExchangeStatus.PENDING:
        raise HTTPException(status_code=422, detail="NOT_PENDING")
    if current_user_id == exchange.initiated_by:
        raise HTTPException(status_code=403, detail="CANNOT_ACCEPT_OWN")
    if current_user_id not in (exchange.requester_id, exchange.helper_id):
        raise HTTPException(status_code=403, detail="NOT_PARTICIPANT")

    # Request unique guard
    if exchange.request_id:
        existing = await db.execute(
            select(func.count()).select_from(
                select(Exchange).where(
                    Exchange.request_id == exchange.request_id,
                    Exchange.id != exchange.id,
                    Exchange.status.in_([ExchangeStatus.ACCEPTED, ExchangeStatus.COMPLETED]),
                ).subquery()
            )
        )
        if (existing.scalar() or 0) > 0:
            raise HTTPException(status_code=422, detail="REQUEST_ALREADY_ACCEPTED")

    # Escrow: lock requester, deduct hearts
    if exchange.hearts_agreed > 0:
        result = await db.execute(
            select(User).where(User.id == exchange.requester_id).with_for_update()
        )
        requester = result.scalar_one_or_none()
        if not requester or requester.heart_balance < exchange.hearts_agreed:
            raise HTTPException(status_code=422, detail="INSUFFICIENT_BALANCE")

        requester.heart_balance -= exchange.hearts_agreed

        ledger = HeartLedger(
            from_user_id=exchange.requester_id,
            to_user_id=exchange.requester_id,
            amount=exchange.hearts_agreed,
            type=HeartLedgerType.EXCHANGE_ESCROW,
            related_exchange_id=exchange.id,
        )
        db.add(ledger)

    exchange.status = ExchangeStatus.ACCEPTED
    await db.flush()
    return exchange


async def complete_exchange(
    db: AsyncSession, exchange_id: UUID, current_user_id: UUID,
) -> Exchange:
    """Complete exchange — requester only. Credit hearts to helper."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if exchange.status != ExchangeStatus.ACCEPTED:
        raise HTTPException(status_code=422, detail="NOT_ACCEPTED")
    if current_user_id != exchange.requester_id:
        raise HTTPException(status_code=403, detail="ONLY_REQUESTER_COMPLETES")

    # Credit helper
    if exchange.hearts_agreed > 0:
        result = await db.execute(
            select(User).where(User.id == exchange.helper_id).with_for_update()
        )
        helper = result.scalar_one_or_none()
        if not helper:
            raise HTTPException(status_code=404, detail="HELPER_NOT_FOUND")

        if helper.heart_balance + exchange.hearts_agreed > settings.heart_balance_cap:
            raise HTTPException(status_code=422, detail="RECIPIENT_CAP_EXCEEDED")

        helper.heart_balance += exchange.hearts_agreed

        ledger = HeartLedger(
            from_user_id=exchange.requester_id,
            to_user_id=exchange.helper_id,
            amount=exchange.hearts_agreed,
            type=HeartLedgerType.EXCHANGE_COMPLETE,
            related_exchange_id=exchange.id,
        )
        db.add(ledger)

    exchange.status = ExchangeStatus.COMPLETED
    exchange.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return exchange


async def cancel_exchange(
    db: AsyncSession, exchange_id: UUID, current_user_id: UUID,
) -> Exchange:
    """Cancel exchange — either participant. Refund if ACCEPTED."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if exchange.status not in (ExchangeStatus.PENDING, ExchangeStatus.ACCEPTED):
        raise HTTPException(status_code=422, detail="NOT_CANCELLABLE")
    if current_user_id not in (exchange.requester_id, exchange.helper_id):
        raise HTTPException(status_code=403, detail="NOT_PARTICIPANT")

    # Refund if escrow was active
    if exchange.status == ExchangeStatus.ACCEPTED and exchange.hearts_agreed > 0:
        result = await db.execute(
            select(User).where(User.id == exchange.requester_id).with_for_update()
        )
        requester = result.scalar_one_or_none()
        if requester:
            requester.heart_balance += exchange.hearts_agreed

        ledger = HeartLedger(
            from_user_id=exchange.requester_id,
            to_user_id=exchange.requester_id,
            amount=exchange.hearts_agreed,
            type=HeartLedgerType.EXCHANGE_REFUND,
            related_exchange_id=exchange.id,
        )
        db.add(ledger)

    exchange.status = ExchangeStatus.CANCELLED
    await db.flush()
    return exchange


async def list_exchanges(
    db: AsyncSession,
    current_user_id: UUID,
    *,
    role: str | None = None,
    status: ExchangeStatus | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Exchange], int]:
    """List exchanges for current user with optional filters."""
    if role == "requester":
        base_filter = Exchange.requester_id == current_user_id
    elif role == "helper":
        base_filter = Exchange.helper_id == current_user_id
    else:
        base_filter = (Exchange.requester_id == current_user_id) | (Exchange.helper_id == current_user_id)

    base_q = select(Exchange).where(base_filter)
    if status:
        base_q = base_q.where(Exchange.status == status)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(Exchange.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()

    return list(entries), total
