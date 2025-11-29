# Orchestrating the Smart City ETL Pipeline with Apache Airflow

This document explains how Apache Airflow is used to schedule and execute the unified Talend ETL job for the Smart City project.

## Overview

Instead of managing multiple individual jobs, the ETL process has been consolidated into a single **master Talend job** (`Run_All_Jobs_Smart_City_ETL`). This simplifies orchestration significantly. Apache Airflow is now configured to run this one job, which in turn handles the entire data pipeline from dimensions to facts.

---

## Airflow DAG for the Unified Job

A new, simplified DAG has been created to orchestrate the master job.

-   **DAG File:** `smart_city_etl_dag.py`
-   **DAG ID:** `smart_city_etl`
-   **Purpose:** This DAG has a single task that executes the master Talend job. It is scheduled to run daily, ensuring the data warehouse is updated regularly.

### Key Features of the DAG:
-   **Simplicity:** Manages a single `PythonOperator` task instead of multiple dynamic tasks.
-   **Robustness:** Includes retries, timeouts, and detailed logging through the Python `subprocess` module.
-   **Scheduling:** Configured to run daily at 2 AM.

---

## How it Works

1.  **Talend Job Export:** The master Talend job (`Run_All_Jobs_Smart_City_ETL`) is exported as a standalone executable.
2.  **Deployment:** The exported job folder is placed in a known location on the Airflow machine (e.g., `/opt/airflow/jobs/`).
3.  **DAG Execution:**
    -   The `smart_city_etl` DAG is triggered by the Airflow scheduler.
    -   The `PythonOperator` calls a function that executes the `.sh` script of the master Talend job using Python's `subprocess` module.
    -   The output and any errors from the Talend job are captured and logged in Airflow, providing a centralized place for monitoring.

### Successful Execution in Airflow

Once the DAG runs successfully, it will appear in the Airflow UI as follows, indicating that the entire ETL pipeline has completed.

![Airflow Success](airflow_success.png)

---

## How to Use

1.  **Export the Master Talend Job:** Build the `Run_All_Jobs_Smart_City_ETL` job as a standalone "Autonomous Job".
2.  **Deploy Job to Airflow Machine:**
    -   Copy the exported job folder (e.g., `Run_All_Jobs_Smart_City_ETL`) to a directory on your Airflow worker/scheduler machine (e.g., `/opt/airflow/jobs/`).
    -   **Important:** Ensure the path in the `smart_city_etl_dag.py` file (`script_path` and `working_dir` variables) matches the location where you placed the job.
3.  **Deploy DAG:**
    -   Copy the `smart_city_etl_dag.py` file into your Airflow `dags` folder.
4.  **Enable in Airflow UI:**
    -   In the Airflow web UI, find and enable the `smart_city_etl` DAG.
    -   You can trigger it manually or wait for its daily schedule to run.
