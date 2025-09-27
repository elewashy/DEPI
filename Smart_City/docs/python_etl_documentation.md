# Smart City Python ETL Project Documentation

## Overview

This document provides a detailed explanation of the Python-based ETL (Extract, Transform, Load) process for the Smart City data warehouse. This implementation mirrors the logic of the SQL-based ETL, following a **Medallion Architecture** (Bronze, Silver, Gold) to progressively refine and structure the data.

The entire process is orchestrated through a series of Python scripts, utilizing libraries such as **Pandas** for data manipulation and **SQLAlchemy** for database interaction.

---

## Project Structure

The project is organized within the `data_with_python/` directory:

```
data_with_python/
├── bronze/
│   └── load_bronze.py
├── silver/
│   └── load_silver.py
├── gold/
│   └── load_gold.py
├── database.py         # Handles DB connection
├── main.py             # Orchestrates the ETL pipeline
├── requirements.txt    # Project dependencies
└── .env.example        # Template for environment variables
```

### Setup and Execution

1.  **Install Dependencies:**
    ```bash
    pip install -r data_with_python/requirements.txt
    ```
2.  **Configure Database:** Copy the `.env.example` file to a new file named `.env` and fill in your SQL Server connection details.
3.  **Run the Pipeline:** Execute the main script from within the `data_with_python` directory.
    ```bash
    python main.py
    ```

---

## ETL Process and Layers

The ETL process is orchestrated by `main.py`, which executes the loading scripts for each layer in the correct sequence.

### 1. Bronze Layer (Raw Ingestion)

The Bronze layer ingests the raw data from the source CSV files into the data warehouse.

-   **Script:** `bronze/load_bronze.py`
-   **Logic:**
    1.  **Connect:** Establishes a database connection using `database.py`.
    2.  **Truncate:** Clears all tables in the `bronze` schema to prevent data duplication on re-runs.
    3.  **Read CSV:** Uses Pandas (`pd.read_csv`) to read each source CSV file from the `datasets` directory into a DataFrame.
    4.  **Load:** Uses Pandas `to_sql()` method to efficiently bulk-load the DataFrame into the corresponding table in the `bronze` schema.

---

### 2. Silver Layer (Cleansing and Conforming)

The Silver layer cleans and applies basic transformations to the data from the Bronze layer.

-   **Script:** `silver/load_silver.py`
-   **Logic:**
    1.  **Read from Bronze:** Reads each table from the `bronze` schema into a Pandas DataFrame.
    2.  **Transformations (Data Cleansing):**
        -   Applies string trimming to all object columns to remove leading/trailing whitespace.
        -   Converts empty strings (`''`) to `NaN` (which becomes `NULL` in the database) for specific foreign key columns (e.g., `building_id`), mirroring the logic from the SQL ETL to improve data integrity.
    3.  **Truncate:** Clears all tables in the `silver` schema.
    4.  **Load:** Writes the cleaned DataFrame into the corresponding table in the `silver` schema.

---

### 3. Gold Layer (Presentation Model)

The Gold layer transforms the cleansed data into a dimensional model (star schema) ready for analytics.

-   **Script:** `gold/load_gold.py`
-   **Logic:** This is the most complex stage, broken down into several steps:
    1.  **Load Non-SCD Dimensions:**
        -   For simple dimensions (`dim_zones`, `dim_devices`, etc.), the script reads data from the silver and gold tables.
        -   It identifies new records by comparing business keys and inserts only the new ones into the gold dimension tables. This makes the load idempotent for these dimensions.
    2.  **Load `dim_buildings` (SCD Type 2):**
        -   Reads current building records from `gold.dim_buildings` and all records from `silver.buildings`.
        -   Uses a Pandas `merge` operation to compare the datasets and identify records that have changed.
        -   For changed records, an `UPDATE` statement is executed to expire the old record in the gold table (setting `is_current = 0` and `valid_to` to the current time).
        -   The new or updated versions of the records are then inserted into `gold.dim_buildings` as new rows with `is_current = 1`.
    3.  **Load Fact Tables:**
        -   All gold dimension tables are loaded into in-memory Pandas DataFrames for efficient lookups.
        -   Each silver fact table is processed individually.
        -   The script uses Pandas `join` or `merge` operations to replace the business keys (e.g., `zone_id`) with their corresponding surrogate keys (e.g., `zone_sk`) from the in-memory dimensions.
        -   For facts related to `dim_buildings`, a time-aware merge is performed to ensure the fact record is linked to the correct historical version of the building.
        -   Finally, the gold fact tables are truncated and the fully transformed fact DataFrames are loaded.
