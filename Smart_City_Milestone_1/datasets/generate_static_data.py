import pandas as pd
import os
import numpy as np

# --- Constants ---
DATA_DIR = "silver_data/static"
ZONES_FILE = os.path.join(DATA_DIR, "zones.csv")
EVENTS_FILE = os.path.join(DATA_DIR, "event_types.csv")
ROUTES_FILE = os.path.join(DATA_DIR, "bus_routes.csv")

# Overall boundaries for El Tagamoa El Khames
TAGAMOA_LAT_MIN, TAGAMOA_LAT_MAX = 30.010, 30.040
TAGAMOA_LON_MIN, TAGAMOA_LON_MAX = 31.480, 31.520


def create_directories():
    """Create the necessary directory structure if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Directory '{DATA_DIR}' is ready.")


def generate_zones_data() -> pd.DataFrame:
    """
    Generates a DataFrame for 5 non-overlapping zones in El Tagamoa El Khames.
    The zones are created by partitioning the total geographic area.
    """
    zones_data = [
        {
            "zone_id": "Z0",
            "zone_name": "No Zone",
            "lat_min": 0.0,
            "lat_max": 0.0,
            "lon_min": 0.0,
            "lon_max": 0.0,
            "description": "Represents events or entities not associated with a specific zone."
        },
        {
            "zone_id": "Z1",
            "zone_name": "Zone A - South 90",
            "lat_min": TAGAMOA_LAT_MIN,
            "lat_max": 30.025,
            "lon_min": TAGAMOA_LON_MIN,
            "lon_max": 31.500,
            "description": "Busy commercial and residential area along South 90th Street."
        },
        {
            "zone_id": "Z2",
            "zone_name": "Zone B - North 90",
            "lat_min": TAGAMOA_LAT_MIN,
            "lat_max": 30.025,
            "lon_min": 31.500,
            "lon_max": TAGAMOA_LON_MAX,
            "description": "Major commercial hub with large malls like Cairo Festival City."
        },
        {
            "zone_id": "Z3",
            "zone_name": "Zone C - AUC Area",
            "lat_min": 30.025,
            "lat_max": TAGAMOA_LAT_MAX,
            "lon_min": TAGAMOA_LON_MIN,
            "lon_max": 31.495,
            "description": "The American University in Cairo campus and surrounding educational facilities."
        },
        {
            "zone_id": "Z4",
            "zone_name": "Zone D - Residential Districts",
            "lat_min": 30.025,
            "lat_max": TAGAMOA_LAT_MAX,
            "lon_min": 31.495,
            "lon_max": 31.510,
            "description": "Primarily residential neighborhoods with villas and apartments."
        },
        {
            "zone_id": "Z5",
            "zone_name": "Zone E - Governmental Services",
            "lat_min": 30.025,
            "lat_max": TAGAMOA_LAT_MAX,
            "lon_min": 31.510,
            "lon_max": TAGAMOA_LON_MAX,
            "description": "Contains governmental buildings, police stations, and public service centers."
        }
    ]
    
    df = pd.DataFrame(zones_data)
    # Ensure float precision
    float_cols = ['lat_min', 'lat_max', 'lon_min', 'lon_max']
    df[float_cols] = df[float_cols].astype(float).round(6)
    return df


def generate_event_types_data() -> pd.DataFrame:
    """Generates a DataFrame for the fixed list of emergency event types."""
    event_types_data = [
        {"event_type_id": "ET01", "event_type_name": "Fire", "description": "Reports of fire incidents in buildings or public spaces."},
        {"event_type_id": "ET02", "event_type_name": "Accident", "description": "Traffic accidents involving vehicles, pedestrians, or property damage."},
        {"event_type_id": "ET03", "event_type_name": "Medical Emergency", "description": "Urgent medical situations requiring immediate attention, like heart attacks or injuries."},
        {"event_type_id": "ET04", "event_type_name": "Crime Report", "description": "Reports of criminal activities such as theft, assault, or vandalism."},
        {"event_type_id": "ET05", "event_type_name": "Power Outage", "description": "Disruption of electrical power in a specific area."},
        {"event_type_id": "ET06", "event_type_name": "Water Leakage", "description": "Reports of major water pipe bursts or significant leakages."},
        {"event_type_id": "ET07", "event_type_name": "Gas Leak", "description": "Detection of natural gas leaks, posing an explosion risk."}
    ]
    return pd.DataFrame(event_types_data)


def generate_bus_routes_data() -> pd.DataFrame:
    """Generates a DataFrame for realistic bus routes within El Tagamoa El Khames."""
    routes_data = [
        {"route_id": "R01", "route_name": "Route 1 - Ring Road to AUC", "start_point": "Ring Road Station", "end_point": "AUC Gate 4", "distance_km": 11.5, "active_status": "Active"},
        {"route_id": "R02", "route_name": "Route 2 - CFC Mall to M. Naguib Axis", "start_point": "Cairo Festival City Mall", "end_point": "Mohamed Naguib Axis", "distance_km": 8.2, "active_status": "Active"},
        {"route_id": "R03", "route_name": "Route 3 - Downtown Mall to 90th St.", "start_point": "Downtown Mall", "end_point": "90th Street Metro Market", "distance_km": 4.5, "active_status": "Active"},
        {"route_id": "R04", "route_name": "Route 4 - North Investors to Air Force Hospital", "start_point": "El Mostashmereen El Shamaleya", "end_point": "Air Force Hospital", "distance_km": 9.8, "active_status": "Active"},
        {"route_id": "R05", "route_name": "Route 5 - AUC to CFC Mall", "start_point": "AUC Gate 4", "end_point": "Cairo Festival City Mall", "distance_km": 5.1, "active_status": "Active"},
        {"route_id": "R06", "route_name": "Route 6 - Ring Road to Downtown Mall", "start_point": "Ring Road Station", "end_point": "Downtown Mall", "distance_km": 7.3, "active_status": "Active"},
        {"route_id": "R07", "route_name": "Route 7 - Police Station to Air Force Hospital", "start_point": "Tagamoa Police Station", "end_point": "Air Force Hospital", "distance_km": 6.5, "active_status": "Active"},
        {"route_id": "R08", "route_name": "Route 8 - M. Naguib Axis to Ring Road", "start_point": "Mohamed Naguib Axis", "end_point": "Ring Road Station", "distance_km": 10.2, "active_status": "Active"},
        {"route_id": "R09", "route_name": "Route 9 - 90th St. to North Investors", "start_point": "90th Street Metro Market", "end_point": "El Mostashmereen El Shamaleya", "distance_km": 5.8, "active_status": "Inactive"},
        {"route_id": "R10", "route_name": "Route 10 - AUC to Police Station", "start_point": "AUC Gate 4", "end_point": "Tagamoa Police Station", "distance_km": 3.4, "active_status": "Inactive"}
    ]
    
    df = pd.DataFrame(routes_data)
    df['distance_km'] = df['distance_km'].astype(float).round(2)
    return df


def main():
    """
    Main function to generate all static data, save it to CSV files,
    and print a summary of the generated data.
    """
    print("Starting data generation process for Smart City project...")
    
    # 1. Create directory structure
    create_directories()
    
    # 2. Generate DataFrames
    zones_df = generate_zones_data()
    event_types_df = generate_event_types_data()
    bus_routes_df = generate_bus_routes_data()
    
    # 3. Save DataFrames to CSV
    zones_df.to_csv(ZONES_FILE, index=False, encoding='utf-8')
    event_types_df.to_csv(EVENTS_FILE, index=False, encoding='utf-8')
    bus_routes_df.to_csv(ROUTES_FILE, index=False, encoding='utf-8')
    
    print("\n--- Data Generation Summary ---")
    print(f"✅ Generated {len(zones_df)} rows for '{ZONES_FILE}'")
    print(f"✅ Generated {len(event_types_df)} rows for '{EVENTS_FILE}'")
    print(f"✅ Generated {len(bus_routes_df)} rows for '{ROUTES_FILE}'")
    print("\nAll files saved successfully.")


if __name__ == "__main__":
    main()
