/*
===============================================================================
DDL Script: Create Silver Tables
===============================================================================
Script Purpose:
    This script creates tables in the 'silver' schema, dropping existing tables 
    if they already exist.
	  Run this script to re-define the DDL structure of 'silver' Tables
===============================================================================
*/

-- Dimensions Tables
IF OBJECT_ID('silver.buildings', 'U') IS NOT NULL
    DROP TABLE silver.buildings;
GO

CREATE TABLE silver.buildings (
    building_id     NVARCHAR(50),
    building_name   NVARCHAR(255),
    zone_id         NVARCHAR(50),
    building_type   NVARCHAR(100),
    owner_name      NVARCHAR(255),
    address         NVARCHAR(MAX),
    lat             FLOAT,
    lon             FLOAT,
    status          NVARCHAR(50),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.calendar', 'U') IS NOT NULL
    DROP TABLE silver.calendar;
GO

CREATE TABLE silver.calendar (
    date_key        INT,
    [date]          DATE,
    [day]           INT,
    [month]         INT,
    month_name      NVARCHAR(50),
    [year]          INT,
    week_day        NVARCHAR(50),
    week_number     INT,
    is_weekend      NVARCHAR(10),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.devices', 'U') IS NOT NULL
    DROP TABLE silver.devices;
GO

CREATE TABLE silver.devices (
    device_id       NVARCHAR(50),
    device_type     NVARCHAR(100),
    building_id     NVARCHAR(50),
    install_date    DATE,
    status          NVARCHAR(50),
    manufacturer    NVARCHAR(100),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.trucks', 'U') IS NOT NULL
    DROP TABLE silver.trucks;
GO

CREATE TABLE silver.trucks (
    truck_id        NVARCHAR(50),
    truck_type      NVARCHAR(100),
    capacity_tons   FLOAT,
    fuel_type       NVARCHAR(50),
    status          NVARCHAR(50),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

-- Facts Tables
IF OBJECT_ID('silver.bus_gps', 'U') IS NOT NULL
    DROP TABLE silver.bus_gps;
GO

CREATE TABLE silver.bus_gps (
    date_key        INT,
    time_key        NVARCHAR(10),
    bus_id          NVARCHAR(50),
    route_id        NVARCHAR(50),
    zone_id         NVARCHAR(50),
    lat             FLOAT,
    lon             FLOAT,
    speed_kmh       FLOAT,
    occupancy_est   INT,
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.emergency_calls', 'U') IS NOT NULL
    DROP TABLE silver.emergency_calls;
GO

CREATE TABLE silver.emergency_calls (
    call_id                 NVARCHAR(50),
    date_key                INT,
    time_key                NVARCHAR(10),
    zone_id                 NVARCHAR(50),
    building_id             NVARCHAR(50),
    event_type_id           NVARCHAR(50),
    priority_level          NVARCHAR(50),
    reported_at             DATETIME,
    resolved_at             DATETIME,
    response_time_minutes   INT,
    dwh_create_date         DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.energy_consumption', 'U') IS NOT NULL
    DROP TABLE silver.energy_consumption;
GO

CREATE TABLE silver.energy_consumption (
    date_key        INT,
    time_key        NVARCHAR(10),
    building_id     NVARCHAR(50),
    device_id       NVARCHAR(50),
    kwh             FLOAT,
    voltage         FLOAT,
    [current]       FLOAT,
    quality_flag    NVARCHAR(10),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.traffic', 'U') IS NOT NULL
    DROP TABLE silver.traffic;
GO

CREATE TABLE silver.traffic (
    date_key        INT,
    time_key        NVARCHAR(10),
    zone_id         NVARCHAR(50),
    device_id       NVARCHAR(50),
    vehicle_count   INT,
    avg_speed_kmh   FLOAT,
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.waste_collection', 'U') IS NOT NULL
    DROP TABLE silver.waste_collection;
GO

CREATE TABLE silver.waste_collection (
    date_key            INT,
    time_key            NVARCHAR(10),
    zone_id             NVARCHAR(50),
    building_id         NVARCHAR(50),
    container_id        NVARCHAR(50),
    fill_level_percent  INT,
    truck_id            NVARCHAR(50),
    dwh_create_date     DATETIME2 DEFAULT GETDATE()
);
GO

-- Static Tables
IF OBJECT_ID('silver.bus_routes', 'U') IS NOT NULL
    DROP TABLE silver.bus_routes;
GO

CREATE TABLE silver.bus_routes (
    route_id        NVARCHAR(50),
    route_name      NVARCHAR(255),
    start_point     NVARCHAR(255),
    end_point       NVARCHAR(255),
    distance_km     FLOAT,
    active_status   NVARCHAR(50),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.event_types', 'U') IS NOT NULL
    DROP TABLE silver.event_types;
GO

CREATE TABLE silver.event_types (
    event_type_id   NVARCHAR(50),
    event_type_name NVARCHAR(100),
    description     NVARCHAR(MAX),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

IF OBJECT_ID('silver.zones', 'U') IS NOT NULL
    DROP TABLE silver.zones;
GO

CREATE TABLE silver.zones (
    zone_id         NVARCHAR(50),
    zone_name       NVARCHAR(100),
    lat_min         FLOAT,
    lat_max         FLOAT,
    lon_min         FLOAT,
    lon_max         FLOAT,
    description     NVARCHAR(MAX),
    dwh_create_date DATETIME2 DEFAULT GETDATE()
);
GO

