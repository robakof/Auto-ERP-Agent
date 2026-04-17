"""Integration tests — verification flows (email, phone, password reset)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.email_service import MockEmailService, get_email_service
from app.services.sms_service import MockSmsService, get_sms_service


def _register_payload(email: str = "verify@example.com", username: str = "verifyuser") -> dict:
    return {
        "email": email,
        "username": username,
        "password": "StrongP@ss1",
        "tos_accepted": True,
        "privacy_policy_accepted": True,
    }


async def _register_and_get_token(client: AsyncClient, **kwargs) -> tuple[str, str]:
    """Register a user and return (access_token, refresh_token)."""
    resp = await client.post("/api/v1/auth/register", json=_register_payload(**kwargs))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return data["access_token"], data["refresh_token"]


def _auth_header(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.mark.asyncio
async def test_register_sends_verification_email(integration_client):
    """Registration should trigger a verification email (mock captures it)."""
    email_svc = get_email_service()
    assert isinstance(email_svc, MockEmailService)
    before = len(email_svc.sent)
    await _register_and_get_token(integration_client)
    assert len(email_svc.sent) > before
    last = email_svc.sent[-1]
    assert last["type"] == "verification"
    assert last["to"] == "verify@example.com"
    assert len(last["token"]) > 10


@pytest.mark.asyncio
async def test_verify_email_activates_flag(integration_client):
    """After verifying email token, user.email_verified should be True."""
    email_svc = get_email_service()
    assert isinstance(email_svc, MockEmailService)
    access, _ = await _register_and_get_token(integration_client, email="eflag@example.com", username="eflaguser")
    raw_token = email_svc.sent[-1]["token"]

    resp = await integration_client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 200

    # Check /me
    me = await integration_client.get("/api/v1/auth/me", headers=_auth_header(access))
    assert me.status_code == 200
    assert me.json()["email_verified"] is True


@pytest.mark.asyncio
async def test_resend_verification_email(integration_client):
    """Resend should create a new token and send another email."""
    email_svc = get_email_service()
    assert isinstance(email_svc, MockEmailService)
    await _register_and_get_token(integration_client, email="resend@example.com", username="resenduser")
    count_before = len(email_svc.sent)

    resp = await integration_client.post("/api/v1/auth/resend-verification-email", json={
        "email": "resend@example.com",
    })
    assert resp.status_code == 200
    assert len(email_svc.sent) > count_before


@pytest.mark.asyncio
async def test_phone_otp_flow_and_initial_grant(integration_client):
    """Send OTP → verify phone → user gets INITIAL_GRANT hearts."""
    sms_svc = get_sms_service()
    assert isinstance(sms_svc, MockSmsService)
    access, _ = await _register_and_get_token(integration_client, email="phone@example.com", username="phoneuser")
    headers = _auth_header(access)

    # Send OTP
    resp = await integration_client.post(
        "/api/v1/auth/send-phone-otp",
        json={"phone_number": "+48111222333"},
        headers=headers,
    )
    assert resp.status_code == 200
    code = sms_svc.sent[-1]["code"]

    # Verify phone
    resp = await integration_client.post(
        "/api/v1/auth/verify-phone",
        json={"phone_number": "+48111222333", "code": code},
        headers=headers,
    )
    assert resp.status_code == 200
    assert "serc" in resp.json()["detail"]  # INITIAL_GRANT message

    # Check user state
    me = await integration_client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["phone_verified"] is True
    assert me.json()["heart_balance"] == 5  # initial_heart_grant


@pytest.mark.asyncio
async def test_forgot_password_and_reset(integration_client):
    """Forgot password + reset flow."""
    email_svc = get_email_service()
    assert isinstance(email_svc, MockEmailService)
    await _register_and_get_token(integration_client, email="reset@example.com", username="resetuser")

    # Forgot password
    resp = await integration_client.post("/api/v1/auth/forgot-password", json={
        "email": "reset@example.com",
    })
    assert resp.status_code == 200
    reset_token = email_svc.sent[-1]["token"]

    # Reset password
    resp = await integration_client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewStr0ngP@ss!",
    })
    assert resp.status_code == 200

    # Login with new password
    resp = await integration_client.post("/api/v1/auth/login", json={
        "email": "reset@example.com",
        "password": "NewStr0ngP@ss!",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_force_relogin(integration_client):
    """After password reset, old refresh token should be revoked."""
    email_svc = get_email_service()
    assert isinstance(email_svc, MockEmailService)
    _, refresh = await _register_and_get_token(integration_client, email="relogin@example.com", username="reloginuser")

    # Forgot + reset
    await integration_client.post("/api/v1/auth/forgot-password", json={"email": "relogin@example.com"})
    reset_token = email_svc.sent[-1]["token"]
    await integration_client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "AnotherP@ss1",
    })

    # Old refresh token should fail
    resp = await integration_client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh,
    })
    assert resp.status_code == 401
