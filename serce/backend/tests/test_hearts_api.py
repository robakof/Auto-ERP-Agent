"""Unit tests for hearts endpoints — in-memory (no DB)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---- POST /hearts/gift ------------------------------------------------------

async def test_gift_no_token(client):
    resp = await client.post("/api/v1/hearts/gift", json={
        "to_user_id": "00000000-0000-0000-0000-000000000001",
        "amount": 1,
    })
    assert resp.status_code == 401


async def test_gift_missing_to_user_id(client):
    """No auth → 401 fires before body validation."""
    resp = await client.post("/api/v1/hearts/gift", json={"amount": 1})
    assert resp.status_code == 401


async def test_gift_invalid_amount_zero(client):
    """No auth → 401 fires before schema validation."""
    resp = await client.post("/api/v1/hearts/gift", json={
        "to_user_id": "00000000-0000-0000-0000-000000000001",
        "amount": 0,
    })
    assert resp.status_code == 401


async def test_gift_invalid_amount_negative(client):
    """No auth → 401."""
    resp = await client.post("/api/v1/hearts/gift", json={
        "to_user_id": "00000000-0000-0000-0000-000000000001",
        "amount": -5,
    })
    assert resp.status_code == 401


# ---- GET /hearts/balance -----------------------------------------------------

async def test_balance_no_token(client):
    resp = await client.get("/api/v1/hearts/balance")
    assert resp.status_code == 401


# ---- GET /hearts/ledger ------------------------------------------------------

async def test_ledger_no_token(client):
    resp = await client.get("/api/v1/hearts/ledger")
    assert resp.status_code == 401
