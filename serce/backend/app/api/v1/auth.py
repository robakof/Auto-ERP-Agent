"""Auth endpoints — register, login, refresh, logout, sessions."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    AcceptTermsRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.session import SessionRead
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/hour")
async def register(
    request: Request,
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user, access, refresh = await auth_service.register_user(
        db, req, ip_address=_client_ip(request),
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user_agent = request.headers.get("user-agent")
    user, access, refresh = await auth_service.login_user(
        db, req.email, req.password,
        ip_address=_client_ip(request),
        device_info=user_agent,
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    access, new_refresh = await auth_service.refresh_tokens(
        db, req.refresh_token, ip_address=_client_ip(request),
    )
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await auth_service.logout_session(db, req.refresh_token)
    return MessageResponse(detail="Wylogowano.")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await auth_service.logout_all(db, current_user.id)
    return MessageResponse(detail=f"Uniewazniono {count} sesji.")


@router.get("/sessions", response_model=list[SessionRead])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.list_sessions(db, current_user.id)


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.revoke_session(db, session_id, current_user.id)
    return MessageResponse(detail="Sesja uniewazniona.")


@router.post("/accept-terms", response_model=MessageResponse)
async def accept_terms(
    req: AcceptTermsRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.accept_terms(
        db, current_user.id, req.document_type, ip_address=_client_ip(request),
    )
    return MessageResponse(detail="Zaakceptowano.")


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
