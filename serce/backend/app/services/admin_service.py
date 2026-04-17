"""Admin service — flags, suspend, hearts grant, audit."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.admin import (
    AdminAuditLog,
    AuditTargetType,
    ContentFlag,
    FlagStatus,
    FlagTargetType,
    ResolutionAction,
)
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import Request, RequestStatus
from app.db.models.user import RefreshToken, User, UserRole, UserStatus


# ---- Audit helper ------------------------------------------------------------

async def _log_audit(
    db: AsyncSession,
    admin_id: UUID,
    action: str,
    target_type: AuditTargetType,
    target_id: UUID | None,
    payload: dict,
    reason: str | None = None,
) -> AdminAuditLog:
    entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload=payload,
        reason=reason,
    )
    db.add(entry)
    await db.flush()
    return entry


# ---- Flag management ---------------------------------------------------------

async def list_flags(
    db: AsyncSession,
    *,
    status: FlagStatus | None = None,
    target_type: FlagTargetType | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[ContentFlag], int]:
    base_q = select(ContentFlag)
    if status:
        base_q = base_q.where(ContentFlag.status == status)
    if target_type:
        base_q = base_q.where(ContentFlag.target_type == target_type)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(ContentFlag.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()
    return list(entries), total


async def get_flag(db: AsyncSession, flag_id: UUID) -> ContentFlag:
    flag = await db.get(ContentFlag, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="FLAG_NOT_FOUND")
    return flag


async def resolve_flag(
    db: AsyncSession,
    admin_id: UUID,
    flag_id: UUID,
    *,
    action: ResolutionAction,
    reason: str,
    params: dict | None = None,
) -> ContentFlag:
    """Compound: resolve flag + execute side effect + audit."""
    flag = await db.get(ContentFlag, flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="FLAG_NOT_FOUND")
    if flag.status != FlagStatus.OPEN:
        raise HTTPException(status_code=422, detail="FLAG_ALREADY_RESOLVED")

    # Resolve flag
    flag.status = FlagStatus.DISMISSED if action == ResolutionAction.DISMISS else FlagStatus.RESOLVED
    flag.resolved_by = admin_id
    flag.resolved_at = datetime.now(timezone.utc)
    flag.resolution_action = action
    flag.resolution_reason = reason

    # Side effects
    await _execute_resolution(db, admin_id, flag, action, params)

    await db.flush()

    await _log_audit(
        db, admin_id, "resolve_flag", AuditTargetType.FLAG, flag.id,
        {
            "resolution_action": action.value,
            "resolution_reason": reason,
            "target_type": flag.target_type.value,
            "target_id": str(flag.target_id),
        },
    )
    return flag


async def _execute_resolution(
    db: AsyncSession,
    admin_id: UUID,
    flag: ContentFlag,
    action: ResolutionAction,
    params: dict | None,
) -> None:
    """Execute side effect of flag resolution."""
    if action in (ResolutionAction.DISMISS, ResolutionAction.WARN_USER):
        return

    if action == ResolutionAction.HIDE_CONTENT:
        await _hide_target(db, flag)

    elif action == ResolutionAction.SUSPEND_USER:
        owner_id = await _get_target_owner(db, flag)
        duration = (params or {}).get("duration_days")
        await suspend_user(db, admin_id, owner_id, reason=f"Flag #{flag.id}: {flag.reason.value}", duration_days=duration)

    elif action == ResolutionAction.BAN_USER:
        owner_id = await _get_target_owner(db, flag)
        await suspend_user(db, admin_id, owner_id, reason=f"Ban via flag #{flag.id}: {flag.reason.value}")

    elif action == ResolutionAction.GRANT_HEARTS_REFUND:
        amount = (params or {}).get("amount", 0)
        if amount <= 0:
            raise HTTPException(status_code=422, detail="REFUND_AMOUNT_REQUIRED")
        if flag.reporter_id:
            await grant_hearts(
                db, admin_id, flag.reporter_id,
                amount=amount, ledger_type="ADMIN_REFUND",
                reason=f"Refund for flag #{flag.id}",
            )


async def _hide_target(db: AsyncSession, flag: ContentFlag) -> None:
    if flag.target_type == FlagTargetType.REQUEST:
        obj = await db.get(Request, flag.target_id)
        if obj:
            obj.status = RequestStatus.HIDDEN
    elif flag.target_type == FlagTargetType.OFFER:
        obj = await db.get(Offer, flag.target_id)
        if obj:
            obj.status = OfferStatus.HIDDEN


async def _get_target_owner(db: AsyncSession, flag: ContentFlag) -> UUID:
    if flag.target_type == FlagTargetType.USER:
        return flag.target_id
    elif flag.target_type == FlagTargetType.REQUEST:
        obj = await db.get(Request, flag.target_id)
        if obj:
            return obj.user_id
    elif flag.target_type == FlagTargetType.OFFER:
        obj = await db.get(Offer, flag.target_id)
        if obj:
            return obj.user_id
    elif flag.target_type == FlagTargetType.EXCHANGE:
        raise HTTPException(
            status_code=422,
            detail="SUSPEND_VIA_FLAG_NOT_SUPPORTED_FOR_EXCHANGES",
        )
    raise HTTPException(status_code=422, detail="CANNOT_DETERMINE_OWNER")


# ---- User management --------------------------------------------------------

async def suspend_user(
    db: AsyncSession,
    admin_id: UUID,
    user_id: UUID,
    *,
    reason: str,
    duration_days: int | None = None,
) -> User:
    """Suspend user, revoke all refresh tokens, audit log."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=422, detail="CANNOT_SUSPEND_ADMIN")
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=422, detail="ALREADY_SUSPENDED")

    now = datetime.now(timezone.utc)
    user.status = UserStatus.SUSPENDED
    user.suspended_at = now
    user.suspended_until = now + timedelta(days=duration_days) if duration_days else None
    user.suspension_reason = reason

    # Revoke all refresh tokens
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    revoked_count = result.rowcount

    await db.flush()

    await _log_audit(
        db, admin_id, "suspend_user", AuditTargetType.USER, user_id,
        {"reason": reason, "duration_days": duration_days, "revoked_tokens_count": revoked_count},
    )
    return user


