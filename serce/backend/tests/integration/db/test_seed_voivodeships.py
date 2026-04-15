"""Integration test: seed_voivodeships migration produces stable 16 voivodeships."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.models.location import Location, LocationType


@pytest.mark.asyncio
async def test_seed_voivodeships_count_and_ids(migrated_db):
    """After `alembic upgrade head` there are exactly 16 voivodeships with IDs 1-16."""
    async with migrated_db() as session:
        result = await session.execute(
            select(Location).where(Location.type == LocationType.VOIVODESHIP)
        )
        rows = list(result.scalars().all())

    assert len(rows) == 16, f"Expected 16 voivodeships, got {len(rows)}"

    ids = sorted(r.id for r in rows)
    assert ids == list(range(1, 17)), f"Voivodeship IDs must be 1..16, got {ids}"

    # Every voivodeship has parent_id = NULL (top of hierarchy).
    for row in rows:
        assert row.parent_id is None, f"Voivodeship {row.name} has parent_id={row.parent_id}"


@pytest.mark.asyncio
async def test_seed_voivodeships_spot_check_names(migrated_db):
    """Specific voivodeships must appear at stable IDs (relied on by seed_cities)."""
    async with migrated_db() as session:
        result = await session.execute(select(Location).where(Location.id.in_([7, 6, 12, 1])))
        by_id = {r.id: r.name for r in result.scalars().all()}

    assert by_id[7] == "Mazowieckie"
    assert by_id[6] == "Małopolskie"
    assert by_id[12] == "Śląskie"
    assert by_id[1] == "Dolnośląskie"
