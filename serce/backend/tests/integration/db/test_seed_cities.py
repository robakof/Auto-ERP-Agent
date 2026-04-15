"""Integration test: seed_cities migration loads 100 cities with valid FK to voivodeships."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.models.location import Location, LocationType


@pytest.mark.asyncio
async def test_seed_cities_count_and_parents(migrated_db):
    """After `alembic upgrade head`: 100 cities, each with parent_id in [1,16]."""
    async with migrated_db() as session:
        result = await session.execute(
            select(Location).where(Location.type == LocationType.CITY)
        )
        cities = list(result.scalars().all())

    assert len(cities) == 100, f"Expected 100 cities, got {len(cities)}"

    for c in cities:
        assert c.parent_id is not None, f"City {c.name} has no parent_id"
        assert 1 <= c.parent_id <= 16, f"City {c.name} parent_id={c.parent_id} out of range"


@pytest.mark.asyncio
async def test_seed_cities_spot_check_warsaw_krakow(migrated_db):
    """Warsaw → Mazowieckie (id=7), Kraków → Małopolskie (id=6)."""
    async with migrated_db() as session:
        result = await session.execute(
            select(Location).where(Location.name.in_(["Warszawa", "Kraków", "Gdańsk"]))
        )
        by_name = {r.name: r for r in result.scalars().all()}

    assert by_name["Warszawa"].parent_id == 7
    assert by_name["Warszawa"].type == LocationType.CITY
    assert by_name["Kraków"].parent_id == 6
    assert by_name["Gdańsk"].parent_id == 11  # Pomorskie


@pytest.mark.asyncio
async def test_seed_cities_ids_above_voivodeship_range(migrated_db):
    """City IDs must start above 16 (voivodeships reserve 1-16)."""
    async with migrated_db() as session:
        result = await session.execute(
            select(Location.id).where(Location.type == LocationType.CITY)
        )
        ids = [r[0] for r in result.all()]

    assert min(ids) > 16, f"City IDs overlap voivodeship range: min={min(ids)}"
