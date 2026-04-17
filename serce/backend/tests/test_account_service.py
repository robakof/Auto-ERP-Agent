"""Unit tests for account_service — soft delete cascade."""
from __future__ import annotations

import hashlib
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.location import Location, LocationType
from app.db.models.notification import Notification, NotificationType
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.user import RefreshToken, User, UserRole, UserStatus
from app.services import account_service


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
        HeartLedger.__table__, Notification.__table__,
        RefreshToken.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
        await conn.execute(text("DROP INDEX IF EXISTS uix_exchange_request_accepted"))
        await conn.execute(text("DROP INDEX IF EXISTS uix_heart_ledger_initial_grant"))

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


PASSWORD_PLAIN = "TestPass1!"
# bcrypt hash of "TestPass1!"
PASSWORD_HASH = "$2b$12$LJ3m4ys3Lk0TSwTvBvXVxOxFwq7FZ0JZnSLqJ0YMfWKj5aMCHdJbm"


async def _user(db, **kw) -> User:
    import bcrypt
    defaults = {
        "email": f"t_{uuid4().hex[:8]}@x.com",
        "username": f"u_{uuid4().hex[:8]}",
        "password_hash": bcrypt.hashpw(PASSWORD_PLAIN.encode(), bcrypt.gensalt()).decode(),
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
    loc = Location(name="Warszawa", type=LocationType.CITY, parent_id=None)
    db.add(loc)
    await db.flush()
    return loc


async def _request(db, user, cat, loc) -> Request:
    r = Request(
        user_id=user.id, category_id=cat.id, title="Help me",
        description="Desc", location_scope=LocationScope.CITY,
        location_id=loc.id, hearts_offered=5,
    )
    db.add(r)
    await db.flush()
    return r


async def _offer(db, user, cat, loc, status=OfferStatus.ACTIVE) -> Offer:
    o = Offer(
        user_id=user.id, category_id=cat.id, title="I can help",
        description="Desc", location_scope=LocationScope.CITY,
        location_id=loc.id, status=status,
    )
    db.add(o)
    await db.flush()
    return o


async def _exchange(db, requester, helper, request, status=ExchangeStatus.PENDING, hearts=5) -> Exchange:
    e = Exchange(
        requester_id=requester.id, helper_id=helper.id,
        request_id=request.id, initiated_by=requester.id,
        hearts_agreed=hearts, status=status,
    )
    db.add(e)
    await db.flush()
    return e


async def _refresh_token(db, user) -> RefreshToken:
    import secrets
    from datetime import datetime, timedelta, timezone
    from app.core.security import hash_token
    raw = secrets.token_urlsafe(32)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(rt)
    await db.flush()
    return rt


# ---- Happy path: void -------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_void_basic(db):
    user = await _user(db, heart_balance=15)
    affected = await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN,
        balance_disposition="void",
    )
    assert user.status == UserStatus.DELETED
    assert user.heart_balance == 0
    assert user.deleted_at is not None
    assert user.anonymized_at is not None
    assert affected == []

    # Ledger entry for void
    ledgers = (await db.execute(
        select(HeartLedger).where(HeartLedger.type == HeartLedgerType.ACCOUNT_DELETED)
    )).scalars().all()
    assert len(ledgers) == 1
    assert ledgers[0].amount == 15
    assert ledgers[0].from_user_id == user.id
    assert ledgers[0].to_user_id is None


@pytest.mark.asyncio
async def test_soft_delete_void_zero_balance(db):
    user = await _user(db, heart_balance=0)
    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN,
        balance_disposition="void",
    )
    assert user.status == UserStatus.DELETED
    # No ledger entry for zero balance
    ledgers = (await db.execute(
        select(HeartLedger).where(HeartLedger.type == HeartLedgerType.ACCOUNT_DELETED)
    )).scalars().all()
    assert len(ledgers) == 0


# ---- Happy path: transfer ---------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_transfer_basic(db):
    user = await _user(db, heart_balance=10)
    recipient = await _user(db, heart_balance=5)
    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN,
        balance_disposition="transfer", transfer_to_user_id=recipient.id,
    )
    assert user.heart_balance == 0
    await db.refresh(recipient)
    assert recipient.heart_balance == 15

    # GIFT ledger
    ledgers = (await db.execute(
        select(HeartLedger).where(
            HeartLedger.type == HeartLedgerType.GIFT,
            HeartLedger.from_user_id == user.id,
        )
    )).scalars().all()
    assert len(ledgers) == 1
    assert ledgers[0].amount == 10
    assert ledgers[0].to_user_id == recipient.id


