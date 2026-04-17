"""Unit tests for admin endpoints — auth guard (401 no token + 403 non-admin)."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.deps import AuthContext, get_auth_context
from app.db.models.user import UserRole, UserStatus
from app.main import app


def _fake_user(role: UserRole = UserRole.USER):
    user = MagicMock()
    user.id = uuid4()
    user.role = role
    user.status = UserStatus.ACTIVE
    return user


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def user_client():
    """Client authenticated as regular USER (not admin)."""
    fake = _fake_user(UserRole.USER)

    async def _override():
        return AuthContext(user=fake, session_id=None)

    app.dependency_overrides[get_auth_context] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_auth_context, None)


DUMMY_ID = "00000000-0000-0000-0000-000000000001"
RESOLVE_BODY = {"action": "dismiss", "reason": "test"}
SUSPEND_BODY = {"reason": "test"}
GRANT_BODY = {"user_id": DUMMY_ID, "amount": 10, "type": "ADMIN_GRANT", "reason": "test"}


# ---- 401 no token -----------------------------------------------------------

async def test_list_flags_no_token(client):
    resp = await client.get("/api/v1/admin/flags")
    assert resp.status_code == 401


async def test_resolve_flag_no_token(client):
    resp = await client.post(f"/api/v1/admin/flags/{DUMMY_ID}/resolve", json=RESOLVE_BODY)
    assert resp.status_code == 401


async def test_suspend_no_token(client):
    resp = await client.post(f"/api/v1/admin/users/{DUMMY_ID}/suspend", json=SUSPEND_BODY)
    assert resp.status_code == 401


async def test_unsuspend_no_token(client):
    resp = await client.post(f"/api/v1/admin/users/{DUMMY_ID}/unsuspend")
    assert resp.status_code == 401


async def test_grant_no_token(client):
    resp = await client.post("/api/v1/admin/hearts/grant", json=GRANT_BODY)
    assert resp.status_code == 401


async def test_audit_no_token(client):
    resp = await client.get("/api/v1/admin/audit")
    assert resp.status_code == 401


# ---- 403 non-admin ----------------------------------------------------------

async def test_list_flags_non_admin(user_client):
    resp = await user_client.get("/api/v1/admin/flags")
    assert resp.status_code == 403


async def test_resolve_flag_non_admin(user_client):
    resp = await user_client.post(f"/api/v1/admin/flags/{DUMMY_ID}/resolve", json=RESOLVE_BODY)
    assert resp.status_code == 403


async def test_suspend_non_admin(user_client):
    resp = await user_client.post(f"/api/v1/admin/users/{DUMMY_ID}/suspend", json=SUSPEND_BODY)
    assert resp.status_code == 403


async def test_unsuspend_non_admin(user_client):
    resp = await user_client.post(f"/api/v1/admin/users/{DUMMY_ID}/unsuspend")
    assert resp.status_code == 403


async def test_grant_non_admin(user_client):
    resp = await user_client.post("/api/v1/admin/hearts/grant", json=GRANT_BODY)
    assert resp.status_code == 403


async def test_audit_non_admin(user_client):
    resp = await user_client.get("/api/v1/admin/audit")
    assert resp.status_code == 403
