"""Integration tests — admin flows (resolve flag, suspend, unsuspend, grant hearts, audit)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.db.models.user import User, UserRole

pytestmark = pytest.mark.integration

TEST_PASSWORD = "StrongP@ss1"


def _reg(email: str, username: str) -> dict:
    return {
        "email": email, "username": username, "password": TEST_PASSWORD,
        "tos_accepted": True, "privacy_policy_accepted": True,
    }


async def _register(client: AsyncClient, email: str, username: str) -> str:
    resp = await client.post("/api/v1/auth/register", json=_reg(email, username))
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _me(client: AsyncClient, token: str) -> dict:
    resp = await client.get("/api/v1/users/me", headers=_auth(token))
    return resp.json()


async def _promote_admin(migrated_db, email: str) -> None:
    """Promote a user to ADMIN role via direct DB update."""
    async with migrated_db() as db:
        await db.execute(
            update(User).where(User.email == email).values(role=UserRole.ADMIN)
        )
        await db.commit()


async def _cat_loc(client: AsyncClient) -> tuple[int, int]:
    cats = (await client.get("/api/v1/categories")).json()
    locs = (await client.get("/api/v1/locations")).json()
    return cats[0]["id"] if cats else 1, locs[0]["id"] if locs else 1


@pytest.mark.asyncio
async def test_resolve_flag_dismiss_e2e(integration_client, migrated_db):
    """Admin resolves a flag with dismiss action."""
    admin_tok = await _register(integration_client, "admres@x.com", "admresolver")
    await _promote_admin(migrated_db, "admres@x.com")

    reporter_tok = await _register(integration_client, "reprfl@x.com", "reprflag")
    owner_tok = await _register(integration_client, "ownrfl@x.com", "ownrflag")
    cat_id, loc_id = await _cat_loc(integration_client)

    # Create request and flag it
    req_resp = await integration_client.post("/api/v1/requests", json={
        "title": "Admin test request", "description": "Will be flagged and dismissed",
        "hearts_offered": 0, "category_id": cat_id, "location_id": loc_id,
        "location_scope": "CITY",
    }, headers=_auth(owner_tok))
    request_id = req_resp.json()["id"]

    flag_resp = await integration_client.post(
        f"/api/v1/requests/{request_id}/flag",
        json={"reason": "spam"},
        headers=_auth(reporter_tok),
    )
    flag_id = flag_resp.json()["id"]

    # Admin resolves (dismiss)
    resolve_resp = await integration_client.post(
        f"/api/v1/admin/flags/{flag_id}/resolve",
        json={"action": "dismiss", "reason": "Not spam, legitimate content"},
        headers=_auth(admin_tok),
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "dismissed"
    assert resolve_resp.json()["resolution_action"] == "dismiss"


@pytest.mark.asyncio
async def test_suspend_user_e2e(integration_client, migrated_db):
    """Admin suspends user → user gets 403 ACCOUNT_NOT_ACTIVE."""
    admin_tok = await _register(integration_client, "admsus@x.com", "admsuspend")
    await _promote_admin(migrated_db, "admsus@x.com")

    user_tok = await _register(integration_client, "susptgt@x.com", "susptarget")
    user_data = await _me(integration_client, user_tok)
    user_id = user_data["id"]

    # Suspend
    susp_resp = await integration_client.post(
        f"/api/v1/admin/users/{user_id}/suspend",
        json={"reason": "Policy violation", "duration_days": 7},
        headers=_auth(admin_tok),
    )
    assert susp_resp.status_code == 200
    assert susp_resp.json()["status"] == "suspended"

    # Suspended user cannot access protected endpoint
    me_resp = await integration_client.get("/api/v1/users/me", headers=_auth(user_tok))
    assert me_resp.status_code == 403
    assert me_resp.json()["detail"] == "ACCOUNT_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_unsuspend_user_e2e(integration_client, migrated_db):
    """Admin suspends then unsuspends → user access restored."""
    admin_tok = await _register(integration_client, "admunsus@x.com", "admunsuspend")
    await _promote_admin(migrated_db, "admunsus@x.com")

    user_tok = await _register(integration_client, "unsptgt@x.com", "unsptarget")
    user_data = await _me(integration_client, user_tok)
    user_id = user_data["id"]

    # Suspend
    await integration_client.post(
        f"/api/v1/admin/users/{user_id}/suspend",
        json={"reason": "Temp suspension"},
        headers=_auth(admin_tok),
    )

    # Unsuspend
    unsus_resp = await integration_client.post(
        f"/api/v1/admin/users/{user_id}/unsuspend",
        headers=_auth(admin_tok),
    )
    assert unsus_resp.status_code == 200
    assert unsus_resp.json()["status"] == "active"

    # User access restored
    me_resp = await integration_client.get("/api/v1/users/me", headers=_auth(user_tok))
    assert me_resp.status_code == 200


@pytest.mark.asyncio
async def test_grant_hearts_e2e(integration_client, migrated_db):
    """Admin grants hearts → user balance increases."""
    admin_tok = await _register(integration_client, "admgrt@x.com", "admgrant")
    await _promote_admin(migrated_db, "admgrt@x.com")

    user_tok = await _register(integration_client, "grtuser@x.com", "grantuser")
    user_data = await _me(integration_client, user_tok)
    user_id = user_data["id"]

    bal_before = (await integration_client.get(
        "/api/v1/hearts/balance", headers=_auth(user_tok),
    )).json()["heart_balance"]

    grant_resp = await integration_client.post("/api/v1/admin/hearts/grant", json={
        "user_id": user_id, "amount": 10, "type": "ADMIN_GRANT",
        "reason": "Welcome bonus",
    }, headers=_auth(admin_tok))
    assert grant_resp.status_code == 201

    bal_after = (await integration_client.get(
        "/api/v1/hearts/balance", headers=_auth(user_tok),
    )).json()["heart_balance"]
    assert bal_after == bal_before + 10


@pytest.mark.asyncio
async def test_audit_log_e2e(integration_client, migrated_db):
    """After admin operations → audit log contains entries."""
    admin_tok = await _register(integration_client, "admaud@x.com", "admaudit")
    await _promote_admin(migrated_db, "admaud@x.com")

    user_tok = await _register(integration_client, "auduser@x.com", "audituser")
    user_data = await _me(integration_client, user_tok)
    user_id = user_data["id"]

    # Perform admin action (grant hearts)
    await integration_client.post("/api/v1/admin/hearts/grant", json={
        "user_id": user_id, "amount": 5, "type": "ADMIN_GRANT",
        "reason": "Audit test",
    }, headers=_auth(admin_tok))

    # Check audit log
    audit_resp = await integration_client.get(
        "/api/v1/admin/audit", headers=_auth(admin_tok),
    )
    assert audit_resp.status_code == 200
    data = audit_resp.json()
    assert data["total"] > 0
    actions = [e["action"] for e in data["entries"]]
    assert any("grant" in a.lower() or "GRANT" in a for a in actions)
