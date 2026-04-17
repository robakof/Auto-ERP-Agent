"""Unit tests for verification_service — logic only, no DB (mocked)."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.verification_service import (
    _find_valid_token,
    _grant_initial_hearts,
)
from app.services.sms_service import generate_otp


def test_generate_otp_6_digits():
    for _ in range(50):
        code = generate_otp()
        assert len(code) == 6
        assert code.isdigit()


def test_hash_token_deterministic():
    from app.core.security import hash_token
    raw = "test_token_123"
    assert hash_token(raw) == hashlib.sha256(raw.encode()).hexdigest()


def test_hash_token_different_for_different_inputs():
    from app.core.security import hash_token
    assert hash_token("a") != hash_token("b")
