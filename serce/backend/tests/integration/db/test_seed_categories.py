"""Integration test: seed_categories migration loads 9 groups + 27 leaf categories."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.models.category import Category


@pytest.mark.asyncio
async def test_seed_categories_groups_count_and_ids(migrated_db):
    """9 top-level groups with stable IDs 1-9, all active, parent_id=NULL."""
    async with migrated_db() as session:
        result = await session.execute(select(Category).where(Category.parent_id.is_(None)))
        groups = list(result.scalars().all())

    assert len(groups) == 9, f"Expected 9 groups, got {len(groups)}"

    ids = sorted(g.id for g in groups)
    assert ids == list(range(1, 10)), f"Group IDs must be 1..9, got {ids}"

    for g in groups:
        assert g.active is True, f"Group {g.name} not active"


@pytest.mark.asyncio
async def test_seed_categories_leaves_count_and_parents(migrated_db):
    """27 leaf categories (see revision note), each parent_id in [1,8] (group 9 'Inne' has none)."""
    async with migrated_db() as session:
        result = await session.execute(select(Category).where(Category.parent_id.is_not(None)))
        leaves = list(result.scalars().all())

    assert len(leaves) == 27, f"Expected 27 leaves, got {len(leaves)}"

    for leaf in leaves:
        assert 1 <= leaf.parent_id <= 8, (
            f"Leaf {leaf.name} parent_id={leaf.parent_id} out of expected range [1,8]"
        )
        assert leaf.active is True


@pytest.mark.asyncio
async def test_seed_categories_sort_order_within_group(migrated_db):
    """sort_order within each group is contiguous 0..N-1."""
    async with migrated_db() as session:
        result = await session.execute(
            select(Category).where(Category.parent_id.is_not(None)).order_by(Category.parent_id, Category.sort_order)
        )
        leaves = list(result.scalars().all())

    by_parent: dict[int, list[int]] = {}
    for c in leaves:
        by_parent.setdefault(c.parent_id, []).append(c.sort_order)

    for parent_id, orders in by_parent.items():
        assert orders == list(range(len(orders))), (
            f"Group {parent_id} sort_order not contiguous: {orders}"
        )


@pytest.mark.asyncio
async def test_seed_categories_spot_check_names(migrated_db):
    """Specific groups present at expected IDs."""
    async with migrated_db() as session:
        result = await session.execute(select(Category).where(Category.id.in_([1, 2, 9])))
        by_id = {c.id: c.name for c in result.scalars().all()}

    assert by_id[1] == "Dom i otoczenie"
    assert by_id[2] == "Opieka"
    assert by_id[9] == "Inne"
