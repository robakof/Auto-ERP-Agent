"""FastAPI dependencies — auth guards."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.models.user import User, UserRole, UserStatus
from app.db.session import get_db

_bearer = HTTPBearer()


@dataclass
class AuthContext:
    """Authenticated user + session metadata from JWT."""

    user: User
    session_id: UUID | None


async def get_auth_context(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Decode JWT, load user, verify active status. Returns AuthContext."""
    result = decode_access_token(creds.credentials)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN",
        )
    user_id, session_id = result
    row = await db.execute(select(User).where(User.id == user_id))
    user = row.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="USER_NOT_FOUND",
        )
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ACCOUNT_NOT_ACTIVE",
        )
    return AuthContext(user=user, session_id=session_id)


async def get_current_user(
    ctx: AuthContext = Depends(get_auth_context),
) -> User:
    """Shorthand — returns just the User (backward-compatible)."""
    return ctx.user


async def require_admin(
    ctx: AuthContext = Depends(get_auth_context),
) -> User:
    """Admin-only guard — 403 if not ADMIN role."""
    if ctx.user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ADMIN_ONLY",
        )
    return ctx.user
