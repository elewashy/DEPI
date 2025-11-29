import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import random

# --- Constants ---
STATIC_DATA_DIR = "silver_data/static"
DIMENSIONS_DATA_DIR = "silver_data/dimensions"
ZONES_FILE = os.path.join(STATIC_DATA_DIR, "zones.csv")
BUILDINGS_FILE = os.path.join(DIMENSIONS_DATA_DIR, "buildings.csv")
DEVICES_FILE = os.path.join(DIMENSIONS_DATA_DIR, "devices.csv")
CALENDAR_FILE = os.path.join(DIMENSIONS_DATA_DIR, "calendar.csv")
TRUCKS_FILE = os.path.join(DIMENSIONS_DATA_DIR, "trucks.csv")

# --- Realistic Data Samples ---
ARABIC_OWNER_NAMES = [
    "Mohamed Adel", "Ahmed Mahmoud", "Youssef Hassan", "Omar Khaled", "Ali Ibrahim",
    "Fatima Zahra", "Mariam Ahmed", "Aya Mohamed", "Salma Ali", "Nourhan Tarek",
    "Khaled El Masry", "Tarek El Shenawy", "Mona Abdelaziz", "Hassan El Shafei", "Amr Diab"
]
ARABIC_STREETS = [
    "El Teseen St.", "El Sadat Axis", "Gamal Abdel Nasser Axis", "Mostafa Kamel Axis",
    "North Investors Area", "South Investors Area", "El Choueifat St.", "El Zohour District"
]
MANUFACTURERS = ["Siemens", "Bosch", "Cisco", "Huawei", "General Electric", "Schneider Electric", "Honeywell"]

def create_directories():
    """Create the necessary directory structure if it doesn't exist."""
    os.makedirs(DIMENSIONS_DATA_DIR, exist_ok=True)
    print(f"Directory '{DIMENSIONS_DATA_DIR}' is ready.")

def generate_buildings_data(zones_df: pd.DataFrame, num_buildings: int = 300) -> pd.DataFrame:
    """Generates a DataFrame for buildings, ensuring lat/lon are within zone boundaries."""
    buildings_data = []
    
    # Add a record for 'No Building'
    buildings_data.append({
        "building_id": "B000",
        "building_name": "No Building",
        "zone_id": "Z0",
        "building_type": "N/A",
        "owner_name": "N/A",
        "address": "N/A",
        "lat": 0.0,
        "lon": 0.0,
        "status": "N/A"
    })

    building_types = np.random.choice(
        ["Residential", "Commercial", "Educational", "Mall", "Hospital"],
        size=num_buildings,
        p=[0.50, 0.20, 0.10, 0.10, 0.10]
    )

    # Filter out 'No Zone' for assigning to real buildings
    real_zones_df = zones_df[zones_df['zone_id'] != 'Z0']

    for i in range(num_buildings):
        building_id = f"B{str(i+1).zfill(3)}"
        
        # Assign to a random zone
        zone = real_zones_df.sample(1).iloc[0]
        zone_id = zone['zone_id']
        
        # Generate lat/lon within the zone's boundaries
        lat = np.random.uniform(zone['lat_min'], zone['lat_max'])
        lon = np.random.uniform(zone['lon_min'], zone['lon_max'])
        
        building_type = building_types[i]
        
        # Generate realistic names
        if building_type == "Residential":
            building_name = f"Villa {random.randint(1, 200)}"
        elif building_type == "Commercial":
            building_name = f"{random.choice(['Misr', 'Delta', 'Cairo'])} Tower"
        elif building_type == "Educational":
            building_name = f"{random.choice(['Future', 'Al-Alson', 'Modern'])} School"
        elif building_type == "Mall":
            building_name = f"{random.choice(['Downtown', 'Point 90', 'Concorde'])} Mall"
        else: # Hospital
            building_name = f"{random.choice(['El-Fouad', 'El-Karma', 'Cleopatra'])} Hospital"

        buildings_data.append({
            "building_id": building_id,
            "building_name": building_name,
            "zone_id": zone_id,
            "building_type": building_type,
            "owner_name": random.choice(ARABIC_OWNER_NAMES),
            "address": f"{random.randint(1, 100)} {random.choice(ARABIC_STREETS)}",
            "lat": lat,
            "lon": lon,
            "status": np.random.choice(["Active", "Under Maintenance", "Planned"], p=[0.9, 0.07, 0.03])
        })
        
    df = pd.DataFrame(buildings_data)
    df[['lat', 'lon']] = df[['lat', 'lon']].astype(float).round(6)
    return df

