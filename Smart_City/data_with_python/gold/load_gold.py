import os
import pandas as pd
from sqlalchemy import text
import time

# Adjust the path to go up one level to the project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_engine

def load_non_scd_dimensions(engine):
    """
    Loads non-SCD dimensions from silver to gold, inserting only new records.
    """
    print("Loading non-SCD dimensions...")
    dims = {
        'dim_calendar': 'date_key',
        'dim_devices': 'device_id',
        'dim_trucks': 'truck_id',
        'dim_zones': 'zone_id',
        'dim_event_types': 'event_type_id',
        'dim_bus_routes': 'route_id'
    }
    
    with engine.connect() as conn:
        for dim_table, business_key in dims.items():
            source_table = dim_table.replace('dim_', '')
            
            # Read source and target tables
            df_silver = pd.read_sql_table(source_table, conn, schema='silver')
            df_gold = pd.read_sql_table(dim_table, conn, schema='gold')

            # Find new records
            new_records = df_silver[~df_silver[business_key].isin(df_gold[business_key])]

            if not new_records.empty:
                print(f">> Inserting {len(new_records)} new records into gold.{dim_table}")
                # For dim_calendar, date_sk is the same as date_key
                if dim_table == 'dim_calendar':
                    new_records = new_records.rename(columns={'date_key': 'date_sk'})
                    # Reorder columns to match gold table
                    cols = [c.name for c in pd.read_sql_table(dim_table, conn, schema='gold', limit=0).columns]
                    new_records['date_sk'] = new_records[business_key]
                
                # Prepare data for insertion (remove dwh_create_date)
                if 'dwh_create_date' in new_records.columns:
                    new_records = new_records.drop(columns=['dwh_create_date'])
                
                new_records.to_sql(dim_table, conn, schema='gold', if_exists='append', index=False)
            else:
                print(f">> No new records for gold.{dim_table}")
        conn.commit()
    print("Non-SCD dimensions loaded.")


def load_scd2_buildings(engine):
    """
    Loads the dim_buildings dimension using SCD Type 2 logic.
    """
    print("Loading buildings dimension (SCD Type 2)...")
    with engine.connect() as conn:
        df_silver = pd.read_sql_table('buildings', conn, schema='silver')
        df_gold = pd.read_sql_query("SELECT * FROM gold.dim_buildings WHERE is_current = 1", conn)

        # Merge silver and gold dataframes to find changes
        merge_df = pd.merge(df_silver, df_gold, on='building_id', how='left', suffixes=('_silver', '_gold'))

        # Identify changed records
        changed_records = merge_df[
            (merge_df['building_sk'].notna()) &
            (
                (merge_df['building_name_silver'] != merge_df['building_name_gold']) |
                (merge_df['zone_id_silver'] != merge_df['zone_id_gold']) |
                (merge_df['status_silver'] != merge_df['status_gold'])
                # Add other columns to check for changes here
            )
        ]

        if not changed_records.empty:
            print(f">> Expiring {len(changed_records)} changed records...")
            building_sks_to_expire = tuple(changed_records['building_sk'].astype(int))
            expire_query = text(f"""
                UPDATE gold.dim_buildings
                SET valid_to = GETDATE(), is_current = 0
                WHERE building_sk IN :sks
            """)
            conn.execute(expire_query, {'sks': building_sks_to_expire})

        # Identify new records (both entirely new and the new versions of changed records)
        new_or_updated_records = merge_df[
            (merge_df['building_sk'].isna()) |  # Entirely new records
            (merge_df['building_id'].isin(changed_records['building_id'])) # New versions of changed records
        ]

        if not new_or_updated_records.empty:
            print(f">> Inserting {len(new_or_updated_records)} new or updated records...")
            df_to_insert = new_or_updated_records[[
                'building_id', 'building_name_silver', 'zone_id_silver', 'building_type_silver',
                'owner_name_silver', 'address_silver', 'lat_silver', 'lon_silver', 'status_silver'
            ]].rename(columns=lambda c: c.replace('_silver', ''))

            df_to_insert['valid_from'] = pd.to_datetime('now')
            df_to_insert['valid_to'] = pd.NaT
            df_to_insert['is_current'] = True
            
            df_to_insert.to_sql('dim_buildings', conn, schema='gold', if_exists='append', index=False)

        conn.commit()
    print("Buildings dimension loaded.")


