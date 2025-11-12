from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RouteStop(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_sn: str = Field(alias='orderSn')
    sequence: int
    address: str
    receiver_name: str = Field(alias='receiverName')
    eta: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RoutePlan(BaseModel):
    id: str
    stops: List[RouteStop]


class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
