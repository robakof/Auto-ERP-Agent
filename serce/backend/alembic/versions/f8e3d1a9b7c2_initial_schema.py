"""initial_schema

Revision ID: f8e3d1a9b7c2
Revises:
Create Date: 2026-04-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f8e3d1a9b7c2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- locations (self-ref FK) ---
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("VOIVODESHIP", "CITY", name="locationtype"),
            nullable=False,
        ),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- categories (self-ref FK) ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(60), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("heart_balance", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("bio", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "suspended", "deleted", name="userstatus"),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="userrole"),
            nullable=False,
            server_default=sa.text("'user'"),
        ),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspended_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspension_reason", sa.String(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "heart_balance >= 0", name="ck_users_heart_balance_non_negative"
        ),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("phone_number"),
    )

    # --- system_config ---
    op.create_table(
        "system_config",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("key"),
    )

    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("device_info", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )

    # --- password_reset_tokens ---
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )

    # --- email_change_tokens ---
    op.create_table(
        "email_change_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("new_email", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_email_change_tokens_token_hash"),
    )

    # --- email_verification_tokens ---
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_email_verification_tokens_token_hash"),
    )

    # --- phone_verification_otps ---
    op.create_table(
        "phone_verification_otps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_hash", name="uq_phone_verification_otps_code_hash"),
    )

    # --- user_consents ---
    op.create_table(
        "user_consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "document_type",
            sa.Enum("tos", "privacy_policy", name="documenttype"),
            nullable=False,
        ),
        sa.Column("document_version", sa.String(), nullable=False),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ip_address", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- requests ---
    op.create_table(
        "requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("hearts_offered", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column(
            "location_scope",
            sa.Enum("CITY", "VOIVODESHIP", "NATIONAL", name="locationscope"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN", "IN_PROGRESS", "DONE", "CANCELLED", "HIDDEN",
                name="requeststatus",
            ),
            nullable=False,
            server_default=sa.text("'OPEN'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "hearts_offered >= 0", name="ck_requests_hearts_offered_non_negative"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- offers ---
    op.create_table(
        "offers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("hearts_asked", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column(
            "location_scope",
            sa.Enum("CITY", "VOIVODESHIP", "NATIONAL", name="locationscope", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE", "PAUSED", "INACTIVE", "HIDDEN",
                name="offerstatus",
            ),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "hearts_asked >= 0", name="ck_offers_hearts_asked_non_negative"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- exchanges ---
    op.create_table(
        "exchanges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=True),
        sa.Column("offer_id", sa.Uuid(), nullable=True),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("helper_id", sa.Uuid(), nullable=False),
        sa.Column("initiated_by", sa.Uuid(), nullable=False),
        sa.Column("hearts_agreed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "ACCEPTED", "COMPLETED", "CANCELLED",
                name="exchangestatus",
            ),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "request_id IS NOT NULL OR offer_id IS NOT NULL",
            name="ck_exchange_has_source",
        ),
        sa.ForeignKeyConstraint(["request_id"], ["requests.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["helper_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # partial unique index: one accepted/completed exchange per request
    op.create_index(
        "uix_exchange_request_accepted",
        "exchanges",
        ["request_id"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('ACCEPTED', 'COMPLETED') AND request_id IS NOT NULL"
        ),
    )

    # --- heart_ledger ---
    op.create_table(
        "heart_ledger",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("from_user_id", sa.Uuid(), nullable=True),
        sa.Column("to_user_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "INITIAL_GRANT", "PAYMENT", "GIFT",
                "ADMIN_GRANT", "ADMIN_REFUND", "ACCOUNT_DELETED",
                name="heartledgertype",
            ),
            nullable=False,
        ),
        sa.Column("related_exchange_id", sa.Uuid(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="ck_heart_ledger_amount_positive"),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_exchange_id"], ["exchanges.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # partial unique index: one INITIAL_GRANT per user
    op.create_index(
        "uix_heart_ledger_initial_grant",
        "heart_ledger",
        ["to_user_id"],
        unique=True,
        postgresql_where=sa.text("type = 'INITIAL_GRANT'"),
    )

    # --- messages ---
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exchange_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["exchange_id"], ["exchanges.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- reviews ---
    op.create_table(
        "reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exchange_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_id", sa.Uuid(), nullable=False),
        sa.Column("comment", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["exchange_id"], ["exchanges.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "exchange_id", "reviewer_id", name="uq_review_exchange_reviewer"
        ),
    )

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "NEW_EXCHANGE", "EXCHANGE_ACCEPTED", "EXCHANGE_COMPLETED",
                "NEW_MESSAGE", "EXCHANGE_CANCELLED", "NEW_REVIEW",
                "HEARTS_RECEIVED", "REQUEST_EXPIRED",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("related_exchange_id", sa.Uuid(), nullable=True),
        sa.Column("related_message_id", sa.Uuid(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_exchange_id"], ["exchanges.id"]),
        sa.ForeignKeyConstraint(["related_message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- content_flags ---
    op.create_table(
        "content_flags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=True),
        sa.Column(
            "target_type",
            sa.Enum(
                "user", "request", "offer", "exchange", "message",
                name="flagtargettype",
            ),
            nullable=False,
        ),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column(
            "reason",
            sa.Enum(
                "spam", "scam", "abuse", "inappropriate", "other",
                name="flagreason",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column(
            "status",
            sa.Enum("open", "resolved", "dismissed", name="flagstatus"),
            nullable=False,
            server_default=sa.text("'open'"),
        ),
        sa.Column("resolved_by", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolution_action",
            sa.Enum(
                "dismiss", "warn_user", "hide_content",
                "suspend_user", "ban_user", "grant_hearts_refund",
                name="resolutionaction",
            ),
            nullable=True,
        ),
        sa.Column("resolution_reason", sa.String(1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- admin_audit_log ---
    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("admin_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column(
            "target_type",
            sa.Enum(
                "user", "request", "offer", "exchange",
                "message", "flag", "system",
                name="audittargettype",
            ),
            nullable=False,
        ),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("admin_audit_log")
    op.drop_table("content_flags")
    op.drop_table("notifications")
    op.drop_table("reviews")
    op.drop_table("messages")
    op.drop_index("uix_heart_ledger_initial_grant", table_name="heart_ledger")
    op.drop_table("heart_ledger")
    op.drop_index("uix_exchange_request_accepted", table_name="exchanges")
    op.drop_table("exchanges")
    op.drop_table("offers")
    op.drop_table("requests")
    op.drop_table("user_consents")
    op.drop_table("phone_verification_otps")
    op.drop_table("email_verification_tokens")
    op.drop_table("email_change_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("system_config")
    op.drop_table("users")
    op.drop_table("categories")
    op.drop_table("locations")

    # Drop enum types
    for enum_name in [
        "audittargettype",
        "resolutionaction",
        "flagstatus",
        "flagreason",
        "flagtargettype",
        "notificationtype",
        "exchangestatus",
        "offerstatus",
        "requeststatus",
        "locationscope",
        "heartledgertype",
        "documenttype",
        "userrole",
        "userstatus",
        "locationtype",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
