"""User profile endpoints — profile, username, email/phone/password change."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import MessageResponse
from app.schemas.profile import (
    ChangeEmailRequest,
    ChangePasswordRequest,
    ChangePhoneRequest,
    ChangeUsernameRequest,
    ConfirmEmailChangeRequest,
    UpdateProfileRequest,
    VerifyPhoneChangeRequest,
)
from app.schemas.user import UserRead
from app.services import profile_service
from app.services.email_service import get_email_service
from app.services.sms_service import get_sms_service

router = APIRouter(prefix="/users", tags=["users"])


# ---- Profile -----------------------------------------------------------------

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await profile_service.update_profile(
        db, current_user.id, bio=req.bio, location_id=req.location_id,
    )
    await db.commit()
    return user


# ---- Username ----------------------------------------------------------------

@router.patch("/me/username", response_model=MessageResponse)
async def change_username(
    req: ChangeUsernameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.change_username(db, current_user.id, req.new_username)
    await db.commit()
    return MessageResponse(detail="Username zmieniony.")


# ---- Email change ------------------------------------------------------------

@router.post("/me/email/change", response_model=MessageResponse)
@limiter.limit("3/hour")
async def initiate_email_change(
    request: Request,
    req: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_token = await profile_service.initiate_email_change(
        db, current_user.id, req.password, req.new_email,
    )
    await db.commit()
    try:
        email_svc = get_email_service()
        await email_svc.send_verification(req.new_email, raw_token)
    except Exception:
        pass  # fire-and-forget — token saved in DB
    return MessageResponse(detail="Link weryfikacyjny wyslany na nowy email.")


@router.post("/me/email/confirm", response_model=MessageResponse)
async def confirm_email_change(
    req: ConfirmEmailChangeRequest,
    db: AsyncSession = Depends(get_db),
):
    old_email, new_email = await profile_service.confirm_email_change(db, req.token)
    await db.commit()
    try:
        email_svc = get_email_service()
        await email_svc.send_email_changed_notification(old_email, new_email)
    except Exception:
        pass  # fire-and-forget — email change already applied
    return MessageResponse(detail="Email zmieniony. Zweryfikuj nowy adres.")


# ---- Phone change ------------------------------------------------------------

@router.post("/me/phone/change", response_model=MessageResponse)
@limiter.limit("5/hour")
async def initiate_phone_change(
    request: Request,
    req: ChangePhoneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = await profile_service.initiate_phone_change(
        db, current_user.id, req.password, req.new_phone_number,
    )
    await db.commit()
    try:
        sms_svc = get_sms_service()
        await sms_svc.send_otp(req.new_phone_number, code)
    except Exception:
        pass  # fire-and-forget — OTP saved in DB
    return MessageResponse(detail="Kod SMS wyslany na nowy numer.")


@router.post("/me/phone/verify", response_model=MessageResponse)
async def verify_phone_change(
    req: VerifyPhoneChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.confirm_phone_change(
        db, current_user.id, req.new_phone_number, req.code,
    )
    await db.commit()
    return MessageResponse(detail="Numer telefonu zmieniony.")


# ---- Password change ---------------------------------------------------------

@router.post("/me/password", response_model=MessageResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await profile_service.change_password(
        db, current_user.id, req.old_password, req.new_password,
    )
    await db.commit()
    return MessageResponse(detail="Haslo zmienione. Pozostale sesje uniewaznione.")
