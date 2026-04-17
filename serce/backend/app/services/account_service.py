"""Account service — soft delete (8-step atomic cascade)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import verify_password
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.notification import NotificationType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import Request, RequestStatus
from app.db.models.user import RefreshToken, User, UserStatus
from app.services import notification_service
from app.services.exchange_service import other_party


@dataclass
class AffectedParty:
    user_id: UUID
    exchange_id: UUID


async def soft_delete_account(
    db: AsyncSession,
    user_id: UUID,
    *,
    password: str,
    balance_disposition: str,
    transfer_to_user_id: UUID | None = None,
) -> list[AffectedParty]:
    """Atomic 8-step account deletion. Returns affected parties for email."""

    # Step 0: Load user + verify password (FOR UPDATE — concurrent safety)
    row = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = row.scalar_one_or_none()
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="WRONG_PASSWORD")

    # Step 1: Validate disposition
    if balance_disposition == "transfer":
        if not transfer_to_user_id:
            raise HTTPException(status_code=422, detail="TRANSFER_RECIPIENT_REQUIRED")
        if transfer_to_user_id == user_id:
            raise HTTPException(status_code=422, detail="CANNOT_TRANSFER_TO_SELF")

    # Step 2: Cancel active exchanges + refund + collect notifications
    participant_filter = (Exchange.requester_id == user_id) | (Exchange.helper_id == user_id)
    exchanges_q = select(Exchange).where(
        participant_filter,
        Exchange.status.in_([ExchangeStatus.PENDING, ExchangeStatus.ACCEPTED]),
    )
    exchanges = (await db.execute(exchanges_q)).scalars().all()

    affected_parties: list[AffectedParty] = []

    for ex in exchanges:
        # Refund if ACCEPTED escrow
        if ex.status == ExchangeStatus.ACCEPTED and ex.hearts_agreed and ex.hearts_agreed > 0:
            requester = await db.get(User, ex.requester_id)
            if requester:
                requester.heart_balance += ex.hearts_agreed
                ledger = HeartLedger(
                    from_user_id=ex.requester_id,
                    to_user_id=ex.requester_id,
                    amount=ex.hearts_agreed,
                    type=HeartLedgerType.EXCHANGE_REFUND,
                    related_exchange_id=ex.id,
                )
                db.add(ledger)

        ex.status = ExchangeStatus.CANCELLED

        # Safety: reopen other party's request if needed (D4)
        if ex.request_id:
            request = await db.get(Request, ex.request_id)
            if request and request.user_id != user_id and request.status != RequestStatus.OPEN:
                request.status = RequestStatus.OPEN

        # Notification to other party
        other_id = other_party(ex, user_id)
        await notification_service.create_notification(
            db, other_id, NotificationType.EXCHANGE_CANCELLED,
            reason="account_deleted", related_exchange_id=ex.id,
        )
        affected_parties.append(AffectedParty(user_id=other_id, exchange_id=ex.id))

    # Step 3: Cancel OPEN requests
    await db.execute(
        update(Request)
        .where(Request.user_id == user_id, Request.status == RequestStatus.OPEN)
        .values(status=RequestStatus.CANCELLED)
    )

    # Step 4: Deactivate offers
    await db.execute(
        update(Offer)
        .where(Offer.user_id == user_id, Offer.status.in_([OfferStatus.ACTIVE, OfferStatus.PAUSED]))
        .values(status=OfferStatus.INACTIVE)
    )

    # Step 5: Heart disposition (on FINAL balance after refunds)
    # Re-read user to get updated balance after potential refunds
    await db.refresh(user)

    if user.heart_balance > 0:
        if balance_disposition == "void":
            ledger = HeartLedger(
                from_user_id=user_id,
                to_user_id=None,
                amount=user.heart_balance,
                type=HeartLedgerType.ACCOUNT_DELETED,
            )
            db.add(ledger)
            user.heart_balance = 0
        elif balance_disposition == "transfer":
            row = await db.execute(
                select(User).where(User.id == transfer_to_user_id).with_for_update()
            )
            recipient = row.scalar_one_or_none()
            if not recipient or recipient.status != UserStatus.ACTIVE:
                raise HTTPException(status_code=422, detail="RECIPIENT_NOT_FOUND")
            if recipient.heart_balance + user.heart_balance > settings.heart_balance_cap:
                raise HTTPException(status_code=422, detail="RECIPIENT_CAP_EXCEEDED")
            recipient.heart_balance += user.heart_balance
            ledger = HeartLedger(
                from_user_id=user_id,
                to_user_id=transfer_to_user_id,
                amount=user.heart_balance,
                type=HeartLedgerType.GIFT,
                note="Balance transfer — account deletion",
            )
            db.add(ledger)
            user.heart_balance = 0

    # Step 6: Anonymize
    anon = hashlib.sha256(user.email.encode()).hexdigest()[:16]
    user.email = f"deleted_{anon}@deleted.local"
    user.username = f"deleted_{anon}"
    user.phone_number = None
    user.bio = None
    user.location_id = None
    user.password_hash = "!"
    user.email_verified = False
    user.phone_verified = False

    # Step 7: Set status + timestamps
    now = datetime.now(timezone.utc)
    user.status = UserStatus.DELETED
    user.deleted_at = now
    user.anonymized_at = now

    # Step 8: Revoke all refresh tokens
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )

    await db.flush()
    return affected_parties
