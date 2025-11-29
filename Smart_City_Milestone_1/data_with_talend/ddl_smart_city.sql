USE master;
GO

-- Drop and recreate the 'SmartCity' database
IF EXISTS (SELECT 1 FROM sys.databases WHERE name = 'SmartCity')
BEGIN
    ALTER DATABASE SmartCity SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE SmartCity;
END;
GO

-- Create the 'SmartCity' database
CREATE DATABASE SmartCity;
GO

USE SmartCity;
GO

-- Create Tables
-- -------------------------

-- Table: buildings
CREATE TABLE buildings (
    building_id VARCHAR(10) PRIMARY KEY,
    building_name VARCHAR(100),
    zone_id VARCHAR(10),
    building_type VARCHAR(50),
    owner_name VARCHAR(100),
    address VARCHAR(255),
    lat DECIMAL(9, 6),
    lon DECIMAL(9, 6),
    status VARCHAR(20)
);

-- Table: calendar
CREATE TABLE calendar (
    date_key INT PRIMARY KEY,
    date DATE,
    day INT,
    month INT,
    month_name VARCHAR(20),
    year INT,
    week_day VARCHAR(20),
    week_number INT,
    is_weekend VARCHAR(5)
);

-- Table: devices
CREATE TABLE devices (
    device_id VARCHAR(10) PRIMARY KEY,
    device_type VARCHAR(50),
    building_id VARCHAR(10),
    install_date DATE,
    status VARCHAR(20),
    manufacturer VARCHAR(50)
);

-- Table: trucks
CREATE TABLE trucks (
    truck_id VARCHAR(10) PRIMARY KEY,
    truck_type VARCHAR(50),
    capacity_tons INT,
    fuel_type VARCHAR(20),
    status VARCHAR(20)
);

-- Table: bus_routes
CREATE TABLE bus_routes (
    route_id VARCHAR(10) PRIMARY KEY,
    route_name VARCHAR(100),
    start_point VARCHAR(100),
    end_point VARCHAR(100),
    distance_km DECIMAL(5, 2),
    active_status VARCHAR(20)
);

-- Table: event_types
CREATE TABLE event_types (
    event_type_id VARCHAR(10) PRIMARY KEY,
    event_type_name VARCHAR(50),
    description VARCHAR(255)
);

-- Table: zones
CREATE TABLE zones (
    zone_id VARCHAR(10) PRIMARY KEY,
    zone_name VARCHAR(50),
    lat_min DECIMAL(9, 6),
    lat_max DECIMAL(9, 6),
    lon_min DECIMAL(9, 6),
    lon_max DECIMAL(9, 6),
    description VARCHAR(255)
);

-- Create Tables
-- --------------------

-- Table: bus_gps
CREATE TABLE bus_gps (
    date_key INT,
    time_key VARCHAR(6),
    bus_id VARCHAR(10),
    route_id VARCHAR(10),
    zone_id VARCHAR(10),
    lat DECIMAL(9, 6),
    lon DECIMAL(9, 6),
    speed_kmh DECIMAL(5, 2),
    occupancy_est INT
);

-- Table: emergency_calls
CREATE TABLE emergency_calls (
    call_id VARCHAR(10) PRIMARY KEY,
    date_key INT,
    time_key VARCHAR(6),
    zone_id VARCHAR(10),
    building_id VARCHAR(10),
    event_type_id VARCHAR(10),
    priority_level VARCHAR(20),
    reported_at DATETIME,
    resolved_at DATETIME,
    response_time_minutes INT
);

-- Table: energy_consumption
CREATE TABLE energy_consumption (
    date_key INT,
    time_key VARCHAR(6),
    building_id VARCHAR(10),
    device_id VARCHAR(10),
    kwh DECIMAL(10, 4),
    voltage DECIMAL(7, 2),
    [current] DECIMAL(10, 4),
    quality_flag VARCHAR(10)
);

-- Table: traffic
CREATE TABLE traffic (
    date_key INT,
    time_key VARCHAR(6),
    zone_id VARCHAR(10),
    device_id VARCHAR(10),
    vehicle_count INT,
    avg_speed_kmh DECIMAL(5, 2)
);

-- Table: waste_collection
CREATE TABLE waste_collection (
    date_key INT,
    time_key VARCHAR(6),
    zone_id VARCHAR(10),
    building_id VARCHAR(10),
    container_id VARCHAR(10),
    fill_level_percent INT,
    truck_id VARCHAR(10)
);
