"""
OrderAction API Schemas

Pydantic models for OrderAction API requests and responses.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateOrderActionRequest(BaseModel):
    """Request to create order action"""
    model_config = ConfigDict(populate_by_name=True)

    action_type: int = Field(
        alias="actionType",
        description="Action type code (0-11)",
        ge=0,
        le=11
    )
    file_ids: Optional[List[int]] = Field(
        default=None,
        alias="fileIds",
        description="List of uploaded file IDs for photo evidence"
    )
    remark: Optional[str] = Field(
        default=None,
        description="Optional notes/comments"
    )


class OrderActionResponse(BaseModel):
    """OrderAction response"""
    model_config = ConfigDict(populate_by_name=True)

    id: int
    order_id: int = Field(alias="orderId")
    order_status: int = Field(alias="orderStatus")
    shipping_status: int = Field(alias="shippingStatus")
    shipping_type: int = Field(alias="shippingType")
    action_type: int = Field(alias="actionType")
    action_type_label: str = Field(alias="actionTypeLabel")
    logistics_voucher_file: Optional[str] = Field(
        default=None,
        alias="logisticsVoucherFile",
        description="Comma-separated file IDs"
    )
    create_by: int = Field(alias="createBy")
    remark: Optional[str] = None
    create_time: datetime = Field(alias="createTime")


class OrderActionWithFilesResponse(OrderActionResponse):
    """OrderAction with file URLs"""
    file_urls: List[str] = Field(
        default_factory=list,
        alias="fileUrls",
        description="List of file URLs for photo evidence"
    )


class WorkflowTimelineItem(BaseModel):
    """Single timeline item with action and files"""
    model_config = ConfigDict(populate_by_name=True)

    action_id: int = Field(alias="actionId")
    action_type: int = Field(alias="actionType")
    action_type_label: str = Field(alias="actionTypeLabel")
    create_time: str = Field(alias="createTime", description="ISO format timestamp")
    create_by: int = Field(alias="createBy")
    remark: Optional[str] = None
    order_status: int = Field(alias="orderStatus")
    shipping_status: int = Field(alias="shippingStatus")
    files: List[str] = Field(default_factory=list, description="List of file URLs")


class WorkflowTimelineResponse(BaseModel):
    """Complete workflow timeline"""
    model_config = ConfigDict(populate_by_name=True)

    order_sn: str = Field(alias="orderSn")
    timeline: List[WorkflowTimelineItem] = Field(
        default_factory=list,
        description="Ordered list of workflow actions"
    )


# Action type label mapping
ACTION_TYPE_LABELS = {
    0: "备货",                    # Goods Prepared
    1: "司机收货",                 # Driver Pickup
    2: "司机送达仓库",             # Driver to Warehouse
    3: "仓库收货",                 # Warehouse Receive
    4: "仓库发货",                 # Warehouse Ship
    5: "完成",                     # Complete
    6: "退款申请",                 # Refund Request
    7: "退款同意",                 # Refund Approved
    8: "退款拒绝",                 # Refund Rejected
    9: "退货",                     # Return Goods
    10: "退款完成",                # Refund Complete
    11: "订单取消",                # Order Cancelled
}


def get_action_type_label(action_type: int) -> str:
    """Get human-readable label for action type"""
    return ACTION_TYPE_LABELS.get(action_type, f"Unknown ({action_type})")
