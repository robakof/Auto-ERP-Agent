import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HeartLedgerType(str, enum.Enum):
    INITIAL_GRANT = "INITIAL_GRANT"
    PAYMENT = "PAYMENT"
    GIFT = "GIFT"
    ADMIN_GRANT = "ADMIN_GRANT"
    ADMIN_REFUND = "ADMIN_REFUND"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"


class HeartLedger(Base):
    __tablename__ = "heart_ledger"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    from_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    to_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[HeartLedgerType] = mapped_column(Enum(HeartLedgerType), nullable=False)
    related_exchange_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("exchanges.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_heart_ledger_amount_positive"),
    )
