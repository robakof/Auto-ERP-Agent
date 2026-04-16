"""hCaptcha server-side verification.

In test/development mode (HCAPTCHA_SECRET not set or empty), verification is skipped.
In production, the hCaptcha response token is validated against the hCaptcha API.
"""
from __future__ import annotations

import os

from fastapi import HTTPException

_HCAPTCHA_SECRET = os.getenv("HCAPTCHA_SECRET", "").strip()
_VERIFY_URL = "https://api.hcaptcha.com/siteverify"


async def verify_captcha(token: str | None) -> None:
    """Verify hCaptcha token. No-op if HCAPTCHA_SECRET is not configured."""
    if not _HCAPTCHA_SECRET:
        return  # dev/test mode — skip verification

    if not token:
        raise HTTPException(status_code=422, detail="CAPTCHA_REQUIRED")

    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _VERIFY_URL,
            data={"secret": _HCAPTCHA_SECRET, "response": token},
        )
    result = resp.json()
    if not result.get("success"):
        raise HTTPException(status_code=422, detail="CAPTCHA_INVALID")
