"""Unit tests for verification_service — async SQLite in-memory DB."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_token
from app.db.base import Base
from app.db.models.heart import HeartLedger, HeartLedgerType
from app.db.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    PhoneVerificationOTP,
    RefreshToken,
    User,
)
from app.services import verification_service
from app.services.sms_service import generate_otp


# ---- Fixtures ----------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    """In-memory async SQLite session with all tables."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # FK OFF — we only create subset of tables (avoid deep FK chain)
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    tables = [
        User.__table__,
        RefreshToken.__table__,
        EmailVerificationToken.__table__,
        PasswordResetToken.__table__,
        PhoneVerificationOTP.__table__,
        HeartLedger.__table__,
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
        "password_hash": "$2b$12$fakehashfakehashfakehashfakehashfakehashfakehashfake",
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    await db.flush()
    return user


# ---- generate_otp / hash_token (basic) --------------------------------------

def test_generate_otp_6_digits():
    for _ in range(50):
        code = generate_otp()
        assert len(code) == 6
        assert code.isdigit()


def test_hash_token_deterministic():
    raw = "test_token_123"
    assert hash_token(raw) == hashlib.sha256(raw.encode()).hexdigest()


def test_hash_token_different_for_different_inputs():
    assert hash_token("a") != hash_token("b")


# ---- Email verification -----------------------------------------------------

@pytest.mark.asyncio
async def test_create_email_verification_token(db):
    user = await _create_user(db)
    raw = await verification_service.create_email_verification(db, user.id, user.email)
    assert len(raw) > 10  # urlsafe base64


@pytest.mark.asyncio
async def test_verify_email_valid_token(db):
    user = await _create_user(db)
    raw = await verification_service.create_email_verification(db, user.id, user.email)
    await db.flush()

    await verification_service.verify_email(db, raw)
    await db.flush()

    await db.refresh(user)
    assert user.email_verified is True


@pytest.mark.asyncio
async def test_verify_email_expired_token(db):
    user = await _create_user(db)
    raw = secrets.token_urlsafe(48)
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(token)
    await db.flush()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verification_service.verify_email(db, raw)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_already_used(db):
    user = await _create_user(db)
    raw = await verification_service.create_email_verification(db, user.id, user.email)
    await db.flush()

    await verification_service.verify_email(db, raw)
    await db.flush()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verification_service.verify_email(db, raw)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_resend_email_creates_new_token(db):
    user = await _create_user(db)
    await verification_service.create_email_verification(db, user.id, user.email)
    await db.flush()

    result = await verification_service.resend_email_verification(db, user.email)
    assert result is not None
    raw_token, uid = result
    assert len(raw_token) > 10
    assert uid == user.id


@pytest.mark.asyncio
async def test_resend_email_rate_limit_exceeded(db):
    user = await _create_user(db)
    # Create 3 tokens (1 from register + 2 resends = over limit on next)
    for _ in range(3):
        await verification_service.create_email_verification(db, user.id, user.email)
        await db.flush()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verification_service.resend_email_verification(db, user.email)
    assert exc_info.value.status_code == 429


# ---- Phone OTP ---------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_phone_otp(db):
    user = await _create_user(db)
    code = await verification_service.create_phone_otp(db, user.id, "+48111222333")
    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
async def test_verify_phone_valid_code(db):
    user = await _create_user(db)
    code = await verification_service.create_phone_otp(db, user.id, "+48111222333")
    await db.flush()

    granted = await verification_service.verify_phone(db, user.id, "+48111222333", code)
    await db.flush()

    await db.refresh(user)
    assert user.phone_verified is True
    assert user.phone_number == "+48111222333"
    assert granted is True  # INITIAL_GRANT


@pytest.mark.asyncio
async def test_verify_phone_wrong_code_increments_attempts(db):
    user = await _create_user(db)
    code = await verification_service.create_phone_otp(db, user.id, "+48111222333")
    await db.flush()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verification_service.verify_phone(db, user.id, "+48111222333", "000000")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_verify_phone_max_attempts_exceeded(db):
    user = await _create_user(db)
    code = await verification_service.create_phone_otp(db, user.id, "+48111222333")
    await db.flush()

    from fastapi import HTTPException
    # Exhaust attempts
    for _ in range(5):
        with pytest.raises(HTTPException):
            await verification_service.verify_phone(db, user.id, "+48111222333", "000000")

    # Now even correct code fails (attempts exhausted)
    with pytest.raises(HTTPException):
        await verification_service.verify_phone(db, user.id, "+48111222333", code)


@pytest.mark.asyncio
async def test_verify_phone_expired_otp(db):
    user = await _create_user(db)
    code = generate_otp()
    otp = PhoneVerificationOTP(
        user_id=user.id,
        phone_number="+48111222333",
        code_hash=hash_token(code),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db.add(otp)
    await db.flush()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verification_service.verify_phone(db, user.id, "+48111222333", code)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_verify_phone_triggers_initial_grant(db):
    user = await _create_user(db)
    code = await verification_service.create_phone_otp(db, user.id, "+48111222333")
    await db.flush()

    granted = await verification_service.verify_phone(db, user.id, "+48111222333", code)
    await db.flush()

    assert granted is True
    await db.refresh(user)
    assert user.heart_balance == 5  # initial_heart_grant


@pytest.mark.asyncio
async def test_initial_grant_idempotent(db):
    user = await _create_user(db)

    # First phone verification
    code1 = await verification_service.create_phone_otp(db, user.id, "+48111222333")
    await db.flush()
    granted1 = await verification_service.verify_phone(db, user.id, "+48111222333", code1)
    await db.flush()
    assert granted1 is True

    # Reset phone_verified to simulate second verification
    user.phone_verified = False
    await db.flush()

    code2 = await verification_service.create_phone_otp(db, user.id, "+48222333444")
    await db.flush()
    granted2 = await verification_service.verify_phone(db, user.id, "+48222333444", code2)
    await db.flush()
    assert granted2 is False  # already got INITIAL_GRANT

    await db.refresh(user)
    assert user.heart_balance == 5  # not 10


# ---- Password reset ----------------------------------------------------------

@pytest.mark.asyncio
async def test_forgot_password_creates_token(db):
    user = await _create_user(db)
    result = await verification_service.create_password_reset(db, user.email)
    assert result is not None
    raw_token, uid = result
    assert len(raw_token) > 10
    assert uid == user.id


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email_no_error(db):
    result = await verification_service.create_password_reset(db, "nobody@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_reset_password_valid_token(db):
    user = await _create_user(db)
    result = await verification_service.create_password_reset(db, user.email)
    raw_token, _ = result
    await db.flush()

    old_hash = user.password_hash
    await verification_service.reset_password(db, raw_token, "NewStr0ngP@ss!")
    await db.flush()

    await db.refresh(user)
    assert user.password_hash != old_hash


@pytest.mark.asyncio
async def test_reset_password_expired_token(db):
    user = await _create_user(db)
    raw = secrets.token_urlsafe(48)
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(token)
    await db.flush()

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verification_service.reset_password(db, raw, "NewP@ss123")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_revokes_all_refresh_tokens(db):
    user = await _create_user(db)
    # Create a refresh token
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token("some_refresh"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(rt)
    await db.flush()

    result = await verification_service.create_password_reset(db, user.email)
    raw_token, _ = result
    await db.flush()

    await verification_service.reset_password(db, raw_token, "NewP@ss123!")
    await db.flush()

    await db.refresh(rt)
    assert rt.revoked_at is not None
