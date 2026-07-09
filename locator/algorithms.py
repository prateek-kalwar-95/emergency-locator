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


class KDTreeNode:
    def __init__(self, unit, left=None, right=None, axis=0):
        self.unit = unit
        self.left = left
        self.right = right
        self.axis = axis

def build_kdtree(units, depth=0):
    if not units:
        return None
    axis = depth % 2
    
    # Sort units based on the current axis (0 for lat, 1 for lon)
    if axis == 0:
        units.sort(key=lambda u: (u.latitude, u.id))
    else:
        units.sort(key=lambda u: (u.longitude, u.id))
        
    median = len(units) // 2
    return KDTreeNode(
        unit=units[median],
        left=build_kdtree(units[:median], depth + 1),
        right=build_kdtree(units[median + 1:], depth + 1),
        axis=axis
    )

def find_nearest_unit(
    incident_lat: float, 
    incident_lon: float, 
    service_type: str
) -> Tuple[Optional[ServiceUnit], float]:
    """
    Scans the database for Available service units and returns the nearest one 
    to the incident location using KD-Tree spatial indexing with Haversine distance.
    """
    queryset = ServiceUnit.objects.filter(status='Available')

    if service_type != "Any":
        queryset = queryset.filter(unit_type=service_type)

    units = list(queryset)
    if not units:
        return None, float('inf')

    # Build KD-Tree from available units
    root = build_kdtree(units)

    best_unit: Optional[ServiceUnit] = None
    min_distance = float('inf')
    epsilon = 1e-6  # 1 millimeter epsilon in km

    def search_kdtree(node):
        nonlocal best_unit, min_distance
        if node is None:
            return
        
        # Calculate distance to current node
        dist = haversine(incident_lat, incident_lon, node.unit.latitude, node.unit.longitude)
        
        if dist < min_distance - epsilon:
            min_distance = dist
            best_unit = node.unit
        elif abs(dist - min_distance) < epsilon:
            if best_unit is None or node.unit.id < best_unit.id:
                best_unit = node.unit
                
        # Determine which branch to search first
        if node.axis == 0:
            diff = incident_lat - node.unit.latitude
            hyperplane_dist = haversine(incident_lat, incident_lon, node.unit.latitude, incident_lon)
        else:
            diff = incident_lon - node.unit.longitude
            hyperplane_dist = haversine(incident_lat, incident_lon, incident_lat, node.unit.longitude)
            
        first, second = (node.left, node.right) if diff < 0 else (node.right, node.left)
        
        search_kdtree(first)
        
        # If the hypersphere intersects the hyperplane, check the other side
        if hyperplane_dist < min_distance:
            search_kdtree(second)

    search_kdtree(root)
    return best_unit, min_distance
