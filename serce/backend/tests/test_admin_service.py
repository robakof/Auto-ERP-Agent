"""Unit tests for admin_service — async SQLite in-memory DB."""
from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.models.admin import (
    AdminAuditLog,
    AuditTargetType,
    ContentFlag,
    FlagReason,
    FlagStatus,
    FlagTargetType,
    ResolutionAction,
)
from app.db.models.category import Category
from app.db.models.exchange import Exchange, ExchangeStatus
from app.db.models.heart import HeartLedger
from app.db.models.location import Location, LocationType
from app.db.models.notification import Notification
from app.db.models.offer import Offer, OfferStatus
from app.db.models.request import LocationScope, Request, RequestStatus
from app.db.models.user import RefreshToken, User, UserRole, UserStatus
from app.services import admin_service


# ---- Fixtures ----------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    # JSONB → JSON for SQLite compatibility
    from sqlalchemy.ext.compiler import compiles
    compiles(JSONB, "sqlite")(lambda element, compiler, **kw: "JSON")

    tables = [
        User.__table__, Category.__table__, Location.__table__,
        Request.__table__, Offer.__table__, Exchange.__table__,
        HeartLedger.__table__, Notification.__table__,
        ContentFlag.__table__, AdminAuditLog.__table__,
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


async def _user(db, **kw) -> User:
    defaults = {
        "email": f"t_{uuid4().hex[:8]}@x.com",
        "username": f"u_{uuid4().hex[:8]}",
        "password_hash": "$2b$12$fakehash",
        "heart_balance": 10,
        "status": UserStatus.ACTIVE,
        "role": UserRole.USER,
    }
    defaults.update(kw)
    u = User(**defaults)
    db.add(u)
    await db.flush()
    return u


async def _admin(db) -> User:
    return await _user(db, role=UserRole.ADMIN)


async def _flag(db, reporter, target_type, target_id, **kw) -> ContentFlag:
    defaults = {
        "reporter_id": reporter.id,
        "target_type": target_type,
        "target_id": target_id,
        "reason": FlagReason.SPAM,
        "status": FlagStatus.OPEN,
    }
    defaults.update(kw)
    f = ContentFlag(**defaults)
    db.add(f)
    await db.flush()
    return f


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
        user_id=user.id, title="Can help", description="I can help you",
        hearts_asked=0, category_id=cat.id, location_id=loc.id,
        location_scope=LocationScope.CITY, status=OfferStatus.ACTIVE,
    )
    db.add(offer)
    await db.flush()
    return offer


from datetime import datetime, timedelta, timezone


