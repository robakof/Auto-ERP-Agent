"""Unit tests for core/security.py — bcrypt + JWT + token hashing."""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_hash_and_verify_password():
    plain = "TestP@ss123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)


def test_bcrypt_different_hashes_same_input():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # different salts


def test_create_and_decode_access_token():
    uid = uuid4()
    token = create_access_token(uid)
    result = decode_access_token(token)
    assert result is not None
    user_id, session_id = result
    assert user_id == uid
    assert session_id is None  # no session_id passed


def test_create_and_decode_with_session_id():
    uid = uuid4()
    sid = uuid4()
    token = create_access_token(uid, session_id=sid)
    result = decode_access_token(token)
    assert result is not None
    user_id, session_id = result
    assert user_id == uid
    assert session_id == sid


def test_access_token_expired():
    uid = uuid4()
    token = create_access_token(uid, expires_delta=timedelta(seconds=-1))
    assert decode_access_token(token) is None


def test_access_token_invalid_string():
    assert decode_access_token("garbage") is None


def test_refresh_token_pair():
    raw, token_hash = create_refresh_token()
    assert len(raw) > 30
    assert len(token_hash) == 64
    assert hash_token(raw) == token_hash


def test_refresh_tokens_are_unique():
    r1, h1 = create_refresh_token()
    r2, h2 = create_refresh_token()
    assert r1 != r2
    assert h1 != h2


def test_hash_token_deterministic():
    assert hash_token("test") == hash_token("test")
    assert hash_token("a") != hash_token("b")
