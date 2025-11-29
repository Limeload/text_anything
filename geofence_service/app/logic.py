"""
Core geofence detection logic.
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from app.models import Zone, ZoneTransition, LocationEvent
from app.state import state_manager
from app.zones import find_zone, load_zones

logger = logging.getLogger(__name__)

# Cache loaded zones
_zones_cache: Optional[List[Zone]] = None


def get_zones() -> list[Zone]:
    """Get zones, loading from file if not cached."""
    global _zones_cache
    if _zones_cache is None:
        _zones_cache = load_zones()
    return _zones_cache


def normalize_coordinate(coord: str) -> float:
    """
    Normalize GPS coordinate string to float.
    
    Handles invalid values like 'D$Q', '-', etc. by converting to 0.0.
    
    Args:
        coord: Coordinate string (may be invalid)
        
    Returns:
        Normalized float value
    """
    if coord is None:
        return 0.0
    
    coord_str = str(coord).strip().upper()
    
    # Handle known invalid patterns
    if coord_str in ['D$Q', '-', '', 'NAN', 'NONE', 'NULL']:
        logger.debug(f"Normalizing invalid coordinate '{coord}' to 0.0")
        return 0.0
    
    try:
        value = float(coord_str)
        # Validate reasonable GPS range
        if abs(value) > 180:
            logger.warning(f"Coordinate {value} out of valid range, setting to 0.0")
            return 0.0
        return value
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse coordinate '{coord}': {e}, setting to 0.0")
        return 0.0


def process_location_event(event: LocationEvent) -> Tuple[Optional[str], ZoneTransition]:
    """
    Process a location event and determine zone transitions.
    
    Args:
        event: LocationEvent to process
        
    Returns:
        Tuple of (new_zone_id, transition_type)
    """
    # Normalize coordinates
    lat = normalize_coordinate(event.latitude)
    lng = normalize_coordinate(event.longitude)
    
    # Get current vehicle state
    vehicle_state = state_manager.get_vehicle(event.vehicle_id)
    old_zone_id = vehicle_state.current_zone
    
    # Find which zone (if any) contains the new location
    zones = get_zones()
    new_zone = find_zone(lat, lng, zones)
    new_zone_id = new_zone.zone_id if new_zone else None
    
    # Determine transition type
    if old_zone_id is None and new_zone_id is not None:
        transition = ZoneTransition.ENTER
    elif old_zone_id is not None and new_zone_id is None:
        transition = ZoneTransition.EXIT
    elif old_zone_id != new_zone_id and old_zone_id is not None and new_zone_id is not None:
        transition = ZoneTransition.CHANGE
    else:
        # No zone change (staying in same zone or still outside)
        transition = None
    
    # Update vehicle state
    timestamp = event.timestamp or datetime.utcnow()
    vehicle_state.update_location(lat, lng, timestamp)
    
    if transition:
        vehicle_state.update_zone(new_zone_id, transition, timestamp)
        state_manager.update_zone_count(old_zone_id, new_zone_id)
        logger.info(
            f"Vehicle {event.vehicle_id}: {transition.value} "
            f"from {old_zone_id} to {new_zone_id}"
        )
    # If no transition, location is updated but zone state remains the same
    
    return new_zone_id, transition

