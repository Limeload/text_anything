"""
FastAPI application for geofence event processing service.
"""
import logging
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from app.models import LocationEvent, VehicleStatus, ZoneInfo, HealthResponse, ZoneTransition
from app.logic import process_location_event, get_zones
from app.state import state_manager
from app.zones import load_zones

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Geofence Event Processing Service",
    description="Microservice for processing GPS events and detecting zone entry/exit",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    try:
        # Pre-load zones
        zones = load_zones()
        logger.info(f"Service started. Loaded {len(zones)} zones.")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Basic root endpoint with service info.
    """
    return {
        "service": "geofence_event_processing",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/events/location", status_code=status.HTTP_200_OK)
async def post_location_event(event: LocationEvent) -> Dict:
    """
    Process a GPS location event from a vehicle.
    
    Detects zone entry, exit, or change transitions.
    
    Args:
        event: LocationEvent with vehicle_id, latitude, longitude, timestamp
        
    Returns:
        Dict with vehicle_id, current_zone, and transition information
    """
    try:
        new_zone_id, transition = process_location_event(event)
        
        response = {
            "vehicle_id": event.vehicle_id,
            "current_zone": new_zone_id,
            "transition": transition.value if transition else None,
            "timestamp": (event.timestamp or datetime.utcnow()).isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing location event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing event: {str(e)}"
        )


@app.get("/vehicles/{vehicle_id}/status", response_model=VehicleStatus)
async def get_vehicle_status(vehicle_id: str) -> VehicleStatus:
    """
    Get current status of a vehicle.
    
    Args:
        vehicle_id: Unique vehicle identifier
        
    Returns:
        VehicleStatus with current zone, location, and transition history
    """
    try:
        vehicle_state = state_manager.get_vehicle(vehicle_id)
        return vehicle_state.to_status()
        
    except Exception as e:
        logger.error(f"Error getting vehicle status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vehicle status: {str(e)}"
        )


@app.get("/zones", response_model=List[ZoneInfo])
async def get_zones_info() -> List[ZoneInfo]:
    """
    Get information about all zones (for debugging).
    
    Returns:
        List of ZoneInfo with bounds and current vehicle counts
    """
    try:
        zones = get_zones()
        zone_info_list = []
        
        for zone in zones:
            vehicle_count = state_manager.get_zone_count(zone.zone_id)
            zone_info = ZoneInfo(
                zone_id=zone.zone_id,
                name=zone.name,
                bounds={
                    "min_lat": zone.min_lat,
                    "max_lat": zone.max_lat,
                    "min_lng": zone.min_lng,
                    "max_lng": zone.max_lng
                },
                vehicle_count=vehicle_count
            )
            zone_info_list.append(zone_info)
        
        return zone_info_list
        
    except Exception as e:
        logger.error(f"Error getting zones info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving zones: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with service status
    """
    return HealthResponse()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

