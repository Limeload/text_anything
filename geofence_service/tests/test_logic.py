"""
Unit tests for geofence logic.
"""
import pytest
from datetime import datetime
from app.models import LocationEvent, Zone
from app.logic import normalize_coordinate, process_location_event, get_zones
from app.state import state_manager
from app.zones import find_zone


class TestNormalizeCoordinate:
    """Tests for coordinate normalization."""
    
    def test_valid_coordinate(self):
        assert normalize_coordinate("37.7749") == 37.7749
        assert normalize_coordinate("-122.4194") == -122.4194
        assert normalize_coordinate("0") == 0.0
    
    def test_invalid_patterns(self):
        assert normalize_coordinate("D$Q") == 0.0
        assert normalize_coordinate("-") == 0.0
        assert normalize_coordinate("") == 0.0
        assert normalize_coordinate("NAN") == 0.0
        assert normalize_coordinate("NONE") == 0.0
        assert normalize_coordinate("NULL") == 0.0
    
    def test_none_value(self):
        assert normalize_coordinate(None) == 0.0
    
    def test_out_of_range(self):
        assert normalize_coordinate("200") == 0.0
        assert normalize_coordinate("-200") == 0.0
    
    def test_unparseable(self):
        assert normalize_coordinate("abc") == 0.0
        assert normalize_coordinate("12.34.56") == 0.0


class TestZoneDetection:
    """Tests for zone detection logic."""
    
    def test_enter_zone(self):
        """Test entering a zone from outside."""
        # Reset state
        state_manager._vehicles.clear()
        state_manager._zone_counts.clear()
        
        event = LocationEvent(
            vehicle_id="vehicle_1",
            latitude="37.78",
            longitude="-122.41"
        )
        
        new_zone_id, transition = process_location_event(event)
        assert new_zone_id is not None
        assert transition.value == "ENTER"
    
    def test_exit_zone(self):
        """Test exiting a zone."""
        # Reset state
        state_manager._vehicles.clear()
        state_manager._zone_counts.clear()
        
        # First enter a zone
        event1 = LocationEvent(
            vehicle_id="vehicle_1",
            latitude="37.78",
            longitude="-122.41"
        )
        process_location_event(event1)
        
        # Then exit
        event2 = LocationEvent(
            vehicle_id="vehicle_1",
            latitude="37.70",
            longitude="-122.50"
        )
        new_zone_id, transition = process_location_event(event2)
        assert new_zone_id is None
        assert transition.value == "EXIT"
    
    def test_change_zone(self):
        """Test changing from one zone to another."""
        # Reset state
        state_manager._vehicles.clear()
        state_manager._zone_counts.clear()
        
        # Enter first zone
        event1 = LocationEvent(
            vehicle_id="vehicle_1",
            latitude="37.78",
            longitude="-122.41"
        )
        process_location_event(event1)
        
        # Move to second zone
        event2 = LocationEvent(
            vehicle_id="vehicle_1",
            latitude="37.625",
            longitude="-122.375"
        )
        new_zone_id, transition = process_location_event(event2)
        assert new_zone_id is not None
        assert transition.value == "CHANGE"
    
    def test_invalid_gps_normalization(self):
        """Test that invalid GPS values are normalized."""
        # Reset state
        state_manager._vehicles.clear()
        state_manager._zone_counts.clear()
        
        event = LocationEvent(
            vehicle_id="vehicle_1",
            latitude="D$Q",
            longitude="-"
        )
        
        new_zone_id, transition = process_location_event(event)
        # Should be outside all zones (0,0)
        assert new_zone_id is None or transition is None


class TestZoneContains:
    """Tests for zone containment logic."""
    
    def test_zone_contains_point(self):
        zone = Zone(
            zone_id="test_zone",
            name="Test",
            min_lat=37.0,
            max_lat=38.0,
            min_lng=-123.0,
            max_lng=-122.0
        )
        
        assert zone.contains(37.5, -122.5) is True
        assert zone.contains(37.0, -122.0) is True  # On boundary
        assert zone.contains(36.9, -122.5) is False  # Below min_lat
        assert zone.contains(38.1, -122.5) is False  # Above max_lat
        assert zone.contains(37.5, -123.1) is False  # Below min_lng
        assert zone.contains(37.5, -121.9) is False  # Above max_lng


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

