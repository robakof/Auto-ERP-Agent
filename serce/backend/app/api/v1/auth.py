"""Auth endpoints — register, login, refresh, logout, sessions."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.captcha import verify_captcha
from app.core.deps import AuthContext, get_auth_context, get_current_user
from app.core.rate_limit import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    AcceptTermsRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SendPhoneOtpRequest,
    TokenResponse,
    VerifyEmailRequest,
    VerifyPhoneRequest,
)
from app.schemas.session import SessionRead
from app.schemas.user import UserRead
from app.services import auth_service
from app.services.email_service import EmailService, get_email_service
from app.services.sms_service import SmsService, get_sms_service
from app.services import verification_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    """Extract real client IP — reuses rate_limit._get_client_ip logic."""
    from app.core.rate_limit import _get_client_ip
    return _get_client_ip(request)


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/hour")
async def register(
    request: Request,
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    await verify_captcha(req.captcha_token)
    user, access, refresh = await auth_service.register_user(
        db, req, ip_address=_client_ip(request),
    )
    # Auto-send verification email (fire-and-forget — registration succeeds regardless)
    raw_token = await verification_service.create_email_verification(db, user.id, user.email)
    await db.commit()
    try:
        email_svc = get_email_service()
        await email_svc.send_verification(user.email, raw_token)
    except Exception:
        pass  # token saved in DB, user can resend later
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
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.revoke_session(
        db, session_id, ctx.user.id, current_session_id=ctx.session_id,
    )
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


# ---- Verification endpoints (M4) --------------------------------------------

@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(req: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    await verification_service.verify_email(db, req.token)
    await db.commit()
    return MessageResponse(detail="Email zweryfikowany.")


@router.post("/resend-verification-email", response_model=MessageResponse)
@limiter.limit("3/hour")
async def resend_verification_email(
    request: Request,
    req: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await verification_service.resend_email_verification(db, req.email)
    if result:
        raw_token, _ = result
        await db.commit()
        email_svc = get_email_service()
        try:
            await email_svc.send_verification(req.email, raw_token)
        except Exception:
            pass  # fire-and-forget — token saved, email delivery best-effort
    # Always 200 — don't reveal if email exists
    return MessageResponse(detail="Jesli email istnieje, wyslano link weryfikacyjny.")


@router.post("/send-phone-otp", response_model=MessageResponse)
@limiter.limit("5/hour")
async def send_phone_otp(
    request: Request,
    req: SendPhoneOtpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = await verification_service.create_phone_otp(db, current_user.id, req.phone_number)
    await db.commit()
    sms_svc = get_sms_service()
    await sms_svc.send_otp(req.phone_number, code)
    return MessageResponse(detail="Kod SMS wyslany.")


@router.post("/verify-phone", response_model=MessageResponse)
@limiter.limit("10/hour")
async def verify_phone_endpoint(
    request: Request,
    req: VerifyPhoneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    granted = await verification_service.verify_phone(
        db, current_user.id, req.phone_number, req.code,
    )
    await db.commit()
    msg = "Telefon zweryfikowany."
    if granted:
        msg += f" Otrzymales {settings.initial_heart_grant} serc na start!"
    return MessageResponse(detail=msg)


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    req: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await verification_service.create_password_reset(db, req.email)
    if result:
        raw_token, _ = result
        await db.commit()
        try:
            email_svc = get_email_service()
            await email_svc.send_password_reset(req.email, raw_token)
        except Exception:
            pass  # fire-and-forget — token saved, email delivery best-effort
    # Always 200 — don't reveal if email exists
    return MessageResponse(detail="Jesli email istnieje, wyslano link do resetu hasla.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(
    req: ResetPasswordRequest, db: AsyncSession = Depends(get_db),
):
    await verification_service.reset_password(db, req.token, req.new_password)
    await db.commit()
    return MessageResponse(detail="Haslo zmienione. Zaloguj sie ponownie.")