async def unsuspend_user(
    db: AsyncSession,
    admin_id: UUID,
    user_id: UUID,
) -> User:
    """Unsuspend user, clear suspension fields, audit log."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    if user.status != UserStatus.SUSPENDED:
        raise HTTPException(status_code=422, detail="NOT_SUSPENDED")

    user.status = UserStatus.ACTIVE
    user.suspended_at = None
    user.suspended_until = None
    user.suspension_reason = None
    await db.flush()

    await _log_audit(
        db, admin_id, "unsuspend_user", AuditTargetType.USER, user_id, {},
    )
    return user


# ---- Hearts management ------------------------------------------------------

async def grant_hearts(
    db: AsyncSession,
    admin_id: UUID,
    user_id: UUID,
    *,
    amount: int,
    ledger_type: str,
    reason: str,
) -> HeartLedger:
    """Grant/refund hearts to user. No from_user (system action)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    if user.heart_balance + amount > settings.heart_balance_cap:
        raise HTTPException(status_code=422, detail="RECIPIENT_CAP_EXCEEDED")

    user.heart_balance += amount

    ledger = HeartLedger(
        from_user_id=None,
        to_user_id=user_id,
        amount=amount,
        type=HeartLedgerType(ledger_type),
        note=reason,
    )
    db.add(ledger)
    await db.flush()

    await _log_audit(
        db, admin_id, "grant_hearts", AuditTargetType.USER, user_id,
        {"amount": amount, "ledger_type": ledger_type, "note": reason},
    )
    return ledger


# ---- Audit listing -----------------------------------------------------------

async def list_audit(
    db: AsyncSession,
    *,
    actor_id: UUID | None = None,
    action: str | None = None,
    target_type: AuditTargetType | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[AdminAuditLog], int]:
    base_q = select(AdminAuditLog)
    if actor_id:
        base_q = base_q.where(AdminAuditLog.admin_id == actor_id)
    if action:
        base_q = base_q.where(AdminAuditLog.action == action)
    if target_type:
        base_q = base_q.where(AdminAuditLog.target_type == target_type)
    if from_date:
        base_q = base_q.where(AdminAuditLog.created_at >= from_date)
    if to_date:
        base_q = base_q.where(AdminAuditLog.created_at <= to_date)

    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    entries_q = base_q.order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit)
    entries = (await db.execute(entries_q)).scalars().all()
    return list(entries), total
