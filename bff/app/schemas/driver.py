from pydantic import BaseModel, Field
from typing import Optional, Literal
from decimal import Decimal
from datetime import datetime
from enum import Enum


class StripeStatusEnum(str, Enum):
    """Stripe Connect onboarding status"""
    PENDING = "pending"
    ONBOARDING = "onboarding"
    VERIFIED = "verified"
    RESTRICTED = "restricted"


class StripePaymentInfo(BaseModel):
    """Stripe payment information for driver"""
    stripe_status: Optional[str] = "pending"
    stripe_payouts_enabled: bool = False
    stripe_details_submitted: bool = False
    stripe_connected_at: Optional[datetime] = None
    can_receive_payouts: bool = False


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

    # Stripe payment fields
    stripe_status: Optional[str] = "pending"
    stripe_payouts_enabled: bool = False
    stripe_details_submitted: bool = False
    stripe_connected_at: Optional[datetime] = None

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


class StripeConnectResponse(BaseModel):
    """Response for Stripe Connect onboarding initiation"""
    onboarding_url: str
    stripe_account_id: str


class StripeStatusResponse(BaseModel):
    """Response for Stripe account status check"""
    stripe_status: str
    stripe_payouts_enabled: bool
    stripe_details_submitted: bool
    stripe_connected_at: Optional[datetime] = None
    can_receive_payouts: bool
    requirements_due: Optional[list[str]] = None
