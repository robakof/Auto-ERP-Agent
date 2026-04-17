"""User resources endpoints — /me/requests, /me/offers, /me/exchanges, /me/reviews, /me/ledger, /me/summary, /users/{id}/profile."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.exchange import ExchangeStatus
from app.db.models.heart import HeartLedgerType
from app.db.models.offer import OfferStatus
from app.db.models.request import RequestStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.exchange import ExchangeListResponse
from app.schemas.hearts import LedgerResponse
from app.schemas.offer import OfferListResponse
from app.schemas.request import RequestListResponse
from app.schemas.review import ReviewListResponse
from app.schemas.user_resources import PublicProfileRead, UserSummary
from app.services import exchange_service, hearts_service, user_resources_service

router = APIRouter(tags=["user-resources"])


@router.get("/users/me/requests", response_model=RequestListResponse)
async def my_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: RequestStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await user_resources_service.my_requests(
        db, current_user.id, status=status, offset=offset, limit=limit,
    )
    return RequestListResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.get("/users/me/offers", response_model=OfferListResponse)
async def my_offers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: OfferStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await user_resources_service.my_offers(
        db, current_user.id, status=status, offset=offset, limit=limit,
    )
    return OfferListResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.get("/users/me/exchanges", response_model=ExchangeListResponse)
async def my_exchanges(
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


@router.get("/users/me/reviews", response_model=ReviewListResponse)
async def my_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    type: str | None = Query(None, pattern=r"^(received|given)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await user_resources_service.my_reviews(
        db, current_user.id, review_type=type, offset=offset, limit=limit,
    )
    return ReviewListResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.get("/users/me/ledger", response_model=LedgerResponse)
async def my_ledger(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    type: HeartLedgerType | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await hearts_service.get_ledger(
        db, current_user.id, type_filter=type, offset=offset, limit=limit,
    )
    return LedgerResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.get("/users/me/summary", response_model=UserSummary)
async def my_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await user_resources_service.user_summary(db, current_user.id)


@router.get("/users/{user_id}/profile", response_model=PublicProfileRead)
async def public_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await user_resources_service.public_profile(db, user_id)
