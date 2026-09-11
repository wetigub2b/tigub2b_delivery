from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.order import Order


class DeliveryProof(Base):
    __tablename__ = "tigu_delivery_proof"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tigu_order.id"))
    order_sn: Mapped[str] = mapped_column(String(64), index=True)
    driver_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tigu_driver.id"))
    photo_url: Mapped[str] = mapped_column(String(512))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    # Relationships
    order: Mapped[Order] = relationship("Order", lazy="joined")
    driver: Mapped[Driver] = relationship("Driver", lazy="joined")
