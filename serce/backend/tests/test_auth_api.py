"""Unit tests for auth endpoints — in-memory (no DB)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_register_missing_tos(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "StrongP@ss1",
        "tos_accepted": False,
        "privacy_policy_accepted": True,
    })
    assert resp.status_code == 422


async def test_register_short_password(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "short",
        "tos_accepted": True,
        "privacy_policy_accepted": True,
    })
    assert resp.status_code == 422


async def test_register_invalid_email(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "username": "testuser",
        "password": "StrongP@ss1",
        "tos_accepted": True,
        "privacy_policy_accepted": True,
    })
    assert resp.status_code == 422


async def test_register_short_username(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "ab",
        "password": "StrongP@ss1",
        "tos_accepted": True,
        "privacy_policy_accepted": True,
    })
    assert resp.status_code == 422


async def test_login_no_body(client):
    resp = await client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


async def test_me_no_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_invalid_token(client):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer garbage"},
    )
    assert resp.status_code == 401


async def test_sessions_no_token(client):
    resp = await client.get("/api/v1/auth/sessions")
    assert resp.status_code == 401


async def test_accept_terms_no_token(client):
    resp = await client.post("/api/v1/auth/accept-terms", json={
        "document_type": "tos",
    })
    assert resp.status_code == 401


async def test_accept_terms_invalid_type_no_token(client):
    """Without token, auth check fires first → 401 regardless of body."""
    resp = await client.post("/api/v1/auth/accept-terms", json={
        "document_type": "invalid",
    })
    assert resp.status_code == 401