@pytest.mark.asyncio
async def test_soft_delete_transfer_cap_exceeded(db):
    from app.config import settings
    user = await _user(db, heart_balance=10)
    recipient = await _user(db, heart_balance=settings.heart_balance_cap - 5)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await account_service.soft_delete_account(
            db, user.id, password=PASSWORD_PLAIN,
            balance_disposition="transfer", transfer_to_user_id=recipient.id,
        )
    assert exc.value.detail == "RECIPIENT_CAP_EXCEEDED"


@pytest.mark.asyncio
async def test_soft_delete_transfer_recipient_not_found(db):
    user = await _user(db, heart_balance=10)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await account_service.soft_delete_account(
            db, user.id, password=PASSWORD_PLAIN,
            balance_disposition="transfer", transfer_to_user_id=uuid4(),
        )
    assert exc.value.detail == "RECIPIENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_soft_delete_transfer_to_self(db):
    user = await _user(db, heart_balance=10)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await account_service.soft_delete_account(
            db, user.id, password=PASSWORD_PLAIN,
            balance_disposition="transfer", transfer_to_user_id=user.id,
        )
    assert exc.value.detail == "CANNOT_TRANSFER_TO_SELF"


@pytest.mark.asyncio
async def test_soft_delete_transfer_missing_recipient_id(db):
    user = await _user(db, heart_balance=10)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await account_service.soft_delete_account(
            db, user.id, password=PASSWORD_PLAIN,
            balance_disposition="transfer",
        )
    assert exc.value.detail == "TRANSFER_RECIPIENT_REQUIRED"


# ---- Cascade: exchanges -----------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_cancels_pending_exchanges(db):
    cat = await _cat(db)
    loc = await _loc(db)
    user = await _user(db, heart_balance=20)
    other = await _user(db, heart_balance=20)
    req = await _request(db, other, cat, loc)
    ex = await _exchange(db, other, user, req, status=ExchangeStatus.PENDING, hearts=5)

    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    await db.refresh(ex)
    assert ex.status == ExchangeStatus.CANCELLED

    # No refund for PENDING
    refunds = (await db.execute(
        select(HeartLedger).where(HeartLedger.type == HeartLedgerType.EXCHANGE_REFUND)
    )).scalars().all()
    assert len(refunds) == 0


