import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def convert_data():
    """
    Convert accident data from text to CSV format and perform initial data analysis
    """
    print("Starting data conversion and analysis...")
    
    try:
        # Try to read the text file
        print("Reading data from accidentdata.txt...")
        df = pd.read_csv('accidentdata.txt', sep='\t', low_memory=False)
        print(f"Successfully loaded {len(df)} rows from text file")
        
        # Select only the relevant columns for our analysis
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
        
        # Convert injury and fatality columns to numeric
        numeric_columns = ['NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate severity score (weighted sum of injuries and fatalities)
        if all(col in df.columns for col in numeric_columns):
            df['SEVERITY'] = df['NUMBER OF PERSONS INJURED'] + df['NUMBER OF PERSONS KILLED'] * 5
        
        # Save to CSV
        print("Saving data to accidentdata.csv...")
        df.to_csv('accidentdata.csv', index=False)
        print(f"Successfully saved {len(df)} rows to CSV")
        
        # Generate some initial data visualizations
        print("Generating data visualizations...")
        
        # Create a directory for visualizations if it doesn't exist
        if not os.path.exists('visualizations'):
            os.makedirs('visualizations')
        
        # 1. Borough distribution
        if 'BOROUGH' in df.columns:
            plt.figure(figsize=(10, 6))
            borough_counts = df['BOROUGH'].value_counts()
            sns.barplot(x=borough_counts.index, y=borough_counts.values)
            plt.title('Accidents by Borough')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('visualizations/borough_distribution.png')
            plt.close()
        
        # 2. Contributing factors
        if 'CONTRIBUTING FACTOR VEHICLE 1' in df.columns:
            plt.figure(figsize=(12, 8))
            factor_counts = df['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(10)
            sns.barplot(x=factor_counts.values, y=factor_counts.index)
            plt.title('Top 10 Contributing Factors')
            plt.tight_layout()
            plt.savefig('visualizations/contributing_factors.png')
            plt.close()
        
        # 3. Severity distribution
        if 'SEVERITY' in df.columns:
            plt.figure(figsize=(10, 6))
            sns.histplot(df['SEVERITY'], bins=20, kde=True)
            plt.title('Accident Severity Distribution')
            plt.xlabel('Severity Score')
            plt.tight_layout()
            plt.savefig('visualizations/severity_distribution.png')
            plt.close()
        
        # 4. Accident locations on a scatter plot
        if 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
            plt.figure(figsize=(10, 10))
            plt.scatter(df['LONGITUDE'], df['LATITUDE'], alpha=0.1, s=1)
            plt.title('Accident Locations')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.tight_layout()
            plt.savefig('visualizations/accident_locations.png')
            plt.close()
        
        print("Data conversion and analysis complete!")
        return True
        
    except Exception as e:
        print(f"Error during data conversion: {str(e)}")
        return False

if __name__ == "__main__":
    convert_data()
