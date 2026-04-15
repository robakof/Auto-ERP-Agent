"""Integration test: GET /api/v1/locations public endpoint."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_list_locations_returns_all(integration_client):
    """GET /api/v1/locations → 200 + 116 records (16 voivodeships + 100 cities)."""
    response = await integration_client.get("/api/v1/locations")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 116

    # Response shape: flat [{id, name, type, parent_id}, ...]
    sample = data[0]
    assert set(sample.keys()) == {"id", "name", "type", "parent_id"}


@pytest.mark.asyncio
async def test_list_locations_filter_voivodeship(integration_client):
    """?type=VOIVODESHIP → 16 records, all with parent_id=None."""
    response = await integration_client.get("/api/v1/locations", params={"type": "VOIVODESHIP"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 16
    for loc in data:
        assert loc["type"] == "VOIVODESHIP"
        assert loc["parent_id"] is None


@pytest.mark.asyncio
async def test_list_locations_filter_city(integration_client):
    """?type=CITY → 100 records, each with parent_id in [1,16]."""
    response = await integration_client.get("/api/v1/locations", params={"type": "CITY"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 100
    for loc in data:
        assert loc["type"] == "CITY"
        assert 1 <= loc["parent_id"] <= 16


@pytest.mark.asyncio
async def test_list_locations_invalid_type(integration_client):
    """?type=FOO → 422 (enum validation)."""
    response = await integration_client.get("/api/v1/locations", params={"type": "FOO"})
    assert response.status_code == 422
