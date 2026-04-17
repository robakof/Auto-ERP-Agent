"""Request service — CRUD, listing, search, cancel with Exchange cascade."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.location import Location
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.user import User, UserStatus


async def create_request(
    db: AsyncSession,
    user_id: UUID,
    *,
    title: str,
    description: str,
    hearts_offered: int,
    category_id: int,
    location_id: int,
    location_scope: LocationScope,
    expires_at: datetime | None,
) -> Request:
    """Create a new request. hearts_offered is declarative, not a balance lock."""
    # Validate category
    cat = await db.get(Category, category_id)
    if not cat or not cat.active:
        raise HTTPException(status_code=404, detail="CATEGORY_NOT_FOUND")

    # Validate location
    loc = await db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="LOCATION_NOT_FOUND")

    # Informational guard — hearts not locked at creation
    if hearts_offered > 0:
        user = await db.get(User, user_id)
        if user and user.heart_balance < hearts_offered:
            raise HTTPException(status_code=422, detail="INSUFFICIENT_BALANCE")

    # Expiry
    if expires_at is not None:
        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=422, detail="EXPIRES_IN_PAST")
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.request_default_expiry_days)

    req = Request(
        user_id=user_id,
        title=title,
        description=description,
        hearts_offered=hearts_offered,
        category_id=category_id,
        location_id=location_id,
        location_scope=location_scope,
        status=RequestStatus.OPEN,
        expires_at=expires_at,
    )
    db.add(req)
    await db.flush()
    return req


async def get_request(
    db: AsyncSession, request_id: UUID, current_user_id: UUID,
) -> Request:
    """Get request by id. HIDDEN visible only to owner."""
    req = await db.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="REQUEST_NOT_FOUND")
    if req.status == RequestStatus.HIDDEN and req.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="REQUEST_NOT_FOUND")
    return req


async def update_request(
    db: AsyncSession,
    request_id: UUID,
    current_user_id: UUID,
    *,
    title: str | None = None,
    description: str | None = None,
    hearts_offered: int | None = None,
    expires_at: datetime | None = None,
) -> Request:
    """Update request fields. Owner only, OPEN only."""
    req = await db.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="REQUEST_NOT_FOUND")
    if req.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="NOT_OWNER")
    if req.status != RequestStatus.OPEN:
        raise HTTPException(status_code=422, detail="REQUEST_NOT_EDITABLE")

    # hearts_offered lock check
    if hearts_offered is not None:
        exchange_q = select(func.count()).select_from(
            select(Exchange).where(
                Exchange.request_id == request_id,
                Exchange.status == ExchangeStatus.PENDING,
            ).subquery()
        )
        pending_count = (await db.execute(exchange_q)).scalar() or 0
        if pending_count > 0:
            raise HTTPException(status_code=422, detail="HEARTS_OFFERED_LOCKED")

    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="EXPIRES_IN_PAST")

    if title is not None:
        req.title = title
    if description is not None:
        req.description = description
    if hearts_offered is not None:
        req.hearts_offered = hearts_offered
    if expires_at is not None:
        req.expires_at = expires_at

    await db.flush()
    return req


async def list_requests(
    db: AsyncSession,
    *,
    category_id: int | None = None,
    location_id: int | None = None,
    location_scope: LocationScope | None = None,
    status: RequestStatus = RequestStatus.OPEN,
    q: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Request], int]:
    """List requests with filters, search, pagination. Excludes suspended/deleted users."""
    base_q = (
        select(Request)
        .join(User, Request.user_id == User.id)
        .where(
            Request.status == status,
            User.status == UserStatus.ACTIVE,
        )
    )

    if category_id is not None:
        base_q = base_q.where(Request.category_id == category_id)
    if location_id is not None:
        base_q = base_q.where(Request.location_id == location_id)
    if location_scope is not None:
        base_q = base_q.where(Request.location_scope == location_scope)
    if q:
        pattern = f"%{q}%"
        base_q = base_q.where(
            Request.title.ilike(pattern) | Request.description.ilike(pattern)
        )

    # Count
    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sort
    sort_col = getattr(Request, sort, Request.created_at)
    order_expr = sort_col.desc() if order == "desc" else sort_col.asc()
    entries_q = base_q.order_by(order_expr).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()

    return list(entries), total


async def cancel_request(
    db: AsyncSession, request_id: UUID, current_user_id: UUID,
) -> Request:
    """Cancel request + cascade PENDING Exchanges to CANCELLED."""
    req = await db.get(Request, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="REQUEST_NOT_FOUND")
    if req.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="NOT_OWNER")
    if req.status != RequestStatus.OPEN:
        raise HTTPException(status_code=422, detail="REQUEST_NOT_CANCELLABLE")

    req.status = RequestStatus.CANCELLED

    # Cascade: cancel PENDING exchanges for this request
    await db.execute(
        update(Exchange)
        .where(
            Exchange.request_id == request_id,
            Exchange.status == ExchangeStatus.PENDING,
        )
        .values(status=ExchangeStatus.CANCELLED)
    )

    await db.flush()
    return req
