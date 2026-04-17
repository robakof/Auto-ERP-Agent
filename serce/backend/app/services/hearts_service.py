"""Hearts service — atomic gift transfer, balance, ledger queries."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.notification import NotificationType
from app.db.models.user import User, UserStatus
from app.services import notification_service


async def gift_hearts(
    db: AsyncSession,
    from_user_id: UUID,
    to_user_id: UUID,
    amount: int,
    note: str | None,
) -> HeartLedger:
    """Atomic heart transfer (GIFT).

    Uses SELECT FOR UPDATE with sorted lock order to prevent deadlocks
    and ensure balance never goes below 0.
    """
    if from_user_id == to_user_id:
        raise HTTPException(status_code=422, detail="CANNOT_GIFT_SELF")

    # Lock both users in deterministic order (prevent deadlock)
    user_ids = sorted([from_user_id, to_user_id])
    users: dict[UUID, User | None] = {}
    for uid in user_ids:
        result = await db.execute(
            select(User).where(User.id == uid).with_for_update()
        )
        users[uid] = result.scalar_one_or_none()

    sender = users[from_user_id]
    recipient = users[to_user_id]

    if not sender:
        raise HTTPException(status_code=404, detail="SENDER_NOT_FOUND")
    if not recipient:
        raise HTTPException(status_code=404, detail="RECIPIENT_NOT_FOUND")
    if recipient.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=422, detail="RECIPIENT_NOT_ACTIVE")

    if sender.heart_balance < amount:
        raise HTTPException(status_code=422, detail="INSUFFICIENT_BALANCE")

    max_receivable = settings.heart_balance_cap - recipient.heart_balance
    if amount > max_receivable:
        raise HTTPException(status_code=422, detail="RECIPIENT_CAP_EXCEEDED")

    # Atomic update
    sender.heart_balance -= amount
    recipient.heart_balance += amount

    ledger = HeartLedger(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        amount=amount,
        type=HeartLedgerType.GIFT,
        note=note,
    )
    db.add(ledger)
    await db.flush()

    await notification_service.create_notification(
        db, to_user_id, NotificationType.HEARTS_RECEIVED,
        reason=note,
    )
    return ledger


async def get_balance(db: AsyncSession, user_id: UUID) -> int:
    """Get current heart balance."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    return user.heart_balance


async def get_ledger(
    db: AsyncSession,
    user_id: UUID,
    *,
    type_filter: HeartLedgerType | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[HeartLedger], int]:
    """Get paginated ledger entries for user. Returns (entries, total_count)."""
    base_filter = (HeartLedger.from_user_id == user_id) | (HeartLedger.to_user_id == user_id)

    if type_filter:
        base_filter = base_filter & (HeartLedger.type == type_filter)

    # Count
    count_q = select(func.count()).select_from(
        select(HeartLedger).where(base_filter).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch page
    entries_q = (
        select(HeartLedger)
        .where(base_filter)
        .order_by(HeartLedger.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    entries = (await db.execute(entries_q)).scalars().all()

    return list(entries), total
