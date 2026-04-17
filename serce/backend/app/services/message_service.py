"""Message service — send, list, hide (admin)."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.message import Message
from app.db.models.notification import NotificationType
from app.db.models.user import UserRole
from app.services import notification_service


async def send_message(
    db: AsyncSession,
    exchange_id: UUID,
    current_user_id: UUID,
    *,
    content: str,
) -> Message:
    """Send message in exchange chat — participant only, not CANCELLED."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if current_user_id not in (exchange.requester_id, exchange.helper_id):
        raise HTTPException(status_code=403, detail="NOT_PARTICIPANT")
    if exchange.status == ExchangeStatus.CANCELLED:
        raise HTTPException(status_code=422, detail="EXCHANGE_CANCELLED")

    msg = Message(
        exchange_id=exchange_id,
        sender_id=current_user_id,
        content=content,
    )
    db.add(msg)
    await db.flush()

    # Notify other participant
    other_id = (
        exchange.helper_id
        if current_user_id == exchange.requester_id
        else exchange.requester_id
    )
    await notification_service.create_notification(
        db, other_id, NotificationType.NEW_MESSAGE,
        related_exchange_id=exchange_id,
        related_message_id=msg.id,
    )
    return msg


async def list_messages(
    db: AsyncSession,
    exchange_id: UUID,
    current_user_id: UUID,
    *,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Message], int]:
    """List visible messages for exchange — participant only."""
    exchange = await db.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=404, detail="EXCHANGE_NOT_FOUND")
    if current_user_id not in (exchange.requester_id, exchange.helper_id):
        raise HTTPException(status_code=403, detail="NOT_PARTICIPANT")

    base_q = select(Message).where(
        Message.exchange_id == exchange_id,
        Message.is_hidden == False,  # noqa: E712
    )

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(Message.created_at.asc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()

    return list(entries), total


async def hide_message(
    db: AsyncSession,
    exchange_id: UUID,
    message_id: UUID,
    current_user_role: UserRole,
) -> Message:
    """Hide message — admin only."""
    if current_user_role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="ADMIN_ONLY")

    msg = await db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="MESSAGE_NOT_FOUND")
    if msg.exchange_id != exchange_id:
        raise HTTPException(status_code=404, detail="MESSAGE_NOT_FOUND")

    msg.is_hidden = True
    await db.flush()
    return msg
