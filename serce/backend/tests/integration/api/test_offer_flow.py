"""Integration tests — offer CRUD, status management flows."""
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


async def _get_cat_loc(client: AsyncClient) -> tuple[int, int]:
    cat_resp = await client.get("/api/v1/categories")
    cats = cat_resp.json()
    cat_id = cats[0]["id"] if cats else 1
    loc_resp = await client.get("/api/v1/locations")
    locs = loc_resp.json()
    loc_id = locs[0]["id"] if locs else 1
    return cat_id, loc_id


def _offer_body(cat_id: int, loc_id: int, **overrides) -> dict:
    body = {
        "title": "Pomogę z przeprowadzką",
        "description": "Mam doświadczenie z przenoszeniem mebli i pakowania rzeczy",
        "hearts_asked": 3,
        "category_id": cat_id,
        "location_id": loc_id,
        "location_scope": "CITY",
    }
    body.update(overrides)
    return body


@pytest.mark.asyncio
async def test_create_and_get_offer(integration_client):
    token = await _register(integration_client, "ofcreate@example.com", "ofcreator")
    cat_id, loc_id = await _get_cat_loc(integration_client)

    resp = await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id), headers=_auth(token),
    )
    assert resp.status_code == 201
    offer_id = resp.json()["id"]

    get_resp = await integration_client.get(f"/api/v1/offers/{offer_id}", headers=_auth(token))
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Pomogę z przeprowadzką"


@pytest.mark.asyncio
async def test_create_and_list(integration_client):
    token = await _register(integration_client, "oflist@example.com", "oflister")
    cat_id, loc_id = await _get_cat_loc(integration_client)

    await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id, title="First offer"),
        headers=_auth(token),
    )
    await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id, title="Second offer"),
        headers=_auth(token),
    )

    list_resp = await integration_client.get("/api/v1/offers", headers=_auth(token))
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 2


@pytest.mark.asyncio
async def test_update_offer(integration_client):
    token = await _register(integration_client, "ofupdate@example.com", "ofupdater")
    cat_id, loc_id = await _get_cat_loc(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id), headers=_auth(token),
    )
    offer_id = create_resp.json()["id"]

    patch_resp = await integration_client.patch(
        f"/api/v1/offers/{offer_id}",
        json={"title": "Zmieniony tytuł oferty"},
        headers=_auth(token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Zmieniony tytuł oferty"


@pytest.mark.asyncio
async def test_status_pause_and_resume(integration_client):
    token = await _register(integration_client, "ofpause@example.com", "ofpauser")
    cat_id, loc_id = await _get_cat_loc(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id), headers=_auth(token),
    )
    offer_id = create_resp.json()["id"]

    # Pause
    pause_resp = await integration_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "PAUSED"},
        headers=_auth(token),
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "PAUSED"

    # Resume
    resume_resp = await integration_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "ACTIVE"},
        headers=_auth(token),
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_status_inactive(integration_client):
    token = await _register(integration_client, "ofinact@example.com", "ofinacter")
    cat_id, loc_id = await _get_cat_loc(integration_client)

    create_resp = await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id), headers=_auth(token),
    )
    offer_id = create_resp.json()["id"]

    inact_resp = await integration_client.patch(
        f"/api/v1/offers/{offer_id}/status",
        json={"status": "INACTIVE"},
        headers=_auth(token),
    )
    assert inact_resp.status_code == 200
    assert inact_resp.json()["status"] == "INACTIVE"

    # Should not appear in default (ACTIVE) list
    list_resp = await integration_client.get("/api/v1/offers", headers=_auth(token))
    ids = [e["id"] for e in list_resp.json()["entries"]]
    assert offer_id not in ids


@pytest.mark.asyncio
async def test_list_search(integration_client):
    token = await _register(integration_client, "ofsearch@example.com", "ofsearcher")
    cat_id, loc_id = await _get_cat_loc(integration_client)

    await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id, title="Nauka gitary"),
        headers=_auth(token),
    )
    await integration_client.post(
        "/api/v1/offers", json=_offer_body(cat_id, loc_id, title="Opieka nad psem"),
        headers=_auth(token),
    )

    search_resp = await integration_client.get(
        "/api/v1/offers", params={"q": "gitary"}, headers=_auth(token),
    )
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
