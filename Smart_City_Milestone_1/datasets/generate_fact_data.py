import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import random

# --- Constants ---
STATIC_DATA_DIR = "silver_data/static"
DIMENSIONS_DATA_DIR = "silver_data/dimensions"
FACTS_DATA_DIR = "silver_data/facts"

# Input files
ZONES_FILE = os.path.join(STATIC_DATA_DIR, "zones.csv")
EVENTS_FILE = os.path.join(STATIC_DATA_DIR, "event_types.csv")
ROUTES_FILE = os.path.join(STATIC_DATA_DIR, "bus_routes.csv")
BUILDINGS_FILE = os.path.join(DIMENSIONS_DATA_DIR, "buildings.csv")
DEVICES_FILE = os.path.join(DIMENSIONS_DATA_DIR, "devices.csv")
CALENDAR_FILE = os.path.join(DIMENSIONS_DATA_DIR, "calendar.csv")
TRUCKS_FILE = os.path.join(DIMENSIONS_DATA_DIR, "trucks.csv")

# Output files
ENERGY_FILE = os.path.join(FACTS_DATA_DIR, "energy_consumption.csv")
TRAFFIC_FILE = os.path.join(FACTS_DATA_DIR, "traffic.csv")
WASTE_FILE = os.path.join(FACTS_DATA_DIR, "waste_collection.csv")
BUS_GPS_FILE = os.path.join(FACTS_DATA_DIR, "bus_gps.csv")
EMERGENCY_FILE = os.path.join(FACTS_DATA_DIR, "emergency_calls.csv")


def create_directories():
    """Create the facts directory if it doesn't exist."""
    os.makedirs(FACTS_DATA_DIR, exist_ok=True)
    print(f"Directory '{FACTS_DATA_DIR}' is ready.")


def load_data():
    """Loads all necessary dimension and static data."""
    try:
        data = {
            "zones": pd.read_csv(ZONES_FILE),
            "events": pd.read_csv(EVENTS_FILE),
            "routes": pd.read_csv(ROUTES_FILE),
            "buildings": pd.read_csv(BUILDINGS_FILE),
            "devices": pd.read_csv(DEVICES_FILE),
            "calendar": pd.read_csv(CALENDAR_FILE),
            "trucks": pd.read_csv(TRUCKS_FILE)
        }
        print("All source data files loaded successfully.")
        return data
    except FileNotFoundError as e:
        print(f"Error loading data: {e}. Please ensure all static and dimension data files exist.")
        return None

# --- Fact Table Generation Functions ---

def generate_energy_consumption(buildings_df, devices_df, calendar_df):
    """Generates hourly energy consumption data for each building."""
    energy_meters = devices_df[devices_df['device_type'] == 'Energy Meter'].copy()
    
    # Filter out 'No Building' record which doesn't consume energy
    building_ids = buildings_df[buildings_df['building_id'] != 'B000']['building_id'].unique()
    
    if len(energy_meters) < len(building_ids):
        raise ValueError("Not enough energy meters for all buildings.")
    
    building_device_map = pd.DataFrame({
        'building_id': building_ids,
        'device_id': energy_meters['device_id'].head(len(building_ids)).values
    })

    timestamps = pd.to_datetime(pd.date_range(start="2025-09-01", end="2025-09-30 23:59:59", freq='h'))
    time_df = pd.DataFrame({'timestamp': timestamps})
    time_df['date_key'] = time_df['timestamp'].dt.strftime('%Y%m%d').astype(int)
    time_df['time_key'] = time_df['timestamp'].dt.strftime('%H%M%S')

    df = pd.merge(time_df, building_device_map, how='cross')
    df = pd.merge(df, buildings_df[['building_id', 'building_type']], on='building_id')

    kwh_patterns = {
        'Residential': (1.5, 5.0), 'Commercial': (15, 50),
        'Educational': (10, 30), 'Mall': (100, 500), 'Hospital': (80, 200)
    }
    
    df['kwh'] = df['building_type'].apply(lambda x: np.random.normal(loc=(kwh_patterns[x][0] + kwh_patterns[x][1]) / 2, scale=(kwh_patterns[x][1] - kwh_patterns[x][0]) / 6))
    df['kwh'] = df['kwh'].clip(lower=0.1).round(4)
    
    df['voltage'] = np.random.normal(loc=220, scale=5, size=len(df)).round(2)
    df['current'] = (df['kwh'] * 1000 / df['voltage']).round(4)
    df['quality_flag'] = np.random.choice(["OK", "SUSPECT"], p=[0.98, 0.02], size=len(df))
    
    return df[['date_key', 'time_key', 'building_id', 'device_id', 'kwh', 'voltage', 'current', 'quality_flag']]

