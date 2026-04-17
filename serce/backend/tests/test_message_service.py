"""Unit tests for message_service — async SQLite in-memory DB."""
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
from app.db.models.message import Message
from app.db.models.offer import Offer
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.user import User, UserRole
from app.services import message_service


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
        HeartLedger.__table__, Message.__table__,
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


async def _exchange(db, requester, helper, *, status=ExchangeStatus.PENDING) -> Exchange:
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
    return ex


# ---- send_message ------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_valid(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper, status=ExchangeStatus.PENDING)
    msg = await message_service.send_message(db, ex.id, requester.id, content="Hello!")
    assert msg.exchange_id == ex.id
    assert msg.sender_id == requester.id
    assert msg.content == "Hello!"
    assert msg.is_hidden is False


@pytest.mark.asyncio
async def test_send_not_participant(db):
    requester = await _user(db)
    helper = await _user(db)
    outsider = await _user(db)
    ex = await _exchange(db, requester, helper)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await message_service.send_message(db, ex.id, outsider.id, content="Hello!")
    assert exc.value.detail == "NOT_PARTICIPANT"


@pytest.mark.asyncio
async def test_send_exchange_not_found(db):
    user = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await message_service.send_message(db, uuid4(), user.id, content="Hello!")
    assert exc.value.detail == "EXCHANGE_NOT_FOUND"


@pytest.mark.asyncio
async def test_send_exchange_cancelled(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper, status=ExchangeStatus.CANCELLED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await message_service.send_message(db, ex.id, requester.id, content="Hello!")
    assert exc.value.detail == "EXCHANGE_CANCELLED"


@pytest.mark.asyncio
async def test_send_pending_exchange(db):
    """Messages allowed from PENDING — negotiation phase."""
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper, status=ExchangeStatus.PENDING)
    msg = await message_service.send_message(db, ex.id, requester.id, content="Let's discuss!")
    assert msg.id is not None


@pytest.mark.asyncio
async def test_send_completed_exchange(db):
    """Messages allowed after COMPLETED — thanks and history."""
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper, status=ExchangeStatus.COMPLETED)
    msg = await message_service.send_message(db, ex.id, helper.id, content="Thanks!")
    assert msg.id is not None


# ---- list_messages -----------------------------------------------------------

@pytest.mark.asyncio
async def test_list_messages_chronological(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper)
    await message_service.send_message(db, ex.id, requester.id, content="First")
    await message_service.send_message(db, ex.id, helper.id, content="Second")
    entries, total = await message_service.list_messages(db, ex.id, requester.id)
    assert total == 2
    # ASC order — first message first
    contents = [e.content for e in entries]
    assert contents == ["First", "Second"]


@pytest.mark.asyncio
async def test_list_not_participant(db):
    requester = await _user(db)
    helper = await _user(db)
    outsider = await _user(db)
    ex = await _exchange(db, requester, helper)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await message_service.list_messages(db, ex.id, outsider.id)
    assert exc.value.detail == "NOT_PARTICIPANT"


@pytest.mark.asyncio
async def test_list_excludes_hidden(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper)
    await message_service.send_message(db, ex.id, requester.id, content="Visible")
    msg2 = await message_service.send_message(db, ex.id, requester.id, content="Hidden")
    # Manually hide
    msg2.is_hidden = True
    await db.flush()
    entries, total = await message_service.list_messages(db, ex.id, requester.id)
    assert total == 1
    assert entries[0].content == "Visible"


@pytest.mark.asyncio
async def test_list_pagination(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper)
    for i in range(5):
        await message_service.send_message(db, ex.id, requester.id, content=f"Msg {i}")
    entries, total = await message_service.list_messages(db, ex.id, requester.id, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2


# ---- hide_message ------------------------------------------------------------

@pytest.mark.asyncio
async def test_hide_admin_valid(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper)
    msg = await message_service.send_message(db, ex.id, requester.id, content="Bad content")
    result = await message_service.hide_message(db, ex.id, msg.id, UserRole.ADMIN)
    assert result.is_hidden is True


@pytest.mark.asyncio
async def test_hide_not_admin(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper)
    msg = await message_service.send_message(db, ex.id, requester.id, content="Content")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await message_service.hide_message(db, ex.id, msg.id, UserRole.USER)
    assert exc.value.detail == "ADMIN_ONLY"


@pytest.mark.asyncio
async def test_hide_wrong_exchange(db):
    requester = await _user(db)
    helper = await _user(db)
    ex1 = await _exchange(db, requester, helper)
    ex2 = await _exchange(db, requester, helper)
    msg = await message_service.send_message(db, ex1.id, requester.id, content="Content")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await message_service.hide_message(db, ex2.id, msg.id, UserRole.ADMIN)
    assert exc.value.detail == "MESSAGE_NOT_FOUND"


@pytest.mark.asyncio
async def test_hide_message_not_found(db):
    requester = await _user(db)
    helper = await _user(db)
    ex = await _exchange(db, requester, helper)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await message_service.hide_message(db, ex.id, uuid4(), UserRole.ADMIN)
    assert exc.value.detail == "MESSAGE_NOT_FOUND"
