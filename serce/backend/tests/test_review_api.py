"""Unit tests for reviews endpoints — auth guard (no DB)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


EXCHANGE_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "00000000-0000-0000-0000-000000000002"


async def test_create_no_token(client):
    resp = await client.post(
        f"/api/v1/exchanges/{EXCHANGE_ID}/reviews",
        json={"comment": "Great experience with this exchange!"},
    )
    assert resp.status_code == 401


async def test_list_exchange_no_token(client):
    resp = await client.get(f"/api/v1/exchanges/{EXCHANGE_ID}/reviews")
    assert resp.status_code == 401


async def test_list_user_no_token(client):
    resp = await client.get(f"/api/v1/users/{USER_ID}/reviews")
    assert resp.status_code == 401
