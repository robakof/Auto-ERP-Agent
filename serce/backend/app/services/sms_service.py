"""SMS service — Protocol + Mock + SMSAPI.pl implementation."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.config import settings


class SmsService(Protocol):
    async def send_otp(self, phone_number: str, code: str) -> None: ...


@dataclass
class MockSmsService:
    """Dev/test — stores sent SMS in memory."""

    sent: list[dict] = field(default_factory=list)

    async def send_otp(self, phone_number: str, code: str) -> None:
        self.sent.append({"phone": phone_number, "code": code})


class SmsApiService:
    """Production — SMSAPI.pl."""

    def __init__(self, api_token: str, sender_name: str) -> None:
        self._api_token = api_token
        self._sender_name = sender_name

    async def send_otp(self, phone_number: str, code: str) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.smsapi.pl/sms.do",
                headers={"Authorization": f"Bearer {self._api_token}"},
                data={
                    "to": phone_number.replace("+", ""),
                    "message": f"Kod weryfikacyjny Serce: {code}",
                    "from": self._sender_name,
                    "format": "json",
                },
                timeout=10.0,
            )
            resp.raise_for_status()


def generate_otp() -> str:
    """Generate 6-digit OTP code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def get_sms_service() -> SmsService:
    """DI factory — MockSmsService when smsapi_token empty."""
    if settings.smsapi_token:
        return SmsApiService(settings.smsapi_token, settings.smsapi_sender)
    return MockSmsService()
