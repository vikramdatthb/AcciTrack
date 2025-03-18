from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
from flask_cors import CORS
import os
import json
from geopy.distance import geodesic
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import io
import base64

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

# Import and initialize Dash app
from dash_app import create_dash_app
dash_app = create_dash_app(app)

# Load and preprocess the accident data
def load_data():
    # Read the data from the CSV file
    # We're only selecting the columns we need for our analysis
    try:
        print("Trying to load accidentdata.csv...")
        df = pd.read_csv('accidentdata.csv', low_memory=False)
        print(f"Successfully loaded CSV with {len(df)} rows")
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        print("Trying to load from text file instead...")
        try:
            # If CSV doesn't exist, try to read from the text file
            df = pd.read_csv('accidentdata.txt', sep='\t', low_memory=False)
            print(f"Successfully loaded TXT with {len(df)} rows")
        except Exception as e:
            print(f"Error loading TXT: {str(e)}")
            # Create a minimal dataframe with required columns to avoid errors
            print("Creating empty dataframe with required columns")
            df = pd.DataFrame(columns=[
                'LATITUDE', 'LONGITUDE', 'CRASH DATE', 'CRASH TIME',
                'NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
                'CONTRIBUTING FACTOR VEHICLE 1', 'ON STREET NAME', 
                'CROSS STREET NAME', 'OFF STREET NAME', 'BOROUGH'
            ])
    
    # Select only the relevant columns
    relevant_columns = [
        'LATITUDE', 'LONGITUDE', 'CRASH DATE', 'CRASH TIME',
        'NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
        'CONTRIBUTING FACTOR VEHICLE 1', 'ON STREET NAME', 
        'CROSS STREET NAME', 'OFF STREET NAME', 'BOROUGH'
    ]
    
    # Check which columns exist in the dataframe
    existing_columns = [col for col in relevant_columns if col in df.columns]
    print(f"Found {len(existing_columns)} of {len(relevant_columns)} required columns")
    
    if len(existing_columns) < len(relevant_columns):
        missing_columns = [col for col in relevant_columns if col not in existing_columns]
        print(f"Missing columns: {missing_columns}")
    
    # Use only existing columns
    df = df[existing_columns].copy()
    
    # Drop rows with missing latitude and longitude
    if 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
        print(f"Before dropping NA: {len(df)} rows")
        df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
        print(f"After dropping NA: {len(df)} rows")
    else:
        print("WARNING: LATITUDE or LONGITUDE columns not found in data")
    
    # Convert injury and fatality columns to numeric
    numeric_columns = ['NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate severity score (weighted sum of injuries and fatalities)
    df['SEVERITY'] = df['NUMBER OF PERSONS INJURED'] + df['NUMBER OF PERSONS KILLED'] * 5
    
    return df

# Global variable to store the data
accident_data = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/hotspots', methods=['POST'])
def get_hotspots():
    global accident_data
    
    try:
        # Load data if not already loaded
        if accident_data is None:
            print("Loading accident data...")
            accident_data = load_data()
            print(f"Loaded {len(accident_data)} accident records")
        
        # Get from and to coordinates from request
        data = request.json
        print(f"Received request data: {data}")
        
        from_lat = data.get('from_lat')
        from_lng = data.get('from_lng')
        to_lat = data.get('to_lat')
        to_lng = data.get('to_lng')
        
        # Check if detailed route coordinates are provided
        route_coordinates = data.get('route_coordinates', [])
        
        # Validate coordinates
        if not all([from_lat, from_lng, to_lat, to_lng]):
            print("Invalid coordinates received")
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        # Convert to float
        from_lat, from_lng = float(from_lat), float(from_lng)
        to_lat, to_lng = float(to_lat), float(to_lng)
        
        print(f"Processing route from ({from_lat}, {from_lng}) to ({to_lat}, {to_lng})")
        
        # Create bounding box for the route (with some buffer)
        if route_coordinates and len(route_coordinates) > 0:
            # If we have detailed route coordinates, create a bounding box that encompasses all points
            lats = [coord[0] for coord in route_coordinates]
            lngs = [coord[1] for coord in route_coordinates]
            min_lat = min(lats) - 0.005  # Smaller buffer since we have precise route
            max_lat = max(lats) + 0.005
            min_lng = min(lngs) - 0.005
            max_lng = max(lngs) + 0.005
        else:
            # Fallback to simple bounding box between start and end points
            min_lat = min(from_lat, to_lat) - 0.02
            max_lat = max(from_lat, to_lat) + 0.02
            min_lng = min(from_lng, to_lng) - 0.02
            max_lng = max(from_lng, to_lng) + 0.02
        
        # Filter accidents within the bounding box
        filtered_data = accident_data[
            (accident_data['LATITUDE'] >= min_lat) & 
            (accident_data['LATITUDE'] <= max_lat) &
            (accident_data['LONGITUDE'] >= min_lng) & 
            (accident_data['LONGITUDE'] <= max_lng)
        ]
        
        print(f"Found {len(filtered_data)} accidents within the bounding box")
        
        # Function to calculate minimum distance from point to a polyline (route)
        def point_to_route_distance(point, route_points):
            min_distance = float('inf')
            
            # If no route points or only one point, return a large distance
            if not route_points or len(route_points) < 2:
                return min_distance
            
            # Check distance to each segment of the route
            for i in range(len(route_points) - 1):
                segment_start = route_points[i]
                segment_end = route_points[i + 1]
                
                # Calculate distance from point to this segment
                try:
                    # Convert to numpy arrays for vector operations
                    point_np = np.array([float(point[0]), float(point[1])])
                    segment_start_np = np.array([float(segment_start[0]), float(segment_start[1])])
                    segment_end_np = np.array([float(segment_end[0]), float(segment_end[1])])
                    
                    # Vector from segment_start to segment_end
                    segment_vec = segment_end_np - segment_start_np
                    segment_length = np.linalg.norm(segment_vec)
                    segment_unit_vec = segment_vec / segment_length if segment_length > 0 else segment_vec
                    
                    # Vector from segment_start to point
                    point_vec = point_np - segment_start_np
                    
                    # Project point_vec onto segment_unit_vec
                    projection_length = np.dot(point_vec, segment_unit_vec)
                    
                    # If projection is outside the segment, use distance to nearest endpoint
                    if projection_length < 0:
                        segment_distance = np.linalg.norm(point_vec)
                    elif projection_length > segment_length:
                        segment_distance = np.linalg.norm(point_np - segment_end_np)
                    else:
                        # Distance from point to segment
                        projection = segment_start_np + projection_length * segment_unit_vec
                        segment_distance = np.linalg.norm(point_np - projection)
                    
                    # Update minimum distance if this segment is closer
                    min_distance = min(min_distance, segment_distance)
                    
                except Exception as e:
                    print(f"Error calculating segment distance: {str(e)}")
                    continue
            
            return min_distance
        
        # Function to calculate distance from point to line segment (for fallback)
        def point_to_line_distance(point, line_start, line_end):
            try:
                # Convert to numpy arrays for vector operations
                point = np.array([float(point[0]), float(point[1])])
                line_start = np.array([float(line_start[0]), float(line_start[1])])
                line_end = np.array([float(line_end[0]), float(line_end[1])])
                
                # Vector from line_start to line_end
                line_vec = line_end - line_start
                line_length = np.linalg.norm(line_vec)
                line_unit_vec = line_vec / line_length if line_length > 0 else line_vec
                
                # Vector from line_start to point
                point_vec = point - line_start
                
                # Project point_vec onto line_unit_vec
                projection_length = np.dot(point_vec, line_unit_vec)
                
                # If projection is outside the line segment, use distance to nearest endpoint
                if projection_length < 0:
                    return np.linalg.norm(point_vec)
                elif projection_length > line_length:
                    return np.linalg.norm(point - line_end)
                else:
                    # Distance from point to line
                    projection = line_start + projection_length * line_unit_vec
                    return np.linalg.norm(point - projection)
            except Exception as e:
                print(f"Error in point_to_line_distance: {str(e)}")
                # Return a large distance if there's an error
                return 999
        
        # Filter accidents that are close to the route
        MAX_DISTANCE_KM = 0.5  # Reduced distance threshold for more precise filtering
        close_accidents = []
        
        for _, accident in filtered_data.iterrows():
            lat, lng = accident['LATITUDE'], accident['LONGITUDE']
            
            # Skip if lat/lng are invalid
            if pd.isna(lat) or pd.isna(lng):
                continue
            
            # Calculate distance in km
            try:
                accident_point = (float(lat), float(lng))
                
                if route_coordinates and len(route_coordinates) > 1:
                    # Use the detailed route path for distance calculation
                    distance = point_to_route_distance(accident_point, route_coordinates)
                    distance_km = distance * 111  # Rough conversion to km
                else:
                    # Fallback to simple line if no detailed route
                    route_start = (float(from_lat), float(from_lng))
                    route_end = (float(to_lat), float(to_lng))
                    distance_km = point_to_line_distance(accident_point, route_start, route_end) * 111
                
            except Exception as e:
                print(f"Error calculating distance: {str(e)}")
                continue  # Skip this accident if there's an error
            
            if distance_km <= MAX_DISTANCE_KM:
                # Create accident data dictionary with proper handling of NaN values
                accident_info = {
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'severity': float(accident['SEVERITY']),
                    'date': str(accident.get('CRASH DATE', '')),
                    'time': str(accident.get('CRASH TIME', '')),
                    'injured': int(accident.get('NUMBER OF PERSONS INJURED', 0)),
                    'killed': int(accident.get('NUMBER OF PERSONS KILLED', 0)),
                    'factor': str(accident.get('CONTRIBUTING FACTOR VEHICLE 1', '')),
                    'street': str(accident.get('ON STREET NAME', '')),
                    'cross_street': str(accident.get('CROSS STREET NAME', '')),
                    'borough': str(accident.get('BOROUGH', '')),
                    'distance_to_route': float(distance_km)  # Add distance to route for reference
                }
                
                # Replace any NaN values with empty strings
                for key, value in accident_info.items():
                    if pd.isna(value):
                        accident_info[key] = ''
                
                close_accidents.append(accident_info)
        
        # Calculate route safety score based on accident density and severity
        safety_score = 100
        if close_accidents:
            # Reduce score based on number and severity of accidents
            accident_count = len(close_accidents)
            total_severity = sum(acc['severity'] for acc in close_accidents)
            
            # Adjust score (simple algorithm - can be refined)
            safety_score -= min(80, accident_count * 5)  # Reduce up to 80 points based on count
            safety_score -= min(15, total_severity)      # Reduce up to 15 points based on severity
        
        # Determine safety level
        safety_level = 'High'
        if safety_score < 70:
            safety_level = 'Low'
        elif safety_score < 85:
            safety_level = 'Medium'
        
        print(f"Found {len(close_accidents)} accidents close to the route")
        print(f"Safety score: {safety_score}, Safety level: {safety_level}")
        
        return jsonify({
            'hotspots': close_accidents,
            'safety_score': safety_score,
            'safety_level': safety_level
        })
        
    except Exception as e:
        print(f"Error in get_hotspots: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/data-summary', methods=['GET'])
def get_data_summary():
    global accident_data
    
    # Load data if not already loaded
    if accident_data is None:
        accident_data = load_data()
    
    # Get summary statistics
    total_accidents = len(accident_data)
    total_injured = int(accident_data['NUMBER OF PERSONS INJURED'].sum())
    total_killed = int(accident_data['NUMBER OF PERSONS KILLED'].sum())
    
    # Get top contributing factors
    top_factors = accident_data['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(10).to_dict()
    
    # Convert any NaN keys to strings
    top_factors_clean = {}
    for key, value in top_factors.items():
        if pd.isna(key):
            top_factors_clean['Unknown'] = value
        else:
            top_factors_clean[str(key)] = value
    
    # Get accident count by borough
    borough_counts = accident_data['BOROUGH'].value_counts().to_dict()
    
    # Convert any NaN keys to strings
    borough_counts_clean = {}
    for key, value in borough_counts.items():
        if pd.isna(key):
            borough_counts_clean['Unknown'] = value
        else:
            borough_counts_clean[str(key)] = value
    
    # Add time-based analysis
    # Extract date and time information if available
    time_of_day = {}
    day_of_week = {}
    
    if 'CRASH TIME' in accident_data.columns and 'CRASH DATE' in accident_data.columns:
        # Convert crash time to hour
        try:
            # Try to extract hour from time string
            accident_data['HOUR'] = accident_data['CRASH TIME'].apply(
                lambda x: int(str(x).split(':')[0]) if pd.notna(x) and ':' in str(x) else None
            )
            
            # Create time of day categories
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
            
            accident_data['TIME_OF_DAY'] = accident_data['HOUR'].apply(categorize_time)
            time_of_day = accident_data['TIME_OF_DAY'].value_counts().to_dict()
            
            # Try to extract day of week
            try:
                accident_data['CRASH_DATE'] = pd.to_datetime(accident_data['CRASH DATE'], errors='coerce')
                accident_data['DAY_OF_WEEK'] = accident_data['CRASH_DATE'].dt.day_name()
                day_of_week = accident_data['DAY_OF_WEEK'].value_counts().to_dict()
            except Exception as e:
                print(f"Error extracting day of week: {str(e)}")
                day_of_week = {'Unknown': total_accidents}
        except Exception as e:
            print(f"Error processing time data: {str(e)}")
            time_of_day = {'Unknown': total_accidents}
    else:
        time_of_day = {'Unknown': total_accidents}
        day_of_week = {'Unknown': total_accidents}
    
    # Calculate severity distribution
    severity_bins = [0, 2, 5, 10, float('inf')]
    severity_labels = ['Low (0-2)', 'Medium (3-5)', 'High (6-10)', 'Very High (>10)']
    
    accident_data['SEVERITY_CATEGORY'] = pd.cut(
        accident_data['SEVERITY'], 
        bins=severity_bins, 
        labels=severity_labels, 
        right=False
    )
    
    severity_distribution = accident_data['SEVERITY_CATEGORY'].value_counts().to_dict()
    
    # Generate time series data for accidents by month if date is available
    time_series_data = []
    if 'CRASH_DATE' in accident_data.columns:
        try:
            # Group by year and month
            accident_data['YEAR_MONTH'] = accident_data['CRASH_DATE'].dt.strftime('%Y-%m')
            monthly_counts = accident_data['YEAR_MONTH'].value_counts().sort_index()
            
            for date, count in monthly_counts.items():
                time_series_data.append({
                    'date': date,
                    'count': int(count)
                })
        except Exception as e:
            print(f"Error generating time series data: {str(e)}")
    
    return jsonify({
        'total_accidents': total_accidents,
        'total_injured': total_injured,
        'total_killed': total_killed,
        'top_factors': top_factors_clean,
        'borough_counts': borough_counts_clean,
        'time_of_day_counts': time_of_day,
        'day_of_week_counts': day_of_week,
        'severity_distribution': severity_distribution,
        'time_series_data': time_series_data
    })

@app.route('/api/accident-trends', methods=['GET'])
def get_accident_trends():
    global accident_data
    
    # Load data if not already loaded
    if accident_data is None:
        accident_data = load_data()
    
    # Initialize response data
    response_data = {
        'severity_by_factor': {},
        'severity_by_borough': {},
        'injuries_by_borough': {},
        'fatalities_by_borough': {}
    }
    
    # Calculate average severity by contributing factor
    factor_severity = accident_data.groupby('CONTRIBUTING FACTOR VEHICLE 1')['SEVERITY'].mean().dropna()
    # Get top 10 factors by severity
    top_factors_by_severity = factor_severity.sort_values(ascending=False).head(10)
    
    # Convert to dictionary with proper handling of NaN keys
    for factor, severity in top_factors_by_severity.items():
        factor_key = 'Unknown' if pd.isna(factor) else str(factor)
        response_data['severity_by_factor'][factor_key] = float(severity)
    
    # Calculate average severity by borough
    if 'BOROUGH' in accident_data.columns:
        borough_severity = accident_data.groupby('BOROUGH')['SEVERITY'].mean().dropna()
        
        # Convert to dictionary with proper handling of NaN keys
        for borough, severity in borough_severity.items():
            borough_key = 'Unknown' if pd.isna(borough) else str(borough)
            response_data['severity_by_borough'][borough_key] = float(severity)
        
        # Calculate total injuries by borough
        borough_injuries = accident_data.groupby('BOROUGH')['NUMBER OF PERSONS INJURED'].sum().dropna()
        
        # Convert to dictionary with proper handling of NaN keys
        for borough, injuries in borough_injuries.items():
            borough_key = 'Unknown' if pd.isna(borough) else str(borough)
            response_data['injuries_by_borough'][borough_key] = int(injuries)
        
        # Calculate total fatalities by borough
        borough_fatalities = accident_data.groupby('BOROUGH')['NUMBER OF PERSONS KILLED'].sum().dropna()
        
        # Convert to dictionary with proper handling of NaN keys
        for borough, fatalities in borough_fatalities.items():
            borough_key = 'Unknown' if pd.isna(borough) else str(borough)
            response_data['fatalities_by_borough'][borough_key] = int(fatalities)
    
    # Time-based analysis if date and time columns are available
    if 'CRASH_DATE' in accident_data.columns and 'HOUR' in accident_data.columns:
        try:
            # Accidents by hour of day
            hour_counts = accident_data['HOUR'].value_counts().sort_index()
            response_data['accidents_by_hour'] = {str(hour): int(count) for hour, count in hour_counts.items() if pd.notna(hour)}
            
            # Accidents by day of week
            if 'DAY_OF_WEEK' in accident_data.columns:
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_counts = accident_data['DAY_OF_WEEK'].value_counts()
                response_data['accidents_by_day'] = {day: int(day_counts.get(day, 0)) for day in day_order}
        except Exception as e:
            print(f"Error in time-based analysis: {str(e)}")
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
