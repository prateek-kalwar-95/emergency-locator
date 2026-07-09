import math
from typing import Tuple, Optional
from locator.models import ServiceUnit

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the great-circle distance between two points on the Earth's surface
    using the Haversine formula.
    
    Formula:
      a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
      c = 2 * asin(√a)
      d = R * c
    
    Where:
      R is the radius of the Earth (6371 km).
      Coordinates must be converted to radians first.
    
    Returns:
      Distance in kilometers (float).
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert coordinates from decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine calculation
    a = (math.sin(dlat / 2.0) ** 2) + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * (math.sin(dlon / 2.0) ** 2)
    
    c = 2.0 * math.asin(math.sqrt(a))
    
    return R * c


def find_nearest_unit(
    incident_lat: float, 
    incident_lon: float, 
    service_type: str
) -> Tuple[Optional[ServiceUnit], float]:
    """
    Scans the database for Available service units and returns the nearest one 
    to the incident location based on the Haversine distance.
    
    Rules:
      - Ignores units with 'Busy' or 'Maintenance' status.
      - If service_type is 'Any', searches all Available units.
      - Otherwise filters to Available units matching service_type.
      - Tie-break: If multiple units are within an epsilon of 1e-6 km (1 millimeter),
        we prefer the one with the lowest primary key (first inserted) by utilizing
        increasing primary key order during candidate evaluation.
        
    Returns:
      Tuple of (nearest_unit_object, distance_km). 
      If no unit is found, returns (None, float('inf')).
    """
    # Order by ID to ensure stable tie-breaker (lowest primary key / first inserted)
    queryset = ServiceUnit.objects.filter(status='Available').order_by('id')

    if service_type != "Any":
        queryset = queryset.filter(unit_type=service_type)

    best_unit: Optional[ServiceUnit] = None
    min_distance = float('inf')
    epsilon = 1e-6  # 1 millimeter epsilon in km

    for unit in queryset:
        dist = haversine(incident_lat, incident_lon, unit.latitude, unit.longitude)
        
        # If the unit is strictly closer (by at least epsilon), update best_unit.
        # If the distance is within epsilon, they are considered equidistant.
        # Since the queryset is sorted by primary key asc, the earlier unit (with lower ID)
        # is already best_unit, so we do not overwrite it.
        if dist < min_distance - epsilon:
            min_distance = dist
            best_unit = unit
        elif abs(dist - min_distance) < epsilon:
            # Equidistant - keep the unit with the lower primary key
            pass

    return best_unit, min_distance
