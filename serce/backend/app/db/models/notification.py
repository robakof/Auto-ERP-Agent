import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationType(str, enum.Enum):
    NEW_EXCHANGE = "NEW_EXCHANGE"
    EXCHANGE_ACCEPTED = "EXCHANGE_ACCEPTED"
    EXCHANGE_COMPLETED = "EXCHANGE_COMPLETED"
    NEW_MESSAGE = "NEW_MESSAGE"
    EXCHANGE_CANCELLED = "EXCHANGE_CANCELLED"
    NEW_REVIEW = "NEW_REVIEW"
    HEARTS_RECEIVED = "HEARTS_RECEIVED"
    REQUEST_EXPIRED = "REQUEST_EXPIRED"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    related_exchange_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("exchanges.id"), nullable=True)
    related_message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
