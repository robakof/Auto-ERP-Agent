"""Unit tests for account endpoints — auth guard + public profile placeholder."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.deps import AuthContext, get_auth_context
from app.db.models.user import UserRole, UserStatus
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


DELETE_BODY = {"password": "Test1!", "balance_disposition": "void"}


async def test_delete_no_token(client):
    resp = await client.request("DELETE", "/api/v1/users/me", json=DELETE_BODY)
    assert resp.status_code == 401
