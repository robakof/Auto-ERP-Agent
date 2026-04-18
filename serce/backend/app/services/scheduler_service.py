"""Scheduler service — periodic background jobs."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.notification import NotificationType
from app.db.models.request import Request, RequestStatus
from app.db.models.user import User
from app.db.session import async_session_factory
from app.services.email_service import get_email_service
from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)


async def expire_requests_job() -> int:
    """Batch expire OPEN requests where expires_at < now().

    For each expired request:
    1. Set status = CANCELLED
    2. Cancel PENDING Exchanges (cascade)
    3. Create Notification REQUEST_EXPIRED
    4. Send email (best-effort, fire-and-forget)

    Returns number of expired requests.
    """
    async with async_session_factory() as db:
        expired = await _fetch_expired_requests(db)
        if not expired:
            return 0

        for req in expired:
            req.status = RequestStatus.CANCELLED
            await _cascade_cancel_exchanges(db, req.id)
            await create_notification(
                db, req.user_id, NotificationType.REQUEST_EXPIRED,
            )

        await db.commit()

        # Best-effort emails (after commit — fire-and-forget)
        await _send_expiry_emails(db, expired)

        logger.info("Expired %d requests", len(expired))
        return len(expired)


async def _fetch_expired_requests(db: AsyncSession) -> list[Request]:
    """SELECT FOR UPDATE expired OPEN requests."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Request)
        .where(
            Request.status == RequestStatus.OPEN,
            Request.expires_at < now,
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _cascade_cancel_exchanges(db: AsyncSession, request_id: UUID) -> int:
    """Cancel PENDING exchanges for a given request. Returns count."""
    result = await db.execute(
        update(Exchange)
        .where(
            Exchange.request_id == request_id,
            Exchange.status == ExchangeStatus.PENDING,
        )
        .values(status=ExchangeStatus.CANCELLED)
    )
    return result.rowcount


async def _send_expiry_emails(db: AsyncSession, requests: list[Request]) -> None:
    """Send expiry email per user. Best-effort — failures logged, not raised."""
    email_svc = get_email_service()
    user_ids = {r.user_id for r in requests}
    users = (await db.execute(
        select(User).where(User.id.in_(user_ids))
    )).scalars().all()
    user_map = {u.id: u for u in users}

    for req in requests:
        user = user_map.get(req.user_id)
        if not user:
            continue
        try:
            await email_svc.send_notification(
                user.email, NotificationType.REQUEST_EXPIRED.value, None,
            )
        except Exception:
            logger.warning("Failed to send expiry email for request %s", req.id)
