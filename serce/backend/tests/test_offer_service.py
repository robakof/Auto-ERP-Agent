"""Unit tests for offer_service — async SQLite in-memory DB."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.location import Location, LocationType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import LocationScope
from app.db.models.user import User, UserRole, UserStatus
from app.services import offer_service


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
        Offer.__table__, Exchange.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
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
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    await db.flush()
    return user


async def _create_category(db: AsyncSession, **kwargs) -> Category:
    defaults = {"name": "Korepetycje", "active": True}
    defaults.update(kwargs)
    cat = Category(**defaults)
    db.add(cat)
    await db.flush()
    return cat


async def _create_location(db: AsyncSession, **kwargs) -> Location:
    defaults = {"name": "Kraków", "type": LocationType.CITY}
    defaults.update(kwargs)
    loc = Location(**defaults)
    db.add(loc)
    await db.flush()
    return loc


async def _create_offer_fixture(db, user, cat, loc, **kwargs):
    return await offer_service.create_offer(
        db, user.id,
        title=kwargs.get("title", "Pomogę z matmą"),
        description=kwargs.get("description", "Oferuję korepetycje z matematyki i fizyki"),
        hearts_asked=kwargs.get("hearts_asked", 3),
        category_id=cat.id,
        location_id=loc.id,
        location_scope=kwargs.get("location_scope", LocationScope.CITY),
    )


# ---- create: happy path ------------------------------------------------------

@pytest.mark.asyncio
async def test_create_offer_valid(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    assert offer.title == "Pomogę z matmą"
    assert offer.status == OfferStatus.ACTIVE
    assert offer.hearts_asked == 3


# ---- create: guards ----------------------------------------------------------

@pytest.mark.asyncio
async def test_create_category_not_found(db):
    user = await _create_user(db)
    loc = await _create_location(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            db, user.id, title="Test", description="Long enough description here",
            hearts_asked=0, category_id=9999, location_id=loc.id,
            location_scope=LocationScope.CITY,
        )
    assert exc_info.value.detail == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_category_inactive(db):
    user = await _create_user(db)
    cat = await _create_category(db, active=False)
    loc = await _create_location(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            db, user.id, title="Test", description="Long enough description here",
            hearts_asked=0, category_id=cat.id, location_id=loc.id,
            location_scope=LocationScope.CITY,
        )
    assert exc_info.value.detail == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_location_not_found(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.create_offer(
            db, user.id, title="Test", description="Long enough description here",
            hearts_asked=0, category_id=cat.id, location_id=9999,
            location_scope=LocationScope.CITY,
        )
    assert exc_info.value.detail == "LOCATION_NOT_FOUND"


# ---- get: happy path + guards ------------------------------------------------

@pytest.mark.asyncio
async def test_get_offer_valid(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    result = await offer_service.get_offer(db, offer.id, user.id)
    assert result.id == offer.id


@pytest.mark.asyncio
async def test_get_offer_not_found(db):
    user = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.get_offer(db, uuid4(), user.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_hidden_offer_by_non_owner(db):
    owner = await _create_user(db)
    other = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, owner, cat, loc)
    offer.status = OfferStatus.HIDDEN
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        await offer_service.get_offer(db, offer.id, other.id)


@pytest.mark.asyncio
async def test_get_hidden_offer_by_owner(db):
    owner = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, owner, cat, loc)
    offer.status = OfferStatus.HIDDEN
    await db.flush()
    result = await offer_service.get_offer(db, offer.id, owner.id)
    assert result.id == offer.id


@pytest.mark.asyncio
async def test_get_inactive_offer_by_non_owner(db):
    owner = await _create_user(db)
    other = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, owner, cat, loc)
    offer.status = OfferStatus.INACTIVE
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        await offer_service.get_offer(db, offer.id, other.id)


@pytest.mark.asyncio
async def test_get_inactive_offer_by_owner(db):
    owner = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, owner, cat, loc)
    offer.status = OfferStatus.INACTIVE
    await db.flush()
    result = await offer_service.get_offer(db, offer.id, owner.id)
    assert result.id == offer.id


# ---- update: happy path ------------------------------------------------------

@pytest.mark.asyncio
async def test_update_title_only(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    updated = await offer_service.update_offer(db, offer.id, user.id, title="Nowy tytuł")
    assert updated.title == "Nowy tytuł"


@pytest.mark.asyncio
async def test_update_hearts_asked(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc, hearts_asked=3)
    updated = await offer_service.update_offer(db, offer.id, user.id, hearts_asked=10)
    assert updated.hearts_asked == 10


@pytest.mark.asyncio
async def test_update_paused_offer(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    offer.status = OfferStatus.PAUSED
    await db.flush()
    updated = await offer_service.update_offer(db, offer.id, user.id, title="Updated paused")
    assert updated.title == "Updated paused"


# ---- update: guards ----------------------------------------------------------

@pytest.mark.asyncio
async def test_update_not_owner(db):
    user = await _create_user(db)
    other = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.update_offer(db, offer.id, other.id, title="Hack")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_inactive_offer(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    offer.status = OfferStatus.INACTIVE
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.update_offer(db, offer.id, user.id, title="X")
    assert exc_info.value.detail == "OFFER_NOT_EDITABLE"


@pytest.mark.asyncio
async def test_update_hidden_offer(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    offer.status = OfferStatus.HIDDEN
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.update_offer(db, offer.id, user.id, title="X")
    assert exc_info.value.detail == "OFFER_NOT_EDITABLE"


# ---- status management -------------------------------------------------------

@pytest.mark.asyncio
async def test_status_active_to_paused(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    result = await offer_service.change_offer_status(db, offer.id, user, OfferStatus.PAUSED)
    assert result.status == OfferStatus.PAUSED


@pytest.mark.asyncio
async def test_status_paused_to_active(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    offer.status = OfferStatus.PAUSED
    await db.flush()
    result = await offer_service.change_offer_status(db, offer.id, user, OfferStatus.ACTIVE)
    assert result.status == OfferStatus.ACTIVE


@pytest.mark.asyncio
async def test_status_active_to_inactive(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    result = await offer_service.change_offer_status(db, offer.id, user, OfferStatus.INACTIVE)
    assert result.status == OfferStatus.INACTIVE


@pytest.mark.asyncio
async def test_status_paused_to_inactive(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    offer.status = OfferStatus.PAUSED
    await db.flush()
    result = await offer_service.change_offer_status(db, offer.id, user, OfferStatus.INACTIVE)
    assert result.status == OfferStatus.INACTIVE


@pytest.mark.asyncio
async def test_status_inactive_to_active_rejected(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    offer.status = OfferStatus.INACTIVE
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.change_offer_status(db, offer.id, user, OfferStatus.ACTIVE)
    assert exc_info.value.detail == "INVALID_STATUS_TRANSITION"


@pytest.mark.asyncio
async def test_status_hidden_to_active_rejected(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    offer.status = OfferStatus.HIDDEN
    await db.flush()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.change_offer_status(db, offer.id, user, OfferStatus.ACTIVE)
    assert exc_info.value.detail == "INVALID_STATUS_TRANSITION"


@pytest.mark.asyncio
async def test_status_not_owner(db):
    user = await _create_user(db)
    other = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await offer_service.change_offer_status(db, offer.id, other, OfferStatus.PAUSED)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_status_admin_can_hide(db):
    user = await _create_user(db)
    admin = await _create_user(db, role=UserRole.ADMIN)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    result = await offer_service.change_offer_status(db, offer.id, admin, OfferStatus.HIDDEN)
    assert result.status == OfferStatus.HIDDEN


@pytest.mark.asyncio
async def test_status_inactive_cascades_exchanges(db):
    user = await _create_user(db)
    helper = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    exchange = Exchange(
        offer_id=offer.id, requester_id=helper.id, helper_id=user.id,
        initiated_by=helper.id, hearts_agreed=3, status=ExchangeStatus.PENDING,
    )
    db.add(exchange)
    await db.flush()
    await offer_service.change_offer_status(db, offer.id, user, OfferStatus.INACTIVE)
    await db.refresh(exchange)
    assert exchange.status == ExchangeStatus.CANCELLED


@pytest.mark.asyncio
async def test_status_inactive_ignores_non_pending(db):
    user = await _create_user(db)
    helper = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    offer = await _create_offer_fixture(db, user, cat, loc)
    exchange = Exchange(
        offer_id=offer.id, requester_id=helper.id, helper_id=user.id,
        initiated_by=helper.id, hearts_agreed=3, status=ExchangeStatus.ACCEPTED,
    )
    db.add(exchange)
    await db.flush()
    await offer_service.change_offer_status(db, offer.id, user, OfferStatus.INACTIVE)
    await db.refresh(exchange)
    assert exchange.status == ExchangeStatus.ACCEPTED


# ---- list_offers --------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_default_active(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_offer_fixture(db, user, cat, loc, title="Active offer")
    offer2 = await _create_offer_fixture(db, user, cat, loc, title="Paused offer")
    offer2.status = OfferStatus.PAUSED
    await db.flush()

    entries, total = await offer_service.list_offers(db)
    assert total == 1
    assert entries[0].title == "Active offer"


@pytest.mark.asyncio
async def test_list_search_ilike(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_offer_fixture(db, user, cat, loc, title="Korepetycje z angielskiego")
    await _create_offer_fixture(db, user, cat, loc, title="Naprawa rowerów")

    entries, total = await offer_service.list_offers(db, q="angielskiego")
    assert total == 1


@pytest.mark.asyncio
async def test_list_filter_category(db):
    user = await _create_user(db)
    cat1 = await _create_category(db, name="Cat A")
    cat2 = await _create_category(db, name="Cat B")
    loc = await _create_location(db)
    await _create_offer_fixture(db, user, cat1, loc)
    await _create_offer_fixture(db, user, cat2, loc)

    entries, total = await offer_service.list_offers(db, category_id=cat1.id)
    assert total == 1


@pytest.mark.asyncio
async def test_list_pagination(db):
    user = await _create_user(db)
    cat = await _create_category(db)
    loc = await _create_location(db)
    for i in range(5):
        await _create_offer_fixture(db, user, cat, loc, title=f"Offer {i}")

    entries, total = await offer_service.list_offers(db, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2


@pytest.mark.asyncio
async def test_list_excludes_suspended_users(db):
    active_user = await _create_user(db)
    suspended_user = await _create_user(db, status=UserStatus.SUSPENDED)
    cat = await _create_category(db)
    loc = await _create_location(db)
    await _create_offer_fixture(db, active_user, cat, loc, title="Active user offer")
    await _create_offer_fixture(db, suspended_user, cat, loc, title="Suspended user offer")

    entries, total = await offer_service.list_offers(db)
    assert total == 1
    assert entries[0].title == "Active user offer"
