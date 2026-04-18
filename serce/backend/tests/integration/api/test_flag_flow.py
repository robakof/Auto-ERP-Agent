"""Integration tests — flag creation flows (request flagging, own-resource guard, duplicate guard)."""
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


async def _cat_loc(client: AsyncClient) -> tuple[int, int]:
    cats = (await client.get("/api/v1/categories")).json()
    locs = (await client.get("/api/v1/locations")).json()
    return cats[0]["id"] if cats else 1, locs[0]["id"] if locs else 1


@pytest.mark.asyncio
async def test_flag_request_e2e(integration_client):
    """Create request → another user flags it → flag exists."""
    owner_tok = await _register(integration_client, "flown@x.com", "flagowner")
    reporter_tok = await _register(integration_client, "flrep@x.com", "flagreporter")
    cat_id, loc_id = await _cat_loc(integration_client)

    req_resp = await integration_client.post("/api/v1/requests", json={
        "title": "Flaggable request", "description": "Content to be flagged",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id,
        "location_scope": "CITY",
    }, headers=_auth(owner_tok))
    assert req_resp.status_code == 201
    request_id = req_resp.json()["id"]

    flag_resp = await integration_client.post(
        f"/api/v1/requests/{request_id}/flag",
        json={"reason": "spam", "description": "Looks like spam"},
        headers=_auth(reporter_tok),
    )
    assert flag_resp.status_code == 201
    data = flag_resp.json()
    assert data["target_id"] == request_id
    assert data["reason"] == "spam"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_flag_own_request_rejected_e2e(integration_client):
    """Flagging own resource → 422 CANNOT_FLAG_OWN_RESOURCE."""
    owner_tok = await _register(integration_client, "flself@x.com", "flagself")
    cat_id, loc_id = await _cat_loc(integration_client)

    req_resp = await integration_client.post("/api/v1/requests", json={
        "title": "My own request", "description": "Cannot flag my own",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id,
        "location_scope": "CITY",
    }, headers=_auth(owner_tok))
    request_id = req_resp.json()["id"]

    flag_resp = await integration_client.post(
        f"/api/v1/requests/{request_id}/flag",
        json={"reason": "spam"},
        headers=_auth(owner_tok),
    )
    assert flag_resp.status_code == 422
    assert flag_resp.json()["detail"] == "CANNOT_FLAG_OWN_RESOURCE"


@pytest.mark.asyncio
async def test_flag_duplicate_rejected_e2e(integration_client):
    """Duplicate flag by same user → 422 ALREADY_FLAGGED."""
    owner_tok = await _register(integration_client, "fldup_own@x.com", "fldupown")
    reporter_tok = await _register(integration_client, "fldup_rep@x.com", "flduprep")
    cat_id, loc_id = await _cat_loc(integration_client)

    req_resp = await integration_client.post("/api/v1/requests", json={
        "title": "Duplicate flag target", "description": "Will be flagged twice",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id,
        "location_scope": "CITY",
    }, headers=_auth(owner_tok))
    request_id = req_resp.json()["id"]

    first = await integration_client.post(
        f"/api/v1/requests/{request_id}/flag",
        json={"reason": "abuse"},
        headers=_auth(reporter_tok),
    )
    assert first.status_code == 201

    second = await integration_client.post(
        f"/api/v1/requests/{request_id}/flag",
        json={"reason": "abuse"},
        headers=_auth(reporter_tok),
    )
    assert second.status_code == 422
    assert second.json()["detail"] == "ALREADY_FLAGGED"
