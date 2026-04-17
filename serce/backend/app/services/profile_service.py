"""Profile service — profile mutations, email/phone/username change, password change."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.email_denylist import is_disposable_email
from app.core.security import hash_password, hash_token, verify_password
from app.db.models.location import Location
from app.db.models.user import (
    EmailChangeToken,
    PhoneVerificationOTP,
    RefreshToken,
    User,
)
from app.services.sms_service import generate_otp
from app.services.verification_service import _find_valid_otp


# ---- Profile -----------------------------------------------------------------

async def update_profile(
    db: AsyncSession, user_id: UUID, *, bio: str | None, location_id: int | None,
) -> User:
    """Update bio and/or location_id. Validates location exists."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    if location_id is not None:
        loc = await db.get(Location, location_id)
        if not loc:
            raise HTTPException(status_code=422, detail="INVALID_LOCATION_ID")

    if bio is not None:
        user.bio = bio
    if location_id is not None:
        user.location_id = location_id

    await db.flush()
    return user


# ---- Username ----------------------------------------------------------------

async def change_username(
    db: AsyncSession, user_id: UUID, new_username: str,
) -> None:
    """Change username. Unique check."""
    existing = await db.execute(select(User).where(User.username == new_username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="USERNAME_TAKEN")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    user.username = new_username
    await db.flush()


# ---- Email change ------------------------------------------------------------

async def initiate_email_change(
    db: AsyncSession, user_id: UUID, password: str, new_email: str,
) -> str:
    """Verify password, create EmailChangeToken. Returns raw token."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="WRONG_PASSWORD")

    if is_disposable_email(new_email):
        raise HTTPException(status_code=422, detail="DISPOSABLE_EMAIL")

    existing = await db.execute(select(User).where(User.email == new_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="EMAIL_TAKEN")

    raw = secrets.token_urlsafe(48)
    token = EmailChangeToken(
        user_id=user_id,
        new_email=new_email,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_expire_hours),
    )
    db.add(token)
    await db.flush()
    return raw


async def confirm_email_change(
    db: AsyncSession, raw_token: str,
) -> tuple[str, str]:
    """Confirm email change. Returns (old_email, new_email)."""
    token_hash = hash_token(raw_token)
    result = await db.execute(
        select(EmailChangeToken).where(
            EmailChangeToken.token_hash == token_hash,
            EmailChangeToken.used_at.is_(None),
            EmailChangeToken.expires_at > datetime.now(timezone.utc),
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_TOKEN")

    # Double-check: new_email still available
    existing = await db.execute(select(User).where(User.email == token.new_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="EMAIL_TAKEN")

    user = await db.get(User, token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    old_email = user.email
    user.email = token.new_email
    user.email_verified = False
    token.used_at = datetime.now(timezone.utc)
    await db.flush()
    return old_email, token.new_email


# ---- Phone change ------------------------------------------------------------

async def initiate_phone_change(
    db: AsyncSession, user_id: UUID, password: str, new_phone: str,
) -> str:
    """Verify password, create OTP for new phone. Returns code."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="WRONG_PASSWORD")

    existing = await db.execute(select(User).where(User.phone_number == new_phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="PHONE_TAKEN")

    code = generate_otp()
    otp = PhoneVerificationOTP(
        user_id=user_id,
        phone_number=new_phone,
        code_hash=hash_token(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.phone_otp_expire_minutes),
    )
    db.add(otp)
    await db.flush()
    return code


async def confirm_phone_change(
    db: AsyncSession, user_id: UUID, new_phone: str, code: str,
) -> None:
    """Verify OTP and change phone. No INITIAL_GRANT."""
    otp = await _find_valid_otp(db, user_id, new_phone, code)
    if not otp:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_CODE")

    otp.used_at = datetime.now(timezone.utc)
    user = await db.get(User, user_id)
    if user:
        user.phone_number = new_phone
        user.phone_verified = True
    await db.flush()


# ---- Password change ---------------------------------------------------------

async def change_password(
    db: AsyncSession, user_id: UUID, old_password: str, new_password: str,
) -> None:
    """Change password. Revokes all other refresh tokens (force re-login)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="WRONG_PASSWORD")

    user.password_hash = hash_password(new_password)

    # Revoke all refresh tokens — force re-login everywhere
    rt_result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    for rt in rt_result.scalars().all():
        rt.revoked_at = now

    await db.flush()
