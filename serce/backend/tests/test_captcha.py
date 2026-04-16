"""Unit tests for hCaptcha verification."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.captcha import verify_captcha


async def test_captcha_skipped_when_no_secret():
    """When HCAPTCHA_SECRET is empty, captcha check is a no-op."""
    await verify_captcha(None)  # should not raise
    await verify_captcha("any-token")  # should not raise


async def test_captcha_required_when_secret_set():
    """When HCAPTCHA_SECRET is set, missing token raises 422."""
    with patch("app.core.captcha._HCAPTCHA_SECRET", "test-secret"):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await verify_captcha(None)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == "CAPTCHA_REQUIRED"


def _make_mock_client(success: bool):
    """Create a mock httpx.AsyncClient that returns a given hCaptcha response."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": success}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


async def test_captcha_invalid_token():
    """When hCaptcha API rejects the token, raises 422."""
    with (
        patch("app.core.captcha._HCAPTCHA_SECRET", "test-secret"),
        patch("httpx.AsyncClient", return_value=_make_mock_client(False)),
    ):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await verify_captcha("bad-token")
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == "CAPTCHA_INVALID"


async def test_captcha_valid_token():
    """When hCaptcha API accepts the token, no exception."""
    with (
        patch("app.core.captcha._HCAPTCHA_SECRET", "test-secret"),
        patch("httpx.AsyncClient", return_value=_make_mock_client(True)),
    ):
        await verify_captcha("valid-token")  # should not raise
