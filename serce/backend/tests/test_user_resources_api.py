"""Unit tests for user_resources endpoints — auth guard (no DB)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


USER_ID = "00000000-0000-0000-0000-000000000001"


async def test_my_requests_no_token(client):
    resp = await client.get("/api/v1/users/me/requests")
    assert resp.status_code == 401


async def test_my_offers_no_token(client):
    resp = await client.get("/api/v1/users/me/offers")
    assert resp.status_code == 401


async def test_my_exchanges_no_token(client):
    resp = await client.get("/api/v1/users/me/exchanges")
    assert resp.status_code == 401


async def test_my_reviews_no_token(client):
    resp = await client.get("/api/v1/users/me/reviews")
    assert resp.status_code == 401


async def test_my_ledger_no_token(client):
    resp = await client.get("/api/v1/users/me/ledger")
    assert resp.status_code == 401


async def test_my_summary_no_token(client):
    resp = await client.get("/api/v1/users/me/summary")
    assert resp.status_code == 401


async def test_public_profile_no_token(client):
    resp = await client.get(f"/api/v1/users/{USER_ID}/profile")
    assert resp.status_code == 401
