"""hCaptcha server-side verification.

In test/development mode (hcaptcha_secret not set or empty), verification is skipped.
In production, the hCaptcha response token is validated against the hCaptcha API.
"""
from __future__ import annotations

from fastapi import HTTPException

from app.config import settings

_VERIFY_URL = "https://api.hcaptcha.com/siteverify"


async def verify_captcha(token: str | None) -> None:
    """Verify hCaptcha token. No-op if hcaptcha_secret is not configured."""
    if not settings.hcaptcha_secret:
        return  # dev/test mode — skip verification

    if not token:
        raise HTTPException(status_code=422, detail="CAPTCHA_REQUIRED")

    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _VERIFY_URL,
            data={"secret": settings.hcaptcha_secret, "response": token},
        )
    result = resp.json()
    if not result.get("success"):
        raise HTTPException(status_code=422, detail="CAPTCHA_INVALID")
