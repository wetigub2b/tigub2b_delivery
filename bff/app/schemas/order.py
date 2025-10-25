from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class WarehouseSnapshot(BaseModel):
    id: int
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OrderItem(BaseModel):
    sku_id: int
    sku_code: Optional[str]
    product_name: str
    quantity: int


class OrderSummary(BaseModel):
    order_sn: str
    shipping_status: int
    order_status: int
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    receiver_city: Optional[str]
    receiver_province: Optional[str]
    receiver_postal_code: Optional[str]
    shipping_status_label: str
    order_status_label: str
    create_time: datetime
    pickup_location: Optional[WarehouseSnapshot]
    items: List[OrderItem]


class OrderDetail(OrderSummary):
    logistics_order_number: Optional[str]
    shipping_time: Optional[datetime]
    finish_time: Optional[datetime]


class UpdateShippingStatus(BaseModel):
    shipping_status: int = Field(..., ge=0, le=3)


class ProofOfDelivery(BaseModel):
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
