"""Message endpoints — send, list, hide."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.exchange import Exchange
from app.db.models.user import User
from app.db.session import get_db
from app.services.email_service import get_email_service
from app.services.exchange_service import other_party
from app.schemas.message import MessageListResponse, MessageRead, SendMessageBody
from app.services import message_service

router = APIRouter(prefix="/exchanges/{exchange_id}/messages", tags=["messages"])


@router.post("", response_model=MessageRead, status_code=201)
@limiter.limit("30/hour")
async def send_message(
    request: FastAPIRequest,
    exchange_id: UUID,
    body: SendMessageBody,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await message_service.send_message(
        db, exchange_id, current_user.id, content=body.content,
    )
    await db.commit()

    exchange = await db.get(Exchange, exchange_id)
    if exchange:
        other = await db.get(User, other_party(exchange, current_user.id))
        if other and other.email:
            background_tasks.add_task(
                get_email_service().send_notification,
                to=other.email, notification_type="NEW_MESSAGE", reason=None,
            )
    return result


@router.get("", response_model=MessageListResponse)
async def list_messages(
    exchange_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    entries, total = await message_service.list_messages(
        db, exchange_id, current_user.id, offset=offset, limit=limit,
    )
    return MessageListResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.patch("/{message_id}/hide", response_model=MessageRead)
async def hide_message(
    exchange_id: UUID,
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await message_service.hide_message(
        db, exchange_id, message_id, current_user.role,
    )
    await db.commit()
    return result