def generate_traffic(zones_df, devices_df, calendar_df, num_sensors=50):
    """Generates 5-minute traffic data from sensors."""
    traffic_sensors = devices_df[devices_df['device_type'] == 'Traffic Sensor'].head(num_sensors).copy()
    
    # Assign sensors to real zones, not 'No Zone'
    real_zone_ids = zones_df[zones_df['zone_id'] != 'Z0']['zone_id']
    traffic_sensors['zone_id'] = np.random.choice(real_zone_ids, size=len(traffic_sensors))
    
    timestamps = pd.to_datetime(pd.date_range(start="2025-09-01", end="2025-09-30 23:59:59", freq='5min'))
    time_df = pd.DataFrame({'timestamp': timestamps})
    time_df['date_key'] = time_df['timestamp'].dt.strftime('%Y%m%d').astype(int)
    time_df['time_key'] = time_df['timestamp'].dt.strftime('%H%M%S')
    time_df['hour'] = time_df['timestamp'].dt.hour
    
    df = pd.merge(time_df, traffic_sensors[['device_id', 'zone_id']], how='cross')

    is_peak = df['hour'].isin(list(range(7, 10)) + list(range(16, 20)))
    
    df['vehicle_count'] = np.where(is_peak,
                                   np.random.randint(100, 301, size=len(df)),
                                   np.random.randint(10, 51, size=len(df)))
    
    df['avg_speed_kmh'] = np.where(is_peak,
                                   np.random.normal(loc=20, scale=5, size=len(df)),
                                   np.random.normal(loc=45, scale=8, size=len(df)))
    df['avg_speed_kmh'] = df['avg_speed_kmh'].clip(lower=10, upper=80).round(2)

    return df[['date_key', 'time_key', 'zone_id', 'device_id', 'vehicle_count', 'avg_speed_kmh']]

def generate_waste_collection(zones_df, buildings_df, calendar_df, trucks_df, num_containers=100):
    """Generates daily waste container readings."""
    containers = buildings_df.sample(num_containers, replace=True).reset_index(drop=True)
    containers['container_id'] = [f"C{str(i+1).zfill(3)}" for i in range(num_containers)]
    
    active_trucks = trucks_df[trucks_df['status'] == 'Active']['truck_id'].tolist()
    if not active_trucks:
        raise ValueError("No active trucks available for waste collection.")
    
    records = []
    fill_levels = {cid: random.randint(5, 30) for cid in containers['container_id']}
    time_key_8am = '080000'

    for _, row in calendar_df.iterrows():
        for _, container in containers.iterrows():
            fill_level = fill_levels[container['container_id']]
            
            truck_id = None
            if fill_level > 80:
                truck_id = random.choice(active_trucks)
                fill_level = random.randint(5, 15)
            else:
                fill_level += random.randint(10, 25)
            
            fill_levels[container['container_id']] = min(fill_level, 100)

            records.append({
                'date_key': row['date_key'],
                'time_key': time_key_8am,
                'zone_id': container['zone_id'],
                'building_id': container['building_id'],
                'container_id': container['container_id'],
                'fill_level_percent': fill_levels[container['container_id']],
                'truck_id': truck_id
            })
            
    df = pd.DataFrame(records)
    df['truck_id'] = df['truck_id'].fillna('T000')
    return df

def generate_bus_gps(zones_df, routes_df, calendar_df, num_buses=30):
    """Generates 5-minute bus GPS tracking data."""
    buses = pd.DataFrame({
        'bus_id': [f"BUS{str(i+1).zfill(2)}" for i in range(num_buses)],
        'route_id': np.random.choice(routes_df[routes_df['active_status'] == 'Active']['route_id'], num_buses)
    })
    
    timestamps = pd.to_datetime(pd.date_range(start="2025-09-01", end="2025-09-30 23:59:59", freq='5min'))
    time_df = pd.DataFrame({'timestamp': timestamps})
    time_df['date_key'] = time_df['timestamp'].dt.strftime('%Y%m%d').astype(int)
    time_df['time_key'] = time_df['timestamp'].dt.strftime('%H%M%S')
    time_df['hour'] = time_df['timestamp'].dt.hour

    df = pd.merge(time_df, buses, how='cross')

    # Assign buses to real zones, not 'No Zone'
    real_zone_ids = zones_df[zones_df['zone_id'] != 'Z0']['zone_id']
    df['zone_id'] = np.random.choice(real_zone_ids, len(df))

    df = pd.merge(df, zones_df, on='zone_id')

    df['lat'] = df.apply(lambda row: np.random.uniform(row['lat_min'], row['lat_max']), axis=1).round(6)
    df['lon'] = df.apply(lambda row: np.random.uniform(row['lon_min'], row['lon_max']), axis=1).round(6)

    is_peak = df['hour'].isin(list(range(7, 10)) + list(range(16, 20)))
    df['speed_kmh'] = np.where(is_peak, 
                              np.random.normal(loc=25, scale=5, size=len(df)),
                              np.random.normal(loc=45, scale=10, size=len(df))).clip(0, 60).round(2)
    df['occupancy_est'] = np.where(is_peak,
                                  np.random.randint(30, 61, size=len(df)),
                                  np.random.randint(10, 21, size=len(df)))

    return df[['date_key', 'time_key', 'bus_id', 'route_id', 'zone_id', 'lat', 'lon', 'speed_kmh', 'occupancy_est']]

