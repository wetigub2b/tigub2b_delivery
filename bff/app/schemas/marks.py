"""
Pydantic schemas for map markers.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Mark(BaseModel):
    """Map marker schema."""
    id: int = Field(..., description="Marker ID")
    name: str = Field(..., description="Marker name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    type: Optional[str] = Field(None, description="Marker type (Warehouse, Hub, etc.)")
    description: Optional[str] = Field(None, description="Marker description")
    is_active: bool = Field(True, description="Whether marker is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class MarkList(BaseModel):
    """List of markers with metadata."""
    marks: List[Mark] = Field(..., description="List of markers")
    total: int = Field(..., description="Total number of markers")
