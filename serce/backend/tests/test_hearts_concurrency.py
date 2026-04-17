"""Concurrency tests for hearts_service — require real Postgres (SELECT FOR UPDATE).

Skip when TEST_DATABASE_URL is not set.
"""
from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL not set — concurrency tests require live Postgres",
)


@pytest_asyncio.fixture
async def pg_session_factory():
    """Session factory on migrated Postgres (reuses conftest.migrated_db logic)."""
    from tests.integration.conftest import _reset_schema, run_alembic

    assert TEST_DATABASE_URL
    await _reset_schema(TEST_DATABASE_URL)
    run_alembic("upgrade", "head")

    engine = create_async_engine(TEST_DATABASE_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield factory
    finally:
        await _reset_schema(TEST_DATABASE_URL)
        await engine.dispose()


async def _create_user_pg(factory, *, heart_balance: int = 0) -> "uuid.UUID":
    from app.core.security import hash_password
    from app.db.models.user import User

    async with factory() as db:
        user = User(
            email=f"conc_{uuid4().hex[:8]}@example.com",
            username=f"conc_{uuid4().hex[:8]}",
            password_hash=hash_password("TestPass1!"),
            heart_balance=heart_balance,
        )
        db.add(user)
        await db.commit()
        return user.id


@pytest.mark.asyncio
async def test_concurrent_gifts_no_negative_balance(pg_session_factory):
    """100 concurrent gifts of 1 heart from user with balance=50.
    Exactly 50 should succeed, rest should fail. Final balance = 0."""
    from app.db.models.user import User
    from app.services import hearts_service

    sender_id = await _create_user_pg(pg_session_factory, heart_balance=50)
    recipient_id = await _create_user_pg(pg_session_factory, heart_balance=0)

    async def _gift():
        async with pg_session_factory() as db:
            try:
                await hearts_service.gift_hearts(db, sender_id, recipient_id, 1, None)
                await db.commit()
                return True
            except Exception:
                await db.rollback()
                return False

    results = await asyncio.gather(*[_gift() for _ in range(100)])
    successes = sum(1 for r in results if r)

    assert successes == 50

    async with pg_session_factory() as db:
        sender = await db.get(User, sender_id)
        assert sender.heart_balance == 0
        recipient = await db.get(User, recipient_id)
        assert recipient.heart_balance == 50


@pytest.mark.asyncio
async def test_concurrent_gifts_to_same_recipient_cap(pg_session_factory):
    """Multiple senders gift to same recipient near cap. No one exceeds cap=50."""
    from app.db.models.user import User
    from app.services import hearts_service

    recipient_id = await _create_user_pg(pg_session_factory, heart_balance=45)

    sender_ids = []
    for _ in range(10):
        sid = await _create_user_pg(pg_session_factory, heart_balance=10)
        sender_ids.append(sid)

    async def _gift(sender_id):
        async with pg_session_factory() as db:
            try:
                await hearts_service.gift_hearts(db, sender_id, recipient_id, 2, None)
                await db.commit()
                return True
            except Exception:
                await db.rollback()
                return False

    results = await asyncio.gather(*[_gift(sid) for sid in sender_ids])
    successes = sum(1 for r in results if r)

    # Cap=50, start=45, each gift=2 → max 2 succeed (45+4=49 or 45+2=47→49)
    # Actually: 50-45=5 room, gifts of 2 → floor(5/2)=2 succeed
    assert successes <= 2

    async with pg_session_factory() as db:
        recipient = await db.get(User, recipient_id)
        assert recipient.heart_balance <= 50


@pytest.mark.asyncio
async def test_concurrent_gift_and_receive(pg_session_factory):
    """User sends and receives concurrently. Balance stays consistent."""
    from app.db.models.user import User
    from app.services import hearts_service

    user_a_id = await _create_user_pg(pg_session_factory, heart_balance=30)
    user_b_id = await _create_user_pg(pg_session_factory, heart_balance=30)

    async def _gift_a_to_b():
        async with pg_session_factory() as db:
            try:
                await hearts_service.gift_hearts(db, user_a_id, user_b_id, 1, None)
                await db.commit()
                return "ab"
            except Exception:
                await db.rollback()
                return None

    async def _gift_b_to_a():
        async with pg_session_factory() as db:
            try:
                await hearts_service.gift_hearts(db, user_b_id, user_a_id, 1, None)
                await db.commit()
                return "ba"
            except Exception:
                await db.rollback()
                return None

    tasks = [_gift_a_to_b() if i % 2 == 0 else _gift_b_to_a() for i in range(50)]
    results = await asyncio.gather(*tasks)

    ab_count = sum(1 for r in results if r == "ab")
    ba_count = sum(1 for r in results if r == "ba")

    async with pg_session_factory() as db:
        user_a = await db.get(User, user_a_id)
        user_b = await db.get(User, user_b_id)

    # Total hearts conserved
    assert user_a.heart_balance + user_b.heart_balance == 60
    # Balance matches expected: start 30, sent ab_count, received ba_count
    assert user_a.heart_balance == 30 - ab_count + ba_count
    assert user_b.heart_balance == 30 + ab_count - ba_count
