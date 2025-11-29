"""
In-memory state management for vehicle locations and zone tracking.
"""
from typing import Dict, Optional, List
from datetime import datetime
from app.models import VehicleStatus, ZoneTransition


class VehicleState:
    """In-memory state for a single vehicle."""
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.current_zone: Optional[str] = None
        self.last_update: Optional[datetime] = None
        self.last_latitude: Optional[float] = None
        self.last_longitude: Optional[float] = None
        self.transition_history: List[Dict] = []

    def update_location(self, lat: float, lng: float, timestamp: datetime):
        """Update vehicle location."""
        self.last_latitude = lat
        self.last_longitude = lng
        self.last_update = timestamp

    def update_zone(self, zone_id: Optional[str], transition: ZoneTransition, timestamp: datetime):
        """Update vehicle zone and record transition."""
        old_zone = self.current_zone
        self.current_zone = zone_id
        
        transition_record = {
            "transition": transition.value,
            "from_zone": old_zone,
            "to_zone": zone_id,
            "timestamp": timestamp.isoformat()
        }
        self.transition_history.append(transition_record)
        
        # Keep only last 100 transitions per vehicle
        if len(self.transition_history) > 100:
            self.transition_history = self.transition_history[-100:]

    def to_status(self) -> VehicleStatus:
        """Convert to VehicleStatus model."""
        return VehicleStatus(
            vehicle_id=self.vehicle_id,
            current_zone=self.current_zone,
            last_update=self.last_update,
            last_latitude=self.last_latitude,
            last_longitude=self.last_longitude,
            transition_history=self.transition_history.copy()
        )


class StateManager:
    """Global state manager for all vehicles."""
    def __init__(self):
        self._vehicles: Dict[str, VehicleState] = {}
        self._zone_counts: Dict[str, int] = {}  # zone_id -> vehicle count

    def get_vehicle(self, vehicle_id: str) -> VehicleState:
        """Get or create vehicle state."""
        if vehicle_id not in self._vehicles:
            self._vehicles[vehicle_id] = VehicleState(vehicle_id)
        return self._vehicles[vehicle_id]

    def update_zone_count(self, old_zone: Optional[str], new_zone: Optional[str]):
        """Update zone vehicle counts."""
        if old_zone:
            self._zone_counts[old_zone] = max(0, self._zone_counts.get(old_zone, 0) - 1)
        if new_zone:
            self._zone_counts[new_zone] = self._zone_counts.get(new_zone, 0) + 1

    def get_zone_count(self, zone_id: str) -> int:
        """Get current vehicle count for a zone."""
        return self._zone_counts.get(zone_id, 0)

    def get_all_vehicles(self) -> Dict[str, VehicleState]:
        """Get all vehicle states."""
        return self._vehicles.copy()


# Global state instance
state_manager = StateManager()

