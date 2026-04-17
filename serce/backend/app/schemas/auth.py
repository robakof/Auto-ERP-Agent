"""Auth request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    tos_accepted: bool
    privacy_policy_accepted: bool
    captcha_token: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AcceptTermsRequest(BaseModel):
    document_type: str = Field(pattern=r"^(tos|privacy_policy)$")


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class SendPhoneOtpRequest(BaseModel):
    phone_number: str = Field(pattern=r"^\+48\d{9}$")


class VerifyPhoneRequest(BaseModel):
    phone_number: str = Field(pattern=r"^\+48\d{9}$")
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    detail: str
