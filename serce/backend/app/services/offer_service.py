"""Offer service — CRUD, listing, status management with Exchange cascade."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.location import Location
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import LocationScope
from app.db.models.user import User, UserRole, UserStatus


# Allowed owner transitions
_OWNER_TRANSITIONS: dict[OfferStatus, set[OfferStatus]] = {
    OfferStatus.ACTIVE: {OfferStatus.PAUSED, OfferStatus.INACTIVE},
    OfferStatus.PAUSED: {OfferStatus.ACTIVE, OfferStatus.INACTIVE},
}


async def create_offer(
    db: AsyncSession,
    user_id: UUID,
    *,
    title: str,
    description: str,
    hearts_asked: int,
    category_id: int,
    location_id: int,
    location_scope: LocationScope,
) -> Offer:
    """Create a new offer. No balance guard — hearts_asked is an expectation."""
    cat = await db.get(Category, category_id)
    if not cat or not cat.active:
        raise HTTPException(status_code=404, detail="CATEGORY_NOT_FOUND")

    loc = await db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="LOCATION_NOT_FOUND")

    offer = Offer(
        user_id=user_id,
        title=title,
        description=description,
        hearts_asked=hearts_asked,
        category_id=category_id,
        location_id=location_id,
        location_scope=location_scope,
        status=OfferStatus.ACTIVE,
    )
    db.add(offer)
    await db.flush()
    return offer


async def get_offer(
    db: AsyncSession, offer_id: UUID, current_user_id: UUID,
) -> Offer:
    """Get offer by id. HIDDEN/INACTIVE visible only to owner."""
    offer = await db.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="OFFER_NOT_FOUND")
    if offer.status in (OfferStatus.HIDDEN, OfferStatus.INACTIVE) and offer.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="OFFER_NOT_FOUND")
    return offer


async def update_offer(
    db: AsyncSession,
    offer_id: UUID,
    current_user_id: UUID,
    *,
    title: str | None = None,
    description: str | None = None,
    hearts_asked: int | None = None,
) -> Offer:
    """Update offer fields. Owner only, ACTIVE/PAUSED only."""
    offer = await db.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="OFFER_NOT_FOUND")
    if offer.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="NOT_OWNER")
    if offer.status not in (OfferStatus.ACTIVE, OfferStatus.PAUSED):
        raise HTTPException(status_code=422, detail="OFFER_NOT_EDITABLE")

    if title is not None:
        offer.title = title
    if description is not None:
        offer.description = description
    if hearts_asked is not None:
        offer.hearts_asked = hearts_asked

    await db.flush()
    return offer


async def change_offer_status(
    db: AsyncSession,
    offer_id: UUID,
    current_user: User,
    new_status: OfferStatus,
) -> Offer:
    """Change offer status. Owner: ACTIVE↔PAUSED, →INACTIVE. Admin: →HIDDEN."""
    offer = await db.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="OFFER_NOT_FOUND")

    is_owner = offer.user_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    # Admin can set HIDDEN from any state
    if new_status == OfferStatus.HIDDEN:
        if not is_admin:
            raise HTTPException(status_code=403, detail="NOT_OWNER")
    else:
        # Owner transitions
        if not is_owner:
            raise HTTPException(status_code=403, detail="NOT_OWNER")
        allowed = _OWNER_TRANSITIONS.get(offer.status, set())
        if new_status not in allowed:
            raise HTTPException(status_code=422, detail="INVALID_STATUS_TRANSITION")

    # Cascade: INACTIVE cancels PENDING Exchanges
    if new_status == OfferStatus.INACTIVE:
        await db.execute(
            update(Exchange)
            .where(
                Exchange.offer_id == offer_id,
                Exchange.status == ExchangeStatus.PENDING,
            )
            .values(status=ExchangeStatus.CANCELLED)
        )

    offer.status = new_status
    await db.flush()
    return offer


async def list_offers(
    db: AsyncSession,
    *,
    category_id: int | None = None,
    location_id: int | None = None,
    location_scope: LocationScope | None = None,
    status: OfferStatus = OfferStatus.ACTIVE,
    q: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Offer], int]:
    """List offers with filters, search, pagination. Excludes suspended/deleted users."""
    base_q = (
        select(Offer)
        .join(User, Offer.user_id == User.id)
        .where(
            Offer.status == status,
            User.status == UserStatus.ACTIVE,
        )
    )

    if category_id is not None:
        base_q = base_q.where(Offer.category_id == category_id)
    if location_id is not None:
        base_q = base_q.where(Offer.location_id == location_id)
    if location_scope is not None:
        base_q = base_q.where(Offer.location_scope == location_scope)
    if q:
        pattern = f"%{q}%"
        base_q = base_q.where(
            Offer.title.ilike(pattern) | Offer.description.ilike(pattern)
        )

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    sort_col = getattr(Offer, sort, Offer.created_at)
    order_expr = sort_col.desc() if order == "desc" else sort_col.asc()
    entries_q = base_q.order_by(order_expr).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()

    return list(entries), total
