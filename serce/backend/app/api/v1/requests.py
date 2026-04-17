"""Request endpoints — create, get, update, list, cancel."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.request import LocationScope, RequestStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.request import (
    CancelResponse,
    CreateRequestBody,
    RequestListResponse,
    RequestRead,
    UpdateRequestBody,
)
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=RequestRead, status_code=201)
@limiter.limit("10/hour")
async def create_request(
    request: FastAPIRequest,
    req: CreateRequestBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await request_service.create_request(
        db,
        current_user.id,
        title=req.title,
        description=req.description,
        hearts_offered=req.hearts_offered,
        category_id=req.category_id,
        location_id=req.location_id,
        location_scope=req.location_scope,
        expires_at=req.expires_at,
    )
    await db.commit()
    return result


@router.get("/{request_id}", response_model=RequestRead)
async def get_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await request_service.get_request(db, request_id, current_user.id)


@router.patch("/{request_id}", response_model=RequestRead)
async def update_request(
    request_id: UUID,
    req: UpdateRequestBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await request_service.update_request(
        db,
        request_id,
        current_user.id,
        title=req.title,
        description=req.description,
        hearts_offered=req.hearts_offered,
        expires_at=req.expires_at,
    )
    await db.commit()
    return result


@router.get("", response_model=RequestListResponse)
async def list_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    category_id: int | None = None,
    location_id: int | None = None,
    location_scope: LocationScope | None = None,
    status: RequestStatus | None = Query(default=RequestStatus.OPEN),
    q: str | None = Query(None, max_length=100),
    sort: str = Query("created_at", pattern=r"^(created_at|hearts_offered|expires_at)$"),
    order: str = Query("desc", pattern=r"^(asc|desc)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await request_service.list_requests(
        db,
        category_id=category_id,
        location_id=location_id,
        location_scope=location_scope,
        status=status or RequestStatus.OPEN,
        q=q,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
    return RequestListResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.post("/{request_id}/cancel", response_model=CancelResponse)
async def cancel_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await request_service.cancel_request(db, request_id, current_user.id)
    await db.commit()
    return result
