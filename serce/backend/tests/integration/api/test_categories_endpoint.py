"""Integration test: GET /api/v1/categories public endpoint."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_list_categories_default_active(integration_client):
    """GET /api/v1/categories → 200 + 36 active records (9 groups + 27 leaves)."""
    response = await integration_client.get("/api/v1/categories")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 36

    # Response shape: flat [{id, name, parent_id, icon, sort_order, active}, ...]
    sample = data[0]
    assert set(sample.keys()) == {"id", "name", "parent_id", "icon", "sort_order", "active"}
    for c in data:
        assert c["active"] is True


@pytest.mark.asyncio
async def test_list_categories_ordered_by_sort(integration_client):
    """Sort order within groups honored — first 9 are groups (parent_id=None)."""
    response = await integration_client.get("/api/v1/categories")
    data = response.json()

    # First 9 should be groups (sort_order 0-8, parent_id None).
    groups = [c for c in data if c["parent_id"] is None]
    assert len(groups) == 9
    assert [g["sort_order"] for g in groups] == list(range(9))


@pytest.mark.asyncio
async def test_list_categories_all_includes_inactive(integration_client):
    """?active=false → 0 records (nothing seeded as inactive in M2)."""
    response = await integration_client.get("/api/v1/categories", params={"active": "false"})
    assert response.status_code == 200

    data = response.json()
    assert data == []
