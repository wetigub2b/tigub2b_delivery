"""
Pydantic schemas for order action audit trail.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderActionBase(BaseModel):
    """Base schema for order action"""
    model_config = ConfigDict(populate_by_name=True)

    order_id: int = Field(alias='orderId')
    order_status: int = Field(alias='orderStatus')
    shipping_status: int = Field(alias='shippingStatus')
    shipping_type: int = Field(alias='shippingType')
    action_type: int = Field(alias='actionType')
    logistics_voucher_file: Optional[str] = Field(default=None, alias='logisticsVoucherFile')


class OrderActionCreate(OrderActionBase):
    """Schema for creating order action"""
    pass


class OrderActionResponse(OrderActionBase):
    """Schema for order action response"""
    id: int
    create_time: datetime = Field(alias='createTime')
    create_by: str = Field(alias='createBy')
    remark: Optional[str] = None


class PickupRequest(BaseModel):
    """Schema for pickup/workflow step with photo upload"""
    model_config = ConfigDict(populate_by_name=True)

    photo: str = Field(..., description="Base64 encoded image or data URL")
    notes: Optional[str] = Field(default=None, max_length=1000)

    @property
    def is_data_url(self) -> bool:
        """Check if photo is a data URL"""
        return self.photo.startswith('data:image/')


class PickupResponse(BaseModel):
    """Schema for pickup/workflow step response"""
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    order_sn: str = Field(alias='orderSn')
    shipping_status: int = Field(alias='shippingStatus')
    action_id: int = Field(alias='actionId')
