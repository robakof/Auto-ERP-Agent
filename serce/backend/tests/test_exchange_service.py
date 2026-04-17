"""Unit tests for exchange_service — async SQLite in-memory DB."""
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
from app.db.models.user import User
from app.services import exchange_service


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
        HeartLedger.__table__,
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
        "heart_balance": 20,
    }
    defaults.update(kw)
    u = User(**defaults)
    db.add(u)
    await db.flush()
    return u


async def _cat(db) -> Category:
    c = Category(name="Help", active=True)
    db.add(c)
    await db.flush()
    return c


async def _loc(db) -> Location:
    loc = Location(name="Wro", type=LocationType.CITY)
    db.add(loc)
    await db.flush()
    return loc


async def _request(db, user, cat, loc, **kw) -> Request:
    r = Request(
        user_id=user.id, title="Need help", description="Please help me",
        hearts_offered=kw.get("hearts_offered", 5),
        category_id=cat.id, location_id=loc.id, location_scope=LocationScope.CITY,
        status=kw.get("status", RequestStatus.OPEN),
    )
    db.add(r)
    await db.flush()
    return r


async def _offer(db, user, cat, loc, **kw) -> Offer:
    o = Offer(
        user_id=user.id, title="Can help", description="I can help you out",
        hearts_asked=kw.get("hearts_asked", 3),
        category_id=cat.id, location_id=loc.id, location_scope=LocationScope.CITY,
        status=kw.get("status", OfferStatus.ACTIVE),
    )
    db.add(o)
    await db.flush()
    return o


# ---- create: request-based ---------------------------------------------------

@pytest.mark.asyncio
async def test_create_from_request_valid(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    assert ex.requester_id == requester.id
    assert ex.helper_id == helper.id
    assert ex.status == ExchangeStatus.PENDING


@pytest.mark.asyncio
async def test_create_request_not_found(db):
    helper = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, helper.id, request_id=uuid4(), offer_id=None, hearts_agreed=5)
    assert exc.value.detail == "REQUEST_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_request_not_open(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc, status=RequestStatus.CANCELLED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    assert exc.value.detail == "REQUEST_NOT_OPEN"


@pytest.mark.asyncio
async def test_create_request_self_exchange(db):
    user = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, user, cat, loc)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, user.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    assert exc.value.detail == "CANNOT_EXCHANGE_SELF"


@pytest.mark.asyncio
async def test_create_request_duplicate_pending(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=3)
    assert exc.value.detail == "EXCHANGE_ALREADY_EXISTS"


# ---- create: offer-based -----------------------------------------------------

@pytest.mark.asyncio
async def test_create_from_offer_valid(db):
    helper = await _user(db)
    requester = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    offer = await _offer(db, helper, cat, loc)
    ex = await exchange_service.create_exchange(db, requester.id, request_id=None, offer_id=offer.id, hearts_agreed=3)
    assert ex.requester_id == requester.id
    assert ex.helper_id == helper.id


@pytest.mark.asyncio
async def test_create_offer_not_found(db):
    user = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, user.id, request_id=None, offer_id=uuid4(), hearts_agreed=3)
    assert exc.value.detail == "OFFER_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_offer_not_active(db):
    helper = await _user(db)
    requester = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    offer = await _offer(db, helper, cat, loc, status=OfferStatus.PAUSED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, requester.id, request_id=None, offer_id=offer.id, hearts_agreed=3)
    assert exc.value.detail == "OFFER_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_create_offer_self_exchange(db):
    user = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    offer = await _offer(db, user, cat, loc)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, user.id, request_id=None, offer_id=offer.id, hearts_agreed=3)
    assert exc.value.detail == "CANNOT_EXCHANGE_SELF"


# ---- create: validation (schema level, tested here via service) ---------------

@pytest.mark.asyncio
async def test_create_no_source(db):
    user = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.create_exchange(db, user.id, request_id=None, offer_id=None, hearts_agreed=5)
    assert exc.value.detail == "INVALID_SOURCE"


# ---- get ---------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_as_requester(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    result = await exchange_service.get_exchange(db, ex.id, requester.id)
    assert result.id == ex.id


