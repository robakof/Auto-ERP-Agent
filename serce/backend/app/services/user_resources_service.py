"""User resources service — my requests/offers/reviews, summary, public profile."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import Request, RequestStatus
from app.db.models.review import Review
from app.db.models.user import User, UserStatus


async def my_requests(
    db: AsyncSession,
    user_id: UUID,
    *,
    status: RequestStatus | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Request], int]:
    """Owner view — all statuses visible."""
    base_q = select(Request).where(Request.user_id == user_id)
    if status:
        base_q = base_q.where(Request.status == status)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(Request.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()
    return list(entries), total


async def my_offers(
    db: AsyncSession,
    user_id: UUID,
    *,
    status: OfferStatus | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Offer], int]:
    """Owner view — all statuses visible."""
    base_q = select(Offer).where(Offer.user_id == user_id)
    if status:
        base_q = base_q.where(Offer.status == status)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(Offer.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()
    return list(entries), total


async def my_reviews(
    db: AsyncSession,
    user_id: UUID,
    *,
    review_type: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Review], int]:
    """Owner view — received (default) or given reviews."""
    if review_type == "given":
        base_q = select(Review).where(Review.reviewer_id == user_id)
    else:
        base_q = select(Review).where(Review.reviewed_id == user_id)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(Review.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()
    return list(entries), total


async def user_summary(
    db: AsyncSession,
    user_id: UUID,
) -> dict:
    """Dashboard summary — counts of active resources."""
    user = await db.get(User, user_id)

    active_requests = (await db.execute(
        select(func.count()).select_from(
            select(Request).where(Request.user_id == user_id, Request.status == RequestStatus.OPEN).subquery()
        )
    )).scalar() or 0

    active_offers = (await db.execute(
        select(func.count()).select_from(
            select(Offer).where(Offer.user_id == user_id, Offer.status == OfferStatus.ACTIVE).subquery()
        )
    )).scalar() or 0

    participant_filter = (Exchange.requester_id == user_id) | (Exchange.helper_id == user_id)

    pending_exchanges = (await db.execute(
        select(func.count()).select_from(
            select(Exchange).where(participant_filter, Exchange.status == ExchangeStatus.PENDING).subquery()
        )
    )).scalar() or 0

    completed_exchanges = (await db.execute(
        select(func.count()).select_from(
            select(Exchange).where(participant_filter, Exchange.status == ExchangeStatus.COMPLETED).subquery()
        )
    )).scalar() or 0

    reviews_received = (await db.execute(
        select(func.count()).select_from(
            select(Review).where(Review.reviewed_id == user_id).subquery()
        )
    )).scalar() or 0

    return {
        "active_requests": active_requests,
        "active_offers": active_offers,
        "pending_exchanges": pending_exchanges,
        "completed_exchanges": completed_exchanges,
        "heart_balance": user.heart_balance if user else 0,
        "reviews_received": reviews_received,
    }


async def public_profile(
    db: AsyncSession,
    user_id: UUID,
) -> dict:
    """Public profile — limited view, active users only."""
    user = await db.get(User, user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    participant_filter = (Exchange.requester_id == user_id) | (Exchange.helper_id == user_id)

    reviews_received = (await db.execute(
        select(func.count()).select_from(
            select(Review).where(Review.reviewed_id == user_id).subquery()
        )
    )).scalar() or 0

    completed_exchanges = (await db.execute(
        select(func.count()).select_from(
            select(Exchange).where(participant_filter, Exchange.status == ExchangeStatus.COMPLETED).subquery()
        )
    )).scalar() or 0

    return {
        "id": user.id,
        "username": user.username,
        "bio": user.bio,
        "location_id": user.location_id,
        "heart_balance": user.heart_balance,
        "created_at": user.created_at,
        "reviews_received": reviews_received,
        "completed_exchanges": completed_exchanges,
    }