def generate_emergency_calls(data):
    """Generates emergency call records."""
    start_time = datetime(2025, 9, 1)
    end_time = datetime(2025, 9, 30, 23, 59, 59)
    total_seconds = int((end_time - start_time).total_seconds())

    num_days = data['calendar']['date'].nunique()
    total_calls = num_days * random.randint(10, 15)
    
    # Use real zones for events that are not tied to a specific building
    real_zone_ids = data['zones'][data['zones']['zone_id'] != 'Z0']['zone_id']
    
    records = []
    for i in range(total_calls):
        random_seconds = random.randint(0, total_seconds)
        reported_at = start_time + timedelta(seconds=random_seconds)
        
        priority = np.random.choice(['High', 'Medium', 'Low'], p=[0.2, 0.5, 0.3])
        if priority == 'High':
            response_time = random.randint(5, 30)
        elif priority == 'Medium':
            response_time = random.randint(30, 60)
        else:
            response_time = random.randint(60, 120)
            
        building_id = random.choice(data['buildings']['building_id']) if random.random() > 0.3 else None
        resolved_at = reported_at + timedelta(minutes=response_time)
        
        records.append({
            'call_id': f"E{str(i+1).zfill(3)}",
            'date_key': int(reported_at.strftime('%Y%m%d')),
            'time_key': reported_at.strftime('%H%M%S'),
            'zone_id': np.random.choice(real_zone_ids),
            'building_id': building_id,
            'event_type_id': random.choice(data['events']['event_type_id']),
            'priority_level': priority,
            'reported_at': reported_at,
            'resolved_at': resolved_at,
            'response_time_minutes': response_time
        })
    df = pd.DataFrame(records)
    df['building_id'] = df['building_id'].fillna('B000')
    return df[['call_id', 'date_key', 'time_key', 'zone_id', 'building_id', 'event_type_id', 'priority_level', 'reported_at', 'resolved_at', 'response_time_minutes']]


def main():
    """Main function to generate all fact data and save to CSV."""
    print("Starting fact data generation process...")
    create_directories()
    
    data = load_data()
    if data is None:
        return

    # Generate each fact table
    print("Generating Energy Consumption data...")
    energy_df = generate_energy_consumption(data['buildings'], data['devices'], data['calendar'])
    
    print("Generating Traffic data...")
    traffic_df = generate_traffic(data['zones'], data['devices'], data['calendar'])
    
    print("Generating Waste Collection data...")
    waste_df = generate_waste_collection(data['zones'], data['buildings'], data['calendar'], data['trucks'])
    
    print("Generating Bus GPS data...")
    bus_gps_df = generate_bus_gps(data['zones'], data['routes'], data['calendar'])
    
    print("Generating Emergency Calls data...")
    emergency_df = generate_emergency_calls(data)

    # Save to CSV
    energy_df.to_csv(ENERGY_FILE, index=False, encoding='utf-8')
    traffic_df.to_csv(TRAFFIC_FILE, index=False, encoding='utf-8')
    waste_df.to_csv(WASTE_FILE, index=False, encoding='utf-8')
    bus_gps_df.to_csv(BUS_GPS_FILE, index=False, encoding='utf-8')
    emergency_df.to_csv(EMERGENCY_FILE, index=False, encoding='utf-8')
    
    print("\n--- Fact Data Generation Summary ---")
    files = {
        ENERGY_FILE: energy_df, TRAFFIC_FILE: traffic_df, WASTE_FILE: waste_df,
        BUS_GPS_FILE: bus_gps_df, EMERGENCY_FILE: emergency_df
    }
    for path, df in files.items():
        print(f"✅ Generated {len(df)} rows for '{os.path.basename(path)}'")
        print(f"Sample of '{os.path.basename(path)}':")
        print(df.head())
        print("-" * 30)
        
    print("\nAll fact files saved successfully.")

if __name__ == "__main__":
    main()
