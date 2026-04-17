"""Email service — Protocol + Mock + Resend.com implementation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.config import settings


class EmailService(Protocol):
    async def send_verification(self, to: str, token: str) -> None: ...
    async def send_password_reset(self, to: str, token: str) -> None: ...
    async def send_email_changed_notification(self, to: str, new_email: str) -> None: ...
    async def send_notification(self, to: str, notification_type: str, reason: str | None) -> None: ...


@dataclass
class MockEmailService:
    """Dev/test — stores sent emails in memory."""

    sent: list[dict] = field(default_factory=list)

    async def send_verification(self, to: str, token: str) -> None:
        self.sent.append({"type": "verification", "to": to, "token": token})

    async def send_password_reset(self, to: str, token: str) -> None:
        self.sent.append({"type": "reset", "to": to, "token": token})

    async def send_email_changed_notification(self, to: str, new_email: str) -> None:
        self.sent.append({"type": "email_changed", "to": to, "new_email": new_email})

    async def send_notification(self, to: str, notification_type: str, reason: str | None) -> None:
        self.sent.append({"type": "notification", "to": to, "notification_type": notification_type, "reason": reason})


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

    async def send_email_changed_notification(self, to: str, new_email: str) -> None:
        await self._send(
            to=to,
            subject="Zmiana adresu email — Serce",
            body=(
                f"Twój adres email w Serce został zmieniony na {new_email}. "
                "Jeśli to nie Ty — skontaktuj się z nami."
            ),
        )

    _NOTIFICATION_SUBJECTS: dict[str, str] = {
        "NEW_EXCHANGE": "Nowa propozycja wymiany — Serce",
        "EXCHANGE_ACCEPTED": "Wymiana zaakceptowana — Serce",
        "EXCHANGE_COMPLETED": "Wymiana zakonczona — Serce",
        "EXCHANGE_CANCELLED": "Wymiana anulowana — Serce",
        "NEW_MESSAGE": "Nowa wiadomosc w wymianie — Serce",
        "NEW_REVIEW": "Otrzymales/as opinie — Serce",
        "HEARTS_RECEIVED": "Otrzymales/as serca — Serce",
        "REQUEST_EXPIRED": "Twoja prosba wygasla — Serce",
    }

    _NOTIFICATION_BODIES: dict[str, str] = {
        "NEW_EXCHANGE": "Ktos zaproponowal wymiane na Twoja prosbe. Sprawdz szczegoly w aplikacji.",
        "EXCHANGE_ACCEPTED": "Twoja propozycja wymiany zostala zaakceptowana. Sprawdz szczegoly w aplikacji.",
        "EXCHANGE_COMPLETED": "Wymiana zostala zakonczona. Sprawdz szczegoly w aplikacji.",
        "EXCHANGE_CANCELLED": "Wymiana zostala anulowana. Sprawdz szczegoly w aplikacji.",
        "NEW_MESSAGE": "Masz nowa wiadomosc w wymianie. Sprawdz szczegoly w aplikacji.",
        "NEW_REVIEW": "Otrzymales/as nowa opinie. Sprawdz szczegoly w aplikacji.",
        "HEARTS_RECEIVED": "Otrzymales/as serca od innego uzytkownika. Sprawdz szczegoly w aplikacji.",
        "REQUEST_EXPIRED": "Twoja prosba wygasla. Sprawdz szczegoly w aplikacji.",
    }

    async def send_notification(self, to: str, notification_type: str, reason: str | None) -> None:
        subject = self._NOTIFICATION_SUBJECTS.get(notification_type, "Powiadomienie — Serce")
        body = self._NOTIFICATION_BODIES.get(notification_type, "Masz nowe powiadomienie w aplikacji Serce.")
        if reason:
            body += f"\n\n{reason}"
        await self._send(to=to, subject=subject, body=body)

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


_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """DI singleton — MockEmailService when resend_api_key empty."""
    global _email_service
    if _email_service is None:
        if settings.resend_api_key:
            _email_service = ResendEmailService(settings.resend_api_key, settings.email_from)
        else:
            _email_service = MockEmailService()
    return _email_service
