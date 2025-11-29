"""
Pydantic models for geofence event processing service.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


class ZoneTransition(str, Enum):
    """Zone transition types."""
    ENTER = "ENTER"
    EXIT = "EXIT"
    CHANGE = "CHANGE"


class LocationEvent(BaseModel):
    """GPS location event from vehicle."""
    vehicle_id: str = Field(..., description="Unique vehicle identifier")
    latitude: str = Field(..., description="Latitude (may be invalid like 'D$Q' or '-')")
    longitude: str = Field(..., description="Longitude (may be invalid like 'D$Q' or '-')")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Event timestamp")

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def normalize_coordinates(cls, v: object) -> str:
        """Normalize invalid GPS values to 0.0-compatible strings."""
        if v is None:
            return "0.0"
        v_str = str(v).strip().upper()
        if v_str in ["D$Q", "-", "", "NAN", "NONE", "NULL"]:
            return "0.0"
        try:
            float(v_str)
            return v_str
        except (ValueError, TypeError):
            return "0.0"


class Zone(BaseModel):
    """Geofence zone definition."""
    zone_id: str = Field(..., description="Unique zone identifier")
    name: str = Field(..., description="Zone name")
    min_lat: float = Field(..., description="Minimum latitude")
    max_lat: float = Field(..., description="Maximum latitude")
    min_lng: float = Field(..., description="Minimum longitude")
    max_lng: float = Field(..., description="Maximum longitude")

    def contains(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within this zone."""
        return (
            self.min_lat <= lat <= self.max_lat and
            self.min_lng <= lng <= self.max_lng
        )


class VehicleStatus(BaseModel):
    """Current status of a vehicle."""
    vehicle_id: str
    current_zone: Optional[str] = Field(None, description="Current zone ID, None if outside all zones")
    last_update: Optional[datetime] = Field(None, description="Last location update timestamp")
    last_latitude: Optional[float] = Field(None, description="Last known latitude")
    last_longitude: Optional[float] = Field(None, description="Last known longitude")
    transition_history: List[Dict] = Field(default_factory=list, description="Recent transition events")


class ZoneInfo(BaseModel):
    """Zone information for debugging."""
    zone_id: str
    name: str
    bounds: Dict[str, float]
    vehicle_count: int = Field(0, description="Number of vehicles currently in this zone")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "geofence_event_processing"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

