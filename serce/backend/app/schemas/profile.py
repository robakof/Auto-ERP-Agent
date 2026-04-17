"""Profile mutation request schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UpdateProfileRequest(BaseModel):
    bio: str | None = Field(None, max_length=500)
    location_id: int | None = None


class ChangeUsernameRequest(BaseModel):
    new_username: str = Field(min_length=3, max_length=30)


class ChangeEmailRequest(BaseModel):
    password: str
    new_email: EmailStr


class ConfirmEmailChangeRequest(BaseModel):
    token: str = Field(max_length=256)


class ChangePhoneRequest(BaseModel):
    password: str
    new_phone_number: str = Field(pattern=r"^\+48\d{9}$")


class VerifyPhoneChangeRequest(BaseModel):
    new_phone_number: str = Field(pattern=r"^\+48\d{9}$")
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
