/*
===============================================================================
Stored Procedure: Load Bronze Layer (Source Files -> Bronze)
===============================================================================
Script Purpose:
    This stored procedure loads data into the 'bronze' schema from external CSV files. 
    It performs the following actions:
    - Truncates the bronze tables before loading data.
    - Uses the `BULK INSERT` command to load data from csv Files to bronze tables.

Parameters:
    None. 
	  This stored procedure does not accept any parameters or return any values.

Usage Example:
    EXEC bronze.load_bronze;
===============================================================================
*/
CREATE OR ALTER PROCEDURE bronze.load_bronze AS
BEGIN
	DECLARE @start_time DATETIME, @end_time DATETIME, @batch_start_time DATETIME, @batch_end_time DATETIME; 
	BEGIN TRY
		SET @batch_start_time = GETDATE();
		PRINT '================================================';
		PRINT 'Loading Bronze Layer';
		PRINT '================================================';

		PRINT '------------------------------------------------';
		PRINT 'Loading Dimensions Tables';
		PRINT '------------------------------------------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.buildings';
		TRUNCATE TABLE bronze.buildings;
		PRINT '>> Inserting Data Into: bronze.buildings';
		BULK INSERT bronze.buildings
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\dimensions\buildings.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.calendar';
		TRUNCATE TABLE bronze.calendar;
		PRINT '>> Inserting Data Into: bronze.calendar';
		BULK INSERT bronze.calendar
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\dimensions\calendar.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.devices';
		TRUNCATE TABLE bronze.devices;
		PRINT '>> Inserting Data Into: bronze.devices';
		BULK INSERT bronze.devices
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\dimensions\devices.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

        SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.trucks';
		TRUNCATE TABLE bronze.trucks;
		PRINT '>> Inserting Data Into: bronze.trucks';
		BULK INSERT bronze.trucks
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\dimensions\trucks.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		PRINT '------------------------------------------------';
		PRINT 'Loading Facts Tables';
		PRINT '------------------------------------------------';
		
		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.bus_gps';
		TRUNCATE TABLE bronze.bus_gps;
		PRINT '>> Inserting Data Into: bronze.bus_gps';
		BULK INSERT bronze.bus_gps
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\facts\bus_gps.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.emergency_calls';
		TRUNCATE TABLE bronze.emergency_calls;
		PRINT '>> Inserting Data Into: bronze.emergency_calls';
		BULK INSERT bronze.emergency_calls
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\facts\emergency_calls.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.energy_consumption';
		TRUNCATE TABLE bronze.energy_consumption;
		PRINT '>> Inserting Data Into: bronze.energy_consumption';
		BULK INSERT bronze.energy_consumption
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\facts\energy_consumption.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.traffic';
		TRUNCATE TABLE bronze.traffic;
		PRINT '>> Inserting Data Into: bronze.traffic';
		BULK INSERT bronze.traffic
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\facts\traffic.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.waste_collection';
		TRUNCATE TABLE bronze.waste_collection;
		PRINT '>> Inserting Data Into: bronze.waste_collection';
		BULK INSERT bronze.waste_collection
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\facts\waste_collection.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		PRINT '------------------------------------------------';
		PRINT 'Loading Static Tables';
		PRINT '------------------------------------------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.bus_routes';
		TRUNCATE TABLE bronze.bus_routes;
		PRINT '>> Inserting Data Into: bronze.bus_routes';
		BULK INSERT bronze.bus_routes
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\static\bus_routes.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.event_types';
		TRUNCATE TABLE bronze.event_types;
		PRINT '>> Inserting Data Into: bronze.event_types';
		BULK INSERT bronze.event_types
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\static\event_types.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		SET @start_time = GETDATE();
		PRINT '>> Truncating Table: bronze.zones';
		TRUNCATE TABLE bronze.zones;
		PRINT '>> Inserting Data Into: bronze.zones';
		BULK INSERT bronze.zones
		FROM 'C:\Users\Mohamed Tamer\Desktop\Smart_City\datasets\silver_data\static\zones.csv'
		WITH (
			FIRSTROW = 2,
			FIELDTERMINATOR = ',',
			TABLOCK
		);
		SET @end_time = GETDATE();
		PRINT '>> Load Duration: ' + CAST(DATEDIFF(second, @start_time, @end_time) AS NVARCHAR) + ' seconds';
		PRINT '>> -------------';

		SET @batch_end_time = GETDATE();
		PRINT '=========================================='
		PRINT 'Loading Bronze Layer is Completed';
        PRINT '   - Total Load Duration: ' + CAST(DATEDIFF(SECOND, @batch_start_time, @batch_end_time) AS NVARCHAR) + ' seconds';
		PRINT '=========================================='
	END TRY
	BEGIN CATCH
		PRINT '=========================================='
		PRINT 'ERROR OCCURED DURING LOADING BRONZE LAYER'
		PRINT 'Error Message' + ERROR_MESSAGE();
		PRINT 'Error Message' + CAST (ERROR_NUMBER() AS NVARCHAR);
		PRINT 'Error Message' + CAST (ERROR_STATE() AS NVARCHAR);
		PRINT '=========================================='
	END CATCH
END
