"""Unit tests for SMS service."""
import pytest

from app.services.sms_service import MockSmsService, generate_otp, get_sms_service


@pytest.mark.asyncio
async def test_mock_sms_service_stores_sent():
    svc = MockSmsService()
    await svc.send_otp("+48123456789", "123456")
    assert len(svc.sent) == 1
    assert svc.sent[0] == {"phone": "+48123456789", "code": "123456"}


def test_otp_generation_6_digits():
    for _ in range(100):
        code = generate_otp()
        assert len(code) == 6
        assert code.isdigit()


def test_get_sms_service_returns_mock_when_no_token():
    svc = get_sms_service()
    assert isinstance(svc, MockSmsService)
