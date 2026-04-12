import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FlagTargetType(str, enum.Enum):
    USER = "user"
    REQUEST = "request"
    OFFER = "offer"
    EXCHANGE = "exchange"
    MESSAGE = "message"


class FlagReason(str, enum.Enum):
    SPAM = "spam"
    SCAM = "scam"
    ABUSE = "abuse"
    INAPPROPRIATE = "inappropriate"
    OTHER = "other"


class FlagStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ResolutionAction(str, enum.Enum):
    DISMISS = "dismiss"
    WARN_USER = "warn_user"
    HIDE_CONTENT = "hide_content"
    SUSPEND_USER = "suspend_user"
    BAN_USER = "ban_user"
    GRANT_HEARTS_REFUND = "grant_hearts_refund"


class ContentFlag(Base):
    __tablename__ = "content_flags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_type: Mapped[FlagTargetType] = mapped_column(Enum(FlagTargetType), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    reason: Mapped[FlagReason] = mapped_column(Enum(FlagReason), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[FlagStatus] = mapped_column(Enum(FlagStatus), default=FlagStatus.OPEN)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_action: Mapped[ResolutionAction | None] = mapped_column(Enum(ResolutionAction), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditTargetType(str, enum.Enum):
    USER = "user"
    REQUEST = "request"
    OFFER = "offer"
    EXCHANGE = "exchange"
    MESSAGE = "message"
    FLAG = "flag"
    SYSTEM = "system"


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[AuditTargetType] = mapped_column(Enum(AuditTargetType), nullable=False)
    target_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
