import pytest

from app.db.base import Base
from app.db.models import (
    AdminAuditLog,
    Category,
    ContentFlag,
    EmailChangeToken,
    EmailVerificationToken,
    Exchange,
    HeartLedger,
    Location,
    Message,
    Notification,
    Offer,
    PasswordResetToken,
    PhoneVerificationOTP,
    RefreshToken,
    Request,
    Review,
    SystemConfig,
    User,
    UserConsent,
)

EXPECTED_TABLES = {
    "users",
    "refresh_tokens",
    "password_reset_tokens",
    "email_change_tokens",
    "email_verification_tokens",
    "phone_verification_otps",
    "user_consents",
    "locations",
    "categories",
    "heart_ledger",
    "requests",
    "offers",
    "exchanges",
    "reviews",
    "messages",
    "notifications",
    "content_flags",
    "admin_audit_log",
    "system_config",
}


def test_all_tables_registered():
    registered = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - registered
    assert not missing, f"Missing tables in metadata: {missing}"


def test_all_models_importable():
    models = [
        User, RefreshToken, PasswordResetToken, EmailChangeToken,
        EmailVerificationToken, PhoneVerificationOTP, UserConsent,
        Location, Category, HeartLedger, Request, Offer, Exchange,
        Review, Message, Notification, ContentFlag, AdminAuditLog,
        SystemConfig,
    ]
    for model in models:
        assert hasattr(model, "__tablename__")
        assert model.__tablename__ in EXPECTED_TABLES


def test_user_table_has_check_columns():
    table = User.__table__
    column_names = {c.name for c in table.columns}
    required = {"id", "email", "username", "password_hash", "heart_balance", "status", "role", "created_at"}
    missing = required - column_names
    assert not missing, f"Missing columns on users: {missing}"


def test_exchange_has_partial_unique_index():
    table = Exchange.__table__
    index_names = {idx.name for idx in table.indexes}
    assert "uix_exchange_request_accepted" in index_names


def test_review_has_unique_constraint():
    table = Review.__table__
    constraint_names = {c.name for c in table.constraints if hasattr(c, "name") and c.name}
    assert "uq_review_exchange_reviewer" in constraint_names
