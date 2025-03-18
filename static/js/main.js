// Initialize the map
let map = L.map('map').setView([40.7128, -74.0060], 11); // NYC coordinates

// Add OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);

// Variables to store markers and heatmap layer
let fromMarker = null;
let toMarker = null;
let routeLine = null;
let heatmapLayer = null;
let accidentMarkers = [];

// Initialize charts
let timeSeriesChart = null;
let factorsChart = null;
let timeOfDayChart = null;
let boroughChart = null;
let severityChart = null;
let dayOfWeekChart = null;

// Function to load data summary and initialize dashboard
function loadDataSummary() {
    showLoading();
    
    fetch('/api/data-summary')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        // Update summary statistics
        document.getElementById('total-accidents').textContent = data.total_accidents.toLocaleString();
        document.getElementById('total-injuries').textContent = data.total_injured.toLocaleString();
        document.getElementById('total-fatalities').textContent = data.total_killed.toLocaleString();
        
        // Initialize dashboard charts
        initializeTimeSeriesChart(data.time_series_data);
        initializeFactorsChart(data.top_factors);
        initializeTimeOfDayChart(data.time_of_day_counts);
        initializeBoroughChart(data.borough_counts);
        initializeSeverityChart(data.severity_distribution);
        initializeDayOfWeekChart(data.day_of_week_counts);
        
        // Load additional trend data
        loadAccidentTrends();
    })
    .catch(error => {
        hideLoading();
        console.error('Error loading data summary:', error);
    });
}

// Function to load accident trends data
function loadAccidentTrends() {
    fetch('/api/accident-trends')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Update charts with additional data if needed
        console.log("Loaded accident trends data:", data);
    })
    .catch(error => {
        console.error('Error loading accident trends:', error);
    });
}

// Function to geocode an address (convert address to coordinates)
// For simplicity, we'll use a mock function since we don't have a geocoding API key
function geocodeAddress(address) {
    return new Promise((resolve, reject) => {
        // For demo purposes, we'll use hardcoded coordinates for some NYC locations
        const locations = {
            'brooklyn': [40.6782, -73.9442],
            'manhattan': [40.7831, -73.9712],
            'queens': [40.7282, -73.7949],
            'bronx': [40.8448, -73.8648],
            'staten island': [40.5795, -74.1502],
            'times square': [40.7580, -73.9855],
            'central park': [40.7812, -73.9665],
            'prospect park': [40.6602, -73.9690],
            'jfk airport': [40.6413, -73.7781],
            'laguardia airport': [40.7769, -73.8740]
        };
        
        // Check if the address matches any of our hardcoded locations
        const lowercaseAddress = address.toLowerCase();
        for (const [key, value] of Object.entries(locations)) {
            if (lowercaseAddress.includes(key)) {
                resolve(value);
                return;
            }
        }
        
        // If no match, use a default location (Brooklyn)
        resolve([40.6782, -73.9442]);
    });
}

// Function to clear all markers and layers
function clearMap() {
    // Remove markers
    if (fromMarker) map.removeLayer(fromMarker);
    if (toMarker) map.removeLayer(toMarker);
    if (routeLine) map.removeLayer(routeLine);
    
    // Remove heatmap
    if (heatmapLayer) map.removeLayer(heatmapLayer);
    
    // Remove accident markers
    accidentMarkers.forEach(marker => map.removeLayer(marker));
    accidentMarkers = [];
}

