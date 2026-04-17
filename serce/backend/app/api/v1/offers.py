"""Offer endpoints — create, get, update, status change, list."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.offer import OfferStatus
from app.db.models.request import LocationScope
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.offer import (
    ChangeOfferStatusBody,
    CreateOfferBody,
    OfferListResponse,
    OfferRead,
    UpdateOfferBody,
)
from app.services import offer_service

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post("", response_model=OfferRead, status_code=201)
@limiter.limit("10/hour")
async def create_offer(
    request: FastAPIRequest,
    req: CreateOfferBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await offer_service.create_offer(
        db,
        current_user.id,
        title=req.title,
        description=req.description,
        hearts_asked=req.hearts_asked,
        category_id=req.category_id,
        location_id=req.location_id,
        location_scope=req.location_scope,
    )
    await db.commit()
    return result


@router.get("/{offer_id}", response_model=OfferRead)
async def get_offer(
    offer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await offer_service.get_offer(db, offer_id, current_user.id)


@router.patch("/{offer_id}", response_model=OfferRead)
async def update_offer(
    offer_id: UUID,
    req: UpdateOfferBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await offer_service.update_offer(
        db,
        offer_id,
        current_user.id,
        title=req.title,
        description=req.description,
        hearts_asked=req.hearts_asked,
    )
    await db.commit()
    return result


@router.patch("/{offer_id}/status", response_model=OfferRead)
async def change_offer_status(
    offer_id: UUID,
    req: ChangeOfferStatusBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await offer_service.change_offer_status(db, offer_id, current_user, req.status)
    await db.commit()
    return result


@router.get("", response_model=OfferListResponse)
async def list_offers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    category_id: int | None = None,
    location_id: int | None = None,
    location_scope: LocationScope | None = None,
    status: OfferStatus | None = Query(default=OfferStatus.ACTIVE),
    q: str | None = Query(None, max_length=100),
    sort: str = Query("created_at", pattern=r"^(created_at|hearts_asked)$"),
    order: str = Query("desc", pattern=r"^(asc|desc)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await offer_service.list_offers(
        db,
        category_id=category_id,
        location_id=location_id,
        location_scope=location_scope,
        status=status or OfferStatus.ACTIVE,
        q=q,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
    return OfferListResponse(entries=entries, total=total, offset=offset, limit=limit)
