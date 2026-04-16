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


class MessageResponse(BaseModel):
    detail: str
