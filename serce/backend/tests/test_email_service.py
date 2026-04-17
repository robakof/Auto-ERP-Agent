"""Unit tests for email service."""
import pytest

from app.services.email_service import MockEmailService, get_email_service


@pytest.mark.asyncio
async def test_mock_email_service_stores_verification():
    svc = MockEmailService()
    await svc.send_verification("user@example.com", "tok123")
    assert len(svc.sent) == 1
    assert svc.sent[0] == {"type": "verification", "to": "user@example.com", "token": "tok123"}


@pytest.mark.asyncio
async def test_mock_email_service_stores_reset():
    svc = MockEmailService()
    await svc.send_password_reset("user@example.com", "reset_tok")
    assert len(svc.sent) == 1
    assert svc.sent[0] == {"type": "reset", "to": "user@example.com", "token": "reset_tok"}


def test_get_email_service_returns_mock_when_no_api_key():
    svc = get_email_service()
    assert isinstance(svc, MockEmailService)
