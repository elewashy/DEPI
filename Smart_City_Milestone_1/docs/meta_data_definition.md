# Data Catalog for Smart City Gold Layer

## Overview
The Gold Layer is the business-level data representation for the Smart City data warehouse, structured to support analytical and reporting use cases. It consists of dimension and fact tables that provide a clean, enriched, and business-ready dataset using a Star Schema model.

---

## Dimensions

### 1. `gold.dim_calendar`
- **Purpose:** Stores date attributes for analysis across different facts.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;"><b>Primary Key.</b> Surrogate key for the calendar dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date_key</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Natural key representing the date (e.g., YYYYMMDD).</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DATE</code></td><td style="padding: 8px; border: 1px solid #ddd;">The full date.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>day</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The day of the month.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>month</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The month of the year.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>month_name</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The name of the month.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>year</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The year.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>week_day</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The name of the day of the week.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>week_number</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The week number of the year.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>is_weekend</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(5)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Flag indicating if the day is a weekend ('True' or 'False').</td></tr>
  </tbody>
</table>

---

### 2. `gold.dim_devices`
- **Purpose:** Stores information about smart devices installed across the city.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>device_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;"><b>Primary Key.</b> Surrogate key for the devices dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>device_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Natural key for the device (e.g., 'D001').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>device_type</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(50)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The type of the device (e.g., 'Traffic Sensor', 'Energy Meter').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The ID of the building where the device is installed.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>install_date</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DATE</code></td><td style="padding: 8px; border: 1px solid #ddd;">The date the device was installed.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>status</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The current operational status of the device.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>manufacturer</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(50)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The manufacturer of the device.</td></tr>
  </tbody>
</table>

---

### 3. `gold.dim_trucks`
- **Purpose:** Stores information about waste collection trucks.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>truck_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;"><b>Primary Key.</b> Surrogate key for the trucks dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>truck_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Natural key for the truck (e.g., 'T001').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>truck_type</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(50)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The type or model of the truck.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>capacity_tons</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The waste capacity of the truck in tons.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>fuel_type</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The type of fuel the truck uses.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>status</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The current status of the truck.</td></tr>
  </tbody>
</table>

---

### 4. `gold.dim_zones`
- **Purpose:** Stores information about geographical zones in the city.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;"><b>Primary Key.</b> Surrogate key for the zones dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Natural key for the zone (e.g., 'Z1').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_name</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(50)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The name of the zone.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lat_min</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The minimum latitude of the zone boundary.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lat_max</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The maximum latitude of the zone boundary.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lon_min</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The minimum longitude of the zone boundary.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lon_max</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The maximum longitude of the zone boundary.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>description</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(255)</code></td><td style="padding: 8px; border: 1px solid #ddd;">A description of the zone.</td></tr>
  </tbody>
</table>

---

### 5. `gold.dim_event_types`
- **Purpose:** Stores details about types of emergency events.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>event_type_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;"><b>Primary Key.</b> Surrogate key for the event types dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>event_type_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Natural key for the event type (e.g., 'ET01').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>event_type_name</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(50)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The name of the event type (e.g., 'Fire', 'Medical').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>description</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(255)</code></td><td style="padding: 8px; border: 1px solid #ddd;">A description of the event type.</td></tr>
  </tbody>
</table>

---

### 6. `gold.dim_bus_routes`
- **Purpose:** Stores information about public bus routes.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>route_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;"><b>Primary Key.</b> Surrogate key for the bus routes dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>route_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Natural key for the bus route (e.g., 'R01').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>route_name</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(100)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The name or number of the bus route.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>start_point</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(100)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The starting point of the route.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>end_point</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(100)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The ending point of the route.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>distance_km</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(5, 2)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The total distance of the route in kilometers.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>active_status</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The operational status of the route.</td></tr>
  </tbody>
</table>

---

### 7. `gold.dim_buildings` (SCD Type 2)
- **Purpose:** Stores the current and historical states of buildings, tracking changes over time.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;"><b>Primary Key.</b> Surrogate key, unique for each version of a building's record.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Natural key for the building. This value is repeated for each historical version.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_name</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(100)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The name of the building.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The ID of the zone where the building is located.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_type</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(50)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The type of building (e.g., 'Residential', 'Commercial').</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>owner_name</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(100)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The name of the building owner.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>address</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(255)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The street address of the building.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lat</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The latitude of the building's location.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lon</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The longitude of the building's location.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>status</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The status of the building for this specific version.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>valid_from</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DATETIME</code></td><td style="padding: 8px; border: 1px solid #ddd;">The timestamp when this record version became active.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>valid_to</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DATETIME</code></td><td style="padding: 8px; border: 1px solid #ddd;">The timestamp when this record version expired (NULL for current).</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>is_current</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>BIT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Flag (1 or 0) indicating if this is the current active record for the building.</td></tr>
  </tbody>
</table>

---

## Facts

### 8. `gold.fact_bus_gps`
- **Purpose:** Stores GPS tracking data for buses.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the calendar dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>route_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the bus routes dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the zones dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>bus_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Degenerate Dimension. The natural key of the bus.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lat</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The latitude of the bus's position.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>lon</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(9, 6)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The longitude of the bus's position.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>speed_kmh</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(5, 2)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The speed of the bus in km/h.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>occupancy_est</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The estimated number of passengers.</td></tr>
  </tbody>
</table>

---

### 9. `gold.fact_emergency_calls`
- **Purpose:** Stores data about emergency calls received.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color:rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the calendar dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the zones dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the building dimension's historical version.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>event_type_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the event types dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>call_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Degenerate Dimension. The natural key of the call.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>priority_level</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(20)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The priority level of the emergency.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>response_time_minutes</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The response time in minutes.</td></tr>
  </tbody>
</table>

---

### 10. `gold.fact_energy_consumption`
- **Purpose:** Stores energy consumption data from smart meters.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the calendar dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the building dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>device_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the devices dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>kwh</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(10, 4)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The energy consumed in kilowatt-hours.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>voltage</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(7, 2)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The voltage reading.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>current</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(10, 4)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The current reading.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>quality_flag</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Degenerate Dimension. A flag indicating the quality of the reading.</td></tr>
  </tbody>
</table>

---

### 11. `gold.fact_traffic`
- **Purpose:** Stores traffic data from road sensors.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color: rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the calendar dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the zones dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>device_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the devices dimension (sensor).</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>vehicle_count</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The number of vehicles detected.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>avg_speed_kmh</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>DECIMAL(5, 2)</code></td><td style="padding: 8px; border: 1px solid #ddd;">The average speed of vehicles in km/h.</td></tr>
  </tbody>
</table>

---

### 12. `gold.fact_waste_collection`
- **Purpose:** Stores data about waste collection operations.
- **Columns:**
<table style="width:100%; border: 1px solid #ddd; border-collapse: collapse;">
  <thead>
    <tr style="background-color:rgb(0, 0, 0);">
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Column Name</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Data Type</th>
      <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Description</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>date_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the calendar dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>zone_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the zones dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>building_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the building dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>truck_sk</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">Surrogate key linking to the trucks dimension.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>container_id</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>VARCHAR(10)</code></td><td style="padding: 8px; border: 1px solid #ddd;">Degenerate Dimension. The natural key of the waste container.</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><code>fill_level_percent</code></td><td style="padding: 8px; border: 1px solid #ddd;"><code>INT</code></td><td style="padding: 8px; border: 1px solid #ddd;">The fill level of the container as a percentage.</td></tr>
  </tbody>
</table>
