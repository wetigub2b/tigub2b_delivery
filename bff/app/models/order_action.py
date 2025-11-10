"""
OrderAction model for complete workflow audit trail.

This module defines the database model for the tigu_order_action table,
which provides a complete audit trail for all order workflow transitions
with photo evidence.

Every status change in the delivery workflow creates an OrderAction record
that captures:
- Status snapshot at time of action
- Action type code
- Photo evidence (file IDs)
- Creator and timestamp
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class OrderAction(Base):
    """
    订单操作记录表 (tigu_order_action)

    Complete audit trail for all order workflow transitions. Each status change
    creates a new action record with photo evidence linked via tigu_uploaded_files.

    Action Type Codes (action_type):
    - 0: 备货 (Goods Prepared) - Merchant marks inventory ready
    - 1: 司机收货 (Driver Pickup) - Driver receives goods from merchant
    - 2: 司机送达仓库 (Driver Arrives Warehouse) - Driver delivers to warehouse
    - 3: 仓库收货 (Warehouse Receives) - Warehouse confirms receipt
    - 4: 仓库发货 (Warehouse Ships) - Warehouse ships to end user
    - 5: 完成 (Delivery Complete) - Final delivery to recipient
    - 6: 用户申请退款 (Refund Requested) - User requests refund
    - 7: 商家允许退货 (Return Approved) - Merchant approves return
    - 8: 商家不允许退货 (Return Denied) - Merchant denies return
    - 9: 商家同意退款 (Refund Approved) - Merchant approves refund
    - 10: 商家拒绝退款 (Refund Denied) - Merchant denies refund
    - 11: 用户退货凭证 (Return Evidence) - User uploads return proof

    Workflow Examples:
    - Workflow 1 (Merchant → Warehouse): actions 0 → 3 → 4 → 5
    - Workflow 2 (Merchant → User): actions 0 → 5
    - Workflow 3 (Driver → Warehouse): actions 0 → 1 → 2 → 3 → 4 → 5
    - Workflow 4 (Driver → User): actions 0 → 1 → 5

    Photo Evidence:
    - logistics_voucher_file contains comma-separated file IDs
    - Files stored in tigu_uploaded_files with biz_id = this action's ID
    - biz_type = "order_action" for action-linked files
    """
    __tablename__ = "tigu_order_action"

    # Snowflake ID for distributed system (generated externally)
    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        comment="雪花算法ID"
    )

    # Order reference
    order_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("tigu_order.id"),
        index=True,
        comment="订单ID"
    )

    # Status snapshot at time of action
    order_status: Mapped[int] = mapped_column(
        Integer,
        comment="订单状态快照 (0-5)"
    )

    shipping_status: Mapped[int] = mapped_column(
        Integer,
        index=True,
        comment="配送状态快照"
    )

    shipping_type: Mapped[int] = mapped_column(
        Integer,
        comment="发货类型: 0=发仓库, 1=发用户"
    )

    # Action details
    action_type: Mapped[int] = mapped_column(
        Integer,
        index=True,
        comment="操作类型(0-11): 0=备货, 1=司机收货, 2=到达仓库, 3=仓库收货, 4=仓库发货, 5=完成, 6-11=退款流程"
    )

    # File evidence (comma-separated file IDs from tigu_uploaded_files)
    logistics_voucher_file: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="物流凭证文件ID列表(逗号分隔，对应tigu_uploaded_files.id)"
    )

    # Audit fields
    create_by: Mapped[str] = mapped_column(
        String(64),
        comment="创建人(操作人): driver_{id}, merchant_{id}, warehouse_{id}"
    )

    create_time: Mapped[datetime] = mapped_column(
        DateTime(),
        index=True,
        comment="创建时间"
    )

    update_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="更新人"
    )

    update_time: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
        comment="更新时间"
    )

    remark: Mapped[str | None] = mapped_column(
        String(5000),
        nullable=True,
        comment="备注"
    )

    # Relationships
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="actions",
        lazy="joined"
    )
