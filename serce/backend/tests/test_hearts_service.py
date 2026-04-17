"""Unit tests for hearts_service — async SQLite in-memory DB."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy import text

from app.db.base import Base
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.user import User, UserStatus
from app.services import hearts_service


# ---- Fixtures ----------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    tables = [User.__table__, HeartLedger.__table__]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
        # Drop partial unique index — SQLite doesn't support postgresql_where,
        # so it creates a plain unique index on to_user_id blocking multiple gifts.
        await conn.execute(text("DROP INDEX IF EXISTS uix_heart_ledger_initial_grant"))

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _create_user(db: AsyncSession, **kwargs) -> User:
    defaults = {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "username": f"user_{uuid4().hex[:8]}",
        "password_hash": "$2b$12$fakehashfakehashfakehashfakehashfakehashfakehashfake",
        "heart_balance": 10,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    await db.flush()
    return user


# ---- gift_hearts: happy path -------------------------------------------------

@pytest.mark.asyncio
async def test_gift_hearts_valid(db):
    sender = await _create_user(db, heart_balance=10)
    recipient = await _create_user(db, heart_balance=0)
    ledger = await hearts_service.gift_hearts(db, sender.id, recipient.id, 5, "thanks")
    assert ledger.amount == 5
    assert ledger.type == HeartLedgerType.GIFT
    assert ledger.note == "thanks"


@pytest.mark.asyncio
async def test_gift_hearts_updates_both_balances(db):
    sender = await _create_user(db, heart_balance=10)
    recipient = await _create_user(db, heart_balance=3)
    await hearts_service.gift_hearts(db, sender.id, recipient.id, 4, None)
    await db.refresh(sender)
    await db.refresh(recipient)
    assert sender.heart_balance == 6
    assert recipient.heart_balance == 7


@pytest.mark.asyncio
async def test_gift_hearts_creates_ledger_entry(db):
    sender = await _create_user(db, heart_balance=10)
    recipient = await _create_user(db, heart_balance=0)
    ledger = await hearts_service.gift_hearts(db, sender.id, recipient.id, 2, "note")
    assert ledger.from_user_id == sender.id
    assert ledger.to_user_id == recipient.id


# ---- gift_hearts: guards -----------------------------------------------------

@pytest.mark.asyncio
async def test_gift_self_rejected(db):
    user = await _create_user(db, heart_balance=10)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.gift_hearts(db, user.id, user.id, 1, None)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "CANNOT_GIFT_SELF"


@pytest.mark.asyncio
async def test_gift_insufficient_balance(db):
    sender = await _create_user(db, heart_balance=3)
    recipient = await _create_user(db, heart_balance=0)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.gift_hearts(db, sender.id, recipient.id, 5, None)
    assert exc_info.value.detail == "INSUFFICIENT_BALANCE"


@pytest.mark.asyncio
async def test_gift_recipient_cap_exceeded(db):
    sender = await _create_user(db, heart_balance=10)
    recipient = await _create_user(db, heart_balance=49)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.gift_hearts(db, sender.id, recipient.id, 2, None)
    assert exc_info.value.detail == "RECIPIENT_CAP_EXCEEDED"


@pytest.mark.asyncio
async def test_gift_recipient_not_active(db):
    sender = await _create_user(db, heart_balance=10)
    recipient = await _create_user(db, heart_balance=0, status=UserStatus.SUSPENDED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.gift_hearts(db, sender.id, recipient.id, 1, None)
    assert exc_info.value.detail == "RECIPIENT_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_gift_sender_not_found(db):
    recipient = await _create_user(db, heart_balance=0)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.gift_hearts(db, uuid4(), recipient.id, 1, None)
    assert exc_info.value.detail == "SENDER_NOT_FOUND"


@pytest.mark.asyncio
async def test_gift_recipient_not_found(db):
    sender = await _create_user(db, heart_balance=10)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.gift_hearts(db, sender.id, uuid4(), 1, None)
    assert exc_info.value.detail == "RECIPIENT_NOT_FOUND"


# ---- gift_hearts: edge cases -------------------------------------------------

@pytest.mark.asyncio
async def test_gift_exact_balance_succeeds(db):
    sender = await _create_user(db, heart_balance=5)
    recipient = await _create_user(db, heart_balance=0)
    await hearts_service.gift_hearts(db, sender.id, recipient.id, 5, None)
    await db.refresh(sender)
    assert sender.heart_balance == 0


@pytest.mark.asyncio
async def test_gift_cap_exact_succeeds(db):
    sender = await _create_user(db, heart_balance=10)
    recipient = await _create_user(db, heart_balance=49)
    await hearts_service.gift_hearts(db, sender.id, recipient.id, 1, None)
    await db.refresh(recipient)
    assert recipient.heart_balance == 50


@pytest.mark.asyncio
async def test_gift_cap_over_rejected(db):
    sender = await _create_user(db, heart_balance=10)
    recipient = await _create_user(db, heart_balance=49)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.gift_hearts(db, sender.id, recipient.id, 2, None)
    assert exc_info.value.detail == "RECIPIENT_CAP_EXCEEDED"


# ---- get_balance -------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_balance(db):
    user = await _create_user(db, heart_balance=42)
    balance = await hearts_service.get_balance(db, user.id)
    assert balance == 42


@pytest.mark.asyncio
async def test_get_balance_user_not_found(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await hearts_service.get_balance(db, uuid4())
    assert exc_info.value.status_code == 404


# ---- get_ledger --------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_ledger_empty(db):
    user = await _create_user(db)
    entries, total = await hearts_service.get_ledger(db, user.id)
    assert entries == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_ledger_with_entries(db):
    sender = await _create_user(db, heart_balance=20)
    recipient = await _create_user(db, heart_balance=0)
    await hearts_service.gift_hearts(db, sender.id, recipient.id, 3, "first")
    await hearts_service.gift_hearts(db, sender.id, recipient.id, 2, "second")

    entries, total = await hearts_service.get_ledger(db, sender.id)
    assert total == 2
    assert len(entries) == 2
    notes = {e.note for e in entries}
    assert notes == {"first", "second"}


@pytest.mark.asyncio
async def test_get_ledger_pagination(db):
    sender = await _create_user(db, heart_balance=50)
    recipient = await _create_user(db, heart_balance=0)
    for i in range(5):
        await hearts_service.gift_hearts(db, sender.id, recipient.id, 1, f"gift_{i}")

    entries, total = await hearts_service.get_ledger(db, sender.id, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2


@pytest.mark.asyncio
async def test_get_ledger_type_filter(db):
    sender = await _create_user(db, heart_balance=20)
    recipient = await _create_user(db, heart_balance=0)
    await hearts_service.gift_hearts(db, sender.id, recipient.id, 3, None)

    # Add a manual INITIAL_GRANT entry for testing filter
    manual = HeartLedger(
        to_user_id=sender.id,
        amount=5,
        type=HeartLedgerType.INITIAL_GRANT,
    )
    db.add(manual)
    await db.flush()

    entries, total = await hearts_service.get_ledger(
        db, sender.id, type_filter=HeartLedgerType.GIFT,
    )
    assert total == 1
    assert entries[0].type == HeartLedgerType.GIFT


@pytest.mark.asyncio
async def test_get_ledger_includes_sent_and_received(db):
    user_a = await _create_user(db, heart_balance=20)
    user_b = await _create_user(db, heart_balance=20)
    await hearts_service.gift_hearts(db, user_a.id, user_b.id, 3, "a->b")
    await hearts_service.gift_hearts(db, user_b.id, user_a.id, 1, "b->a")

    entries, total = await hearts_service.get_ledger(db, user_a.id)
    assert total == 2  # both sent and received
