from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_serializer


class AdminLoginRequest(BaseModel):
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")


class DriverBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    vehicle_model: Optional[str] = None
    notes: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    vehicle_model: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[int] = None


class DriverResponse(DriverBase):
    id: int
    status: int  # 1=active, 0=inactive
    rating: Decimal
    total_deliveries: int
    created_at: datetime
    updated_at: datetime

    # Fields for frontend compatibility (mapped from tigu_driver + sys_user)
    user_id: Optional[int] = None  # From sys_user if linked
    user_name: Optional[str] = None  # From sys_user if linked
    nick_name: Optional[str] = None  # From sys_user if linked
    phonenumber: Optional[str] = None  # Mapped from phone
    license_plate: Optional[str] = None  # Mapped from vehicle_plate
    role: str = "driver"  # Default role
    last_login: Optional[datetime] = None  # From sys_user if linked

    @property
    def is_active(self) -> bool:
        return self.status == 1

    @property
    def is_admin(self) -> bool:
        return self.role in ["admin", "super_admin"]

    @field_serializer('rating')
    def serialize_rating(self, value: Decimal) -> float:
        """Serialize Decimal rating as float for JSON compatibility"""
        return float(value)

    class Config:
        from_attributes = True


class DriverAssignment(BaseModel):
    driver_id: int
    order_sn: str
    priority: Optional[int] = 1
    notes: Optional[str] = None


class DriverPerformance(BaseModel):
    driver_id: int
    total_orders: int
    completed_orders: int
    completion_rate: float
    average_delivery_time: Optional[float] = None
    customer_rating: Optional[float] = None
    last_delivery: Optional[datetime] = None


class OrderDispatch(BaseModel):
    order_sn: str
    driver_id: int
    priority: int = 1
    notes: Optional[str] = None
    estimated_pickup_time: Optional[datetime] = None
    estimated_delivery_time: Optional[datetime] = None


class AdminDashboardStats(BaseModel):
    total_drivers: int
    active_drivers: int
    total_orders: int
    pending_orders: int
    in_transit_orders: int
    completed_orders: int
    completion_rate: float
    average_delivery_time: Optional[float] = None


class DriverLocation(BaseModel):
    driver_id: int
    latitude: float
    longitude: float
    timestamp: datetime
    address: Optional[str] = None


class BulkActionRequest(BaseModel):
    action: str  # activate, deactivate, delete, assign_role
    driver_ids: list[int]
    value: Optional[str] = None  # for assign_role action


class DriverPerformanceMetrics(BaseModel):
    """Comprehensive driver performance metrics"""
    driver_id: int
    driver_name: str
    period_start: datetime
    period_end: datetime

    # Delivery metrics
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float

    # Time metrics
    avg_delivery_time: Optional[Decimal] = None
    total_active_time: Optional[Decimal] = None

    # Distance and efficiency
    total_distance: Optional[Decimal] = None
    orders_per_hour: Optional[Decimal] = None
    fuel_efficiency: Optional[Decimal] = None

    # Quality metrics
    customer_rating: Optional[Decimal] = None
    on_time_percentage: Optional[Decimal] = None

    @field_serializer('avg_delivery_time', 'total_active_time', 'total_distance',
                      'orders_per_hour', 'fuel_efficiency', 'customer_rating',
                      'on_time_percentage')
    def serialize_decimal_fields(self, value: Optional[Decimal]) -> Optional[float]:
        """Serialize Decimal fields as float for JSON compatibility"""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True


class DriverPerformanceLogEntry(BaseModel):
    """Individual driver action log entry"""
    id: int
    driver_id: int
    order_id: Optional[int] = None
    action_type: str
    action_timestamp: datetime
    duration_minutes: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None

    @field_serializer('duration_minutes', 'distance_km')
    def serialize_decimal_fields(self, value: Optional[Decimal]) -> Optional[float]:
        """Serialize Decimal fields as float for JSON compatibility"""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True


class DriverAlertResponse(BaseModel):
    """Driver alert information"""
    id: int
    driver_id: int
    driver_name: str
    alert_type: str
    severity: str
    title: str
    description: str
    metric_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    @field_serializer('metric_value', 'threshold_value')
    def serialize_decimal_fields(self, value: Optional[Decimal]) -> Optional[float]:
        """Serialize Decimal fields as float for JSON compatibility"""
        return float(value) if value is not None else None

    class Config:
        from_attributes = True


class PerformanceAnalyticsRequest(BaseModel):
    """Request for performance analytics"""
    driver_ids: Optional[list[int]] = None
    start_date: datetime
    end_date: datetime
    metrics: list[str] = ["delivery_rate", "avg_time", "customer_rating"]


class PerformanceComparisonResponse(BaseModel):
    """Performance comparison between drivers"""
    driver_id: int
    driver_name: str
    metrics: dict[str, float]
    rank: int
    percentile: float

    class Config:
        from_attributes = True


class AlertActionRequest(BaseModel):
    """Request to update alert status"""
    alert_id: int
    action: str  # acknowledge, resolve, dismiss
    notes: Optional[str] = None