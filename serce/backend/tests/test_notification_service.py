"""Unit tests for notification_service — async SQLite in-memory DB."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.exchange import Exchange
from app.db.models.message import Message
from app.db.models.notification import Notification, NotificationType
from app.db.models.user import User
from app.services import notification_service


# ---- Fixtures ----------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    tables = [
        User.__table__, Exchange.__table__, Message.__table__,
        Notification.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
        await conn.execute(text("DROP INDEX IF EXISTS uix_exchange_request_accepted"))
        await conn.execute(text("DROP INDEX IF EXISTS uix_heart_ledger_initial_grant"))

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _user(db, **kw) -> User:
    defaults = {
        "email": f"t_{uuid4().hex[:8]}@x.com",
        "username": f"u_{uuid4().hex[:8]}",
        "password_hash": "$2b$12$fakehash",
        "heart_balance": 0,
    }
    defaults.update(kw)
    u = User(**defaults)
    db.add(u)
    await db.flush()
    return u


# ---- create_notification -----------------------------------------------------

@pytest.mark.asyncio
async def test_create_notification(db):
    user = await _user(db)
    notif = await notification_service.create_notification(
        db, user.id, NotificationType.HEARTS_RECEIVED, reason="Gift from friend",
    )
    assert notif.user_id == user.id
    assert notif.type == NotificationType.HEARTS_RECEIVED
    assert notif.reason == "Gift from friend"
    assert notif.is_read is False


# ---- list_notifications ------------------------------------------------------

@pytest.mark.asyncio
async def test_list_notifications_empty(db):
    user = await _user(db)
    entries, total = await notification_service.list_notifications(db, user.id)
    assert total == 0
    assert entries == []


@pytest.mark.asyncio
async def test_list_notifications_paginated(db):
    user = await _user(db)
    for i in range(5):
        await notification_service.create_notification(
            db, user.id, NotificationType.NEW_MESSAGE, reason=f"msg {i}",
        )
    entries, total = await notification_service.list_notifications(db, user.id, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2


@pytest.mark.asyncio
async def test_list_notifications_unread_filter(db):
    user = await _user(db)
    n1 = await notification_service.create_notification(
        db, user.id, NotificationType.NEW_EXCHANGE,
    )
    await notification_service.create_notification(
        db, user.id, NotificationType.NEW_MESSAGE,
    )
    # Mark first as read
    await notification_service.mark_as_read(db, n1.id, user.id)

    entries, total = await notification_service.list_notifications(
        db, user.id, unread_only=True,
    )
    assert total == 1
    assert entries[0].type == NotificationType.NEW_MESSAGE


# ---- mark_as_read ------------------------------------------------------------

@pytest.mark.asyncio
async def test_mark_as_read(db):
    user = await _user(db)
    notif = await notification_service.create_notification(
        db, user.id, NotificationType.NEW_REVIEW,
    )
    result = await notification_service.mark_as_read(db, notif.id, user.id)
    assert result.is_read is True


@pytest.mark.asyncio
async def test_mark_as_read_not_found(db):
    user = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await notification_service.mark_as_read(db, uuid4(), user.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_as_read_wrong_user(db):
    owner = await _user(db)
    other = await _user(db)
    notif = await notification_service.create_notification(
        db, owner.id, NotificationType.NEW_EXCHANGE,
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await notification_service.mark_as_read(db, notif.id, other.id)
    assert exc.value.status_code == 404


# ---- mark_all_as_read -------------------------------------------------------

@pytest.mark.asyncio
async def test_mark_all_as_read(db):
    user = await _user(db)
    for _ in range(3):
        await notification_service.create_notification(
            db, user.id, NotificationType.HEARTS_RECEIVED,
        )
    count = await notification_service.mark_all_as_read(db, user.id)
    assert count == 3

    _, total_unread = await notification_service.list_notifications(
        db, user.id, unread_only=True,
    )
    assert total_unread == 0


# ---- unread_count ------------------------------------------------------------

@pytest.mark.asyncio
async def test_unread_count(db):
    user = await _user(db)
    await notification_service.create_notification(
        db, user.id, NotificationType.NEW_EXCHANGE,
    )
    await notification_service.create_notification(
        db, user.id, NotificationType.NEW_MESSAGE,
    )
    n3 = await notification_service.create_notification(
        db, user.id, NotificationType.NEW_REVIEW,
    )
    # Mark one as read
    await notification_service.mark_as_read(db, n3.id, user.id)

    count = await notification_service.unread_count(db, user.id)
    assert count == 2
