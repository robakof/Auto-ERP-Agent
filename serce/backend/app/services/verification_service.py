"""Verification service — email verify, phone OTP, password reset, INITIAL_GRANT."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password, hash_token
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    PhoneVerificationOTP,
    RefreshToken,
    User,
)
from app.services.sms_service import generate_otp


# ---- Email verification ------------------------------------------------------

async def create_email_verification(
    db: AsyncSession, user_id: UUID, email: str,
) -> str:
    """Create token, return raw token for sending via email."""
    raw = secrets.token_urlsafe(48)
    token = EmailVerificationToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_expire_hours),
    )
    db.add(token)
    await db.flush()
    return raw


async def verify_email(db: AsyncSession, raw_token: str) -> None:
    """Verify email by token. Sets user.email_verified = True."""
    token = await _find_valid_token(db, EmailVerificationToken, raw_token)
    if not token:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_TOKEN")

    token.used_at = datetime.now(timezone.utc)
    user = await db.get(User, token.user_id)
    if user:
        user.email_verified = True
    await db.flush()


async def resend_email_verification(
    db: AsyncSession, email: str,
) -> tuple[str, UUID] | None:
    """Create new verification token. Returns (raw_token, user_id) or None if email not found.

    Rate: max 3 active tokens per email per 24h.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None

    # Rate check: count ALL tokens created in last 24h (not just unused — C1 fix)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    count_result = await db.execute(
        select(func.count()).select_from(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.created_at >= since,
        )
    )
    count = count_result.scalar() or 0
    if count >= 3:
        raise HTTPException(status_code=429, detail="RESEND_RATE_EXCEEDED")

    # Invalidate old tokens
    old_result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_(None),
        )
    )
    for old in old_result.scalars().all():
        old.used_at = datetime.now(timezone.utc)

    raw = await create_email_verification(db, user.id, user.email)
    await db.flush()
    return raw, user.id


# ---- Phone OTP ---------------------------------------------------------------

async def create_phone_otp(
    db: AsyncSession, user_id: UUID, phone_number: str,
) -> str:
    """Create OTP, return plain code for sending via SMS."""
    # Max 3 active OTPs per user
    active_result = await db.execute(
        select(func.count()).select_from(PhoneVerificationOTP).where(
            PhoneVerificationOTP.user_id == user_id,
            PhoneVerificationOTP.used_at.is_(None),
            PhoneVerificationOTP.expires_at > datetime.now(timezone.utc),
        )
    )
    active_count = active_result.scalar() or 0
    if active_count >= 3:
        raise HTTPException(status_code=429, detail="OTP_RATE_EXCEEDED")

    code = generate_otp()
    otp = PhoneVerificationOTP(
        user_id=user_id,
        phone_number=phone_number,
        code_hash=hash_token(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.phone_otp_expire_minutes),
    )
    db.add(otp)
    await db.flush()
    return code


async def verify_phone(
    db: AsyncSession, user_id: UUID, phone_number: str, code: str,
) -> bool:
    """Verify phone by OTP. Returns True if INITIAL_GRANT was triggered."""
    otp = await _find_valid_otp(db, user_id, phone_number, code)
    if not otp:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_CODE")

    otp.used_at = datetime.now(timezone.utc)
    user = await db.get(User, user_id)
    if user:
        user.phone_verified = True
        user.phone_number = phone_number

    granted = await _grant_initial_hearts(db, user_id)
    await db.flush()
    return granted


async def _find_valid_otp(
    db: AsyncSession, user_id: UUID, phone_number: str, code: str,
) -> PhoneVerificationOTP | None:
    """Find matching OTP. Increments attempts on wrong code."""
    result = await db.execute(
        select(PhoneVerificationOTP).where(
            PhoneVerificationOTP.user_id == user_id,
            PhoneVerificationOTP.phone_number == phone_number,
            PhoneVerificationOTP.used_at.is_(None),
            PhoneVerificationOTP.expires_at > datetime.now(timezone.utc),
        ).order_by(PhoneVerificationOTP.created_at.desc())
    )
    otps = result.scalars().all()

    code_hash = hash_token(code)
    for otp in otps:
        if otp.attempts >= settings.phone_otp_max_attempts:
            continue
        if otp.code_hash == code_hash:
            return otp
        # Wrong code — increment attempts
        otp.attempts += 1
        await db.flush()

    return None


# ---- Password reset -----------------------------------------------------------

async def create_password_reset(
    db: AsyncSession, email: str,
) -> tuple[str, UUID] | None:
    """Create reset token. Returns (raw_token, user_id) or None if email not found."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None

    raw = secrets.token_urlsafe(48)
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_expire_minutes),
    )
    db.add(token)
    await db.flush()
    return raw, user.id


async def reset_password(
    db: AsyncSession, raw_token: str, new_password: str,
) -> None:
    """Reset password by token. Revokes all refresh tokens (force re-login)."""
    token = await _find_valid_token(db, PasswordResetToken, raw_token)
    if not token:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_TOKEN")

    token.used_at = datetime.now(timezone.utc)
    user = await db.get(User, token.user_id)
    if user:
        user.password_hash = hash_password(new_password)

    # Revoke ALL refresh tokens — force re-login everywhere
    rt_result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == token.user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    for rt in rt_result.scalars().all():
        rt.revoked_at = now

    await db.flush()


# ---- INITIAL_GRANT ------------------------------------------------------------

async def _grant_initial_hearts(db: AsyncSession, user_id: UUID) -> bool:
    """Grant initial hearts on first phone verification. Idempotent. Returns True if granted."""
    existing = await db.execute(
        select(HeartLedger).where(
            HeartLedger.to_user_id == user_id,
            HeartLedger.type == HeartLedgerType.INITIAL_GRANT,
        )
    )
    if existing.scalar_one_or_none():
        return False

    db.add(HeartLedger(
        to_user_id=user_id,
        amount=settings.initial_heart_grant,
        type=HeartLedgerType.INITIAL_GRANT,
        note="Phone verification",
    ))
    user = await db.get(User, user_id)
    if user:
        user.heart_balance += settings.initial_heart_grant
    return True


# ---- Shared helpers -----------------------------------------------------------

async def _find_valid_token(db: AsyncSession, model, raw_token: str):
    """Find unexpired, unused token by hash."""
    token_hash = hash_token(raw_token)
    result = await db.execute(
        select(model).where(
            model.token_hash == token_hash,
            model.used_at.is_(None),
            model.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()
