"""Integration tests — request CRUD, listing, search, cancel flows."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


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


async def _ensure_category_and_location(client: AsyncClient) -> tuple[int, int]:
    """Get first category and location IDs from seeded data."""
    # Categories endpoint
    cat_resp = await client.get("/api/v1/categories")
    cats = cat_resp.json()
    cat_id = cats[0]["id"] if cats else 1

    loc_resp = await client.get("/api/v1/locations")
    locs = loc_resp.json()
    loc_id = locs[0]["id"] if locs else 1

    return cat_id, loc_id


def _request_body(cat_id: int, loc_id: int, **overrides) -> dict:
    body = {
        "title": "Potrzebuję pomocy z przeprowadzką",
        "description": "Szukam kogoś kto pomoże mi przenieść meble z mieszkania na 3 piętrze",
        "hearts_offered": 5,
        "category_id": cat_id,
        "location_id": loc_id,
        "location_scope": "CITY",
    }
    body.update(overrides)
    return body


@pytest.mark.asyncio
async def test_create_and_get_request(integration_client):
    token = await _register(integration_client, "reqcreate@example.com", "reqcreator")
    cat_id, loc_id = await _ensure_category_and_location(integration_client)

    resp = await integration_client.post(
        "/api/v1/requests",
        json=_request_body(cat_id, loc_id),
        headers=_auth(token),
    )
    assert resp.status_code == 201
    req_id = resp.json()["id"]

    get_resp = await integration_client.get(f"/api/v1/requests/{req_id}", headers=_auth(token))
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Potrzebuję pomocy z przeprowadzką"


@pytest.mark.asyncio
async def test_create_and_list(integration_client):
    token = await _register(integration_client, "reqlist@example.com", "reqlister")
    cat_id, loc_id = await _ensure_category_and_location(integration_client)

    await integration_client.post(
        "/api/v1/requests",
        json=_request_body(cat_id, loc_id, title="First request here"),
        headers=_auth(token),
    )
    await integration_client.post(
        "/api/v1/requests",
        json=_request_body(cat_id, loc_id, title="Second request here"),
        headers=_auth(token),
    )

    list_resp = await integration_client.get("/api/v1/requests", headers=_auth(token))
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_update_request(integration_client):
    token = await _register(integration_client, "requpdate@example.com", "requpdater")
    cat_id, loc_id = await _ensure_category_and_location(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/requests",
        json=_request_body(cat_id, loc_id),
        headers=_auth(token),
    )
    req_id = create_resp.json()["id"]

    patch_resp = await integration_client.patch(
        f"/api/v1/requests/{req_id}",
        json={"title": "Zaktualizowany tytuł"},
        headers=_auth(token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Zaktualizowany tytuł"


@pytest.mark.asyncio
async def test_cancel_request(integration_client):
    token = await _register(integration_client, "reqcancel@example.com", "reqcanceler")
    cat_id, loc_id = await _ensure_category_and_location(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/requests",
        json=_request_body(cat_id, loc_id),
        headers=_auth(token),
    )
    req_id = create_resp.json()["id"]

    cancel_resp = await integration_client.post(
        f"/api/v1/requests/{req_id}/cancel",
        headers=_auth(token),
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_list_search(integration_client):
    token = await _register(integration_client, "reqsearch@example.com", "reqsearcher")
    cat_id, loc_id = await _ensure_category_and_location(integration_client)

    await integration_client.post(
        "/api/v1/requests",
        json=_request_body(cat_id, loc_id, title="Pomoc z kotem domowym"),
        headers=_auth(token),
    )
    await integration_client.post(
        "/api/v1/requests",
        json=_request_body(cat_id, loc_id, title="Naprawa roweru górskiego"),
        headers=_auth(token),
    )

    search_resp = await integration_client.get(
        "/api/v1/requests", params={"q": "kotem"}, headers=_auth(token),
    )
    assert search_resp.status_code == 200
    data = search_resp.json()
    assert data["total"] == 1
    assert "kotem" in data["entries"][0]["title"]


@pytest.mark.asyncio
async def test_list_pagination(integration_client):
    token = await _register(integration_client, "reqpage@example.com", "reqpager")
    cat_id, loc_id = await _ensure_category_and_location(integration_client)

    for i in range(5):
        await integration_client.post(
            "/api/v1/requests",
            json=_request_body(cat_id, loc_id, title=f"Paginated request {i}"),
            headers=_auth(token),
        )

    page_resp = await integration_client.get(
        "/api/v1/requests", params={"offset": 2, "limit": 2}, headers=_auth(token),
    )
    assert page_resp.status_code == 200
    data = page_resp.json()
    assert data["total"] >= 5
    assert len(data["entries"]) == 2
    assert data["offset"] == 2
    assert data["limit"] == 2
