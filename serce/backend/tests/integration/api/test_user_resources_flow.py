"""Integration tests — user resources flows (summary, profile, my requests)."""
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
async def test_summary_reflects_activity(integration_client):
    """Register → Create request + offer → Summary → verify counts."""
    tok = await _register(integration_client, "summ_user@x.com", "summuser")
    cat_id, loc_id = await _cat_loc(integration_client)

    # Create request
    await integration_client.post("/api/v1/requests", json={
        "title": "Summary test request", "description": "Testing summary endpoint counts",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
    }, headers=_auth(tok))

    # Create offer
    await integration_client.post("/api/v1/offers", json={
        "title": "Summary test offer", "description": "Testing summary endpoint offer counts",
        "hearts_asked": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
    }, headers=_auth(tok))

    # Get summary
    resp = await integration_client.get("/api/v1/users/me/summary", headers=_auth(tok))
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_requests"] >= 1
    assert data["active_offers"] >= 1


@pytest.mark.asyncio
async def test_public_profile(integration_client):
    """Register → GET /users/{id}/profile → verify."""
    tok = await _register(integration_client, "prof_user@x.com", "profuser")
    me = await _me(integration_client, tok)
    user_id = me["id"]

    resp = await integration_client.get(
        f"/api/v1/users/{user_id}/profile", headers=_auth(tok),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "profuser"
    assert "email" not in data
    assert "role" not in data


@pytest.mark.asyncio
async def test_my_requests_list(integration_client):
    """Create requests → GET /me/requests → verify."""
    tok = await _register(integration_client, "myreq_user@x.com", "myrequser")
    cat_id, loc_id = await _cat_loc(integration_client)

    for i in range(3):
        await integration_client.post("/api/v1/requests", json={
            "title": f"My request {i}", "description": "Testing my requests list endpoint",
            "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id, "location_scope": "CITY",
        }, headers=_auth(tok))

    resp = await integration_client.get("/api/v1/users/me/requests", headers=_auth(tok))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 3
