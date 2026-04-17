"""Unit tests for user_resources_service — async SQLite in-memory DB."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.heart import HeartLedger
from app.db.models.location import Location, LocationType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.review import Review
from app.db.models.user import User, UserStatus
from app.services import user_resources_service


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
        User.__table__, Category.__table__, Location.__table__,
        Request.__table__, Offer.__table__, Exchange.__table__,
        HeartLedger.__table__, Review.__table__,
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
        "heart_balance": 10,
    }
    defaults.update(kw)
    u = User(**defaults)
    db.add(u)
    await db.flush()
    return u


async def _cat_loc(db) -> tuple[Category, Location]:
    cat = Category(name="Help", active=True)
    db.add(cat)
    await db.flush()
    loc = Location(name="Wro", type=LocationType.CITY)
    db.add(loc)
    await db.flush()
    return cat, loc


async def _request(db, user, cat, loc, **kw) -> Request:
    r = Request(
        user_id=user.id, title="Need help", description="Please help me",
        hearts_offered=0, category_id=cat.id, location_id=loc.id,
        location_scope=LocationScope.CITY,
        status=kw.get("status", RequestStatus.OPEN),
    )
    db.add(r)
    await db.flush()
    return r


async def _offer(db, user, cat, loc, **kw) -> Offer:
    o = Offer(
        user_id=user.id, title="Can help", description="I can help you out",
        hearts_asked=0, category_id=cat.id, location_id=loc.id,
        location_scope=LocationScope.CITY,
        status=kw.get("status", OfferStatus.ACTIVE),
    )
    db.add(o)
    await db.flush()
    return o


async def _exchange(db, requester, helper, *, status=ExchangeStatus.PENDING) -> Exchange:
    cat, loc = await _cat_loc(db)
    # Use CANCELLED request to avoid polluting request count tests
    req = await _request(db, requester, cat, loc, status=RequestStatus.CANCELLED)
    ex = Exchange(
        request_id=req.id, requester_id=requester.id, helper_id=helper.id,
        initiated_by=helper.id, hearts_agreed=0, status=status,
    )
    db.add(ex)
    await db.flush()
    return ex


async def _review(db, exchange, reviewer_id, reviewed_id) -> Review:
    r = Review(
        exchange_id=exchange.id, reviewer_id=reviewer_id,
        reviewed_id=reviewed_id, comment="Good experience overall",
    )
    db.add(r)
    await db.flush()
    return r


# ---- my_requests -------------------------------------------------------------

@pytest.mark.asyncio
async def test_my_requests_all(db):
    user = await _user(db)
    cat, loc = await _cat_loc(db)
    await _request(db, user, cat, loc, status=RequestStatus.OPEN)
    await _request(db, user, cat, loc, status=RequestStatus.CANCELLED)
    entries, total = await user_resources_service.my_requests(db, user.id)
    assert total == 2


@pytest.mark.asyncio
async def test_my_requests_filter_status(db):
    user = await _user(db)
    cat, loc = await _cat_loc(db)
    await _request(db, user, cat, loc, status=RequestStatus.OPEN)
    await _request(db, user, cat, loc, status=RequestStatus.CANCELLED)
    entries, total = await user_resources_service.my_requests(db, user.id, status=RequestStatus.OPEN)
    assert total == 1


@pytest.mark.asyncio
async def test_my_requests_empty(db):
    user = await _user(db)
    entries, total = await user_resources_service.my_requests(db, user.id)
    assert total == 0
    assert entries == []


@pytest.mark.asyncio
async def test_my_requests_pagination(db):
    user = await _user(db)
    cat, loc = await _cat_loc(db)
    for _ in range(5):
        await _request(db, user, cat, loc)
    entries, total = await user_resources_service.my_requests(db, user.id, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2


# ---- my_offers ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_my_offers_all(db):
    user = await _user(db)
    cat, loc = await _cat_loc(db)
    await _offer(db, user, cat, loc, status=OfferStatus.ACTIVE)
    await _offer(db, user, cat, loc, status=OfferStatus.PAUSED)
    await _offer(db, user, cat, loc, status=OfferStatus.INACTIVE)
    entries, total = await user_resources_service.my_offers(db, user.id)
    assert total == 3


@pytest.mark.asyncio
async def test_my_offers_filter_status(db):
    user = await _user(db)
    cat, loc = await _cat_loc(db)
    await _offer(db, user, cat, loc, status=OfferStatus.ACTIVE)
    await _offer(db, user, cat, loc, status=OfferStatus.PAUSED)
    entries, total = await user_resources_service.my_offers(db, user.id, status=OfferStatus.ACTIVE)
    assert total == 1


# ---- my_reviews --------------------------------------------------------------

@pytest.mark.asyncio
async def test_my_reviews_received(db):
    user = await _user(db)
    other = await _user(db)
    ex = await _exchange(db, user, other, status=ExchangeStatus.COMPLETED)
    await _review(db, ex, reviewer_id=other.id, reviewed_id=user.id)
    entries, total = await user_resources_service.my_reviews(db, user.id)
    assert total == 1
    assert entries[0].reviewed_id == user.id


@pytest.mark.asyncio
async def test_my_reviews_given(db):
    user = await _user(db)
    other = await _user(db)
    ex = await _exchange(db, user, other, status=ExchangeStatus.COMPLETED)
    await _review(db, ex, reviewer_id=user.id, reviewed_id=other.id)
    entries, total = await user_resources_service.my_reviews(db, user.id, review_type="given")
    assert total == 1
    assert entries[0].reviewer_id == user.id


@pytest.mark.asyncio
async def test_my_reviews_empty(db):
    user = await _user(db)
    entries, total = await user_resources_service.my_reviews(db, user.id)
    assert total == 0
    assert entries == []


# ---- user_summary ------------------------------------------------------------

@pytest.mark.asyncio
async def test_summary_empty_user(db):
    user = await _user(db, heart_balance=0)
    summary = await user_resources_service.user_summary(db, user.id)
    assert summary["active_requests"] == 0
    assert summary["active_offers"] == 0
    assert summary["pending_exchanges"] == 0
    assert summary["completed_exchanges"] == 0
    assert summary["heart_balance"] == 0
    assert summary["reviews_received"] == 0


@pytest.mark.asyncio
async def test_summary_with_data(db):
    user = await _user(db, heart_balance=15)
    other = await _user(db)
    cat, loc = await _cat_loc(db)

    # 2 OPEN requests
    await _request(db, user, cat, loc, status=RequestStatus.OPEN)
    await _request(db, user, cat, loc, status=RequestStatus.OPEN)
    # 1 CANCELLED request (should NOT count)
    await _request(db, user, cat, loc, status=RequestStatus.CANCELLED)

    # 1 ACTIVE offer
    await _offer(db, user, cat, loc, status=OfferStatus.ACTIVE)
    # 1 PAUSED offer (should NOT count)
    await _offer(db, user, cat, loc, status=OfferStatus.PAUSED)

    # 1 PENDING exchange
    await _exchange(db, user, other, status=ExchangeStatus.PENDING)
    # 1 COMPLETED exchange
    ex_completed = await _exchange(db, user, other, status=ExchangeStatus.COMPLETED)

    # 1 review received
    await _review(db, ex_completed, reviewer_id=other.id, reviewed_id=user.id)

    summary = await user_resources_service.user_summary(db, user.id)
    assert summary["active_requests"] == 2
    assert summary["active_offers"] == 1
    assert summary["pending_exchanges"] == 1
    assert summary["completed_exchanges"] == 1
    assert summary["heart_balance"] == 15
    assert summary["reviews_received"] == 1


# ---- public_profile ----------------------------------------------------------

@pytest.mark.asyncio
async def test_public_profile_valid(db):
    user = await _user(db, heart_balance=10)
    other = await _user(db)
    ex = await _exchange(db, user, other, status=ExchangeStatus.COMPLETED)
    await _review(db, ex, reviewer_id=other.id, reviewed_id=user.id)

    profile = await user_resources_service.public_profile(db, user.id)
    assert profile["username"] == user.username
    assert profile["heart_balance"] == 10
    assert profile["reviews_received"] == 1
    assert profile["completed_exchanges"] == 1
    # No email/phone/role exposed
    assert "email" not in profile
    assert "phone_number" not in profile
    assert "role" not in profile


@pytest.mark.asyncio
async def test_public_profile_not_found(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await user_resources_service.public_profile(db, uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_public_profile_suspended_hidden(db):
    user = await _user(db, status=UserStatus.SUSPENDED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await user_resources_service.public_profile(db, user.id)
    assert exc.value.status_code == 404
