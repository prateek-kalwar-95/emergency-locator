# Intelligent Emergency Dispatch MVP

A Django web application designed to help emergency dispatch centers instantly identify the nearest available emergency service unit (Ambulance, Fire Station, or Police Vehicle) to an incident location. It utilizes an interactive Leaflet.js map, dynamic metric cards, and a custom implementation of the Haversine formula to compute great-circle distances.

---

## Technical Stack
- **Backend:** Python 3.12+, Django 5.0+, SQLite
- **Frontend:** HTML5, CSS3, Bootstrap 5, Leaflet.js, OpenStreetMap tiles, Vanilla Javascript (Fetch API)
- **External Geo Libraries:** None. Distance calculation (Haversine) and spatial indexing (KD-Tree) are coded manually from scratch in Python.

---

## Installation & Setup

Ensure you have Python 3.12+ installed. Run the following commands:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Navigate to the project root:**
   ```bash
   cd EmergencyLocator
   ```

3. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

5. Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## Dataset Format

The application accepts plain text (`.txt`) datasets to bulk-populate service units and incidents. Columns must be separated by commas, and the file must include the headers `# Units` and `# Incidents`.

### Example Dataset (`sample_data/sample_dataset.txt`)
```text
# Units
A1,Ambulance,22.5726,88.3639,Available
A2,Ambulance,22.5850,88.3820,Busy
F1,Fire,22.5650,88.3550,Available
P1,Police,22.5690,88.3600,Available

# Incidents
Hospital,22.5710,88.3605
School,22.5600,88.3520
```

- **Validation Rules:**
  - **Service Units:** `unit_id` must be unique. `unit_type` must be Ambulance, Fire, or Police (case-insensitive). `latitude` must be in `[-90, 90]`, `longitude` in `[-180, 180]`, and `status` in `Available`, `Busy`, or `Maintenance`.
  - **Incidents:** `name` must be non-empty. Coordinates must be in range.
  - Malformed lines do not cause the parser to fail. They are gathered in a warnings list, skipped, and displayed on the interface.

---

## Route Summary

- **`GET /`** - Home dashboard UI.
- **`POST /upload/`** - Uploads and parses the dataset. Overwrites prior service units and dataset-sourced incidents. Returns counts and parse warnings.
- **`GET /units/`** - Lists all units in the database as JSON.
- **`GET /incidents/`** - Lists all dataset-sourced incidents in the database as JSON.
- **`POST /find-nearest/`** - Calculates the closest available unit matching the criteria. Accepts coordinates or an incident ID.

---

## Manual-Entry / Map-Click Workflow

1. Toggle the incident location source to **Enter Coordinates**.
2. EITHER:
   - Click anywhere on the map: A red pin appears, and the latitude and longitude inputs are filled automatically.
   - Enter manual values in the **Latitude** and **Longitude** boxes: The pin on the map updates automatically.
3. The red pin is **draggable**. Dragging it updates the coordinate input boxes dynamically.
4. Select the desired service type and click **Find Nearest Unit** to view routing results.

---

## Known Limitations & Design Considerations

### 1. SQLite & Dataset Purging on Upload
Whenever a new dataset is uploaded, all previous service units and dataset-sourced incidents are deleted inside a single database transaction. This keeps the active working environment tidy. However, manually placed incident points are **preserved** (not deleted) to maintain session continuity for tests. Since SQLite handles transactions sequentially, rapid parallel uploads will lock the database temporarily.

### 2. Equidistant Tie-Breaking Rule
When searching for the nearest unit, if multiple units are equidistant (defined by a coordinate/distance threshold epsilon of `1e-6 km` or `1 millimeter`), the algorithm resolves the tie by returning the unit with the **lowest primary key** (first inserted). This ensures stable, deterministic outcome selection.

### 3. KD-Tree Spatial Indexing
To handle large datasets efficiently, the nearest-neighbor search utilizes a custom KD-Tree data structure instead of a linear scan. 
- The KD-Tree splits coordinates iteratively by latitude and longitude, pruning distant search branches in average $O(\log N)$ time.
- Haversine distance bounds are used accurately during pruning to account for the Earth's curvature.

### 4. Search History & Auditing
Every successful dispatch request is automatically recorded in the `SearchHistory` database model. This allows administrators to audit incidents (via the Django Admin panel) and track which service unit was dispatched, along with the precise distance calculation and timestamp.
