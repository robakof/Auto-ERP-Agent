"""Unit tests for config validation — C1 secret_key guard."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings, _INSECURE_DEFAULT_KEY


def test_default_key_allowed_in_dev():
    """Default secret_key is fine in development."""
    s = Settings(env="development", secret_key=_INSECURE_DEFAULT_KEY)
    assert s.secret_key == _INSECURE_DEFAULT_KEY


def test_default_key_allowed_in_test():
    """Default secret_key is fine in test."""
    s = Settings(env="test", secret_key=_INSECURE_DEFAULT_KEY)
    assert s.secret_key == _INSECURE_DEFAULT_KEY


def test_default_key_crashes_in_production():
    """Default secret_key must crash in production."""
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        Settings(env="production", secret_key=_INSECURE_DEFAULT_KEY)


def test_default_key_crashes_in_staging():
    """Default secret_key must crash in staging."""
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        Settings(env="staging", secret_key=_INSECURE_DEFAULT_KEY)


def test_custom_key_allowed_in_production():
    """Custom secret_key is fine in production."""
    s = Settings(env="production", secret_key="my-secure-random-key-1234567890ab")
    assert s.secret_key == "my-secure-random-key-1234567890ab"
