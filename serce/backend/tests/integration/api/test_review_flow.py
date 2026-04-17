"""Integration tests — review flows (create, list, user profile)."""
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


async def _create_completed_exchange(
    client: AsyncClient, requester_tok: str, helper_tok: str, cat_id: int, loc_id: int,
) -> str:
    """Create request → exchange → accept → complete. Return exchange_id."""
    req_resp = await client.post("/api/v1/requests", json={
        "title": "Review test request", "description": "Need help for review testing flow",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
    }, headers=_auth(requester_tok))
    assert req_resp.status_code == 201
    request_id = req_resp.json()["id"]

    ex_resp = await client.post("/api/v1/exchanges", json={
        "request_id": request_id, "hearts_agreed": 0,
    }, headers=_auth(helper_tok))
    assert ex_resp.status_code == 201
    exchange_id = ex_resp.json()["id"]

    accept_resp = await client.patch(
        f"/api/v1/exchanges/{exchange_id}/accept", headers=_auth(requester_tok),
    )
    assert accept_resp.status_code == 200

    complete_resp = await client.patch(
        f"/api/v1/exchanges/{exchange_id}/complete", headers=_auth(requester_tok),
    )
    assert complete_resp.status_code == 200
    return exchange_id


@pytest.mark.asyncio
async def test_full_review_flow(integration_client):
    """Exchange COMPLETED → Both review → verify."""
    requester_tok = await _register(integration_client, "revreq@x.com", "revrequer")
    helper_tok = await _register(integration_client, "revhelp@x.com", "revhelper")
    cat_id, loc_id = await _cat_loc(integration_client)
    exchange_id = await _create_completed_exchange(
        integration_client, requester_tok, helper_tok, cat_id, loc_id,
    )

    # Requester reviews helper
    r1 = await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/reviews",
        json={"comment": "Excellent helper, very helpful!"},
        headers=_auth(requester_tok),
    )
    assert r1.status_code == 201

    # Helper reviews requester
    r2 = await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/reviews",
        json={"comment": "Great requester, clear communication"},
        headers=_auth(helper_tok),
    )
    assert r2.status_code == 201

    # List reviews for exchange
    list_resp = await integration_client.get(
        f"/api/v1/exchanges/{exchange_id}/reviews",
        headers=_auth(requester_tok),
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2


@pytest.mark.asyncio
async def test_review_on_pending_rejected(integration_client):
    """Exchange PENDING → review → 422."""
    requester_tok = await _register(integration_client, "pendrev_req@x.com", "pendrevreq")
    helper_tok = await _register(integration_client, "pendrev_help@x.com", "pendrevhelp")
    cat_id, loc_id = await _cat_loc(integration_client)

    req_resp = await integration_client.post("/api/v1/requests", json={
        "title": "Pending review test", "description": "Cannot review pending exchange test",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
    }, headers=_auth(requester_tok))
    request_id = req_resp.json()["id"]

    ex_resp = await integration_client.post("/api/v1/exchanges", json={
        "request_id": request_id, "hearts_agreed": 0,
    }, headers=_auth(helper_tok))
    exchange_id = ex_resp.json()["id"]

    resp = await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/reviews",
        json={"comment": "Too early to review this exchange"},
        headers=_auth(requester_tok),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "EXCHANGE_NOT_COMPLETED"


@pytest.mark.asyncio
async def test_user_reviews_profile(integration_client):
    """Create reviews → GET /users/{id}/reviews."""
    requester_tok = await _register(integration_client, "profrev_req@x.com", "profrevreq")
    helper_tok = await _register(integration_client, "profrev_help@x.com", "profrevhelp")
    cat_id, loc_id = await _cat_loc(integration_client)
    helper_me = await _me(integration_client, helper_tok)
    helper_id = helper_me["id"]

    exchange_id = await _create_completed_exchange(
        integration_client, requester_tok, helper_tok, cat_id, loc_id,
    )

    await integration_client.post(
        f"/api/v1/exchanges/{exchange_id}/reviews",
        json={"comment": "Wonderful helper, highly recommended!"},
        headers=_auth(requester_tok),
    )

    # Any authenticated user can see user reviews
    resp = await integration_client.get(
        f"/api/v1/users/{helper_id}/reviews",
        headers=_auth(requester_tok),
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["entries"][0]["reviewed_id"] == helper_id
