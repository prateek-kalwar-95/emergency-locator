// Emergency Response Locator - Client Application Script

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // State Variables
    // ----------------------------------------------------
    let map = null;
    
    // Layers
    let unitsGroup = L.layerGroup();
    let incidentsGroup = L.layerGroup();
    let searchGroup = L.layerGroup();
    
    // Draggable Manual Incident Marker
    let manualMarker = null;

    // Default map center (Kolkata)
    const KOLKATA_CENTER = [22.5726, 88.3639];
    const DEFAULT_ZOOM = 13;

    // ----------------------------------------------------
    // Initialize Map
    // ----------------------------------------------------
    function initMap() {
        map = L.map('map').setView(KOLKATA_CENTER, DEFAULT_ZOOM);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Add Layer Groups to Map
        unitsGroup.addTo(map);
        incidentsGroup.addTo(map);
        searchGroup.addTo(map);

        // Add click listener for Manual Coordinates Setting
        map.on('click', (e) => {
            const sourceMode = document.querySelector('input[name="incident_source"]:checked').value;
            if (sourceMode === 'manual') {
                updateManualCoords(e.latlng.lat, e.latlng.lng);
            }
        });
    }

    // ----------------------------------------------------
    // Icon Builders (Rich Visual Aesthetics)
    // ----------------------------------------------------
    function getUnitIcon(type, status) {
        let color = '#4361ee'; // default blue
        let iconClass = 'bi-shield-fill-exclamation';
        
        if (type === 'Ambulance') {
            color = '#10b981'; // green
            iconClass = 'bi-truck-front-fill';
        } else if (type === 'Fire' || type === 'Fire Station') {
            color = '#f97316'; // orange
            iconClass = 'bi-fire';
        } else if (type === 'Police' || type === 'Police Unit') {
            color = '#3b82f6'; // light blue
            iconClass = 'bi-shield-shaded';
        }

        let opacity = 1.0;
        let grayscale = '';
        if (status === 'Busy' || status === 'Maintenance') {
            opacity = 0.45;
            grayscale = 'filter: grayscale(60%)';
        }

        const html = `
            <div style="
                background-color: ${color};
                width: 34px;
                height: 34px;
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 3px 8px rgba(0,0,0,0.25);
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: ${opacity};
                ${grayscale};
            ">
                <i class="bi ${iconClass}" style="color: white; font-size: 16px;"></i>
            </div>
        `;

        return L.divIcon({
            html: html,
            className: 'custom-unit-marker',
            iconSize: [34, 34],
            iconAnchor: [17, 17]
        });
    }

    function getDatasetIncidentIcon() {
        const html = `
            <div style="
                background-color: #6c757d;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <i class="bi bi-geo-alt-fill" style="color: white; font-size: 12px;"></i>
            </div>
        `;
        return L.divIcon({
            html: html,
            className: 'custom-incident-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
    }

    function getActiveIncidentIcon() {
        const html = `
            <div class="animate-pulse" style="
                background-color: #ef233c;
                width: 38px;
                height: 38px;
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 0 10px rgba(239, 35, 60, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <i class="bi bi-geo-alt-fill" style="color: white; font-size: 18px;"></i>
            </div>
        `;
        return L.divIcon({
            html: html,
            className: 'active-incident-marker',
            iconSize: [38, 38],
            iconAnchor: [18, 18]
        });
    }

    function getHighlightedUnitIcon(type) {
        let color = '#4361ee';
        let iconClass = 'bi-shield-shaded';
        
        if (type === 'Ambulance') {
            color = '#10b981';
            iconClass = 'bi-truck-front-fill';
        } else if (type === 'Fire' || type === 'Fire Station') {
            color = '#f97316';
            iconClass = 'bi-fire';
        } else if (type === 'Police' || type === 'Police Unit') {
            color = '#3b82f6';
            iconClass = 'bi-shield-shaded';
        }

        const html = `
            <div class="animate-pulse" style="
                background-color: ${color};
                width: 44px;
                height: 44px;
                border-radius: 50%;
                border: 3px solid #ffffff;
                box-shadow: 0 0 18px rgba(0,0,0,0.4);
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <i class="bi ${iconClass}" style="color: white; font-size: 20px;"></i>
            </div>
        `;
        return L.divIcon({
            html: html,
            className: 'highlighted-unit-marker',
            iconSize: [44, 44],
            iconAnchor: [22, 22]
        });
    }

    // ----------------------------------------------------
    // Update Manual Incident Coordinates (Inputs & Draggable Marker)
    // ----------------------------------------------------
    function updateManualCoords(lat, lon, focusMap = false) {
        const latVal = parseFloat(lat).toFixed(6);
        const lonVal = parseFloat(lon).toFixed(6);

        document.getElementById('manual-lat').value = latVal;
        document.getElementById('manual-lon').value = lonVal;

        if (manualMarker) {
            manualMarker.setLatLng([lat, lon]);
        } else {
            const html = `
                <div style="
                    background-color: #ef233c;
                    width: 28px;
                    height: 28px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <i class="bi bi-pin-angle-fill" style="color: white; font-size: 14px;"></i>
                </div>
            `;
            const manualPinIcon = L.divIcon({
                html: html,
                className: 'manual-pin-icon',
                iconSize: [28, 28],
                iconAnchor: [14, 28] // anchor bottom center
            });

            manualMarker = L.marker([lat, lon], {
                draggable: true,
                icon: manualPinIcon
            }).addTo(map);

            manualMarker.on('dragend', (event) => {
                const marker = event.target;
                const position = marker.getLatLng();
                updateManualCoords(position.lat, position.lng);
            });
        }

        if (focusMap) {
            map.setView([lat, lon], DEFAULT_ZOOM);
        }
    }

    function removeManualMarker() {
        if (manualMarker) {
            map.removeLayer(manualMarker);
            manualMarker = null;
        }
    }

    // ----------------------------------------------------
    // Toggle Source Input Modes
    // ----------------------------------------------------
    const sourceDataset = document.getElementById('source-dataset');
    const sourceManual = document.getElementById('source-manual');
    const datasetGroup = document.getElementById('dataset-group');
    const manualGroup = document.getElementById('manual-group');

    function toggleSource() {
        if (sourceDataset.checked) {
            datasetGroup.classList.remove('d-none');
            manualGroup.classList.add('d-none');
            removeManualMarker();
        } else {
            datasetGroup.classList.add('d-none');
            manualGroup.classList.remove('d-none');
            
            // Set initial coordinates if manual input is empty
            const latInput = document.getElementById('manual-lat').value;
            const lonInput = document.getElementById('manual-lon').value;
            if (!latInput || !lonInput) {
                updateManualCoords(KOLKATA_CENTER[0], KOLKATA_CENTER[1], true);
            } else {
                updateManualCoords(latInput, lonInput, true);
            }
        }
    }

    sourceDataset.addEventListener('change', toggleSource);
    sourceManual.addEventListener('change', toggleSource);

    // Sync typing coordinates manual inputs with the marker
    document.getElementById('manual-lat').addEventListener('change', syncManualCoordsInput);
    document.getElementById('manual-lon').addEventListener('change', syncManualCoordsInput);

    function syncManualCoordsInput() {
        const lat = parseFloat(document.getElementById('manual-lat').value);
        const lon = parseFloat(document.getElementById('manual-lon').value);
        if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
            updateManualCoords(lat, lon, true);
        }
    }

    // ----------------------------------------------------
    // API Requests & Refresh Content
    // ----------------------------------------------------
    
    // Fetch and redraw units on map
    async function loadUnits() {
        try {
            const res = await fetch(window.LOCATOR_URLS.units);
            if (!res.ok) throw new Error("Failed to load units list.");
            const units = await res.json();
            
            unitsGroup.clearLayers();
            
            units.forEach(u => {
                const marker = L.marker([u.latitude, u.longitude], {
                    icon: getUnitIcon(u.unit_type, u.status)
                });
                
                const popupContent = `
                    <div class="font-inter">
                        <h6 class="fw-bold mb-1">${u.unit_id}</h6>
                        <div class="small mb-1"><span class="text-muted">Type:</span> ${u.unit_type}</div>
                        <div class="small mb-1"><span class="text-muted">Status:</span> 
                            <span class="badge ${u.status === 'Available' ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'}">${u.status}</span>
                        </div>
                        <div class="small font-monospace">${u.latitude.toFixed(5)}, ${u.longitude.toFixed(5)}</div>
                    </div>
                `;
                marker.bindPopup(popupContent);
                unitsGroup.addLayer(marker);
            });
        } catch (err) {
            console.error("Units loading error:", err);
        }
    }

    // Fetch and populate incidents list
    async function loadIncidents() {
        try {
            const res = await fetch(window.LOCATOR_URLS.incidents);
            if (!res.ok) throw new Error("Failed to load incidents list.");
            const incidents = await res.json();

            // Populate dropdown
            const selectEl = document.getElementById('incident-select');
            selectEl.innerHTML = '<option value="">-- Choose Incident --</option>';
            
            incidentsGroup.clearLayers();

            incidents.forEach(inc => {
                // Dropdown entry
                const opt = document.createElement('option');
                opt.value = inc.id;
                opt.textContent = `${inc.name} (${inc.latitude.toFixed(4)}, ${inc.longitude.toFixed(4)})`;
                selectEl.appendChild(opt);

                // Map marker
                const marker = L.marker([inc.latitude, inc.longitude], {
                    icon: getDatasetIncidentIcon()
                });
                
                const popupContent = `
                    <div class="font-inter">
                        <h6 class="fw-bold mb-1">${inc.name}</h6>
                        <div class="small mb-1 text-muted">Dataset Sourced Incident</div>
                        <div class="small font-monospace">${inc.latitude.toFixed(5)}, ${inc.longitude.toFixed(5)}</div>
                    </div>
                `;
                marker.bindPopup(popupContent);
                incidentsGroup.addLayer(marker);
            });
        } catch (err) {
            console.error("Incidents loading error:", err);
        }
    }

    // Helper to get CSRF token value
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // ----------------------------------------------------
    // Dataset Upload AJAX
    // ----------------------------------------------------
    const uploadForm = document.getElementById('upload-form');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadSpinner = document.getElementById('upload-spinner');
    const uploadAlert = document.getElementById('upload-alert');
    const uploadAlertMsg = document.getElementById('upload-alert-message');
    const warningsContainer = document.getElementById('warnings-container');
    const warningsList = document.getElementById('warnings-list');

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI Reset
        uploadAlert.classList.add('d-none');
        warningsContainer.classList.add('d-none');
        warningsList.innerHTML = '';
        
        uploadBtn.disabled = true;
        uploadSpinner.classList.remove('d-none');

        const formData = new FormData(uploadForm);

        try {
            const res = await fetch(window.LOCATOR_URLS.upload, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || "An error occurred during dataset processing.");
            }

            // Success
            uploadAlert.className = "alert alert-success alert-dismissible mt-3";
            uploadAlertMsg.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>Dataset parsed successfully! Added <strong>${data.units_count}</strong> units and <strong>${data.incidents_count}</strong> incidents.`;
            uploadAlert.classList.remove('d-none');

            // Reset File input
            uploadForm.reset();

            // Populate dashboard metrics
            if (data.stats) {
                document.getElementById('stat-ambulances').textContent = data.stats.ambulances;
                document.getElementById('stat-fire').textContent = data.stats.fire_stations;
                document.getElementById('stat-police').textContent = data.stats.police_units;
                document.getElementById('stat-available').textContent = data.stats.available_units;
                document.getElementById('stat-non-available').textContent = data.stats.non_available_units;
                document.getElementById('stat-incidents').textContent = data.stats.dataset_incidents;
            }

            // Parse warnings
            if (data.warnings && data.warnings.length > 0) {
                warningsContainer.classList.remove('d-none');
                data.warnings.forEach(warn => {
                    const el = document.createElement('div');
                    el.className = 'py-1 border-bottom border-warning-subtle';
                    el.innerHTML = `<strong>Line ${warn.line}:</strong> <code class="text-danger">${escapeHtml(warn.content)}</code> - ${warn.reason}`;
                    warningsList.appendChild(el);
                });
            }

            // Reload records
            await loadUnits();
            await loadIncidents();
            
            // Clear previous search outcomes
            searchGroup.clearLayers();
            document.getElementById('result-card').classList.add('d-none');

        } catch (err) {
            uploadAlert.className = "alert alert-danger alert-dismissible mt-3";
            uploadAlertMsg.innerHTML = `<i class="bi bi-exclamation-octagon-fill me-2"></i>${err.message}`;
            uploadAlert.classList.remove('d-none');
        } finally {
            uploadBtn.disabled = false;
            uploadSpinner.classList.add('d-none');
        }
    });

    function escapeHtml(str) {
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // ----------------------------------------------------
    // Find Nearest Unit AJAX
    // ----------------------------------------------------
    const searchForm = document.getElementById('search-form');
    const searchBtn = document.getElementById('search-btn');
    const searchSpinner = document.getElementById('search-spinner');
    const searchAlert = document.getElementById('search-alert');
    const resultCard = document.getElementById('result-card');

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI Reset
        searchAlert.classList.add('d-none');
        resultCard.classList.add('d-none');
        searchGroup.clearLayers();

        const sourceMode = document.querySelector('input[name="incident_source"]:checked').value;
        const serviceType = document.getElementById('service-select').value;
        
        let payload = { service: serviceType };

        // Client-side validations
        if (sourceMode === 'dataset') {
            const selectEl = document.getElementById('incident-select');
            const incidentId = selectEl.value;
            if (!incidentId) {
                showSearchError("Please select a target incident location from the dropdown menu.");
                return;
            }
            payload.incident_id = incidentId;
        } else {
            // Manual validation
            const name = document.getElementById('manual-name').value;
            const latRaw = document.getElementById('manual-lat').value;
            const lonRaw = document.getElementById('manual-lon').value;

            if (!latRaw || !lonRaw) {
                showSearchError("Please enter valid decimal coordinates for the incident.");
                return;
            }

            const lat = parseFloat(latRaw);
            const lon = parseFloat(lonRaw);

            if (isNaN(lat) || lat < -90 || lat > 90) {
                showSearchError("Latitude must be a valid number between -90 and 90.");
                return;
            }
            if (isNaN(lon) || lon < -180 || lon > 180) {
                showSearchError("Longitude must be a valid number between -180 and 180.");
                return;
            }

            payload.latitude = lat;
            payload.longitude = lon;
            payload.name = name;
        }

        // Send request
        searchBtn.disabled = true;
        searchSpinner.classList.remove('d-none');

        try {
            const res = await fetch(window.LOCATOR_URLS.findNearest, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || "Server failed to locate the nearest service unit.");
            }

            // Bind result card text
            document.getElementById('res-unit-id').textContent = data.unit_id;
            document.getElementById('res-unit-type').textContent = data.unit_type;
            document.getElementById('res-unit-coords').textContent = `${data.latitude.toFixed(6)}, ${data.longitude.toFixed(6)}`;
            document.getElementById('res-unit-status').textContent = data.status;
            document.getElementById('res-distance').textContent = `${data.distance_km.toFixed(2)} km`;
            document.getElementById('res-incident-label').textContent = `${data.incident.label} (${data.incident.latitude.toFixed(6)}, ${data.incident.longitude.toFixed(6)})`;

            resultCard.classList.remove('d-none');

            // Draw on Leaflet Map
            plotSearchResult(data);

        } catch (err) {
            showSearchError(err.message);
        } finally {
            searchBtn.disabled = false;
            searchSpinner.classList.add('d-none');
        }
    });

    function showSearchError(message) {
        searchAlert.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i> ${message}`;
        searchAlert.classList.remove('d-none');
    }

    // Plots the dispatched unit, target incident, polyline path and focus zoom bounds
    function plotSearchResult(data) {
        const incidentCoords = [data.incident.latitude, data.incident.longitude];
        const unitCoords = [data.latitude, data.longitude];

        // 1. Incident Marker (Red Pin)
        const incidentMarker = L.marker(incidentCoords, {
            icon: getActiveIncidentIcon()
        });
        incidentMarker.bindPopup(`
            <div class="font-inter">
                <span class="badge bg-danger text-white mb-1">Target Incident</span>
                <h6 class="fw-bold mb-1">${data.incident.label}</h6>
                <div class="small font-monospace">${data.incident.latitude.toFixed(5)}, ${data.incident.longitude.toFixed(5)}</div>
            </div>
        `).addTo(searchGroup);

        // 2. Nearest Unit Marker (Blue Highlighted)
        const unitMarker = L.marker(unitCoords, {
            icon: getHighlightedUnitIcon(data.unit_type)
        });
        unitMarker.bindPopup(`
            <div class="font-inter">
                <span class="badge bg-primary text-white mb-1">Nearest Responder</span>
                <h6 class="fw-bold mb-1">${data.unit_id}</h6>
                <div class="small mb-1"><span class="text-muted">Type:</span> ${data.unit_type}</div>
                <div class="small mb-1"><span class="text-muted">Distance:</span> <strong>${data.distance_km.toFixed(2)} km</strong></div>
                <div class="small font-monospace">${data.latitude.toFixed(5)}, ${data.longitude.toFixed(5)}</div>
            </div>
        `).addTo(searchGroup);

        // 3. Draw connection line
        const connectionLine = L.polyline([incidentCoords, unitCoords], {
            color: '#4361ee',
            weight: 4,
            dashArray: '8, 8',
            opacity: 0.85
        }).addTo(searchGroup);

        // Fit map bounds
        const bounds = L.latLngBounds([incidentCoords, unitCoords]);
        map.fitBounds(bounds, { padding: [50, 50] });

        // Auto trigger popup
        unitMarker.openPopup();
    }

    // ----------------------------------------------------
    // App Bootstrap Execution
    // ----------------------------------------------------
    initMap();
    loadUnits();
    loadIncidents();
});
