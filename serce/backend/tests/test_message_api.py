"""Unit tests for messages endpoints — auth guard (no DB)."""
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
MESSAGE_ID = "00000000-0000-0000-0000-000000000002"


async def test_send_no_token(client):
    resp = await client.post(
        f"/api/v1/exchanges/{EXCHANGE_ID}/messages",
        json={"content": "Hello!"},
    )
    assert resp.status_code == 401


async def test_list_no_token(client):
    resp = await client.get(f"/api/v1/exchanges/{EXCHANGE_ID}/messages")
    assert resp.status_code == 401


async def test_hide_no_token(client):
    resp = await client.patch(
        f"/api/v1/exchanges/{EXCHANGE_ID}/messages/{MESSAGE_ID}/hide",
    )
    assert resp.status_code == 401
