"""Unit tests for notification endpoints — auth guard + ownership."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


NOTIFICATION_ID = "00000000-0000-0000-0000-000000000001"


async def test_list_notifications_no_token(client):
    resp = await client.get("/api/v1/users/me/notifications")
    assert resp.status_code == 401


async def test_mark_read_no_token(client):
    resp = await client.post(f"/api/v1/users/me/notifications/{NOTIFICATION_ID}/read")
    assert resp.status_code == 401


async def test_mark_all_read_no_token(client):
    resp = await client.post("/api/v1/users/me/notifications/read-all")
    assert resp.status_code == 401


async def test_unread_count_no_token(client):
    resp = await client.get("/api/v1/users/me/notifications/unread-count")
    assert resp.status_code == 401
