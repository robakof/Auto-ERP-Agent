"""Unit tests for scheduler_service.expire_requests_job — async SQLite in-memory DB."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.location import Location, LocationType
from app.db.models.message import Message
from app.db.models.notification import Notification, NotificationType
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.user import User
from app.services import scheduler_service


# ---- Fixtures ----------------------------------------------------------------

@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(eng.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    tables = [
        User.__table__,
        Category.__table__,
        Location.__table__,
        Request.__table__,
        Exchange.__table__,
        Message.__table__,
        Notification.__table__,
    ]
    async with eng.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
        await conn.execute(text("DROP INDEX IF EXISTS uix_exchange_request_accepted"))

    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db(session_factory):
    async with session_factory() as session:
        yield session


async def _create_user(db: AsyncSession, **kwargs) -> User:
    defaults = {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "username": f"user_{uuid4().hex[:8]}",
        "password_hash": "$2b$12$fakehash",
        "heart_balance": 20,
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    await db.flush()
    return user


async def _create_category(db: AsyncSession) -> Category:
    cat = Category(name=f"cat_{uuid4().hex[:6]}")
    db.add(cat)
    await db.flush()
    return cat


async def _create_location(db: AsyncSession) -> Location:
    loc = Location(name="Warszawa", type=LocationType.CITY)
    db.add(loc)
    await db.flush()
    return loc


async def _create_request(
    db: AsyncSession, user_id, category_id: int, location_id: int,
    *, status=RequestStatus.OPEN, expires_at=None,
) -> Request:
    req = Request(
        user_id=user_id,
        title="Test request",
        description="desc",
        hearts_offered=3,
        category_id=category_id,
        location_id=location_id,
        location_scope=LocationScope.CITY,
        status=status,
        expires_at=expires_at,
    )
    db.add(req)
    await db.flush()
    return req


# ---- Tests -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expire_open_request_past_expiry(db, session_factory):
    """OPEN request with expires_at in the past → CANCELLED + notification."""
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    req = await _create_request(db, user.id, cat.id, loc.id, expires_at=past)
    await db.commit()

    with patch.object(scheduler_service, "async_session_factory", session_factory):
        count = await scheduler_service.expire_requests_job()

    assert count == 1

    async with session_factory() as check_db:
        updated = await check_db.get(Request, req.id)
        assert updated.status == RequestStatus.CANCELLED

        notifs = (await check_db.execute(
            select(Notification).where(
                Notification.user_id == user.id,
                Notification.type == NotificationType.REQUEST_EXPIRED,
            )
        )).scalars().all()
        assert len(notifs) == 1


@pytest.mark.asyncio
async def test_no_expire_open_request_future(db, session_factory):
    """OPEN request with expires_at in the future → no change."""
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    future = datetime.now(timezone.utc) + timedelta(days=7)
    req = await _create_request(db, user.id, cat.id, loc.id, expires_at=future)
    await db.commit()

    with patch.object(scheduler_service, "async_session_factory", session_factory):
        count = await scheduler_service.expire_requests_job()

    assert count == 0

    async with session_factory() as check_db:
        updated = await check_db.get(Request, req.id)
        assert updated.status == RequestStatus.OPEN


@pytest.mark.asyncio
async def test_no_expire_cancelled_request(db, session_factory):
    """Already CANCELLED request with past expires_at → no change (idempotency)."""
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    req = await _create_request(
        db, user.id, cat.id, loc.id, status=RequestStatus.CANCELLED, expires_at=past,
    )
    await db.commit()

    with patch.object(scheduler_service, "async_session_factory", session_factory):
        count = await scheduler_service.expire_requests_job()

    assert count == 0


@pytest.mark.asyncio
async def test_cascade_pending_exchanges(db, session_factory):
    """OPEN request + PENDING Exchange → both CANCELLED after job."""
    user = await _create_user(db)
    helper = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    req = await _create_request(db, user.id, cat.id, loc.id, expires_at=past)

    exchange = Exchange(
        request_id=req.id,
        requester_id=user.id,
        helper_id=helper.id,
        initiated_by=helper.id,
        hearts_agreed=3,
        status=ExchangeStatus.PENDING,
    )
    db.add(exchange)
    await db.flush()
    await db.commit()

    with patch.object(scheduler_service, "async_session_factory", session_factory):
        count = await scheduler_service.expire_requests_job()

    assert count == 1

    async with session_factory() as check_db:
        updated_req = await check_db.get(Request, req.id)
        assert updated_req.status == RequestStatus.CANCELLED

        updated_ex = await check_db.get(Exchange, exchange.id)
        assert updated_ex.status == ExchangeStatus.CANCELLED


@pytest.mark.asyncio
async def test_no_double_cancel(db, session_factory):
    """Two consecutive job runs → second = NOP (0 changes)."""
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    await _create_request(db, user.id, cat.id, loc.id, expires_at=past)
    await db.commit()

    with patch.object(scheduler_service, "async_session_factory", session_factory):
        count1 = await scheduler_service.expire_requests_job()
        count2 = await scheduler_service.expire_requests_job()

    assert count1 == 1
    assert count2 == 0


@pytest.mark.asyncio
async def test_email_sent_on_expire(db, session_factory):
    """After expire → email service receives notification call."""
    user = await _create_user(db, email="expire_test@example.com")
    cat = await _create_category(db)
    loc = await _create_location(db)
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    await _create_request(db, user.id, cat.id, loc.id, expires_at=past)
    await db.commit()

    mock_email = AsyncMock()
    with (
        patch.object(scheduler_service, "async_session_factory", session_factory),
        patch.object(scheduler_service, "get_email_service", return_value=mock_email),
    ):
        count = await scheduler_service.expire_requests_job()

    assert count == 1
    mock_email.send_notification.assert_called_once_with(
        "expire_test@example.com", "REQUEST_EXPIRED", None,
    )
