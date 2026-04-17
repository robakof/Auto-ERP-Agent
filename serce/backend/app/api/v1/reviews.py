"""Review endpoints — create, list per exchange, list per user."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request as FastAPIRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.services.email_service import get_email_service
from app.schemas.review import CreateReviewBody, ReviewListResponse, ReviewRead
from app.services import review_service

router = APIRouter(tags=["reviews"])


@router.post(
    "/exchanges/{exchange_id}/reviews",
    response_model=ReviewRead,
    status_code=201,
)
@limiter.limit("10/hour")
async def create_review(
    request: FastAPIRequest,
    exchange_id: UUID,
    body: CreateReviewBody,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await review_service.create_review(
        db, exchange_id, current_user.id, comment=body.comment,
    )
    await db.commit()

    reviewed = await db.get(User, result.reviewed_id)
    if reviewed and reviewed.email:
        background_tasks.add_task(
            get_email_service().send_notification,
            to=reviewed.email, notification_type="NEW_REVIEW", reason=None,
        )
    return result


@router.get(
    "/exchanges/{exchange_id}/reviews",
    response_model=list[ReviewRead],
)
async def list_exchange_reviews(
    exchange_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await review_service.list_reviews_for_exchange(
        db, exchange_id, current_user.id,
    )


@router.get(
    "/users/{user_id}/reviews",
    response_model=ReviewListResponse,
)
async def list_user_reviews(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    entries, total = await review_service.list_reviews_for_user(
        db, user_id, offset=offset, limit=limit,
    )
    return ReviewListResponse(entries=entries, total=total, offset=offset, limit=limit)
