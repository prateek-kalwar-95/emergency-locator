from django.db import transaction
from django.utils import timezone
from typing import Tuple, Dict, Any, List

from locator.models import ServiceUnit, Incident
from locator.parser import parse_dataset, ParseError
from locator.algorithms import find_nearest_unit

# Domain-specific exceptions
class NoIncidentFound(Exception):
    """Raised when the specified incident ID cannot be found in the database."""
    pass

class NoAvailableUnits(Exception):
    """Raised when no available units match the requested emergency service type."""
    pass

class InvalidService(Exception):
    """Raised when the requested service type is not recognized."""
    pass


def handle_dataset_upload(file) -> Tuple[int, int, List[Dict[str, Any]]]:
    """
    Validates the uploaded file, parses it, purges existing units and dataset-sourced
    incidents, and inserts the new records within a database transaction.
    """
    # 1. Validate file extension and size (cap at 2MB)
    if not file.name.endswith('.txt'):
        raise ValueError("Invalid file format. Only plain text (.txt) files are supported.")

    # 2MB cap = 2 * 1024 * 1024 bytes
    if file.size > 2 * 1024 * 1024:
        raise ValueError("File size limit exceeded. Max allowed size is 2MB.")

    # 2. Decode content
    try:
        file_content = file.read().decode('utf-8')
    except Exception:
        raise ValueError("Unable to read file content. Ensure it is encoded in UTF-8.")

    # 3. Parse contents using the custom parser
    valid_units, valid_incidents, warnings = parse_dataset(file_content)

    # 4. Perform database operations within a transaction
    with transaction.atomic():
        # Clean up existing database-sourced records
        ServiceUnit.objects.all().delete()
        Incident.objects.filter(source='dataset').delete()

        # Create units
        units_to_create = [
            ServiceUnit(
                unit_id=u['unit_id'],
                unit_type=u['unit_type'],
                latitude=u['latitude'],
                longitude=u['longitude'],
                status=u['status']
            )
            for u in valid_units
        ]
        ServiceUnit.objects.bulk_create(units_to_create)

        # Create incidents
        incidents_to_create = [
            Incident(
                name=inc['name'],
                latitude=inc['latitude'],
                longitude=inc['longitude'],
                source='dataset'
            )
            for inc in valid_incidents
        ]
        Incident.objects.bulk_create(incidents_to_create)

    return len(valid_units), len(valid_incidents), warnings


def resolve_incident(payload: Dict[str, Any]) -> Tuple[float, float, str]:
    """
    Resolves the incident coordinates and label based on the input mode.
    
    Mode A: payload contains 'incident_id' (look up existing incident in database).
    Mode B: payload contains 'latitude' and 'longitude' (validate coordinates and save as a manual incident).
    """
    if 'incident_id' in payload and payload['incident_id'] is not None:
        try:
            incident_id = int(payload['incident_id'])
            incident = Incident.objects.get(id=incident_id)
            label = incident.name or f"Incident #{incident.id}"
            return incident.latitude, incident.longitude, label
        except (Incident.DoesNotExist, ValueError, TypeError):
            raise NoIncidentFound("The specified incident ID does not exist in the database.")
            
    # Mode B: Manual entry mode
    try:
        lat = float(payload.get('latitude'))
        lon = float(payload.get('longitude'))
    except (TypeError, ValueError):
        raise ValueError("Latitude and longitude must be valid numeric decimal coordinates.")

    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude ({lat}) must be in the range [-90, 90].")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude ({lon}) must be in the range [-180, 180].")

    # Generate custom name if manual input didn't specify one
    raw_name = payload.get('name', '').strip()
    if not raw_name:
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        name = f"Manual Incident {timestamp}"
    else:
        name = raw_name

    # Persist the manual incident so it remains in database history
    incident = Incident.objects.create(
        name=name,
        latitude=lat,
        longitude=lon,
        source='manual'
    )
    
    return incident.latitude, incident.longitude, incident.name


def get_nearest_unit_for_incident(
    lat: float, 
    lon: float, 
    service_type: str,
    incident_label: str
) -> Dict[str, Any]:
    """
    Finds the nearest available unit for the given coordinates and service type.
    """
    valid_services = {"Ambulance", "Fire", "Police", "Any"}
    if service_type not in valid_services:
        raise InvalidService(f"Invalid service type '{service_type}'. Must be Ambulance, Fire, Police, or Any.")

    nearest_unit, distance = find_nearest_unit(lat, lon, service_type)

    if nearest_unit is None:
        raise NoAvailableUnits(f"No available {service_type if service_type != 'Any' else ''} emergency units found.")

    # Friendly type names for JSON display
    friendly_type_names = {
        "Ambulance": "Ambulance",
        "Fire": "Fire Station",
        "Police": "Police Unit"
    }
    unit_type_display = friendly_type_names.get(nearest_unit.unit_type, nearest_unit.unit_type)

    return {
        "unit_id": nearest_unit.unit_id,
        "unit_type": unit_type_display,
        "latitude": nearest_unit.latitude,
        "longitude": nearest_unit.longitude,
        "distance_km": round(distance, 2),
        "status": nearest_unit.status,
        "incident": {
            "label": incident_label,
            "latitude": lat,
            "longitude": lon
        }
    }
