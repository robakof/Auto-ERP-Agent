import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.request import LocationScope


class OfferStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    INACTIVE = "INACTIVE"
    HIDDEN = "HIDDEN"


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    hearts_asked: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    location_scope: Mapped[LocationScope] = mapped_column(Enum(LocationScope), nullable=False)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus), default=OfferStatus.ACTIVE, server_default=text("'ACTIVE'")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("hearts_asked >= 0", name="ck_offers_hearts_asked_non_negative"),
    )
