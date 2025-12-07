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
    from app.models.order_action import OrderAction


class UploadedFile(Base):
    """
    文件上传表 (tigu_uploaded_files)

    Stores uploaded files with business entity linking via biz_id and biz_type.

    Business Entity Types (biz_type):
    - "order_action": Links to tigu_order_action.id (workflow photo evidence)
    - "product_sku": Links to product SKU images
    - "prepare_good": Links to tigu_prepare_goods.id (pickup/delivery photos)
    - Other business entity types as needed

    File Linking Pattern:
    1. Upload file → Get file_id
    2. Create business entity (e.g., OrderAction) → Get entity_id
    3. Update file: SET biz_id = entity_id, biz_type = 'order_action'
    """
    __tablename__ = "tigu_uploaded_files"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        comment="文件ID (雪花算法)"
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        comment="原始文件名"
    )

    file_url: Mapped[str] = mapped_column(
        String(500),
        comment="文件存储路径/URL"
    )

    file_type: Mapped[str] = mapped_column(
        String(200),
        comment="文件类型（如image/png、application/pdf等）"
    )

    file_size: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        comment="文件大小（字节）"
    )

    # Business entity linking
    biz_type: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="业务类型（如user、product、order、prepare_good等）"
    )

    biz_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
        index=True,
        comment="业务表主键ID"
    )

    uploader_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
        comment="上传人ID"
    )

    uploader_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="上传人姓名"
    )

    extra_info: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="扩展信息（如缩略图、MD5等）"
    )

    create_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default='',
        comment="创建者"
    )

    create_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="创建时间"
    )

    update_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default='',
        comment="更新者"
    )

    update_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="更新时间"
    )

    remark: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default='',
        comment="备注"
    )

    is_main: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="是否主图: 0=否, 1=是"
    )


class Order(Base):
    __tablename__ = "tigu_order"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    order_sn: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), index=True)
    shop_id: Mapped[int] = mapped_column(BIGINT(unsigned=True))

    # Amount fields
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)

    # Delivery configuration
    # NOTE: delivery_type is stored in tigu_prepare_goods (single source of truth)
    # Access via: prepare_goods.delivery_type

    shipping_type: Mapped[int] = mapped_column(
        Integer,
        default=0,
        index=True,
        comment="发货类型: 0=发仓库, 1=发用户"
    )

    # Order status fields
    shipping_status: Mapped[int] = mapped_column(Integer, default=0)
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

    # Workflow timestamp fields
    shipping_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        comment="发货时间 (when shipment starts)"
    )

    driver_receive_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="司机收货时间 (driver pickup timestamp)"
    )

    arrive_warehouse_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="到达仓库时间 (arrival at warehouse timestamp)"
    )

    warehouse_shipping_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="仓库发货时间 (warehouse ship timestamp)"
    )

    finish_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        comment="完成时间 (final delivery timestamp)"
    )

    create_time: Mapped[datetime] = mapped_column(DateTime())
    update_time: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="创建者")
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="更新者")

    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order", lazy="selectin")
    warehouse: Mapped[Warehouse | None] = relationship("Warehouse", back_populates="orders", lazy="joined")
    driver: Mapped[Driver | None] = relationship("Driver", lazy="joined")
    delivery_proof: Mapped["DeliveryProof | None"] = relationship("DeliveryProof", back_populates="order", lazy="joined", uselist=False)

    # NEW: Order action audit trail
    actions: Mapped[list["OrderAction"]] = relationship(
        "OrderAction",
        back_populates="order",
        lazy="selectin",
        order_by="OrderAction.create_time.desc()"
    )


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
