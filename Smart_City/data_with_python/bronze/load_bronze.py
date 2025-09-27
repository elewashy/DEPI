import os
import pandas as pd
from sqlalchemy import text
import time

# Adjust the path to go up one level to the project root
# This allows the script to be run from the 'bronze' directory 
# while finding the 'database.py' and '.env' at the project root level.
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_engine

def get_csv_files_info():
    """
    Returns a dictionary with table names as keys and their corresponding CSV file paths.
    """
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'datasets', 'silver_data')
    
    files_info = {
        # Dimensions
        "buildings": os.path.join(base_path, 'dimensions', 'buildings.csv'),
        "calendar": os.path.join(base_path, 'dimensions', 'calendar.csv'),
        "devices": os.path.join(base_path, 'dimensions', 'devices.csv'),
        "trucks": os.path.join(base_path, 'dimensions', 'trucks.csv'),
        # Facts
        "bus_gps": os.path.join(base_path, 'facts', 'bus_gps.csv'),
        "emergency_calls": os.path.join(base_path, 'facts', 'emergency_calls.csv'),
        "energy_consumption": os.path.join(base_path, 'facts', 'energy_consumption.csv'),
        "traffic": os.path.join(base_path, 'facts', 'traffic.csv'),
        "waste_collection": os.path.join(base_path, 'facts', 'waste_collection.csv'),
        # Static
        "bus_routes": os.path.join(base_path, 'static', 'bus_routes.csv'),
        "event_types": os.path.join(base_path, 'static', 'event_types.csv'),
        "zones": os.path.join(base_path, 'static', 'zones.csv'),
    }
    return files_info

def load_bronze_layer():
    """
    Loads data from CSV files into the bronze layer tables.
    It truncates the tables before inserting new data.
    """
    print("================================================")
    print("Loading Bronze Layer")
    print("================================================")
    
    engine = get_db_engine()
    files_info = get_csv_files_info()
    
    total_start_time = time.time()

    with engine.connect() as conn:
        for table_name, file_path in files_info.items():
            start_time = time.time()
            full_table_name = f"bronze.{table_name}"
            
            print(f">> Truncating Table: {full_table_name}")
            conn.execute(text(f"TRUNCATE TABLE {full_table_name}"))
            
            print(f">> Inserting Data Into: {full_table_name} from {os.path.basename(file_path)}")
            df = pd.read_csv(file_path)
            
            # Write the data to the table
            df.to_sql(table_name, conn, schema='bronze', if_exists='append', index=False, chunksize=1000)
            
            end_time = time.time()
            print(f">> Load Duration: {end_time - start_time:.2f} seconds")
            print(">> -------------")
            
        conn.commit() # Commit the transaction

    total_end_time = time.time()
    print("==========================================")
    print("Loading Bronze Layer is Completed")
    print(f"   - Total Load Duration: {total_end_time - total_start_time:.2f} seconds")
    print("==========================================")


if __name__ == '__main__':
    load_bronze_layer()
