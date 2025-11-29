# Geofence Event Processing Service

A microservice for processing GPS location events and detecting zone entry/exit transitions in real-time.

## Overview

This service provides HTTP endpoints for:
- Ingesting GPS location events from vehicles
- Detecting when vehicles enter, exit, or change geofence zones
- Tracking vehicle state and zone occupancy
- Querying vehicle status and zone information

## Architecture

### Components

1. **FastAPI Application** (`app/main.py`)
   - RESTful HTTP endpoints
   - Request validation using Pydantic models
   - Error handling and logging

2. **State Management** (`app/state.py`)
   - In-memory dictionaries for vehicle tracking
   - Vehicle state with transition history
   - Zone occupancy counts

3. **Zone Detection Logic** (`app/logic.py`)
   - GPS coordinate normalization
   - Zone containment checks
   - Transition detection (ENTER/EXIT/CHANGE)

4. **Zone Loading** (`app/zones.py`)
   - JSON-based zone configuration
   - Rectangular zone definitions
   - Default zones fallback

5. **Data Models** (`app/models.py`)
   - Pydantic models for type safety
   - Request/response schemas
   - Validation rules

## API Endpoints

### POST /events/location
Process a GPS location event from a vehicle.

**Request Body:**
```json
{
  "vehicle_id": "vehicle_123",
  "latitude": "37.7749",
  "longitude": "-122.4194",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response:**
```json
{
  "vehicle_id": "vehicle_123",
  "current_zone": "zone_1",
  "transition": "ENTER",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /vehicles/{vehicleId}/status
Get current status of a vehicle including zone, location, and transition history.

**Response:**
```json
{
  "vehicle_id": "vehicle_123",
  "current_zone": "zone_1",
  "last_update": "2024-01-15T10:30:00Z",
  "last_latitude": 37.7749,
  "last_longitude": -122.4194,
  "transition_history": [
    {
      "transition": "ENTER",
      "from_zone": null,
      "to_zone": "zone_1",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### GET /zones
Get information about all configured zones (for debugging).

**Response:**
```json
[
  {
    "zone_id": "zone_1",
    "name": "Downtown",
    "bounds": {
      "min_lat": 37.7749,
      "max_lat": 37.7849,
      "min_lng": -122.4194,
      "max_lng": -122.4094
    },
    "vehicle_count": 5
  }
]
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "geofence_event_processing",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Assumptions

1. **Zone Format**: Zones are rectangular (axis-aligned bounding boxes) defined by min/max latitude and longitude.

2. **GPS Normalization**: Invalid GPS values (`D$Q`, `-`, empty strings, `NaN`, etc.) are normalized to `0.0`, which places vehicles outside all zones.

3. **Coordinate Validation**: Coordinates outside the valid GPS range (-180 to 180) are normalized to `0.0`.

4. **State Management**: State is stored in-memory and will be lost on service restart. This is suitable for development/testing but not production without persistence.

5. **Transition Detection**:
   - `ENTER`: Vehicle moves from outside all zones into a zone
   - `EXIT`: Vehicle moves from a zone to outside all zones
   - `CHANGE`: Vehicle moves from one zone directly to another zone

6. **Timestamp Handling**: If not provided, timestamps default to current UTC time.

7. **Zone File Location**: `zones.json` is expected in the project root directory (`geofence_service/zones.json`).

## Error Handling

- **Invalid Coordinates**: Automatically normalized to `0.0` with warning logs
- **Missing Zones File**: Falls back to default zones with warning
- **Invalid JSON**: Returns 500 error with descriptive message
- **Missing Vehicle**: Vehicle state is created on first access
- **Global Exception Handler**: Catches unhandled exceptions and returns 500 error

## Running the Service

### Installation

```bash
cd geofence_service
pip install -r requirements.txt
```

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Running Tests

```bash
pytest tests/ -v
```

## Scalability Notes

### Current Limitations

1. **In-Memory State**: State is not persisted and is lost on restart
2. **Single Process**: Not designed for horizontal scaling (shared state)
3. **No Database**: No persistent storage for events or state
4. **Synchronous Processing**: Events are processed synchronously

### Production Improvements

If more time was available, I would implement:

1. **Persistent Storage**:
   - Redis for distributed state management
   - PostgreSQL for event history and analytics
   - Message queue (RabbitMQ/Kafka) for event ingestion

2. **Horizontal Scaling**:
   - Stateless API servers behind load balancer
   - Shared state via Redis or database
   - Event streaming for high throughput

3. **Advanced Features**:
   - Circular/polygonal zone support
   - Geospatial indexing (PostGIS, Redis Geo)
   - Zone hierarchy and nested zones
   - Time-based zone rules
   - Webhook notifications for transitions

4. **Monitoring & Observability**:
   - Prometheus metrics
   - Distributed tracing (OpenTelemetry)
   - Structured logging with correlation IDs
   - Health checks with dependencies

5. **Performance Optimizations**:
   - Spatial indexing (R-tree, quadtree)
   - Batch event processing
   - Caching frequently accessed zones
   - Async event processing

6. **Reliability**:
   - Circuit breakers for external dependencies
   - Retry logic with exponential backoff
   - Dead letter queues for failed events
   - State snapshots and recovery

7. **Security**:
   - API authentication (JWT, OAuth)
   - Rate limiting
   - Input sanitization
   - HTTPS/TLS

## Example Usage

```python
import requests

# Post a location event
response = requests.post("http://localhost:8000/events/location", json={
    "vehicle_id": "vehicle_123",
    "latitude": "37.78",
    "longitude": "-122.41"
})
print(response.json())

# Get vehicle status
response = requests.get("http://localhost:8000/vehicles/vehicle_123/status")
print(response.json())

# Get all zones
response = requests.get("http://localhost:8000/zones")
print(response.json())
```

## Testing

Unit tests cover:
- Coordinate normalization
- Zone containment logic
- Transition detection (ENTER/EXIT/CHANGE)
- Invalid GPS value handling

Run tests with:
```bash
pytest tests/test_logic.py -v
```

