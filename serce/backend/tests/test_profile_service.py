"""Unit tests for profile_service — async SQLite in-memory DB."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password, hash_token
from app.db.base import Base
from app.db.models.location import Location, LocationType
from app.db.models.user import (
    EmailChangeToken,
    PhoneVerificationOTP,
    RefreshToken,
    User,
)
from app.services import profile_service


# ---- Fixtures ----------------------------------------------------------------

TEST_PASSWORD = "StrongP@ss1"


@pytest_asyncio.fixture
async def db():
    """In-memory async SQLite session with needed tables."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    tables = [
        User.__table__,
        Location.__table__,
        EmailChangeToken.__table__,
        PhoneVerificationOTP.__table__,
        RefreshToken.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _create_user(db: AsyncSession, **kwargs) -> User:
    defaults = {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "username": f"user_{uuid4().hex[:8]}",
        "password_hash": hash_password(TEST_PASSWORD),
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    await db.flush()
    return user


async def _create_location(db: AsyncSession, **kwargs) -> Location:
    defaults = {"name": "Warszawa", "type": LocationType.CITY}
    defaults.update(kwargs)
    loc = Location(**defaults)
    db.add(loc)
    await db.flush()
    return loc


# ---- update_profile ----------------------------------------------------------

@pytest.mark.asyncio
async def test_update_profile_bio(db):
    user = await _create_user(db)
    result = await profile_service.update_profile(db, user.id, bio="Hello world", location_id=None)
    assert result.bio == "Hello world"


@pytest.mark.asyncio
async def test_update_profile_location_id_valid(db):
    user = await _create_user(db)
    loc = await _create_location(db)
    result = await profile_service.update_profile(db, user.id, bio=None, location_id=loc.id)
    assert result.location_id == loc.id


@pytest.mark.asyncio
async def test_update_profile_location_id_invalid(db):
    user = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.update_profile(db, user.id, bio=None, location_id=99999)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_update_profile_user_not_found(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.update_profile(db, uuid4(), bio="x", location_id=None)
    assert exc_info.value.status_code == 404


# ---- change_username ---------------------------------------------------------

@pytest.mark.asyncio
async def test_change_username_valid(db):
    user = await _create_user(db)
    await profile_service.change_username(db, user.id, "newname123")
    await db.refresh(user)
    assert user.username == "newname123"


@pytest.mark.asyncio
async def test_change_username_taken(db):
    user1 = await _create_user(db, username="taken_name")
    user2 = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.change_username(db, user2.id, "taken_name")
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_change_username_user_not_found(db):
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.change_username(db, uuid4(), "whatever")
    assert exc_info.value.status_code == 404


# ---- initiate_email_change ---------------------------------------------------

@pytest.mark.asyncio
async def test_initiate_email_change_valid(db):
    user = await _create_user(db)
    raw = await profile_service.initiate_email_change(
        db, user.id, TEST_PASSWORD, "new@example.com",
    )
    assert len(raw) > 20  # token_urlsafe(48) → ~64 chars


@pytest.mark.asyncio
async def test_initiate_email_change_wrong_password(db):
    user = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.initiate_email_change(
            db, user.id, "WrongPassword!", "new@example.com",
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_initiate_email_change_email_taken(db):
    user1 = await _create_user(db, email="taken@example.com")
    user2 = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.initiate_email_change(
            db, user2.id, TEST_PASSWORD, "taken@example.com",
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_initiate_email_change_disposable_email(db):
    user = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.initiate_email_change(
            db, user.id, TEST_PASSWORD, "test@mailinator.com",
        )
    assert exc_info.value.status_code == 422


# ---- confirm_email_change ----------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_email_change_valid(db):
    user = await _create_user(db, email="old@example.com")
    raw = await profile_service.initiate_email_change(
        db, user.id, TEST_PASSWORD, "new@example.com",
    )
    old_email, new_email = await profile_service.confirm_email_change(db, raw)
    assert old_email == "old@example.com"
    assert new_email == "new@example.com"
    await db.refresh(user)
    assert user.email == "new@example.com"
    assert user.email_verified is False


@pytest.mark.asyncio
async def test_confirm_email_change_expired_token(db):
    user = await _create_user(db)
    raw = await profile_service.initiate_email_change(
        db, user.id, TEST_PASSWORD, "expired@example.com",
    )
    # Manually expire the token
    token_hash = hash_token(raw)
    from sqlalchemy import select
    result = await db.execute(
        select(EmailChangeToken).where(EmailChangeToken.token_hash == token_hash)
    )
    token = result.scalar_one()
    token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db.flush()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.confirm_email_change(db, raw)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_email_change_already_used(db):
    user = await _create_user(db, email="used@example.com")
    raw = await profile_service.initiate_email_change(
        db, user.id, TEST_PASSWORD, "new_used@example.com",
    )
    await profile_service.confirm_email_change(db, raw)

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.confirm_email_change(db, raw)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_email_change_email_taken_meanwhile(db):
    user1 = await _create_user(db, email="orig@example.com")
    raw = await profile_service.initiate_email_change(
        db, user1.id, TEST_PASSWORD, "race@example.com",
    )
    # Another user takes the email before confirmation
    await _create_user(db, email="race@example.com")

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.confirm_email_change(db, raw)
    assert exc_info.value.status_code == 409


# ---- initiate_phone_change --------------------------------------------------

@pytest.mark.asyncio
async def test_initiate_phone_change_valid(db):
    user = await _create_user(db)
    code = await profile_service.initiate_phone_change(
        db, user.id, TEST_PASSWORD, "+48111222333",
    )
    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
async def test_initiate_phone_change_wrong_password(db):
    user = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.initiate_phone_change(
            db, user.id, "WrongPassword!", "+48111222333",
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_initiate_phone_change_phone_taken(db):
    user1 = await _create_user(db, phone_number="+48999888777")
    user2 = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.initiate_phone_change(
            db, user2.id, TEST_PASSWORD, "+48999888777",
        )
    assert exc_info.value.status_code == 409


# ---- confirm_phone_change ---------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_phone_change_valid(db):
    user = await _create_user(db)
    code = await profile_service.initiate_phone_change(
        db, user.id, TEST_PASSWORD, "+48111222333",
    )
    await profile_service.confirm_phone_change(db, user.id, "+48111222333", code)
    await db.refresh(user)
    assert user.phone_number == "+48111222333"
    assert user.phone_verified is True


@pytest.mark.asyncio
async def test_confirm_phone_change_wrong_code(db):
    user = await _create_user(db)
    await profile_service.initiate_phone_change(
        db, user.id, TEST_PASSWORD, "+48111222333",
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.confirm_phone_change(db, user.id, "+48111222333", "000000")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_phone_change_no_initial_grant(db):
    """Phone change must NOT trigger INITIAL_GRANT — only first-time verify does."""
    user = await _create_user(db, heart_balance=0)
    code = await profile_service.initiate_phone_change(
        db, user.id, TEST_PASSWORD, "+48111222333",
    )
    await profile_service.confirm_phone_change(db, user.id, "+48111222333", code)
    await db.refresh(user)
    assert user.heart_balance == 0  # no hearts granted


# ---- change_password ---------------------------------------------------------

@pytest.mark.asyncio
async def test_change_password_valid(db):
    user = await _create_user(db)
    await profile_service.change_password(db, user.id, TEST_PASSWORD, "NewStrongP@ss2")
    await db.refresh(user)
    from app.core.security import verify_password
    assert verify_password("NewStrongP@ss2", user.password_hash)


@pytest.mark.asyncio
async def test_change_password_wrong_old(db):
    user = await _create_user(db)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await profile_service.change_password(db, user.id, "WrongOldPass!", "NewStrongP@ss2")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_change_password_revokes_refresh_tokens(db):
    user = await _create_user(db)
    # Create a refresh token
    import secrets
    from app.core.security import hash_token as ht
    raw = secrets.token_urlsafe(48)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=ht(raw),
        device_info="test",
        ip_address="127.0.0.1",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(rt)
    await db.flush()
    assert rt.revoked_at is None

    await profile_service.change_password(db, user.id, TEST_PASSWORD, "NewStrongP@ss2")
    await db.refresh(rt)
    assert rt.revoked_at is not None
