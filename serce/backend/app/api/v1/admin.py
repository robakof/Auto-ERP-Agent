"""Admin endpoints — flags moderation, suspend, hearts grant, audit log."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.models.admin import AuditTargetType, FlagStatus, FlagTargetType
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.admin import (
    AuditListResponse,
    FlagDetailRead,
    FlagListResponse,
    GrantHeartsBody,
    ResolveFlagBody,
    SuspendUserBody,
    UserAdminRead,
)
from app.schemas.hearts import LedgerEntryRead
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


# ---- Flags ------------------------------------------------------------------

@router.get("/flags", response_model=FlagListResponse)
async def list_flags(
    status: FlagStatus | None = None,
    target_type: FlagTargetType | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    entries, total = await admin_service.list_flags(
        db, status=status, target_type=target_type, offset=offset, limit=limit,
    )
    return FlagListResponse(entries=entries, total=total, offset=offset, limit=limit)


@router.get("/flags/{flag_id}", response_model=FlagDetailRead)
async def get_flag(
    flag_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.get_flag(db, flag_id)


@router.post("/flags/{flag_id}/resolve", response_model=FlagDetailRead)
async def resolve_flag(
    flag_id: UUID,
    body: ResolveFlagBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.resolve_flag(
        db, admin.id, flag_id,
        action=body.action, reason=body.reason, params=body.params,
    )
    await db.commit()
    return result


# ---- Users ------------------------------------------------------------------

@router.post("/users/{user_id}/suspend", response_model=UserAdminRead)
async def suspend_user(
    user_id: UUID,
    body: SuspendUserBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.suspend_user(
        db, admin.id, user_id,
        reason=body.reason, duration_days=body.duration_days,
    )
    await db.commit()
    return result


@router.post("/users/{user_id}/unsuspend", response_model=UserAdminRead)
async def unsuspend_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.unsuspend_user(db, admin.id, user_id)
    await db.commit()
    return result


# ---- Hearts -----------------------------------------------------------------

@router.post("/hearts/grant", response_model=LedgerEntryRead, status_code=201)
async def grant_hearts(
    body: GrantHeartsBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await admin_service.grant_hearts(
        db, admin.id, body.user_id,
        amount=body.amount, ledger_type=body.type, reason=body.reason,
    )
    await db.commit()
    return result


# ---- Audit ------------------------------------------------------------------

@router.get("/audit", response_model=AuditListResponse)
async def list_audit(
    actor_id: UUID | None = None,
    action: str | None = None,
    target_type: AuditTargetType | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    entries, total = await admin_service.list_audit(
        db, actor_id=actor_id, action=action, target_type=target_type,
        from_date=from_date, to_date=to_date, offset=offset, limit=limit,
    )
    return AuditListResponse(entries=entries, total=total, offset=offset, limit=limit)
