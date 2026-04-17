"""Notification service — create, list, mark read, unread count."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    type: NotificationType,
    *,
    reason: str | None = None,
    related_exchange_id: UUID | None = None,
    related_message_id: UUID | None = None,
) -> Notification:
    """Create in-app notification. Same transaction as caller (flush only)."""
    notif = Notification(
        user_id=user_id,
        type=type,
        reason=reason,
        related_exchange_id=related_exchange_id,
        related_message_id=related_message_id,
    )
    db.add(notif)
    await db.flush()
    return notif


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    *,
    unread_only: bool = False,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Notification], int]:
    """List notifications for user, newest first."""
    base_q = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        base_q = base_q.where(Notification.is_read == False)  # noqa: E712

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()

    return list(entries), total


async def mark_as_read(
    db: AsyncSession,
    notification_id: UUID,
    current_user_id: UUID,
) -> Notification:
    """Mark single notification as read. 404 if not found or wrong user."""
    notif = await db.get(Notification, notification_id)
    if not notif or notif.user_id != current_user_id:
        raise HTTPException(status_code=404, detail="NOTIFICATION_NOT_FOUND")
    notif.is_read = True
    await db.flush()
    return notif


async def mark_all_as_read(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Mark all unread notifications as read. Returns count of updated."""
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    await db.flush()
    return result.rowcount


async def unread_count(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Count unread notifications for user."""
    q = select(func.count()).select_from(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        ).subquery()
    )
    return (await db.execute(q)).scalar() or 0
