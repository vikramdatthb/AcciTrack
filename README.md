# AcciTrack Traffic Accident Analysis Project

![Project Banner](https://raw.githubusercontent.com/vikramdatthb/AcciTrack/refs/heads/main/images/screenshot_3_18_2025_3-15-30%20AM.png)

## Project Overview

This comprehensive data analysis project focuses on New York City traffic accident data, providing powerful insights into accident patterns, contributing factors, and safety metrics. The project leverages advanced data processing techniques, statistical analysis, and interactive visualizations to transform raw accident data into actionable safety intelligence.

## Key Features

- **Accident Hotspot Identification**: Utilizes geospatial analysis to identify and visualize high-risk areas across NYC
- **Route Safety Analysis**: Analyzes accident patterns along specific routes to calculate safety scores
- **Temporal Pattern Analysis**: Examines accident distribution across different times of day, days of the week, and trends over time
- **Contributing Factor Analysis**: Identifies and ranks the most common causes of accidents
- **Severity Classification**: Categorizes accidents based on a custom severity scoring algorithm
- **Borough-level Insights**: Provides comparative analysis of accident patterns across NYC boroughs
- **Interactive Data Exploration**: Enables dynamic filtering and visualization of accident data

## Data Processing Pipeline

The project implements a robust data processing pipeline that handles raw accident data:

1. **Data Acquisition**: Imports NYC traffic accident data from text or CSV formats
2. **Data Cleaning**: Removes invalid entries and handles missing values
3. **Feature Engineering**: 
   - Calculates severity scores based on injuries and fatalities
   - Extracts temporal features (time of day, day of week, month, year)
   - Categorizes accidents by contributing factors and location
4. **Statistical Analysis**: Performs aggregations and calculations to identify patterns and trends
5. **Visualization Generation**: Creates static visualizations for initial data exploration

```python
# severity score calculation 
df['SEVERITY'] = df['NUMBER OF PERSONS INJURED'] + df['NUMBER OF PERSONS KILLED'] * 5

# Example of time categorization
def categorize_time(hour):
    if pd.isna(hour):
        return 'Unknown'
    hour = int(hour)
    if 5 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'
```

## Project Components

### 1. Data Preprocessing Module
The `convert_data.py` script handles the initial data processing:

- Converts raw accident data from text to CSV format
- Filters for relevant columns and cleans the dataset
- Performs geographic data validation
- Calculates derived metrics like severity scores
- Generates preliminary visualizations for data exploration:
  - Borough distribution charts
  - Contributing factor analysis
  - Severity distribution histograms
  - Accident location scatter plots

### 2. Main Analysis Engine

The core analysis functionality in `app.py` provides:

- **Data Summary Statistics**: Calculates key metrics like total accidents, injuries, and fatalities
- **Geospatial Analysis**: Identifies accident clusters and hotspots
- **Route Safety Algorithm**: Implements a custom algorithm that:
  - Creates a buffer zone around routes
  - Identifies accidents within proximity
  - Calculates distance-weighted safety scores
  - Classifies routes into safety categories (High, Medium, Low)
- **Trend Analysis**: Examines accident patterns over time and by location
- **Factor Analysis**: Identifies correlations between contributing factors and accident severity

```python
# route safety scoring algorithm
safety_score = 100
if close_accidents:
    # Reduce score based on number and severity of accidents
    accident_count = len(close_accidents)
    total_severity = sum(acc['severity'] for acc in close_accidents)
    
    # Adjust score (simple algorithm - can be refined)
    safety_score -= min(80, accident_count * 5)  # Reduce up to 80 points based on count
    safety_score -= min(15, total_severity)      # Reduce up to 15 points based on severity
```

### 3. Advanced Analytics Dashboard

![Analytics Dashboard](https://raw.githubusercontent.com/vikramdatthb/AcciTrack/refs/heads/main/images/screenshot_3_18_2025_3-22-30%20AM.png)
![Analytics Dashboard](https://raw.githubusercontent.com/vikramdatthb/AcciTrack/refs/heads/main/images/screenshot_3_18_2025_3-23-08%20AM.png)
![Analytics Dashboard](https://raw.githubusercontent.com/vikramdatthb/AcciTrack/refs/heads/main/images/screenshot_3_18_2025_3-24-33%20AM.png)
![Analytics Dashboard](https://raw.githubusercontent.com/vikramdatthb/AcciTrack/refs/heads/main/images/screenshot_3_18_2025_4-27-35%20AM.png)

The `dash_app.py` module provides an advanced data analysis dashboard with:

- **Accident Heatmap**: Density-based visualization of accident hotspots across NYC
- **Temporal Analysis**: 
  - Time of day distribution (Morning, Afternoon, Evening, Night)
  - Day of week patterns
  - Monthly and yearly trends
- **Contributing Factors Analysis**: Interactive visualizations of accident causes
- **Severity Analysis**: 
  - Distribution of accident severity
  - Borough-level severity comparisons
  - Correlation between severity and other factors

The dashboard leverages Plotly and Dash to create interactive, responsive visualizations that allow for deep data exploration.

### 4. Interactive Web Interface

![Analytics Dashboard](https://raw.githubusercontent.com/vikramdatthb/AcciTrack/refs/heads/main/images/screenshot_3_18_2025_3-12-00%20AM.png)
![Analytics Dashboard](https://raw.githubusercontent.com/vikramdatthb/AcciTrack/refs/heads/main/images/Screenshot%202025-03-18%20031843.png)

While the primary focus is data analysis, the project includes a web interface to make the insights accessible:

- **Route Safety Analysis**: Enter start and end locations to analyze the safety of a route
- **Data Summary Dashboard**: View key statistics and trends at a glance
- **Interactive Maps**: Visualize accident hotspots and severity patterns
- **Dynamic Charts**: Explore accident data through interactive visualizations

## Technical Implementation

### Data Analysis Technologies

- **Pandas & NumPy**: Core data processing and numerical analysis
- **Scikit-learn**: Machine learning for pattern recognition and clustering
- **Matplotlib & Seaborn**: Static data visualization generation
- **Plotly & Dash**: Interactive data visualization dashboard
- **Geospatial Analysis**: Custom algorithms for route safety assessment

### Data Visualization Techniques

- **Heatmaps**: Visualize accident density across geographic areas
- **Time Series Analysis**: Track accident trends over time
- **Bar & Pie Charts**: Compare categorical distributions
- **Scatter Plots**: Examine relationships between variables
- **Choropleth Maps**: Display borough-level statistics

### Web Development Implementation
While data analysis is the primary focus of this project, a lightweight web application was developed to make the insights accessible and interactive:

- **Flask Framework**: Powers the main application backend, handling data requests and API endpoints
- **Dash (Plotly)**: Implements the advanced analytics dashboard with minimal code
- **Leaflet.js**: Renders interactive maps with accident hotspots and route visualization
- **Chart.js**: Creates responsive, animated data visualizations for the main dashboard
- **AJAX**: Enables asynchronous data loading for seamless user experience
- **Responsive Design**: Ensures accessibility across devices with modern CSS techniques

The web implementation follows a modular architecture:
1. **Backend API**: RESTful endpoints provide processed data to the frontend
2. **Interactive Maps**: Visualize geospatial data with custom overlays
3. **Dynamic Dashboards**: Real-time filtering and exploration of accident data
4. **Route Analysis Interface**: User-friendly input for location-based safety analysis

```javascript
//heatmap implementation with Leaflet.js
heatmapLayer = L.heatLayer(heatmapData, {
    radius: 30,         // Larger radius for better visibility
    blur: 20,           // More blur for smoother appearance
    maxZoom: 17,
    gradient: {
        0.3: 'yellow',  // Low Accident Density
        0.6: 'orange',  // Medium Accident Density
        0.9: 'red'      // High Accident Density
    }
}).addTo(map);
```

## Key Insights

The analysis reveals several important patterns in NYC traffic accidents:

- **Temporal Patterns**: Accidents show distinct patterns by time of day and day of week
- **Geographic Hotspots**: Certain intersections and areas consistently show higher accident rates
- **Contributing Factors**: Driver inattention/distraction is among the leading causes of accidents
- **Severity Distribution**: Most accidents result in low to medium severity, with a small percentage causing serious injuries or fatalities
- **Borough Variations**: Accident rates and severity vary significantly across different NYC boroughs

## Future Enhancements

- Implement predictive modeling to forecast accident likelihood
- Incorporate weather data to analyze environmental factors
- Develop machine learning algorithms for more sophisticated pattern recognition
- Add real-time data integration for up-to-date analysis
- Expand the analysis to include vehicle type and pedestrian factors

## Installation and Usage

```bash
# Clone the repository
git clone https://github.com/yourusername/nyc-traffic-accident-analysis.git

# Install required packages
pip install -r requirements.txt

# Run the data conversion script
python convert_data.py

# Start the application
python run.py
```

## Project Structure

```
nyc-traffic-accident-analysis/
├── app.py                      # Main Flask application
├── dash_app.py                 # Dash dashboard for advanced analytics
├── convert_data.py             # Data preprocessing script
├── checkrequirements.py        # Dependency checker
├── run.py                      # Application runner
├── accidentdata.csv            # Processed accident data
├── accidentdata.txt            # Raw accident data
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Custom styling
│   └── js/
│       └── main.js             # Client-side functionality
├── templates/                  # HTML templates
│   └── index.html              # Main application template
└── visualizations/             # Generated data visualizations
    ├── accident_locations.png  # Scatter plot of accident locations
    ├── borough_distribution.png # Accidents by borough
    ├── contributing_factors.png # Top contributing factors
    └── severity_distribution.png # Distribution of accident severity
```
## Conclusion

This NYC Traffic Accident Analysis project demonstrates advanced data analysis techniques applied to real-world safety data. By transforming raw accident records into actionable insights, the project showcases the power of data analysis for understanding complex urban safety patterns and potentially informing policy decisions to improve traffic safety.

