import os
import pandas as pd
from sqlalchemy import text
import time
import numpy as np

# Adjust the path to go up one level to the project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_engine

def get_tables():
    """Returns a list of table names to be processed."""
    return [
        "buildings", "calendar", "devices", "trucks",
        "bus_gps", "emergency_calls", "energy_consumption", "traffic", "waste_collection",
        "bus_routes", "event_types", "zones"
    ]

def clean_data(df, table_name):
    """Applies specific cleaning rules to the dataframe."""
    
    # General cleaning: trim whitespace from all string columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()

    # Specific cleaning rules based on the silver SQL script
    if table_name == 'devices':
        df['building_id'] = df['building_id'].replace('', np.nan)
    
    if table_name == 'emergency_calls':
        df['building_id'] = df['building_id'].replace('', np.nan)

    if table_name == 'waste_collection':
        df['building_id'] = df['building_id'].replace('', np.nan)
        df['truck_id'] = df['truck_id'].replace('', np.nan)

    return df

def load_silver_layer():
    """
    Loads data from the bronze layer, cleans it, and inserts it into the silver layer.
    """
    print("================================================")
    print("Loading Silver Layer")
    print("================================================")
    
    engine = get_db_engine()
    tables = get_tables()
    
    total_start_time = time.time()

    with engine.connect() as conn:
        for table_name in tables:
            start_time = time.time()
            
            bronze_table = f"bronze.{table_name}"
            silver_table = f"silver.{table_name}"
            
            print(f">> Reading data from: {bronze_table}")
            df = pd.read_sql_table(table_name, conn, schema='bronze')

            print(f">> Cleaning data for: {table_name}")
            df_cleaned = clean_data(df, table_name)
            
            print(f">> Truncating Table: {silver_table}")
            conn.execute(text(f"TRUNCATE TABLE {silver_table}"))
            
            print(f">> Inserting Data Into: {silver_table}")
            df_cleaned.to_sql(table_name, conn, schema='silver', if_exists='append', index=False, chunksize=1000)
            
            end_time = time.time()
            print(f">> Load Duration for {table_name}: {end_time - start_time:.2f} seconds")
            print(">> -------------")
            
        conn.commit()

    total_end_time = time.time()
    print("==========================================")
    print("Loading Silver Layer is Completed")
    print(f"   - Total Load Duration: {total_end_time - total_start_time:.2f} seconds")
    print("==========================================")


if __name__ == '__main__':
    load_silver_layer()