async def _refresh_token(db, user) -> RefreshToken:
    rt = RefreshToken(
        user_id=user.id,
        token_hash=uuid4().hex,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(rt)
    await db.flush()
    return rt


# ---- Flag resolution ---------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_flag_dismiss(db):
    admin = await _admin(db)
    reporter = await _user(db)
    target = await _user(db)
    flag = await _flag(db, reporter, FlagTargetType.USER, target.id)
    result = await admin_service.resolve_flag(
        db, admin.id, flag.id, action=ResolutionAction.DISMISS, reason="Not a real issue",
    )
    assert result.status == FlagStatus.DISMISSED
    assert result.resolved_by == admin.id
    # Audit log created
    logs = (await db.execute(select(AdminAuditLog))).scalars().all()
    assert len(logs) == 1
    assert logs[0].action == "resolve_flag"


@pytest.mark.asyncio
async def test_resolve_flag_warn(db):
    admin = await _admin(db)
    reporter = await _user(db)
    target = await _user(db)
    flag = await _flag(db, reporter, FlagTargetType.USER, target.id)
    result = await admin_service.resolve_flag(
        db, admin.id, flag.id, action=ResolutionAction.WARN_USER, reason="Warning issued",
    )
    assert result.status == FlagStatus.RESOLVED


@pytest.mark.asyncio
async def test_resolve_flag_hide_request(db):
    admin = await _admin(db)
    reporter = await _user(db)
    owner = await _user(db)
    req = await _request(db, owner)
    flag = await _flag(db, reporter, FlagTargetType.REQUEST, req.id)
    await admin_service.resolve_flag(
        db, admin.id, flag.id, action=ResolutionAction.HIDE_CONTENT, reason="Inappropriate",
    )
    refreshed = await db.get(Request, req.id)
    assert refreshed.status == RequestStatus.HIDDEN


@pytest.mark.asyncio
async def test_resolve_flag_hide_offer(db):
    admin = await _admin(db)
    reporter = await _user(db)
    owner = await _user(db)
    offer = await _offer(db, owner)
    flag = await _flag(db, reporter, FlagTargetType.OFFER, offer.id)
    await admin_service.resolve_flag(
        db, admin.id, flag.id, action=ResolutionAction.HIDE_CONTENT, reason="Spam offer",
    )
    refreshed = await db.get(Offer, offer.id)
    assert refreshed.status == OfferStatus.HIDDEN


@pytest.mark.asyncio
async def test_resolve_flag_suspend(db):
    admin = await _admin(db)
    reporter = await _user(db)
    target = await _user(db)
    await _refresh_token(db, target)
    flag = await _flag(db, reporter, FlagTargetType.USER, target.id)
    await admin_service.resolve_flag(
        db, admin.id, flag.id, action=ResolutionAction.SUSPEND_USER, reason="Abusive",
        params={"duration_days": 7},
    )
    refreshed = await db.get(User, target.id)
    assert refreshed.status == UserStatus.SUSPENDED


@pytest.mark.asyncio
async def test_resolve_flag_not_found(db):
    admin = await _admin(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.resolve_flag(
            db, admin.id, uuid4(), action=ResolutionAction.DISMISS, reason="nope",
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_resolve_flag_already_resolved(db):
    admin = await _admin(db)
    reporter = await _user(db)
    target = await _user(db)
    flag = await _flag(db, reporter, FlagTargetType.USER, target.id, status=FlagStatus.RESOLVED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.resolve_flag(
            db, admin.id, flag.id, action=ResolutionAction.DISMISS, reason="already done",
        )
    assert exc.value.detail == "FLAG_ALREADY_RESOLVED"


@pytest.mark.asyncio
async def test_resolve_flag_grant_refund(db):
    admin = await _admin(db)
    reporter = await _user(db, heart_balance=5)
    target = await _user(db)
    flag = await _flag(db, reporter, FlagTargetType.USER, target.id)
    await admin_service.resolve_flag(
        db, admin.id, flag.id, action=ResolutionAction.GRANT_HEARTS_REFUND, reason="Refund",
        params={"amount": 3},
    )
    refreshed = await db.get(User, reporter.id)
    assert refreshed.heart_balance == 8


# ---- Suspend -----------------------------------------------------------------

@pytest.mark.asyncio
async def test_suspend_user_valid(db):
    admin = await _admin(db)
    target = await _user(db)
    result = await admin_service.suspend_user(db, admin.id, target.id, reason="Bad behavior")
    assert result.status == UserStatus.SUSPENDED
    assert result.suspension_reason == "Bad behavior"
    logs = (await db.execute(select(AdminAuditLog).where(AdminAuditLog.action == "suspend_user"))).scalars().all()
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_suspend_revokes_tokens(db):
    admin = await _admin(db)
    target = await _user(db)
    rt = await _refresh_token(db, target)
    await admin_service.suspend_user(db, admin.id, target.id, reason="Suspend")
    row = (await db.execute(
        select(RefreshToken).where(RefreshToken.id == rt.id)
    )).scalar_one()
    assert row.revoked_at is not None


@pytest.mark.asyncio
async def test_suspend_admin_rejected(db):
    admin = await _admin(db)
    admin2 = await _admin(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.suspend_user(db, admin.id, admin2.id, reason="nope")
    assert exc.value.detail == "CANNOT_SUSPEND_ADMIN"


@pytest.mark.asyncio
async def test_suspend_already_suspended(db):
    admin = await _admin(db)
    target = await _user(db, status=UserStatus.SUSPENDED)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.suspend_user(db, admin.id, target.id, reason="again")
    assert exc.value.detail == "ALREADY_SUSPENDED"


@pytest.mark.asyncio
async def test_suspend_not_found(db):
    admin = await _admin(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.suspend_user(db, admin.id, uuid4(), reason="ghost")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_suspend_with_duration(db):
    admin = await _admin(db)
    target = await _user(db)
    result = await admin_service.suspend_user(
        db, admin.id, target.id, reason="Temp ban", duration_days=30,
    )
    assert result.suspended_until is not None


# ---- Unsuspend ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_unsuspend_valid(db):
    admin = await _admin(db)
    target = await _user(db)
    await admin_service.suspend_user(db, admin.id, target.id, reason="test")
    result = await admin_service.unsuspend_user(db, admin.id, target.id)
    assert result.status == UserStatus.ACTIVE
    assert result.suspended_at is None
    assert result.suspension_reason is None


@pytest.mark.asyncio
async def test_unsuspend_not_suspended(db):
    admin = await _admin(db)
    target = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.unsuspend_user(db, admin.id, target.id)
    assert exc.value.detail == "NOT_SUSPENDED"


# ---- Hearts grant ------------------------------------------------------------

@pytest.mark.asyncio
async def test_grant_hearts_admin_grant(db):
    admin = await _admin(db)
    target = await _user(db, heart_balance=5)
    ledger = await admin_service.grant_hearts(
        db, admin.id, target.id, amount=3, ledger_type="ADMIN_GRANT", reason="Welcome bonus",
    )
    assert ledger.amount == 3
    refreshed = await db.get(User, target.id)
    assert refreshed.heart_balance == 8
    logs = (await db.execute(select(AdminAuditLog).where(AdminAuditLog.action == "grant_hearts"))).scalars().all()
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_grant_hearts_admin_refund(db):
    admin = await _admin(db)
    target = await _user(db, heart_balance=5)
    ledger = await admin_service.grant_hearts(
        db, admin.id, target.id, amount=2, ledger_type="ADMIN_REFUND", reason="Refund for issue",
    )
    assert ledger.type.value == "ADMIN_REFUND"


@pytest.mark.asyncio
async def test_grant_cap_exceeded(db):
    admin = await _admin(db)
    target = await _user(db, heart_balance=48)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.grant_hearts(
            db, admin.id, target.id, amount=5, ledger_type="ADMIN_GRANT", reason="too much",
        )
    assert exc.value.detail == "RECIPIENT_CAP_EXCEEDED"


@pytest.mark.asyncio
async def test_grant_user_not_found(db):
    admin = await _admin(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.grant_hearts(
            db, admin.id, uuid4(), amount=1, ledger_type="ADMIN_GRANT", reason="ghost",
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_grant_invalid_type(db):
    admin = await _admin(db)
    target = await _user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.grant_hearts(
            db, admin.id, target.id, amount=1, ledger_type="GIFT", reason="wrong type",
        )
    assert exc.value.detail == "INVALID_LEDGER_TYPE"


# ---- Audit listing -----------------------------------------------------------

@pytest.mark.asyncio
async def test_list_audit_empty(db):
    entries, total = await admin_service.list_audit(db)
    assert total == 0
    assert entries == []


@pytest.mark.asyncio
async def test_list_audit_paginated(db):
    admin = await _admin(db)
    for i in range(5):
        target = await _user(db)
        await admin_service.suspend_user(db, admin.id, target.id, reason=f"reason {i}")
    entries, total = await admin_service.list_audit(db, offset=2, limit=2)
    assert total == 5
    assert len(entries) == 2


@pytest.mark.asyncio
async def test_list_audit_filter_action(db):
    admin = await _admin(db)
    target = await _user(db)
    await admin_service.suspend_user(db, admin.id, target.id, reason="bad")
    await admin_service.unsuspend_user(db, admin.id, target.id)
    entries, total = await admin_service.list_audit(db, action="unsuspend_user")
    assert total == 1
    assert entries[0].action == "unsuspend_user"


@pytest.mark.asyncio
async def test_list_audit_filter_target_type(db):
    admin = await _admin(db)
    target = await _user(db)
    await admin_service.grant_hearts(
        db, admin.id, target.id, amount=1, ledger_type="ADMIN_GRANT", reason="test",
    )
    entries, total = await admin_service.list_audit(db, target_type=AuditTargetType.USER)
    assert total >= 1


@pytest.mark.asyncio
async def test_list_audit_filter_date(db):
    admin = await _admin(db)
    target = await _user(db)
    await admin_service.suspend_user(db, admin.id, target.id, reason="dated")
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    entries, total = await admin_service.list_audit(db, from_date=past, to_date=future)
    assert total >= 1


# ---- Flag listing ------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_flags_all(db):
    reporter = await _user(db)
    target = await _user(db)
    await _flag(db, reporter, FlagTargetType.USER, target.id)
    entries, total = await admin_service.list_flags(db)
    assert total == 1


@pytest.mark.asyncio
async def test_list_flags_filter_status(db):
    reporter = await _user(db)
    target = await _user(db)
    await _flag(db, reporter, FlagTargetType.USER, target.id, status=FlagStatus.OPEN)
    await _flag(db, reporter, FlagTargetType.REQUEST, uuid4(), status=FlagStatus.RESOLVED)
    entries, total = await admin_service.list_flags(db, status=FlagStatus.OPEN)
    assert total == 1


@pytest.mark.asyncio
async def test_list_flags_filter_target_type(db):
    reporter = await _user(db)
    target = await _user(db)
    req = await _request(db, target)
    await _flag(db, reporter, FlagTargetType.USER, target.id)
    await _flag(db, reporter, FlagTargetType.REQUEST, req.id)
    entries, total = await admin_service.list_flags(db, target_type=FlagTargetType.REQUEST)
    assert total == 1


@pytest.mark.asyncio
async def test_get_flag_valid(db):
    reporter = await _user(db)
    target = await _user(db)
    flag = await _flag(db, reporter, FlagTargetType.USER, target.id)
    result = await admin_service.get_flag(db, flag.id)
    assert result.id == flag.id


@pytest.mark.asyncio
async def test_get_flag_not_found(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await admin_service.get_flag(db, uuid4())
    assert exc.value.status_code == 404
