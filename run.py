import os
import subprocess
import sys

def check_requirements():
    """Run the checkrequirements.py script"""
    print("Checking required packages...")
    subprocess.call([sys.executable, "checkrequirements.py"])

def convert_data():
    """Run the convert_data.py script"""
    print("Converting accident data...")
    subprocess.call([sys.executable, "convert_data.py"])

def run_app():
    """Run the Flask application"""
    print("Starting the Flask application...")
    subprocess.call([sys.executable, "app.py"])

if __name__ == "__main__":
    # Check if the required packages are installed
    check_requirements()
    
    # Convert the data if needed
    convert_data()
    
    # Run the Flask application
    run_app()
