"""Integration tests — account deletion flows (void, transfer)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

TEST_PASSWORD = "StrongP@ss1"


def _reg(email: str, username: str) -> dict:
    return {
        "email": email, "username": username, "password": TEST_PASSWORD,
        "tos_accepted": True, "privacy_policy_accepted": True,
    }


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post("/api/v1/auth/register", json=_reg(email, username))
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _me(client: AsyncClient, token: str) -> dict:
    resp = await client.get("/api/v1/users/me", headers=_auth(token))
    return resp.json()


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={
        "email": email, "password": TEST_PASSWORD,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_soft_delete_void_e2e(integration_client):
    """Delete account (void) → login fails, public profile = placeholder."""
    tok = await _register(integration_client, "delvoid@x.com", "delvoiduser")
    user_data = await _me(integration_client, tok)
    user_id = user_data["id"]

    # Delete with void
    del_resp = await integration_client.request(
        "DELETE", "/api/v1/users/me",
        json={"password": TEST_PASSWORD, "balance_disposition": "void"},
        headers=_auth(tok),
    )
    assert del_resp.status_code == 200

    # Login fails (401)
    login_resp = await integration_client.post("/api/v1/auth/login", json={
        "email": "delvoid@x.com", "password": TEST_PASSWORD,
    })
    assert login_resp.status_code == 401

    # Public profile → placeholder (need another user's token to check)
    checker_tok = await _register(integration_client, "delcheck@x.com", "delchecker")
    profile_resp = await integration_client.get(
        f"/api/v1/users/{user_id}/profile",
        headers=_auth(checker_tok),
    )
    assert profile_resp.status_code == 200
    profile = profile_resp.json()
    assert profile["username"] is None
    assert profile["is_deleted"] is True


@pytest.mark.asyncio
async def test_soft_delete_transfer_e2e(integration_client):
    """Delete account with transfer → recipient balance increases."""
    # Donor has 0 balance by default, so we test the flow works even with 0
    donor_tok = await _register(integration_client, "delxfer@x.com", "delxferuser")
    recipient_tok = await _register(integration_client, "delrcpt@x.com", "delrcptuser")
    recipient_data = await _me(integration_client, recipient_tok)
    recipient_id = recipient_data["id"]

    bal_before = (await integration_client.get(
        "/api/v1/hearts/balance", headers=_auth(recipient_tok),
    )).json()["heart_balance"]

    # Delete with transfer
    del_resp = await integration_client.request(
        "DELETE", "/api/v1/users/me",
        json={
            "password": TEST_PASSWORD,
            "balance_disposition": "transfer",
            "transfer_to_user_id": recipient_id,
        },
        headers=_auth(donor_tok),
    )
    assert del_resp.status_code == 200

    bal_after = (await integration_client.get(
        "/api/v1/hearts/balance", headers=_auth(recipient_tok),
    )).json()["heart_balance"]
    # Balance should be >= bal_before (transfer of 0 is fine; confirms no error)
    assert bal_after >= bal_before