def generate_devices_data(buildings_df: pd.DataFrame, num_devices: int = 600) -> pd.DataFrame:
    """Generates a DataFrame for devices, linking them to buildings where appropriate."""
    devices_data = []
    building_ids = buildings_df['building_id'].tolist()
    num_buildings = len(building_ids)

    # Ensure at least one energy meter per building
    device_types = ["Energy Meter"] * num_buildings
    
    # Fill the rest with a random distribution
    remaining_devices = num_devices - num_buildings
    device_types.extend(np.random.choice(
        ["Traffic Sensor", "Waste Sensor", "Bus GPS Device"],
        size=remaining_devices,
        p=[0.4, 0.3, 0.3] # Adjust probabilities for the remainder
    ))
    random.shuffle(device_types)

    for i in range(num_devices):
        device_id = f"D{str(i+1).zfill(3)}"
        device_type = device_types[i]
        
        # Assign building_id based on device type
        b_id = None
        if device_type in ["Energy Meter", "Waste Sensor"]:
            b_id = random.choice(building_ids)
        
        # Generate a random installation date in the last 3 years
        install_date = (datetime.now() - timedelta(days=random.randint(0, 3*365))).date()
        
        devices_data.append({
            "device_id": device_id,
            "device_type": device_type,
            "building_id": b_id,
            "install_date": install_date,
            "status": np.random.choice(["Active", "Inactive", "Under Maintenance"], p=[0.9, 0.05, 0.05]),
            "manufacturer": random.choice(MANUFACTURERS)
        })

    df = pd.DataFrame(devices_data)
    df['building_id'] = df['building_id'].fillna('B000')
    return df

def generate_calendar_data() -> pd.DataFrame:
    """Generates a calendar dimension for 30 days."""
    date_range = pd.to_datetime(pd.date_range(start="2025-09-01", end="2025-09-30", freq='D'))
    
    calendar_df = pd.DataFrame()
    calendar_df['date'] = date_range
    calendar_df['date_key'] = calendar_df['date'].dt.strftime('%Y%m%d').astype(int)
    calendar_df['day'] = calendar_df['date'].dt.day
    calendar_df['month'] = calendar_df['date'].dt.month
    calendar_df['month_name'] = calendar_df['date'].dt.month_name()
    calendar_df['year'] = calendar_df['date'].dt.year
    calendar_df['week_day'] = calendar_df['date'].dt.day_name()
    calendar_df['week_number'] = calendar_df['date'].dt.isocalendar().week.astype(int)
    calendar_df['is_weekend'] = calendar_df['week_day'].isin(['Friday', 'Saturday'])
    
    # Reorder columns to match specification
    return calendar_df[['date_key', 'date', 'day', 'month', 'month_name', 'year', 'week_day', 'week_number', 'is_weekend']]


def generate_trucks_data(num_trucks: int = 15) -> pd.DataFrame:
    """Generates a DataFrame for waste collection trucks."""
    trucks_data = []
    
    # Add a record for 'No Truck'
    trucks_data.append({
        "truck_id": "T000",
        "truck_type": "No Truck",
        "capacity_tons": 0,
        "fuel_type": "N/A",
        "status": "N/A"
    })

    truck_types = ["Compactor", "Recycling", "Organic"]
    fuel_types = ["Diesel", "CNG", "Electric"]
    
    for i in range(num_trucks):
        truck_id = f"T{str(i+1).zfill(3)}"
        trucks_data.append({
            "truck_id": truck_id,
            "truck_type": random.choice(truck_types),
            "capacity_tons": random.choice([5, 7, 10]),
            "fuel_type": random.choice(fuel_types),
            "status": np.random.choice(["Active", "Under Maintenance"], p=[0.85, 0.15])
        })
        
    return pd.DataFrame(trucks_data)


def main():
    """
    Main function to generate all dimension data, save it to CSV files,
    and print a summary.
    """
    print("Starting dimension data generation process...")
    
    # 1. Create directory
    create_directories()
    
    # 2. Load static data needed for relationships
    try:
        zones_df = pd.read_csv(ZONES_FILE)
        print(f"Successfully loaded '{ZONES_FILE}'.")
    except FileNotFoundError:
        print(f"Error: Static zones file not found at '{ZONES_FILE}'. Please generate static data first.")
        return

    # 3. Generate Dimension DataFrames
    buildings_df = generate_buildings_data(zones_df, num_buildings=300)
    devices_df = generate_devices_data(buildings_df, num_devices=600)
    calendar_df = generate_calendar_data()
    trucks_df = generate_trucks_data(num_trucks=15)
    
    # 4. Save DataFrames to CSV
    buildings_df.to_csv(BUILDINGS_FILE, index=False, encoding='utf-8')
    devices_df.to_csv(DEVICES_FILE, index=False, encoding='utf-8')
    calendar_df.to_csv(CALENDAR_FILE, index=False, encoding='utf-8')
    trucks_df.to_csv(TRUCKS_FILE, index=False, encoding='utf-8')
    
    print("\n--- Dimension Data Generation Summary ---")
    print(f"✅ Generated {len(buildings_df)} rows for '{BUILDINGS_FILE}'")
    print(f"✅ Generated {len(devices_df)} rows for '{DEVICES_FILE}'")
    print(f"✅ Generated {len(calendar_df)} rows for '{CALENDAR_FILE}'")
    print(f"✅ Generated {len(trucks_df)} rows for '{TRUCKS_FILE}'")
    
    print("\n--- Data Previews ---")
    print(f"\nSample of '{os.path.basename(BUILDINGS_FILE)}':")
    print(buildings_df.head())
    print(f"\nSample of '{os.path.basename(DEVICES_FILE)}':")
    print(devices_df.head())
    print(f"\nSample of '{os.path.basename(CALENDAR_FILE)}':")
    print(calendar_df.head())
    print(f"\nSample of '{os.path.basename(TRUCKS_FILE)}':")
    print(trucks_df.head())
    
    print("\nAll dimension files saved successfully.")

if __name__ == "__main__":
    main()
