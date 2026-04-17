"""Unit tests for request_service — async SQLite in-memory DB."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.location import Location, LocationType
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.user import User, UserStatus
from app.services import request_service


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
        User.__table__,
        Category.__table__,
        Location.__table__,
        Request.__table__,
        Exchange.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
        # Drop partial unique index — SQLite doesn't support postgresql_where
        await conn.execute(text("DROP INDEX IF EXISTS uix_exchange_request_accepted"))

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


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


async def _create_category(db: AsyncSession, **kwargs) -> Category:
    defaults = {"name": "Pomoc domowa", "active": True}
    defaults.update(kwargs)
    cat = Category(**defaults)
    db.add(cat)
    await db.flush()
    return cat


async def _create_location(db: AsyncSession, **kwargs) -> Location:
    defaults = {"name": "Warszawa", "type": LocationType.CITY}
    defaults.update(kwargs)
    loc = Location(**defaults)
    db.add(loc)
    await db.flush()
    return loc


async def _create_request_fixture(db, user, cat, loc, **kwargs):
    return await request_service.create_request(
        db, user.id,
        title=kwargs.get("title", "Potrzebuję pomocy"),
        description=kwargs.get("description", "Opis mojej prośby o pomoc jest tutaj"),
        hearts_offered=kwargs.get("hearts_offered", 5),
        category_id=cat.id,
        location_id=loc.id,
        location_scope=kwargs.get("location_scope", LocationScope.CITY),
        expires_at=kwargs.get("expires_at", None),
    )


# ---- create_request: happy path ----------------------------------------------

@pytest.mark.asyncio
async def test_create_request_valid(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    assert req.title == "Potrzebuję pomocy"
    assert req.status == RequestStatus.OPEN
    assert req.hearts_offered == 5


@pytest.mark.asyncio
async def test_create_request_default_expires(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    assert req.expires_at is not None
    # Should be ~30 days from now
    delta = req.expires_at - datetime.now(timezone.utc)
    assert 29 <= delta.days <= 30


@pytest.mark.asyncio
async def test_create_request_custom_expires(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    future = datetime.now(timezone.utc) + timedelta(days=7)
    req = await _create_request_fixture(db, user, cat, loc, expires_at=future)
    assert abs((req.expires_at - future).total_seconds()) < 2


# ---- create_request: guards --------------------------------------------------

@pytest.mark.asyncio
async def test_create_category_not_found(db):
    user = await _create_user(db)
    loc = await _create_location(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.create_request(
            db, user.id, title="Test", description="A long enough description",
            hearts_offered=0, category_id=9999, location_id=loc.id,
            location_scope=LocationScope.CITY, expires_at=None,
        )
    assert exc_info.value.detail == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_category_inactive(db):
    user = await _create_user(db)
    cat = await _create_category(db, active=False)
    loc = await _create_location(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.create_request(
            db, user.id, title="Test", description="A long enough description",
            hearts_offered=0, category_id=cat.id, location_id=loc.id,
            location_scope=LocationScope.CITY, expires_at=None,
        )
    assert exc_info.value.detail == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_location_not_found(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.create_request(
            db, user.id, title="Test", description="A long enough description",
            hearts_offered=0, category_id=cat.id, location_id=9999,
            location_scope=LocationScope.CITY, expires_at=None,
        )
    assert exc_info.value.detail == "LOCATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_expires_in_past(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await _create_request_fixture(db, user, cat, loc, expires_at=past)
    assert exc_info.value.detail == "EXPIRES_IN_PAST"


# ---- get_request -------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_request_valid(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    result = await request_service.get_request(db, req.id, user.id)
    assert result.id == req.id


@pytest.mark.asyncio
async def test_get_request_not_found(db):
    user = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.get_request(db, uuid4(), user.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_hidden_request_by_non_owner(db):
    owner = await _create_user(db)
    other = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, owner, cat, loc)
    req.status = RequestStatus.HIDDEN
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.get_request(db, req.id, other.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_hidden_request_by_owner(db):
    owner = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, owner, cat, loc)
    req.status = RequestStatus.HIDDEN
    await db.flush()
    result = await request_service.get_request(db, req.id, owner.id)
    assert result.id == req.id


# ---- update_request: happy path ----------------------------------------------

@pytest.mark.asyncio
async def test_update_title_only(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    updated = await request_service.update_request(db, req.id, user.id, title="Nowy tytuł")
    assert updated.title == "Nowy tytuł"
    assert updated.description == req.description  # unchanged


@pytest.mark.asyncio
async def test_update_hearts_offered(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc, hearts_offered=3)
    updated = await request_service.update_request(db, req.id, user.id, hearts_offered=10)
    assert updated.hearts_offered == 10


# ---- update_request: guards --------------------------------------------------

@pytest.mark.asyncio
async def test_update_not_owner(db):
    user = await _create_user(db)
    other = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.update_request(db, req.id, other.id, title="Hack")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_not_open(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    req.status = RequestStatus.CANCELLED
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.update_request(db, req.id, user.id, title="X")
    assert exc_info.value.detail == "REQUEST_NOT_EDITABLE"


@pytest.mark.asyncio
async def test_update_hearts_locked(db):
    user = await _create_user(db)
    helper = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    # Create a PENDING exchange
    exchange = Exchange(
        request_id=req.id,
        requester_id=user.id,
        helper_id=helper.id,
        initiated_by=helper.id,
        hearts_agreed=5,
        status=ExchangeStatus.PENDING,
    )
    db.add(exchange)
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.update_request(db, req.id, user.id, hearts_offered=10)
    assert exc_info.value.detail == "HEARTS_OFFERED_LOCKED"


# ---- list_requests -----------------------------------------------------------

@pytest.mark.asyncio
async def test_list_default_open(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_request_fixture(db, user, cat, loc, title="Open request")
    req2 = await _create_request_fixture(db, user, cat, loc, title="Cancelled one")
    req2.status = RequestStatus.CANCELLED
    await db.flush()

    entries, total = await request_service.list_requests(db)
    assert total == 1
    assert entries[0].title == "Open request"


@pytest.mark.asyncio
async def test_list_search_ilike(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_request_fixture(db, user, cat, loc, title="Szukam pomocy z psem")
    await _create_request_fixture(db, user, cat, loc, title="Potrzebuję korepetycji")

    entries, total = await request_service.list_requests(db, q="psem")
    assert total == 1
    assert "psem" in entries[0].title


@pytest.mark.asyncio
async def test_list_filter_category(db):
    user = await _create_user(db)
    cat1 = await _create_category(db, name="Cat A")
    cat2 = await _create_category(db, name="Cat B")
    loc = await _create_location(db)
    await _create_request_fixture(db, user, cat1, loc)
    await _create_request_fixture(db, user, cat2, loc)

    entries, total = await request_service.list_requests(db, category_id=cat1.id)
    assert total == 1


@pytest.mark.asyncio
async def test_list_filter_location_scope(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_request_fixture(db, user, cat, loc, location_scope=LocationScope.CITY)
    await _create_request_fixture(db, user, cat, loc, location_scope=LocationScope.NATIONAL)

    entries, total = await request_service.list_requests(db, location_scope=LocationScope.NATIONAL)
    assert total == 1


@pytest.mark.asyncio
async def test_list_pagination(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    for i in range(5):
        await _create_request_fixture(db, user, cat, loc, title=f"Request numer {i}")

    entries, total = await request_service.list_requests(db, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2


@pytest.mark.asyncio
async def test_list_sort_hearts_desc(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_request_fixture(db, user, cat, loc, hearts_offered=1)
    await _create_request_fixture(db, user, cat, loc, hearts_offered=10)
    await _create_request_fixture(db, user, cat, loc, hearts_offered=5)

    entries, total = await request_service.list_requests(db, sort="hearts_offered", order="desc")
    assert entries[0].hearts_offered == 10
    assert entries[1].hearts_offered == 5
    assert entries[2].hearts_offered == 1


@pytest.mark.asyncio
async def test_list_excludes_suspended_users(db):
    active_user = await _create_user(db)
    suspended_user = await _create_user(db, status=UserStatus.SUSPENDED)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_request_fixture(db, active_user, cat, loc, title="Active req")
    await _create_request_fixture(db, suspended_user, cat, loc, title="Suspended req")

    entries, total = await request_service.list_requests(db)
    assert total == 1
    assert entries[0].title == "Active req"


# ---- cancel_request ----------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_request_valid(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    result = await request_service.cancel_request(db, req.id, user.id)
    assert result.status == RequestStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_not_owner(db):
    user = await _create_user(db)
    other = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.cancel_request(db, req.id, other.id)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cancel_not_open(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    req.status = RequestStatus.DONE
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await request_service.cancel_request(db, req.id, user.id)
    assert exc_info.value.detail == "REQUEST_NOT_CANCELLABLE"


@pytest.mark.asyncio
async def test_cancel_cascades_pending_exchanges(db):
    user = await _create_user(db)
    helper = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    exchange = Exchange(
        request_id=req.id, requester_id=user.id, helper_id=helper.id,
        initiated_by=helper.id, hearts_agreed=5, status=ExchangeStatus.PENDING,
    )
    db.add(exchange)
    await db.flush()

    await request_service.cancel_request(db, req.id, user.id)
    await db.refresh(exchange)
    assert exchange.status == ExchangeStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_ignores_non_pending_exchanges(db):
    user = await _create_user(db)
    helper = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    req = await _create_request_fixture(db, user, cat, loc)
    exchange = Exchange(
        request_id=req.id, requester_id=user.id, helper_id=helper.id,
        initiated_by=helper.id, hearts_agreed=5, status=ExchangeStatus.ACCEPTED,
    )
    db.add(exchange)
    await db.flush()

    # Need to set request to OPEN (it is by default)
    # But cancel only works on OPEN — and we have ACCEPTED exchange
    # Plan says cancel only from OPEN. The exchange being ACCEPTED doesn't prevent cancel.
    await request_service.cancel_request(db, req.id, user.id)
    await db.refresh(exchange)
    assert exchange.status == ExchangeStatus.ACCEPTED  # untouched
