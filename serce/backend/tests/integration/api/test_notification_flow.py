"""Integration tests — notification flow (exchange → notifications → read)."""
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


async def _me(client: AsyncClient, token: str) -> dict:
    resp = await client.get("/api/v1/users/me", headers=_auth(token))
    return resp.json()


async def _cat_loc(client: AsyncClient) -> tuple[int, int]:
    cats = (await client.get("/api/v1/categories")).json()
    locs = (await client.get("/api/v1/locations")).json()
    return cats[0]["id"] if cats else 1, locs[0]["id"] if locs else 1


@pytest.mark.asyncio
async def test_exchange_flow_generates_notifications(integration_client):
    """Register 2 users → create request → create exchange → accept → complete.
    Verify 3 notifications generated for the non-acting party at each step."""
    tok_a = await _register(integration_client, "notif_a@x.com", "notifa")
    tok_b = await _register(integration_client, "notif_b@x.com", "notifb")
    me_b = await _me(integration_client, tok_b)
    cat_id, loc_id = await _cat_loc(integration_client)

    # A creates request
    req_resp = await integration_client.post("/api/v1/requests", json={
        "title": "Help me please test", "description": "Integration test notification request",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
    }, headers=_auth(tok_a))
    assert req_resp.status_code == 201
    request_id = req_resp.json()["id"]

    # B creates exchange on A's request
    ex_resp = await integration_client.post("/api/v1/exchanges", json={
        "request_id": request_id, "hearts_agreed": 0,
    }, headers=_auth(tok_b))
    assert ex_resp.status_code == 201
    exchange_id = ex_resp.json()["id"]

    # A should have NEW_EXCHANGE notification
    notif_resp = await integration_client.get(
        "/api/v1/users/me/notifications", headers=_auth(tok_a),
    )
    assert notif_resp.status_code == 200
    notifs_a = notif_resp.json()
    assert notifs_a["total"] >= 1
    types_a = [n["type"] for n in notifs_a["entries"]]
    assert "NEW_EXCHANGE" in types_a

    # A accepts exchange
    await integration_client.patch(
        f"/api/v1/exchanges/{exchange_id}/accept", headers=_auth(tok_a),
    )

    # B should have EXCHANGE_ACCEPTED notification
    notif_resp = await integration_client.get(
        "/api/v1/users/me/notifications", headers=_auth(tok_b),
    )
    assert notif_resp.status_code == 200
    types_b = [n["type"] for n in notif_resp.json()["entries"]]
    assert "EXCHANGE_ACCEPTED" in types_b

    # A completes exchange
    await integration_client.patch(
        f"/api/v1/exchanges/{exchange_id}/complete", headers=_auth(tok_a),
    )

    # B should have EXCHANGE_COMPLETED notification
    notif_resp = await integration_client.get(
        "/api/v1/users/me/notifications", headers=_auth(tok_b),
    )
    types_b2 = [n["type"] for n in notif_resp.json()["entries"]]
    assert "EXCHANGE_COMPLETED" in types_b2


@pytest.mark.asyncio
async def test_notification_read_and_unread_count(integration_client):
    """Create notifications via exchange, then test mark-read + unread-count."""
    tok_a = await _register(integration_client, "notifrd_a@x.com", "notifrda")
    tok_b = await _register(integration_client, "notifrd_b@x.com", "notifrdb")
    cat_id, loc_id = await _cat_loc(integration_client)

    # A creates request, B creates exchange → A gets notification
    req_resp = await integration_client.post("/api/v1/requests", json={
        "title": "Read test request", "description": "Testing notification read flow",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
    }, headers=_auth(tok_a))
    request_id = req_resp.json()["id"]

    await integration_client.post("/api/v1/exchanges", json={
        "request_id": request_id, "hearts_agreed": 0,
    }, headers=_auth(tok_b))

    # Unread count for A
    count_resp = await integration_client.get(
        "/api/v1/users/me/notifications/unread-count", headers=_auth(tok_a),
    )
    assert count_resp.status_code == 200
    assert count_resp.json()["count"] >= 1

    # Mark all as read
    mark_resp = await integration_client.post(
        "/api/v1/users/me/notifications/read-all", headers=_auth(tok_a),
    )
    assert mark_resp.status_code == 200
    assert mark_resp.json()["updated"] >= 1

    # Unread count should be 0
    count_resp2 = await integration_client.get(
        "/api/v1/users/me/notifications/unread-count", headers=_auth(tok_a),
    )
    assert count_resp2.json()["count"] == 0
