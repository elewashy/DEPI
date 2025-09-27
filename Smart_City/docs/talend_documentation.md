# Smart City ETL Project Documentation using Talend

## Overview

This document provides a detailed explanation of the ETL (Extract, Transform, Load) process designed using Talend. The goal of this project is to build a Data Warehouse for a smart city, enabling the analysis of various data such as energy consumption, traffic, and bus locations.

Data is extracted from an operational (OLTP) database named `SmartCity`, then transformed, cleaned, and loaded into the `SmartCityDWH` data warehouse, which is designed with a Star Schema model.

---

## Architecture

### 1. Source Database

-   **Name:** `SmartCity`
-   **Description:** An operational (OLTP) database containing daily data for smart city services.
-   **DDL File:** `data_with_talend/ddl_smart_city.sql`
-   **Data Load File:** `data_with_talend/load_data_smart_city.sql`

### 2. Data Warehouse

-   **Name:** `SmartCityDWH`
-   **Description:** An analytical (OLAP) data warehouse containing dimension and fact tables to facilitate analysis and reporting.
-   **DDL File:** `data_with_talend/ddl_smart_city_dwh.sql`

---

## Talend ETL Jobs

Two main jobs were designed in Talend to load data into the data warehouse.

### Job 1: Loading `dim_buildings` Dimension (SCD Type 2)

<img src="dim_buildings.png" alt="Talend Job for dim_buildings" width="600"/>

#### Purpose

This job is responsible for loading and processing building data into the `dim_buildings` table. It uses the Slowly Changing Dimension (SCD) Type 2 technique to maintain a history of changes to the building data.

#### Components Used

1.  **`SmartCity` (tDBInput):** Reads building data from the `buildings` table in the `SmartCity` source database.
2.  **`tJava` (tJava):** Used to execute Java code. In this case, it initializes context variables or sets up values before the loading process, such as `entry_date_key`.
3.  **`tMap` (tMap):** Maps the source fields to the target fields.
4.  **`tDBSCD` (tDBSCD):** The core component for implementing SCD Type 2. It performs the following tasks:
    -   **Source Key:** `building_id` (the business key).
    -   **Surrogate Key:** `building_sk` (the auto-generated surrogate key).
    -   **Start Date & End Date:** `valid_from` and `valid_to` to define the validity period of each record.
    -   **Version:** `is_current` to identify the current record.

#### Logic

1.  All records are read from the source `buildings` table.
2.  For each record, the `tDBSCD` component checks if the `building_id` already exists in `dim_buildings`.
3.  **If the record is new:** It is inserted as a new record with `is_current = 1` and `valid_to = NULL`.
4.  **If the record exists and its data has changed:**
    -   The old record is updated by setting `is_current = 0` and `valid_to` to the current date.
    -   A new record is inserted with the same `building_id` and the updated data, with `is_current = 1` and `valid_to = NULL`.

---

### Job 2: Loading `fact_bus_gps` Fact Table

<img src="fact_bus_gps.png" alt="Talend Job for fact_bus_gps" width="700"/>

#### Purpose

This job is responsible for loading bus GPS tracking data into the `fact_bus_gps` fact table. This table combines measurements (like speed and location) with various dimension keys (like date, zone, and bus route).

#### Components Used

1.  **`bus_gps` (tDBInput):** Reads bus tracking data from the `bus_gps` table in the `SmartCity` source database.
2.  **`dim_calendar`, `dim_zones`, `dim_bus_routes` (tDBInput):** Lookup components that read dimension tables from `SmartCityDWH` to retrieve their surrogate keys.
3.  **`tMap_1` (tMap):** The central component in this job, which performs the following:
    -   **Join:** Joins the incoming `bus_gps` data with the dimension tables (`dim_calendar`, `dim_zones`, `dim_bus_routes`) using business keys like `date_key`, `zone_id`, and `route_id`.
    -   **Mapping:** Replaces the business keys with their corresponding surrogate keys (e.g., `date_sk`, `zone_sk`, `route_sk`) and passes the measures to the target table.
4.  **`fact_bus_gps` (tDBOutput):** Loads the transformed data into the `fact_bus_gps` table in `SmartCityDWH`.

#### Logic

1.  The `bus_gps` data is read as the main data flow.
2.  For each record in `bus_gps`, `tMap` performs a lookup on the dimension tables to find the corresponding surrogate keys.
3.  For example, the `date_key` from the `bus_gps` table is used to look up the `date_sk` in `dim_calendar`.
4.  The surrogate keys are combined with the measures (like `speed_kmh`, `occupancy_est`) into a single data flow.
5.  Finally, this combined data is loaded into the `fact_bus_gps` table.

---

## Generalized ETL Job Patterns

The following sections describe the general patterns for loading the remaining dimension and fact tables, based on the examples provided and the data warehouse schema.

### General Pattern for Loading Other Dimension Tables

The other dimension tables in the data warehouse (`dim_calendar`, `dim_devices`, `dim_trucks`, `dim_bus_routes`, `dim_event_types`, `dim_zones`) do not appear to require SCD Type 2 history tracking. They can be loaded using a simpler, more direct ETL pattern, likely as SCD Type 1 (overwrite updates) or a simple truncate-and-load.

#### Assumed Logic (SCD Type 1)

1.  **Source Input:** A `tDBInput` component reads data from the corresponding source table in the `SmartCity` database (e.g., `zones` for `dim_zones`).
2.  **Mapping:** A `tMap` component performs a direct one-to-one mapping of columns from the source to the target dimension table. It would also be used to generate the surrogate key (`_sk`) if it's not an identity column and add metadata like `entry_date_key`.
3.  **Target Output:** A `tDBOutput` component writes the data to the target dimension table in `SmartCityDWH`. The "Action on data" would typically be set to **"Insert or Update"**.
    -   It would use the business key (e.g., `zone_id`) to check for the existence of a record.
    -   If the record is new, it's inserted.
    -   If the record exists, it's updated with the latest values from the source.

### General Pattern for Loading Other Fact Tables

The remaining fact tables (`fact_emergency_calls`, `fact_energy_consumption`, `fact_traffic`, `fact_waste_collection`) follow a similar pattern to `fact_bus_gps`. They involve reading transactional data and looking up surrogate keys from the corresponding dimension tables.

#### Assumed Logic

1.  **Main Source Input:** A `tDBInput` reads the main transactional data from the source database (e.g., `emergency_calls` for `fact_emergency_calls`).
2.  **Lookup Inputs:** Multiple `tDBInput` components are configured as lookups to read from the relevant dimension tables (e.g., `dim_calendar`, `dim_zones`, `dim_buildings`, `dim_event_types`).
3.  **Mapping and Transformation (`tMap`):**
    -   The main source flow is joined with each dimension lookup flow inside the `tMap`.
    -   The join condition matches the business key from the source data (e.g., `building_id`) with the business key in the dimension table.
    -   The surrogate key (e.g., `building_sk`) from each dimension is retrieved.
    -   The output flow from the `tMap` consists of all the required surrogate keys and the measures/degenerate dimensions from the source fact data (e.g., `priority_level`, `response_time_minutes`).
4.  **Target Output:** A `tDBOutput` component performs a standard insert of the fully formed fact records into the target fact table in `SmartCityDWH`.