@pytest.mark.asyncio
async def test_soft_delete_cancels_accepted_exchanges_refund(db):
    cat = await _cat(db)
    loc = await _loc(db)
    requester = await _user(db, heart_balance=10)
    helper = await _user(db, heart_balance=20)
    req = await _request(db, requester, cat, loc)
    ex = await _exchange(db, requester, helper, req, status=ExchangeStatus.ACCEPTED, hearts=5)

    # Delete the helper → exchange cancelled, requester gets refund
    await account_service.soft_delete_account(
        db, helper.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    await db.refresh(ex)
    assert ex.status == ExchangeStatus.CANCELLED

    # Requester got refund
    await db.refresh(requester)
    assert requester.heart_balance == 15  # 10 + 5 refund

    refunds = (await db.execute(
        select(HeartLedger).where(HeartLedger.type == HeartLedgerType.EXCHANGE_REFUND)
    )).scalars().all()
    assert len(refunds) == 1
    assert refunds[0].amount == 5


@pytest.mark.asyncio
async def test_soft_delete_notifications_sent(db):
    cat = await _cat(db)
    loc = await _loc(db)
    user = await _user(db, heart_balance=0)
    other = await _user(db, heart_balance=20)
    req = await _request(db, other, cat, loc)
    ex = await _exchange(db, other, user, req, status=ExchangeStatus.PENDING)

    affected = await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    assert len(affected) == 1
    assert affected[0].user_id == other.id
    assert affected[0].exchange_id == ex.id

    notifs = (await db.execute(
        select(Notification).where(
            Notification.user_id == other.id,
            Notification.type == NotificationType.EXCHANGE_CANCELLED,
        )
    )).scalars().all()
    assert len(notifs) == 1
    assert notifs[0].reason == "account_deleted"


@pytest.mark.asyncio
async def test_soft_delete_reopens_other_request(db):
    cat = await _cat(db)
    loc = await _loc(db)
    user = await _user(db, heart_balance=0)
    other = await _user(db, heart_balance=20)
    req = await _request(db, other, cat, loc)
    # Simulate a request that was moved to non-OPEN status
    req.status = RequestStatus.CANCELLED
    await db.flush()
    ex = await _exchange(db, other, user, req, status=ExchangeStatus.PENDING)

    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    await db.refresh(req)
    assert req.status == RequestStatus.OPEN  # reopened


# ---- Cascade: requests/offers -----------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_cancels_open_requests(db):
    cat = await _cat(db)
    loc = await _loc(db)
    user = await _user(db, heart_balance=0)
    r1 = await _request(db, user, cat, loc)
    r2 = await _request(db, user, cat, loc)
    # One already cancelled — should not be affected
    r2.status = RequestStatus.CANCELLED
    await db.flush()

    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    await db.refresh(r1)
    await db.refresh(r2)
    assert r1.status == RequestStatus.CANCELLED
    assert r2.status == RequestStatus.CANCELLED  # unchanged


@pytest.mark.asyncio
async def test_soft_delete_inactivates_offers(db):
    cat = await _cat(db)
    loc = await _loc(db)
    user = await _user(db, heart_balance=0)
    o1 = await _offer(db, user, cat, loc, status=OfferStatus.ACTIVE)
    o2 = await _offer(db, user, cat, loc, status=OfferStatus.PAUSED)
    o3 = await _offer(db, user, cat, loc, status=OfferStatus.INACTIVE)

    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    await db.refresh(o1)
    await db.refresh(o2)
    await db.refresh(o3)
    assert o1.status == OfferStatus.INACTIVE
    assert o2.status == OfferStatus.INACTIVE
    assert o3.status == OfferStatus.INACTIVE  # unchanged


@pytest.mark.asyncio
async def test_soft_delete_completed_exchange_untouched(db):
    cat = await _cat(db)
    loc = await _loc(db)
    user = await _user(db, heart_balance=0)
    other = await _user(db, heart_balance=20)
    req = await _request(db, other, cat, loc)
    ex = await _exchange(db, other, user, req, status=ExchangeStatus.COMPLETED)

    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    await db.refresh(ex)
    assert ex.status == ExchangeStatus.COMPLETED  # untouched


# ---- Anonymization ----------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_anonymizes_user(db):
    original_email = f"t_{uuid4().hex[:8]}@real.com"
    user = await _user(db, email=original_email, heart_balance=0,
                       bio="My bio", phone_number="+48123456789")

    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    anon = hashlib.sha256(original_email.encode()).hexdigest()[:16]
    assert user.email == f"deleted_{anon}@deleted.local"
    assert user.username == f"deleted_{anon}"
    assert user.phone_number is None
    assert user.bio is None
    assert user.location_id is None
    assert user.email_verified is False
    assert user.phone_verified is False


@pytest.mark.asyncio
async def test_soft_delete_password_invalidated(db):
    user = await _user(db, heart_balance=0)
    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    assert user.password_hash == "!"


# ---- Token revocation -------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_revokes_all_tokens(db):
    user = await _user(db, heart_balance=0)
    rt = await _refresh_token(db, user)
    await account_service.soft_delete_account(
        db, user.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    row = (await db.execute(
        select(RefreshToken).where(RefreshToken.id == rt.id)
    )).scalar_one()
    assert row.revoked_at is not None


# ---- Guards ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_wrong_password(db):
    user = await _user(db, heart_balance=0)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await account_service.soft_delete_account(
            db, user.id, password="WrongPass!",
            balance_disposition="void",
        )
    assert exc.value.status_code == 401
    assert exc.value.detail == "WRONG_PASSWORD"


@pytest.mark.asyncio
async def test_soft_delete_already_deleted(db):
    user = await _user(db, heart_balance=0, status=UserStatus.DELETED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await account_service.soft_delete_account(
            db, user.id, password=PASSWORD_PLAIN,
            balance_disposition="void",
        )
    assert exc.value.status_code == 404


# ---- Balance after refund ----------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_refund_then_void(db):
    """Escrow refund increases balance BEFORE void — correct final balance."""
    cat = await _cat(db)
    loc = await _loc(db)
    # Requester has 5, but is owed 10 from escrow
    requester = await _user(db, heart_balance=5)
    helper = await _user(db, heart_balance=20)
    req = await _request(db, requester, cat, loc)
    ex = await _exchange(db, requester, helper, req, status=ExchangeStatus.ACCEPTED, hearts=10)

    # Requester deletes account → refund 10, balance=15, then void 15
    await account_service.soft_delete_account(
        db, requester.id, password=PASSWORD_PLAIN, balance_disposition="void",
    )
    assert requester.heart_balance == 0

    # ACCOUNT_DELETED ledger should be for 15 (5 original + 10 refund)
    void_ledger = (await db.execute(
        select(HeartLedger).where(HeartLedger.type == HeartLedgerType.ACCOUNT_DELETED)
    )).scalars().all()
    assert len(void_ledger) == 1
    assert void_ledger[0].amount == 15
