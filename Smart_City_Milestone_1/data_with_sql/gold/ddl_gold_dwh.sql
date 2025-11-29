USE SmartCityDWH;
GO

-- Create the gold schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'gold')
BEGIN
    EXEC('CREATE SCHEMA gold');
END
GO


-- Create Dimension Tables
-- -------------------------

-- Dimension: Buildings (SCD Type 2)
CREATE TABLE gold.dim_buildings (
    building_sk INT IDENTITY(1,1) PRIMARY KEY,
    building_id VARCHAR(10), -- Business Key (will be repeated)
    building_name VARCHAR(100),
    zone_id VARCHAR(10),
    building_type VARCHAR(50),
    owner_name VARCHAR(100),
    address VARCHAR(255),
    lat DECIMAL(9, 6),
    lon DECIMAL(9, 6),
    status VARCHAR(20),
    valid_from DATETIME,
    valid_to DATETIME,
    is_current BIT
);

-- Dimension: Calendar
CREATE TABLE gold.dim_calendar (
    date_sk INT PRIMARY KEY,
    date_key INT UNIQUE, -- Business Key
    date DATE,
    day INT,
    month INT,
    month_name VARCHAR(20),
    year INT,
    week_day VARCHAR(20),
    week_number INT,
    is_weekend VARCHAR(5)
);

-- Dimension: Devices
CREATE TABLE gold.dim_devices (
    device_sk INT IDENTITY(1,1) PRIMARY KEY,
    device_id VARCHAR(10), -- Business Key
    device_type VARCHAR(50),
    building_id VARCHAR(10),
    install_date DATE,
    status VARCHAR(20),
    manufacturer VARCHAR(50)
);

-- Dimension: Trucks
CREATE TABLE gold.dim_trucks (
    truck_sk INT IDENTITY(1,1) PRIMARY KEY,
    truck_id VARCHAR(10), -- Business Key
    truck_type VARCHAR(50),
    capacity_tons INT,
    fuel_type VARCHAR(20),
    status VARCHAR(20)
);

-- Dimension: Bus Routes
CREATE TABLE gold.dim_bus_routes (
    route_sk INT IDENTITY(1,1) PRIMARY KEY,
    route_id VARCHAR(10), -- Business Key
    route_name VARCHAR(100),
    start_point VARCHAR(100),
    end_point VARCHAR(100),
    distance_km DECIMAL(5, 2),
    active_status VARCHAR(20)
);

-- Dimension: Event Types
CREATE TABLE gold.dim_event_types (
    event_type_sk INT IDENTITY(1,1) PRIMARY KEY,
    event_type_id VARCHAR(10), -- Business Key
    event_type_name VARCHAR(50),
    description VARCHAR(255)
);

-- Dimension: Zones
CREATE TABLE gold.dim_zones (
    zone_sk INT IDENTITY(1,1) PRIMARY KEY,
    zone_id VARCHAR(10), -- Business Key
    zone_name VARCHAR(50),
    lat_min DECIMAL(9, 6),
    lat_max DECIMAL(9, 6),
    lon_min DECIMAL(9, 6),
    lon_max DECIMAL(9, 6),
    description VARCHAR(255)
);

-- Create Fact Tables
-- --------------------

-- Fact: Bus GPS
CREATE TABLE gold.fact_bus_gps (
    date_sk INT,
    route_sk INT,
    zone_sk INT,
    bus_id VARCHAR(10), -- Degenerate Dimension
    lat DECIMAL(9, 6),
    lon DECIMAL(9, 6),
    speed_kmh DECIMAL(5, 2),
    occupancy_est INT
);

-- Fact: Emergency Calls
CREATE TABLE gold.fact_emergency_calls (
    date_sk INT,
    zone_sk INT,
    building_sk INT,
    event_type_sk INT,
    call_id VARCHAR(10), -- Degenerate Dimension
    priority_level VARCHAR(20),
    response_time_minutes INT
);

-- Fact: Energy Consumption
CREATE TABLE gold.fact_energy_consumption (
    date_sk INT,
    building_sk INT,
    device_sk INT,
    kwh DECIMAL(10, 4),
    voltage DECIMAL(7, 2),
    [current] DECIMAL(10, 4),
    quality_flag VARCHAR(10) -- Degenerate Dimension
);

