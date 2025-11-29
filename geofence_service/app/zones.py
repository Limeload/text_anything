"""
Zone loading and management.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional
from app.models import Zone

logger = logging.getLogger(__name__)


def load_zones(zones_file: str = "zones.json") -> List[Zone]:
    """
    Load zones from JSON file.
    
    Args:
        zones_file: Path to zones.json file
        
    Returns:
        List of Zone objects
        
    Raises:
        FileNotFoundError: If zones file doesn't exist
        ValueError: If zones file is invalid
    """
    # Try to find zones.json relative to the app directory
    zones_path = Path(__file__).parent.parent / zones_file
    
    if not zones_path.exists():
        logger.warning(f"Zones file not found at {zones_path}, using default zones")
        return _get_default_zones()
    
    try:
        with open(zones_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            zones = [Zone(**zone_data) for zone_data in data]
        elif isinstance(data, dict) and 'zones' in data:
            zones = [Zone(**zone_data) for zone_data in data['zones']]
        else:
            raise ValueError(f"Invalid zones.json format: expected list or dict with 'zones' key")
        
        logger.info(f"Loaded {len(zones)} zones from {zones_path}")
        return zones
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in zones file: {e}")
        raise ValueError(f"Invalid JSON in zones file: {e}")
    except Exception as e:
        logger.error(f"Error loading zones: {e}")
        raise


def _get_default_zones() -> List[Zone]:
    """Return default zones if zones.json is not found."""
    return [
        Zone(
            zone_id="zone_1",
            name="Downtown",
            min_lat=37.7749,
            max_lat=37.7849,
            min_lng=-122.4194,
            max_lng=-122.4094
        ),
        Zone(
            zone_id="zone_2",
            name="Airport",
            min_lat=37.6213,
            max_lat=37.6313,
            min_lng=-122.3789,
            max_lng=-122.3689
        )
    ]


def find_zone(lat: float, lng: float, zones: List[Zone]) -> Optional[Zone]:
    """
    Find which zone (if any) contains the given coordinates.
    
    Args:
        lat: Latitude
        lng: Longitude
        zones: List of zones to check
        
    Returns:
        Zone object if found, None otherwise
    """
    for zone in zones:
        if zone.contains(lat, lng):
            return zone
    return None

