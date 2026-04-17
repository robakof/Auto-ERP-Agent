"""Integration tests — message flows (send, list, both participants)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


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


async def _cat_loc(client: AsyncClient) -> tuple[int, int]:
    cats = (await client.get("/api/v1/categories")).json()
    locs = (await client.get("/api/v1/locations")).json()
    return cats[0]["id"] if cats else 1, locs[0]["id"] if locs else 1


async def _create_exchange(client: AsyncClient, requester_tok: str, helper_tok: str, cat_id: int, loc_id: int) -> str:
    """Helper: create request + exchange, return exchange_id."""
    req_resp = await client.post("/api/v1/requests", json={
        "title": "Message test request", "description": "Need help for message testing",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
    }, headers=_auth(requester_tok))
    assert req_resp.status_code == 201
    request_id = req_resp.json()["id"]

    ex_resp = await client.post("/api/v1/exchanges", json={
        "request_id": request_id, "hearts_agreed": 0,
    }, headers=_auth(helper_tok))
    assert ex_resp.status_code == 201
    return ex_resp.json()["id"]


@pytest.mark.asyncio
async def test_send_and_list(integration_client):
    """Send message → list → verify."""
    requester_tok = await _register(integration_client, "msgreq@x.com", "msgrequer")
    helper_tok = await _register(integration_client, "msghelp@x.com", "msghelper")
    cat_id, loc_id = await _cat_loc(integration_client)
    exchange_id = await _create_exchange(integration_client, requester_tok, helper_tok, cat_id, loc_id)

    # Send message
    send_resp = await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/messages",
        json={"content": "Hello, can we discuss?"},
        headers=_auth(requester_tok),
    )
    assert send_resp.status_code == 201
    assert send_resp.json()["content"] == "Hello, can we discuss?"

    # List messages
    list_resp = await integration_client.get(
        f"/api/v1/exchanges/{exchange_id}/messages",
        headers=_auth(requester_tok),
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["entries"][0]["content"] == "Hello, can we discuss?"


@pytest.mark.asyncio
async def test_conversation_both_participants(integration_client):
    """Both participants send messages → verify chronological order."""
    requester_tok = await _register(integration_client, "conv_req@x.com", "convrequer")
    helper_tok = await _register(integration_client, "conv_help@x.com", "convhelper")
    cat_id, loc_id = await _cat_loc(integration_client)
    exchange_id = await _create_exchange(integration_client, requester_tok, helper_tok, cat_id, loc_id)

    await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/messages",
        json={"content": "First from requester"},
        headers=_auth(requester_tok),
    )
    await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/messages",
        json={"content": "Reply from helper"},
        headers=_auth(helper_tok),
    )

    list_resp = await integration_client.get(
        f"/api/v1/exchanges/{exchange_id}/messages",
        headers=_auth(requester_tok),
    )
    assert list_resp.status_code == 200
    entries = list_resp.json()["entries"]
    assert len(entries) == 2
    # Chronological (ASC)
    assert entries[0]["content"] == "First from requester"
    assert entries[1]["content"] == "Reply from helper"


@pytest.mark.asyncio
async def test_send_on_pending(integration_client):
    """Messages allowed on PENDING exchange — negotiation."""
    requester_tok = await _register(integration_client, "pend_req@x.com", "pendrequer")
    helper_tok = await _register(integration_client, "pend_help@x.com", "pendhelper")
    cat_id, loc_id = await _cat_loc(integration_client)
    exchange_id = await _create_exchange(integration_client, requester_tok, helper_tok, cat_id, loc_id)

    # Exchange is PENDING by default — send should succeed
    send_resp = await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/messages",
        json={"content": "Negotiating terms..."},
        headers=_auth(requester_tok),
    )
    assert send_resp.status_code == 201
