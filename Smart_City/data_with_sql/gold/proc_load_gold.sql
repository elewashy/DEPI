/*
===============================================================================
Stored Procedure: gold.proc_load_gold
===============================================================================
Purpose:
    This procedure loads data from the Silver layer into the Gold layer DWH.
    It performs an incremental load for dimensions and facts, and handles
    Slowly Changing Dimensions Type 2 logic for the buildings dimension.
===============================================================================
*/
ALTER PROCEDURE gold.proc_load_gold
AS
BEGIN
    SET NOCOUNT ON;

    -- =========================================================================
    --  Load Dimensions (Non-SCD)
    --  (New records from silver are inserted into gold)
    -- =========================================================================
    PRINT 'Loading non-SCD dimensions...';

    -- dim_calendar (assumes full load or pre-populated)
    -- For simplicity, we'll merge based on date_key.
    MERGE gold.dim_calendar AS target
    USING silver.calendar AS source
    ON target.date_key = source.date_key
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (date_sk, date_key, date, day, month, month_name, year, week_day, week_number, is_weekend)
        VALUES (source.date_key, source.date_key, source.date, source.day, source.month, source.month_name, source.year, source.week_day, source.week_number, source.is_weekend);

    -- Other dimensions
    INSERT INTO gold.dim_devices (device_id, device_type, building_id, install_date, status, manufacturer)
    SELECT s.device_id, s.device_type, s.building_id, s.install_date, s.status, s.manufacturer
    FROM silver.devices s
    WHERE NOT EXISTS (SELECT 1 FROM gold.dim_devices g WHERE g.device_id = s.device_id);

    INSERT INTO gold.dim_trucks (truck_id, truck_type, capacity_tons, fuel_type, status)
    SELECT s.truck_id, s.truck_type, s.capacity_tons, s.fuel_type, s.status
    FROM silver.trucks s
    WHERE NOT EXISTS (SELECT 1 FROM gold.dim_trucks g WHERE g.truck_id = s.truck_id);

    INSERT INTO gold.dim_zones (zone_id, zone_name, lat_min, lat_max, lon_min, lon_max, description)
    SELECT s.zone_id, s.zone_name, s.lat_min, s.lat_max, s.lon_min, s.lon_max, s.description
    FROM silver.zones s
    WHERE NOT EXISTS (SELECT 1 FROM gold.dim_zones g WHERE g.zone_id = s.zone_id);

    INSERT INTO gold.dim_event_types (event_type_id, event_type_name, description)
    SELECT s.event_type_id, s.event_type_name, s.description
    FROM silver.event_types s
    WHERE NOT EXISTS (SELECT 1 FROM gold.dim_event_types g WHERE g.event_type_id = s.event_type_id);

    INSERT INTO gold.dim_bus_routes (route_id, route_name, start_point, end_point, distance_km, active_status)
    SELECT s.route_id, s.route_name, s.start_point, s.end_point, s.distance_km, s.active_status
    FROM silver.bus_routes s
    WHERE NOT EXISTS (SELECT 1 FROM gold.dim_bus_routes g WHERE g.route_id = s.route_id);

    PRINT 'Non-SCD dimensions loaded.';

    -- =========================================================================
    --  Load dim_buildings (SCD Type 2)
    -- =========================================================================
    PRINT 'Loading buildings dimension (SCD Type 2)...';

    -- Step 1: Create a temp table to store changes from silver
    SELECT *
    INTO #building_changes
    FROM silver.buildings;

    -- Step 2: Update existing records that have changed
    -- These records are now historical, so we set their 'valid_to' and 'is_current' flags
    UPDATE gold.dim_buildings
    SET
        valid_to = GETDATE(),
        is_current = 0
    FROM gold.dim_buildings g
    JOIN #building_changes s ON g.building_id = s.building_id
    WHERE g.is_current = 1 AND
          (g.building_name <> s.building_name OR g.zone_id <> s.zone_id OR g.status <> s.status); -- Add other columns to check for changes

    -- Step 3: Insert new records
    -- These can be completely new buildings or the new versions of existing buildings
    INSERT INTO gold.dim_buildings (
        building_id, building_name, zone_id, building_type, owner_name, address,
        lat, lon, status, valid_from, valid_to, is_current
    )
    SELECT
        s.building_id, s.building_name, s.zone_id, s.building_type, s.owner_name, s.address,
        s.lat, s.lon, s.status, GETDATE() AS valid_from, NULL AS valid_to, 1 AS is_current
    FROM #building_changes s
    WHERE NOT EXISTS (
        SELECT 1 FROM gold.dim_buildings g
        WHERE g.building_id = s.building_id AND g.is_current = 1
    );

    DROP TABLE #building_changes;
    PRINT 'Buildings dimension loaded.';


    -- =========================================================================
    --  Load Fact Tables
    --  (Assuming we are loading a specific timeframe, e.g., yesterday's data)
    --  For this example, we'll do a full truncate and load for simplicity.
    -- =========================================================================
    PRINT 'Truncating and loading fact tables...';

    TRUNCATE TABLE gold.fact_bus_gps;
    INSERT INTO gold.fact_bus_gps (date_sk, route_sk, zone_sk, bus_id, lat, lon, speed_kmh, occupancy_est)
    SELECT d_cal.date_sk, d_br.route_sk, d_z.zone_sk, s.bus_id, s.lat, s.lon, s.speed_kmh, s.occupancy_est
    FROM silver.bus_gps s
    JOIN gold.dim_calendar d_cal ON s.date_key = d_cal.date_key
    JOIN gold.dim_bus_routes d_br ON s.route_id = d_br.route_id
    JOIN gold.dim_zones d_z ON s.zone_id = d_z.zone_id;

    TRUNCATE TABLE gold.fact_emergency_calls;
    INSERT INTO gold.fact_emergency_calls (date_sk, zone_sk, building_sk, event_type_sk, call_id, priority_level, response_time_minutes)
    SELECT d_cal.date_sk, d_z.zone_sk, d_b.building_sk, d_et.event_type_sk, s.call_id, s.priority_level, s.response_time_minutes
    FROM silver.emergency_calls s
    JOIN gold.dim_calendar d_cal ON s.date_key = d_cal.date_key
    JOIN gold.dim_zones d_z ON s.zone_id = d_z.zone_id
    JOIN gold.dim_event_types d_et ON s.event_type_id = d_et.event_type_id
    -- Joining with buildings requires matching on the correct historical record
    JOIN gold.dim_buildings d_b ON s.building_id = d_b.building_id AND s.reported_at >= d_b.valid_from AND s.reported_at < ISNULL(d_b.valid_to, '9999-12-31');


    TRUNCATE TABLE gold.fact_energy_consumption;
    -- Note: The join to dim_buildings should be time-aware if building attributes affect energy analysis
    INSERT INTO gold.fact_energy_consumption (date_sk, building_sk, device_sk, kwh, voltage, [current], quality_flag)
    SELECT d_cal.date_sk, d_b.building_sk, d_d.device_sk, s.kwh, s.voltage, s.[current], s.quality_flag
    FROM silver.energy_consumption s
    JOIN gold.dim_calendar d_cal ON s.date_key = d_cal.date_key
    JOIN gold.dim_devices d_d ON s.device_id = d_d.device_id
    JOIN gold.dim_buildings d_b ON s.building_id = d_b.building_id AND d_b.is_current = 1; -- Simplified: joining with current building record


    TRUNCATE TABLE gold.fact_traffic;
    INSERT INTO gold.fact_traffic (date_sk, zone_sk, device_sk, vehicle_count, avg_speed_kmh)
    SELECT d_cal.date_sk, d_z.zone_sk, d_d.device_sk, s.vehicle_count, s.avg_speed_kmh
    FROM silver.traffic s
    JOIN gold.dim_calendar d_cal ON s.date_key = d_cal.date_key
    JOIN gold.dim_zones d_z ON s.zone_id = d_z.zone_id
    JOIN gold.dim_devices d_d ON s.device_id = d_d.device_id;

    TRUNCATE TABLE gold.fact_waste_collection;
    -- Note: The join to dim_buildings should be time-aware
    INSERT INTO gold.fact_waste_collection (date_sk, zone_sk, building_sk, truck_sk, container_id, fill_level_percent)
    SELECT d_cal.date_sk, d_z.zone_sk, d_b.building_sk, d_t.truck_sk, s.container_id, s.fill_level_percent
    FROM silver.waste_collection s
    JOIN gold.dim_calendar d_cal ON s.date_key = d_cal.date_key
    JOIN gold.dim_zones d_z ON s.zone_id = d_z.zone_id
    JOIN gold.dim_trucks d_t ON s.truck_id = d_t.truck_id
    JOIN gold.dim_buildings d_b ON s.building_id = d_b.building_id AND d_b.is_current = 1; -- Simplified: joining with current building record

    PRINT 'Fact tables loaded.';
    PRINT 'Gold layer load process completed successfully.';

END;
GO
