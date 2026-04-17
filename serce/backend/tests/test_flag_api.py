"""Unit tests for flag endpoints — auth guard (no DB)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


TARGET_ID = "00000000-0000-0000-0000-000000000001"
FLAG_BODY = {"reason": "spam"}


async def test_flag_request_no_token(client):
    resp = await client.post(f"/api/v1/requests/{TARGET_ID}/flag", json=FLAG_BODY)
    assert resp.status_code == 401


async def test_flag_offer_no_token(client):
    resp = await client.post(f"/api/v1/offers/{TARGET_ID}/flag", json=FLAG_BODY)
    assert resp.status_code == 401


async def test_flag_exchange_no_token(client):
    resp = await client.post(f"/api/v1/exchanges/{TARGET_ID}/flag", json=FLAG_BODY)
    assert resp.status_code == 401


async def test_flag_user_no_token(client):
    resp = await client.post(f"/api/v1/users/{TARGET_ID}/flag", json=FLAG_BODY)
    assert resp.status_code == 401
