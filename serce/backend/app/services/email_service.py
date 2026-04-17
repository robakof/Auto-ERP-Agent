"""Email service — Protocol + Mock + Resend.com implementation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.config import settings


class EmailService(Protocol):
    async def send_verification(self, to: str, token: str) -> None: ...
    async def send_password_reset(self, to: str, token: str) -> None: ...


@dataclass
class MockEmailService:
    """Dev/test — stores sent emails in memory."""

    sent: list[dict] = field(default_factory=list)

    async def send_verification(self, to: str, token: str) -> None:
        self.sent.append({"type": "verification", "to": to, "token": token})

    async def send_password_reset(self, to: str, token: str) -> None:
        self.sent.append({"type": "reset", "to": to, "token": token})


class ResendEmailService:
    """Production — Resend.com API."""

    def __init__(self, api_key: str, from_email: str) -> None:
        self._api_key = api_key
        self._from_email = from_email

    async def send_verification(self, to: str, token: str) -> None:
        url = f"{settings.email_verification_url}?token={token}"
        await self._send(
            to=to,
            subject="Potwierdź swój email — Serce",
            body=f"Kliknij aby potwierdzić email:\n\n{url}\n\nLink ważny 24h.",
        )

    async def send_password_reset(self, to: str, token: str) -> None:
        url = f"{settings.password_reset_url}?token={token}"
        await self._send(
            to=to,
            subject="Reset hasła — Serce",
            body=f"Kliknij aby zresetować hasło:\n\n{url}\n\nLink ważny 1h.",
        )

    async def _send(self, *, to: str, subject: str, body: str) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "from": self._from_email,
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
                timeout=10.0,
            )
            resp.raise_for_status()


def get_email_service() -> EmailService:
    """DI factory — MockEmailService when resend_api_key empty."""
    if settings.resend_api_key:
        return ResendEmailService(settings.resend_api_key, settings.email_from)
    return MockEmailService()