-- Fact: Traffic
CREATE TABLE gold.fact_traffic (
    date_sk INT,
    zone_sk INT,
    device_sk INT,
    vehicle_count INT,
    avg_speed_kmh DECIMAL(5, 2)
);

-- Fact: Waste Collection
CREATE TABLE gold.fact_waste_collection (
    date_sk INT,
    zone_sk INT,
    building_sk INT,
    truck_sk INT,
    container_id VARCHAR(10), -- Degenerate Dimension
    fill_level_percent INT
);
GO

-- Add Foreign Key Constraints
-- ---------------------------

-- Fact Bus GPS
ALTER TABLE gold.fact_bus_gps ADD CONSTRAINT fk_bus_gps_date FOREIGN KEY (date_sk) REFERENCES gold.dim_calendar(date_sk);
ALTER TABLE gold.fact_bus_gps ADD CONSTRAINT fk_bus_gps_route FOREIGN KEY (route_sk) REFERENCES gold.dim_bus_routes(route_sk);
ALTER TABLE gold.fact_bus_gps ADD CONSTRAINT fk_bus_gps_zone FOREIGN KEY (zone_sk) REFERENCES gold.dim_zones(zone_sk);

-- Fact Emergency Calls
ALTER TABLE gold.fact_emergency_calls ADD CONSTRAINT fk_emergency_calls_date FOREIGN KEY (date_sk) REFERENCES gold.dim_calendar(date_sk);
ALTER TABLE gold.fact_emergency_calls ADD CONSTRAINT fk_emergency_calls_zone FOREIGN KEY (zone_sk) REFERENCES gold.dim_zones(zone_sk);
ALTER TABLE gold.fact_emergency_calls ADD CONSTRAINT fk_emergency_calls_building FOREIGN KEY (building_sk) REFERENCES gold.dim_buildings(building_sk);
ALTER TABLE gold.fact_emergency_calls ADD CONSTRAINT fk_emergency_calls_event_type FOREIGN KEY (event_type_sk) REFERENCES gold.dim_event_types(event_type_sk);

-- Fact Energy Consumption
ALTER TABLE gold.fact_energy_consumption ADD CONSTRAINT fk_energy_consumption_date FOREIGN KEY (date_sk) REFERENCES gold.dim_calendar(date_sk);
ALTER TABLE gold.fact_energy_consumption ADD CONSTRAINT fk_energy_consumption_building FOREIGN KEY (building_sk) REFERENCES gold.dim_buildings(building_sk);
ALTER TABLE gold.fact_energy_consumption ADD CONSTRAINT fk_energy_consumption_device FOREIGN KEY (device_sk) REFERENCES gold.dim_devices(device_sk);

-- Fact Traffic
ALTER TABLE gold.fact_traffic ADD CONSTRAINT fk_traffic_date FOREIGN KEY (date_sk) REFERENCES gold.dim_calendar(date_sk);
ALTER TABLE gold.fact_traffic ADD CONSTRAINT fk_traffic_zone FOREIGN KEY (zone_sk) REFERENCES gold.dim_zones(zone_sk);
ALTER TABLE gold.fact_traffic ADD CONSTRAINT fk_traffic_device FOREIGN KEY (device_sk) REFERENCES gold.dim_devices(device_sk);

-- Fact Waste Collection
ALTER TABLE gold.fact_waste_collection ADD CONSTRAINT fk_waste_collection_date FOREIGN KEY (date_sk) REFERENCES gold.dim_calendar(date_sk);
ALTER TABLE gold.fact_waste_collection ADD CONSTRAINT fk_waste_collection_zone FOREIGN KEY (zone_sk) REFERENCES gold.dim_zones(zone_sk);
ALTER TABLE gold.fact_waste_collection ADD CONSTRAINT fk_waste_collection_building FOREIGN KEY (building_sk) REFERENCES gold.dim_buildings(building_sk);
ALTER TABLE gold.fact_waste_collection ADD CONSTRAINT fk_waste_collection_truck FOREIGN KEY (truck_sk) REFERENCES gold.dim_trucks(truck_sk);
GO
