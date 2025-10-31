from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.delivery_proof import DeliveryProof


class UploadedFile(Base):
    __tablename__ = "tigu_uploaded_files"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    file_url: Mapped[str] = mapped_column(String(500))
    biz_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    biz_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    is_main: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)


class Order(Base):
    __tablename__ = "tigu_order"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    order_sn: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), index=True)
    shop_id: Mapped[int] = mapped_column(BIGINT(unsigned=True))
    shipping_status: Mapped[int] = mapped_column(Integer, default=0)
    shipping_type: Mapped[int] = mapped_column(Integer, default=0)
    order_status: Mapped[int] = mapped_column(Integer, default=0)
    pay_status: Mapped[int] = mapped_column(Integer, default=0)
    receiver_name: Mapped[str] = mapped_column(String(64))
    receiver_phone: Mapped[str] = mapped_column(String(32))
    receiver_province: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receiver_city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receiver_district: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receiver_address: Mapped[str] = mapped_column(String(256))
    receiver_postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    logistics_order_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    warehouse_id: Mapped[int | None] = mapped_column(BIGINT, ForeignKey("tigu_warehouse.id"))
    driver_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), ForeignKey("tigu_driver.id"), nullable=True)
    shipping_time: Mapped[datetime | None] = mapped_column(DateTime())
    finish_time: Mapped[datetime | None] = mapped_column(DateTime())
    driver_receive_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    arrive_warehouse_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    warehouse_shipping_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime())
    update_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order", lazy="selectin")
    warehouse: Mapped[Warehouse | None] = relationship("Warehouse", back_populates="orders", lazy="joined")
    driver: Mapped[Driver | None] = relationship("Driver", lazy="joined")
    delivery_proof: Mapped["DeliveryProof | None"] = relationship("DeliveryProof", back_populates="order", lazy="joined", uselist=False)


class OrderItem(Base):
    __tablename__ = "tigu_order_item"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    order_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("tigu_order.id"), index=True)
    product_id: Mapped[int] = mapped_column(BIGINT(unsigned=True))
    sku_id: Mapped[int] = mapped_column(BIGINT(unsigned=True))
    product_name: Mapped[dict | str] = mapped_column(JSON)
    sku_name: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sku_code: Mapped[str | None] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2))

    order: Mapped[Order] = relationship("Order", back_populates="items")


class Warehouse(Base):
    __tablename__ = "tigu_warehouse"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(2000))
    contact_person: Mapped[str] = mapped_column(String(50))
    contact_phone: Mapped[str] = mapped_column(String(30))
    line1: Mapped[str] = mapped_column(String(255))
    line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(50))
    province: Mapped[str] = mapped_column(String(50))
    country: Mapped[str] = mapped_column(String(50))
    postal_code: Mapped[str] = mapped_column(String(20))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))

    orders: Mapped[list[Order]] = relationship("Order", back_populates="warehouse")


class OrderAction(Base):
    """
    Order action audit trail table.
    Tracks all workflow steps with photo evidence linking.
    """
    __tablename__ = "tigu_order_action"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    order_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("tigu_order.id"), index=True)
    order_status: Mapped[int] = mapped_column(Integer, default=0)
    shipping_status: Mapped[int] = mapped_column(Integer)
    shipping_type: Mapped[int] = mapped_column(Integer, default=0)
    action_type: Mapped[int] = mapped_column(Integer)  # 0-10: action type codes
    logistics_voucher_file: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    create_by: Mapped[str] = mapped_column(String(64), default="")
    create_time: Mapped[datetime] = mapped_column(DateTime())
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    update_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    # Relationship to order
    order: Mapped[Order] = relationship("Order", backref="actions")
