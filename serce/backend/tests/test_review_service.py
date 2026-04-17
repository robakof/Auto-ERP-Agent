"""Unit tests for review_service — async SQLite in-memory DB."""
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
from app.db.models.offer import Offer
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.notification import Notification
from app.db.models.review import Review
from app.db.models.user import User
from app.services import review_service


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
        HeartLedger.__table__, Review.__table__, Notification.__table__,
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


async def _completed_exchange(db, requester, helper) -> Exchange:
    cat = Category(name="Help", active=True)
    db.add(cat)
    await db.flush()
    loc = Location(name="Wro", type=LocationType.CITY)
    db.add(loc)
    await db.flush()
    req = Request(
        user_id=requester.id, title="Need help", description="Please help me",
        hearts_offered=0, category_id=cat.id, location_id=loc.id,
        location_scope=LocationScope.CITY, status=RequestStatus.OPEN,
    )
    db.add(req)
    await db.flush()
    ex = Exchange(
        request_id=req.id, requester_id=requester.id, helper_id=helper.id,
        initiated_by=helper.id, hearts_agreed=0, status=ExchangeStatus.COMPLETED,
    )
    db.add(ex)
    await db.flush()
    return ex


# ---- create_review -----------------------------------------------------------

@pytest.mark.asyncio
async def test_create_review_as_requester(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _completed_exchange(db, requester, helper)
    review = await review_service.create_review(db, ex.id, requester.id, comment="Great helper!")
    assert review.reviewer_id == requester.id
    assert review.reviewed_id == helper.id
    assert review.comment == "Great helper!"


@pytest.mark.asyncio
async def test_create_review_as_helper(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _completed_exchange(db, requester, helper)
    review = await review_service.create_review(db, ex.id, helper.id, comment="Nice requester, very polite")
    assert review.reviewer_id == helper.id
    assert review.reviewed_id == requester.id


@pytest.mark.asyncio
async def test_create_exchange_not_completed(db):
    requester = await _user(db)
    helper = await _user(db)
    cat = Category(name="Help", active=True)
    db.add(cat)
    await db.flush()
    loc = Location(name="Wro", type=LocationType.CITY)
    db.add(loc)
    await db.flush()
    req = Request(
        user_id=requester.id, title="Need help", description="Please help me",
        hearts_offered=0, category_id=cat.id, location_id=loc.id,
        location_scope=LocationScope.CITY, status=RequestStatus.OPEN,
    )
    db.add(req)
    await db.flush()
    ex = Exchange(
        request_id=req.id, requester_id=requester.id, helper_id=helper.id,
        initiated_by=helper.id, hearts_agreed=0, status=ExchangeStatus.PENDING,
    )
    db.add(ex)
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(db, ex.id, requester.id, comment="Too early to review!")
    assert exc.value.detail == "EXCHANGE_NOT_COMPLETED"


@pytest.mark.asyncio
async def test_create_not_participant(db):
    requester = await _user(db)
    helper = await _user(db)
    outsider = await _user(db)
    ex = await _completed_exchange(db, requester, helper)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(db, ex.id, outsider.id, comment="I want to review too!")
    assert exc.value.detail == "NOT_PARTICIPANT"


@pytest.mark.asyncio
async def test_create_duplicate_review(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _completed_exchange(db, requester, helper)
    await review_service.create_review(db, ex.id, requester.id, comment="First review here")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(db, ex.id, requester.id, comment="Second attempt review")
    assert exc.value.detail == "REVIEW_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_exchange_not_found(db):
    user = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await review_service.create_review(db, uuid4(), user.id, comment="Review for nothing")
    assert exc.value.detail == "EXCHANGE_NOT_FOUND"


# ---- list_reviews_for_exchange -----------------------------------------------

@pytest.mark.asyncio
async def test_list_reviews_for_exchange(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _completed_exchange(db, requester, helper)
    await review_service.create_review(db, ex.id, requester.id, comment="Great helper person")
    await review_service.create_review(db, ex.id, helper.id, comment="Nice requester person")
    reviews = await review_service.list_reviews_for_exchange(db, ex.id, requester.id)
    assert len(reviews) == 2


@pytest.mark.asyncio
async def test_list_reviews_not_participant(db):
    requester = await _user(db)
    helper = await _user(db)
    outsider = await _user(db)
    ex = await _completed_exchange(db, requester, helper)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await review_service.list_reviews_for_exchange(db, ex.id, outsider.id)
    assert exc.value.detail == "NOT_PARTICIPANT"


# ---- list_reviews_for_user ---------------------------------------------------

@pytest.mark.asyncio
async def test_list_reviews_for_user(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _completed_exchange(db, requester, helper)
    await review_service.create_review(db, ex.id, requester.id, comment="Excellent helper work")
    entries, total = await review_service.list_reviews_for_user(db, helper.id)
    assert total == 1
    assert entries[0].reviewed_id == helper.id


@pytest.mark.asyncio
async def test_list_reviews_user_not_found(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await review_service.list_reviews_for_user(db, uuid4())
    assert exc.value.detail == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_reviews_empty(db):
    user = await _user(db)
    entries, total = await review_service.list_reviews_for_user(db, user.id)
    assert total == 0
    assert entries == []


@pytest.mark.asyncio
async def test_list_reviews_pagination(db):
    reviewed_user = await _user(db)
    for _ in range(5):
        reviewer = await _user(db)
        ex = await _completed_exchange(db, reviewer, reviewed_user)
        await review_service.create_review(db, ex.id, reviewer.id, comment="Good user to work with")
    entries, total = await review_service.list_reviews_for_user(db, reviewed_user.id, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2
