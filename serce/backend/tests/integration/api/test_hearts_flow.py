"""Integration tests — hearts gift, balance, ledger flows."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


TEST_PASSWORD = "StrongP@ss1"


def _register_payload(email: str, username: str) -> dict:
    return {
        "email": email,
        "username": username,
        "password": TEST_PASSWORD,
        "tos_accepted": True,
        "privacy_policy_accepted": True,
    }


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post("/api/v1/auth/register", json=_register_payload(email, username))
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _get_me(client: AsyncClient, token: str) -> dict:
    resp = await client.get("/api/v1/users/me", headers=_auth(token))
    assert resp.status_code == 200
    return resp.json()


# ---- Gift e2e ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_gift_e2e(integration_client):
    sender_token = await _register(integration_client, "gsend@example.com", "gsender")
    recipient_token = await _register(integration_client, "grecv@example.com", "grecver")

    recipient_me = await _get_me(integration_client, recipient_token)
    recipient_id = recipient_me["id"]

    resp = await integration_client.post(
        "/api/v1/hearts/gift",
        json={"to_user_id": recipient_id, "amount": 2, "note": "thanks"},
        headers=_auth(sender_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 2
    assert data["type"] == "GIFT"
    assert data["note"] == "thanks"


@pytest.mark.asyncio
async def test_gift_and_check_balance(integration_client):
    sender_token = await _register(integration_client, "bsend@example.com", "bsender")
    recipient_token = await _register(integration_client, "brecv@example.com", "brecver")

    recipient_me = await _get_me(integration_client, recipient_token)

    # Check sender balance before
    bal_before = await integration_client.get("/api/v1/hearts/balance", headers=_auth(sender_token))
    balance_before = bal_before.json()["heart_balance"]

    # Gift
    await integration_client.post(
        "/api/v1/hearts/gift",
        json={"to_user_id": recipient_me["id"], "amount": 3},
        headers=_auth(sender_token),
    )

    # Check sender balance after
    bal_after = await integration_client.get("/api/v1/hearts/balance", headers=_auth(sender_token))
    assert bal_after.json()["heart_balance"] == balance_before - 3

    # Check recipient balance after
    bal_recv = await integration_client.get("/api/v1/hearts/balance", headers=_auth(recipient_token))
    assert bal_recv.json()["heart_balance"] == 3


@pytest.mark.asyncio
async def test_gift_and_check_ledger(integration_client):
    sender_token = await _register(integration_client, "lsend@example.com", "lsender")
    recipient_token = await _register(integration_client, "lrecv@example.com", "lrecver")

    recipient_me = await _get_me(integration_client, recipient_token)

    await integration_client.post(
        "/api/v1/hearts/gift",
        json={"to_user_id": recipient_me["id"], "amount": 1, "note": "test ledger"},
        headers=_auth(sender_token),
    )

    # Sender sees it in ledger
    ledger_resp = await integration_client.get("/api/v1/hearts/ledger", headers=_auth(sender_token))
    assert ledger_resp.status_code == 200
    data = ledger_resp.json()
    assert data["total"] >= 1
    assert any(e["note"] == "test ledger" for e in data["entries"])

    # Recipient sees it in ledger
    ledger_recv = await integration_client.get("/api/v1/hearts/ledger", headers=_auth(recipient_token))
    assert ledger_recv.json()["total"] >= 1


@pytest.mark.asyncio
async def test_gift_cap_exceeded_e2e(integration_client):
    sender_token = await _register(integration_client, "capsend@example.com", "capsender")
    recipient_token = await _register(integration_client, "caprecv@example.com", "caprecver")

    sender_me = await _get_me(integration_client, sender_token)
    recipient_me = await _get_me(integration_client, recipient_token)

    # Try to gift more than cap allows (recipient starts at 0, cap=50, but sender has limited balance)
    # Gift amount > 50 → schema rejects (le=50)
    resp = await integration_client.post(
        "/api/v1/hearts/gift",
        json={"to_user_id": recipient_me["id"], "amount": 51},
        headers=_auth(sender_token),
    )
    assert resp.status_code == 422  # schema validation


@pytest.mark.asyncio
async def test_gift_insufficient_balance_e2e(integration_client):
    sender_token = await _register(integration_client, "inssend@example.com", "inssender")
    recipient_token = await _register(integration_client, "insrecv@example.com", "insrecver")

    recipient_me = await _get_me(integration_client, recipient_token)

    # Sender starts with 0 hearts (new user, no initial grant)
    resp = await integration_client.post(
        "/api/v1/hearts/gift",
        json={"to_user_id": recipient_me["id"], "amount": 1},
        headers=_auth(sender_token),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "INSUFFICIENT_BALANCE"
