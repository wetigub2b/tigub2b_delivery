from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WarehouseSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OrderItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sku_id: int = Field(alias='skuId')
    sku_code: Optional[str] = Field(alias='skuCode')
    product_name: str = Field(alias='productName')
    quantity: int
    sku_image: Optional[str] = Field(default=None, alias='skuImage')


class OrderSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_sn: str = Field(alias='orderSn')
    shipping_status: int = Field(alias='shippingStatus')
    order_status: int = Field(alias='orderStatus')
    driver_id: Optional[int] = Field(default=None, alias='driverId')
    driver_name: Optional[str] = Field(default=None, alias='driverName')
    receiver_name: str = Field(alias='receiverName')
    receiver_phone: str = Field(alias='receiverPhone')
    receiver_address: str = Field(alias='receiverAddress')
    receiver_city: Optional[str] = Field(alias='receiverCity')
    receiver_province: Optional[str] = Field(alias='receiverProvince')
    receiver_postal_code: Optional[str] = Field(alias='receiverPostalCode')
    shipping_status_label: str = Field(alias='shippingStatusLabel')
    order_status_label: str = Field(alias='orderStatusLabel')
    create_time: datetime = Field(alias='createTime')
    pickup_location: Optional[WarehouseSnapshot] = Field(default=None, alias='pickupLocation')
    items: List[OrderItem]


class OrderDetail(OrderSummary):
    logistics_order_number: Optional[str] = Field(alias='logisticsOrderNumber')
    shipping_time: Optional[datetime] = Field(alias='shippingTime')
    finish_time: Optional[datetime] = Field(alias='finishTime')


class UpdateShippingStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    shipping_status: int = Field(..., ge=0, le=3, alias='shippingStatus')


class ProofOfDelivery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    photo: str = Field(..., description="Base64 encoded image or data URL")
    notes: Optional[str] = Field(default=None, max_length=1000)

    @property
    def is_data_url(self) -> bool:
        """Check if photo is a data URL"""
        return self.photo.startswith('data:image/')


class ProofOfDeliveryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    photo_url: str = Field(alias='photoUrl')
    order_sn: str = Field(alias='orderSn')
    uploaded_at: datetime = Field(alias='uploadedAt')
