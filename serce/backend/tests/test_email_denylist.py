"""Unit tests for disposable email denylist."""
from app.core.email_denylist import is_disposable_email


def test_mailinator_blocked():
    assert is_disposable_email("user@mailinator.com") is True


def test_yopmail_blocked():
    assert is_disposable_email("test@yopmail.com") is True


def test_guerrillamail_blocked():
    assert is_disposable_email("x@guerrillamail.com") is True


def test_normal_email_allowed():
    assert is_disposable_email("user@gmail.com") is False


def test_custom_domain_allowed():
    assert is_disposable_email("admin@mycompany.pl") is False


def test_case_insensitive():
    assert is_disposable_email("user@MAILINATOR.COM") is True