@pytest.mark.asyncio
async def test_get_as_helper(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    result = await exchange_service.get_exchange(db, ex.id, helper.id)
    assert result.id == ex.id


@pytest.mark.asyncio
async def test_get_not_participant(db):
    requester = await _user(db)
    helper = await _user(db)
    outsider = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.get_exchange(db, ex.id, outsider.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_not_found(db):
    user = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.get_exchange(db, uuid4(), user.id)
    assert exc.value.status_code == 404


# ---- accept ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_accept_valid(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    # Requester accepts (non-initiator)
    result = await exchange_service.accept_exchange(db, ex.id, requester.id)
    assert result.status == ExchangeStatus.ACCEPTED
    await db.refresh(requester)
    assert requester.heart_balance == 15  # 20 - 5 escrow


@pytest.mark.asyncio
async def test_accept_own_exchange(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.accept_exchange(db, ex.id, helper.id)  # initiator tries to accept
    assert exc.value.detail == "CANNOT_ACCEPT_OWN"


@pytest.mark.asyncio
async def test_accept_not_pending(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    await exchange_service.accept_exchange(db, ex.id, requester.id)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.accept_exchange(db, ex.id, requester.id)
    assert exc.value.detail == "NOT_PENDING"


@pytest.mark.asyncio
async def test_accept_insufficient_balance(db):
    requester = await _user(db, heart_balance=2)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.accept_exchange(db, ex.id, requester.id)
    assert exc.value.detail == "INSUFFICIENT_BALANCE"


@pytest.mark.asyncio
async def test_accept_request_already_accepted(db):
    requester = await _user(db, heart_balance=20)
    helper1 = await _user(db)
    helper2 = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex1 = await exchange_service.create_exchange(db, helper1.id, request_id=req.id, offer_id=None, hearts_agreed=3)
    ex2 = await exchange_service.create_exchange(db, helper2.id, request_id=req.id, offer_id=None, hearts_agreed=2)
    await exchange_service.accept_exchange(db, ex1.id, requester.id)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.accept_exchange(db, ex2.id, requester.id)
    assert exc.value.detail == "REQUEST_ALREADY_ACCEPTED"


# ---- complete ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_complete_valid(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db, heart_balance=5)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    await exchange_service.accept_exchange(db, ex.id, requester.id)
    result = await exchange_service.complete_exchange(db, ex.id, requester.id)
    assert result.status == ExchangeStatus.COMPLETED
    assert result.completed_at is not None
    await db.refresh(helper)
    assert helper.heart_balance == 10  # 5 + 5


@pytest.mark.asyncio
async def test_complete_not_requester(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    await exchange_service.accept_exchange(db, ex.id, requester.id)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.complete_exchange(db, ex.id, helper.id)
    assert exc.value.detail == "ONLY_REQUESTER_COMPLETES"


@pytest.mark.asyncio
async def test_complete_not_accepted(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.complete_exchange(db, ex.id, requester.id)
    assert exc.value.detail == "NOT_ACCEPTED"


@pytest.mark.asyncio
async def test_complete_cap_exceeded(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db, heart_balance=48)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    await exchange_service.accept_exchange(db, ex.id, requester.id)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.complete_exchange(db, ex.id, requester.id)
    assert exc.value.detail == "RECIPIENT_CAP_EXCEEDED"


# ---- cancel ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_pending(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    result = await exchange_service.cancel_exchange(db, ex.id, requester.id)
    assert result.status == ExchangeStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_accepted_refund(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    await exchange_service.accept_exchange(db, ex.id, requester.id)
    await db.refresh(requester)
    assert requester.heart_balance == 15  # escrow deducted
    result = await exchange_service.cancel_exchange(db, ex.id, requester.id)
    assert result.status == ExchangeStatus.CANCELLED
    await db.refresh(requester)
    assert requester.heart_balance == 20  # refunded


@pytest.mark.asyncio
async def test_cancel_not_participant(db):
    requester = await _user(db)
    helper = await _user(db)
    outsider = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.cancel_exchange(db, ex.id, outsider.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_cancel_completed(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db, heart_balance=5)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    ex = await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    await exchange_service.accept_exchange(db, ex.id, requester.id)
    await exchange_service.complete_exchange(db, ex.id, requester.id)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await exchange_service.cancel_exchange(db, ex.id, requester.id)
    assert exc.value.detail == "NOT_CANCELLABLE"


# ---- list --------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_my_exchanges(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req = await _request(db, requester, cat, loc)
    await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=5)
    entries, total = await exchange_service.list_exchanges(db, requester.id)
    assert total == 1


@pytest.mark.asyncio
async def test_list_filter_role(db):
    user = await _user(db, heart_balance=20)
    other1 = await _user(db)
    other2 = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    # user as requester (via offer)
    offer = await _offer(db, other1, cat, loc)
    await exchange_service.create_exchange(db, user.id, request_id=None, offer_id=offer.id, hearts_agreed=2)
    # user as helper (via request)
    req = await _request(db, other2, cat, loc)
    await exchange_service.create_exchange(db, user.id, request_id=req.id, offer_id=None, hearts_agreed=3)

    as_requester, total_req = await exchange_service.list_exchanges(db, user.id, role="requester")
    as_helper, total_help = await exchange_service.list_exchanges(db, user.id, role="helper")
    assert total_req == 1
    assert total_help == 1


@pytest.mark.asyncio
async def test_list_filter_status(db):
    requester = await _user(db, heart_balance=20)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    req1 = await _request(db, requester, cat, loc)
    req2 = await _request(db, requester, cat, loc)
    ex1 = await exchange_service.create_exchange(db, helper.id, request_id=req1.id, offer_id=None, hearts_agreed=3)
    await exchange_service.create_exchange(db, helper.id, request_id=req2.id, offer_id=None, hearts_agreed=2)
    await exchange_service.accept_exchange(db, ex1.id, requester.id)

    pending, total_p = await exchange_service.list_exchanges(db, requester.id, status=ExchangeStatus.PENDING)
    assert total_p == 1
    accepted, total_a = await exchange_service.list_exchanges(db, requester.id, status=ExchangeStatus.ACCEPTED)
    assert total_a == 1


@pytest.mark.asyncio
async def test_list_pagination(db):
    requester = await _user(db)
    helper = await _user(db)
    cat, loc = await _cat(db), await _loc(db)
    for _ in range(5):
        req = await _request(db, requester, cat, loc)
        await exchange_service.create_exchange(db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=1)

    entries, total = await exchange_service.list_exchanges(db, requester.id, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2
