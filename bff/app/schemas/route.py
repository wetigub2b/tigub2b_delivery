from typing import List, Optional

from pydantic import BaseModel, Field


class RouteStop(BaseModel):
    order_sn: str
    sequence: int
    address: str
    receiver_name: str
    eta: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


class RoutePlan(BaseModel):
    id: str
    stops: List[RouteStop]


class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
