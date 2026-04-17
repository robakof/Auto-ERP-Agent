"""Unit tests for flag_service — async SQLite in-memory DB."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.admin import ContentFlag, FlagReason, FlagStatus, FlagTargetType
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.heart import HeartLedger
from app.db.models.location import Location, LocationType
from app.db.models.notification import Notification
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.user import User, UserStatus
from app.services import flag_service


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
        HeartLedger.__table__, Notification.__table__, ContentFlag.__table__,
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
        "status": UserStatus.ACTIVE,
    }
    defaults.update(kw)
    u = User(**defaults)
    db.add(u)
    await db.flush()
    return u


async def _request(db, user) -> Request:
    cat = Category(name="Help", active=True)
    db.add(cat)
    await db.flush()
    loc = Location(name="Wro", type=LocationType.CITY)
    db.add(loc)
    await db.flush()
    req = Request(
        user_id=user.id, title="Need help", description="Please help me",
        hearts_offered=0, category_id=cat.id, location_id=loc.id,
        location_scope=LocationScope.CITY, status=RequestStatus.OPEN,
    )
    db.add(req)
    await db.flush()
    return req


async def _offer(db, user) -> Offer:
    cat = Category(name="Offer", active=True)
    db.add(cat)
    await db.flush()
    loc = Location(name="Wro", type=LocationType.CITY)
    db.add(loc)
    await db.flush()
    offer = Offer(
        user_id=user.id, title="Can help", description="I can help you out",
        hearts_asked=0, category_id=cat.id, location_id=loc.id,
        location_scope=LocationScope.CITY, status=OfferStatus.ACTIVE,
    )
    db.add(offer)
    await db.flush()
    return offer


async def _exchange(db, requester, helper) -> Exchange:
    req = await _request(db, requester)
    ex = Exchange(
        request_id=req.id, requester_id=requester.id, helper_id=helper.id,
        initiated_by=helper.id, hearts_agreed=0, status=ExchangeStatus.PENDING,
    )
    db.add(ex)
    await db.flush()
    return ex


# ---- Create flag — valid cases -----------------------------------------------

@pytest.mark.asyncio
async def test_flag_request_valid(db):
    owner = await _user(db)
    reporter = await _user(db)
    req = await _request(db, owner)
    flag = await flag_service.create_flag(
        db, reporter.id, FlagTargetType.REQUEST, req.id,
        reason=FlagReason.SPAM,
    )
    assert flag.target_type == FlagTargetType.REQUEST
    assert flag.reporter_id == reporter.id
    assert flag.status == FlagStatus.OPEN


@pytest.mark.asyncio
async def test_flag_offer_valid(db):
    owner = await _user(db)
    reporter = await _user(db)
    offer = await _offer(db, owner)
    flag = await flag_service.create_flag(
        db, reporter.id, FlagTargetType.OFFER, offer.id,
        reason=FlagReason.INAPPROPRIATE,
    )
    assert flag.target_type == FlagTargetType.OFFER


@pytest.mark.asyncio
async def test_flag_exchange_valid(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper)
    flag = await flag_service.create_flag(
        db, requester.id, FlagTargetType.EXCHANGE, ex.id,
        reason=FlagReason.ABUSE, description="Bad behavior in exchange",
    )
    assert flag.target_type == FlagTargetType.EXCHANGE
    assert flag.description == "Bad behavior in exchange"


@pytest.mark.asyncio
async def test_flag_user_valid(db):
    reporter = await _user(db)
    target = await _user(db)
    flag = await flag_service.create_flag(
        db, reporter.id, FlagTargetType.USER, target.id,
        reason=FlagReason.SCAM,
    )
    assert flag.target_type == FlagTargetType.USER


# ---- Self-flag prevention ----------------------------------------------------

@pytest.mark.asyncio
async def test_flag_own_request_rejected(db):
    owner = await _user(db)
    req = await _request(db, owner)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, owner.id, FlagTargetType.REQUEST, req.id, reason=FlagReason.SPAM,
        )
    assert exc.value.detail == "CANNOT_FLAG_OWN_RESOURCE"


@pytest.mark.asyncio
async def test_flag_own_offer_rejected(db):
    owner = await _user(db)
    offer = await _offer(db, owner)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, owner.id, FlagTargetType.OFFER, offer.id, reason=FlagReason.SPAM,
        )
    assert exc.value.detail == "CANNOT_FLAG_OWN_RESOURCE"


@pytest.mark.asyncio
async def test_flag_self_rejected(db):
    user = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, user.id, FlagTargetType.USER, user.id, reason=FlagReason.ABUSE,
        )
    assert exc.value.detail == "CANNOT_FLAG_OWN_RESOURCE"


# ---- Exchange special rules --------------------------------------------------

@pytest.mark.asyncio
async def test_flag_exchange_non_participant(db):
    requester = await _user(db)
    helper = await _user(db)
    outsider = await _user(db)
    ex = await _exchange(db, requester, helper)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, outsider.id, FlagTargetType.EXCHANGE, ex.id, reason=FlagReason.ABUSE,
        )
    assert exc.value.status_code == 404


# ---- Target validation -------------------------------------------------------

@pytest.mark.asyncio
async def test_flag_nonexistent_request(db):
    reporter = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, reporter.id, FlagTargetType.REQUEST, uuid4(), reason=FlagReason.SPAM,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_flag_nonexistent_user(db):
    reporter = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, reporter.id, FlagTargetType.USER, uuid4(), reason=FlagReason.SPAM,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_flag_suspended_user(db):
    reporter = await _user(db)
    target = await _user(db, status=UserStatus.SUSPENDED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, reporter.id, FlagTargetType.USER, target.id, reason=FlagReason.ABUSE,
        )
    assert exc.value.status_code == 404


# ---- Duplicate prevention ----------------------------------------------------

@pytest.mark.asyncio
async def test_flag_duplicate_rejected(db):
    owner = await _user(db)
    reporter = await _user(db)
    req = await _request(db, owner)
    await flag_service.create_flag(
        db, reporter.id, FlagTargetType.REQUEST, req.id, reason=FlagReason.SPAM,
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await flag_service.create_flag(
            db, reporter.id, FlagTargetType.REQUEST, req.id, reason=FlagReason.ABUSE,
        )
    assert exc.value.detail == "ALREADY_FLAGGED"


@pytest.mark.asyncio
async def test_flag_after_resolved_allowed(db):
    owner = await _user(db)
    reporter = await _user(db)
    req = await _request(db, owner)
    flag1 = await flag_service.create_flag(
        db, reporter.id, FlagTargetType.REQUEST, req.id, reason=FlagReason.SPAM,
    )
    # Simulate resolution
    flag1.status = FlagStatus.RESOLVED
    await db.flush()

    # New flag should be allowed
    flag2 = await flag_service.create_flag(
        db, reporter.id, FlagTargetType.REQUEST, req.id, reason=FlagReason.ABUSE,
    )
    assert flag2.status == FlagStatus.OPEN
    assert flag2.id != flag1.id
