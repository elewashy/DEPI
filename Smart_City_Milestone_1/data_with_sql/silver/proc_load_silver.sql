/*
===============================================================================
Stored Procedure: Load Silver Layer (Bronze -> Silver)
===============================================================================
Script Purpose:
    This stored procedure performs the ETL (Extract, Transform, Load) process to 
    populate the 'silver' schema tables from the 'bronze' schema.
	Actions Performed:
		- Truncates Silver tables.
		- Inserts cleansed data from Bronze into Silver tables.
		
Parameters:
    None. 
	  This stored procedure does not accept any parameters or return any values.

Usage Example:
    EXEC Silver.load_silver;
===============================================================================
*/

CREATE OR ALTER PROCEDURE silver.load_silver AS
BEGIN
    DECLARE @start_time DATETIME, @end_time DATETIME, @batch_start_time DATETIME, @batch_end_time DATETIME; 
    BEGIN TRY
        SET @batch_start_time = GETDATE();
        PRINT '================================================';
        PRINT 'Loading Silver Layer';
        PRINT '================================================';

		PRINT '------------------------------------------------';
		PRINT 'Loading Dimensions Tables';
		PRINT '------------------------------------------------';

		-- Loading silver.buildings
        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.buildings';
		TRUNCATE TABLE silver.buildings;
		PRINT '>> Inserting Data Into: silver.buildings';
		INSERT INTO silver.buildings (
			building_id, building_name, zone_id, building_type, owner_name, 
			address, lat, lon, status
		)
		SELECT
			building_id, building_name, zone_id, building_type, owner_name, 
			address, lat, lon, status
		FROM bronze.buildings;
		SET @end_time = GETDATE();
        PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		-- Loading silver.calendar
        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.calendar';
		TRUNCATE TABLE silver.calendar;
		PRINT '>> Inserting Data Into: silver.calendar';
		INSERT INTO silver.calendar (
			date_key, [date], [day], [month], month_name, [year], 
			week_day, week_number, is_weekend
		)
		SELECT
			date_key, [date], [day], [month], month_name, [year], 
			week_day, week_number, is_weekend
		FROM bronze.calendar;
        SET @end_time = GETDATE();
        PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

        -- Loading silver.devices
        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.devices';
		TRUNCATE TABLE silver.devices;
		PRINT '>> Inserting Data Into: silver.devices';
		INSERT INTO silver.devices (
			device_id, device_type, building_id, install_date, status, manufacturer
		)
		SELECT
			device_id,
			device_type,
			NULLIF(TRIM(building_id), ''),
			install_date,
			status,
			manufacturer
		FROM bronze.devices;
        SET @end_time = GETDATE();
        PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		-- Loading silver.trucks
        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.trucks';
		TRUNCATE TABLE silver.trucks;
		PRINT '>> Inserting Data Into: silver.trucks';
		INSERT INTO silver.trucks (
			truck_id, truck_type, capacity_tons, fuel_type, status
		)
		SELECT
			truck_id, truck_type, capacity_tons, fuel_type, status
		FROM bronze.trucks;
		SET @end_time = GETDATE();
        PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		PRINT '------------------------------------------------';
		PRINT 'Loading Facts Tables';
		PRINT '------------------------------------------------';

        -- Loading silver.bus_gps
        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.bus_gps';
		TRUNCATE TABLE silver.bus_gps;
		PRINT '>> Inserting Data Into: silver.bus_gps';
		INSERT INTO silver.bus_gps (
			date_key, time_key, bus_id, route_id, zone_id, lat, lon, speed_kmh, occupancy_est
		)
		SELECT
			date_key, time_key, bus_id, route_id, zone_id, lat, lon, speed_kmh, occupancy_est
		FROM bronze.bus_gps;
	    SET @end_time = GETDATE();
        PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';
		
		-- Loading silver.emergency_calls
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.emergency_calls';
		TRUNCATE TABLE silver.emergency_calls;
		PRINT '>> Inserting Data Into: silver.emergency_calls';
		INSERT INTO silver.emergency_calls (
			call_id, date_key, time_key, zone_id, building_id, event_type_id, 
			priority_level, reported_at, resolved_at, response_time_minutes
		)
		SELECT
			call_id, date_key, time_key, zone_id, NULLIF(TRIM(building_id), ''), 
			event_type_id, priority_level, reported_at, resolved_at, response_time_minutes
		FROM bronze.emergency_calls;
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		-- Loading silver.energy_consumption
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.energy_consumption';
		TRUNCATE TABLE silver.energy_consumption;
		PRINT '>> Inserting Data Into: silver.energy_consumption';
		INSERT INTO silver.energy_consumption (
			date_key, time_key, building_id, device_id, kwh, voltage, [current], quality_flag
		)
		SELECT
			date_key, time_key, building_id, device_id, kwh, voltage, [current], quality_flag
		FROM bronze.energy_consumption;
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		-- Loading silver.traffic
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.traffic';
		TRUNCATE TABLE silver.traffic;
		PRINT '>> Inserting Data Into: silver.traffic';
		INSERT INTO silver.traffic (
			date_key, time_key, zone_id, device_id, vehicle_count, avg_speed_kmh
		)
		SELECT
			date_key, time_key, zone_id, device_id, vehicle_count, avg_speed_kmh
		FROM bronze.traffic;
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		-- Loading silver.waste_collection
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.waste_collection';
		TRUNCATE TABLE silver.waste_collection;
		PRINT '>> Inserting Data Into: silver.waste_collection';
		INSERT INTO silver.waste_collection (
			date_key, time_key, zone_id, building_id, container_id, fill_level_percent, truck_id
		)
		SELECT
			date_key, time_key, zone_id, 
			NULLIF(TRIM(building_id), ''),
			container_id,
			fill_level_percent,
			NULLIF(TRIM(truck_id), '')
		FROM bronze.waste_collection;
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		PRINT '------------------------------------------------';
		PRINT 'Loading Static Tables';
		PRINT '------------------------------------------------';

		-- Loading silver.bus_routes
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.bus_routes';
		TRUNCATE TABLE silver.bus_routes;
		PRINT '>> Inserting Data Into: silver.bus_routes';
		INSERT INTO silver.bus_routes (
			route_id, route_name, start_point, end_point, distance_km, active_status
		)
		SELECT
			route_id, route_name, start_point, end_point, distance_km, active_status
		FROM bronze.bus_routes;
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		-- Loading silver.event_types
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.event_types';
		TRUNCATE TABLE silver.event_types;
		PRINT '>> Inserting Data Into: silver.event_types';
		INSERT INTO silver.event_types (
			event_type_id, event_type_name, description
		)
		SELECT
			event_type_id, event_type_name, description
		FROM bronze.event_types;
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		-- Loading silver.zones
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: silver.zones';
		TRUNCATE TABLE silver.zones;
		PRINT '>> Inserting Data Into: silver.zones';
		INSERT INTO silver.zones (
			zone_id, zone_name, lat_min, lat_max, lon_min, lon_max, description
		)
		SELECT
			zone_id, zone_name, lat_min, lat_max, lon_min, lon_max, description
		FROM bronze.zones;
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(SECOND, @start_time, @end_time) AS NVARCHAR) + ' seconds';
        PRINT '>> -------------';

		SET @batch_end_time = GETDATE();
		PRINT '=========================================='
		PRINT 'Loading Silver Layer is Completed';
        PRINT '   - Total Load Duration: ' + CAST(DATEDIFF(SECOND, @batch_start_time, @batch_end_time) AS NVARCHAR) + ' seconds';
		PRINT '=========================================='
		
	END TRY
	BEGIN CATCH
		PRINT '=========================================='
		PRINT 'ERROR OCCURED DURING LOADING SILVER LAYER'
		PRINT 'Error Message' + ERROR_MESSAGE();
		PRINT 'Error Message' + CAST (ERROR_NUMBER() AS NVARCHAR);
		PRINT 'Error Message' + CAST (ERROR_STATE() AS NVARCHAR);
		PRINT '=========================================='
	END CATCH
END
