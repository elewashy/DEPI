-- Use the 'SmartCity' database
USE SmartCity;
GO

-- Load Data
-- -------------------
BULK INSERT buildings
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\dimensions\buildings.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT calendar
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\dimensions\calendar.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT devices
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\dimensions\devices.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT trucks
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\dimensions\trucks.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

-- Load Static Data
-- ----------------------------
BULK INSERT bus_routes
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\static\bus_routes.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT event_types
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\static\event_types.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT zones
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\static\zones.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

-- Load Data
-- --------------
BULK INSERT bus_gps
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\facts\bus_gps.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT emergency_calls
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\facts\emergency_calls.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT energy_consumption
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\facts\energy_consumption.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT traffic
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\facts\traffic.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);

BULK INSERT waste_collection
FROM 'C:\Users\Mohamed Tamer\Desktop\Work\DEPI\Smart_City\datasets\silver_data\facts\waste_collection.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);
