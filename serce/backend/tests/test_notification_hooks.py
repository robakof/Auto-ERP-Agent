"""Hook tests — verify that domain events create notifications."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.heart import HeartLedger
from app.db.models.location import Location, LocationType
from app.db.models.message import Message
from app.db.models.notification import Notification, NotificationType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.review import Review
from app.db.models.user import User, UserStatus
from app.services import exchange_service, hearts_service, message_service, review_service


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
        HeartLedger.__table__, Message.__table__, Review.__table__,
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
        "heart_balance": 100,
        "status": UserStatus.ACTIVE,
    }
    defaults.update(kw)
    u = User(**defaults)
    db.add(u)
    await db.flush()
    return u


async def _request_and_exchange(db, requester, helper, status=ExchangeStatus.PENDING):
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
        initiated_by=helper.id, hearts_agreed=0, status=status,
    )
    db.add(ex)
    await db.flush()
    return req, ex


async def _get_notifications(db, user_id, ntype=None):
    q = select(Notification).where(Notification.user_id == user_id)
    if ntype:
        q = q.where(Notification.type == ntype)
    return (await db.execute(q)).scalars().all()


# ---- Exchange hooks ----------------------------------------------------------

@pytest.mark.asyncio
async def test_exchange_create_notifies_other_party(db):
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

    exchange = await exchange_service.create_exchange(
        db, helper.id, request_id=req.id, offer_id=None, hearts_agreed=0,
    )
    # Helper initiated → requester gets notified
    notifs = await _get_notifications(db, requester.id, NotificationType.NEW_EXCHANGE)
    assert len(notifs) == 1
    assert notifs[0].related_exchange_id == exchange.id


@pytest.mark.asyncio
async def test_exchange_accept_notifies_initiator(db):
    requester = await _user(db)
    helper = await _user(db)
    _, ex = await _request_and_exchange(db, requester, helper)
    # helper initiated, requester accepts
    await exchange_service.accept_exchange(db, ex.id, requester.id)
    notifs = await _get_notifications(db, helper.id, NotificationType.EXCHANGE_ACCEPTED)
    assert len(notifs) == 1


@pytest.mark.asyncio
async def test_exchange_complete_notifies_helper(db):
    requester = await _user(db)
    helper = await _user(db)
    _, ex = await _request_and_exchange(db, requester, helper, ExchangeStatus.ACCEPTED)
    await exchange_service.complete_exchange(db, ex.id, requester.id)
    notifs = await _get_notifications(db, helper.id, NotificationType.EXCHANGE_COMPLETED)
    assert len(notifs) == 1


@pytest.mark.asyncio
async def test_exchange_cancel_notifies_other(db):
    requester = await _user(db)
    helper = await _user(db)
    _, ex = await _request_and_exchange(db, requester, helper)
    await exchange_service.cancel_exchange(db, ex.id, requester.id)
    # Requester cancelled → helper gets notified
    notifs = await _get_notifications(db, helper.id, NotificationType.EXCHANGE_CANCELLED)
    assert len(notifs) == 1


# ---- Message hook ------------------------------------------------------------

@pytest.mark.asyncio
async def test_message_send_notifies_other(db):
    requester = await _user(db)
    helper = await _user(db)
    _, ex = await _request_and_exchange(db, requester, helper, ExchangeStatus.ACCEPTED)
    msg = await message_service.send_message(db, ex.id, requester.id, content="Hello!")
    notifs = await _get_notifications(db, helper.id, NotificationType.NEW_MESSAGE)
    assert len(notifs) == 1
    assert notifs[0].related_message_id == msg.id


# ---- Review hook -------------------------------------------------------------

@pytest.mark.asyncio
async def test_review_create_notifies_reviewed(db):
    requester = await _user(db)
    helper = await _user(db)
    _, ex = await _request_and_exchange(db, requester, helper, ExchangeStatus.COMPLETED)
    await review_service.create_review(db, ex.id, requester.id, comment="Great helper!")
    notifs = await _get_notifications(db, helper.id, NotificationType.NEW_REVIEW)
    assert len(notifs) == 1


# ---- Hearts hook -------------------------------------------------------------

@pytest.mark.asyncio
async def test_gift_hearts_notifies_recipient(db):
    sender = await _user(db, heart_balance=50)
    recipient = await _user(db, heart_balance=0)
    await hearts_service.gift_hearts(db, sender.id, recipient.id, 10, "Thanks!")
    notifs = await _get_notifications(db, recipient.id, NotificationType.HEARTS_RECEIVED)
    assert len(notifs) == 1
    assert notifs[0].reason == "Thanks!"
