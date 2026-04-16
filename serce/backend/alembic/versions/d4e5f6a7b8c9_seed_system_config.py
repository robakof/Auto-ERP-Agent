"""seed_system_config

Seeds initial system_config values:
- tos_current_version = 1.0
- privacy_current_version = 1.0

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


CONFIG_ROWS = [
    ("tos_current_version", "1.0"),
    ("privacy_current_version", "1.0"),
]


def upgrade() -> None:
    t = sa.table(
        "system_config",
        sa.column("key", sa.String),
        sa.column("value", sa.String),
    )
    op.bulk_insert(t, [{"key": k, "value": v} for k, v in CONFIG_ROWS])


def downgrade() -> None:
    op.execute(
        "DELETE FROM system_config WHERE key IN ('tos_current_version', 'privacy_current_version')"
    )
