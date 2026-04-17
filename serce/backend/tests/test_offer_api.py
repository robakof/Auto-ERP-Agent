"""Unit tests for offers endpoints — auth guard (no DB)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_create_no_token(client):
    resp = await client.post("/api/v1/offers", json={
        "title": "Test", "description": "Long enough description here",
        "hearts_asked": 0, "category_id": 1, "location_id": 1,
        "location_scope": "CITY",
    })
    assert resp.status_code == 401


async def test_get_no_token(client):
    resp = await client.get("/api/v1/offers/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 401


async def test_update_no_token(client):
    resp = await client.patch(
        "/api/v1/offers/00000000-0000-0000-0000-000000000001",
        json={"title": "New title"},
    )
    assert resp.status_code == 401


async def test_status_no_token(client):
    resp = await client.patch(
        "/api/v1/offers/00000000-0000-0000-0000-000000000001/status",
        json={"status": "PAUSED"},
    )
    assert resp.status_code == 401


async def test_list_no_token(client):
    resp = await client.get("/api/v1/offers")
    assert resp.status_code == 401
