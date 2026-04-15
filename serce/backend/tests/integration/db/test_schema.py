"""Integration tests for the initial_schema migration (M1).

Covers roadmap DoD: `tests/integration/db/test_schema.py` — smoke INSERT
oraz pełny cykl upgrade/downgrade/upgrade na rzeczywistym PostgreSQL.

Uruchomienie:
    # docker compose up -d db  (lub dostępny Postgres)
    TEST_DATABASE_URL=postgresql+asyncpg://serce:serce_dev@localhost:5432/serce \
        pytest tests/integration/db/test_schema.py -v
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
import app.db.models  # noqa: F401 — register all models
from app.db.models.category import Category
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.location import Location, LocationType
from app.db.models.user import User

from tests.integration.conftest import run_alembic

EXPECTED_TABLES = set(Base.metadata.tables.keys())
EXPECTED_ENUMS = {
    "locationtype", "userstatus", "userrole", "documenttype",
    "heartledgertype", "requeststatus", "locationscope", "offerstatus",
    "exchangestatus", "notificationtype", "flagtargettype", "flagreason",
    "flagstatus", "resolutionaction", "audittargettype",
}


async def _table_names(url: str) -> set[str]:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            names = await conn.run_sync(
                lambda sync_conn: set(inspect(sync_conn).get_table_names(schema="public"))
            )
    finally:
        await engine.dispose()
    return names


async def _enum_names(url: str) -> set[str]:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT typname FROM pg_type WHERE typtype = 'e'")
            )
            return {row[0] for row in result}
    finally:
        await engine.dispose()


async def test_upgrade_creates_all_tables(clean_db):
    """alembic upgrade head creates every table + enum in Base.metadata."""
    run_alembic("upgrade", "head")

    tables = await _table_names(clean_db)
    missing_tables = EXPECTED_TABLES - tables
    assert not missing_tables, f"Missing tables after upgrade: {missing_tables}"

    enums = await _enum_names(clean_db)
    missing_enums = EXPECTED_ENUMS - enums
    assert not missing_enums, f"Missing enum types after upgrade: {missing_enums}"

    # alembic_version also present
    assert "alembic_version" in tables


async def test_insert_location_category_user(migrated_db):
    """ORM INSERT + SELECT — verifies schema matches models on real DB.

    Uses IDs above the reserved seed range (locations 1-16 + cities, categories 1-9 + leaves)
    to avoid collision with data seeded by M2 migrations.
    """
    async with migrated_db() as session:
        loc = Location(id=9001, name="Test-voivodeship", type=LocationType.VOIVODESHIP)
        cat = Category(id=9001, name="Pomoc sąsiedzka", sort_order=0, active=True)
        user = User(
            email="ada@example.com",
            username="ada",
            password_hash="x" * 60,
            location_id=9001,
        )
        session.add_all([loc, cat, user])
        await session.commit()

    async with migrated_db() as session:
        db_user = (await session.execute(
            text("SELECT email, heart_balance, email_verified, status, role FROM users")
        )).first()
        assert db_user.email == "ada@example.com"
        # server_default values must kick in for fields not set by Python
        assert db_user.heart_balance == 0
        assert db_user.email_verified is False
        assert db_user.status == "active"
        assert db_user.role == "user"


async def test_insert_respects_check_constraints(migrated_db):
    """CHECK constraint `heart_balance >= 0` must be enforced by PostgreSQL."""
    async with migrated_db() as session:
        user = User(
            email="bob@example.com",
            username="bob",
            password_hash="x" * 60,
            heart_balance=-1,
        )
        session.add(user)
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_insert_respects_partial_unique_index(migrated_db):
    """Partial unique index: only one INITIAL_GRANT per to_user_id."""
    # Seed a user first
    async with migrated_db() as session:
        user = User(email="c@e.pl", username="c", password_hash="x" * 60)
        session.add(user)
        await session.commit()
        user_id = user.id

    async with migrated_db() as session:
        session.add(HeartLedger(
            from_user_id=None, to_user_id=user_id, amount=5,
            type=HeartLedgerType.INITIAL_GRANT,
        ))
        await session.commit()

    async with migrated_db() as session:
        session.add(HeartLedger(
            from_user_id=None, to_user_id=user_id, amount=5,
            type=HeartLedgerType.INITIAL_GRANT,
        ))
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_downgrade_drops_all_tables(clean_db):
    """alembic downgrade base removes all tables + enum types."""
    run_alembic("upgrade", "head")
    run_alembic("downgrade", "base")

    tables = await _table_names(clean_db)
    # alembic_version may stay (depends on alembic version) — everything else must be gone
    lingering = (tables - {"alembic_version"}) & EXPECTED_TABLES
    assert not lingering, f"Tables still exist after downgrade: {lingering}"

    enums = await _enum_names(clean_db)
    lingering_enums = EXPECTED_ENUMS & enums
    assert not lingering_enums, f"Enum types still exist after downgrade: {lingering_enums}"


async def test_upgrade_downgrade_cycle(clean_db):
    """upgrade → downgrade → upgrade must be idempotent (enum types recreate cleanly)."""
    run_alembic("upgrade", "head")
    run_alembic("downgrade", "base")
    run_alembic("upgrade", "head")

    tables = await _table_names(clean_db)
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Tables missing after re-upgrade: {missing}"
