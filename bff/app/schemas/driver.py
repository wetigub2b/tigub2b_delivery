from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class DriverProfileResponse(BaseModel):
    """Response schema for driver profile data"""
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    vehicle_model: Optional[str] = None
    status: int
    rating: Decimal = Decimal("5.00")
    total_deliveries: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DriverProfileUpdateRequest(BaseModel):
    """Request schema for updating driver profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    vehicle_type: Optional[str] = Field(None, max_length=50)
    vehicle_plate: Optional[str] = Field(None, max_length=20)
    vehicle_model: Optional[str] = Field(None, max_length=100)
