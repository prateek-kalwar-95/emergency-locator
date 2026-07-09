import re
from typing import List, Tuple, Dict, Any

class ParseError(Exception):
    """Custom exception raised when the dataset parsing fails critically."""
    pass

def parse_dataset(file_content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parses the dataset text content and returns (valid_units, valid_incidents, warnings).
    
    Validates each row and gathers warnings for malformed entries.
    Raises ParseError on critical formatting errors:
      - Missing both `# Units` and `# Incidents` sections.
      - A section exists but contains zero valid rows.
      - File content is empty.
    """
    if not file_content.strip():
        raise ParseError("The uploaded file is empty.")

    lines = file_content.splitlines()
    
    valid_units: List[Dict[str, Any]] = []
    valid_incidents: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    has_units_header = False
    has_incidents_header = False
    
    current_section = None  # can be 'units' or 'incidents'

    # Valid unit types and statuses (case-insensitive mapping to normalized Title Case)
    valid_unit_types = {"ambulance": "Ambulance", "fire": "Fire", "police": "Police"}
    valid_statuses = {"available": "Available", "busy": "Busy", "maintenance": "Maintenance"}

    for line_idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Check for section headers
        if line.lower() == "# units":
            has_units_header = True
            current_section = "units"
            continue
        elif line.lower() == "# incidents":
            has_incidents_header = True
            current_section = "incidents"
            continue
            
        # Skip other comments
        if line.startswith("#"):
            continue

        # If we encounter data before any section header, treat it as a warning or skip
        if current_section is None:
            warnings.append({
                "line": line_idx,
                "content": raw_line,
                "reason": "Data row encountered before any section header (# Units or # Incidents)."
            })
            continue

        parts = [p.strip() for p in line.split(",")]

        if current_section == "units":
            # Expecting 5 columns: unit_id, unit_type, latitude, longitude, status
            if len(parts) != 5:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Invalid column count for Unit. Expected 5, got {len(parts)}."
                })
                continue
            
            unit_id, raw_type, raw_lat, raw_lon, raw_status = parts
            
            if not unit_id:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": "Unit ID cannot be empty."
                })
                continue

            # Validate type
            norm_type = valid_unit_types.get(raw_type.lower())
            if not norm_type:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Invalid unit type '{raw_type}'. Must be Ambulance, Fire, or Police."
                })
                continue

            # Validate coordinates
            try:
                lat = float(raw_lat)
                lon = float(raw_lon)
            except ValueError:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Invalid coordinates '{raw_lat}, {raw_lon}'. Must be numeric."
                })
                continue

            if not (-90.0 <= lat <= 90.0):
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Latitude {lat} out of range [-90, 90]."
                })
                continue

            if not (-180.0 <= lon <= 180.0):
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Longitude {lon} out of range [-180, 180]."
                })
                continue

            # Validate status
            norm_status = valid_statuses.get(raw_status.lower())
            if not norm_status:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Invalid status '{raw_status}'. Must be Available, Busy, or Maintenance."
                })
                continue

            valid_units.append({
                "unit_id": unit_id,
                "unit_type": norm_type,
                "latitude": lat,
                "longitude": lon,
                "status": norm_status
            })

        elif current_section == "incidents":
            # Expecting 3 columns: name, latitude, longitude
            if len(parts) != 3:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Invalid column count for Incident. Expected 3, got {len(parts)}."
                })
                continue

            name, raw_lat, raw_lon = parts

            if not name:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": "Incident name cannot be empty."
                })
                continue

            # Validate coordinates
            try:
                lat = float(raw_lat)
                lon = float(raw_lon)
            except ValueError:
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Invalid coordinates '{raw_lat}, {raw_lon}'. Must be numeric."
                })
                continue

            if not (-90.0 <= lat <= 90.0):
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Latitude {lat} out of range [-90, 90]."
                })
                continue

            if not (-180.0 <= lon <= 180.0):
                warnings.append({
                    "line": line_idx,
                    "content": raw_line,
                    "reason": f"Longitude {lon} out of range [-180, 180]."
                })
                continue

            valid_incidents.append({
                "name": name,
                "latitude": lat,
                "longitude": lon
            })

    # Critical structure validation
    if not has_units_header and not has_incidents_header:
        raise ParseError("Missing both '# Units' and '# Incidents' section headers.")
    if not has_units_header:
        raise ParseError("Missing '# Units' section header.")
    if not has_incidents_header:
        raise ParseError("Missing '# Incidents' section header.")

    # Section-level content checks
    if len(valid_units) == 0:
        raise ParseError("The '# Units' section contains zero valid service units.")
    if len(valid_incidents) == 0:
        raise ParseError("The '# Incidents' section contains zero valid incidents.")

    return valid_units, valid_incidents, warnings