// Function to analyze the route and display results
function analyzeRoute() {
    const fromLocation = document.getElementById('from-location').value;
    const toLocation = document.getElementById('to-location').value;
    
    if (!fromLocation || !toLocation) {
        alert('Please enter both starting and destination locations');
        return;
    }
    
    // Clear previous markers and layers
    clearMap();
    
    // Show loading state
    showLoading();
    document.getElementById('analyze-btn').textContent = 'Analyzing...';
    
    // Geocode the addresses
    Promise.all([
        geocodeAddress(fromLocation),
        geocodeAddress(toLocation)
    ])
    .then(([fromCoords, toCoords]) => {
        // Add markers for from and to locations
        fromMarker = L.marker(fromCoords, { 
            title: 'From: ' + fromLocation,
            icon: L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color:#3498db;color:white;border-radius:50%;width:30px;height:30px;display:flex;justify-content:center;align-items:center;box-shadow:0 0 10px rgba(0,0,0,0.5);"><i class="fas fa-map-marker-alt"></i></div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        })
        .addTo(map)
        .bindPopup('From: ' + fromLocation);
        
        toMarker = L.marker(toCoords, { 
            title: 'To: ' + toLocation,
            icon: L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color:#e74c3c;color:white;border-radius:50%;width:30px;height:30px;display:flex;justify-content:center;align-items:center;box-shadow:0 0 10px rgba(0,0,0,0.5);"><i class="fas fa-flag-checkered"></i></div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        })
        .addTo(map)
        .bindPopup('To: ' + toLocation);
        
        // Get a proper route path using OpenStreetMap's OSRM service
        showLoading();
        
        // Construct the OSRM API URL (using the public demo server)
        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${fromCoords[1]},${fromCoords[0]};${toCoords[1]},${toCoords[0]}?overview=full&geometries=geojson`;
        
        // Return a promise that will be resolved with the API response
        return new Promise((resolve, reject) => {
            // Fetch the route from OSRM
            fetch(osrmUrl)
            .then(response => response.json())
            .then(data => {
                if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) {
                    throw new Error('Failed to get route from OSRM');
                }
                
                // Get the route geometry (array of coordinates)
                const routeGeometry = data.routes[0].geometry.coordinates;
                
                // OSRM returns coordinates as [longitude, latitude], but Leaflet expects [latitude, longitude]
                const routeCoordinates = routeGeometry.map(coord => [coord[1], coord[0]]);
                
                // Create a polyline for the route
                routeLine = L.polyline(routeCoordinates, { 
                    color: '#3498db', 
                    weight: 5,
                    opacity: 0.9,
                    lineCap: 'round'
                })
                .addTo(map);
                
                // Fit the map to show the entire route
                map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
                
                // Call the API to get accident hotspots along the route, passing the full route path
                return fetch('/api/hotspots', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        from_lat: fromCoords[0],
                        from_lng: fromCoords[1],
                        to_lat: toCoords[0],
                        to_lng: toCoords[1],
                        route_coordinates: routeCoordinates
                    })
                });
            })
    // This data is already a JSON object from the promise resolution above
    // This data is already a JSON object from the promise resolution above
    // This is already a data object from the promise resolution above
            .then(data => {
                // Resolve the promise with the data
                resolve(data);
            })
            .catch(error => {
                console.error('Error getting route:', error);
                
                // Fallback to a simple straight line if the routing service fails
                console.log('Falling back to simple straight line route');
                routeLine = L.polyline([fromCoords, toCoords], { 
                    color: '#3498db', 
                    weight: 5,
                    opacity: 0.7,
                    dashArray: '10, 10',
                    lineCap: 'round'
                })
                .addTo(map);
                
                // Fit the map to show both markers
                map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
                
                // Call the API to get accident hotspots along the route (without detailed path)
                fetch('/api/hotspots', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        from_lat: fromCoords[0],
                        from_lng: fromCoords[1],
                        to_lat: toCoords[0],
                        to_lng: toCoords[1]
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // Resolve the promise with the data
                    resolve(data);
                })
                .catch(err => {
                    // If everything fails, reject the promise
                    reject(err);
                });
            });
        });
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Reset button text
        document.getElementById('analyze-btn').textContent = 'Analyze Route';
        hideLoading();
        
        // Show results container
        document.getElementById('results-container').style.display = 'block';
        
        // Update safety score
        const safetyScoreElement = document.getElementById('safety-score-value');
        safetyScoreElement.textContent = data.safety_score;
        
        // Set color based on safety level
        if (data.safety_level === 'Low') {
            safetyScoreElement.style.color = '#e74c3c'; // Red
            document.getElementById('safety-level').textContent = 'Low Safety';
        } else if (data.safety_level === 'Medium') {
            safetyScoreElement.style.color = '#f39c12'; // Orange
            document.getElementById('safety-level').textContent = 'Medium Safety';
        } else {
            safetyScoreElement.style.color = '#27ae60'; // Green
            document.getElementById('safety-level').textContent = 'High Safety';
        }
        
        // Update accident statistics
        document.getElementById('accident-count').textContent = data.hotspots.length;
        
        let totalInjuries = 0;
        let totalFatalities = 0;
        const factors = {};
        
        // Create heatmap data
        const heatmapData = [];
        
        // Process each hotspot
        data.hotspots.forEach(hotspot => {
            totalInjuries += hotspot.injured;
            totalFatalities += hotspot.killed;
            
            // Count factors
            if (hotspot.factor && hotspot.factor !== 'Unspecified') {
                factors[hotspot.factor] = (factors[hotspot.factor] || 0) + 1;
            }
            
            // Add to heatmap data with intensity based on severity
            heatmapData.push([
                hotspot.latitude, 
                hotspot.longitude, 
                Math.min(1, hotspot.severity / 10) // Normalize severity for heatmap intensity
            ]);
            
            // Add a marker for each accident (smaller and more transparent)
            const marker = L.circleMarker([hotspot.latitude, hotspot.longitude], {
                radius: 5,                                      // Smaller radius
                fillColor: getColorBySeverity(hotspot.severity),
                color: '#fff',
                weight: 1,
                opacity: 0.7,                                   // More transparent border
                fillOpacity: 0.5                                // More transparent fill
            }).addTo(map);
            
            // Create popup content
            let popupContent = `
                <div class="accident-popup">
                    <h3>Accident Details</h3>
                    <p><strong>Date:</strong> ${hotspot.date}</p>
                    <p><strong>Time:</strong> ${hotspot.time}</p>
                    <p><strong>Injuries:</strong> ${hotspot.injured}</p>
                    <p><strong>Fatalities:</strong> ${hotspot.killed}</p>
                    <p><strong>Cause:</strong> ${hotspot.factor || 'Unknown'}</p>
                    <p><strong>Location:</strong> ${getLocationString(hotspot)}</p>
                </div>
            `;
            
            marker.bindPopup(popupContent);
            accidentMarkers.push(marker);
        });
        
        // Update injury and fatality counts
        document.getElementById('injury-count').textContent = totalInjuries;
        document.getElementById('fatality-count').textContent = totalFatalities;
        
        // Update factors list
        const factorsList = document.getElementById('factors-list');
        factorsList.innerHTML = '';
        
        // Sort factors by frequency
        const sortedFactors = Object.entries(factors)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5); // Top 5 factors
        
        sortedFactors.forEach(([factor, count]) => {
            const li = document.createElement('li');
            li.textContent = `${factor} (${count})`;
            factorsList.appendChild(li);
        });
        
        // If no factors found
        if (sortedFactors.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No specific factors identified';
            factorsList.appendChild(li);
        }
        
        // Add heatmap layer if there are hotspots
        if (heatmapData.length > 0) {
            console.log("Creating heatmap with data:", heatmapData);
            try {
                // Check if L.heatLayer is available
                if (typeof L.heatLayer === 'function') {
                    // Create a more visible heatmap
                    heatmapLayer = L.heatLayer(heatmapData, {
                        radius: 30,         // Larger radius for better visibility
                        blur: 20,           // More blur for smoother appearance
                        maxZoom: 17,
                        max: 1.0,           // Maximum intensity
                        minOpacity: 0.5,    // Minimum opacity to ensure visibility
                        gradient: {
                            0.3: 'yellow',  // Low Accident Density
                            0.6: 'orange',  // Medium Accident Density
                            0.9: 'red'      // High Accident Density
                        }
                    }).addTo(map);
                    console.log("Heatmap added successfully");
                    
                    // Make sure the heatmap is added on top of the base map but below markers
                    heatmapLayer.bringToFront();
                    
                    // Bring route line and markers to front
                    if (routeLine) routeLine.bringToFront();
                    if (fromMarker) fromMarker.bringToFront();
                    if (toMarker) toMarker.bringToFront();
                } else {
                    console.error("L.heatLayer is not a function. Leaflet.heat may not be loaded properly.");
                    alert("Heatmap library not loaded properly. Some features may not work correctly.");
                }
            } catch (error) {
                console.error("Error creating heatmap:", error);
            }
        } else {
            console.log("No heatmap data available");
        }
    })
    .catch(error => {
        console.error('Error analyzing route:', error);
        document.getElementById('analyze-btn').textContent = 'Analyze Route';
        
        // Show a more detailed error message
        let errorMessage = 'Error analyzing route. ';
        
        if (error.message) {
            errorMessage += error.message;
        } else {
            errorMessage += 'Please try again.';
        }
        
        alert(errorMessage);
        
        // Log additional debug information
        console.log('From coordinates:', fromCoords);
        console.log('To coordinates:', toCoords);
    });
}

// Helper function to get color based on severity
function getColorBySeverity(severity) {
    if (severity >= 5) return '#ff0000'; // Red for high severity
    if (severity >= 2) return '#ffa500'; // Orange for medium severity
    return '#ffff00'; // Yellow for low severity
}

// Helper function to format location string
function getLocationString(hotspot) {
    const parts = [];
    if (hotspot.street) parts.push(hotspot.street);
    if (hotspot.cross_street) parts.push(hotspot.cross_street);
    if (hotspot.borough) parts.push(hotspot.borough);
    
    return parts.join(', ') || 'Unknown location';
}

// Function to initialize time series chart
function initializeTimeSeriesChart(data) {
    const ctx = document.getElementById('time-series-chart').getContext('2d');
    
    // If no data or empty array, show a message
    if (!data || data.length === 0) {
        if (timeSeriesChart) {
            timeSeriesChart.destroy();
        }
        
        // Draw a "No Data Available" message
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No Time Series Data Available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    // Sort data by date
    data.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // Extract dates and counts
    const dates = data.map(item => item.date);
    const counts = data.map(item => item.count);
    
    // Create chart
    if (timeSeriesChart) {
        timeSeriesChart.destroy();
    }
    
    timeSeriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Number of Accidents',
                data: counts,
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 3,
                pointBackgroundColor: 'rgba(52, 152, 219, 1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Accident Trends Over Time',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Function to initialize factors chart
function initializeFactorsChart(data) {
    const ctx = document.getElementById('factors-chart').getContext('2d');
    
    // If no data, show a message
    if (!data || Object.keys(data).length === 0) {
        if (factorsChart) {
            factorsChart.destroy();
        }
        
        // Draw a "No Data Available" message
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No Contributing Factors Data Available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    // Sort data by count
    const sortedData = Object.entries(data)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8); // Top 8 factors
    
    // Extract factors and counts
    const factors = sortedData.map(item => item[0]);
    const counts = sortedData.map(item => item[1]);
    
    // Create chart
    if (factorsChart) {
        factorsChart.destroy();
    }
    
    factorsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: factors,
            datasets: [{
                label: 'Number of Accidents',
                data: counts,
                backgroundColor: [
                    'rgba(231, 76, 60, 0.7)',
                    'rgba(230, 126, 34, 0.7)',
                    'rgba(241, 196, 15, 0.7)',
                    'rgba(46, 204, 113, 0.7)',
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(155, 89, 182, 0.7)',
                    'rgba(52, 73, 94, 0.7)',
                    'rgba(149, 165, 166, 0.7)'
                ],
                borderColor: [
                    'rgba(231, 76, 60, 1)',
                    'rgba(230, 126, 34, 1)',
                    'rgba(241, 196, 15, 1)',
                    'rgba(46, 204, 113, 1)',
                    'rgba(52, 152, 219, 1)',
                    'rgba(155, 89, 182, 1)',
                    'rgba(52, 73, 94, 1)',
                    'rgba(149, 165, 166, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top Contributing Factors',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Function to initialize time of day chart
function initializeTimeOfDayChart(data) {
    const ctx = document.getElementById('time-of-day-chart').getContext('2d');
    
    // If no data, show a message
    if (!data || Object.keys(data).length === 0) {
        if (timeOfDayChart) {
            timeOfDayChart.destroy();
        }
        
        // Draw a "No Data Available" message
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No Time of Day Data Available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    // Extract time of day and counts
    const timeOfDay = Object.keys(data);
    const counts = Object.values(data);
    
    // Create chart
    if (timeOfDayChart) {
        timeOfDayChart.destroy();
    }
    
    timeOfDayChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: timeOfDay,
            datasets: [{
                data: counts,
                backgroundColor: [
                    'rgba(241, 196, 15, 0.7)', // Morning
                    'rgba(230, 126, 34, 0.7)', // Afternoon
                    'rgba(52, 152, 219, 0.7)', // Evening
                    'rgba(44, 62, 80, 0.7)'    // Night
                ],
                borderColor: [
                    'rgba(241, 196, 15, 1)',
                    'rgba(230, 126, 34, 1)',
                    'rgba(52, 152, 219, 1)',
                    'rgba(44, 62, 80, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Accidents by Time of Day',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Function to initialize borough chart
function initializeBoroughChart(data) {
    const ctx = document.getElementById('borough-chart').getContext('2d');
    
    // If no data, show a message
    if (!data || Object.keys(data).length === 0) {
        if (boroughChart) {
            boroughChart.destroy();
        }
        
        // Draw a "No Data Available" message
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No Borough Data Available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    // Extract boroughs and counts
    const boroughs = Object.keys(data);
    const counts = Object.values(data);
    
    // Create chart
    if (boroughChart) {
        boroughChart.destroy();
    }
    
    boroughChart = new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: boroughs,
            datasets: [{
                data: counts,
                backgroundColor: [
                    'rgba(52, 152, 219, 0.7)', // Primary color
                    'rgba(155, 89, 182, 0.7)',
                    'rgba(52, 73, 94, 0.7)',
                    'rgba(46, 204, 113, 0.7)',
                    'rgba(230, 126, 34, 0.7)',
                    'rgba(231, 76, 60, 0.7)'
                ],
                borderColor: [
                    'rgba(52, 152, 219, 1)',
                    'rgba(155, 89, 182, 1)',
                    'rgba(52, 73, 94, 1)',
                    'rgba(46, 204, 113, 1)',
                    'rgba(230, 126, 34, 1)',
                    'rgba(231, 76, 60, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Accidents by Borough',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Function to initialize severity chart
function initializeSeverityChart(data) {
    const ctx = document.getElementById('severity-chart').getContext('2d');
    
    // If no data, show a message
    if (!data || Object.keys(data).length === 0) {
        if (severityChart) {
            severityChart.destroy();
        }
        
        // Draw a "No Data Available" message
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No Severity Data Available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    // Extract severity categories and counts
    const categories = Object.keys(data);
    const counts = Object.values(data);
    
    // Create chart
    if (severityChart) {
        severityChart.destroy();
    }
    
    severityChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categories,
            datasets: [{
                data: counts,
                backgroundColor: [
                    'rgba(46, 204, 113, 0.7)', // Low
                    'rgba(241, 196, 15, 0.7)', // Medium
                    'rgba(230, 126, 34, 0.7)', // High
                    'rgba(231, 76, 60, 0.7)'   // Very High
                ],
                borderColor: [
                    'rgba(46, 204, 113, 1)',
                    'rgba(241, 196, 15, 1)',
                    'rgba(230, 126, 34, 1)',
                    'rgba(231, 76, 60, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Accident Severity Distribution',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Function to initialize day of week chart
function initializeDayOfWeekChart(data) {
    const ctx = document.getElementById('day-of-week-chart').getContext('2d');
    
    // If no data, show a message
    if (!data || Object.keys(data).length === 0) {
        if (dayOfWeekChart) {
            dayOfWeekChart.destroy();
        }
        
        // Draw a "No Data Available" message
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('No Day of Week Data Available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    // Sort days of week in correct order
    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const sortedData = {};
    
    dayOrder.forEach(day => {
        if (data[day]) {
            sortedData[day] = data[day];
        }
    });
    
    // For any days not in the standard order
    Object.keys(data).forEach(day => {
        if (!dayOrder.includes(day)) {
            sortedData[day] = data[day];
        }
    });
    
    // Extract days and counts
    const days = Object.keys(sortedData);
    const counts = Object.values(sortedData);
    
    // Create chart
    if (dayOfWeekChart) {
        dayOfWeekChart.destroy();
    }
    
    dayOfWeekChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                label: 'Number of Accidents',
                data: counts,
                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Accidents by Day of Week',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Function to show loading spinner
function showLoading() {
    document.getElementById('loading-spinner').style.display = 'flex';
}

// Function to hide loading spinner
function hideLoading() {
    document.getElementById('loading-spinner').style.display = 'none';
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load data summary and initialize dashboard
    loadDataSummary();
    
    // Add event listener to the analyze button
    document.getElementById('analyze-btn').addEventListener('click', analyzeRoute);
    
    // Add event listeners for Enter key in input fields
    document.getElementById('from-location').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('to-location').focus();
        }
    });
    
    document.getElementById('to-location').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            analyzeRoute();
        }
    });
});
