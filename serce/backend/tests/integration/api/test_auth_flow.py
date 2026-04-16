"""Integration tests — full auth flow against test Postgres."""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


_REG_PAYLOAD = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "StrongP@ss123",
    "tos_accepted": True,
    "privacy_policy_accepted": True,
}


async def test_register_returns_tokens(integration_client):
    resp = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate_email(integration_client):
    await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    resp = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "EMAIL_TAKEN"


async def test_register_duplicate_username(integration_client):
    await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    resp = await integration_client.post("/api/v1/auth/register", json={
        **_REG_PAYLOAD,
        "email": "other@example.com",
    })
    assert resp.status_code == 409
    assert resp.json()["detail"] == "USERNAME_TAKEN"


async def test_login_valid_credentials(integration_client):
    await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    resp = await integration_client.post("/api/v1/auth/login", json={
        "email": _REG_PAYLOAD["email"],
        "password": _REG_PAYLOAD["password"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password(integration_client):
    await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    resp = await integration_client.post("/api/v1/auth/login", json={
        "email": _REG_PAYLOAD["email"],
        "password": "WrongPassword",
    })
    assert resp.status_code == 401
    assert resp.json()["detail"] == "INVALID_CREDENTIALS"


async def test_login_nonexistent_email(integration_client):
    resp = await integration_client.post("/api/v1/auth/login", json={
        "email": "ghost@example.com",
        "password": "whatever",
    })
    assert resp.status_code == 401


async def test_me_with_valid_token(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    token = reg.json()["access_token"]
    resp = await integration_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == _REG_PAYLOAD["email"]
    assert body["username"] == _REG_PAYLOAD["username"]


async def test_refresh_rotates_tokens(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    refresh = reg.json()["refresh_token"]

    resp = await integration_client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] != reg.json()["access_token"]
    assert body["refresh_token"] != refresh  # rotated


async def test_refresh_old_token_rejected(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    old_refresh = reg.json()["refresh_token"]

    # Rotate once
    await integration_client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    # Old token should be revoked
    resp = await integration_client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    assert resp.status_code == 401


async def test_logout_revokes_refresh(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    refresh = reg.json()["refresh_token"]

    resp = await integration_client.post("/api/v1/auth/logout", json={
        "refresh_token": refresh,
    })
    assert resp.status_code == 200

    # Refresh should fail now
    resp = await integration_client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh,
    })
    assert resp.status_code == 401


async def test_logout_all_revokes_all_sessions(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    access = reg.json()["access_token"]
    refresh = reg.json()["refresh_token"]

    # Login again to create second session
    login = await integration_client.post("/api/v1/auth/login", json={
        "email": _REG_PAYLOAD["email"],
        "password": _REG_PAYLOAD["password"],
    })
    refresh2 = login.json()["refresh_token"]

    resp = await integration_client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200

    # Both refreshes should be revoked
    r1 = await integration_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    r2 = await integration_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh2})
    assert r1.status_code == 401
    assert r2.status_code == 401


async def test_list_sessions(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    access = reg.json()["access_token"]

    resp = await integration_client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 1
    assert "id" in sessions[0]
    assert "expires_at" in sessions[0]


async def test_accept_terms_tos(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    access = reg.json()["access_token"]

    # Accept current TOS (already accepted at register → should get 409)
    resp = await integration_client.post(
        "/api/v1/auth/accept-terms",
        json={"document_type": "tos"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "ALREADY_ACCEPTED"


async def test_accept_terms_no_token(integration_client):
    resp = await integration_client.post(
        "/api/v1/auth/accept-terms",
        json={"document_type": "tos"},
    )
    assert resp.status_code == 401


async def test_revoke_current_session_blocked(integration_client):
    """Cannot revoke the session that issued the current access token."""
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    access = reg.json()["access_token"]

    sessions = (await integration_client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access}"},
    )).json()
    # The most recent session (first in list, ordered by created_at desc)
    current_session_id = sessions[0]["id"]

    resp = await integration_client.delete(
        f"/api/v1/auth/sessions/{current_session_id}",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "CANNOT_REVOKE_CURRENT_SESSION"


async def test_revoke_other_session_by_id(integration_client):
    reg = await integration_client.post("/api/v1/auth/register", json=_REG_PAYLOAD)
    access = reg.json()["access_token"]

    # Create a second session via login
    login = await integration_client.post("/api/v1/auth/login", json={
        "email": _REG_PAYLOAD["email"],
        "password": _REG_PAYLOAD["password"],
    })
    access2 = login.json()["access_token"]

    # List sessions from second login (current = second session)
    sessions = (await integration_client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access2}"},
    )).json()
    assert len(sessions) >= 2

    # Find a session that is NOT the current one (second login)
    # The first session in the list is the newest (current for access2)
    other_session_id = sessions[1]["id"]

    resp = await integration_client.delete(
        f"/api/v1/auth/sessions/{other_session_id}",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert resp.status_code == 200

    # Session list should be shorter
    sessions_after = (await integration_client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access2}"},
    )).json()
    assert len(sessions_after) == len(sessions) - 1
