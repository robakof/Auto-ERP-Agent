"""Auth business logic — register, login, refresh, logout."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.email_denylist import is_disposable_email
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models.admin import SystemConfig
from app.db.models.user import (
    DocumentType,
    RefreshToken,
    User,
    UserConsent,
    UserStatus,
)
from app.schemas.auth import RegisterRequest


async def register_user(
    db: AsyncSession,
    req: RegisterRequest,
    ip_address: str,
) -> tuple[User, str, str]:
    """Create user + initial consents. Returns (user, access_token, raw_refresh)."""
    if not req.tos_accepted or not req.privacy_policy_accepted:
        raise HTTPException(
            status_code=422,
            detail="Musisz zaakceptowac regulamin i polityke prywatnosci.",
        )

    if is_disposable_email(req.email):
        raise HTTPException(
            status_code=422,
            detail="DISPOSABLE_EMAIL",
        )

    # Check unique email
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="EMAIL_TAKEN",
        )

    # Check unique username
    existing_u = await db.execute(select(User).where(User.username == req.username))
    if existing_u.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="USERNAME_TAKEN",
        )

    user = User(
        email=req.email,
        username=req.username,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    await db.flush()

    # Record consents
    for doc_type in (DocumentType.TOS, DocumentType.PRIVACY_POLICY):
        db.add(UserConsent(
            user_id=user.id,
            document_type=doc_type,
            document_version="1.0",
            ip_address=ip_address,
        ))

    # Issue tokens
    access = create_access_token(user.id)
    raw_refresh, refresh_hash = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))

    await db.commit()
    await db.refresh(user)
    return user, access, raw_refresh


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: str,
    device_info: str | None = None,
) -> tuple[User, str, str]:
    """Authenticate user. Returns (user, access_token, raw_refresh)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="INVALID_CREDENTIALS",
        )
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail="ACCOUNT_NOT_ACTIVE",
        )

    access = create_access_token(user.id)
    raw_refresh, refresh_hash = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        ip_address=ip_address,
        device_info=device_info,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    await db.commit()
    await db.refresh(user)
    return user, access, raw_refresh


async def refresh_tokens(
    db: AsyncSession,
    raw_refresh: str,
    ip_address: str,
) -> tuple[str, str]:
    """Rotate refresh token. Returns (new_access, new_raw_refresh)."""
    token_hash = hash_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="INVALID_REFRESH_TOKEN",
        )
    if token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=401,
            detail="REFRESH_TOKEN_EXPIRED",
        )

    # Revoke old, issue new
    token.revoked_at = datetime.now(timezone.utc)

    new_raw, new_hash = create_refresh_token()
    db.add(RefreshToken(
        user_id=token.user_id,
        token_hash=new_hash,
        ip_address=ip_address,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    await db.commit()

    access = create_access_token(token.user_id)
    return access, new_raw


async def logout_session(
    db: AsyncSession,
    raw_refresh: str,
) -> None:
    """Revoke a specific refresh token."""
    token_hash = hash_token(raw_refresh)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    token = result.scalar_one_or_none()
    if token:
        token.revoked_at = datetime.now(timezone.utc)
        await db.commit()


async def logout_all(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Revoke all active refresh tokens for user. Returns count revoked."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    tokens = result.scalars().all()
    now = datetime.now(timezone.utc)
    for t in tokens:
        t.revoked_at = now
    await db.commit()
    return len(tokens)


async def list_sessions(
    db: AsyncSession,
    user_id: UUID,
) -> list[RefreshToken]:
    """List active (non-revoked, non-expired) sessions for user."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        ).order_by(RefreshToken.created_at.desc())
    )
    return list(result.scalars().all())


async def accept_terms(
    db: AsyncSession,
    user_id: UUID,
    document_type_str: str,
    ip_address: str,
) -> None:
    """Record acceptance of current TOS or privacy policy version."""
    doc_type = DocumentType(document_type_str)

    # Fetch current required version from SystemConfig
    config_key = (
        "tos_current_version"
        if doc_type == DocumentType.TOS
        else "privacy_current_version"
    )
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config_key)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=500, detail="MISSING_CONFIG")

    current_version = config.value

    # Check if already accepted this version
    existing = await db.execute(
        select(UserConsent).where(
            UserConsent.user_id == user_id,
            UserConsent.document_type == doc_type,
            UserConsent.document_version == current_version,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="ALREADY_ACCEPTED")

    db.add(UserConsent(
        user_id=user_id,
        document_type=doc_type,
        document_version=current_version,
        ip_address=ip_address,
    ))
    await db.commit()


async def revoke_session(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
) -> None:
    """Revoke a specific session by ID. Only owner can revoke."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.id == session_id,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )
    token.revoked_at = datetime.now(timezone.utc)
    await db.commit()
