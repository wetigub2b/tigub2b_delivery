"""
PrepareGoods API Schemas

Pydantic models for PrepareGoods API requests and responses.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PrepareGoodsItemSchema(BaseModel):
    """PrepareGoods item in response"""
    model_config = ConfigDict(populate_by_name=True)

    prepare_id: int = Field(alias="prepareId")
    order_item_id: int = Field(alias="orderItemId")
    product_id: int = Field(alias="productId")
    sku_id: int = Field(alias="skuId")
    quantity: int


class CreatePreparePackageRequest(BaseModel):
    """Request to create prepare goods package"""
    model_config = ConfigDict(populate_by_name=True)

    order_ids: List[int] = Field(alias="orderIds", description="List of order IDs to include in package")
    shop_id: int = Field(alias="shopId", description="Merchant shop ID")
    delivery_type: int = Field(
        alias="deliveryType",
        description="0=Merchant self-delivery, 1=Third-party driver",
        ge=0,
        le=1
    )
    shipping_type: int = Field(
        alias="shippingType",
        description="0=Ship to warehouse, 1=Ship to user",
        ge=0,
        le=1
    )
    warehouse_id: Optional[int] = Field(
        default=None,
        alias="warehouseId",
        description="Target warehouse ID (required if shipping_type=0)"
    )


class UpdatePrepareStatusRequest(BaseModel):
    """Request to update prepare status"""
    model_config = ConfigDict(populate_by_name=True)

    new_status: int = Field(
        alias="newStatus",
        description="New prepare status (0-6)",
        ge=0,
        le=6
    )


class AssignDriverRequest(BaseModel):
    """Request to assign driver to prepare package"""
    model_config = ConfigDict(populate_by_name=True)

    driver_id: int = Field(alias="driverId", description="Driver ID to assign")


class ConfirmPickupRequest(BaseModel):
    """Request to confirm pickup with photo proof"""
    model_config = ConfigDict(populate_by_name=True)

    photo: str = Field(description="Base64 encoded photo or data URL")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional pickup notes")


class PrepareGoodsResponse(BaseModel):
    """PrepareGoods package response"""
    model_config = ConfigDict(populate_by_name=True)

    id: int
    prepare_sn: str = Field(alias="prepareSn")
    order_ids: str = Field(alias="orderIds", description="Comma-separated order IDs")
    delivery_type: int = Field(alias="deliveryType")
    shipping_type: int = Field(alias="shippingType")
    prepare_status: Optional[int] = Field(default=None, alias="prepareStatus")
    shop_id: int = Field(alias="shopId")
    warehouse_id: Optional[int] = Field(default=None, alias="warehouseId")
    driver_id: Optional[int] = Field(default=None, alias="driverId")
    create_time: datetime = Field(alias="createTime")
    update_time: Optional[datetime] = Field(default=None, alias="updateTime")


class PrepareGoodsDetailResponse(PrepareGoodsResponse):
    """PrepareGoods package with items"""
    items: List[PrepareGoodsItemSchema] = Field(default_factory=list)
    warehouse_name: Optional[str] = Field(default=None, alias="warehouseName")
    driver_name: Optional[str] = Field(default=None, alias="driverName")
    order_serial_numbers: List[str] = Field(default_factory=list, alias="orderSerialNumbers", description="List of order serial numbers")


class PrepareGoodsSummary(BaseModel):
    """PrepareGoods summary for list view"""
    model_config = ConfigDict(populate_by_name=True)

    prepare_sn: str = Field(alias="prepareSn")
    order_count: int = Field(alias="orderCount", description="Number of orders in package")
    delivery_type: int = Field(alias="deliveryType")
    shipping_type: int = Field(alias="shippingType")
    prepare_status: Optional[int] = Field(default=None, alias="prepareStatus")
    prepare_status_label: str = Field(alias="prepareStatusLabel")
    warehouse_name: Optional[str] = Field(default=None, alias="warehouseName")
    driver_name: Optional[str] = Field(default=None, alias="driverName")
    create_time: datetime = Field(alias="createTime")
