/*
===============================================================================
DDL Script: Create Bronze Tables
===============================================================================
Script Purpose:
    This script creates tables in the 'bronze' schema, dropping existing tables 
    if they already exist.
	  Run this script to re-define the DDL structure of 'bronze' Tables
===============================================================================
*/

-- Dimensions Tables
IF OBJECT_ID('bronze.buildings', 'U') IS NOT NULL
    DROP TABLE bronze.buildings;
GO

CREATE TABLE bronze.buildings (
    building_id     NVARCHAR(50),
    building_name   NVARCHAR(255),
    zone_id         NVARCHAR(50),
    building_type   NVARCHAR(100),
    owner_name      NVARCHAR(255),
    address         NVARCHAR(MAX),
    lat             FLOAT,
    lon             FLOAT,
    status          NVARCHAR(50)
);
GO

IF OBJECT_ID('bronze.calendar', 'U') IS NOT NULL
    DROP TABLE bronze.calendar;
GO

CREATE TABLE bronze.calendar (
    date_key        INT,
    [date]          DATE,
    [day]           INT,
    [month]         INT,
    month_name      NVARCHAR(50),
    [year]          INT,
    week_day        NVARCHAR(50),
    week_number     INT,
    is_weekend      NVARCHAR(10)
);
GO

IF OBJECT_ID('bronze.devices', 'U') IS NOT NULL
    DROP TABLE bronze.devices;
GO

CREATE TABLE bronze.devices (
    device_id       NVARCHAR(50),
    device_type     NVARCHAR(100),
    building_id     NVARCHAR(50),
    install_date    DATE,
    status          NVARCHAR(50),
    manufacturer    NVARCHAR(100)
);
GO

IF OBJECT_ID('bronze.trucks', 'U') IS NOT NULL
    DROP TABLE bronze.trucks;
GO

CREATE TABLE bronze.trucks (
    truck_id        NVARCHAR(50),
    truck_type      NVARCHAR(100),
    capacity_tons   FLOAT,
    fuel_type       NVARCHAR(50),
    status          NVARCHAR(50)
);
GO

-- Facts Tables
IF OBJECT_ID('bronze.bus_gps', 'U') IS NOT NULL
    DROP TABLE bronze.bus_gps;
GO

CREATE TABLE bronze.bus_gps (
    date_key        INT,
    time_key        NVARCHAR(10),
    bus_id          NVARCHAR(50),
    route_id        NVARCHAR(50),
    zone_id         NVARCHAR(50),
    lat             FLOAT,
    lon             FLOAT,
    speed_kmh       FLOAT,
    occupancy_est   INT
);
GO

IF OBJECT_ID('bronze.emergency_calls', 'U') IS NOT NULL
    DROP TABLE bronze.emergency_calls;
GO

CREATE TABLE bronze.emergency_calls (
    call_id                 NVARCHAR(50),
    date_key                INT,
    time_key                NVARCHAR(10),
    zone_id                 NVARCHAR(50),
    building_id             NVARCHAR(50),
    event_type_id           NVARCHAR(50),
    priority_level          NVARCHAR(50),
    reported_at             DATETIME,
    resolved_at             DATETIME,
    response_time_minutes   INT
);
GO

IF OBJECT_ID('bronze.energy_consumption', 'U') IS NOT NULL
    DROP TABLE bronze.energy_consumption;
GO

CREATE TABLE bronze.energy_consumption (
    date_key        INT,
    time_key        NVARCHAR(10),
    building_id     NVARCHAR(50),
    device_id       NVARCHAR(50),
    kwh             FLOAT,
    voltage         FLOAT,
    [current]       FLOAT,
    quality_flag    NVARCHAR(10)
);
GO

IF OBJECT_ID('bronze.traffic', 'U') IS NOT NULL
    DROP TABLE bronze.traffic;
GO

CREATE TABLE bronze.traffic (
    date_key        INT,
    time_key        NVARCHAR(10),
    zone_id         NVARCHAR(50),
    device_id       NVARCHAR(50),
    vehicle_count   INT,
    avg_speed_kmh   FLOAT
);
GO

IF OBJECT_ID('bronze.waste_collection', 'U') IS NOT NULL
    DROP TABLE bronze.waste_collection;
GO

CREATE TABLE bronze.waste_collection (
    date_key            INT,
    time_key            NVARCHAR(10),
    zone_id             NVARCHAR(50),
    building_id         NVARCHAR(50),
    container_id        NVARCHAR(50),
    fill_level_percent  INT,
    truck_id            NVARCHAR(50)
);
GO

-- Static Tables
IF OBJECT_ID('bronze.bus_routes', 'U') IS NOT NULL
    DROP TABLE bronze.bus_routes;
GO

CREATE TABLE bronze.bus_routes (
    route_id        NVARCHAR(50),
    route_name      NVARCHAR(255),
    start_point     NVARCHAR(255),
    end_point       NVARCHAR(255),
    distance_km     FLOAT,
    active_status   NVARCHAR(50)
);
GO

IF OBJECT_ID('bronze.event_types', 'U') IS NOT NULL
    DROP TABLE bronze.event_types;
GO

CREATE TABLE bronze.event_types (
    event_type_id   NVARCHAR(50),
    event_type_name NVARCHAR(100),
    description     NVARCHAR(MAX)
);
GO

IF OBJECT_ID('bronze.zones', 'U') IS NOT NULL
    DROP TABLE bronze.zones;
GO

CREATE TABLE bronze.zones (
    zone_id         NVARCHAR(50),
    zone_name       NVARCHAR(100),
    lat_min         FLOAT,
    lat_max         FLOAT,
    lon_min         FLOAT,
    lon_max         FLOAT,
    description     NVARCHAR(MAX)
);
GO
