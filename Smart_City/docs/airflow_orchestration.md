# Orchestrating Talend Jobs with Apache Airflow

This document explains how Apache Airflow is used to schedule, execute, and monitor the Talend ETL jobs developed for the Smart City project.

## Overview

Apache Airflow is an open-source platform for programmatically authoring, scheduling, and monitoring workflows. By integrating our Talend jobs with Airflow, we gain the ability to automate the entire data pipeline, set complex schedules, handle failures and retries, and have a centralized view of all our ETL executions.

---

## Project Structure

The Airflow-related files are located in the `Smart_City_Airflow/` directory. For this integration to work, this directory should be placed inside the `dags` folder of your Airflow instance.

```
<airflow_home>/dags/
└── Smart_City_Airflow/
    ├── Smart_City/
    │   ├── into_data_into_dim_buildings/
    │   │   ├── into_data_into_dim_buildings_run.sh
    │   │   └── ... (other Talend job files)
    │   ├── into_data_into_fact_bus_gps/
    │   │   ├── into_data_into_fact_bus_gps_run.sh
    │   │   └── ...
    │   └── ... (directories for all other exported Talend jobs)
    └── talend_jobs_dag.py
```

-   **`talend_jobs_dag.py`**: This is the core Python script that defines the Airflow DAGs.
-   **`Smart_City/`**: This directory acts as a container for all the standalone Talend jobs that have been built and exported. Each sub-directory (e.g., `into_data_into_dim_buildings/`) contains the executable shell script (`.sh`), JAR files, and other dependencies needed to run that specific Talend job.

---

## Dynamic DAG Generation

Instead of creating a separate DAG file for each Talend job, a dynamic approach is used.

-   **Script:** `talend_jobs_dag.py`
-   **Logic:**
    1.  **Scan Directory:** The script scans the `Smart_City/` directory to find all the sub-directories, where each directory represents an individual Talend job.
    2.  **Generate DAGs:** For each job directory found, it dynamically creates a new Airflow DAG. The DAG is named based on the directory name (e.g., `talend_into_data_into_dim_buildings`).
    3.  **Create Bash Task:** Each DAG consists of a single `BashOperator` task. This task is configured to:
        -   Make the `.sh` run script executable (`chmod +x`).
        -   Execute the shell script, which in turn runs the Java-based Talend job.

This dynamic generation means that to add a new Talend job to Airflow, you simply need to export the job and place it in the `Smart_City/` directory. Airflow will automatically detect it and create a new DAG for it on the next scheduler refresh.

---

## How to Use

1.  **Export Talend Jobs:** Build each of your Talend jobs as a standalone "Autonomous Job".
2.  **Deploy to Airflow:**
    -   Copy the entire `Smart_City_Airflow` folder (which includes the `talend_jobs_dag.py` file and the `Smart_City` directory with all the exported jobs) into the `dags` folder of your Airflow installation.
    -   The default path in the DAG is set to `/opt/airflow/dags/Smart_City`. You may need to adjust the `TALEND_JOBS_BASE_PATH` variable in `talend_jobs_dag.py` if your Airflow setup is different.
3.  **Enable in Airflow UI:**
    -   After a few moments, Airflow will parse the DAG file.
    -   In the Airflow web UI, you will see a new DAG for each Talend job (e.g., `talend_into_data_into_dim_buildings`).
    -   You can then enable these DAGs, trigger them manually, or set them to run on a schedule.
