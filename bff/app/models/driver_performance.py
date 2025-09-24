from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order


class DriverPerformance(Base):
    """Driver performance tracking and analytics"""
    __tablename__ = "driver_performance"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    driver_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("sys_user.user_id"), index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Delivery metrics
    total_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    successful_deliveries: Mapped[int] = mapped_column(Integer, default=0)
    failed_deliveries: Mapped[int] = mapped_column(Integer, default=0)

    # Time metrics (in minutes)
    avg_delivery_time: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_active_time: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Distance metrics (in kilometers)
    total_distance: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Quality metrics
    customer_rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)  # 0.00 to 5.00
    on_time_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # 0.00 to 100.00

    # Efficiency metrics
    orders_per_hour: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    fuel_efficiency: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # km per liter

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    driver: Mapped[User] = relationship("User", lazy="joined")


class DriverPerformanceLog(Base):
    """Detailed log of individual driver actions for performance tracking"""
    __tablename__ = "driver_performance_log"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    driver_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("sys_user.user_id"), index=True)
    order_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), ForeignKey("tigu_order.id"), nullable=True)

    action_type: Mapped[str] = mapped_column(String(50))  # pickup, delivery, route_start, route_end, break_start, break_end
    action_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Location data
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)

    # Performance data
    duration_minutes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    fuel_used: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    # Status and notes
    status: Mapped[str] = mapped_column(String(20), default="completed")  # completed, failed, cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    driver: Mapped[User] = relationship("User", lazy="joined")
    order: Mapped[Order | None] = relationship("Order", lazy="joined")


class DriverAlert(Base):
    """Alerts and notifications for driver performance issues"""
    __tablename__ = "driver_alert"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    driver_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("sys_user.user_id"), index=True)

    alert_type: Mapped[str] = mapped_column(String(50))  # performance_drop, late_delivery, customer_complaint, efficiency_low
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high, critical

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)

    # Alert data
    metric_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, acknowledged, resolved, dismissed
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    driver: Mapped[User] = relationship("User", lazy="joined")