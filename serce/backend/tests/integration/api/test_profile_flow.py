"""Integration tests — profile change flows (email, phone, username, password)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.email_service import MockEmailService, get_email_service
from app.services.sms_service import MockSmsService, get_sms_service


TEST_PASSWORD = "StrongP@ss1"


def _register_payload(email: str = "profile@example.com", username: str = "profuser") -> dict:
    return {
        "email": email,
        "username": username,
        "password": TEST_PASSWORD,
        "tos_accepted": True,
        "privacy_policy_accepted": True,
    }


async def _register_and_get_token(client: AsyncClient, **kwargs) -> tuple[str, str]:
    resp = await client.post("/api/v1/auth/register", json=_register_payload(**kwargs))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return data["access_token"], data["refresh_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---- Profile update ----------------------------------------------------------

@pytest.mark.asyncio
async def test_update_profile_and_read_back(integration_client):
    access, _ = await _register_and_get_token(integration_client)
    resp = await integration_client.patch(
        "/api/v1/users/me",
        json={"bio": "Test bio 123"},
        headers=_auth(access),
    )
    assert resp.status_code == 200
    assert resp.json()["bio"] == "Test bio 123"

    # Read back via GET
    me = await integration_client.get("/api/v1/users/me", headers=_auth(access))
    assert me.json()["bio"] == "Test bio 123"


# ---- Username change ---------------------------------------------------------

@pytest.mark.asyncio
async def test_change_username_e2e(integration_client):
    access, _ = await _register_and_get_token(
        integration_client, email="uname@example.com", username="oldname",
    )
    resp = await integration_client.patch(
        "/api/v1/users/me/username",
        json={"new_username": "newname"},
        headers=_auth(access),
    )
    assert resp.status_code == 200

    me = await integration_client.get("/api/v1/users/me", headers=_auth(access))
    assert me.json()["username"] == "newname"


# ---- Email change flow -------------------------------------------------------

@pytest.mark.asyncio
async def test_email_change_flow_e2e(integration_client):
    email_svc = get_email_service()
    assert isinstance(email_svc, MockEmailService)

    access, _ = await _register_and_get_token(
        integration_client, email="echange@example.com", username="echangeuser",
    )

    # Initiate
    resp = await integration_client.post(
        "/api/v1/users/me/email/change",
        json={"password": TEST_PASSWORD, "new_email": "newemail@example.com"},
        headers=_auth(access),
    )
    assert resp.status_code == 200

    # Find verification token sent to new email
    sent = [m for m in email_svc.sent if m["type"] == "verification" and m["to"] == "newemail@example.com"]
    assert len(sent) >= 1
    raw_token = sent[-1]["token"]

    # Confirm
    resp = await integration_client.post(
        "/api/v1/users/me/email/confirm",
        json={"token": raw_token},
    )
    assert resp.status_code == 200

    # Verify email changed + email_verified reset
    me = await integration_client.get("/api/v1/users/me", headers=_auth(access))
    assert me.json()["email"] == "newemail@example.com"
    assert me.json()["email_verified"] is False


@pytest.mark.asyncio
async def test_email_change_sends_notification_to_old_email(integration_client):
    email_svc = get_email_service()
    assert isinstance(email_svc, MockEmailService)

    access, _ = await _register_and_get_token(
        integration_client, email="notif@example.com", username="notifuser",
    )

    # Initiate + confirm
    resp = await integration_client.post(
        "/api/v1/users/me/email/change",
        json={"password": TEST_PASSWORD, "new_email": "new_notif@example.com"},
        headers=_auth(access),
    )
    assert resp.status_code == 200

    sent_verif = [m for m in email_svc.sent if m["type"] == "verification" and m["to"] == "new_notif@example.com"]
    raw_token = sent_verif[-1]["token"]

    await integration_client.post(
        "/api/v1/users/me/email/confirm",
        json={"token": raw_token},
    )

    # Check notification to OLD email
    notifs = [m for m in email_svc.sent if m["type"] == "email_changed" and m["to"] == "notif@example.com"]
    assert len(notifs) >= 1
    assert notifs[-1]["new_email"] == "new_notif@example.com"


# ---- Phone change flow -------------------------------------------------------

@pytest.mark.asyncio
async def test_phone_change_flow_e2e(integration_client):
    sms_svc = get_sms_service()
    assert isinstance(sms_svc, MockSmsService)

    access, _ = await _register_and_get_token(
        integration_client, email="pchange@example.com", username="pchangeuser",
    )

    # Initiate
    resp = await integration_client.post(
        "/api/v1/users/me/phone/change",
        json={"password": TEST_PASSWORD, "new_phone_number": "+48111222333"},
        headers=_auth(access),
    )
    assert resp.status_code == 200

    # Get OTP from mock
    sent = [m for m in sms_svc.sent if m["to"] == "+48111222333"]
    assert len(sent) >= 1
    code = sent[-1]["code"]

    # Verify
    resp = await integration_client.post(
        "/api/v1/users/me/phone/verify",
        json={"new_phone_number": "+48111222333", "code": code},
        headers=_auth(access),
    )
    assert resp.status_code == 200

    me = await integration_client.get("/api/v1/users/me", headers=_auth(access))
    assert me.json()["phone_number"] == "+48111222333"
    assert me.json()["phone_verified"] is True


@pytest.mark.asyncio
async def test_phone_change_no_initial_grant(integration_client):
    """Phone change must NOT grant initial hearts."""
    sms_svc = get_sms_service()
    assert isinstance(sms_svc, MockSmsService)

    access, _ = await _register_and_get_token(
        integration_client, email="nogrant@example.com", username="nograntuser",
    )

    me_before = await integration_client.get("/api/v1/users/me", headers=_auth(access))
    balance_before = me_before.json()["heart_balance"]

    # Initiate phone change
    resp = await integration_client.post(
        "/api/v1/users/me/phone/change",
        json={"password": TEST_PASSWORD, "new_phone_number": "+48999888777"},
        headers=_auth(access),
    )
    assert resp.status_code == 200

    sent = [m for m in sms_svc.sent if m["to"] == "+48999888777"]
    code = sent[-1]["code"]

    await integration_client.post(
        "/api/v1/users/me/phone/verify",
        json={"new_phone_number": "+48999888777", "code": code},
        headers=_auth(access),
    )

    me_after = await integration_client.get("/api/v1/users/me", headers=_auth(access))
    assert me_after.json()["heart_balance"] == balance_before


# ---- Password change ---------------------------------------------------------

@pytest.mark.asyncio
async def test_change_password_e2e(integration_client):
    access, _ = await _register_and_get_token(
        integration_client, email="pwdch@example.com", username="pwdchuser",
    )

    resp = await integration_client.post(
        "/api/v1/users/me/password",
        json={"old_password": TEST_PASSWORD, "new_password": "NewSecure@99"},
        headers=_auth(access),
    )
    assert resp.status_code == 200

    # Old password should no longer work for login
    login_resp = await integration_client.post(
        "/api/v1/auth/login",
        json={"email": "pwdch@example.com", "password": TEST_PASSWORD},
    )
    assert login_resp.status_code == 401

    # New password should work
    login_resp = await integration_client.post(
        "/api/v1/auth/login",
        json={"email": "pwdch@example.com", "password": "NewSecure@99"},
    )
    assert login_resp.status_code == 200
