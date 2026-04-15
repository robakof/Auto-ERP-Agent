"""Tests for the initial_schema migration (offline validation).

Since we may not have a live PostgreSQL, these tests validate:
1. Migration file is importable and has correct structure
2. Upgrade/downgrade functions reference all expected tables
3. Migration metadata matches the model metadata (table & column coverage)
"""
import importlib.util
from pathlib import Path

import pytest

from app.db.base import Base
import app.db.models  # noqa: F401 — register all models


MIGRATION_FILE = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "f8e3d1a9b7c2_initial_schema.py"


@pytest.fixture(scope="module")
def migration():
    spec = importlib.util.spec_from_file_location("initial_schema", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_revision_metadata(migration):
    assert migration.revision == "f8e3d1a9b7c2"
    assert migration.down_revision is None
    assert hasattr(migration, "upgrade")
    assert hasattr(migration, "downgrade")


def test_migration_covers_all_tables(migration):
    """Every table in Base.metadata should appear in upgrade() source."""
    import inspect
    source = inspect.getsource(migration.upgrade)

    expected_tables = set(Base.metadata.tables.keys())
    missing = []
    for table_name in expected_tables:
        # Look for create_table("table_name" in the source
        if f'"{table_name}"' not in source:
            missing.append(table_name)

    assert not missing, f"Tables missing from upgrade(): {missing}"


def test_downgrade_drops_all_tables(migration):
    """Every table in upgrade should be dropped in downgrade."""
    import inspect
    source = inspect.getsource(migration.downgrade)

    expected_tables = set(Base.metadata.tables.keys())
    missing = []
    for table_name in expected_tables:
        if f'"{table_name}"' not in source:
            missing.append(table_name)

    assert not missing, f"Tables missing from downgrade(): {missing}"


def test_migration_column_coverage(migration):
    """Spot-check that key columns exist in the migration source."""
    import inspect
    source = inspect.getsource(migration.upgrade)

    checks = {
        "users": ["email", "username", "password_hash", "heart_balance", "status", "role"],
        "heart_ledger": ["from_user_id", "to_user_id", "amount", "type", "related_exchange_id"],
        "exchanges": ["request_id", "offer_id", "requester_id", "helper_id", "initiated_by", "status"],
        "requests": ["user_id", "title", "hearts_offered", "category_id", "location_scope", "updated_at"],
        "offers": ["user_id", "title", "hearts_asked", "category_id", "location_scope", "updated_at"],
        "categories": ["sort_order", "active"],
        "admin_audit_log": ["admin_id", "action", "target_type", "payload"],
    }

    missing = []
    for table, columns in checks.items():
        for col in columns:
            if f'"{col}"' not in source:
                missing.append(f"{table}.{col}")

    assert not missing, f"Columns missing from migration: {missing}"


def test_check_constraints_present(migration):
    """Verify CHECK constraints are in the migration."""
    import inspect
    source = inspect.getsource(migration.upgrade)

    expected = [
        "ck_users_heart_balance_non_negative",
        "ck_requests_hearts_offered_non_negative",
        "ck_offers_hearts_asked_non_negative",
        "ck_heart_ledger_amount_positive",
        "ck_exchange_has_source",
    ]

    missing = [name for name in expected if name not in source]
    assert not missing, f"Check constraints missing: {missing}"


def test_partial_indexes_present(migration):
    """Verify partial unique indexes are in the migration."""
    import inspect
    source = inspect.getsource(migration.upgrade)

    assert "uix_heart_ledger_initial_grant" in source
    assert "uix_exchange_request_accepted" in source
    assert "INITIAL_GRANT" in source
    assert "ACCEPTED" in source


def test_unique_constraints_present(migration):
    """Verify unique constraints are in the migration."""
    import inspect
    source = inspect.getsource(migration.upgrade)

    assert "uq_review_exchange_reviewer" in source


def test_foreign_key_cascades(migration):
    """Token tables should have CASCADE on user FK."""
    import inspect
    source = inspect.getsource(migration.upgrade)

    cascade_tables = [
        "refresh_tokens",
        "password_reset_tokens",
        "email_change_tokens",
        "email_verification_tokens",
        "phone_verification_otps",
        "user_consents",
    ]

    # Each cascade table section should contain ondelete="CASCADE"
    # We check that CASCADE appears enough times (at least 6)
    cascade_count = source.count('ondelete="CASCADE"')
    assert cascade_count >= len(cascade_tables), (
        f"Expected at least {len(cascade_tables)} CASCADE FKs, found {cascade_count}"
    )


def test_enum_types_dropped_in_downgrade(migration):
    """Downgrade should drop all enum types."""
    import inspect
    source = inspect.getsource(migration.downgrade)

    expected_enums = [
        "locationtype",
        "userstatus",
        "userrole",
        "documenttype",
        "heartledgertype",
        "requeststatus",
        "locationscope",
        "offerstatus",
        "exchangestatus",
        "notificationtype",
        "flagtargettype",
        "flagreason",
        "flagstatus",
        "resolutionaction",
        "audittargettype",
    ]

    missing = [name for name in expected_enums if name not in source]
    assert not missing, f"Enum types missing from downgrade: {missing}"