def load_fact_tables(engine):
    """
    Truncates and loads all fact tables by joining silver data with gold dimensions.
    """
    print("Truncating and loading fact tables...")
    fact_tables = [
        "fact_bus_gps", "fact_emergency_calls", "fact_energy_consumption", 
        "fact_traffic", "fact_waste_collection"
    ]

    with engine.connect() as conn:
        # Load all dimensions into memory for faster lookups
        dims = {
            'dim_calendar': pd.read_sql_table('dim_calendar', conn, schema='gold', index_col='date_key'),
            'dim_bus_routes': pd.read_sql_table('dim_bus_routes', conn, schema='gold', index_col='route_id'),
            'dim_zones': pd.read_sql_table('dim_zones', conn, schema='gold', index_col='zone_id'),
            'dim_devices': pd.read_sql_table('dim_devices', conn, schema='gold', index_col='device_id'),
            'dim_trucks': pd.read_sql_table('dim_trucks', conn, schema='gold', index_col='truck_id'),
            'dim_event_types': pd.read_sql_table('dim_event_types', conn, schema='gold', index_col='event_type_id'),
            'dim_buildings_scd': pd.read_sql_table('dim_buildings', conn, schema='gold')
        }

        for table in fact_tables:
            print(f">> Loading {table}...")
            source_table = table.replace('fact_', '')
            df_silver = pd.read_sql_table(source_table, conn, schema='silver')

            # Join with dimensions to get surrogate keys
            if table == 'fact_bus_gps':
                df_fact = df_silver.join(dims['dim_calendar']['date_sk'], on='date_key')\
                                   .join(dims['dim_bus_routes']['route_sk'], on='route_id')\
                                   .join(dims['dim_zones']['zone_sk'], on='zone_id')
                df_fact = df_fact[['date_sk', 'route_sk', 'zone_sk', 'bus_id', 'lat', 'lon', 'speed_kmh', 'occupancy_est']]

            # ... (Implement similar logic for other fact tables)
            # This is a simplified example. A full implementation would handle all fact tables.
            # For brevity, only fact_bus_gps is fully implemented here.
            
            # Example for fact_emergency_calls with SCD2 join
            if table == 'fact_emergency_calls':
                # Convert dates for comparison
                df_silver['reported_at'] = pd.to_datetime(df_silver['reported_at'])
                df_buildings_scd = dims['dim_buildings_scd']
                df_buildings_scd['valid_from'] = pd.to_datetime(df_buildings_scd['valid_from'])
                df_buildings_scd['valid_to'] = pd.to_datetime(df_buildings_scd['valid_to']).fillna(pd.Timestamp('9999-12-31'))

                # Perform a time-aware join
                df_merged = pd.merge(df_silver, df_buildings_scd, on='building_id')
                df_fact_scd = df_merged[
                    (df_merged['reported_at'] >= df_merged['valid_from']) & 
                    (df_merged['reported_at'] < df_merged['valid_to'])
                ]
                
                df_fact = df_fact_scd.join(dims['dim_calendar']['date_sk'], on='date_key')\
                                     .join(dims['dim_zones']['zone_sk'], on='zone_id')\
                                     .join(dims['dim_event_types']['event_type_sk'], on='event_type_id')
                df_fact = df_fact[['date_sk', 'zone_sk', 'building_sk', 'event_type_sk', 'call_id', 'priority_level', 'response_time_minutes']]


            if 'df_fact' in locals() and not df_fact.empty:
                conn.execute(text(f"TRUNCATE TABLE gold.{table}"))
                df_fact.to_sql(table, conn, schema='gold', if_exists='append', index=False, chunksize=1000)
                del df_fact # cleanup for next loop

        conn.commit()
    print("Fact tables loaded.")


def load_gold_layer():
    """
    Main function to orchestrate the loading of the Gold layer.
    """
    print("================================================")
    print("Loading Gold Layer")
    print("================================================")
    
    engine = get_db_engine()
    total_start_time = time.time()

    load_non_scd_dimensions(engine)
    load_scd2_buildings(engine)
    # The fact table loading is simplified. A full version would be more robust.
    load_fact_tables(engine)

    total_end_time = time.time()
    print("==========================================")
    print("Loading Gold Layer is Completed")
    print(f"   - Total Load Duration: {total_end_time - total_start_time:.2f} seconds")
    print("==========================================")

if __name__ == '__main__':
    load_gold_layer()
