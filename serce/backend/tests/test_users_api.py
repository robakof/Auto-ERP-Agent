"""Unit tests for users endpoints — in-memory (no DB)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---- GET /users/me -----------------------------------------------------------

async def test_get_me_no_token(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


# ---- PATCH /users/me ---------------------------------------------------------

async def test_patch_me_no_token(client):
    resp = await client.patch("/api/v1/users/me", json={"bio": "hello"})
    assert resp.status_code == 401


# ---- PATCH /users/me/username ------------------------------------------------

async def test_change_username_no_token(client):
    resp = await client.patch("/api/v1/users/me/username", json={"new_username": "test"})
    assert resp.status_code == 401


# ---- POST /users/me/email/change --------------------------------------------

async def test_change_email_no_token(client):
    resp = await client.post("/api/v1/users/me/email/change", json={
        "password": "x", "new_email": "a@b.com",
    })
    assert resp.status_code == 401


# ---- POST /users/me/email/confirm -------------------------------------------

async def test_confirm_email_no_body(client):
    """confirm endpoint has no auth dep — empty body → 422."""
    resp = await client.post("/api/v1/users/me/email/confirm", json={})
    assert resp.status_code == 422


# ---- POST /users/me/phone/change --------------------------------------------

async def test_change_phone_no_token(client):
    resp = await client.post("/api/v1/users/me/phone/change", json={
        "password": "x", "new_phone_number": "+48123456789",
    })
    assert resp.status_code == 401


# ---- POST /users/me/phone/verify --------------------------------------------

async def test_verify_phone_change_no_token(client):
    resp = await client.post("/api/v1/users/me/phone/verify", json={
        "new_phone_number": "+48123456789", "code": "123456",
    })
    assert resp.status_code == 401


# ---- POST /users/me/password -------------------------------------------------

async def test_change_password_no_token(client):
    resp = await client.post("/api/v1/users/me/password", json={
        "old_password": "x", "new_password": "LongEnough1!",
    })
    assert resp.status_code == 401
