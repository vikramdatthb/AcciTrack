# Set matplotlib backend to non-interactive 'Agg' to prevent GUI thread issues
import matplotlib
matplotlib.use('Agg')

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from flask import Flask

# Function to load and preprocess data
def load_data():
    try:
        # Try to load from CSV
        df = pd.read_csv('accidentdata.csv', low_memory=False)
    except:
        try:
            # If CSV doesn't exist, try to read from the text file
            df = pd.read_csv('accidentdata.txt', sep='\t', low_memory=False)
        except:
            # Create a minimal dataframe with required columns to avoid errors
            print("Creating empty dataframe with required columns")
            df = pd.DataFrame(columns=[
                'LATITUDE', 'LONGITUDE', 'CRASH DATE', 'CRASH TIME',
                'NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
                'CONTRIBUTING FACTOR VEHICLE 1', 'ON STREET NAME', 
                'CROSS STREET NAME', 'OFF STREET NAME', 'BOROUGH'
            ])
    
    # Drop rows with missing latitude and longitude
    if 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
        df = df.dropna(subset=['LATITUDE', 'LONGITUDE'])
    
    # Convert injury and fatality columns to numeric
    numeric_columns = ['NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate severity score (weighted sum of injuries and fatalities)
    if all(col in df.columns for col in numeric_columns):
        df['SEVERITY'] = df['NUMBER OF PERSONS INJURED'] + df['NUMBER OF PERSONS KILLED'] * 5
    
    # Convert date and time if available
    if 'CRASH DATE' in df.columns:
        try:
            df['CRASH_DATE'] = pd.to_datetime(df['CRASH DATE'], errors='coerce')
            df['YEAR'] = df['CRASH_DATE'].dt.year
            df['MONTH'] = df['CRASH_DATE'].dt.month
            df['DAY'] = df['CRASH_DATE'].dt.day
            df['DAY_OF_WEEK'] = df['CRASH_DATE'].dt.day_name()
        except:
            pass
    
    if 'CRASH TIME' in df.columns:
        try:
            # Extract hour from time string
            df['HOUR'] = df['CRASH TIME'].apply(
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
            
            df['TIME_OF_DAY'] = df['HOUR'].apply(categorize_time)
        except:
            pass
    
    return df

# Initialize the Dash app
def init_dash_app(server):
    # Load data
    df = load_data()
    
    # Create Dash app
    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname='/dash/',
        external_stylesheets=[
            'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap'
        ]
    )
    
    # Define layout
    dash_app.layout = html.Div([
        html.Div([
            html.H1("NYC Traffic Accident Analysis Dashboard", 
                    style={'textAlign': 'center', 'color': '#2c3e50', 'fontFamily': 'Poppins'}),
            html.P("Interactive data analysis of NYC traffic accidents", 
                   style={'textAlign': 'center', 'color': '#7f8c8d', 'fontFamily': 'Poppins'})
        ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px', 'margin-bottom': '20px'}),
        
        html.Div([
            html.Div([
                html.H3("Analysis Type", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                dcc.Tabs(id='tabs', value='tab-1', children=[
                    dcc.Tab(label='Accident Heatmap', value='tab-1', 
                            style={'fontFamily': 'Poppins'}, selected_style={'fontFamily': 'Poppins'}),
                    dcc.Tab(label='Time Analysis', value='tab-2', 
                            style={'fontFamily': 'Poppins'}, selected_style={'fontFamily': 'Poppins'}),
                    dcc.Tab(label='Contributing Factors', value='tab-3', 
                            style={'fontFamily': 'Poppins'}, selected_style={'fontFamily': 'Poppins'}),
                    dcc.Tab(label='Severity Analysis', value='tab-4', 
                            style={'fontFamily': 'Poppins'}, selected_style={'fontFamily': 'Poppins'}),
                ]),
            ], style={'width': '100%', 'display': 'inline-block'})
        ], style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px', 'margin-bottom': '20px'}),
        
        html.Div(id='tab-content', style={'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '10px'}),
        
        html.Div([
            html.A("Return to Main Application", href="/", 
                   style={'color': '#3498db', 'textDecoration': 'none', 'fontFamily': 'Poppins'})
        ], style={'textAlign': 'center', 'padding': '20px'})
    ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'})
    
    # Define callbacks
    @dash_app.callback(
        Output('tab-content', 'children'),
        Input('tabs', 'value')
    )
    def render_content(tab):
        if tab == 'tab-1':
            # Accident Heatmap
            if len(df) > 0 and 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
                fig = px.density_mapbox(
                    df, 
                    lat='LATITUDE', 
                    lon='LONGITUDE', 
                    z='SEVERITY' if 'SEVERITY' in df.columns else None,
                    radius=10,
                    center=dict(lat=40.7128, lon=-74.0060),
                    zoom=10,
                    mapbox_style="open-street-map",
                    title="Accident Density Heatmap"
                )
                
                return html.Div([
                    html.H3("Accident Hotspot Heatmap", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("This heatmap shows the density of accidents across NYC. Darker areas indicate higher accident concentration.", 
                           style={'fontFamily': 'Poppins'}),
                    dcc.Graph(figure=fig)
                ])
            else:
                return html.Div([
                    html.H3("Accident Hotspot Heatmap", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("Insufficient data to generate heatmap. Please ensure the dataset contains latitude and longitude information.", 
                           style={'fontFamily': 'Poppins', 'color': '#e74c3c'})
                ])
                
        elif tab == 'tab-2':
            # Time Analysis
            time_figures = []
            
            # Time of day analysis
            if 'TIME_OF_DAY' in df.columns:
                time_of_day_counts = df['TIME_OF_DAY'].value_counts().reset_index()
                time_of_day_counts.columns = ['Time of Day', 'Count']
                
                fig1 = px.pie(
                    time_of_day_counts, 
                    values='Count', 
                    names='Time of Day',
                    title="Accidents by Time of Day",
                    color_discrete_sequence=px.colors.sequential.Plasma
                )
                time_figures.append(dcc.Graph(figure=fig1))
            
            # Day of week analysis
            if 'DAY_OF_WEEK' in df.columns:
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_counts = df['DAY_OF_WEEK'].value_counts().reindex(day_order).reset_index()
                day_counts.columns = ['Day of Week', 'Count']
                
                fig2 = px.bar(
                    day_counts, 
                    x='Day of Week', 
                    y='Count',
                    title="Accidents by Day of Week",
                    color='Count',
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                time_figures.append(dcc.Graph(figure=fig2))
            
            # Monthly analysis
            if 'MONTH' in df.columns and 'YEAR' in df.columns:
                # Group by year and month
                df['Year_Month'] = df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str).str.zfill(2)
                monthly_counts = df['Year_Month'].value_counts().sort_index().reset_index()
                monthly_counts.columns = ['Year-Month', 'Count']
                
                fig3 = px.line(
                    monthly_counts, 
                    x='Year-Month', 
                    y='Count',
                    title="Accident Trends Over Time",
                    markers=True
                )
                time_figures.append(dcc.Graph(figure=fig3))
            
            if time_figures:
                return html.Div([
                    html.H3("Temporal Analysis of Accidents", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("These visualizations show how accidents are distributed across different time periods.", 
                           style={'fontFamily': 'Poppins'}),
                    *time_figures
                ])
            else:
                return html.Div([
                    html.H3("Temporal Analysis of Accidents", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("Insufficient time data to generate visualizations. Please ensure the dataset contains date and time information.", 
                           style={'fontFamily': 'Poppins', 'color': '#e74c3c'})
                ])
                
        elif tab == 'tab-3':
            # Contributing Factors Analysis
            if 'CONTRIBUTING FACTOR VEHICLE 1' in df.columns:
                # Get top factors
                top_factors = df['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(10).reset_index()
                top_factors.columns = ['Factor', 'Count']
                
                # Replace NaN with "Unknown"
                top_factors['Factor'] = top_factors['Factor'].fillna('Unknown')
                
                fig = px.bar(
                    top_factors, 
                    x='Count', 
                    y='Factor',
                    orientation='h',
                    title="Top 10 Contributing Factors",
                    color='Count',
                    color_continuous_scale=px.colors.sequential.Blues
                )
                
                # Generate a matplotlib/seaborn visualization
                fig_mpl, ax = plt.subplots(figsize=(10, 6))
                sns.countplot(y=df['CONTRIBUTING FACTOR VEHICLE 1'].fillna('Unknown').head(10), ax=ax)
                ax.set_title('Top Contributing Factors (Seaborn Visualization)')
                fig_mpl.tight_layout()
                
                # Convert matplotlib figure to base64 for embedding
                buf = io.BytesIO()
                fig_mpl.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode('utf-8')
                plt.close(fig_mpl)
                plt.close('all')  # Ensure all figures are closed
                
                return html.Div([
                    html.H3("Contributing Factors Analysis", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("These visualizations show the most common factors contributing to accidents.", 
                           style={'fontFamily': 'Poppins'}),
                    dcc.Graph(figure=fig),
                    html.H4("Seaborn Visualization", style={'fontFamily': 'Poppins', 'color': '#2c3e50', 'marginTop': '30px'}),
                    html.Img(src=f'data:image/png;base64,{img_str}', style={'width': '100%'})
                ])
            else:
                return html.Div([
                    html.H3("Contributing Factors Analysis", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("Insufficient data to analyze contributing factors. Please ensure the dataset contains contributing factor information.", 
                           style={'fontFamily': 'Poppins', 'color': '#e74c3c'})
                ])
                
        elif tab == 'tab-4':
            # Severity Analysis
            if 'SEVERITY' in df.columns:
                # Create severity bins
                df['Severity_Category'] = pd.cut(
                    df['SEVERITY'],
                    bins=[0, 2, 5, 10, float('inf')],
                    labels=['Low (0-2)', 'Medium (3-5)', 'High (6-10)', 'Very High (>10)']
                )
                
                severity_counts = df['Severity_Category'].value_counts().reset_index()
                severity_counts.columns = ['Severity', 'Count']
                
                fig1 = px.pie(
                    severity_counts, 
                    values='Count', 
                    names='Severity',
                    title="Accident Severity Distribution",
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                
                # Borough severity analysis if available
                borough_fig = None
                if 'BOROUGH' in df.columns:
                    borough_severity = df.groupby('BOROUGH')['SEVERITY'].mean().reset_index()
                    borough_severity.columns = ['Borough', 'Average Severity']
                    borough_severity = borough_severity.sort_values('Average Severity', ascending=False)
                    
                    borough_fig = px.bar(
                        borough_severity,
                        x='Borough',
                        y='Average Severity',
                        title="Average Accident Severity by Borough",
                        color='Average Severity',
                        color_continuous_scale=px.colors.sequential.Reds
                    )
                
                return html.Div([
                    html.H3("Accident Severity Analysis", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("These visualizations show the distribution of accident severity and how it varies across different factors.", 
                           style={'fontFamily': 'Poppins'}),
                    dcc.Graph(figure=fig1),
                    html.Div([dcc.Graph(figure=borough_fig)]) if borough_fig else html.Div()
                ])
            else:
                return html.Div([
                    html.H3("Accident Severity Analysis", style={'fontFamily': 'Poppins', 'color': '#2c3e50'}),
                    html.P("Insufficient data to analyze severity. Please ensure the dataset contains injury and fatality information.", 
                           style={'fontFamily': 'Poppins', 'color': '#e74c3c'})
                ])
                
        # Cluster Analysis tab has been removed
    
    return dash_app

# This function will be imported and used in app.py
def create_dash_app(server):
    return init_dash_app(server)
