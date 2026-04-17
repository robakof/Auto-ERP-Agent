"""Notification endpoints — list, mark read, mark all read, unread count."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationRead,
    UnreadCountResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/users/me/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    unread: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await notification_service.list_notifications(
        db, current_user.id, unread_only=unread, offset=offset, limit=limit,
    )
    return NotificationListResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await notification_service.mark_as_read(db, notification_id, current_user.id)
    await db.commit()
    return result


@router.post("/read-all", response_model=MarkAllReadResponse)
@limiter.limit("10/minute")
async def mark_all_as_read(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await notification_service.mark_all_as_read(db, current_user.id)
    await db.commit()
    return MarkAllReadResponse(updated=count)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await notification_service.unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)
