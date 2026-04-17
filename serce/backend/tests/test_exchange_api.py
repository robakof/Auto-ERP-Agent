"""Unit tests for exchanges endpoints — auth guard (no DB)."""
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
    resp = await client.post("/api/v1/exchanges", json={
        "request_id": "00000000-0000-0000-0000-000000000001", "hearts_agreed": 5,
    })
    assert resp.status_code == 401


async def test_get_no_token(client):
    resp = await client.get("/api/v1/exchanges/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 401


async def test_accept_no_token(client):
    resp = await client.patch("/api/v1/exchanges/00000000-0000-0000-0000-000000000001/accept")
    assert resp.status_code == 401


async def test_complete_no_token(client):
    resp = await client.patch("/api/v1/exchanges/00000000-0000-0000-0000-000000000001/complete")
    assert resp.status_code == 401


async def test_cancel_no_token(client):
    resp = await client.patch("/api/v1/exchanges/00000000-0000-0000-0000-000000000001/cancel")
    assert resp.status_code == 401


async def test_list_no_token(client):
    resp = await client.get("/api/v1/exchanges")
    assert resp.status_code == 401
