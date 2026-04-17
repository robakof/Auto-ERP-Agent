"""Review service — create, list for exchange, list for user."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.review import Review
from app.db.models.user import User


async def create_review(
    db: AsyncSession,
    exchange_id: UUID,
    current_user_id: UUID,
    *,
    comment: str,
) -> Review:
    """Create review for completed exchange — participant only, once per person."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if exchange.status != ExchangeStatus.COMPLETED:
        raise HTTPException(status_code=422, detail="EXCHANGE_NOT_COMPLETED")
    if current_user_id not in (exchange.requester_id, exchange.helper_id):
        raise HTTPException(status_code=403, detail="NOT_PARTICIPANT")

    # Determine reviewed_id (the other side)
    if current_user_id == exchange.requester_id:
        reviewed_id = exchange.helper_id
    else:
        reviewed_id = exchange.requester_id

    # Application-level duplicate check (better error than IntegrityError)
    existing = await db.execute(
        select(func.count()).select_from(
            select(Review).where(
                Review.exchange_id == exchange_id,
                Review.reviewer_id == current_user_id,
            ).subquery()
        )
    )
    if (existing.scalar() or 0) > 0:
        raise HTTPException(status_code=422, detail="REVIEW_ALREADY_EXISTS")

    review = Review(
        exchange_id=exchange_id,
        reviewer_id=current_user_id,
        reviewed_id=reviewed_id,
        comment=comment,
    )
    db.add(review)
    await db.flush()
    return review


async def list_reviews_for_exchange(
    db: AsyncSession,
    exchange_id: UUID,
    current_user_id: UUID,
) -> list[Review]:
    """List reviews for exchange — participant only (max 2)."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if current_user_id not in (exchange.requester_id, exchange.helper_id):
        raise HTTPException(status_code=403, detail="NOT_PARTICIPANT")

    result = await db.execute(
        select(Review).where(Review.exchange_id == exchange_id)
    )
    return list(result.scalars().all())


async def list_reviews_for_user(
    db: AsyncSession,
    user_id: UUID,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Review], int]:
    """List reviews received by user — public profile."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    base_q = select(Review).where(Review.reviewed_id == user_id)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(Review.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()

    return list(entries), total
