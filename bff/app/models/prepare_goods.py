"""
PrepareGoods models for merchant preparation workflow.

This module defines the database models for the tigu_prepare_goods and
tigu_prepare_goods_item tables, which track merchant preparation packages
for delivery.

Tables:
- tigu_prepare_goods: Main prepare package table
- tigu_prepare_goods_item: Items in prepare packages
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.driver import Driver
    from app.models.order import OrderItem, Warehouse


class PrepareGoods(Base):
    """
    备货表 (tigu_prepare_goods)

    Tracks prepared packages for driver delivery. A prepare goods package
    can contain multiple orders and defines the delivery configuration.

    Delivery Workflows (based on delivery_type + shipping_type):
    - delivery_type=0, shipping_type=0: Merchant self-delivery to warehouse
    - delivery_type=0, shipping_type=1: Merchant self-delivery to user
    - delivery_type=1, shipping_type=0: Third-party driver to warehouse
    - delivery_type=1, shipping_type=1: Third-party driver to user

    Status Flow (prepare_status):
    - NULL: 待备货 (Pending prepare)
    - 0: 已备货 (Prepared - merchant uploaded photo)
    - 1: 司机收货中 (Driver pickup - driver uploaded photo)
    - 2: 司机送达仓库 (Driver delivered to warehouse)
    - 3: 仓库已收货 (Warehouse received)
    - 4: 司机配送用户 (Driver delivering to user)
    - 5: 已送达 (Delivered to user)
    - 6: 完成 (Complete)
    """
    __tablename__ = "tigu_prepare_goods"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        comment="备货单ID"
    )

    prepare_sn: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        comment="备货单号"
    )

    # Linked orders (one prepare package can contain multiple orders)
    order_ids: Mapped[str] = mapped_column(
        Text,
        comment="订单ID列表(逗号分隔)"
    )

    # Delivery configuration
    delivery_type: Mapped[int] = mapped_column(
        Integer,
        default=0,
        index=True,
        comment="配送方式: 0=商家自配, 1=第三方配送"
    )

    shipping_type: Mapped[int] = mapped_column(
        Integer,
        default=0,
        index=True,
        comment="发货类型: 0=发仓库, 1=发用户"
    )

    # Status tracking
    prepare_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        index=True,
        comment="备货状态: NULL=待备货, 0=已备货, 1=司机收货中, 2=司机送达仓库, 3=仓库已收货, 4=司机配送用户, 5=已送达, 6=完成"
    )

    # Merchant info
    shop_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        index=True,
        comment="商家ID"
    )

    # Warehouse (if applicable - shipping_type=0)
    warehouse_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_warehouse.id"),
        nullable=True,
        index=True,
        comment="目标仓库ID (仅当shipping_type=0)"
    )

    # Driver (if third-party delivery - delivery_type=1)
    driver_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_driver.id"),
        nullable=True,
        index=True,
        comment="司机ID (仅当delivery_type=1)"
    )

    # Timestamps
    create_time: Mapped[datetime] = mapped_column(
        DateTime(),
        comment="创建时间"
    )

    update_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="更新时间"
    )

    # Relationships
    items: Mapped[list[PrepareGoodsItem]] = relationship(
        "PrepareGoodsItem",
        back_populates="prepare_goods",
        lazy="selectin"
    )

    warehouse: Mapped[Warehouse | None] = relationship(
        "Warehouse",
        lazy="joined"
    )

    driver: Mapped[Driver | None] = relationship(
        "Driver",
        lazy="joined"
    )


class PrepareGoodsItem(Base):
    """
    备货明细表 (tigu_prepare_goods_item)

    Items in prepared packages for detailed display. This table provides
    a denormalized view of order items for quick access and display.

    Each item links to an order_item_id from tigu_order_item and contains
    denormalized product information for performance.
    """
    __tablename__ = "tigu_prepare_goods_item"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        comment="备货明细ID"
    )

    prepare_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_prepare_goods.id"),
        index=True,
        comment="备货单ID"
    )

    order_item_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_order_item.id"),
        index=True,
        comment="订单明细ID"
    )

    # Item details (denormalized for performance)
    product_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        comment="商品ID"
    )

    sku_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        comment="SKU ID"
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        comment="数量"
    )

    # Timestamps
    create_time: Mapped[datetime] = mapped_column(
        DateTime(),
        comment="创建时间"
    )

    # Relationships
    prepare_goods: Mapped[PrepareGoods] = relationship(
        "PrepareGoods",
        back_populates="items"
    )

    order_item: Mapped[OrderItem] = relationship(
        "OrderItem",
        lazy="joined"
    )
